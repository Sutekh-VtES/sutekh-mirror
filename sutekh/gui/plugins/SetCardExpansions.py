# SetCardExpansions.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""Force all cards which can only belong to 1 expansion to that expansion"""

import gtk
from sutekh.core.SutekhObjects import PhysicalCardSet, IExpansion, \
        IPhysicalCard, IAbstractCard, MapPhysicalCardToPhysicalCardSet
from sutekh.core.DBSignals import send_changed_signal
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error
from sutekh.gui.ScrolledList import ScrolledList


class SetCardExpansions(SutekhPlugin):
    """Set al the selected cards in the card list to a single expansion

       Find the common subset of expansions for the selected list, and allow
       the user to choose which expansion to set all the cards too.
       """

    dTableVersions = {PhysicalCardSet: (5, 6)}
    aModelsSupported = (PhysicalCardSet,)

    def get_menu_item(self):
        """Return a gtk.MenuItem to activate this plugin."""
        if not self.check_versions() or not self.check_model_type():
            return None
        oMenuItem = gtk.MenuItem("Set selected cards to a single expansion")
        oMenuItem.connect("activate", self.activate)
        return ('Edit', oMenuItem)

    def activate(self, _oWidget):
        """Handle menu activation"""
        self.create_dialog()

    def create_dialog(self):
        """Find the common subset of the selected cards, and prompt the user
           for the expansion.
           """
        dSelected, aAbsCards = self._get_selected_cards()
        if not aAbsCards:
            do_complaint_error('Need to select some cards for this plugin')
            return
        aExpansions = self.find_common_expansions(aAbsCards)
        oDialog = SutekhDialog('Select expansion', self.parent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                    gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        oExpList = ScrolledList('Possible Expansions')
        # pylint: disable-msg=E1101
        # vbox confuses pylint
        oDialog.vbox.pack_start(oExpList)
        oExpList.set_size_request(150, 300)
        oExpList.fill_list(sorted(aExpansions))
        oExpList.set_select_single()
        if oDialog.run() == gtk.RESPONSE_OK:
            aExpNames = oExpList.get_selection()
            if not aExpNames:
                sExpName = None
                do_complaint_error('No Expansion selected')
            else:
                sExpName = aExpNames[0]
                if sExpName == self.model.sUnknownExpansion:
                    oExpansion = None
                else:
                    oExpansion = IExpansion(sExpName)
                self.do_set_expansion(dSelected, oExpansion)
        oDialog.destroy()

    def do_set_expansion(self, dSelected, oExpansion):
        """Iterate over the cards, setting the correct expansion"""
        # Dealing with selected cards, so filter list is the correct one
        oCS = self.get_card_set()
        for oCard in self.model.get_card_iterator(
                self.model.get_current_filter()):
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oAbsCard = IAbstractCard(oCard)
            if oAbsCard.name in dSelected:
                oPhysCard = IPhysicalCard(oCard)
                if oPhysCard.expansion is oExpansion:
                    continue  # No need to change this
                if (self.model.sUnknownExpansion in dSelected[oAbsCard.name]
                        and not oPhysCard.expansion) or \
                        (oPhysCard.expansion and oPhysCard.expansion.name in
                                dSelected[oAbsCard.name]):
                    oNewCard = IPhysicalCard((oAbsCard, oExpansion))
                    # Card in the selection, so replace with changed card
                    MapPhysicalCardToPhysicalCardSet.delete(oCard.id)
                    oCS.addPhysicalCard(oNewCard.id)
                    oCS.syncUpdate()
                    # Handle updates
                    send_changed_signal(oCS, oPhysCard, -1)
                    send_changed_signal(oCS, oNewCard, +1)
        self.view.reload_keep_expanded()

    def _get_selected_cards(self):
        """Extract selected cards from the selection."""
        dSelected = self.view.process_selection()
        aAbsCards = []
        for sCardName in dSelected:
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oCard = IAbstractCard(sCardName)
            aAbsCards.append(oCard)

        return dSelected, aAbsCards

    def find_common_expansions(self, aCardList):
        """Find the common possible set of expansions for the given list
           of abstract cards."""
        aCandExpansions = set([x.expansion.name for x in aCardList[0].rarity])
        for oCard in aCardList:
            aThisExpansions = set([x.expansion.name for x in oCard.rarity])
            aCandExpansions = aThisExpansions.intersection(aCandExpansions)
        aCandExpansions.add(self.model.sUnknownExpansion)  # Always possible
        return aCandExpansions

plugin = SetCardExpansions
