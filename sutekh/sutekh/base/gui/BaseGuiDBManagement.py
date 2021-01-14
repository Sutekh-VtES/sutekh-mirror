# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008-2018 Neil Muller <drnlmuller+sutekh@gmail.com>
# Factored out into base.gui 2014 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""This handles the gui aspects of upgrading the database."""

import logging
import datetime
import zipfile
from collections import namedtuple
from io import BytesIO

from gi.repository import Gtk

from sqlobject import sqlhub, connectionForURI

from ..core.BaseDBManagement import (UnknownVersion,
                                     copy_to_new_abstract_card_db)
from ..core.BaseTables import AbstractCard, PhysicalCardSet
from ..core.DBUtility import (flush_cache, get_cs_id_name_table,
                              refresh_tables, set_metadata_date,
                              CARDLIST_UPDATE_DATE)

from ..io.EncodedFile import EncodedFile
from ..io.UrlOps import urlopen_with_timeout, HashError
from ..io.BaseZipFileWrapper import ZipEntryProxy

from .DBUpgradeDialog import DBUpgradeDialog
from .ProgressDialog import (ProgressDialog,
                             SutekhCountLogHandler,
                             SutekhHTMLLogHandler)
from .SutekhDialog import (do_complaint_buttons, do_info_message,
                           do_complaint_warning, do_exception_complaint,
                           do_complaint_error, do_complaint_error_details)
from .GuiUtils import save_config
from .GuiDataPack import gui_error_handler, progress_fetch_data
from .DataFilesDialog import DataFilesDialog, COMBINED_ZIP


def wrapped_read(oFile, fDoRead, sDesc, oProgressDialog, oLogHandler):
    """Wrap the reading of a file in a ProgressDialog."""
    oProgressDialog.set_description(sDesc)
    oProgressDialog.show()
    fDoRead(oFile, oLogHandler)
    oProgressDialog.set_complete()


# Information about a data file
# sName and sDescription are used to construct the file dialog
# sUrl is the download url for the file, if applicable
# bRequired is True if the file is required for the import to succeed
# bCountLogger is True if the reader uses the SutekhCountLogHandler
# if False, SutekhHTMLLogHandler is used.
# fReader is the function that reads the asociated data file
DataFileReader = namedtuple('DataFileReader', ['sName', 'sUrl',
                                               'sDescription',
                                               'tPattern', 'bRequired',
                                               'bCountLogger', 'fReader'])


