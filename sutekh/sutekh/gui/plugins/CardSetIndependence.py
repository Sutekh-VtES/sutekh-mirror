# CardSetIndependence.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>,
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test whether card sets can be constructed independently"""

import gtk
from sutekh.core.SutekhObjects import PhysicalCardSet, \
        PhysicalCard, IAbstractCard
from sutekh.core.Filters import PhysicalCardSetFilter
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.ScrolledList import ScrolledList
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint

# helper functions

def _get_cards(oCardSet, dFullCardList):
    """Extract the abstract cards from the card set oCardSet"""
    # pylint: disable-msg=E1101
    # SQLObject + pyprotocol methods confuse pylint
    for oCard in oCardSet:
        oAC = IAbstractCard(oCard)
        dFullCardList.setdefault(oCard, [oAC.name, 0])
        dFullCardList[oCard][1] += 1

def _get_physical_card_set_list(aCardSetNames):
    """Get the cards in the list of PhysicalCardSets aCardSetNames"""
    # pylint: disable-msg=E1101
    # SQLObject + pyprotocol methods confuse pylint
    dFullCardList = {}
    for sName in aCardSetNames:
        oFilter = PhysicalCardSetFilter(sName)
        oCS = oFilter.select(PhysicalCard)
        _get_cards(oCS, dFullCardList)
    return dFullCardList

def _test_physical_card_sets(aCardSetNames):
    """Test if the Physical Card Sets are actaully independent by
       looking for cards common to the sets"""
    dFullCardList = _get_physical_card_set_list(aCardSetNames)
    dDuplicates = {}
    for oCard, (sName, iCount) in dFullCardList.iteritems():
        if iCount > 1:
            if oCard.expansion is not None:
                dDuplicates[(sName, oCard.expansion.name)] = iCount
            else:
                dDuplicates[(sName, '(unspecified expansion)')] = iCount
    if len(dDuplicates) > 0:
        sMessage = "<span foreground = \"red\">Duplicate Cards</span>\n"
        for (sCardName, sExpansion), iCount in dDuplicates.iteritems():
            sMessage += "<span foreground = \"blue\">" + sCardName \
                    + " (from expansion: " + sExpansion \
                    + ")</span> : used " + str(iCount) + " times\n"
    else:
        sMessage = "No cards duplicated"
    do_complaint(sMessage, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, True)

class CardSetIndependence(CardListPlugin):
    """Provides a plugin for testing whether card sets are independant.

       Independence in this cases means that there are enought cards in
       the card collection to construct all the card sets simulatenously.
       For physical card sets, this doesn't consider the current card
       assignment, just whether enough cards are present.
       """
    dTableVersions = {PhysicalCardSet : [1, 2, 3, 4, 5]}
    aModelsSupported = [PhysicalCardSet]

    def get_menu_item(self):
        """Register with the 'Plugins' Menu"""
        if not self.check_versions() or not self.check_model_type():
            return None
        oTest = gtk.MenuItem("Test Card Set Independence")
        oTest.connect("activate", self.activate)
        return ('Plugins', oTest)

    # pylint: disable-msg=W0613
    # oWidget required by function signature
    def activate(self, oWidget):
        """Create the dialog in response to the menu item."""
        oDlg = self.make_dialog()
        oDlg.run()

    # pylint: enable-msg=W0613

    def make_dialog(self):
        """Create the list of card sets to select"""
        oDlg = SutekhDialog("Choose Card Sets to Test", self.parent,
                          gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                          (gtk.STOCK_OK, gtk.RESPONSE_OK,
                           gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        oSelect = PhysicalCardSet.select().orderBy('name')
        oCSList = ScrolledList('Physical Card Sets')
        # pylint: disable-msg=E1101
        # vbox confuses pylint
        oDlg.vbox.pack_start(oCSList)
        oCSList.set_size_request(150, 300)
        aNames = [oCS.name for oCS in oSelect if oCS.name !=
                self.view.sSetName]
        oCSList.fill_list(aNames)
        oDlg.connect("response", self.handle_response, oCSList)
        oDlg.show_all()
        return oDlg

    def handle_response(self, oDlg, oResponse, oCSList):
        """Handle the response from the dialog."""
        if oResponse ==  gtk.RESPONSE_OK:
            aCardSetNames = [self.view.sSetName]
            aCardSetNames.extend(oCSList.get_selection())
            _test_physical_card_sets(aCardSetNames)
        oDlg.destroy()


# pylint: disable-msg=C0103
# accept plugin name
plugin = CardSetIndependence
