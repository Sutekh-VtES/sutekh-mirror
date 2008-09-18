# DeckFromFilter.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Converts a filter into a card set"""

import gtk
from sutekh.core.SutekhObjects import PhysicalCardSet, PhysicalCard, \
        IPhysicalCard
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error

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
        # FIXME: modify CreateCardSetDialog here
        oDlg = SutekhDialog("Choose Card Set Name", self.parent,
                          gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                          (gtk.STOCK_OK, gtk.RESPONSE_OK,
                           gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        oEntry = gtk.Entry(50)
        oEntry.connect("activate", self.handle_response,
                gtk.RESPONSE_OK, oDlg, oEntry)
        oDlg.connect("response", self.handle_response, oDlg, oEntry)

        # pylint: disable-msg=E1101
        # pylint misses vbox methods
        oDlg.vbox.pack_start(oEntry)
        oDlg.show_all()

        oDlg.run()

    def handle_response(self, oWidget, oResponse, oDlg, oEntry):
        """Handle the user response from make_dialog

           call make_pcs_from_filter to create the PCS if needed
           """
        if oResponse ==  gtk.RESPONSE_OK:
            sCSName = oEntry.get_text().strip()
            self.make_cs_from_filter(sCSName)

        oDlg.destroy()
    # pylint: enable-msg=W0613

    def make_cs_from_filter(self, sCSName):
        """Create the actual PCS."""
        # Check CS Doesn't Exist
        # pylint: disable-msg=E1101
        # pylint misses PhysicalCardSet methods
        if PhysicalCardSet.selectBy(name=sCSName).count() != 0:
            do_complaint_error("Card Set %s already exists."
                    % sCSName)
            return

        # Create PCS
        oCS = PhysicalCardSet(name=sCSName)

        # E1101 is still disabled for this
        for oCard in self.model.get_card_iterator(
                self.model.get_current_filter()):
            oCS.addPhysicalCard(IPhysicalCard(oCard))

        self.open_cs(sCSName)

# pylint: disable-msg=C0103
# accept plugin name
plugin = DeckFromFilter