class BaseGuiDBManager:
    """Base class for handling gui DB Upgrades."""
    # Tuple about files and associated reader functions and details
    # We use a tuple so this is ordered, and files will be read from
    # the first entry to the last
    tReaders = ()
    # Control whether to display the option for a combined zip file
    bDisplayZip = False
    # Url for zip file containing the combined data
    sZippedUrl = None
    # Hash for zip url if applicable
    sHash = None
    # List of database tables to reload when importing
    aTables = []

    cZipFileWrapper = None

    def __init__(self, oWin, cDatabaseUpgrade):
        self._oWin = oWin
        self._oDatabaseUpgrade = cDatabaseUpgrade()

    def _get_names(self, bDisableBackup):
        """Query the user for the files / urls to import.

           Returns a list of file names and a backup file name if required.
           return dFiles, sBackupFile
           dFiles should be None to skip the import / initialisation."""
        # Add the individual file buttons
        sBackupFile = None
        oFilesDialog = DataFilesDialog(self._oWin, self.tReaders,
                                       self.bDisplayZip, self.sZippedUrl,
                                       bDisableBackup)
        oFilesDialog.run()
        dChoices, sBackupFile = oFilesDialog.get_names()
        oFilesDialog.destroy()
        dFiles = {}
        # Check for zipped file case
        if COMBINED_ZIP in dChoices:
            dFiles = self.read_zip_file(dChoices[COMBINED_ZIP], self.sHash)
        else:
            # Handle the files individually
            for sName, oResult in dChoices.items():
                if oResult.sName is not None:
                    dFiles[sName] = EncodedFile(oResult.sName,
                                                bUrl=oResult.bIsUrl)
        return dFiles, sBackupFile

    def _do_import_checks(self, _oAbsCard):
        """Do the actual import checks.
           Returns a list of errors. An empty list is considered a success.

           Subclasses must implement the correct logic here."""
        raise NotImplementedError("Implement _do_import_checks")

    def _check_import(self):
        """Check the database for any import issues and display
           any errors to the user."""
        aMessages = []
        for oAbsCard in AbstractCard.select():
            aMessages.extend(self._do_import_checks(oAbsCard))
        if not aMessages:
            # No messages, so import should be fine
            return True
        # Display an abort / continue dialog with the messages
        aFullMessages = ["<b>The database import has failed"
                         " consistency checks</b>"]
        for sDetails in aMessages:
            aFullMessages.append('<i>%s</i>' % sDetails)
        iRes = do_complaint_buttons(
            '\n'.join(aFullMessages),
            Gtk.MessageType.ERROR,
            ("Abort import?", 1, "Accept import despite errors", 2),
            True)
        return iRes == 2

    def read_zip_file(self, oZipDetails, sHash):
        """open (Downlaoding it if required) a zip file and split it into
           the required bits.

           We provide a parameter for hashes, so it can be used when a
           hash is available."""
        aReaderNames = [x.sName for x in self.tReaders]
        if oZipDetails.bIsUrl:
            oFile = urlopen_with_timeout(oZipDetails.sName,
                                         fErrorHandler=gui_error_handler,
                                         bBinary=True)
            try:
                sData = progress_fetch_data(oFile, sHash=sHash,
                                            sDesc="Downloading zipfile")
            except HashError:
                do_complaint_error("Checksum failed for zipfile.\n"
                                   "Aborting")
                return None
        else:
            if not oZipDetails.sName:
                do_complaint_error("No filename or url given to update from.\n"
                                   "Aborting")
                return None
            fIn = open(oZipDetails.sName, 'rb')
            sData = fIn.read()
            fIn.close()
        oZipFile = zipfile.ZipFile(BytesIO(sData), 'r')
        aNames = oZipFile.namelist()
        dFiles = {}
        for sName in aNames:
            # We rely on the later checks to catch missing files, but
            # we only include files we have readers for here
            if sName in aReaderNames:
                # This may be a bit dangerous, but zip documentation suggests
                # it is correct for text data, which is what we expect here.
                oFile = ZipEntryProxy(oZipFile.read(sName).decode('utf8'))
                dFiles[sName] = oFile
        if not dFiles:
            do_complaint_error("Aborting the import."
                               "No useable files found in the zipfile")
        return dFiles

    def _read_data(self, dFiles, oProgressDialog):
        """Read the data from the give files / urls."""
        aMissing = []
        for oReader in self.tReaders:
            if oReader.bRequired and oReader.sName not in dFiles:
                aMissing.append("Missing %s" % oReader.sDescription)
        if aMissing:
            # Abort, since we're missing required data
            do_complaint_error_details("Aborting the import - "
                                       "Missing required data files",
                                       "\n".join(aMissing))
            return False
        refresh_tables(self.aTables, sqlhub.processConnection)
        oProgressDialog.reset()
        for oReader in self.tReaders:
            if oReader.sName not in dFiles:
                continue
            if oReader.bCountLogger:
                oLogHandler = SutekhCountLogHandler()
            else:
                oLogHandler = SutekhHTMLLogHandler()
            oLogHandler.set_dialog(oProgressDialog)
            wrapped_read(dFiles[oReader.sName], oReader.fReader,
                         oReader.sDescription, oProgressDialog, oLogHandler)
        return True

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
            return iResponse == Gtk.ResponseType.OK
        return True

    def initialize_db(self, oConfig):
        """Initialise the database if it doesn't exist."""
        # The config file is passed in as a parameter becasuse this can be
        # called before the window is setup completely, so we may not have
        # access to the config file via the main window.
        iRes = do_complaint_buttons(
            "The database doesn't seem to be properly initialised",
            Gtk.MessageType.ERROR,
            ("_Quit", Gtk.ResponseType.CLOSE,
             "Initialise database with cardlist and rulings?", 1))
        if iRes != 1:
            return False
        dFiles, _sBackup = self._get_names(True)
        if dFiles is not None:
            oProgressDialog = ProgressDialog()
            try:
                bRet = self._read_data(dFiles, oProgressDialog)
                oProgressDialog.destroy()
            except IOError as oErr:
                do_exception_complaint("Failed to read cardlists.\n\n%s\n"
                                       "Aborting import." % oErr)
                oProgressDialog.destroy()
                return False
        else:
            return False
        if bRet:
            # Import successful
            # Create the Physical Card Collection card set
            PhysicalCardSet(name='My Collection', parent=None)
        return bRet

    def save_backup(self, sBackupFile, oProgressDialog):
        """Save a backup file, showing a progress dialog"""
        oLogHandler = SutekhCountLogHandler()
        oProgressDialog.set_description("Saving backup")
        oLogHandler.set_dialog(oProgressDialog)
        oProgressDialog.show()
        # pylint: disable=not-callable
        # subclasses will provide a callable cZipFileWrapper
        oFile = self.cZipFileWrapper(sBackupFile)
        oFile.do_dump_all_to_zip(oLogHandler)
        oProgressDialog.set_complete()

    def refresh_card_list(self, oUpdateDate=None, dFiles=None):
        """Handle grunt work of refreshing the card lists"""
        # pylint: disable=too-many-locals, too-many-statements
        # We're juggling lots of different bits of state, so we use a
        # lot of variables
        # There isn't much benefit to breaking this function up,
        # since it's a single process we're managing.
        # pylint: disable=too-many-return-statements
        # Bunch of different failure points we need to consider
        aEditable = self._oWin.get_editable_panes()
        dOldMap = get_cs_id_name_table()
        if not dFiles:
            dFiles, sBackupFile = self._get_names(False)
        else:
            # XXX: Is this wise? We don't want to have the user
            # click through dialog after dialog, but should
            # we present this option anyway?
            sBackupFile = None
        if not dFiles:
            return False  # Nothing happened
        oProgressDialog = ProgressDialog()
        if sBackupFile is not None:
            # pylint: disable=broad-except
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
            bRet = self._read_data(dFiles, oProgressDialog)
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
        if not bRet:
            # Aborted for some other reason, so cleanup as above.
            # We assume the user has already seen a suitable error dialog.
            oProgressDialog.destroy()
            sqlhub.processConnection = oOldConn
            self._oWin.update_to_new_db()
            return False
        if not self._check_import():
            # user aborted the import due to failing consistency checks
            oProgressDialog.destroy()
            sqlhub.processConnection = oOldConn
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
            logging.warning('\n'.join([sMesg] + aErrors))
            do_complaint_error_details(sMesg, "\n".join(aErrors))
        else:
            sMesg = "Import Completed\n"
            sMesg += "Everything seems to have gone OK"
            do_info_message(sMesg)
        oProgressDialog.destroy()
        dNewMap = get_cs_id_name_table()
        self._oWin.config_file.fix_profile_mapping(dOldMap, dNewMap)
        # We defer to the main window to publish this event on the message bus
        # to ensure we handle the caches correctly
        self._oWin.update_to_new_db()
        self._oWin.restore_editable_panes(aEditable)
        # Update the cardlist update date if it's provided
        if oUpdateDate:
            # We assume the actual import has set the date to something
            # sensible by default (probably today), so we only change it
            # if we have specific information.
            set_metadata_date(CARDLIST_UPDATE_DATE, oUpdateDate)
        # Saving immediately to ensure we record the id updates seems
        # the safest thing to do here, although it's different from
        # how we usually treat the config file.
        save_config(self._oWin.config_file)
        return True

    def do_db_upgrade(self, aLowerTables, aHigherTables):
        """Attempt to upgrade the database"""
        if aHigherTables:
            sMesg = ("Database version error. Cannot continue\n"
                     "The following tables have a higher version"
                     " than expected:\n")
            sMesg += "\n".join(aHigherTables)
            sMesg += "\n\n<b>Unable to continue</b>"
            do_complaint_buttons(sMesg, Gtk.MessageType.ERROR,
                                 ("_Quit", Gtk.ResponseType.CLOSE), True)
            # No sensible default here - user can override using
            # --ignore-db-version if desired
            return False
        sMesg = "Database version error. Cannot continue\n" \
                "The following tables need to be upgraded:\n"
        sMesg += "\n".join(aLowerTables)
        iRes = do_complaint_buttons(sMesg, Gtk.MessageType.ERROR,
                                    ("_Quit", Gtk.ResponseType.CLOSE,
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
                if iRes == Gtk.ResponseType.OK:
                    return self._do_commit_db(oLogHandler, oTempConn,
                                              aMessages)
                if iRes == 1:
                    # Try running with the upgraded database
                    sqlhub.processConnection = oTempConn
                    # Ensure adapters are correctly updated
                    flush_cache()
                    return True
            else:
                sMesg = "Unable to create memory copy!\nUpgrade Failed."
                logging.warning('\n'.join([sMesg] + aMessages))
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
            if aMessages:
                sMesg += "Messages from commiting changes are:"
                for sStr in aMessages:
                    sMesg += '<b>%s</b>\n' % sStr
            else:
                sMesg += "Everything seems to have gone smoothly."
            do_info_message(sMesg)
            return True
        sMesg = ("Unable to commit updated database!\nUpgrade Failed.\n"
                 "Your database may be in an inconsistent state.")
        logging.warning('\n'.join([sMesg] + aMessages))
        do_complaint_error_details(sMesg, "\n".join(aMessages))
        return False
