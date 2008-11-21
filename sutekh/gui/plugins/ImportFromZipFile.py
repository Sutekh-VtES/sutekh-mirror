# ImportFromZipFile.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""Plugin to import selected card sets from a zip file"""

import gtk
import os
from logging import Logger
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error
from sutekh.gui.SutekhFileWidget import SutekhFileDialog
from sutekh.gui.ProgressDialog import ProgressDialog, SutekhCountLogHandler
from sutekh.gui.ScrolledList import ScrolledList
from sutekh.io.ZipFileWrapper import ZipFileWrapper

def _do_rename_parent(sOldName, sNewName, dRemaining):
    """Handle the renaming of a parent card set in the unprocessed list."""
    dResult = {}
    for sName, tInfo in dRemaining.iteritems():
        if tInfo[2] == sOldName:
            dResult[sName] = (tInfo[0], tInfo[1], sNewName)
        else:
            dResult[sName] = tInfo
    return dResult

class ImportFromZipFile(CardListPlugin):
    """Extract selected card sets from a zip file."""

    dTableVersions = {}
    aModelsSupported = ["MainWindow"]

    # Dialog and Menu Item Creation

    def get_menu_item(self):
        """Register on the Plugins menu"""
        if not self.check_versions() or not self.check_model_type():
            return None

        oImport = gtk.MenuItem("Import Card Set(s) from zip file")
        oImport.connect("activate", self.make_dialog)
        return ('Import Card Set', oImport)

    # Menu responses

    # pylint: disable-msg=W0613
    # oWidget needed by gtk function signature

    def make_dialog(self, oWidget):
        """Create the dialog used to select the zip file"""
        sName = "Select zip file to import from."

        oDlg = SutekhFileDialog(self.parent, sName,
                oAction=gtk.FILE_CHOOSER_ACTION_OPEN,
                oButtons=(gtk.STOCK_OK, gtk.RESPONSE_OK,
                    gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        oDlg.set_name("Sutekh.dialog")
        oDlg.add_filter_with_pattern('Zip Files', ['*.zip', '*.ZIP'])

        oDlg.connect("response", self.handle_response)
        oDlg.set_local_only(True)
        oDlg.set_select_multiple(False)
        oDlg.show_all()

        return oDlg

    # pylint: enable-msg=W0613

    def handle_response(self, oDlg, oResponse):
        """Handle response from the import dialog"""
        if oResponse == gtk.RESPONSE_OK:
            sFile = oDlg.get_filename()
            oDlg.destroy()

            if not os.path.exists(sFile):
                do_complaint_error("Backup file %s does not seem to exist."
                        % sFile)
                return
            oFile = ZipFileWrapper(sFile)
            dList = oFile.get_all_entries()
            dSelected = {}
            # Ask user to select entries to import
            oSelDlg = SutekhDialog("Select Card Sets to Import", self.parent,
                    gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
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
        else:
            oDlg.destroy()

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
                # Check for whether we're overwriting something
                # or not
                if PhysicalCardSet.selectBy(name=sName).count() != 0:
                    # Ask the user whether to rename, replace or cancel
                    sNewName = self._query_rename(sName)
                    dRenames[sName] = sNewName
                    # Check for cardsets that were waiting for us
                    dRemaining = _do_rename_parent(sName, sNewName, dRemaining)
                    if sNewName:
                        # rename
                        oCardSetHolder.name = sNewName
                    else:
                        # We skip this card set
                        continue
                # Ensure we use the right name for the parent
                oCardSetHolder.parent = sParentName
                oCardSetHolder.create_pcs(self.cardlookup)
                self.reload_pcs_list()
            except Exception, oException:
                sMsg = "Failed to import card set %s.\n\n%s" % (sName,
                        oException)
                do_complaint_error(sMsg)
        return dRemaining

    def _query_rename(self, sOldName):
        """Request a new name for the card set."""
        sNewName = None
        bRenamed = False
        oDlg = SutekhDialog("Card Set Name Exists", self.parent,
                gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL,
                    gtk.RESPONSE_CANCEL))
        # pylint: disable-msg=E1101
        # vbox confuses pylint
        oLabel = gtk.Label()
        oLabel.set_markup('Card Set %s already.\nPlease choose a new name or\n'
                'press Cancel to skip this card set' % sOldName)
        oDlg.vbox.pack_start(oLabel)
        oEntry = gtk.Entry(50)
        oDlg.vbox.pack_start(oEntry)
        # Need this so entry box works as expected
        oEntry.connect("activate", oDlg.response, gtk.RESPONSE_OK)
        oDlg.vbox.show_all()
        while not bRenamed:
            iResponse = oDlg.run()
            if iResponse == gtk.RESPONSE_OK:
                sNewName = oEntry.get_text().strip()
                if not sNewName:
                    do_complaint_error('No new name given')
                    # go around again
                    continue
                elif PhysicalCardSet.selectBy(name=sNewName).count() != 0:
                    do_complaint_error('New name %s is already in use'
                            % sNewName)
                    # go around again
                    continue
            else:
                sNewName = None
            # we got here, so we're done
            bRenamed = True
        oDlg.destroy()
        return sNewName


# pylint: disable-msg=C0103
# accept plugin name
plugin = ImportFromZipFile
