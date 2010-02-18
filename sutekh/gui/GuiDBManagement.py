# GuiDBManagement.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmil.com>
# GPL - see COPYING for details
"""This handles the gui aspects of upgrading the database."""

import gtk
from sqlobject import sqlhub, connectionForURI
from sutekh.gui.DBUpgradeDialog import DBUpgradeDialog
from sutekh.gui.WWFilesDialog import WWFilesDialog
from sutekh.gui.ProgressDialog import ProgressDialog, SutekhHTMLLogHandler, \
        SutekhCountLogHandler
from sutekh.core.DatabaseUpgrade import create_memory_copy, \
        create_final_copy, UnknownVersion, copy_to_new_abstract_card_db
from sutekh.gui.SutekhDialog import do_complaint_buttons, do_complaint_error, \
        do_complaint, do_complaint_warning
from sutekh.io.ZipFileWrapper import ZipFileWrapper
from sutekh.io.WwFile import WwFile
from sutekh.core.SutekhObjects import aObjectList, PhysicalCardSet
from sutekh.SutekhUtility import refresh_tables, read_rulings, \
        read_white_wolf_list


def read_cardlist(oCardList, oProgressDialog, oLogHandler):
    """Read the WW Card list into the database"""
    oProgressDialog.set_description("Reading White Wolf Card List")
    oProgressDialog.show()
    read_white_wolf_list(oCardList, oLogHandler)
    oProgressDialog.set_complete()

def read_ww_rulings(oRulings, oProgressDialog, oLogHandler):
    """Read the WW Rulings file into the database"""
    oProgressDialog.set_description("Reading White Wolf Rulings")
    oProgressDialog.reset()
    read_rulings(oRulings, oLogHandler)
    oProgressDialog.set_complete()

def read_ww_lists_into_db(aCLFile, oRulingsFile, oProgressDialog):
    """Read WW card list and possibly rulings into the given database"""
    refresh_tables(aObjectList, sqlhub.processConnection)
    oProgressDialog.reset()
    # WhiteWolf Parser uses sqlhub connection
    oLogHandler = SutekhHTMLLogHandler()
    oLogHandler.set_dialog(oProgressDialog)
    read_cardlist(aCLFile, oProgressDialog, oLogHandler)
    if oRulingsFile:
        read_ww_rulings(oRulingsFile, oProgressDialog,  oLogHandler)

