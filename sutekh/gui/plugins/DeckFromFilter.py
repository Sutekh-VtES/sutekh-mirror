# DeckFromFilter.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.SutekhObjects import PhysicalCardSet
from sutekh.gui.PluginManager import CardListPlugin

class DeckFromFilter(CardListPlugin):
    dTableVersions = { "PhysicalCardSet" : [2,3]}
    aModelsSupported = ["PhysicalCardSet","AbstractCardSet","PhysicalCard",]

    def __init__(self,*args,**kws):
        super(DeckFromFilter,self).__init__(*args,**kws)

    def getMenuItem(self):
        """
        Overrides method from base class.
        """
        if not self.checkVersions() or not self.checkModelType():
            return None
        iDF = gtk.MenuItem("Physical Card Set From Filter")
        iDF.connect("activate", self.activate)
        return iDF

    def getDesiredMenu(self):
        return "Filter"

    def activate(self,oWidget):
        oDlg = self.makeDialog()
        oDlg.run()

    def makeDialog(self):
        parent = self.view.getWindow()

        self.oDlg = gtk.Dialog("Choose Physical Card Set Name",parent,
                          gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                          (gtk.STOCK_OK, gtk.RESPONSE_OK,
                           gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.oDlg.connect("response", self.handleResponse)

        self.oPCSNameEntry = gtk.Entry(50)
        self.oPCSNameEntry.connect("activate", self.handleResponse, gtk.RESPONSE_OK)

        self.oDlg.vbox.pack_start(self.oPCSNameEntry)
        self.oDlg.show_all()

        return self.oDlg

    def handleResponse(self,oWidget,oResponse):
       if oResponse ==  gtk.RESPONSE_OK:
          sPCSName = self.oPCSNameEntry.get_text().strip()
          self.makeDeckFromFilter(sPCSName)

       self.oDlg.destroy()

    def makeDeckFromFilter(self,sPCSName):
        parent = self.view.getWindow()
        # Check PCS Doesn't Exist
        if PhysicalCardSet.selectBy(name=sPCSName).count() != 0:
            oComplaint = gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
                                           gtk.BUTTONS_CLOSE,"Physical Card Set %s already exists." % sPCSName)
            oComplaint.connect("response",lambda oW, oResp: oW.destroy())
            oComplaint.run()
            return

        # Create PCS
        oPCS = PhysicalCardSet(name=sPCSName)

        for oCard in self.model.getCardIterator(self.model.getSelectFilter()):
            oPCS.addPhysicalCard(oCard)
        parent.getManager().reloadCardSetLists()

plugin = DeckFromFilter
