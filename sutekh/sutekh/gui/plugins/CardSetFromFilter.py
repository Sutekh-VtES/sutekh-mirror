# CardSetFromFilter.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Converts a filter into a card set"""

import gtk
from sutekh.core.SutekhObjects import PhysicalCardSet, PhysicalCard, \
        IPhysicalCard
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import do_complaint_error
from sutekh.gui.CreateCardSetDialog import CreateCardSetDialog
from sutekh.gui.CardSetManagementController import update_card_set

class DeckFromFilter(CardListPlugin):
    """Converts a filter into a Card Set."""

    dTableVersions = { PhysicalCardSet : [2, 3, 4, 5]}
    aModelsSupported = [PhysicalCardSet, PhysicalCard]

    def get_menu_item(self):
        """Register on the 'Filter' Menu"""
        if not self.check_versions() or not self.check_model_type():
            return None
        oGenPCS = gtk.MenuItem("Card Set From Filter")
        oGenPCS.connect("activate", self.activate)
        return ('Filter', oGenPCS)

    # pylint: disable-msg=W0613
    # oWidget required by gtk function signature
    def activate(self, oWidget):
        """Create the dialog.

           Prompt the user for Card Set Properties, and so forth.
           """
        oDlg = CreateCardSetDialog(self.parent)
        oDlg.run()

        self.handle_response(oDlg)

    # pylint: enable-msg=W0613

    def handle_response(self, oDlg):
        """Handle the user response from make_dialog

           call make_pcs_from_filter to create the PCS if needed
           """
        sCSName = oDlg.get_name()
        if sCSName:
            oCardSet = self.make_cs_from_filter(sCSName)
            if oCardSet:
                update_card_set(oCardSet, oDlg, self.parent, None)
                self.open_cs(sCSName)

    def make_cs_from_filter(self, sCSName):
        """Create the actual PCS."""
        # Check CS Doesn't Exist
        # pylint: disable-msg=E1101
        # pylint misses PhysicalCardSet methods
        if PhysicalCardSet.selectBy(name=sCSName).count() != 0:
            do_complaint_error("Card Set %s already exists."
                    % sCSName)
            return None

        # Create PCS
        oCS = PhysicalCardSet(name=sCSName)

        # E1101 is still disabled for this
        for oCard in self.model.get_card_iterator(
                self.model.get_current_filter()):
            oCS.addPhysicalCard(IPhysicalCard(oCard))

        return oCS

# pylint: disable-msg=C0103
# accept plugin name
plugin = DeckFromFilter
