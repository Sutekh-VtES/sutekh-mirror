# CardSetFromFilter.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Converts a filter into a card set"""

import gtk
from sutekh.core.SutekhObjects import PhysicalCardSet, PhysicalCard, \
        IPhysicalCard, IPhysicalCardSet
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.gui.GuiCardSetFunctions import create_card_set


class DeckFromFilter(SutekhPlugin):
    """Converts a filter into a Card Set."""

    dTableVersions = {PhysicalCardSet: (4, 5, 6)}
    aModelsSupported = (PhysicalCardSet, PhysicalCard)

    def get_menu_item(self):
        """Register on the 'Filter' Menu"""
        if not self.check_versions() or not self.check_model_type():
            return None
        oGenPCS = gtk.MenuItem("Card Set From Filter")
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
                self.open_cs(sCSName, True)

    def make_cs_from_filter(self, sCSName):
        """Create the actual PCS."""
        # pylint: disable-msg=E1101
        # pylint misses PhysicalCardSet methods
        oCS = IPhysicalCardSet(sCSName)
        for oCard in self.model.get_card_iterator(
                self.model.get_current_filter()):
            oCS.addPhysicalCard(IPhysicalCard(oCard))

        return oCS


plugin = DeckFromFilter
