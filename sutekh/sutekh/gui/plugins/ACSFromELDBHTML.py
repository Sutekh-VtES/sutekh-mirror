# ACSFromFilter.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
import urllib2
from sutekh.io.ELDBHTMLParser import ELDBHTMLParser
from sutekh.core.SutekhObjects import AbstractCard, AbstractCardSet
from sutekh.core.CardSetHolder import CardSetHolder
from sutekh.core.CardLookup import LookupFailed
from sutekh.gui.GuiCardLookup import GuiLookup
from sutekh.gui.PluginManager import CardListPlugin

class ACSFromELDBHTML(CardListPlugin):
    dTableVersions = { AbstractCardSet: [2,3]}
    aModelsSupported = [AbstractCard]

    def __init__(self,*args,**kws):
        super(ACSFromELDBHTML,self).__init__(*args,**kws)

    def get_menu_item(self):
        """
        Overrides method from base class.
        """
        if not self.check_versions() or not self.check_model_type():
            return None
        iDF = gtk.MenuItem("Abstract Card Set From ELDB HTML")
        iDF.connect("activate", self.activate)
        return iDF

    def get_desired_menu(self):
        return "Plugin"

    def activate(self,oWidget):
        oDlg = self.makeDialog()
        oDlg.run()

    def makeDialog(self):
        parent = self.view.getWindow()

        self.oDlg = gtk.Dialog("Choose ELDB HTML File",None,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                 gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        self.oDlg.vbox.pack_start(gtk.Label("URL:"),expand=False)

        self.oUri = gtk.Entry(150)
        self.oUri.connect("activate", self.handleResponse, gtk.RESPONSE_OK)
        self.oDlg.vbox.pack_start(self.oUri,expand=False)

        self.oDlg.vbox.pack_start(gtk.Label("OR"),expand=False)

        self.oFileChooser = gtk.FileChooserWidget(gtk.FILE_CHOOSER_ACTION_OPEN)
        self.oDlg.vbox.pack_start(self.oFileChooser)

        self.oDlg.connect("response", self.handleResponse)
        self.oDlg.set_size_request(400,300)
        self.oDlg.show_all()

        return self.oDlg

    def handleResponse(self,oWidget,oResponse):
        if oResponse == gtk.RESPONSE_OK:
            sUri = self.oUri.get_text().strip()
            sFile = self.oFileChooser.get_filename()
            if sUri:
                self.makeACSFromUri(sUri)
            elif sFile:
                self.makeACSFromFile(sFile)

        self.oDlg.destroy()

    def makeACSFromUri(self,sUri):
        fIn = urllib2.urlopen(sUri)
        try:
            self.makeACS(fIn)
        finally:
            fIn.close()

    def makeACSFromFile(self,sFile):
        fIn = file(sFile,"rb")
        try:
            self.makeACS(fIn)
        finally:
            fIn.close()

    def makeACS(self,fIn):
        oHolder = CardSetHolder()

        oP = ELDBHTMLParser(oHolder)
        for sLine in fIn:
            oP.feed(sLine)

        # Check ACS Doesn't Exist
        if AbstractCardSet.selectBy(name=oHolder.name).count() != 0:
            sMsg = "Abstract Card Set %s already exists." % oHolder.name
            oComplaint = gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
                                           gtk.BUTTONS_CLOSE, sMsg)
            oComplaint.connect("response",lambda oW, oResp: oW.destroy())
            oComplaint.run()
            return

        # Create ACS
        try:
            # Never need the physical_lookup, so the bogus view is OK
            oHolder.createACS(oCardLookup=GuiLookup())
        except RuntimeError, e:
            sMsg = "Creating the card set failed with the following error:\n"
            sMsg += str(e) + "\n"
            sMsg += "The file is probably not in the format the ELDB Parser expects\n"
            sMsg += "Aborting"
            oComplaint = gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
                                           gtk.BUTTONS_OK, sMsg)
            oComplaint.connect("response",lambda oW, oResp: oW.destroy())
            oComplaint.run()
            return
        except LookupFailed, e:
            return

        parent = self.view.getWindow()
        parent.add_abstract_card_set(oHolder.name)

plugin = ACSFromELDBHTML
