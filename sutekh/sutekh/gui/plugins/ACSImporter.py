# ACSImporter.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>,
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Convert a ELDB or ARDB text or html file into an Abstract Card Set."""

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
    """Convert a HTML or text deck into an ACS.

       Handles the most common formats, and allows the user to choose
       uri's, so decks published online can be easily imported.
       """
    dTableVersions = { AbstractCardSet: [2, 3]}
    aModelsSupported = [AbstractCard]

    # pylint: disable-msg=W0142
    # ** magic OK
    def __init__(self, *aArgs, **kwargs):
        super(ACSImporter, self).__init__(*aArgs, **kwargs)
        # Parser classes should be instantiable using Parser(oCardSetHolder)
        # Parser objects should have a .feed(sLine) method
        self._dParsers = {
            'ELDB HTML File': ELDBHTMLParser,
            'ARDB Text File': ARDBTextParser,
        }
        self.oUri = None
        self.oDlg = None
        self._oFirstBut = None
        self.oFileChooser = None

    def get_menu_item(self):
        """Register with the 'Plugins' Menu"""
        if not self.check_versions() or not self.check_model_type():
            return None
        oImport = gtk.MenuItem("Import Abstract Card Set")
        oImport.connect("activate", self.make_dialog)
        return ('Plugins', oImport)

    # pylint: disable-msg=W0613
    # oWidget required by signature
    def make_dialog(self, oWidget):
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

        self.oFileChooser = gtk.FileChooserWidget(gtk.FILE_CHOOSER_ACTION_OPEN)
        self.oDlg.vbox.pack_start(self.oFileChooser)

        oIter = self._dParsers.iterkeys()
        for sName in oIter:
            self._oFirstBut = gtk.RadioButton(None, sName, False)
            self._oFirstBut.set_active(True)
            self.oDlg.vbox.pack_start(self._oFirstBut)
            break
        for sName in oIter:
            oBut = gtk.RadioButton(self._oFirstBut, sName)
            self.oDlg.vbox.pack_start(oBut)

        self.oDlg.connect("response", self.handle_response)
        self.oDlg.set_size_request(400, 400)
        self.oDlg.show_all()

        self.oDlg.run()

    def handle_response(self, oWidget, oResponse):
        """Handle the user's clicking on OK or CANCEL in the dialog."""
        if oResponse == gtk.RESPONSE_OK:
            sUri = self.oUri.get_text().strip()
            sFile = self.oFileChooser.get_filename()

            for oBut in self._oFirstBut.get_group():
                sName = oBut.get_label()
                if oBut.get_active():
                    cParser = self._dParsers[sName]

            if sUri:
                self.make_acs_from_uri(sUri, cParser)
            elif sFile:
                self.make_acs_from_file(sFile, cParser)

        self.oDlg.destroy()

    # pylint: enable-msg=W0613

    def make_acs_from_uri(self, sUri, cParser):
        """From an URI, create an Abstract Card Set"""
        fIn = urllib2.urlopen(sUri)
        try:
            self.make_acs(fIn, cParser)
        finally:
            fIn.close()

    def make_acs_from_file(self, sFile, cParser):
        """From an fiel, create an Abstract Card Set"""
        fIn = file(sFile, "rb")
        try:
            self.make_acs(fIn, cParser)
        finally:
            fIn.close()

    def make_acs(self, fIn, cParser):
        """Create a Abstract card set from the given file object."""
        oHolder = CardSetHolder()

        oParser = cParser(oHolder)
        for sLine in fIn:
            oParser.feed(sLine)

        # Check ACS Doesn't Exist
        if AbstractCardSet.selectBy(name=oHolder.name).count() != 0:
            sMsg = "Abstract Card Set %s already exists." % oHolder.name
            do_complaint_error(sMsg)
            return

        # Create ACS
        try:
            oHolder.createACS(oCardLookup=self.cardlookup)
        except RuntimeError, oExp:
            sMsg = "Creating the card set failed with the following error:\n"
            sMsg += str(oExp) + "\n"
            sMsg += "The file is probably not in the format the ELDB Parser" \
                    " expects\n"
            sMsg += "Aborting"
            do_complaint_error(sMsg)
            return
        except LookupFailed, oExp:
            return

        self.open_acs(oHolder.name)

# pylint: disable-msg=C0103
# accept plugin name
plugin = ACSImporter
