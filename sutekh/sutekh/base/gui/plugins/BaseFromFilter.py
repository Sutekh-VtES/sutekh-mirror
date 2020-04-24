# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Converts a filter into a card set"""

from gi.repository import Gtk
from ...core.BaseTables import PhysicalCardSet, PhysicalCard
from ...core.BaseAdapters import IPhysicalCard, IPhysicalCardSet
from ..BasePluginManager import BasePlugin
from ..GuiCardSetFunctions import create_card_set


class BaseFromFilter(BasePlugin):
    """Converts a filter into a Card Set."""

    dTableVersions = {PhysicalCardSet: (4, 5, 6, 7)}
    aModelsSupported = (PhysicalCardSet, PhysicalCard)

    sMenuName = "Card Set From Filter"

    sHelpCategory = "card_list:filter"

    sHelpText = """Create a new card set containing the results
                   of the current filter. The new card set will
                   be opened automatically and will be set editable."""

    def get_menu_item(self):
        """Register on the 'Filter' Menu"""
        oGenPCS = Gtk.MenuItem(label="Card Set From Filter")
        oGenPCS.connect("activate", self.activate)
        return ('Filter', oGenPCS)

    def activate(self, _oWidget):
        """Create the dialog.

           Prompt the user for Card Set Properties, and so forth.
           """
        sCSName = create_card_set(self.parent)
        if sCSName:
            oCardSet = self.make_cs_from_filter(sCSName)
            if oCardSet:
                self._open_cs(sCSName, True)

    def make_cs_from_filter(self, sCSName):
        """Create the actual PCS."""
        oCS = IPhysicalCardSet(sCSName)
        aCards = [IPhysicalCard(x) for x in
                  self.model.get_card_iterator(
                      self.model.get_current_filter())]
        self._commit_cards(oCS, aCards)
        return oCS
