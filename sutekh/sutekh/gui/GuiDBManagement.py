# GuiDBManagement.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmil.com>
# GPL - see COPYING for details
"""
This handles the gui aspects of upgrading the database.
"""

import gtk
from sqlobject import sqlhub, connectionForURI
from sutekh.gui.DBUpgradeDialog import DBUpgradeDialog
from sutekh.gui.WWFilesDialog import WWFilesDialog
from sutekh.gui.ProgressDialog import ProgressDialog, SutekhHTMLLogHandler, \
        SutekhCountLogHandler
from sutekh.core.DatabaseUpgrade import create_memory_copy, create_final_copy, \
        UnknownVersion, copy_to_new_AbstractCardDB
from sutekh.gui.SutekhDialog import do_complaint_buttons, do_complaint_error, \
        do_complaint, do_complaint_warning
from sutekh.io.ZipFileWrapper import ZipFileWrapper
from sutekh.io.WwFile import WwFile
from sutekh.core.SutekhObjects import ObjectList
from sutekh.SutekhUtility import refresh_tables, read_rulings, read_white_wolf_list


def read_cardlist(oCardList, oProgressDialog, oLogHandler):
    oProgressDialog.set_description("Reading WW Cardlist")
    oProgressDialog.show()
    read_white_wolf_list(oCardList, oLogHandler)
    oProgressDialog.set_complete()

def read_ww_rulings(oRulings, oProgressDialog, oLogHandler):
    oProgressDialog.reset()
    oProgressDialog.set_description("Reading WW Rulings List")
    read_rulings(oRulings, oLogHandler)
    oProgressDialog.set_complete()

def copy_to_new_db(oOldConn, oTempConn, oWin, oProgressDialog, oLogHandler):
    oProgressDialog.reset()
    oProgressDialog.set_description("Reloading card list and card sets")
    (bOK, aErrors) = copy_to_new_AbstractCardDB(oOldConn, oTempConn, oWin.cardLookup, oLogHandler)
    oProgressDialog.set_complete()
    if not bOK:
        sMesg = "\n".join (["There was a problem copying the cardlist to the new database"] +
                aErrors +
                ["Attempt to Continue Anyway (This is quite possibly dangerous)?"])
        iResponse = do_complaint_warning(sMesg)
        if iResponse == gtk.RESPONSE_OK:
            return True
        else:
            return False
    return True

def initialize_db():
    """Initailize the database if it doesn't exist"""
    iRes = do_complaint_buttons("The database doesn't seem to be properly initialised",
            gtk.MESSAGE_ERROR, (gtk.STOCK_QUIT, gtk.RESPONSE_CLOSE,
                "Initialise database with cardlist and rulings?", 1))
    if iRes != 1:
        return False
    else:
        oDialog = WWFilesDialog(None)
        oDialog.run()
        (sCLFileName, bCLIsUrl, sRulingsFileName, bRulingsIsUrl, sIgnore) = oDialog.getNames()
        oDialog.destroy()
        if sCLFileName is not None:
            refresh_tables(ObjectList, sqlhub.processConnection)
            oLogHandler = SutekhHTMLLogHandler()
            oProgressDialog = ProgressDialog()
            oLogHandler.set_dialog(oProgressDialog)
            oCLFile = WwFile(sCLFileName, bUrl=bCLIsUrl)
            read_cardlist(oCLFile, oProgressDialog, oLogHandler)
            if sRulingsFileName is not None:
                oRulingsFile = WwFile(sRulingsFileName, bUrl=bRulingsIsUrl)
                read_ww_rulings(oRulingsFile, oProgressDialog,  oLogHandler)
            oProgressDialog.destroy()
        else:
            return False
    return True

