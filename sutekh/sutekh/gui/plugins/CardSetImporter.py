# CardSetImporter.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>,
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Convert a ELDB or ARDB text or html file into an Card Set."""

import gtk
import urllib2
from sutekh.io.ELDBHTMLParser import ELDBHTMLParser
from sutekh.io.ARDBTextParser import ARDBTextParser
from sutekh.io.ARDBXMLDeckParser import ARDBXMLDeckParser
from sutekh.io.ARDBXMLInvParser import ARDBXMLInvParser
from sutekh.io.ELDBDeckFileParser import ELDBDeckFileParser
from sutekh.io.ELDBInventoryParser import ELDBInventoryParser
from sutekh.io.JOLDeckParser import JOLDeckParser
from sutekh.io.LackeyDeckParser import LackeyDeckParser
from sutekh.io.GuessFileParser import GuessFileParser
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.gui.SutekhDialog import SutekhDialog
from sutekh.gui.GuiCardSetFunctions import import_cs
from sutekh.gui.SutekhFileWidget import SutekhFileWidget


class ACSImporter(SutekhPlugin):
    """Convert a HTML or text deck into an ACS.

       Handles the most common formats, and allows the user to choose
       uri's, so decks published online can be easily imported.
       """
    dTableVersions = {PhysicalCardSet: (5, 6)}
    aModelsSupported = ("MainWindow",)

    # pylint: disable-msg=W0142
    # ** magic OK
    def __init__(self, *aArgs, **kwargs):
        super(ACSImporter, self).__init__(*aArgs, **kwargs)
        # Parser classes should be instantiable using Parser()
        # Parser objects should have a .parse(oFile, oCardSetHolder) method
        # (see the interface in IOBase)
        self._dParsers = {
            'ELDB HTML File': ELDBHTMLParser,
            'ARDB Text File': ARDBTextParser,
            'ELDB Deck (.eld)': ELDBDeckFileParser,
            'ELDB Inventory': ELDBInventoryParser,
            'ARDB Deck XML File': ARDBXMLDeckParser,
            'ARDB Inventory XML File': ARDBXMLInvParser,
            'JOL Deck File': JOLDeckParser,
            'Lackey CCG Deck File': LackeyDeckParser,
            'Guess file format': GuessFileParser,
        }
        self.oUri = None
        self.oDlg = None
        self._oFirstBut = None
        self.oFileChooser = None
        self._sNewName = ''

    def get_menu_item(self):
        """Register with the 'Import' Menu"""
        if not self.check_versions() or not self.check_model_type():
            return None
        oImport = gtk.MenuItem("Import Card Set in other formats")
        oImport.connect("activate", self.make_dialog)
        return ('Import Card Set', oImport)

    def make_dialog(self, _oWidget):
        """Create the dialog asking the user for the source to import."""
        self.oDlg = SutekhDialog("Choose Card Set File or URL", None,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                 gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        # pylint: disable-msg=E1101
        # vbox confuses pylint
        self.oDlg.vbox.pack_start(gtk.Label("URL:"), expand=False)

        self.oUri = gtk.Entry(150)
        self.oUri.connect("activate", self.handle_response, gtk.RESPONSE_OK)
        self.oDlg.vbox.pack_start(self.oUri, expand=False)

        self.oDlg.vbox.pack_start(gtk.Label("OR"), expand=False)

        self.oFileChooser = SutekhFileWidget(self.parent,
                gtk.FILE_CHOOSER_ACTION_OPEN)
        self.oFileChooser.add_filter_with_pattern('HTML files', ['*.html',
            '*.htm'])
        self.oFileChooser.add_filter_with_pattern('TXT files', ['*.txt'])
        self.oFileChooser.add_filter_with_pattern('ELD files', ['*.eld'])
        self.oFileChooser.add_filter_with_pattern('XML files', ['*.xml'])
        self.oFileChooser.add_filter_with_pattern('CSV files', ['*.csv'])
        self.oFileChooser.default_filter()
        self.oDlg.vbox.pack_start(self.oFileChooser)

        self._oFirstBut = gtk.RadioButton(None, 'Guess file format', False)
        self._oFirstBut.set_active(True)
        self.oDlg.vbox.pack_start(self._oFirstBut, expand=False)
        oTable = gtk.Table(len(self._dParsers) / 2, 2)
        self.oDlg.vbox.pack_start(oTable)
        oIter = self._dParsers.iterkeys()
        iXPos, iYPos = 0, 0
        for sName in oIter:
            if sName == 'Guess file format':
                continue
            oBut = gtk.RadioButton(self._oFirstBut, sName)
            oTable.attach(oBut, iXPos, iXPos + 1, iYPos, iYPos + 1)
            iXPos += 1
            if iXPos > 1:
                iXPos = 0
                iYPos += 1

        self.oDlg.connect("response", self.handle_response)
        self.oDlg.set_size_request(600, 500)
        self.oDlg.show_all()

        self.oDlg.run()

    def handle_response(self, _oWidget, oResponse):
        """Handle the user's clicking on OK or CANCEL in the dialog."""
        if oResponse == gtk.RESPONSE_OK:
            sUri = self.oUri.get_text().strip()
            sFile = self.oFileChooser.get_filename()

            for oBut in self._oFirstBut.get_group():
                sName = oBut.get_label()
                if oBut.get_active():
                    cParser = self._dParsers[sName]

            if sUri:
                self.make_cs_from_uri(sUri, cParser)
            elif sFile:
                self.make_cs_from_file(sFile, cParser)

        self.oDlg.destroy()

    def make_cs_from_uri(self, sUri, cParser):
        """From an URI, create an Card Set"""
        fIn = urllib2.urlopen(sUri)
        try:
            import_cs(fIn, cParser(), self.parent)
        finally:
            fIn.close()

    def make_cs_from_file(self, sFile, cParser):
        """From an file, create an Card Set"""
        fIn = file(sFile, "rb")
        try:
            import_cs(fIn, cParser(), self.parent)
        finally:
            fIn.close()


plugin = ACSImporter
