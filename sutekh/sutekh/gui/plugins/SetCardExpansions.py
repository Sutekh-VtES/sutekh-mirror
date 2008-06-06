# SetCardExpansions.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""Force all cards which can only belong to 1 expansion to that expansion"""

import gtk
from sutekh.core.SutekhObjects import PhysicalCardSet, IExpansion
from sutekh.gui.PluginManager import CardListPlugin

class SetCardExpansions(CardListPlugin):
    """Set al the selected cards in the card list to a single expansion

       Find the common subset of expansions for the selected list, and allow
       the user to choose which expansion to set all the cards too.
       """

    dTableVersions = { PhysicalCardSet: [4] }
    aModelsSupported = [PhysicalCardSet]

    def get_menu_item(self):
        """Return a gtk.MenuItem to activate this plugin."""
        if not self.check_versions() or not self.check_model_type():
            return None
        oMenuItem = gtk.MenuItem("Set Expansion for Cards")
        oMenuItem.connect("activate", self.activate)
        return ('Plugins', oMenuItem)

    # pylint: disable-msg=W0613
    # oWidget needed by gtk function signature
    def activate(self, oWidget):
        """Handle menu activiation"""
        self.create_dialog()

    # pylint: enable-msg=W0613

    def create_dialog(self):
        """Find the common subset of the selected cards, and prompt the user
           for the expansion.
           """

    def do_set_expansions(self, aCards, oExpansion):
        """Iterate over the cards, setting the correct expansion"""

        self.view.reload_keep_expanded()

# pylint: disable-msg=C0103
# accept plugin name
plugin = SetSingleExpansionCards
