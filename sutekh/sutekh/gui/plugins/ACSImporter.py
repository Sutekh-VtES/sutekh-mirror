# ACSImporter.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>,
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
import urllib2
from sutekh.io.ELDBHTMLParser import ELDBHTMLParser
from sutekh.io.ARDBTextParser import ARDBTextParser
from sutekh.core.SutekhObjects import AbstractCard, AbstractCardSet
from sutekh.core.CardSetHolder import CardSetHolder
from sutekh.core.CardLookup import LookupFailed
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error

class ACSImporter(CardListPlugin):
    dTableVersions = { AbstractCardSet: [2,3]}
    aModelsSupported = [AbstractCard]

    def __init__(self,*args,**kws):
        super(ACSImporter,self).__init__(*args,**kws)
        # Parser classes should be instantiable using Parser(oCardSetHolder)
        # Parser objects should have a .feed(sLine) method
        self._dParsers = {
            'ELDB HTML File': ELDBHTMLParser,
            'ARDB Text File': ARDBTextParser,
        }

    def get_menu_item(self):
        """
        Overrides method from base class.
        """
        if not self.check_versions() or not self.check_model_type():
            return None
        iDF = gtk.MenuItem("Import Abstract Card Set")
        iDF.connect("activate", self.activate)
        return iDF

    def get_desired_menu(self):
        return "Plugins"

    def activate(self,oWidget):
        oDlg = self.makeDialog()
        oDlg.run()

    def makeDialog(self):
        self.oDlg = SutekhDialog("Choose Card Set File or URL",None,
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

        oIter = self._dParsers.iteritems()
        for sName, cParser in oIter:
            self._oFirstBut = gtk.RadioButton(None,sName,False)
            self._oFirstBut.set_active(True)
            self.oDlg.vbox.pack_start(self._oFirstBut)
            break
        for sName, cParser in oIter:
            oBut = gtk.RadioButton(self._oFirstBut,sName)
            self.oDlg.vbox.pack_start(oBut)

        self.oDlg.connect("response", self.handleResponse)
        self.oDlg.set_size_request(400,400)
        self.oDlg.show_all()

        return self.oDlg

    def handleResponse(self,oWidget,oResponse):
        if oResponse == gtk.RESPONSE_OK:
            sUri = self.oUri.get_text().strip()
            sFile = self.oFileChooser.get_filename()

            for oBut in self._oFirstBut.get_group():
                sName = oBut.get_label()
                if oBut.get_active(): cParser = self._dParsers[sName]

            if sUri:
                self.makeACSFromUri(sUri,cParser)
            elif sFile:
                self.makeACSFromFile(sFile,cParser)

        self.oDlg.destroy()

    def makeACSFromUri(self,sUri,cParser):
        fIn = urllib2.urlopen(sUri)
        try:
            self.makeACS(fIn,cParser)
        finally:
            fIn.close()

    def makeACSFromFile(self,sFile,cParser):
        fIn = file(sFile,"rb")
        try:
            self.makeACS(fIn,cParser)
        finally:
            fIn.close()

    def makeACS(self,fIn,cParser):
        oHolder = CardSetHolder()

        oP = cParser(oHolder)
        for sLine in fIn:
            oP.feed(sLine)

        # Check ACS Doesn't Exist
        if AbstractCardSet.selectBy(name=oHolder.name).count() != 0:
            sMsg = "Abstract Card Set %s already exists." % oHolder.name
            do_complaint_error(sMsg)
            return

        # Create ACS
        try:
            oHolder.createACS(oCardLookup=self.cardlookup)
        except RuntimeError, e:
            sMsg = "Creating the card set failed with the following error:\n"
            sMsg += str(e) + "\n"
            sMsg += "The file is probably not in the format the ELDB Parser expects\n"
            sMsg += "Aborting"
            do_complaint_error(sMsg)
            return
        except LookupFailed, e:
            return

        self.open_acs(oHolder.name)

plugin = ACSImporter
