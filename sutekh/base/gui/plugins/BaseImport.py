# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>,
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Convert a ELDB or ARDB text or html file into an Card Set."""

import gtk
from ...io.UrlOps import urlopen_with_timeout
from ...core.BaseTables import PhysicalCardSet
from ..BasePluginManager import BasePlugin
from ..SutekhDialog import SutekhDialog
from ..GuiCardSetFunctions import import_cs
from ..SutekhFileWidget import SutekhFileWidget
from ..GuiDataPack import gui_error_handler

GUESS_FILE_FORMAT = 'Guess File Format'


class BaseImport(BasePlugin):
    """Import a cardset in some format.

       Allows the user to choose uri's, so decks published
       online can be imported, and handles all the footwork
       around imports.
       """
    dTableVersions = {PhysicalCardSet: (5, 6, 7)}
    aModelsSupported = ("MainWindow",)

    PARSERS = {
        # Format:
        # 'Description': (Parser, Filter name, filter),
        # Filter name may be None, in which case nothing is added
        # filter is a list of filter patterns
        # Duplicate filter names will be silently skipped.
        #
        #   i.e.
        # 'Lackey File': (LackeyParser, 'TXT files', ['*.txt']),
        # 'JOL File': (JOLParser, None, None),
        #
        # Parser classes should be instantiable using Parser()
        # Parser objects should have a .parse(oFile, oCardSetHolder) method
        # (see the interface in IOBase)
        #
        # A parser with the description 'Guess File Format' is treated
        # specially and added as the first on the list, otherwise they
        # are sorted alphabetically
    }

    def __init__(self, *aArgs, **kwargs):
        super(BaseImport, self).__init__(*aArgs, **kwargs)
        self.oUri = None
        self.oDlg = None
        self._oFirstBut = None
        self.oFileChooser = None
        self._sNewName = ''

    def get_menu_item(self):
        """Register with the 'Import' Menu"""
        oImport = gtk.MenuItem("Import Card Set in other formats")
        oImport.connect("activate", self.make_dialog)
        return ('Import Card Set', oImport)

    def make_dialog(self, _oWidget):
        """Create the dialog asking the user for the source to import."""
        self.oDlg = SutekhDialog("Choose Card Set File or URL", None,
                                 gtk.DIALOG_MODAL |
                                 gtk.DIALOG_DESTROY_WITH_PARENT,
                                 (gtk.STOCK_OK, gtk.RESPONSE_OK,
                                  gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        self.oDlg.vbox.pack_start(gtk.Label("URL:"), expand=False)

        self.oUri = gtk.Entry(150)
        self.oUri.connect("activate", self.handle_response, gtk.RESPONSE_OK)
        self.oDlg.vbox.pack_start(self.oUri, expand=False)

        self.oDlg.vbox.pack_start(gtk.Label("OR"), expand=False)

        self.oFileChooser = SutekhFileWidget(self.parent,
                                             gtk.FILE_CHOOSER_ACTION_OPEN)
        aAddedFilters = set()  # Guard against adding filter multiple times
        for tInfo in self.PARSERS.values():
            if tInfo[1] and tInfo[1] not in aAddedFilters:
                # Add the filter
                self.oFileChooser.add_filter_with_pattern(tInfo[1], tInfo[2])
                aAddedFilters.add(tInfo[1])
        self.oFileChooser.default_filter()
        self.oDlg.vbox.pack_start(self.oFileChooser, expand=True)

        # If there's a 'Guess File Format' option, set it to the first button
        if GUESS_FILE_FORMAT in self.PARSERS:
            self._oFirstBut = gtk.RadioButton(None, GUESS_FILE_FORMAT, False)
            self._oFirstBut.set_active(True)
            self.oDlg.vbox.pack_start(self._oFirstBut, expand=False)

        oTable = gtk.Table(len(self.PARSERS) // 2, 2)
        self.oDlg.vbox.pack_start(oTable, expand=False)
        iXPos, iYPos = 0, 0
        for sName in sorted(self.PARSERS):
            if sName == GUESS_FILE_FORMAT:
                continue
            if self._oFirstBut:
                oBut = gtk.RadioButton(self._oFirstBut, sName)
            else:
                # No first button (no 'Guess File Format' case) so add it
                self._oFirstBut = gtk.RadioButton(None, sName, False)
                self._oFirstBut.set_active(True)
                oBut = self._oFirstBut
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
                    cParser = self.PARSERS[sName][0]

            if sUri:
                self.make_cs_from_uri(sUri, cParser)
            elif sFile:
                self.make_cs_from_file(sFile, cParser)

        self.oDlg.destroy()

    def make_cs_from_uri(self, sUri, cParser):
        """From an URI, create an Card Set"""
        fIn = urlopen_with_timeout(sUri,
                                   fErrorHandler=gui_error_handler)
        if not fIn:
            # probable timeout, so bail
            return
        try:
            import_cs(fIn, cParser(), self.parent)
        finally:
            fIn.close()

    def make_cs_from_file(self, sFile, cParser):
        """From an file, create an Card Set"""
        fIn = open(sFile, "rb")
        try:
            import_cs(fIn, cParser(), self.parent)
        finally:
            fIn.close()
