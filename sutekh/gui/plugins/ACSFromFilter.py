# ACSFromFilter.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.SutekhObjects import AbstractCardSet, IAbstractCard
from sutekh.gui.PluginManager import CardListPlugin

class ACSFromFilter(CardListPlugin):
    dTableVersions = { "AbstractCardSet" : [2,3]}
    aModelsSupported = ["PhysicalCardSet","AbstractCardSet","PhysicalCard",
            "AbstractCard"]

    def __init__(self,*args,**kws):
        super(ACSFromFilter,self).__init__(*args,**kws)

    def getMenuItem(self):
        """
        Overrides method from base class.
        """
        if not self.checkVersions() or not self.checkModelType():
            return None
        iDF = gtk.MenuItem("Abstract Card Set From Filter")
        iDF.connect("activate", self.activate)
        return iDF

    def getDesiredMenu(self):
        return "Filter"

    def activate(self,oWidget):
        oDlg = self.makeDialog()
        oDlg.run()

    def makeDialog(self):
        parent = self.view.getWindow()

        self.oDlg = gtk.Dialog("Choose Abstract Card Set Name",parent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                    gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.oDlg.connect("response", self.handleResponse)

        self.oACSNameEntry = gtk.Entry(50)
        self.oACSNameEntry.connect("activate", self.handleResponse, gtk.RESPONSE_OK)

        self.oDlg.vbox.pack_start(self.oACSNameEntry)
        self.oDlg.show_all()

        return self.oDlg

    def handleResponse(self,oWidget,oResponse):
        if oResponse ==  gtk.RESPONSE_OK:
            sACSName = self.oACSNameEntry.get_text().strip()
            self.makeACSFromFilter(sACSName)

        self.oDlg.destroy()

    def makeACSFromFilter(self,sACSName):
        parent = self.view.getWindow()
        # Check ACS Doesn't Exist
        if AbstractCardSet.selectBy(name=sACSName).count() != 0:
            oComplaint = gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
                    gtk.BUTTONS_CLOSE,"Abstract Card Set %s already exists." % sACSName)
            oComplaint.connect("response",lambda oW, oResp: oW.destroy())
            oComplaint.run()
            return

        # Create ACS
        oACS = AbstractCardSet(name=sACSName)

        for oCard in self.model.getCardIterator(self.model.getSelectFilter()):
            oACS.addAbstractCard(IAbstractCard(oCard))
        parent.getManager().reloadCardSetLists()

plugin = ACSFromFilter
