# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""Plugin to import selected card sets from a zip file"""

import os
from logging import Logger

from gi.repository import GLib, GObject, Gtk

from ..BasePluginManager import BasePlugin
from ..SutekhDialog import (SutekhDialog, do_complaint_error,
                            do_exception_complaint)
from ..SutekhFileWidget import ZipFileDialog
from ..ProgressDialog import ProgressDialog, SutekhCountLogHandler
from ..ScrolledList import ScrolledList
from ..GuiCardSetFunctions import (reparent_all_children,
                                   update_open_card_sets, get_import_name,
                                   PROMPT, RENAME, REPLACE)


def _do_rename_parent(sOldName, sNewName, dRemaining):
    """Handle the renaming of a parent card set in the unprocessed list."""
    dResult = {}
    for sName, tInfo in dRemaining.items():
        if tInfo[3] == sOldName:
            dResult[sName] = (tInfo[0], tInfo[1], tInfo[2], sNewName)
        else:
            dResult[sName] = tInfo
    return dResult


def _set_selected_rows(_oButton, oScrolledList, aData):
    """Helper to manage changing the se;ection of the scrolled list"""
    oScrolledList.set_selected_rows(aData)


class ZipFileDirStore(Gtk.TreeStore):
    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so many public methods
    """Simple tree store to show card set hierachy in a ScrolledList widget"""
    def __init__(self):
        super().__init__(GObject.TYPE_STRING)

    def fill_list(self, dEscapedList):
        """Fill the list"""
        self.clear()
        aNames = sorted(dEscapedList)
        dAdded = {}
        while aNames:
            for sEntry in aNames[:]:
                sParent = dEscapedList[sEntry][3]
                if sParent:
                    # Need escaped version for comparisons
                    sParent = GLib.markup_escape_text(sParent)
                oIter = None
                if sParent in dAdded:
                    oParIter = dAdded[sParent]
                    oIter = self.append(oParIter)
                elif sParent is None or sParent not in aNames:
                    oIter = self.append(None)
                else:
                    # Can't add this entry yet, so look at next one
                    continue
                self.set(oIter, 0, sEntry)
                dAdded[sEntry] = oIter
                aNames.remove(sEntry)
        self.set_sort_column_id(0, Gtk.SortType.ASCENDING)  # Sort the display


class SelectZipFileContents(SutekhDialog):
    """Dialog for querying contents of the zip file"""
    # pylint: disable=too-many-public-methods
    # Gtk.Dialog, so lots of public methods

    def __init__(self, dEscapedList, oParent):
        super().__init__(
            "Select Card Sets to Import", oParent,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            ("_OK", Gtk.ResponseType.OK,
             "_Cancel", Gtk.ResponseType.CANCEL))

        self.dEscapedList = dEscapedList

        oModel = ZipFileDirStore()

        # Ask user to select entries to import
        self.oScrolledList = ScrolledList('Available Card Sets', oModel)
        self.vbox.pack_start(self.oScrolledList, True, True, 0)
        self.oScrolledList.set_size_request(450, 300)
        self.oScrolledList.fill_list(self.dEscapedList)
        self.oScrolledList.view.expand_all()
        # Add the various buttons
        # Select all and unselect all
        oSelectAll = Gtk.Button('Select All')
        oUnSelectAll = Gtk.Button('Unselect All')
        oSelectAll.connect('clicked', _set_selected_rows,
                           self.oScrolledList, self.dEscapedList)
        oUnSelectAll.connect('clicked', _set_selected_rows,
                             self.oScrolledList, [])
        oSelectButtons = Gtk.VBox(homogeneous=False, spacing=2)
        oSelectButtons.pack_start(oSelectAll, False, True, 0)
        oSelectButtons.pack_start(oUnSelectAll, False, True, 0)
        self.oPrompt = Gtk.RadioButton(group=None, label='Always Ask')
        self.oPrompt.set_active(True)
        self.oReplace = Gtk.RadioButton(
            group=self.oPrompt, label='Always replace with new card set')
        self.oReplace.set_active(False)
        self.oRename = Gtk.RadioButton(group=self.oPrompt,
                                       label='Always create unique name')
        self.oRename.set_active(False)
        oRadioButs = Gtk.VBox(homogeneous=False, spacing=2)
        oRadioLabel = Gtk.Label()
        oRadioLabel.set_markup('<b>How to handle card set name conflicts?</b>')
        oRadioButs.pack_start(oRadioLabel, True, True, 0)
        oRadioButs.pack_start(self.oPrompt, False, True, 0)
        oRadioButs.pack_start(self.oReplace, False, True, 0)
        oRadioButs.pack_start(self.oRename, False, True, 0)

        oButtons = Gtk.HBox(False, 2)
        oButtons.pack_start(oSelectButtons, False, True, 0)
        oButtons.pack_start(oRadioButs, True, True, 0)
        self.vbox.pack_start(oButtons, False, True, 0)

        self.show_all()

    def get_clash_mode(self):
        """Return the selected clash mode"""
        if self.oRename.get_active():
            return RENAME
        if self.oReplace.get_active():
            return REPLACE
        return PROMPT

    def get_selected(self):
        """Get the list of selected card sets"""
        dSelected = {}
        for sName in self.oScrolledList.get_selection():
            dSelected[sName] = self.dEscapedList[sName]
        return dSelected


