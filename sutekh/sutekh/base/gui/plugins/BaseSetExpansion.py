# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""Force all cards which can only belong to 1 expansion to that expansion"""

from gi.repository import Gtk
from ...core.BaseTables import (PhysicalCardSet,
                                MapPhysicalCardToPhysicalCardSet)
from ...core.BaseAdapters import (IExpansion, IPhysicalCard,
                                  IAbstractCard, IPrinting)
from ...core.DBSignals import send_changed_signal
from ..BasePluginManager import BasePlugin
from ..SutekhDialog import SutekhDialog, do_complaint_error
from ..ScrolledList import ScrolledList


class BaseSetExpansion(BasePlugin):
    """Set al the selected cards in the card list to a single expansion

       Find the common subset of expansions for the selected list, and allow
       the user to choose which expansion to set all the cards too.
       """

    dTableVersions = {PhysicalCardSet: (5, 6, 7)}
    aModelsSupported = (PhysicalCardSet,)

    def get_menu_item(self):
        """Return a Gtk.MenuItem to activate this plugin."""
        oMenuItem = Gtk.MenuItem(
            label="Set selected cards to a single expansion")
        oMenuItem.connect("activate", self.activate)
        return ('Actions', oMenuItem)

    def activate(self, _oWidget):
        """Handle menu activation"""
        self.create_dialog()

    def create_dialog(self):
        """Find the common subset of the selected cards, and prompt the user
           for the expansion.
           """
        dSelected = self.view.process_selection()
        # Only want the distinct cards here - numbers are unimportant
        aAbsCards = set(self._get_selected_abs_cards())
        if not aAbsCards:
            do_complaint_error('Need to select some cards for this plugin')
            return
        aExpansions = self.find_common_expansions(aAbsCards)
        oDialog = SutekhDialog('Select expansion', self.parent,
                               Gtk.DialogFlags.MODAL |
                               Gtk.DialogFlags.DESTROY_WITH_PARENT,
                               ("_OK", Gtk.ResponseType.OK,
                                "_Cancel", Gtk.ResponseType.CANCEL))
        oExpList = ScrolledList('Possible Expansions')
        oDialog.vbox.pack_start(oExpList, True, True, 0)
        oExpList.set_size_request(150, 300)
        oExpList.fill_list(sorted(aExpansions))
        oExpList.set_select_single()
        if oDialog.run() == Gtk.ResponseType.OK:
            aExpNames = oExpList.get_selection()
            if not aExpNames:
                sExpName = None
                do_complaint_error('No Expansion selected')
            else:
                sExpName = aExpNames[0]
                if sExpName == self.model.sUnknownExpansion:
                    oPrinting = None
                else:
                    oExpansion = IExpansion(sExpName)
                    oPrinting = IPrinting((oExpansion, None))
                self.do_set_printing(dSelected, oPrinting)
        oDialog.destroy()

    def do_set_printing(self, dSelected, oPrinting):
        """Iterate over the cards, setting the correct expansion"""
        # Dealing with selected cards, so filter list is the correct one
        oCS = self._get_card_set()
        for oCard in self.model.get_card_iterator(
                self.model.get_current_filter()):
            oAbsCard = IAbstractCard(oCard)
            if oAbsCard.id in dSelected:
                oPhysCard = IPhysicalCard(oCard)
                if oPhysCard.printing is oPrinting:
                    continue  # No need to change this
                if oPhysCard.id in dSelected[oAbsCard.id]:
                    oNewCard = IPhysicalCard((oAbsCard, oPrinting))
                    # Card in the selection, so replace with changed card
                    MapPhysicalCardToPhysicalCardSet.delete(oCard.id)
                    oCS.addPhysicalCard(oNewCard.id)
                    oCS.syncUpdate()
                    # Handle updates
                    send_changed_signal(oCS, oPhysCard, -1)
                    send_changed_signal(oCS, oNewCard, +1)
        self.view.reload_keep_expanded()

    def find_common_expansions(self, aCardList):
        """Find the common possible set of expansions for the given list
           of abstract cards."""
        oFirstCard = aCardList.pop()
        aCandExpansions = set([x.expansion.name for x in oFirstCard.rarity])
        for oCard in aCardList:
            aThisExpansions = set([x.expansion.name for x in oCard.rarity])
            aCandExpansions = aThisExpansions.intersection(aCandExpansions)
        aCandExpansions.add(self.model.sUnknownExpansion)  # Always possible
        return aCandExpansions
