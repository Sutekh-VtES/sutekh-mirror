# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>,
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Provide count card options for the WW card list"""

from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.SutekhUtility import is_crypt_card
from sutekh.base.gui.plugins.BaseCardListCount import BaseCardListCount
from sutekh.gui.plugins.CountCardSetCards import FORMAT, TOOLTIP, CRYPT, LIB

SORT_COLUMN_OFFSET = 300  # ensure we don't clash with other extra columns


class CountWWListCards(SutekhPlugin, BaseCardListCount):
    """Listen to changes on the card list views, and display a toolbar
       containing a label with a running count of the cards in the card
       set, the library cards and the crypt cards
       """

    TOT_FORMAT = FORMAT
    TOT_TOOLTIP = TOOLTIP

    # We override the default config option so we don't break existing
    # configs
    OPTION_NAME = 'White Wolf Card List Count Mode'

    dCardListConfig = {
        OPTION_NAME: 'option(%s, default="%s")' % (
            BaseCardListCount.OPTION_STR, BaseCardListCount.NO_COUNT_OPT),
    }

    def _get_card_keys(self, oAbsCard):
        """Listen on load events & update counts"""
        if is_crypt_card(oAbsCard):
            return [CRYPT]
        return [LIB]

    def _add_dict_keys(self):
        """Add 'crypt' and 'library' to the correct dicts"""
        self._dCardTotals[CRYPT] = 0
        self._dCardTotals[LIB] = 0
        self._dExpTotals[CRYPT] = 0
        self._dExpTotals[LIB] = 0


plugin = CountWWListCards
