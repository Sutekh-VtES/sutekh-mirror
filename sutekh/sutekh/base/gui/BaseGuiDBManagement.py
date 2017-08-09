# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# Factored out into base.gui 2014 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""This handles the gui aspects of upgrading the database."""

import logging
import datetime
import gtk
from sqlobject import sqlhub, connectionForURI
from .DBUpgradeDialog import DBUpgradeDialog
from .ProgressDialog import (ProgressDialog,
                             SutekhCountLogHandler)
from ..core.BaseDBManagement import (UnknownVersion,
                                     copy_to_new_abstract_card_db)
from ..core.DBUtility import flush_cache
from .SutekhDialog import (do_complaint_buttons, do_complaint,
                           do_complaint_warning, do_exception_complaint,
                           do_complaint_error_details)
from .GuiUtils import save_config
from ..core.BaseObjects import PhysicalCardSet
from ..core.DBUtility import get_cs_id_name_table


def wrapped_read(oFile, fDoRead, sDesc, oProgressDialog, oLogHandler):
    """Wrap the reading of a file in a ProgressDialog."""
    oProgressDialog.set_description(sDesc)
    oProgressDialog.show()
    fDoRead(oFile, oLogHandler)
    oProgressDialog.set_complete()


class BaseGuiDBManager(object):
    """Base class for handling gui DB Upgrades."""

    cZipFileWrapper = None

    def __init__(self, oWin, cDatabaseUpgrade):
        self._oWin = oWin
        self._oDatabaseUpgrade = cDatabaseUpgrade()

    def _get_names(self, _bDisableBackup):
        """Query the user for the files / urls to import.

           Returns a list of file names and a backup file name if required.
           return aFiles, sBackupFile
           aFiles should be None to skip the import / initialisation."""
        raise NotImplementedError('Implement _get_names')

    def _read_data(self, aFiles, oProgressDialog):
        """Read the data from the give files / urls."""
        raise NotImplementedError('Implement _read_data')

    def copy_to_new_db(self, oOldConn, oTempConn, oProgressDialog,
                       oLogHandler):
        """Copy card collection and card sets to a new abstract card db."""
        oProgressDialog.set_description(
            "Reloading card collection and card sets")
        oProgressDialog.reset()
        (bOK, aErrors) = copy_to_new_abstract_card_db(oOldConn,
                                                      oTempConn,
                                                      self._oWin.cardLookup,
                                                      oLogHandler)
        oProgressDialog.set_complete()
        if not bOK:
            sMesg = "\n".join(["There was a problem copying your collection"
                               " to the new database"] + aErrors +
                              ["Attempt to Continue Anyway (This is most"
                               " probably very dangerous)?"])
            iResponse = do_complaint_warning(sMesg)
            if iResponse == gtk.RESPONSE_OK:
                return True
            else:
                return False
        return True

    def initialize_db(self, oConfig):
        """Initialise the database if it doesn't exist."""
        # The config file is passed in as a parameter becasuse this can be
        # called before the window is setup completely, so we may not have
        # access to the config file via the main window.
        iRes = do_complaint_buttons(
            "The database doesn't seem to be properly initialised",
            gtk.MESSAGE_ERROR,
            (gtk.STOCK_QUIT, gtk.RESPONSE_CLOSE,
             "Initialise database with cardlist and rulings?", 1))
        if iRes != 1:
            return False
        else:
            aFiles, _sBackup = self._get_names(True)
            if aFiles is not None:
                oProgressDialog = ProgressDialog()
                try:
                    self._read_data(aFiles, oProgressDialog)
                    oProgressDialog.destroy()
                except IOError as oErr:
                    do_exception_complaint("Failed to read cardlists.\n\n%s\n"
                                           "Aborting import." % oErr)
                    oProgressDialog.destroy()
                    return False
            else:
                return False
        # Create the Physical Card Collection card set
        PhysicalCardSet(name='My Collection', parent=None)
        # Set the update date to today, so we don't prompt the user immediately
        # for a new update after we've started.
        # This may introduce clock issues, but matches the behaviour for when
        # the user manually refreshes the card list, rather than auto updating
        oConfig.set_last_update_date(datetime.date.today())
        # We have to save, since the re-validation after the plugins will
        # reload the file
        save_config(oConfig)
        return True

    def save_backup(self, sBackupFile, oProgressDialog):
        """Save a backup file, showing a progress dialog"""
        oLogHandler = SutekhCountLogHandler()
        oProgressDialog.set_description("Saving backup")
        oLogHandler.set_dialog(oProgressDialog)
        oProgressDialog.show()
        # pylint: disable=E1102
        # subclasses will provide a callable cZipFileWrapper
        oFile = self.cZipFileWrapper(sBackupFile)
        oFile.do_dump_all_to_zip(oLogHandler)
        oProgressDialog.set_complete()

    def refresh_card_list(self, oUpdateDate=None, aFiles=None):
        """Handle grunt work of refreshing the card lists"""
        # pylint: disable=R0914
        # We're juggling lots of different bits of state, so we use a lot
        # of variables
        aEditable = self._oWin.get_editable_panes()
        dOldMap = get_cs_id_name_table()
        if not aFiles:
            aFiles, sBackupFile = self._get_names(False)
        else:
            # XXX: Is this wise? We don't want to have the user
            # click through dialog after dialog, but should
            # we present this option anyway?
            sBackupFile = None
        if not aFiles:
            return False  # Nothing happened
        oProgressDialog = ProgressDialog()
        if sBackupFile is not None:
            # pylint: disable=W0703
            # we do want to catch all exceptions here
            try:
                self.save_backup(sBackupFile, oProgressDialog)
            except Exception as oErr:
                do_exception_complaint("Failed to write backup.\n\n%s\n"
                                       "Not touching the database further."
                                       % oErr)
                return False
        # This doesn't strictly need to be bounced via the main window
        # (unlike the signal at the end), but we do this for consistency
        self._oWin.prepare_for_db_update()
        oOldConn = sqlhub.processConnection
        oTempConn = connectionForURI("sqlite:///:memory:")
        sqlhub.processConnection = oTempConn
        try:
            self._read_data(aFiles, oProgressDialog)
        except IOError as oErr:
            # Failed to read one of the card lists, so clean up and abort
            do_exception_complaint("Failed to read cardlists.\n\n%s\n"
                                   "Aborting import." % oErr)
            oProgressDialog.destroy()
            # Restore connection
            sqlhub.processConnection = oOldConn
            # Undo effects of prepare_for_db_update
            self._oWin.update_to_new_db()
            return False
        # Refresh abstract card view for card lookups
        oLogHandler = SutekhCountLogHandler()
        oLogHandler.set_dialog(oProgressDialog)
        sqlhub.processConnection = oOldConn
        if not self.copy_to_new_db(oOldConn, oTempConn, oProgressDialog,
                                   oLogHandler):
            oProgressDialog.destroy()
            self._oWin.update_to_new_db()
            return True  # Force refresh
        # OK, update complete, copy back from oTempConn
        sqlhub.processConnection = oOldConn
        self._oWin.clear_cache()  # Don't hold old copies
        oProgressDialog.set_description("Finalizing import")
        oProgressDialog.reset()
        oProgressDialog.show()
        (bOK, aErrors) = self._oDatabaseUpgrade.create_final_copy(
            oTempConn, oLogHandler)
        if not bOK:
            sMesg = ("There was a problem updating the database\n"
                     "Your database may be in an inconsistent state -"
                     " sorry")
            logging.warn('\n'.join([sMesg] + aErrors))
            do_complaint_error_details(sMesg, "\n".join(aErrors))
        else:
            sMesg = "Import Completed\n"
            sMesg += "Everything seems to have gone OK"
            do_complaint(sMesg, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, True)
        oProgressDialog.destroy()
        dNewMap = get_cs_id_name_table()
        self._oWin.config_file.fix_profile_mapping(dOldMap, dNewMap)
        # We defer to the main window to publish this event on the message bus
        # to ensure we handle the caches correctly
        self._oWin.update_to_new_db()
        self._oWin.restore_editable_panes(aEditable)
        # Set the last update date
        if not oUpdateDate:
            # No date given, so set the last update date to today
            oUpdateDate = datetime.date.today()
        self._oWin.config_file.set_last_update_date(oUpdateDate)
        # Saving immediately to ensure we record the update seems
        # the safest thing to do here, although it's different from
        # how we usually treat the config file.
        save_config(self._oWin.config_file)
        return True

    def do_db_upgrade(self, aLowerTables, aHigherTables):
        """Attempt to upgrade the database"""
        if len(aHigherTables) > 0:
            sMesg = ("Database version error. Cannot continue\n"
                     "The following tables have a higher version"
                     " than expected:\n")
            sMesg += "\n".join(aHigherTables)
            sMesg += "\n\n<b>Unable to continue</b>"
            do_complaint_buttons(sMesg, gtk.MESSAGE_ERROR,
                                 (gtk.STOCK_QUIT, gtk.RESPONSE_CLOSE), True)
            # No sensible default here - user can override using
            # --ignore-db-version if desired
            return False
        sMesg = "Database version error. Cannot continue\n" \
                "The following tables need to be upgraded:\n"
        sMesg += "\n".join(aLowerTables)
        iRes = do_complaint_buttons(sMesg, gtk.MESSAGE_ERROR,
                                    (gtk.STOCK_QUIT, gtk.RESPONSE_CLOSE,
                                     "Attempt Automatic Database Upgrade", 1))
        if iRes != 1:
            return False
        oTempConn = connectionForURI("sqlite:///:memory:")
        oLogHandler = SutekhCountLogHandler()
        oProgressDialog = ProgressDialog()
        oLogHandler.set_dialog(oProgressDialog)
        try:
            oProgressDialog.set_description("Creating temporary copy")
            (bOK, aMessages) = self._oDatabaseUpgrade.create_memory_copy(
                oTempConn, oLogHandler)
            oProgressDialog.destroy()
            if bOK:
                oDialog = DBUpgradeDialog(aMessages)
                iRes = oDialog.run()
                oDialog.destroy()
                if iRes == gtk.RESPONSE_OK:
                    return self._do_commit_db(oLogHandler, oTempConn, aMessages)
                elif iRes == 1:
                    # Try running with the upgraded database
                    sqlhub.processConnection = oTempConn
                    # Ensure adapters are correctly updated
                    flush_cache()
                    return True
            else:
                sMesg = "Unable to create memory copy!\nUpgrade Failed."
                logging.warn('\n'.join([sMesg] + aMessages))
                do_complaint_error_details(sMesg, "\n".join(aMessages))
        except UnknownVersion as oErr:
            oProgressDialog.destroy()
            do_exception_complaint("Upgrade Failed. %s" % oErr)
        return False

    def _do_commit_db(self, oLogHandler, oTempConn, aOldMessages):
        """Handle committing the memory copy to the actual DB"""
        oProgressDialog = ProgressDialog()
        oProgressDialog.set_description("Commiting changes")
        oLogHandler.set_dialog(oProgressDialog)
        (bOK, aMessages) = self._oDatabaseUpgrade.create_final_copy(
            oTempConn, oLogHandler)
        oProgressDialog.destroy()
        if bOK:
            if aOldMessages:
                # Redisplay the messages from the database upgrade, so they
                # aren't forgetten about
                sMesg = 'Messages from Database Upgrade are:\n'
                for sStr in aOldMessages:
                    sMesg += '<b>%s</b>\n' % sStr
                sMesg += "\nChanges Commited\n"
            else:
                sMesg = "Changes Commited\n"
            if len(aMessages) > 0:
                sMesg += "Messages from commiting changes are:"
                for sStr in aMessages:
                    sMesg += '<b>%s</b>\n' % sStr
            else:
                sMesg += "Everything seems to have gone smoothly."
            do_complaint(sMesg, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, True)
            return True
        else:
            sMesg = ("Unable to commit updated database!\nUpgrade Failed.\n"
                     "Your database may be in an inconsistent state.")
            logging.warn('\n'.join([sMesg] + aMessages))
            do_complaint_error_details(sMesg, "\n".join(aMessages))
            return False
