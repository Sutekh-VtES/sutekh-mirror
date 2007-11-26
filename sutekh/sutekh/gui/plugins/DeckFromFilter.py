# DeckFromFilter.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.core.SutekhObjects import PhysicalCardSet, PhysicalCard
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error

class DeckFromFilter(CardListPlugin):
    dTableVersions = { PhysicalCardSet : [2,3]}
    aModelsSupported = [PhysicalCardSet, PhysicalCard]

    def __init__(self,*args,**kws):
        super(DeckFromFilter,self).__init__(*args,**kws)

    def get_menu_item(self):
        """
        Overrides method from base class.
        """
        if not self.check_versions() or not self.check_model_type():
            return None
        iDF = gtk.MenuItem("Physical Card Set From Filter")
        iDF.connect("activate", self.activate)
        return iDF

    def get_desired_menu(self):
        return "Filter"

    def activate(self,oWidget):
        oDlg = self.makeDialog()
        oDlg.run()

    def makeDialog(self):
        self.oDlg = SutekhDialog("Choose Physical Card Set Name", self.parent,
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
        # Check PCS Doesn't Exist
        if PhysicalCardSet.selectBy(name=sPCSName).count() != 0:
            do_complaint_error("Physical Card Set %s already exists." % sPCSName)
            return

        # Create PCS
        oPCS = PhysicalCardSet(name=sPCSName)

        for oCard in self.model.getCardIterator(self.model.getCurrentFilter()):
            oPCS.addPhysicalCard(oCard)

        self.open_pcs(sPCSName)

plugin = DeckFromFilter
