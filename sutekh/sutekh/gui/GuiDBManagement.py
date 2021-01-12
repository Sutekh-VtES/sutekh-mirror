# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""This handles the gui aspects of upgrading the database."""

from sutekh.base.gui.BaseGuiDBManagement import (BaseGuiDBManager,
                                                 DataFileReader)
from sutekh.base.gui.GuiDataPack import gui_error_handler
from sutekh.core.DatabaseUpgrade import DBUpgradeManager
from sutekh.core.SutekhTables import TABLE_LIST
from sutekh.io.ZipFileWrapper import ZipFileWrapper
from sutekh.io.WwUrls import (WW_CARDLIST_URL, WW_RULINGS_URL, EXTRA_CARD_URL,
                              EXP_DATA_URL, LOOKUP_DATA_URL,
                              WW_CARDLIST_DATAPACK)
from sutekh.io.DataPack import find_data_pack
from sutekh.SutekhUtility import (read_rulings, read_white_wolf_list,
                                  read_exp_info_file, read_lookup_data,
                                  do_card_checks)


CARD_LIST_READER = DataFileReader(sName="cardlist.txt",
                                  sUrl=WW_CARDLIST_URL,
                                  sDescription="Official Card List",
                                  tPattern=('TXT files', ['*.txt']),
                                  bRequired=True,
                                  bCountLogger=False,
                                  fReader=read_white_wolf_list,
                                 )

EXTRA_CARD_READER = DataFileReader(sName="extra_list.txt",
                                   sUrl=EXTRA_CARD_URL,
                                   sDescription="Additional Card List",
                                   tPattern=('TXT files', ['*.txt']),
                                   bRequired=False,
                                   bCountLogger=False,
                                   fReader=read_white_wolf_list,
                                  )

RULINGS_READER = DataFileReader(sName="rulings.html",
                                sUrl=WW_RULINGS_URL,
                                sDescription="Official Rulings File",
                                tPattern=('HTML files', ['*.html', '*htm']),
                                bRequired=False,
                                bCountLogger=False,
                                fReader=read_rulings,
                               )

EXP_DATA_READER = DataFileReader(sName="expansions.json",
                                 sUrl=EXP_DATA_URL,
                                 sDescription="Extra Expansion Information "
                                              "File",
                                 tPattern=('JSON files', ['*json']),
                                 bRequired=False,
                                 bCountLogger=True,
                                 fReader=read_exp_info_file,
                                )

LOOKUP_DATA_READER = DataFileReader(sName="lookup.csv",
                                    sUrl=LOOKUP_DATA_URL,
                                    sDescription="Lookup Data File",
                                    tPattern=('CSV files', ['*csv']),
                                    bRequired=True,
                                    bCountLogger=True,
                                    fReader=read_lookup_data,
                                   )


class GuiDBManager(BaseGuiDBManager):
    """Handle the GUI aspects of upgrading the database or reloading the
       card lists."""

    cZipFileWrapper = ZipFileWrapper

    aTables = TABLE_LIST

    bDisplayZip = True

    tReaders = (LOOKUP_DATA_READER, CARD_LIST_READER, EXTRA_CARD_READER,
                RULINGS_READER, EXP_DATA_READER)

    def __init__(self, oWin):
        super().__init__(oWin, DBUpgradeManager)

    def _get_zip_url(self):
        """Download the zip file details and set attributes accordingly"""
        # We do this before each call, to make sure we're pointing at
        # the right place.
        # We ignore the hash, because we can't be certain that the zip
        # file we read is the one in the url, since we allow people to
        # load one from file.
        sUrl, sHash = find_data_pack(WW_CARDLIST_DATAPACK,
                                     fErrorHandler=gui_error_handler)
        if not sUrl:
            self.sZippedUrl = None
            self.sHash = None
        else:
            self.sZippedUrl = sUrl
            self.sHash = sHash

    def _do_import_checks(self, oAbsCard):
        return do_card_checks(oAbsCard)

    def initialize_db(self, oConfig):
        """Setup zip file url before calling the base class method"""
        self._get_zip_url()
        return super().initialize_db(oConfig)

    def refresh_card_list(self, oUpdateDate=None, dFiles=None):
        """Setup zip file before calling the base class method"""
        if not dFiles:
            self._get_zip_url()
        return super().refresh_card_list(oUpdateDate, dFiles)
