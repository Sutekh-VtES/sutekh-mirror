# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>,
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Display a running total of the cards in a card set"""

from gi.repository import Gtk
from ...core.BaseTables import PhysicalCardSet
from ...core.BaseAdapters import IAbstractCard
from ..BasePluginManager import BasePlugin
from ..MessageBus import MessageBus

TOTAL = 'total'


class BaseCountCSCards(BasePlugin):
    """Listen to changes on the card list views, and display a toolbar
       containing a label with a running count of the cards in the card
       set.
       """
    dTableVersions = {PhysicalCardSet: (5, 6, 7)}
    aModelsSupported = (PhysicalCardSet,)

    # Subclasses should provide this
    TOT_FORMAT = ''
    TOT_TOOLTIP = ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.dInfo = {TOTAL: 0}
        self._add_dict_keys()
        self._oTextLabel = None

        MessageBus.subscribe(self.model, 'add_new_card', self.add_new_card)
        MessageBus.subscribe(self.model, 'alter_card_count',
                             self.alter_card_count)
        MessageBus.subscribe(self.model, 'load', self.load)

    def cleanup(self):
        """Remove the listener"""
        MessageBus.unsubscribe(self.model, 'add_new_card',
                               self.add_new_card)
        MessageBus.unsubscribe(self.model, 'alter_card_count',
                               self.alter_card_count)
        MessageBus.unsubscribe(self.model, 'load', self.load)
        super().cleanup()

    def get_toolbar_widget(self):
        """Overrides method from base class."""
        self._oTextLabel = Gtk.Label(label=self.TOT_FORMAT % self.dInfo)
        self._oTextLabel.set_tooltip_markup(self.TOT_TOOLTIP % self.dInfo)
        self._oTextLabel.show()
        return self._oTextLabel

    def update_numbers(self):
        """Update the label"""
        # Timing issues mean that this can be called before text label has
        # been properly realised, so we need this guard case
        if self._oTextLabel:
            self._oTextLabel.set_markup(self.TOT_FORMAT % self.dInfo)
            self._oTextLabel.set_tooltip_markup(self.TOT_TOOLTIP % self.dInfo)

    def load(self, aCards):
        """Listen on load events & update counts"""
        # We cache type  lookups to save time
        # The cache is short-lived to avoid needing to deal with
        # flushing the cache on database changes.
        dCache = {}
        self.dInfo = {TOTAL: len(aCards)}
        self._add_dict_keys()
        for oCard in aCards:
            aKeys = dCache.get(oCard.id, None)
            if aKeys is None:
                oAbsCard = IAbstractCard(oCard)
                aKeys = self._get_card_keys(oAbsCard)
                dCache[oCard.id] = aKeys
            for sKey in aKeys:
                self.dInfo[sKey] += 1
        self.update_numbers()

    def alter_card_count(self, oCard, iChg):
        """respond to alter_card_count events"""
        self.dInfo[TOTAL] += iChg
        oAbsCard = IAbstractCard(oCard)
        aKeys = self._get_card_keys(oAbsCard)
        for sKey in aKeys:
            self.dInfo[sKey] += iChg
        self.update_numbers()

    def add_new_card(self, oCard, iCnt):
        """response to add_new_card events"""
        self.dInfo[TOTAL] += iCnt
        oAbsCard = IAbstractCard(oCard)
        aKeys = self._get_card_keys(oAbsCard)
        for sKey in aKeys:
            self.dInfo[sKey] += iCnt
        self.update_numbers()

    def _get_card_keys(self, oAbsCard):
        """Get the list of applicable dictionary keys for this card."""
        raise NotImplementedError('Subclasses must implement _get_card_keys')

    def _add_dict_keys(self):
        """Ensure the totals dictionary has all the required keys."""
        raise NotImplementedError('Subclasses must implement _add_dict_keys')
