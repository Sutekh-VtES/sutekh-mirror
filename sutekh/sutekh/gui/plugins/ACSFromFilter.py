# ACSFromFilter.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>,
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"Convert a filter on an Abstract Card Set"

import gtk
from sutekh.core.SutekhObjects import AbstractCardSet, PhysicalCardSet, \
                                      AbstractCard, PhysicalCard, \
                                      IAbstractCard
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error

class ACSFromFilter(CardListPlugin):
    """
    Converts a filter into a Abstract Card Set
    """
    dTableVersions = { AbstractCardSet : [2, 3]}
    aModelsSupported = [PhysicalCardSet, AbstractCardSet,
                        PhysicalCard, AbstractCard]

    def get_menu_item(self):
        """Register on the 'Filter' Menu"""
        if not self.check_versions() or not self.check_model_type():
            return None
        oGenACS = gtk.MenuItem("Abstract Card Set From Filter")
        oGenACS.connect("activate", self.activate)
        return ('Filter', oGenACS)

    # pylint: disable-msg=W0613
    # oWidget required by gtk function signature
    def activate(self, oWidget):
        "Create the dialog in response to the menu"
        oDlg = SutekhDialog("Choose Abstract Card Set Name", self.parent,
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
        call make_acs_from_filter to create the ACS if needed
        """
        if oResponse ==  gtk.RESPONSE_OK:
            sACSName = oEntry.get_text().strip()
            self.make_acs_from_filter(sACSName)

        oDlg.destroy()

    def make_acs_from_filter(self, sACSName):
        """
        Create the actual ACS
        """
        # Check ACS Doesn't Exist
        # pylint: disable-msg=E1101
        # pylint misses AbstractCardSet methods
        if AbstractCardSet.selectBy(name=sACSName).count() != 0:
            do_complaint_error("Abstract Card Set %s already exists."
                    % sACSName)
            return

        # Create ACS
        oACS = AbstractCardSet(name=sACSName)

        for oCard in self.model.getCardIterator(
                self.model.get_current_filter()):
            oACS.addAbstractCard(IAbstractCard(oCard))

        self.open_acs(sACSName)

# pylint: disable-msg=C0103
# accept plugin name
plugin = ACSFromFilter
