# CountWWListCards.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>,
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Provide count card options for the WW card list"""

import gtk
from sutekh.core.SutekhObjects import PhysicalCard, IAbstractCard
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.gui.CardListModel import CardListModelListener
from sutekh.SutekhUtility import is_crypt_card
from sutekh.gui.plugins.CountCardSetCards import TOT_FORMAT, TOT_TOOLTIP, \
        TOTAL, CRYPT, LIB

SORT_COLUMN_OFFSET = 300  # ensure we don't clash with other extra columns


class CountWWListCards(SutekhPlugin, CardListModelListener):
    """Listen to changes on the card list views, and display a toolbar
       containing a label with a running count of the cards in the card
       set, the library cards and the crypt cards
       """
    dTableVersions = {PhysicalCard: (2,)}
    aModelsSupported = (PhysicalCard,)

    NO_COUNT, COUNT_CARDS, COUNT_EXP = range(3)

    COLUMN_NAME = '#'

    NO_COUNT_OPT = "Don't show card counts"
    COUNT_CARD_OPT = "Show counts for each distinct card"
    COUNT_EXP_OPT = "Show counts for each expansion"

    MODES = {
            NO_COUNT_OPT: NO_COUNT,
            COUNT_CARD_OPT: COUNT_CARDS,
            COUNT_EXP_OPT: COUNT_EXP,
            }

    OPTION_NAME = "White Wolf Card List Count Mode"

    OPTION_STR = ", ".join('"%s"' % sKey for sKey in sorted(MODES.keys()))

    dCardListConfig = {
        OPTION_NAME: 'option(%s, default="%s")' % (OPTION_STR, NO_COUNT_OPT),
    }

    # pylint: disable-msg=W0142
    # **magic OK here
    def __init__(self, *args, **kwargs):
        super(CountWWListCards, self).__init__(*args, **kwargs)

        self._oTextLabel = None
        self._iMode = self.NO_COUNT_OPT
        self._dExpCounts = {}
        self._dAbsCounts = {}
        self._dCardTotals = {TOTAL: 0, CRYPT: 0, LIB: 0}
        self._dExpTotals = {TOTAL: 0, CRYPT: 0, LIB: 0}

        # We only add listeners to windows we're going to display the toolbar
        # on
        if self.check_versions() and self.check_model_type():
            self.model.add_listener(self)
    # pylint: enable-msg=W0142

    def cleanup(self):
        """Remove the listener"""
        if self.check_versions() and self.check_model_type():
            self.model.remove_listener(self)
        super(CountWWListCards, self).cleanup()

    def _get_card_count(self, oAbsCard):
        """Get the count for the card for the current mode"""
        if self._iMode == self.COUNT_EXP:
            # We default if we're only showing the unspecified expansion
            return self._dExpCounts.get(oAbsCard, 0)
        else:
            return self._dAbsCounts[oAbsCard]

    def get_toolbar_widget(self):
        """Overrides method from base class."""
        if not self.check_versions() or not self.check_model_type():
            return None

        dInfo = {TOTAL: 0, CRYPT: 0, LIB: 0}
        self._oTextLabel = gtk.Label(TOT_FORMAT % dInfo)
        self._oTextLabel.set_tooltip_markup(TOT_TOOLTIP % dInfo)

        if self._iMode != self.NO_COUNT:
            self._oTextLabel.show()
        else:
            self._oTextLabel.hide()
        return self._oTextLabel

    def update_numbers(self):
        """Update the label"""
        # Timing issues mean that this can be called before text label has
        # been properly realised, so we need this guard case
        if self._oTextLabel:
            if self._iMode == self.NO_COUNT:
                self._oTextLabel.hide()
                return
            elif self._iMode == self.COUNT_CARDS:
                dInfo = self._dCardTotals
            else:
                dInfo = self._dExpTotals
            self._oTextLabel.set_markup(TOT_FORMAT % dInfo)
            self._oTextLabel.set_tooltip_markup(TOT_TOOLTIP % dInfo)
            self._oTextLabel.show()

    def load(self, aCards):
        """Listen on load events & update counts"""
        # The logic is a bit complicated, but it's intended that
        # filtering the WW cardlist on a card set will give sensible
        # results.
        self._dAbsCounts = {}
        self._dExpCounts = {}
        self._dCardTotals = {TOTAL: 0, CRYPT: 0, LIB: 0}
        self._dExpTotals = {TOTAL: 0, CRYPT: 0, LIB: 0}
        for oCard in aCards:
            oAbsCard = IAbstractCard(oCard)
            if oAbsCard not in self._dAbsCounts:
                self._dAbsCounts[oAbsCard] = 1
                iAbsCount = 1
            else:
                iAbsCount = 0
            if oCard.expansionID:
                # We don't count expansion ifno for cards with no expansion set
                iExpCount = 1
                if oAbsCard not in self._dExpCounts:
                    # First time we've seen this card
                    self._dExpCounts[oAbsCard] = 1
                else:
                    # Has an expansion, and by the nature of the list, this is
                    # a new expansion for the card we haven't seen before
                    self._dExpCounts[oAbsCard] += 1
            else:
                iExpCount = 0
            if is_crypt_card(oAbsCard):
                self._dExpTotals[CRYPT] += iExpCount
                self._dCardTotals[CRYPT] += iAbsCount
            else:
                self._dExpTotals[LIB] += iExpCount
                self._dCardTotals[LIB] += iAbsCount
            self._dCardTotals[TOTAL] += iAbsCount
            self._dExpTotals[TOTAL] += iExpCount
        self.update_numbers()

    def perpane_config_updated(self, _bDoReload=True):
        """Called by base class on config updates."""
        if self.check_versions() and self.check_model_type():
            sCountMode = self.get_perpane_item(self.OPTION_NAME)
            self._iMode = self.MODES.get(sCountMode, self.NO_COUNT)
            if self._iMode == self.NO_COUNT:
                self.clear_col()
            else:
                self.add_col()
            self.update_numbers()

    def _get_cols(self):
        """Get a list holding the column"""
        return [oCol for oCol in self.view.get_columns() if
                oCol.get_property("title") == self.COLUMN_NAME]

    def clear_col(self):
        """Remove the column if it's in use"""
        for oCol in self._get_cols():
            self.view.remove_column(oCol)

    def add_col(self):
        """Add the count col"""
        aCols = self._get_cols()
        if aCols:
            return  # column already there
        oCell = gtk.CellRendererText()
        oColumn = gtk.TreeViewColumn(self.COLUMN_NAME, oCell)
        oColumn.set_cell_data_func(oCell, self._render_count)
        oColumn.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        oColumn.set_fixed_width(40)
        oColumn.set_resizable(True)
        self.view.insert_column(oColumn, 0)
        oColumn.set_sort_column_id(SORT_COLUMN_OFFSET)
        self.model.set_sort_func(SORT_COLUMN_OFFSET, self._sort_count)

    def _get_count(self, oIter):
        """Get the count for this iter"""
        if self.model.iter_depth(oIter) == 0:
            # Group level item, so need to total counts for all subiters
            iTot = 0
            oSubIter = self.model.iter_children(oIter)
            while oSubIter:
                iTot += self._get_count(oSubIter)
                oSubIter = self.model.iter_next(oSubIter)
            return iTot
        elif self.model.iter_depth(oIter) == 1:
            oAbsCard = self.model.get_abstract_card_from_iter(oIter)
            return self._get_card_count(oAbsCard)
        elif self.model.iter_depth(oIter) == 2 and \
                self._iMode == self.COUNT_EXP:
            oPhysCard = self.model.get_physical_card_from_iter(oIter)
            if oPhysCard.expansionID:
                return 1
        return 0

    def _render_count(self, _oColumn, oCell, _oModel, oIter):
        """Render the count for the card"""
        iVal = self._get_count(oIter)
        oCell.set_property('text', iVal)

    def _sort_count(self, _oModel, oIter1, oIter2):
        """Card count Comparision of oIter1 and oIter2.

           Return -1 if oIter1 < oIter, 0 in ==, 1 if >
           """
        iVal1 = self._get_count(oIter1)
        iVal2 = self._get_count(oIter2)
        if iVal1 < iVal2:
            return -1
        elif iVal1 > iVal2:
            return 1
        else:
            # Values agree, so do fall back sort
            return self.model.sort_equal_iters(oIter1, oIter2)


plugin = CountWWListCards
