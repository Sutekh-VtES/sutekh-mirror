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
                              EXP_DATE_URL, LOOKUP_DATA_URL,
                              WW_CARDLIST_DATAPACK)
from sutekh.io.DataPack import find_data_pack
from sutekh.SutekhUtility import (read_rulings, read_white_wolf_list,
                                  read_exp_info_file, read_lookup_data,
                                  find_base_vampire, is_crypt_card,
                                  is_vampire)


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
                                 sUrl=EXP_DATE_URL,
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


def check_ally_keywords(aKeywords, sKeywordType, sName):
    """Check if we have the correct keywords in the list.

       We return a list, so we can use .extend on the result."""
    for sKeyword in aKeywords:
        if sKeyword.endswith(sKeywordType):
            # Found it, so no messages
            return []
    # Return a message
    return ["%s (ally) is missing %s keyword" % (sName, sKeywordType)]


class GuiDBManager(BaseGuiDBManager):
    """Handle the GUI aspects of upgrading the database or reloading the
       card lists."""

    cZipFileWrapper = ZipFileWrapper

    aTables = TABLE_LIST

    bDisplayZip = True

    tReaders = (LOOKUP_DATA_READER, CARD_LIST_READER, EXTRA_CARD_READER,
                RULINGS_READER, EXP_DATA_READER)

    def __init__(self, oWin):
        super(GuiDBManager, self).__init__(oWin, DBUpgradeManager)

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
        """Spot check cards for consisency after importing a new card list.

           We check the following things:
           * Each card has a card type
           * Each vampire has a clan, a group and a capacity
           * Each advanced vampire has a base vampire
             (including storyline advanced vamps)
           * Each Imbued has a creed, a group and a life total
           * Each Ally has a life total, and the bleed and strength keywords.
           * Each retainer has a life total
        """
        aMessages = []
        sName = oAbsCard.name
        if not oAbsCard.cardtype:
            aMessages.append('%s has no Type' % sName)
            # We skip the other checks, as this is a badly broken card
            return aMessages
        if oAbsCard.cost is not None:
            if not oAbsCard.costtype:
                aMessages.append('%s has a cost, but no cost type' % sName)
        elif oAbsCard.costtype is not None:
            aMessages.append('%s has a costtype, but no cost' % sName)
        aTypes = [oT.name.lower() for oT in oAbsCard.cardtype]
        aKeywords = [oK.keyword for oK in oAbsCard.keywords]
        if 'retainer' in aTypes:
            if not oAbsCard.life:
                aMessages.append("%s (retainer) has no life" % sName)
        if 'ally' in aTypes:
            if not oAbsCard.life:
                aMessages.append("%s (ally) has no life" % sName)
            aMessages.extend(check_ally_keywords(aKeywords, 'strength', sName))
            aMessages.extend(check_ally_keywords(aKeywords, 'bleed', sName))

        if is_crypt_card(oAbsCard):
            # We don't check keywords for crypt cards, because the parser
            # always adds them, even if they're not parsed correctly
            if not oAbsCard.group:
                aMessages.append("%s is a crypt card with no group" % sName)
            if not is_vampire(oAbsCard):
                # Imbued checks
                if not oAbsCard.life:
                    aMessages.append("%s (imbued) has no life" % sName)
                if not oAbsCard.creed:
                    aMessages.append("%s (imbued) has no creed" % sName)
            else:
                # Vampire checks
                if not oAbsCard.clan:
                    aMessages.append("%s (vampire) has no clan" % sName)
                if not oAbsCard.capacity:
                    aMessages.append("%s (vampire) has no capacity" % sName)
                if oAbsCard.level:
                   oBase = find_base_vampire(oAbsCard)
                   if not oBase:
                       aMessages.append("Advanced vampire %s has no base"
                                        " vampire" % sName)
        return aMessages

    def initialize_db(self, oConfig):
        """Setup zip file url before calling the base class method"""
        self._get_zip_url()
        return super(GuiDBManager, self).initialize_db(oConfig)

    def refresh_card_list(self, oUpdateDate=None, dFiles=None):
        """Setup zip file before calling the base class method"""
        if not dFiles:
            self._get_zip_url()
        return super(GuiDBManager, self).refresh_card_list(oUpdateDate, dFiles)
