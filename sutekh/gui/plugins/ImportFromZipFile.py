# ImportFromZipFile.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""Plugin to import selected card sets from a zip file"""

import gtk
import os
from logging import Logger
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error
from sutekh.gui.SutekhFileWidget import ZipFileDialog
from sutekh.gui.ProgressDialog import ProgressDialog, SutekhCountLogHandler
from sutekh.gui.ScrolledList import ScrolledList
from sutekh.io.ZipFileWrapper import ZipFileWrapper
from sutekh.gui.GuiCardSetFunctions import reparent_all_children, \
        update_open_card_sets, get_import_name


def _do_rename_parent(sOldName, sNewName, dRemaining):
    """Handle the renaming of a parent card set in the unprocessed list."""
    dResult = {}
    for sName, tInfo in dRemaining.iteritems():
        if tInfo[2] == sOldName:
            dResult[sName] = (tInfo[0], tInfo[1], sNewName)
        else:
            dResult[sName] = tInfo
    return dResult


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
        dSelected = {}
        # Ask user to select entries to import
        oSelDlg = SutekhDialog("Select Card Sets to Import", self.parent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL,
                    gtk.RESPONSE_CANCEL))

        oScrolledList = ScrolledList('Available Card Sets')
        # pylint: disable-msg=E1101
        # vbox confuses pylint
        oSelDlg.vbox.pack_start(oScrolledList)
        oScrolledList.set_size_request(150, 300)
        oScrolledList.fill_list(sorted(dList))
        oResponse = oSelDlg.run()
        # Extract selected cards from the dialog
        for sName in oScrolledList.get_selection():
            dSelected[sName] = dList[sName]
        oSelDlg.destroy()
        if oResponse == gtk.RESPONSE_OK and len(dSelected) > 0:
            self.do_read_list(oFile, dSelected)

    def do_read_list(self, oFile, dSelected):
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
            dSelected = self._read_heart(oFile, dSelected, oLogger)
            bDone = len(dSelected) == 0
        oProgressDialog.destroy()

    def _read_heart(self, oFile, dSelected, oLogger):
        """Heart of the reading loop - ensure we read parents before
           children, and correct for renames that occur."""
        # pylint: disable-msg=W0703
        # we really do want all the exceptions
        dRemaining = {}
        dRenames = {}
        for sName, tInfo in dSelected.iteritems():
            sFilename, bParentExists, sParentName = tInfo
            # We aim to ensure that we always keep loaded card sets together,
            # so if the parent name clashes, we want to follow the renamed
            # parent, rather than be added to the existing card set of the
            # same name
            if sParentName is not None and sParentName in dSelected:
                # Do have a parent to look at, so skip for now
                if not bParentExists:
                    # The parent is in the list of cards to read, so it
                    # will exist when we get to it
                    dRemaining[sName] = (sFilename, True, sParentName)
                else:
                    dRemaining[sName] = tInfo
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
                oCardSetHolder, aChildren = get_import_name(oCardSetHolder)
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
                do_complaint_error(sMsg)
        return dRemaining


plugin = ImportFromZipFile
