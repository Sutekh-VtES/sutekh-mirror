# ImportFromZipFile.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""Plugin to import selected card sets from a zip file"""

import gtk
import gobject
import os
from logging import Logger
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error, \
        do_exception_complaint
from sutekh.gui.SutekhFileWidget import ZipFileDialog
from sutekh.gui.ProgressDialog import ProgressDialog, SutekhCountLogHandler
from sutekh.gui.ScrolledList import ScrolledList
from sutekh.io.ZipFileWrapper import ZipFileWrapper
from sutekh.gui.GuiCardSetFunctions import reparent_all_children, \
        update_open_card_sets, get_import_name, PROMPT, RENAME, REPLACE


def _do_rename_parent(sOldName, sNewName, dRemaining):
    """Handle the renaming of a parent card set in the unprocessed list."""
    dResult = {}
    for sName, tInfo in dRemaining.iteritems():
        if tInfo[3] == sOldName:
            dResult[sName] = (tInfo[0], tInfo[1], tInfo[2], sNewName)
        else:
            dResult[sName] = tInfo
    return dResult


def _set_selected_rows(_oButton, oScrolledList, aData):
    """Helper to manage changing the se;ection of the scrolled list"""
    oScrolledList.set_selected_rows(aData)


class ZipFileDirStore(gtk.TreeStore):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """Simple tree store to show card set hierachy in a ScrolledList widget"""
    def __init__(self):
        super(ZipFileDirStore, self).__init__(gobject.TYPE_STRING)

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
                    sParent = gobject.markup_escape_text(sParent)
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
        self.set_sort_column_id(0, gtk.SORT_ASCENDING)  # Sort the display


class SelectZipFileContents(SutekhDialog):
    """Dialog for querying contents of the zip file"""
    # pylint: disable-msg=R0904
    # gtk.Dialog, so lots of public methods

    def __init__(self, dEscapedList, oParent):
        super(SelectZipFileContents, self).__init__(
                "Select Card Sets to Import", oParent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL,
                    gtk.RESPONSE_CANCEL))

        self.dEscapedList = dEscapedList

        oModel = ZipFileDirStore()

        # Ask user to select entries to import
        self.oScrolledList = ScrolledList('Available Card Sets', oModel)
        # pylint: disable-msg=E1101
        # vbox confuses pylint
        self.vbox.pack_start(self.oScrolledList)
        self.oScrolledList.set_size_request(450, 300)
        self.oScrolledList.fill_list(self.dEscapedList)
        self.oScrolledList.view.expand_all()
        # Add the various buttons
        # Select all and unselect all
        oSelectAll = gtk.Button('Select All')
        oUnSelectAll = gtk.Button('Unselect All')
        oSelectAll.connect('clicked', _set_selected_rows, self.oScrolledList,
                self.dEscapedList)
        oUnSelectAll.connect('clicked', _set_selected_rows, self.oScrolledList,
                [])
        oSelectButtons = gtk.VBox(False, 2)
        oSelectButtons.pack_start(oSelectAll, expand=False)
        oSelectButtons.pack_start(oUnSelectAll, expand=False)
        self.oPrompt = gtk.RadioButton(None, 'Always Ask', False)
        self.oPrompt.set_active(True)
        self.oReplace = gtk.RadioButton(self.oPrompt,
                'Always replace with new card set', False)
        self.oReplace.set_active(False)
        self.oRename = gtk.RadioButton(self.oPrompt,
                'Always create unique name', False)
        self.oRename.set_active(False)
        oRadioButs = gtk.VBox(False, 2)
        oRadioLabel = gtk.Label()
        oRadioLabel.set_markup('<b>How to handle card set name conflicts?</b>')
        oRadioButs.pack_start(oRadioLabel)
        oRadioButs.pack_start(self.oPrompt, expand=False)
        oRadioButs.pack_start(self.oReplace, expand=False)
        oRadioButs.pack_start(self.oRename, expand=False)

        oButtons = gtk.HBox(False, 2)
        oButtons.pack_start(oSelectButtons, expand=False)
        oButtons.pack_start(oRadioButs)
        self.vbox.pack_start(oButtons, expand=False)

        self.show_all()

    def get_clash_mode(self):
        """Return the selected clash mode"""
        if self.oRename.get_active():
            return RENAME
        elif self.oReplace.get_active():
            return REPLACE
        return PROMPT

    def get_selected(self):
        """Get the list of selected card sets"""
        dSelected = {}
        for sName in self.oScrolledList.get_selection():
            dSelected[sName] = self.dEscapedList[sName]
        return dSelected


class ImportFromZipFile(SutekhPlugin):
    """Extract selected card sets from a zip file."""

    dTableVersions = {}
    aModelsSupported = ("MainWindow",)

    # Dialog and Menu Item Creation

    def get_menu_item(self):
        """Register on the Plugins menu"""
        if not self.check_versions() or not self.check_model_type():
            return None

        oImport = gtk.MenuItem("Import Card Set(s) from zip file")
        oImport.connect("activate", self.make_dialog)
        return ('Import Card Set', oImport)

    # Menu responses

    def make_dialog(self, _oWidget):
        """Create the dialog used to select the zip file"""
        sName = "Select zip file to import from."

        oDlg = ZipFileDialog(self.parent, sName, gtk.FILE_CHOOSER_ACTION_OPEN)
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

        oFile = ZipFileWrapper(sFilename)
        dList = oFile.get_all_entries()
        dEscapedList = {}
        for sName, tInfo in dList.iteritems():
            dEscapedList[self.escape(sName)] = (sName, tInfo[0], tInfo[1],
                    tInfo[2])

        oSelDlg = SelectZipFileContents(dEscapedList, self.parent)
        oResponse = oSelDlg.run()
        dSelected = oSelDlg.get_selected()
        iClashMode = oSelDlg.get_clash_mode()
        oSelDlg.destroy()
        if oResponse == gtk.RESPONSE_OK and len(dSelected) > 0:
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
        bDone = False
        while not bDone:
            dSelected = self._read_heart(oFile, dSelected, oLogger, iClashMode)
            bDone = len(dSelected) == 0
        oProgressDialog.destroy()

    def _read_heart(self, oFile, dSelected, oLogger, iClashMode):
        """Heart of the reading loop - ensure we read parents before
           children, and correct for renames that occur."""
        # pylint: disable-msg=W0703, R0914
        # @0703: we really do want all the exceptions
        # R0914: Use track a lot of state, so many local variables
        dRemaining = {}
        dRenames = {}
        for sEscapedName, tInfo in dSelected.iteritems():
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
                    update_open_card_sets(self.parent, oCardSetHolder.name)
                self.reload_pcs_list()
            except Exception, oException:
                sMsg = "Failed to import card set %s.\n\n%s" % (sName,
                        oException)
                do_exception_complaint(sMsg)
        return dRemaining


plugin = ImportFromZipFile
