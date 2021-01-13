# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>,
# GPL - see COPYING for details

"""plugin for managing CSV file imports"""

import csv

from gi.repository import GObject, Gtk

from ...core.BaseTables import PhysicalCardSet
from ...io.CSVParser import CSVParser
from ..BasePluginManager import BasePlugin
from ..SutekhDialog import SutekhDialog, do_complaint_error
from ..SutekhFileWidget import SutekhFileButton
from ..GuiCardSetFunctions import import_cs


class BaseCSVImport(BasePlugin):
    """CSV Import plugin.

       Allow the user to select the file, provide information about the
       columns to use and so forth.
       The list of the columns available is updated to reflect the
       currently selected file.
       """
    dTableVersions = {PhysicalCardSet: (4, 5, 6, 7)}
    aModelsSupported = ("MainWindow",)

    def get_menu_item(self):
        """Overrides method from base class. Register on the 'Import' menu"""
        oMenuItem = Gtk.MenuItem(label="Import CSV File")
        oMenuItem.connect("activate", self.activate)
        return ('Import Card Set', oMenuItem)

    def activate(self, _oWidget):
        """Handle response form the user"""
        oDlg = self.make_dialog()
        oDlg.run()

    # pylint: disable=attribute-defined-outside-init
    # defining elements outside of init is OK here, because of plugin structure
    def make_dialog(self):
        """Create the dialog.

           Allow the user to select a file and specify which columns to
           use for card name, card count and expansions.
           """
        self.oDlg = SutekhDialog("Choose CSV File", None,
                                 Gtk.DialogFlags.MODAL |
                                 Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                 ("_OK", Gtk.ResponseType.OK,
                                  "_Cancel", Gtk.ResponseType.CANCEL))
        oLabel = Gtk.Label()
        oLabel.set_markup("<b>Select CSV File ...</b>")
        oLabel.set_alignment(0.0, 0.5)
        self.oDlg.vbox.pack_start(oLabel, False, False, 5)

        self.oFileChooser = SutekhFileButton(self.parent, "Select a CSV File")
        self.oFileChooser.connect("selection-changed",
                                  self._selected_file_changed)
        self.oDlg.vbox.pack_start(self.oFileChooser, True, True, 0)

        self.oDlg.vbox.pack_start(Gtk.HSeparator(), False, False, 5)

        oLabel = Gtk.Label()
        oLabel.set_markup("<b>Select columns containing ...</b>")
        oLabel.set_alignment(0.0, 0.5)
        self.oDlg.vbox.pack_start(oLabel, True, True, 0)

        oNameBox = Gtk.HBox()
        oNameBox.pack_start(Gtk.Label(label="Card name:"), True, True, 0)
        self.oCardNameCombo = self._create_column_selector()
        oNameBox.pack_start(self.oCardNameCombo, True, True, 0)
        self.oDlg.vbox.pack_start(oNameBox, True, True, 0)

        oCountBox = Gtk.HBox()
        oCountBox.pack_start(Gtk.Label(label="Card count:"), True, True, 0)
        self.oCountCombo = self._create_column_selector()
        oCountBox.pack_start(self.oCountCombo, True, True, 0)
        self.oDlg.vbox.pack_start(oCountBox, True, True, 0)

        oExpansionBox = Gtk.HBox()
        oExpansionBox.pack_start(Gtk.Label(label="Expansion name (optional):"),
                                 True, True, 0)
        self.oExpansionCombo = self._create_column_selector()
        oExpansionBox.pack_start(self.oExpansionCombo, True, True, 0)
        self.oDlg.vbox.pack_start(oExpansionBox, True, True, 0)

        self._clear_column_selectors()

        self.oDlg.vbox.pack_start(Gtk.HSeparator(), False, False, 5)

        oLabel = Gtk.Label()
        oLabel.set_markup("<b>Import as ...</b>")
        oLabel.set_alignment(0.0, 0.5)
        self.oDlg.vbox.pack_start(oLabel, True, True, 0)

        oCardSetNameBox = Gtk.HBox()
        oCardSetNameBox.pack_start(Gtk.Label(label="Card Set Name:"),
                                   True, True, 0)
        self.oSetNameEntry = Gtk.Entry()
        oCardSetNameBox.pack_start(self.oSetNameEntry, True, True, 0)
        self.oDlg.vbox.pack_start(oCardSetNameBox, True, True, 0)

        self.oDlg.connect("response", self.handle_response)
        self.oDlg.set_size_request(400, 400)
        self.oDlg.show_all()

        return self.oDlg

    def _selected_file_changed(self, oFileChooser):
        """Update the column selection options for a new file."""
        sFile = oFileChooser.get_filename()

        # pylint: disable=broad-except
        # We want to catch all exceptions here
        try:
            fIn = open(sFile, "rb")
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

        self.oDlg.set_response_sensitive(Gtk.ResponseType.OK, True)
        self._set_column_selectors(aColumns)

    # pylint: disable=no-self-use
    # A method for consistency
    def _create_column_selector(self):
        """Create a combo box from which a column can be selected."""
        oListStore = Gtk.ListStore(GObject.TYPE_INT, GObject.TYPE_STRING)
        oComboBox = Gtk.ComboBox()
        oComboBox.set_model(oListStore)
        oCell = Gtk.CellRendererText()
        oComboBox.pack_start(oCell, True)
        oComboBox.add_attribute(oCell, 'text', 1)
        return oComboBox
    # pylint: enable=no-self-use

    def _clear_column_selectors(self):
        """Clear the column selection lists."""
        # can't click ok until a valid CSV file is chosen
        self.oDlg.set_response_sensitive(Gtk.ResponseType.OK, False)
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
            oCombo.set_active_iter(oListStore.get_iter_first())

    def handle_response(self, _oWidget, oResponse):
        """Handle the user clicking OK on the dialog.

           Do the actual import.
           """
        if oResponse == Gtk.ResponseType.OK:

            # pylint: disable=unbalanced-tuple-unpacking
            # pylint thinks _get_cols isn't returning a list
            iCardNameColumn, iCountColumn, iExpansionColumn = self._get_cols()
            # pylint: enable=unbalanced-tuple-unpacking

            if iCardNameColumn is None or iCountColumn is None:
                sMsg = ("Importing a CSV file requires valid columns for both"
                        " the card names and card counts.")
                do_complaint_error(sMsg)
                self.oDlg.run()
                return

            oParser = CSVParser(iCardNameColumn, iCountColumn,
                                iExpansionColumn, bHasHeader=True)

            sFile = self.oFileChooser.get_filename()

            # pylint: disable=broad-except
            # We want to catch all exceptions here
            try:
                fIn = open(sFile, "rb")
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
