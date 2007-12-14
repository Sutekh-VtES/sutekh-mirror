# SetSingleExpansionCards.py
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.core.SutekhObjects import PhysicalCard
from sutekh.gui.PluginManager import CardListPlugin

class SetSingleExpansionCards(CardListPlugin):
    """
    For all cards in the Physical Card List that a) have no expansion
    set, and b) only occur ina single expansion, set the expansion
    appropriately
    """

    dTableVersions = { PhysicalCard: [2] }
    aModelsSupported = [PhysicalCard]

    def get_menu_item(self):
        """
        Overrides method from base class.
        """
        if not self.check_versions() or not self.check_model_type():
            return None
        iDF = gtk.MenuItem("Force Expansion for Single Expansion Cards")
        iDF.connect("activate", self.activate)
        return iDF

    def get_desired_menu(self):
        return "Plugins"

    def activate(self,oWidget):
        self.do_set_expansions()

    def do_set_expansions(self):
        for oCard in self.model.getCardIterator(None):
            if oCard.expansion is None:
                oAC = oCard.abstractCard
                aExpansion = set([oRP.expansion for oRP in oAC.rarity])
                if len(aExpansion) == 1:
                    oExp = aExpansion.pop()
                    oCard.expansion = oExp
                    oCard.syncUpdate()
        self.view.reload_keep_expanded()

plugin = SetSingleExpansionCards
