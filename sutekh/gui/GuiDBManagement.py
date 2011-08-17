# GuiDBManagement.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmil.com>
# GPL - see COPYING for details
"""This handles the gui aspects of upgrading the database."""

import gtk
import logging
from sqlobject import sqlhub, connectionForURI
from sutekh.gui.DBUpgradeDialog import DBUpgradeDialog
from sutekh.gui.WWFilesDialog import WWFilesDialog
from sutekh.gui.ProgressDialog import ProgressDialog, SutekhHTMLLogHandler, \
        SutekhCountLogHandler
from sutekh.core.DatabaseUpgrade import create_memory_copy, \
        create_final_copy, UnknownVersion, copy_to_new_abstract_card_db
from sutekh.gui.SutekhDialog import do_complaint_buttons, do_complaint, \
        do_complaint_warning, do_exception_complaint, \
        do_complaint_error_details
from sutekh.io.ZipFileWrapper import ZipFileWrapper
from sutekh.io.WwFile import WwFile
from sutekh.core.SutekhObjects import TABLE_LIST, PhysicalCardSet
from sutekh.SutekhUtility import refresh_tables, read_rulings, \
        read_white_wolf_list, get_cs_id_name_table


def read_cardlist(oCardList, oProgressDialog, oLogHandler):
    """Read the WW Card list into the database"""
    oProgressDialog.set_description("Reading White Wolf Card List")
    oProgressDialog.show()
    read_white_wolf_list(oCardList, oLogHandler)
    oProgressDialog.set_complete()


def read_extra(oExtraFile, oProgressDialog, oLogHandler):
    """Read extra card info into the database"""
    oProgressDialog.set_description("Reading Extra Card Info")
    oProgressDialog.show()
    read_white_wolf_list(oExtraFile, oLogHandler)
    oProgressDialog.set_complete()


def read_ww_rulings(aRulingFiles, oProgressDialog, oLogHandler):
    """Read the WW Rulings file into the database"""
    oProgressDialog.set_description("Reading White Wolf Rulings")
    oProgressDialog.reset()
    read_rulings(aRulingFiles, oLogHandler)
    oProgressDialog.set_complete()


def read_ww_lists_into_db(aCLFile, oExtraFile, aRulingsFiles, oProgressDialog):
    """Read WW card list and possibly rulings into the given database"""
    refresh_tables(TABLE_LIST, sqlhub.processConnection)
    oProgressDialog.reset()
    # WhiteWolf Parser uses sqlhub connection
    oLogHandler = SutekhHTMLLogHandler()
    oLogHandler.set_dialog(oProgressDialog)
    read_cardlist(aCLFile, oProgressDialog, oLogHandler)
    if oExtraFile:
        read_extra([oExtraFile], oProgressDialog, oLogHandler)
    if aRulingsFiles:
        read_ww_rulings(aRulingsFiles, oProgressDialog,  oLogHandler)


def copy_to_new_db(oOldConn, oTempConn, oWin, oProgressDialog, oLogHandler):
    """Copy card collection and card sets to a new abstract card db."""
    oProgressDialog.set_description("Reloading card collection and card sets")
    oProgressDialog.reset()
    (bOK, aErrors) = copy_to_new_abstract_card_db(oOldConn, oTempConn,
            oWin.cardLookup, oLogHandler)
    oProgressDialog.set_complete()
    if not bOK:
        sMesg = "\n".join(["There was a problem copying your collection"
            " to the new database"] + aErrors +
                ["Attempt to Continue Anyway (This is most probably"
                    " very dangerous)?"])
        iResponse = do_complaint_warning(sMesg)
        if iResponse == gtk.RESPONSE_OK:
            return True
        else:
            return False
    return True


def initialize_db(oParent):
    """Initialise the database if it doesn't exist"""
    iRes = do_complaint_buttons("The database doesn't seem to be properly"
            " initialised",
            gtk.MESSAGE_ERROR, (gtk.STOCK_QUIT, gtk.RESPONSE_CLOSE,
                "Initialise database with cardlist and rulings?", 1))
    if iRes != 1:
        return False
    else:
        aCLFile, oExtraFile, aRulingsFiles, _sIgnore = _get_names(oParent,
                True)
        if aCLFile is not None:
            oProgressDialog = ProgressDialog()
            try:
                read_ww_lists_into_db(aCLFile, oExtraFile, aRulingsFiles,
                        oProgressDialog)
                oProgressDialog.destroy()
            except IOError, oErr:
                do_exception_complaint("Failed to read cardlists.\n\n%s\n"
                        "Aborting import." % oErr)
                oProgressDialog.destroy()
                return False
        else:
            return False
    # Create the Physical Card Collection card set
    PhysicalCardSet(name='My Collection', parent=None)
    return True


def save_backup(sBackupFile, oProgressDialog):
    """Save a backup file, showing a progress dialog"""
    oLogHandler = SutekhCountLogHandler()
    oProgressDialog.set_description("Saving backup")
    oLogHandler.set_dialog(oProgressDialog)
    oProgressDialog.show()
    oFile = ZipFileWrapper(sBackupFile)
    oFile.do_dump_all_to_zip(oLogHandler)
    oProgressDialog.set_complete()


