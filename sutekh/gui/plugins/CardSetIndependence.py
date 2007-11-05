# CardSetIndependence.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>, Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.core.SutekhObjects import AbstractCardSet, PhysicalCardSet, \
                                 AbstractCard, PhysicalCard, IAbstractCard
from sutekh.core.Filters import AbstractCardSetFilter, PhysicalCardSetFilter
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.ScrolledList import ScrolledList

class CardSetIndependence(CardListPlugin):
    dTableVersions = {AbstractCardSet : [1,2,3],
                      PhysicalCardSet : [1,2,3]}
    aModelsSupported = [AbstractCardSet,
            PhysicalCardSet]
    def getMenuItem(self):
        """
        Overrides method from base class.
        """
        if not self.checkVersions() or not self.checkModelType():
            return None
        iDF = gtk.MenuItem("Test Card Set Independence")
        iDF.connect("activate", self.activate)
        return iDF

    def getDesiredMenu(self):
        return "Plugins"

    def activate(self, oWidget):
        oDlg = self.makeDialog()
        oDlg.run()

    def makeDialog(self):
        """
        Create the list of card sets to select
        """
        parent = self.view.getWindow()
        self.oDlg = gtk.Dialog("Choose Card Sets to Test",parent,
                          gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                          (gtk.STOCK_OK, gtk.RESPONSE_OK,
                           gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        if self._cModelType is AbstractCardSet:
            oSelect = AbstractCardSet.select().orderBy('name')
            self.csFrame = ScrolledList('Abstract Card Sets')
        elif self._cModelType is PhysicalCardSet:
            oSelect = PhysicalCardSet.select().orderBy('name')
            self.csFrame = ScrolledList('Physical Card Sets')
        else:
            return
        self.oDlg.vbox.pack_start(self.csFrame)
        self.csFrame.set_size_request(150,300)
        for cs in oSelect:
            if cs.name != self.view.sSetName:
                iter = self.csFrame.get_list().append(None)
                self.csFrame.get_list().set(iter,0,cs.name)
        self.oDlg.connect("response", self.handleResponse)
        self.oDlg.show_all()
        return self.oDlg

    def handleResponse(self,oWidget,oResponse):
        if oResponse ==  gtk.RESPONSE_OK:
            aCardSetNames = [self.view.sSetName]
            dSelect = {}
            self.csFrame.get_selection(aCardSetNames, dSelect)
            if self._cModelType is AbstractCardSet:
                self.testAbstractCardSets(aCardSetNames)
            else:
                self.testPhysicalCardSets(aCardSetNames)
        self.oDlg.destroy()

    def testAbstractCardSets(self, aCardSetNames):
        """Test if all the Abstract Cards selected can be realised
            independently"""
        dMissing = {}
        dFullCardList = self.__getAbstractCardSetList(aCardSetNames)
        for iCardId, (sCardName, iCount) in dFullCardList.iteritems():
            oPC = list(PhysicalCard.selectBy(abstractCardID=iCardId))
            if iCount > len(oPC):
                dMissing[sCardName] = iCount - len(oPC)
        if len(dMissing) > 0:
            message = "<span foreground = \"red\"> Missing Cards </span>\n"
            for sCardName, iCount in dMissing.iteritems():
                message += "<span foreground = \"blue\">" + sCardName + "</span> : " + str(iCount) + "\n"
            Results = gtk.MessageDialog(None, 0, gtk.MESSAGE_INFO,
                    gtk.BUTTONS_CLOSE, None)
            Results.set_markup(message)
        else:
            Results = gtk.MessageDialog(None, 0, gtk.MESSAGE_INFO,
                    gtk.BUTTONS_CLOSE, "All Cards in the PhysicalCard List")
        Results.run()
        Results.destroy()

    def testPhysicalCardSets(self, aCardSetNames):
        """Test if the Physical Card Sets are actaully independent by
           looking for cards common to the sets"""
        dFullCardList = self.__getPhysicalCardSetList(aCardSetNames)
        dMissing = {}
        for oCard, (sName, iCount) in dFullCardList:
            if iCount > 1:
                if oCard.expansion is not None:
                    dMissing[(sName, oCard.expansion.name)] = iCount
                else:
                    dMissing[(sName, '(unspecified expansion)')] = iCount
        if len(dMissing) > 0:
            message = "<span foreground = \"red\"> Duplicate Cards </span>\n"
            for (sCardName, sExpansion), iCount in dMissing.iteritems():
                message += "<span foreground = \"blue\">" + sCardName \
                        + " (from expansion: " + sExpansion \
                        + ")</span> : used " + str(iCount) + " times\n"
            Results = gtk.MessageDialog(None, 0, gtk.MESSAGE_INFO,
                    gtk.BUTTONS_CLOSE, None)
            Results.set_markup(message)
        else:
            Results = gtk.MessageDialog(None, 0, gtk.MESSAGE_INFO,
                    gtk.BUTTONS_CLOSE, "No cards duplicated")
        Results.run()
        Results.destroy()



    def __getAbstractCardSetList(self, aCardSetNames):
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

    def __getPhysicalCardSetList(self, aCardSetNames):
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

plugin = CardSetIndependence