def refresh_WW_card_list(oWin):
    """Handle grunt work of refreshing the card lists"""
    oWWFilesDialog = WWFilesDialog(oWin)
    oWWFilesDialog.run()
    (sCLFileName, bCLIsUrl, sRulingsFileName, bRulingsIsUrl, sBackupFile) = oWWFilesDialog.getNames()
    oWWFilesDialog.destroy()
    if sCLFileName is not None:
        oProgressDialog = ProgressDialog()
        if sBackupFile is not None:
            try:
                oLogHandler = SutekhCountLogHandler()
                oProgressDialog.set_description("Saving backup")
                oLogHandler.set_dialog(oProgressDialog)
                oProgressDialog.show()
                oFile = ZipFileWrapper(sBackupFile)
                oFile.doDumpAllToZip(oLogHandler)
                oProgressDialog.set_complete()
            except Exception, oErr:
                sMsg = "Failed to write backup.\n\n" + str(oErr) \
                    + "\nNot touching the database further"
                do_complaint_error(sMsg)
                return False
        oTempConn = connectionForURI("sqlite:///:memory:")
        oOldConn = sqlhub.processConnection
        refresh_tables(ObjectList, oTempConn)
        oProgressDialog.reset()
        # WhiteWolf Parser uses sqlhub connection
        sqlhub.processConnection = oTempConn
        oLogHandler = SutekhHTMLLogHandler()
        oLogHandler.set_dialog(oProgressDialog)
        oCLFile = WwFile(sCLFileName, bUrl=bCLIsUrl)
        read_cardlist(oCLFile, oProgressDialog, oLogHandler)
        if sRulingsFileName is not None:
                oRulingsFile = WwFile(sRulingsFileName, bUrl=bRulingsIsUrl)
                read_ww_rulings(oRulingsFile, oProgressDialog,  oLogHandler)
        bCont = False
        # Refresh abstract card view for card lookups
        oWin.reload_all()
        oLogHandler = SutekhCountLogHandler()
        oLogHandler.set_dialog(oProgressDialog)
        if copy_to_new_db(oOldConn, oTempConn, oWin, oProgressDialog, oLogHandler):
            bCont = True
        # OK, update complete, copy back from oTempConn
        sqlhub.processConnection = oOldConn
        if bCont:
            oProgressDialog.reset()
            oProgressDialog.set_description("Finalizing import")
            oProgressDialog.show()
            (bOK, aErrors) = create_final_copy(oTempConn, oLogHandler)
            if not bOK:
                sMesg = "There was a problem updating the database\n"
                for sStr in aErrors:
                    sMesg += sStr + "\n"
                sMesg += "Your database may be in an inconsistent state - sorry"
                do_complaint_error(sMesg)
            else:
                sMesg = "Import Completed\n"
                sMesg += "Eveything seems to have gone OK"
                do_complaint_error(sMesg)
        oProgressDialog.destroy()
        return True

def do_db_upgrade(aBadTables):
    """Attempt to upgrade the database"""
    sMesg = "Database version error. Cannot continue\n" \
            "The following tables need to be upgraded:\n"
    sMesg += "\n".join(aBadTables)
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
        oProgressDialog.set_description("Creating temprary copy")
        (bOK, aMessages) = create_memory_copy(oTempConn, oLogHandler)
        oProgressDialog.destroy()
        if bOK:
            oDialog = DBUpgradeDialog(aMessages)
            iRes = oDialog.run()
            oDialog.destroy()
            if iRes == gtk.RESPONSE_OK:
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
                            ["Upgrade Failed.", "Your database may be in an inconsistent state."])
                    return False
            elif iRes == 1:
                # Try running with the upgraded database
                sqlhub.processConnection = oTempConn
                return True
            else:
                return False
        else:
            sMesg = '\n'.join(["Unable to create memory copy!"] +
                    aMessages + ["Upgrade Failed."])
            do_complaint_error(sMesg)
            return False
    except UnknownVersion, oErr:
        oProgressDialog.destroy()
        do_complaint_error("Upgrade Failed. " + str(oErr))
        return False