def copy_to_new_db(oOldConn, oTempConn, oWin, oProgressDialog, oLogHandler):
    """Copy card collection and card sets to a new abstract card db."""
    oProgressDialog.set_description("Reloading card collection and card sets")
    oProgressDialog.reset()
    (bOK, aErrors) = copy_to_new_abstract_card_db(oOldConn, oTempConn,
            oWin.cardLookup, oLogHandler)
    oProgressDialog.set_complete()
    if not bOK:
        sMesg = "\n".join (["There was a problem copying your collection"
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
    """Initailize the database if it doesn't exist"""
    iRes = do_complaint_buttons("The database doesn't seem to be properly"
            " initialised",
            gtk.MESSAGE_ERROR, (gtk.STOCK_QUIT, gtk.RESPONSE_CLOSE,
                "Initialise database with cardlist and rulings?", 1))
    # pylint: disable-msg=W0612
    # sIgnore is ignored here
    if iRes != 1:
        return False
    else:
        aCLFile, oRulingsFile, sIgnore = _get_names(oParent)
        if aCLFile is not None:
            oProgressDialog = ProgressDialog()
            read_ww_lists_into_db(aCLFile, oRulingsFile, oProgressDialog)
            oProgressDialog.destroy()
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

def _get_names(oWin):
    """Get the names from the user, and ready them for the import."""
    oWWFilesDialog = WWFilesDialog(oWin)
    oWWFilesDialog.run()
    (sCLFileName, bCLIsUrl, sRulingsFileName, bRulingsIsUrl,
            sBackupFile) = oWWFilesDialog.get_names()
    oWWFilesDialog.destroy()
    if sCLFileName is not None:
        if isinstance(sCLFileName, list):
            aCLFile = [WwFile(x, bUrl=bCLIsUrl) for x in sCLFileName]
        else:
            aCLFile = [WwFile(sCLFileName, bUrl=bCLIsUrl)]
    else:
        aCLFile = None
    if sRulingsFileName is not None:
        oRulingsFile = WwFile(sRulingsFileName, bUrl=bRulingsIsUrl)
    else:
        oRulingsFile = None
    return aCLFile, oRulingsFile, sBackupFile

def refresh_ww_card_list(oWin):
    """Handle grunt work of refreshing the card lists"""
    aEditable = oWin.get_editable_panes()
    aCLFile, oRulingsFile, sBackupFile = _get_names(oWin)
    if not aCLFile:
        return False # Nothing happened
    oProgressDialog = ProgressDialog()
    if sBackupFile is not None:
        # pylint: disable-msg=W0703
        # we do want to catch all exceptions here
        try:
            save_backup(sBackupFile, oProgressDialog)
        except Exception, oErr:
            do_complaint_error("Failed to write backup.\n\n%s\n"
                    "Not touching the database further." % oErr)
            return False
    oOldConn = sqlhub.processConnection
    oTempConn = connectionForURI("sqlite:///:memory:")
    sqlhub.processConnection = oTempConn
    read_ww_lists_into_db(aCLFile, oRulingsFile, oProgressDialog)
    # Refresh abstract card view for card lookups
    oLogHandler = SutekhCountLogHandler()
    oLogHandler.set_dialog(oProgressDialog)
    sqlhub.processConnection = oOldConn
    if not copy_to_new_db(oOldConn, oTempConn, oWin, oProgressDialog,
            oLogHandler):
        oProgressDialog.destroy()
        return True # Force refresh
    # OK, update complete, copy back from oTempConn
    sqlhub.processConnection = oOldConn
    oWin.clear_cache() # Don't hold old copies
    oProgressDialog.set_description("Finalizing import")
    oProgressDialog.reset()
    oProgressDialog.show()
    (bOK, aErrors) = create_final_copy(oTempConn, oLogHandler)
    if not bOK:
        sMesg = "There was a problem updating the database\n"
        for sStr in aErrors:
            sMesg += sStr + "\n"
        sMesg += "Your database may be in an inconsistent state -" \
                " sorry"
        do_complaint_error(sMesg)
    else:
        sMesg = "Import Completed\n"
        sMesg += "Everything seems to have gone OK"
        do_complaint(sMesg, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, True)
    oProgressDialog.destroy()
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
            sMesg = '\n'.join(["Unable to create memory copy!"] +
                    aMessages + ["Upgrade Failed."])
            do_complaint_error(sMesg)
    except UnknownVersion, oErr:
        oProgressDialog.destroy()
        do_complaint_error("Upgrade Failed. " + str(oErr))
    return False

def _do_commit_db(oLogHandler, oTempConn):
    """Handle commiting the memory copy to the actual DB"""
    oProgressDialog = ProgressDialog()
    oProgressDialog.set_description("Commiting changes")
    oLogHandler.set_dialog(oProgressDialog)
    (bOK, aMessages) = create_final_copy(oTempConn, oLogHandler)
    oProgressDialog.destroy()
    if bOK:
        sMesg = "Changes Commited\n"
        if len(aMessages)>0:
            sMesg += '\n'.join(["Messages reported are:"] +
                    aMessages)
        else:
            sMesg += "Everything seems to have gone smoothly."
        do_complaint(sMesg, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, True)
        return True
    else:
        sMesg = '\n'.join(["Unable to commit updated database!"] +
                aMessages +
                ["Upgrade Failed.", "Your database may be"
                    " in an inconsistent state."])
        do_complaint_error(sMesg)
        return False
