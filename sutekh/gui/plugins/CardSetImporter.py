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
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.core.CardSetHolder import CardSetHolder
from sutekh.core.CardLookup import LookupFailed
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error
from sutekh.gui.SutekhFileWidget import SutekhFileWidget

class ACSImporter(CardListPlugin):
    """Convert a HTML or text deck into an ACS.

       Handles the most common formats, and allows the user to choose
       uri's, so decks published online can be easily imported.
       """
    dTableVersions = { PhysicalCardSet: [5]}
    aModelsSupported = ["MainWindow"]

    # pylint: disable-msg=W0142
    # ** magic OK
    def __init__(self, *aArgs, **kwargs):
        super(ACSImporter, self).__init__(*aArgs, **kwargs)
        # Parser classes should be instantiable using Parser(oCardSetHolder)
        # Parser objects should have a .feed(sLine) method
        self._dParsers = {
            'ELDB HTML File': ELDBHTMLParser,
            'ARDB Text File': ARDBTextParser,
            'ELDB Deck (.eld)': ELDBDeckFileParser,
            'ELDB Inventory': ELDBInventoryParser,
            'ARDB Deck XML File': ARDBXMLDeckParser,
            'ARDB Inventory XML File': ARDBXMLInvParser,
            'JOL Deck File': JOLDeckParser,
            'Lackey CCG Deck File': LackeyDeckParser,
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
        oImport = gtk.MenuItem("Import ARDB or ELDB Card Set")
        oImport.connect("activate", self.make_dialog)
        return ('Import Card Set', oImport)

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

        # FIXME: Add some sort of 'guess format' option for the default,
        # rather than the first one in the _dParsers dict.
        oIter = self._dParsers.iterkeys()
        for sName in oIter:
            self._oFirstBut = gtk.RadioButton(None, sName, False)
            self._oFirstBut.set_active(True)
            self.oDlg.vbox.pack_start(self._oFirstBut, expand=False)
            break
        for sName in oIter:
            oBut = gtk.RadioButton(self._oFirstBut, sName)
            self.oDlg.vbox.pack_start(oBut, expand=False)

        self.oDlg.connect("response", self.handle_response)
        self.oDlg.set_size_request(600, 500)
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
                self.make_cs_from_uri(sUri, cParser)
            elif sFile:
                self.make_cs_from_file(sFile, cParser)

        self.oDlg.destroy()

    def handle_name_response(self, oWidget, oResponse, oDlg, oEntry):
        """Handle the user's clicking on OK or CANCEL in the dialog."""
        if oResponse == gtk.RESPONSE_OK:
            self._sNewName = oEntry.get_text().strip()

    # pylint: enable-msg=W0613

    def make_cs_from_uri(self, sUri, cParser):
        """From an URI, create an Card Set"""
        fIn = urllib2.urlopen(sUri)
        try:
            self.make_cs(fIn, cParser)
        finally:
            fIn.close()

    def make_cs_from_file(self, sFile, cParser):
        """From an fiel, create an Card Set"""
        fIn = file(sFile, "rb")
        try:
            self.make_cs(fIn, cParser)
        finally:
            fIn.close()

    def make_cs(self, fIn, cParser):
        """Create a Abstract card set from the given file object."""
        oHolder = CardSetHolder()

        # pylint: disable-msg=W0703
        # we really do want all the exceptions
        try:
            oParser = cParser(oHolder)
            for sLine in fIn:
                oParser.feed(sLine)
        except Exception, oExp:
            sMsg = "Reading the card set failed with the following error:\n" \
                   "%s\n The file is probably not in the format the Parser" \
                   " expects.\nAborting" % oExp
            do_complaint_error(sMsg)
            # Fail out
            return

        if oHolder.num_entries < 1:
            # No cards seen, so abort
            do_complaint_error("No cards found in the card set.\n"
                    "The file may not be in the format the Parser expects.\n"
                    "Aborting")
            return

        # Check CS Doesn't Exist
        bContinue = False
        # We loop until we have an acceptable name
        while not bContinue:
            bDoNewName = False
            sMsg = ""
            if PhysicalCardSet.selectBy(name=oHolder.name).count() != 0:
                sMsg = "Card Set %s already exists.\n" \
                        "Please choose another name.\n" \
                        "Choose cancel to abort this import." % oHolder.name
                bDoNewName = True
            elif not oHolder.name:
                sMsg = "No name given for the card set\n" \
                        "Please specify a name.\n" \
                        "Choose cancel to abort this import."
                bDoNewName = True
            if bDoNewName:
                if not self.make_name_dialog(sMsg):
                    return
                oHolder.name = self._sNewName
                self._sNewName = ""
            else:
                bContinue = True

        # Create CS
        try:
            oHolder.create_pcs(oCardLookup=self.cardlookup)
        except RuntimeError, oExp:
            sMsg = "Creating the card set failed with the following error:\n"
            sMsg += str(oExp) + "\n"
            sMsg += "The file is probably not in the format the Parser" \
                    " expects\n"
            sMsg += "Aborting"
            do_complaint_error(sMsg)
            return
        except LookupFailed, oExp:
            return

        self.open_cs(oHolder.name)

    def make_name_dialog(self, sMsg):
        """Create a dialog to prompt for a new name"""
        oDlg = SutekhDialog("Choose New Card Set Name", self.parent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                    gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        oLabel = gtk.Label(sMsg)

        oEntry = gtk.Entry(50)
        # Need this so entry box works as expected
        oEntry.connect("activate", self.handle_name_response,
                gtk.RESPONSE_OK, oDlg, oEntry)
        oDlg.connect("response", self.handle_name_response, oDlg, oEntry)

        # pylint: disable-msg=E1101
        # pylint misses vbox methods
        oDlg.vbox.pack_start(oLabel)
        oDlg.vbox.pack_start(oEntry)
        oDlg.show_all()

        iResponse = oDlg.run()
        oDlg.destroy()
        return iResponse == gtk.RESPONSE_OK


# pylint: disable-msg=C0103
# accept plugin name
plugin = ACSImporter
