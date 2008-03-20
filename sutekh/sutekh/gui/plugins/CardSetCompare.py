# CardSetCompare.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>, Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.core.SutekhObjects import PhysicalCard, AbstractCardSet, \
                                 PhysicalCardSet, AbstractCard, IAbstractCard
from sutekh.core.Filters import PhysicalCardSetFilter, AbstractCardSetFilter
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import SutekhDialog
from sutekh.gui.ScrolledList import ScrolledList

class CardSetCompare(CardListPlugin):
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
        iDF = gtk.MenuItem("Compare with another Card Set")
        iDF.connect("activate", self.activate)
        return iDF

    def get_desired_menu(self):
        return "Plugins"

    def activate(self, oWidget):
        oDlg = self.make_dialog()
        oDlg.run()
        # only do stuff for AbstractCardSets

    def make_dialog(self):
        """
        Create the list of card sets to select
        """
        self.oDlg = SutekhDialog("Choose Card Set to Compare with", self.parent,
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
        self.oCSList.set_select_single()
        self.oDlg.vbox.pack_start(self.oCSList)
        self.oCSList.set_size_request(150, 300)
        aVals = [oCS.name for oCS in oSelect if oCS.name != self.view.sSetName]
        self.oCSList.fill_list(aVals)
        self.oDlg.connect("response", self.handle_response)
        self.oDlg.show_all()
        return self.oDlg

    def handle_response(self, oWidget, oResponse):
        if oResponse ==  gtk.RESPONSE_OK:
            aCardSetNames = [self.view.sSetName]
            aCardSetNames.extend(self.oCSList.get_selection())
            self.comp_card_sets(aCardSetNames)
        self.oDlg.destroy()

    def comp_card_sets(self, aCardSetNames):
        (dDifferences, aCommon) = self.__get_card_set_list(aCardSetNames)
        Results = SutekhDialog("Card Comparison", self.parent, gtk.DIALOG_MODAL | \
                gtk.DIALOG_DESTROY_WITH_PARENT, \
                (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        myHBox = gtk.HBox(False, 0)
        if len(aCommon) > 0:
            oFrame = gtk.Frame("placeholder")
            oFrame.get_label_widget().set_markup("<span foreground = \"blue\">Common Cards</span>")
            message = ""
            for sCardName, iCount in aCommon:
                message += "<span foreground = \"green\">" + sCardName + \
                        "</span> : " + str(iCount) + "\n"
            myLabel = gtk.Label()
            myLabel.set_markup(message)
            oFrame.add(myLabel)
            myHBox.pack_start(oFrame)
        if len(dDifferences[aCardSetNames[0]]) > 0:
            oFrame = gtk.Frame("placeholder")
            oFrame.get_label_widget().set_markup("<span foreground = \"red\">Cards only in " + aCardSetNames[0] + "</span>")
            message = ""
            for sCardName, iCount in dDifferences[aCardSetNames[0]]:
                message += "<span foreground = \"blue\">" + sCardName + "</span> : " + str(iCount) + "\n"
            myLabel = gtk.Label()
            myLabel.set_markup(message)
            oFrame.add(myLabel)
            myHBox.pack_start(oFrame)
        if len(dDifferences[aCardSetNames[1]]) > 0:
            oFrame = gtk.Frame("placeholder")
            oFrame.get_label_widget().set_markup("<span foreground = \"red\">Cards only in " + aCardSetNames[1] + "</span>")
            message = ""
            for sCardName, iCount in dDifferences[aCardSetNames[1]]:
                message += "<span foreground = \"blue\">" + sCardName + "</span> : " + str(iCount) + "\n"
            myLabel = gtk.Label()
            myLabel.set_markup(message)
            oFrame.add(myLabel)
            myHBox.pack_start(oFrame)
        Results.vbox.pack_start(myHBox)
        Results.show_all()
        Results.run()
        Results.destroy()

    def __get_card_set_list(self, aCardSetNames):
        dFullCardList = {}
        sCardSetName1 = aCardSetNames[0]
        sCardSetName2 = aCardSetNames[1]
        for sCardSetName in aCardSetNames:
            if self._cModelType is AbstractCardSet:
                oFilter = AbstractCardSetFilter(sCardSetName)
                oCS = oFilter.select(AbstractCard)
            elif self._cModelType is PhysicalCardSet:
                oFilter = PhysicalCardSetFilter(sCardSetName)
                oCS = oFilter.select(PhysicalCard)
            for oC in oCS:
                oAC = IAbstractCard(oC)
                dFullCardList.setdefault(oAC.name, {sCardSetName1 : 0, sCardSetName2 : 0})
                dFullCardList[oAC.name][sCardSetName] += 1
        dDifferences = { sCardSetName1 : [], sCardSetName2 : [] }
        aCommon = []
        for sCardName in dFullCardList.keys():
            iDiff = dFullCardList[sCardName][sCardSetName1] - dFullCardList[sCardName][sCardSetName2]
            iCommon = min(dFullCardList[sCardName][sCardSetName1], dFullCardList[sCardName][sCardSetName2])
            if iDiff > 0:
                dDifferences[sCardSetName1].append( (sCardName, iDiff) )
            elif iDiff < 0:
                dDifferences[sCardSetName2].append( (sCardName, abs(iDiff)) )
            if iCommon > 0:
                aCommon.append((sCardName, iCommon))
        return (dDifferences, aCommon)

# pylint: disable-msg=C0103
# accept plugin name
plugin = CardSetCompare