def _get_names(oWin, bDisableBackup):
    """Get the names from the user, and ready them for the import."""
    oWWFilesDialog = WWFilesDialog(oWin, bDisableBackup)
    oWWFilesDialog.run()
    (sCLFileName, bCLIsUrl, sExtraFileName, bExtraIsUrl,
            sRulingsFileName, bRulingsIsUrl,
            sBackupFile) = oWWFilesDialog.get_names()
    oWWFilesDialog.destroy()
    if sCLFileName is not None:
        if isinstance(sCLFileName, list):
            aCLFile = [WwFile(x, bUrl=bCLIsUrl) for x in sCLFileName]
        else:
            aCLFile = [WwFile(sCLFileName, bUrl=bCLIsUrl)]
    else:
        aCLFile = None
    if sExtraFileName is not None:
        oExtraFile = WwFile(sExtraFileName, bUrl=bExtraIsUrl)
    else:
        oExtraFile = None
    if sRulingsFileName is not None:
        if isinstance(sRulingsFileName, list):
            aRulingsFiles = [WwFile(x, bUrl=bRulingsIsUrl) for x in
                    sRulingsFileName]
        else:
            aRulingsFiles = [WwFile(sRulingsFileName, bUrl=bRulingsIsUrl)]
    else:
        aRulingsFiles = None
    return aCLFile, oExtraFile, aRulingsFiles, sBackupFile


def refresh_ww_card_list(oWin):
    """Handle grunt work of refreshing the card lists"""
    # pylint: disable-msg=R0914
    # We're juggling lots of different bits of start, so we use a lot
    # of variables
    aEditable = oWin.get_editable_panes()
    dOldMap = get_cs_id_name_table()
    aCLFile, oExtraFile, oRulingsFile, sBackupFile = _get_names(oWin, False)
    if not aCLFile:
        return False  # Nothing happened
    oProgressDialog = ProgressDialog()
    if sBackupFile is not None:
        # pylint: disable-msg=W0703
        # we do want to catch all exceptions here
        try:
            save_backup(sBackupFile, oProgressDialog)
        except Exception, oErr:
            do_exception_complaint("Failed to write backup.\n\n%s\n"
                    "Not touching the database further." % oErr)
            return False
    oOldConn = sqlhub.processConnection
    oTempConn = connectionForURI("sqlite:///:memory:")
    sqlhub.processConnection = oTempConn
    try:
        read_ww_lists_into_db(aCLFile, oExtraFile, oRulingsFile,
            oProgressDialog)
    except IOError, oErr:
        # Failed to read one of the card lists, so celan up and abort
        do_exception_complaint("Failed to read cardlists.\n\n%s\n"
                    "Aborting import." % oErr)
        oProgressDialog.destroy()
        return False
    # Refresh abstract card view for card lookups
    oLogHandler = SutekhCountLogHandler()
    oLogHandler.set_dialog(oProgressDialog)
    sqlhub.processConnection = oOldConn
    if not copy_to_new_db(oOldConn, oTempConn, oWin, oProgressDialog,
            oLogHandler):
        oProgressDialog.destroy()
        return True  # Force refresh
    # OK, update complete, copy back from oTempConn
    sqlhub.processConnection = oOldConn
    oWin.clear_cache()  # Don't hold old copies
    oProgressDialog.set_description("Finalizing import")
    oProgressDialog.reset()
    oProgressDialog.show()
    (bOK, aErrors) = create_final_copy(oTempConn, oLogHandler)
    if not bOK:
        sMesg = "There was a problem updating the database\n" \
                "Your database may be in an inconsistent state -" \
                " sorry"
        logging.warn('\n'.join([sMesg] + aErrors))
        do_complaint_error_details(sMesg, "\n".join(aErrors))
    else:
        sMesg = "Import Completed\n"
        sMesg += "Everything seems to have gone OK"
        do_complaint(sMesg, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, True)
    oProgressDialog.destroy()
    dNewMap = get_cs_id_name_table()
    oWin.config_file.fix_profile_mapping(dOldMap, dNewMap)
    oWin.update_to_new_db()
    oWin.restore_editable_panes(aEditable)
    return True


def do_db_upgrade(aLowerTables, aHigherTables):
    """Attempt to upgrade the database"""
    if len(aHigherTables) > 0:
        sMesg = "Database version error. Cannot continue\n" \
                "The following tables have a higher version than expected:\n"
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
        (bOK, aMessages) = create_memory_copy(oTempConn, oLogHandler)
        oProgressDialog.destroy()
        if bOK:
            oDialog = DBUpgradeDialog(aMessages)
            iRes = oDialog.run()
            oDialog.destroy()
            if iRes == gtk.RESPONSE_OK:
                return _do_commit_db(oLogHandler, oTempConn)
            elif iRes == 1:
                # Try running with the upgraded database
                sqlhub.processConnection = oTempConn
                return True
        else:
            sMesg = "Unable to create memory copy!\nUpgrade Failed."
            logging.warn('\n'.join([sMesg] + aMessages))
            do_complaint_error_details(sMesg, "\n".join(aMessages))
    except UnknownVersion, oErr:
        oProgressDialog.destroy()
        do_exception_complaint("Upgrade Failed. %s" % oErr)
    return False


def _do_commit_db(oLogHandler, oTempConn):
    """Handle committing the memory copy to the actual DB"""
    oProgressDialog = ProgressDialog()
    oProgressDialog.set_description("Commiting changes")
    oLogHandler.set_dialog(oProgressDialog)
    (bOK, aMessages) = create_final_copy(oTempConn, oLogHandler)
    oProgressDialog.destroy()
    if bOK:
        sMesg = "Changes Commited\n"
        if len(aMessages) > 0:
            sMesg += '\n'.join(["Messages reported are:"] +
                    aMessages)
        else:
            sMesg += "Everything seems to have gone smoothly."
        do_complaint(sMesg, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, True)
        return True
    else:
        sMesg = "Unable to commit updated database!\nUpgrade Failed.\n" \
                "Your database may be in an inconsistent state."
        logging.warn('\n'.join([sMesg] + aMessages))
        do_complaint_error_details(sMesg, "\n".join(aMessages))
        return False
