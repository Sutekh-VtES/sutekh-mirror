# AbstractCardSetIndependence.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>, Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from SutekhObjects import *
from Filters import *
from gui.PluginManager import CardListPlugin
from gui.ScrolledList import ScrolledList

class AbstractCardSetIndependence(CardListPlugin):
    dTableVersions = {}
    aModelsSupported = ["AbstractCardSet"]
    def getMenuItem(self):
        """
        Overrides method from base class.
        """
        if not self.checkVersions() or not self.checkModelType():
            return None
        iDF = gtk.MenuItem("Test Abstract Card Set Independence")
        iDF.connect("activate", self.activate)
        return iDF

    def activate(self,oWidget):
        oDlg = self.makeDialog()
        oDlg.run()
        # only do stuff for AbstractCardSets

    def makeDialog(self):
        """
        Create the list of card sets to select
        """
        parent = self.view.getWindow()
        self.oDlg = gtk.Dialog("Choose Abstract Card Sets to Test",parent,
                          gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                          (gtk.STOCK_OK, gtk.RESPONSE_OK,
                           gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.csFrame=ScrolledList('Abstract Card Sets')
        self.oDlg.vbox.pack_start(self.csFrame)
        for cs in AbstractCardSet.select().orderBy('name'):
            if cs.name != self.view.sSetName:
                iter=self.csFrame.get_list().append(None)
                self.csFrame.get_list().set(iter,0,cs.name)
        self.oDlg.connect("response", self.handleResponse)
        self.oDlg.show_all()
        return self.oDlg

    def handleResponse(self,oWidget,oResponse):
       if oResponse ==  gtk.RESPONSE_OK:
           aAbstractCardSetNames=[self.view.sSetName]
           dSelect={}
           self.csFrame.get_selection(aAbstractCardSetNames,dSelect)
           self.testAbstractCardSets(aAbstractCardSetNames)
       self.oDlg.destroy()

    def testAbstractCardSets(self,aAbstractCardSetNames):
        dFullCardList={}
        dMissing={}
        for name in aAbstractCardSetNames:
            oFilter=AbstractCardSetFilter(name)
            oCS=AbstractCard.select(oFilter.getExpression())
            for oC in oCS:
                try:
                    dFullCardList[oC.id][1]+=1
                except KeyError:
                    dFullCardList[oC.id]=[oC.name,1]
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

plugin = AbstractCardSetIndependence
