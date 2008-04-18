# DeckFromFilter.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Converts a filter into a card set"""

import gtk
from sutekh.core.SutekhObjects import PhysicalCardSet, PhysicalCard
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error

class DeckFromFilter(CardListPlugin):
    """
    Converts a filter into a Physical Card Set
    """

    dTableVersions = { PhysicalCardSet : [2, 3, 4]}
    aModelsSupported = [PhysicalCardSet, PhysicalCard]

    def get_menu_item(self):
        """Register on the 'Filter' Menu"""
        if not self.check_versions() or not self.check_model_type():
            return None
        oGenPCS = gtk.MenuItem("Physical Card Set From Filter")
        oGenPCS.connect("activate", self.activate)
        return ('Filter', oGenPCS)

    # pylint: disable-msg=W0613
    # oWidget required by gtk function signature
    def activate(self, oWidget):
        """Create the dialog.

           Prompt the user for Physical Card Set Properties, and so forth.
           """
        oDlg = SutekhDialog("Choose Physical Card Set Name", self.parent,
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
        """
        Handle the user response from make_dialog
        call make_pcs_from_filter to create the PCS if needed
        """
        if oResponse ==  gtk.RESPONSE_OK:
            sPCSName = oEntry.get_text().strip()
            self.make_pcs_from_filter(sPCSName)

        oDlg.destroy()
    # pylint: enable-msg=W0613

    def make_pcs_from_filter(self, sPCSName):
        """
        Create the actual PCS
        """
        # Check PCS Doesn't Exist
        # pylint: disable-msg=E1101
        # pylint misses PhysicalCardSet methods
        if PhysicalCardSet.selectBy(name=sPCSName).count() != 0:
            do_complaint_error("Physical Card Set %s already exists."
                    % sPCSName)
            return

        # Create PCS
        oPCS = PhysicalCardSet(name=sPCSName)

        # E1101 is still disabled for this
        for oCard in self.model.get_card_iterator(
                self.model.get_current_filter()):
            oPCS.addPhysicalCard(oCard)

        self.open_pcs(sPCSName)

# pylint: disable-msg=C0103
# accept plugin name
plugin = DeckFromFilter
