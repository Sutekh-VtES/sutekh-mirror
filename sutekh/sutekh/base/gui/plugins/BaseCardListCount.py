# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>,
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Provide count card options for the full card list"""
import enum

from gi.repository import Gtk
from ...core.BaseTables import PhysicalCard
from ...core.BaseAdapters import IAbstractCard
from ..BasePluginManager import BasePlugin
from ..MessageBus import MessageBus
from .BaseCountCSCards import TOTAL

SORT_COLUMN_OFFSET = 300  # ensure we don't clash with other extra columns


class BaseCardListCount(BasePlugin):
    """Listen to changes on the card list views, and display a toolbar
       containing a label with a running count of the cards in the list.
       """
    dTableVersions = {PhysicalCard: (2, 3, )}
    aModelsSupported = (PhysicalCard,)

    @enum.unique
    class Modes(enum.Enum):
        """Counting modes"""
        NO_COUNT = 1
        COUNT_CARDS = 2
        COUNT_EXP = 3

    COLUMN_NAME = '#'

    NO_COUNT_OPT = "Don't show card counts"
    COUNT_CARD_OPT = "Show counts for each distinct card"
    COUNT_EXP_OPT = "Show counts for each expansion"

    MODES = {
        NO_COUNT_OPT: Modes.NO_COUNT,
        COUNT_CARD_OPT: Modes.COUNT_CARDS,
        COUNT_EXP_OPT: Modes.COUNT_EXP,
    }

    OPTION_NAME = "Full Card List Count Mode"

    OPTION_STR = ", ".join('"%s"' % sKey for sKey in sorted(MODES.keys()))

    dCardListConfig = {
        OPTION_NAME: 'option(%s, default="%s")' % (OPTION_STR, NO_COUNT_OPT),
    }

    TOT_FORMAT = ''
    TOT_TOOLTIP = ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._oTextLabel = None
        self._eMode = self.Modes.NO_COUNT
        self._dExpCounts = {}
        self._dAbsCounts = {}
        self._dCardTotals = {TOTAL: 0}
        self._dExpTotals = {TOTAL: 0}
        self._add_dict_keys()

        # We only add listeners to windows we're going to display the toolbar
        # on
        MessageBus.subscribe(self.model, 'load', self.load)
        self.perpane_config_updated()

    def cleanup(self):
        """Remove the listener"""
        MessageBus.unsubscribe(self.model, 'load', self.load)
        super().cleanup()

    def _get_card_count(self, oAbsCard):
        """Get the count for the card for the current mode"""
        if self._eMode == self.Modes.COUNT_EXP:
            # We default if we're only showing the unspecified expansion
            return self._dExpCounts.get(oAbsCard, 0)
        return self._dAbsCounts[oAbsCard]

    def get_toolbar_widget(self):
        """Overrides method from base class."""
        if self._eMode == self.Modes.COUNT_CARDS:
            dInfo = self._dCardTotals
        else:
            dInfo = self._dExpTotals
        self._oTextLabel = Gtk.Label(label=self.TOT_FORMAT % dInfo)
        self._oTextLabel.set_tooltip_markup(self.TOT_TOOLTIP % dInfo)

        if self._eMode != self.Modes.NO_COUNT:
            self._oTextLabel.show()
        else:
            self._oTextLabel.hide()
        return self._oTextLabel

    def update_numbers(self):
        """Update the label"""
        # Timing issues mean that this can be called before text label has
        # been properly realised, so we need this guard case
        if self._oTextLabel:
            if self._eMode == self.Modes.NO_COUNT:
                self._oTextLabel.hide()
                return
            if self._eMode == self.Modes.COUNT_CARDS:
                dInfo = self._dCardTotals
            else:
                dInfo = self._dExpTotals
            self._oTextLabel.set_markup(self.TOT_FORMAT % dInfo)
            self._oTextLabel.set_tooltip_markup(self.TOT_TOOLTIP % dInfo)
            self._oTextLabel.show()

    def load(self, aCards):
        """Listen on load events & update counts"""
        # The logic is a bit complicated, but it's intended that
        # filtering the WW cardlist on a card set will give sensible
        # results.
        self._dAbsCounts = {}
        self._dExpCounts = {}
        self._dCardTotals = {TOTAL: 0}
        self._dExpTotals = {TOTAL: 0}
        self._add_dict_keys()
        for oCard in aCards:
            oAbsCard = IAbstractCard(oCard)
            if oAbsCard not in self._dAbsCounts:
                self._dAbsCounts[oAbsCard] = 1
                iAbsCount = 1
            else:
                iAbsCount = 0
            if oCard.printingID:
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
            aKeys = self._get_card_keys(oAbsCard)
            for sKey in aKeys:
                self._dCardTotals[sKey] += iAbsCount
                self._dExpTotals[sKey] += iExpCount
            self._dCardTotals[TOTAL] += iAbsCount
            self._dExpTotals[TOTAL] += iExpCount
        self.update_numbers()

    def perpane_config_updated(self, _bDoReload=True):
        """Called by base class on config updates."""
        sCountMode = self.get_perpane_item(self.OPTION_NAME)
        self._eMode = self.MODES.get(sCountMode, self.Modes.NO_COUNT)
        if self._eMode == self.Modes.NO_COUNT:
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
        oCell = Gtk.CellRendererText()
        oColumn = Gtk.TreeViewColumn(self.COLUMN_NAME, oCell)
        oColumn.set_cell_data_func(oCell, self._render_count)
        oColumn.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
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
        if self.model.iter_depth(oIter) == 1:
            oAbsCard = self.model.get_abstract_card_from_iter(oIter)
            return self._get_card_count(oAbsCard)
        if self.model.iter_depth(oIter) == 2 and \
                self._eMode == self.Modes.COUNT_EXP:
            oPhysCard = self.model.get_physical_card_from_iter(oIter)
            if oPhysCard.printingID:
                return 1
        return 0

    def _render_count(self, _oColumn, oCell, _oModel, oIter, _oDummy):
        """Render the count for the card"""
        iVal = self._get_count(oIter)
        oCell.set_property('text', '%d' % iVal)

    def _sort_count(self, _oModel, oIter1, oIter2):
        """Card count Comparision of oIter1 and oIter2.

           Return -1 if oIter1 < oIter, 0 in ==, 1 if >
           """
        iVal1 = self._get_count(oIter1)
        iVal2 = self._get_count(oIter2)
        if iVal1 < iVal2:
            return -1
        if iVal1 > iVal2:
            return 1
        # Values agree, so do fall back sort
        return self.model.sort_equal_iters(oIter1, oIter2)

    def _get_card_keys(self, oAbsCard):
        """Get the list of applicable dictionary keys for this card."""
        raise NotImplementedError('Subclasses must implement _get_card_keys')

    def _add_dict_keys(self):
        """Ensure the totals dictionary has all the required keys."""
        raise NotImplementedError('Subclasses must implement _add_dict_keys')
