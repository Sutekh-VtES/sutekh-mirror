# ACSFromFilter.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
import urllib2
from sutekh.ELDBHTMLParser import ELDBHTMLParser
from sutekh.SutekhObjects import AbstractCardSet
from sutekh.gui.PluginManager import CardListPlugin

class ACSFromELDBHTML(CardListPlugin):
    dTableVersions = { "AbstractCardSet" : [2,3]}
    aModelsSupported = ["AbstractCard"]

    def __init__(self,*args,**kws):
        super(ACSFromELDBHTML,self).__init__(*args,**kws)

    def getMenuItem(self):
        """
        Overrides method from base class.
        """
        if not self.checkVersions() or not self.checkModelType():
            return None
        iDF = gtk.MenuItem("Abstract Card Set From ELDB HTML")
        iDF.connect("activate", self.activate)
        return iDF

    def getDesiredMenu(self):
        return "Plugin"

    def activate(self,oWidget):
        oDlg = self.makeDialog()
        oDlg.run()

    def makeDialog(self):
        parent = self.view.getWindow()

        self.oDlg = gtk.Dialog("Choose ELDB HTML File",parent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                 gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        self.oDlg.vbox.pack_start(gtk.Label("URL:"))

        self.oUri = gtk.Entry(50)
        self.oUri.connect("activate", self.handleResponse, gtk.RESPONSE_OK)
        self.oDlg.vbox.pack_start(self.oUri)

        self.oDlg.vbox.pack_start(gtk.Label("OR"))

        self.oFileChooser = gtk.FileChooserWidget(gtk.FILE_CHOOSER_ACTION_OPEN)
        self.oDlg.vbox.pack_start(self.oFileChooser)

        self.oDlg.connect("response", self.handleResponse)
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
        oP = ELDBHTMLParser()
        for sLine in fIn:
            oP.feed(sLine)
        oHolder = oP.holder()

        # Check ACS Doesn't Exist
        if AbstractCardSet.selectBy(name=oHolder.name).count() != 0:
            oComplaint = gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
                                           gtk.BUTTONS_CLOSE,
                                           "Abstract Card Set %s already exists." % oHolder.name)
            oComplaint.connect("response",lambda oW, oResp: oW.destroy())
            oComplaint.run()
            return

        # Create ACS
        oHolder.createACS()

        parent = self.view.getWindow()
        parent.getManager().reloadCardSetLists()

plugin = ACSFromELDBHTML
