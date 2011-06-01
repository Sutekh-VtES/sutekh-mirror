# CSVImporter.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>,
# GPL - see COPYING for details

"""plugin for managing CSV file imports"""

import gtk
import csv
import gobject
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.io.CSVParser import CSVParser
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error
from sutekh.gui.SutekhFileWidget import SutekhFileButton
from sutekh.gui.GuiCardSetFunctions import import_cs


class CSVImporter(SutekhPlugin):
    """CSV Import plugin.

       Allow the user to select the file, provide information about the
       columns to use and so forth.
       The list of the columns available is updated to reflect the
       currently selected file.
       """
    dTableVersions = {
        PhysicalCardSet: (4, 5, 6),
    }
    aModelsSupported = ("MainWindow",)

    def get_menu_item(self):
        """Overrides method from base class. Register on the 'Import' menu"""
        if not self.check_versions() or not self.check_model_type():
            return None
        oMenuItem = gtk.MenuItem("Import CSV File")
        oMenuItem.connect("activate", self.activate)
        return ('Import Card Set', oMenuItem)

    def activate(self, _oWidget):
        """Handle response form the user"""
        oDlg = self.make_dialog()
        oDlg.run()

    # pylint: disable-msg=W0201
    # defining elements outside of init is OK here, because of plugin structure
    def make_dialog(self):
        """Create the dialog.

           Allow the user to select a file and specify which columns to
           use for card name, card count and expansions.
           """
        self.oDlg = SutekhDialog("Choose CSV File", None,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                 gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        oLabel = gtk.Label()
        oLabel.set_markup("<b>Select CSV File ...</b>")
        oLabel.set_alignment(0.0, 0.5)
        # pylint: disable-msg=E1101
        # vbox confuses pylint
        self.oDlg.vbox.pack_start(oLabel, padding=5)

        self.oFileChooser = SutekhFileButton(self.parent, "Select a CSV File")
        self.oFileChooser.connect("selection-changed",
                                  self._selected_file_changed)
        self.oDlg.vbox.pack_start(self.oFileChooser)

        self.oDlg.vbox.pack_start(gtk.HSeparator(), padding=5)

        oLabel = gtk.Label()
        oLabel.set_markup("<b>Select columns containing ...</b>")
        oLabel.set_alignment(0.0, 0.5)
        self.oDlg.vbox.pack_start(oLabel)

        oNameBox = gtk.HBox()
        oNameBox.pack_start(gtk.Label("Card name:"))
        self.oCardNameCombo = self._create_column_selector()
        oNameBox.pack_start(self.oCardNameCombo)
        self.oDlg.vbox.pack_start(oNameBox)

        oCountBox = gtk.HBox()
        oCountBox.pack_start(gtk.Label("Card count:"))
        self.oCountCombo = self._create_column_selector()
        oCountBox.pack_start(self.oCountCombo)
        self.oDlg.vbox.pack_start(oCountBox)

        oExpansionBox = gtk.HBox()
        oExpansionBox.pack_start(gtk.Label("Expansion name (optional):"))
        self.oExpansionCombo = self._create_column_selector()
        oExpansionBox.pack_start(self.oExpansionCombo)
        self.oDlg.vbox.pack_start(oExpansionBox)

        self._clear_column_selectors()

        self.oDlg.vbox.pack_start(gtk.HSeparator(), padding=5)

        oLabel = gtk.Label()
        oLabel.set_markup("<b>Import as ...</b>")
        oLabel.set_alignment(0.0, 0.5)
        self.oDlg.vbox.pack_start(oLabel)

        oCardSetNameBox = gtk.HBox()
        oCardSetNameBox.pack_start(gtk.Label("Card Set Name:"))
        self.oSetNameEntry = gtk.Entry()
        oCardSetNameBox.pack_start(self.oSetNameEntry)
        self.oDlg.vbox.pack_start(oCardSetNameBox)

        self.oDlg.connect("response", self.handle_response)
        self.oDlg.set_size_request(400, 400)
        self.oDlg.show_all()

        return self.oDlg

    def _selected_file_changed(self, oFileChooser):
        """Update the column selection options for a new file."""
        sFile = oFileChooser.get_filename()

        # pylint: disable-msg=W0703
        # We want to catch all exceptions here
        try:
            fIn = file(sFile, "rb")
        except Exception:
            self._clear_column_selectors()
            return

        try:
            sLine1 = fIn.next()
            sLine2 = fIn.next()
        except Exception:
            fIn.close()
            self._clear_column_selectors()
            return

        fIn.close()

        try:
            oCsv = csv.reader([sLine1, sLine2])
            aRow = oCsv.next()
            sSample = sLine1 + "\n" + sLine2
            oSniff = csv.Sniffer()
            bHasHeader = oSniff.has_header(sSample)
        except (Exception, csv.Error):
            self._clear_column_selectors()
            return

        if bHasHeader:
            aColumns = [(-1, '-')] + list(enumerate(aRow))
        else:
            aColumns = [(-1, '-')] + [(i, str(i)) for i in range(len(aRow))]

        self.oDlg.set_response_sensitive(gtk.RESPONSE_OK, True)
        self._set_column_selectors(aColumns)

    # pylint: disable-msg=R0201
    # A method for consistency
    def _create_column_selector(self):
        """Create a combo box from which a column can be selected."""
        oListStore = gtk.ListStore(gobject.TYPE_INT, gobject.TYPE_STRING)
        oComboBox = gtk.ComboBox(oListStore)
        oCell = gtk.CellRendererText()
        oComboBox.pack_start(oCell, True)
        oComboBox.add_attribute(oCell, 'text', 1)
        return oComboBox
    # pylint: enable-msg=R0201

    def _clear_column_selectors(self):
        """Clear the column selection lists."""
        # can't click ok until a valid CSV file is chosen
        self.oDlg.set_response_sensitive(gtk.RESPONSE_OK, False)
        self._set_column_selectors([(-1, '-')])

    def _set_column_selectors(self, aColumns):
        """Set the contents of the column selection widgets."""
        for oCombo in (self.oCardNameCombo, self.oCountCombo,
                       self.oExpansionCombo):
            oListStore = oCombo.get_model()
            oListStore.clear()
            for iRow, sHeading in aColumns:
                oIter = oListStore.append(None)
                oListStore.set(oIter, 0, iRow, 1, sHeading)
            oCombo.set_active_iter(oListStore.get_iter_root())

    def handle_response(self, _oWidget, oResponse):
        """Handle the user clicking OK on the dialog.

           Do the actual import.
           """
        if oResponse == gtk.RESPONSE_OK:

            iCardNameColumn, iCountColumn, iExpansionColumn = self._get_cols()

            if iCardNameColumn is None or iCountColumn is None:
                sMsg = "Importing a CSV file requires valid columns for both" \
                        " the card names and card counts."
                do_complaint_error(sMsg)
                self.oDlg.run()
                return

            oParser = CSVParser(iCardNameColumn, iCountColumn,
                                iExpansionColumn, bHasHeader=True)

            sFile = self.oFileChooser.get_filename()

            # pylint: disable-msg=W0703
            # We want to catch all exceptions here
            try:
                fIn = file(sFile, "rb")
            except Exception:
                do_complaint_error("Could not open file '%s'." % sFile)
                self.oDlg.destroy()
                return

            # Tread the well-worn import path
            sSetName = self.oSetNameEntry.get_text().strip()
            import_cs(fIn, oParser, self.parent, sSetName)

        self.oDlg.destroy()

    def _get_cols(self):
        """Get the columns of interest from the user's choices"""
        aCols = []
        for oCombo in (self.oCardNameCombo, self.oCountCombo,
                       self.oExpansionCombo):
            oIter = oCombo.get_active_iter()
            oModel = oCombo.get_model()
            if oIter is None:
                aCols.append(None)
            else:
                iVal = oModel.get_value(oIter, 0)
                if iVal < 0:
                    aCols.append(None)
                else:
                    aCols.append(iVal)
        return aCols


plugin = CSVImporter
