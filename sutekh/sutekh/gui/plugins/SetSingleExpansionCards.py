# SetSingleExpansionCards.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""Force all cards which can only belong to 1 expansion to that expansion"""

import gtk
from sutekh.core.SutekhObjects import PhysicalCard
from sutekh.gui.PluginManager import CardListPlugin

class SetSingleExpansionCards(CardListPlugin):
    """Force expansion for single expansion cards.

       For all cards in the Physical Card List that a) have no expansion
       set, and b) only occur ina single expansion, set the expansion
       appropriately
       """

    dTableVersions = { PhysicalCard: [2] }
    aModelsSupported = [PhysicalCard]

    def get_menu_item(self):
        """Return a gtk.MenuItem to activate this plugin."""
        if not self.check_versions() or not self.check_model_type():
            return None
        oMenuItem = gtk.MenuItem("Force Expansion for Single Expansion Cards")
        oMenuItem.connect("activate", self.activate)
        return ('Plugins', oMenuItem)

    # pylint: disable-msg=W0613
    # oWidget needed by gtk function signature
    def activate(self, oWidget):
        """Handle menu activiation"""
        self.do_set_expansions()

    def do_set_expansions(self):
        """Iterate through card list and set expansions"""
        for oCard in self.model.getCardIterator(None):
            if oCard.expansion is None:
                oAC = oCard.abstractCard
                aExpansion = set([oRP.expansion for oRP in oAC.rarity])
                if len(aExpansion) == 1:
                    oExp = aExpansion.pop()
                    oCard.expansion = oExp
                    oCard.syncUpdate()
        self.view.reload_keep_expanded()

# pylint: disable-msg=C0103
# accept plugin name
plugin = SetSingleExpansionCards
