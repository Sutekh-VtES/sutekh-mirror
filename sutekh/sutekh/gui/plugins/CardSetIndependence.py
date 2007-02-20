# CardSetIndependence.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>, Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from SutekhObjects import *
from Filters import *
from gui.PluginManager import CardListPlugin
from gui.ScrolledList import ScrolledList

class CardSetIndependence(CardListPlugin):
    dTableVersions = {"AbstractCardSet" : [1,2],
                      "PhysicalCardSet" : [1,2]}
    aModelsSupported = ["AbstractCardSet","PhysicalCardSet"]
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

    def activate(self,oWidget):
        oDlg = self.makeDialog()
        oDlg.run()
        # only do stuff for AbstractCardSets

    def makeDialog(self):
        """
        Create the list of card sets to select
        """
        parent = self.view.getWindow()
        self.oDlg = gtk.Dialog("Choose Card Sets to Test",parent,
                          gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                          (gtk.STOCK_OK, gtk.RESPONSE_OK,
                           gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.csFrame=ScrolledList('Abstract Card Sets')
        self.oDlg.vbox.pack_start(self.csFrame)
        self.csFrame.set_size_request(150,300)
        if self.view.sSetType == 'AbstractCardSet':
            oSelect=AbstractCardSet.select().orderBy('name')
        elif self.view.sSetType == 'PhysicalCardSet':
            oSelect=PhysicalCardSet.select().orderBy('name')
        else:
            return
        for cs in oSelect:
            if cs.name != self.view.sSetName:
                iter=self.csFrame.get_list().append(None)
                self.csFrame.get_list().set(iter,0,cs.name)
        self.oDlg.connect("response", self.handleResponse)
        self.oDlg.show_all()
        return self.oDlg

    def handleResponse(self,oWidget,oResponse):
       if oResponse ==  gtk.RESPONSE_OK:
           aCardSetNames=[self.view.sSetName]
           dSelect={}
           self.csFrame.get_selection(aCardSetNames,dSelect)
           self.testCardSets(aCardSetNames)
       self.oDlg.destroy()

    def testCardSets(self,aCardSetNames):
        dMissing={}
        dFullCardList=self.__getCardSetList(aCardSetNames)
        for cardid,(cardname,cardcount) in dFullCardList.iteritems():
            oPC=list(PhysicalCard.selectBy(abstractCardID=cardid))
            if cardcount>len(oPC):
                dMissing[cardname]=cardcount-len(oPC)
        if len(dMissing)>0:
            message="<span foreground=\"red\">Missing Cards</span>\n"
            for cardname,cardcount in dMissing.iteritems():
                message+="<span foreground=\"blue\">"+cardname+"</span> : "+str(cardcount)+"\n"
            Results=gtk.MessageDialog(None,0,gtk.MESSAGE_INFO,\
                    gtk.BUTTONS_CLOSE,None)
            Results.set_markup(message)
        else:
            Results=gtk.MessageDialog(None,0,gtk.MESSAGE_INFO,\
                    gtk.BUTTONS_CLOSE,"All Cards in the PhysicalCard List")
        Results.run()
        Results.destroy()

    def __getCardSetList(self,aCardSetNames):
        dFullCardList={}
        for name in aCardSetNames:
            if self.view.sSetType=='AbstractCardSet':
                oFilter=AbstractCardSetFilter(name)
                oCS=AbstractCard.select(oFilter.getExpression())
            elif self.view.sSetType=='PhysicalCardSet':
                oFilter=PhysicalCardSetFilter(name)
                oCS=PhysicalCard.select(oFilter.getExpression())
            for oC in oCS:
                oAC=IAbstractCard(oC)
                try:
                    dFullCardList[oAC.id][1]+=1
                except KeyError:
                    dFullCardList[oAC.id]=[oAC.name,1]
        return dFullCardList

plugin = CardSetIndependence
