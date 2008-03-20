# CardSetIndependence.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>, Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.core.SutekhObjects import AbstractCardSet, PhysicalCardSet, \
                                 AbstractCard, PhysicalCard, IAbstractCard
from sutekh.core.Filters import AbstractCardSetFilter, PhysicalCardSetFilter
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.ScrolledList import ScrolledList
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint

class CardSetIndependence(CardListPlugin):
    dTableVersions = {AbstractCardSet : [1, 2, 3],
                      PhysicalCardSet : [1, 2, 3]}
    aModelsSupported = [AbstractCardSet,
            PhysicalCardSet]

    def get_menu_item(self):
        """
        Overrides method from base class.
        """
        if not self.check_versions() or not self.check_model_type():
            return None
        iDF = gtk.MenuItem("Test Card Set Independence")
        iDF.connect("activate", self.activate)
        return iDF

    def get_desired_menu(self):
        return "Plugins"

    def activate(self, oWidget):
        oDlg = self.make_dialog()
        oDlg.run()

    def make_dialog(self):
        """
        Create the list of card sets to select
        """
        self.oDlg = SutekhDialog("Choose Card Sets to Test", self.parent,
                          gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                          (gtk.STOCK_OK, gtk.RESPONSE_OK,
                           gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        if self._cModelType is AbstractCardSet:
            oSelect = AbstractCardSet.select().orderBy('name')
            self.oCSList = ScrolledList('Abstract Card Sets')
        elif self._cModelType is PhysicalCardSet:
            oSelect = PhysicalCardSet.select().orderBy('name')
            self.oCSList = ScrolledList('Physical Card Sets')
        else:
            return
        self.oDlg.vbox.pack_start(self.oCSList)
        self.oCSList.set_size_request(150, 300)
        aNames = [oCS.name for oCS in oSelect if oCS.name != self.view.sSetName]
        self.oCSList.fill_list(aNames)
        self.oDlg.connect("response", self.handle_response)
        self.oDlg.show_all()
        return self.oDlg

    def handle_response(self, oWidget, oResponse):
        if oResponse ==  gtk.RESPONSE_OK:
            aCardSetNames = [self.view.sSetName]
            aCardSetNames.extend(self.oCSList.get_selection())
            if self._cModelType is AbstractCardSet:
                self.test_abstract_card_sets(aCardSetNames)
            else:
                self.test_physical_card_sets(aCardSetNames)
        self.oDlg.destroy()

    def test_abstract_card_sets(self, aCardSetNames):
        """Test if all the Abstract Cards selected can be realised
            independently"""
        dMissing = {}
        dFullCardList = self.__get_abstract_card_set_list(aCardSetNames)
        for iCardId, (sCardName, iCount) in dFullCardList.iteritems():
            oPC = list(PhysicalCard.selectBy(abstractCardID=iCardId))
            if iCount > len(oPC):
                dMissing[sCardName] = iCount - len(oPC)
        if len(dMissing) > 0:
            sMessage = "<span foreground = \"red\"> Missing Cards </span>\n"
            for sCardName, iCount in dMissing.iteritems():
                sMessage += "<span foreground = \"blue\">" + sCardName + "</span> : " + str(iCount) + "\n"
        else:
            sMessage = "All Cards in the PhysicalCard List"
        do_complaint(sMessage, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, True)

    def test_physical_card_sets(self, aCardSetNames):
        """Test if the Physical Card Sets are actaully independent by
           looking for cards common to the sets"""
        dFullCardList = self.__get_physical_card_set_list(aCardSetNames)
        dMissing = {}
        for oCard, (sName, iCount) in dFullCardList:
            if iCount > 1:
                if oCard.expansion is not None:
                    dMissing[(sName, oCard.expansion.name)] = iCount
                else:
                    dMissing[(sName, '(unspecified expansion)')] = iCount
        if len(dMissing) > 0:
            sMessage = "<span foreground = \"red\"> Duplicate Cards </span>\n"
            for (sCardName, sExpansion), iCount in dMissing.iteritems():
                sMessage += "<span foreground = \"blue\">" + sCardName \
                        + " (from expansion: " + sExpansion \
                        + ")</span> : used " + str(iCount) + " times\n"
        else:
            sMessage = "No cards duplicated"
        do_complaint(sMessage, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, True)

    def __get_abstract_card_set_list(self, aCardSetNames):
        dFullCardList = {}
        for sName in aCardSetNames:
            oFilter = AbstractCardSetFilter(sName)
            oCS = oFilter.select(AbstractCard)
            for oC in oCS:
                oAC = IAbstractCard(oC)
                try:
                    dFullCardList[oAC.id][1] += 1
                except KeyError:
                    dFullCardList[oAC.id] = [oAC.name, 1]
        return dFullCardList

    def __get_physical_card_set_list(self, aCardSetNames):
        dFullCardList = {}
        for sName in aCardSetNames:
            oFilter = PhysicalCardSetFilter(sName)
            oCS = oFilter.select(PhysicalCard)
            for oC in oCS:
                oAC = IAbstractCard(oC)
                try:
                    dFullCardList[oC][1] += 1
                except KeyError:
                    dFullCardList[oC] = [oAC.name, 1]
        return dFullCardList

# pylint: disable-msg=C0103
# accept plugin name
plugin = CardSetIndependence