class BaseZipImport(BasePlugin):
    """Extract selected card sets from a zip file."""
    dTableVersions = {}
    aModelsSupported = ("MainWindow",)

    cZipWrapper = None

    sMenuName = "Import Card Set(s) from zip file"

    sHelpCategory = "card_list:file"

    sHelpText = """This option allows you to select some or all of
                   the Card Sets included in a zip file (such as those
                   produced by backups) and import them into the database.
                   Unlike restoring a backup, this does not replace any
                   existing card sets automatically.

                   After selecting the zip file, you will be asked to
                   select the card sets to import from the list of card
                   sets in the zip file. If any of the card sets share
                   the same name as an existing card set, you will be
                   asked either to rename the card set, or skip importing
                   that card set.

                   If a card set to be imported has a parent card set, and
                   that set cannot be found, the card set will be imported
                   with no parent set."""

    # Dialog and Menu Item Creation

    def get_menu_item(self):
        """Register on the Plugins menu"""
        oImport = Gtk.MenuItem(label=self.sMenuName)
        oImport.connect("activate", self.make_dialog)
        return ('Import Card Set', oImport)

    # Menu responses

    def make_dialog(self, _oWidget):
        """Create the dialog used to select the zip file"""
        sName = "Select zip file to import from."

        oDlg = ZipFileDialog(self.parent, sName, Gtk.FileChooserAction.OPEN)
        oDlg.show_all()
        oDlg.run()

        sFilename = oDlg.get_name()
        if sFilename:
            self.handle_response(sFilename)

    def handle_response(self, sFilename):
        """Handle response from the import dialog"""
        if not os.path.exists(sFilename):
            do_complaint_error("Backup file %s does not seem to exist."
                               % sFilename)
            return

        # pylint: disable=not-callable
        # subclasses will provide a callable cZipWrapper
        oFile = self.cZipWrapper(sFilename)
        # pylint: enable=not-callable
        dList = oFile.get_all_entries()
        dEscapedList = {}
        for sName, tInfo in dList.items():
            dEscapedList[self._escape(sName)] = (sName, tInfo[0], tInfo[1],
                                                 tInfo[2])

        oSelDlg = SelectZipFileContents(dEscapedList, self.parent)
        oResponse = oSelDlg.run()
        dSelected = oSelDlg.get_selected()
        iClashMode = oSelDlg.get_clash_mode()
        oSelDlg.destroy()
        if oResponse == Gtk.ResponseType.OK and dSelected:
            self.do_read_list(oFile, dSelected, iClashMode)

    def do_read_list(self, oFile, dSelected, iClashMode):
        """Read the selected list of card sets"""
        oLogHandler = SutekhCountLogHandler()
        oProgressDialog = ProgressDialog()
        oProgressDialog.set_description("Importing Files")
        oLogger = Logger('Read zip file')
        oLogger.addHandler(oLogHandler)
        oLogHandler.set_dialog(oProgressDialog)
        oLogHandler.set_total(len(dSelected))
        oProgressDialog.show()
        while dSelected:
            dSelected = self._read_heart(oFile, dSelected, oLogger, iClashMode)
        oProgressDialog.destroy()

    def _read_heart(self, oFile, dSelected, oLogger, iClashMode):
        """Heart of the reading loop - ensure we read parents before
           children, and correct for renames that occur."""
        # pylint: disable=broad-except, too-many-locals
        # we really do want all the exceptions
        # Use track a lot of state, so many local variables
        dRemaining = {}
        dRenames = {}
        for sEscapedName, tInfo in dSelected.items():
            sName, sFilename, bParentExists, sParentName = tInfo
            # We aim to ensure that we always keep loaded card sets together,
            # so if the parent name clashes, we want to follow the renamed
            # parent, rather than be added to the existing card set of the
            # same name
            if sParentName is not None and sParentName in dSelected and \
                    sParentName not in dRenames:
                # Do have a parent to look at, so skip for now
                if not bParentExists:
                    # The parent is in the list of cards to read, so it
                    # will exist when we get to it
                    dRemaining[sEscapedName] = (sName, sFilename, True,
                                                sParentName)
                else:
                    dRemaining[sEscapedName] = tInfo
                continue
            elif sParentName is not None and sParentName in dRenames:
                # Renamed parent, so adjust this - this will also correctly
                # handle cards that no longer need a parent, since it will
                # set sParentName to None
                sParentName = dRenames[sParentName]
            elif not bParentExists:
                # Parent doesn't exist, but isn't in the list, so turn into
                # top level card set
                sParentName = None
            try:
                oCardSetHolder = oFile.read_single_card_set(sFilename)
                oLogger.info('Read %s' % sName)
                # Ask the user whether to rename, replace or cancel
                oCardSetHolder, aChildren = get_import_name(
                    oCardSetHolder, iClashMode)
                dRenames[sName] = oCardSetHolder.name
                # Check for cardsets that were waiting for us
                dRemaining = _do_rename_parent(sName, oCardSetHolder.name,
                                               dRemaining)
                if not oCardSetHolder.name:
                    # We skip this card set
                    continue
                # Ensure we use the right name for the parent
                oCardSetHolder.parent = sParentName
                oCardSetHolder.create_pcs(self.cardlookup)
                reparent_all_children(oCardSetHolder.name, aChildren)
                if self.parent.find_cs_pane_by_set_name(oCardSetHolder.name):
                    # Already open, so update to changes
                    update_open_card_sets(oCardSetHolder.name, self.parent)
                self._reload_pcs_list()
            except Exception as oException:
                sMsg = "Failed to import card set %s.\n\n%s" % (sName,
                                                                oException)
                do_exception_complaint(sMsg)
        return dRemaining
