# DeckFromFilter.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk
from SutekhObjects import *
from gui.PluginManager import CardListPlugin

class DeckFromFilter(CardListPlugin):
    dTableVersions = {"PhysicalCardSet" : [2],
            "AbstractCardSet" : [2],
            "PhysicalCard" : [1]}
    aModelsSupported = ["PhysicalCardSet","AbstractCardSet","PhysicalCard"]
    def __init__(self,*args,**kws):
        super(DeckFromFilter,self).__init__(*args,**kws)

    def getMenuItem(self):
        """
        Overrides method from base class.
        """
        if not self.checkVersions() or not self.checkModelType():
            return None
        iDF = gtk.MenuItem("Deck From Filter")
        iDF.connect("activate", self.activate)
        return iDF

    def getDesiredMenu(self):
        return "Filter"
        
    def activate(self,oWidget):
        oDlg = self.makeDialog()
        oDlg.run()

    def makeDialog(self):
        parent = self.view.getWindow()
    
        self.oDlg = gtk.Dialog("Choose Deck Name",parent,
                          gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                          (gtk.STOCK_OK, gtk.RESPONSE_OK,
                           gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))     
        self.oDlg.connect("response", self.handleResponse)
        
        self.oDeckNameEntry = gtk.Entry(50)
        self.oDeckNameEntry.connect("activate", self.handleResponse, gtk.RESPONSE_OK)
        
        self.oDlg.vbox.pack_start(self.oDeckNameEntry)
        self.oDlg.show_all()
        
        return self.oDlg

    def handleResponse(self,oWidget,oResponse):
       if oResponse ==  gtk.RESPONSE_OK:
          sDeckName = self.oDeckNameEntry.get_text().strip()
          self.makeDeckFromFilter(sDeckName)
          
       self.oDlg.destroy()
          
    def makeDeckFromFilter(self,sDeckName):
        # Check Deck Doesn't Exist
        if PhysicalCardSet.selectBy(name=sDeckName).count() != 0:
            oComplaint = gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
                                           gtk.BUTTONS_CLOSE,"Deck %s already exists." % sDeckName)
            oComplaint.connect("response",lambda oW, oResp: oW.destroy())
            oComplaint.run()
            return
        
        # Create Deck
        oDeck = PhysicalCardSet(name=sDeckName)
    
        for oCard in self.model.getCardIterator(self.model.getSelectFilter()):
            oDeck.addPhysicalCard(oCard)

plugin = DeckFromFilter
