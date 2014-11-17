# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""This handles the gui aspects of upgrading the database."""

from sqlobject import sqlhub
from sutekh.gui.WWFilesDialog import WWFilesDialog
from sutekh.base.gui.ProgressDialog import (SutekhHTMLLogHandler,
                                            SutekhCountLogHandler)
from sutekh.core.DatabaseUpgrade import DBUpgradeManager
from sutekh.io.ZipFileWrapper import ZipFileWrapper
from sutekh.base.io.EncodedFile import EncodedFile
from sutekh.core.SutekhObjects import TABLE_LIST
from sutekh.base.gui.BaseGuiDBManagement import wrapped_read, BaseGuiDBManager
from sutekh.SutekhUtility import (read_rulings, read_white_wolf_list,
                                  read_exp_date_list)
from sutekh.base.core.DBUtility import refresh_tables


class GuiDBManager(BaseGuiDBManager):
    """Handle the GUI aspects of upgrading the database or reloading the
       card lists."""

    cZipFileWrapper = ZipFileWrapper

    def __init__(self, oWin):
        super(GuiDBManager, self).__init__(oWin, DBUpgradeManager)

    def _read_data(self, aFiles, oProgressDialog):
        """Read relevant data files into the given database."""
        refresh_tables(TABLE_LIST, sqlhub.processConnection)
        oProgressDialog.reset()
        # WhiteWolf Parser uses sqlhub connection
        oLogHandler = SutekhHTMLLogHandler()
        oLogHandler.set_dialog(oProgressDialog)
        aCLFile, oExtraFile, aExpDateFiles, aRulingsFiles = aFiles
        wrapped_read(aCLFile, read_white_wolf_list,
                     "Reading White Wolf Card List", oProgressDialog,
                     oLogHandler)
        if oExtraFile:
            wrapped_read([oExtraFile], read_white_wolf_list,
                         "Reading Extra Card Info", oProgressDialog,
                         oLogHandler)
        if aExpDateFiles:
            oCountLogHandler = SutekhCountLogHandler()
            oCountLogHandler.set_dialog(oProgressDialog)
            wrapped_read(aExpDateFiles, read_exp_date_list,
                         "Reading Exp Date Info List", oProgressDialog,
                         oCountLogHandler)
        if aRulingsFiles:
            wrapped_read(aRulingsFiles, read_rulings,
                         "Reading White Wolf Rulings", oProgressDialog,
                         oLogHandler)

    def _get_names(self, bDisableBackup):
        """Get the names from the user, and ready them for the import."""
        oWWFilesDialog = WWFilesDialog(self._oWin, bDisableBackup)
        oWWFilesDialog.run()
        (sCLFileName, bCLIsUrl, sExtraFileName, bExtraIsUrl,
         sRulingsFileName, bRulingsIsUrl,
         sExpDateFileName, bExpDateIsUrl,
         sBackupFile) = oWWFilesDialog.get_names()
        oWWFilesDialog.destroy()
        if sCLFileName is not None:
            if isinstance(sCLFileName, list):
                aCLFile = [EncodedFile(x, bUrl=bCLIsUrl) for x in sCLFileName]
            else:
                aCLFile = [EncodedFile(sCLFileName, bUrl=bCLIsUrl)]
        else:
            # Bail out
            return None, sBackupFile
        if sExtraFileName is not None:
            oExtraFile = EncodedFile(sExtraFileName, bUrl=bExtraIsUrl)
        else:
            oExtraFile = None
        if sRulingsFileName is not None:
            if isinstance(sRulingsFileName, list):
                aRulingsFiles = [EncodedFile(x, bUrl=bRulingsIsUrl) for x in
                                 sRulingsFileName]
            else:
                aRulingsFiles = [EncodedFile(sRulingsFileName,
                                             bUrl=bRulingsIsUrl)]
        else:
            aRulingsFiles = None
        if sExpDateFileName is not None:
            if isinstance(sExpDateFileName, list):
                aExpDateFiles = [EncodedFile(x, bUrl=bExpDateIsUrl) for x in
                                 sExpDateFileName]
            else:
                aExpDateFiles = [EncodedFile(sExpDateFileName,
                                             bUrl=bExpDateIsUrl)]
        else:
            aExpDateFiles = None

        return [aCLFile, oExtraFile, aExpDateFiles, aRulingsFiles], sBackupFile
