# StarterDeckInfo.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Adds info about the starter decks cards are found in"""

from sutekh.core.SutekhObjects import PhysicalCardSet, \
        MapPhysicalCardToPhysicalCardSet, IPhysicalCardSet
from sutekh.core.Filters import PhysicalCardSetFilter, \
        FilterAndBox, SpecificCardIdFilter
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.CardTextView import CardTextViewListener
from sutekh.gui.ProgressDialog import ProgressDialog, SutekhCountLogHandler
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error
from sutekh.core.CardSetUtilities import delete_physical_card_set, \
        find_children
from sutekh.io.ZipFileWrapper import ZipFileWrapper
from sutekh.gui.CardSetManagementController import reparent_all_children, \
        update_open_card_sets
from sutekh.SutekhUtility import prefs_dir, ensure_dir_exists
import re
import gtk
import urllib2
import tempfile
from logging import Logger

class StarterConfigDialog(SutekhDialog):
    # pylint: disable-msg=R0904
    # R0904 - gtk Widget, so has many public methods
    """Dialog for configuring the Starter plugin."""
    def __init__(self, oParent, bFirstTime=False):
        super(StarterConfigDialog, self).__init__(
                'Configure Stater Info Plugin', oParent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL,
                    gtk.RESPONSE_CANCEL))
        oDescLabel = gtk.Label()
        if not bFirstTime:
            oDescLabel.set_markup('<b>Choose how to configure the starter info'
                    ' plugin</b>')
        else:
            oDescLabel.set_markup('<b>Choose how to configure the starter info'
                    ' plugin</b>\nChoose cancel to skip configuring the '
                    ' plugin\nYou will not be prompted again')
        self.oChoiceDownload = gtk.RadioButton(
                label='Download starter info from sourceforge.net')
        self.oChoiceLocalCopy = gtk.RadioButton(self.oChoiceDownload,
                label='Add starters from a local zip file')
        oChoiceBox = gtk.VBox(False, 2)
        self.oFileChoiceWidget = gtk.FileChooserWidget(
                action=gtk.FILE_CHOOSER_ACTION_OPEN)
        self.oChoiceDownload.connect('toggled', self._radio_toggled,
                oChoiceBox, None)
        self.oChoiceLocalCopy.connect('toggled', self._radio_toggled,
                oChoiceBox, self.oFileChoiceWidget)

        self.oChoiceDownload.set_active(True)
        # pylint: disable-msg=E1101
        # pylint doesn't pick up vbox methods correctly
        self.vbox.pack_start(oDescLabel, False, False)
        self.vbox.pack_start(self.oChoiceDownload, False, False)
        self.vbox.pack_start(self.oChoiceLocalCopy, False, False)
        self.vbox.pack_start(oChoiceBox)
        self.set_size_request(600, 600)

        oZipFilter = gtk.FileFilter()
        oZipFilter.add_pattern('*.zip')
        oZipFilter.add_pattern('*.ZIP')
        self.oFileChoiceWidget.add_filter(oZipFilter)
        self.show_all()

    def _radio_toggled(self, oRadioButton, oChoiceBox, oFileWidget):
        """Display the correct file widget when radio buttons change"""
        if oRadioButton.get_active():
            for oChild in oChoiceBox.get_children():
                oChoiceBox.remove(oChild)
            if oFileWidget:
                oChoiceBox.pack_start(oFileWidget)
            self.show_all()

    def get_file(self):
        """Get the file from oFileChoiceWidget."""
        return self.oFileChoiceWidget.get_filename()

    def get_choice(self):
        """Get which of the RadioButtons was active."""
        if self.oChoiceDownload.get_active():
            return 'Download'
        elif self.oChoiceLocalCopy.get_active():
            return 'Local copy'

def _check_precon(oAbsCard):
    """Check if we have a precon rarity here"""
    for oPair in oAbsCard.rarity:
        if oPair.rarity.name == 'Precon':
            return True
    return False

def _check_exp_name(sExpName, oAbsCard):
    """Check that expansion is one of the precon expansions of the card"""
    for oPair in oAbsCard.rarity:
        if oPair.expansion.name.lower() == sExpName.lower() and \
                oPair.rarity.name == 'Precon':
            return True
    return False

class StarterInfoPlugin(CardListPlugin, CardTextViewListener):
    """Plugin providing access to CardImageFrame."""
    dTableVersions = {PhysicalCardSet : [5, 6]}
    aModelsSupported = ["MainWindow"]

    # FIXME: Expose this to the user?
    oStarterRegex = re.compile('^\[(.*)\] (.*) Starter')

    # pylint: disable-msg=W0142
    # ** magic OK here
    def __init__(self, *args, **kwargs):
        super(StarterInfoPlugin, self).__init__(*args, **kwargs)
        self.oToggle = None
        self.oLastCard = None
        self.bShowInfo = False

    def get_menu_item(self):
        """Overrides method from base class.

           Adds the menu item on the MainWindow if the images can be found.
           """
        if not self.check_versions() or not self.check_model_type():
            return None
        # Make sure we add the tag we need
        oCardTextView = self.parent.card_text_pane.view
        oCardTextView.add_listener(self)
        oCardTextView.text_buffer.add_list_tag('starters')

        self.oToggle = gtk.CheckMenuItem("Show Starter Information")
        self.oToggle.connect('toggled', self._toggle_starter)
        self.oToggle.set_active(False)
        if self.check_enabled():
            sPrefsValue = \
                    self.parent.config_file.get_plugin_key('show starters')
            if sPrefsValue == 'Yes':
                self.oToggle.set_active(True)
        else:
            self.oToggle.set_sensitive(False)
        oDownload = gtk.MenuItem("Download starter decks")
        oDownload.connect('activate', self.do_download)
        return [('Plugins', self.oToggle), ('Plugins', oDownload)]

    def check_enabled(self):
        """check for starter decks in the database and disable menu if not"""
        bEnabled = False
        for oCS in PhysicalCardSet.select():
            oMatch = self.oStarterRegex.match(oCS.name)
            if oMatch:
                bEnabled = True
                break
        return bEnabled

    def setup(self):
        """1st time setup tasks"""
        sPrefsValue = self.parent.config_file.get_plugin_key('show starters')
        if sPrefsValue is None:
            # First time
            self.parent.config_file.set_plugin_key('show starters', 'No')
            if not self.check_enabled():
                oDialog = StarterConfigDialog(self.parent, True)
                self.handle_response(oDialog)

    def do_download(self, _oMenuWidget):
        """Prompt the user to download/setup decks"""
        oDialog = StarterConfigDialog(self.parent)
        self.handle_response(oDialog)

    def handle_response(self, oDialog):
        """Handle the response from the config dialog"""
        iResponse = oDialog.run()
        if iResponse == gtk.RESPONSE_OK:
            sChoice = oDialog.get_choice()
            if sChoice == 'Download':
                if not self._download_file():
                    do_complaint_error('Unable to successfully download'
                            ' and install zipfile')
            elif sChoice == 'Local copy':
                sFileName = oDialog.get_file()
                if not self._unzip_file(sFileName):
                    do_complaint_error('Unable to successfully install '
                            ' zipfile %s' % sFileName)
        if self.check_enabled():
            self.oToggle.set_sensitive(True)
        else:
            self.oToggle.set_sensitive(False)
        # get rid of the dialog
        oDialog.destroy()

    def _download_file(self):
        """Download a zip file containing the starters."""
        # FIXME: re-work so we can always get the latest zip file here.
        sUrl = 'http://sourceforge.net/apps/trac/sutekh/raw-attachment/' \
                'wiki/MiscWikiFiles/Starters_SW_to_KoT.zip'
        oFile = urllib2.urlopen(sUrl)
        sDownloadDir = prefs_dir('Sutekh')
        ensure_dir_exists(sDownloadDir)
        fTemp = tempfile.TemporaryFile()
        sLength = oFile.info().getheader('Content-Length')
        if sLength:
            iLength = int(sLength)
            oProgress = ProgressDialog()
            oProgress.set_description('Download progress')
            iTotal = 0
            bCont = True
            while bCont:
                oInf = oFile.read(10000)
                iTotal += 10000
                oProgress.update_bar(float(iTotal) / iLength)
                if oInf:
                    fTemp.write(oInf)
                else:
                    bCont = False
            oProgress.destroy()
        else:
            # Just try and download
            fTemp.write(oFile.read())
        # pylint: disable-msg=W0703
        # we really do want all the exceptions
        try:
            # zipfile will accept file-like objects
            oZipFile = ZipFileWrapper(fTemp)
            bResult = self._unzip_heart(oZipFile)
        except Exception, _oExcept:
            bResult = False
        # cleanup file
        fTemp.close()
        return bResult

    def _unzip_file(self, sFileName):
        """Unzip a file containing the images."""
        bResult = False
        # pylint: disable-msg=W0703
        # we really do want all the exceptions
        try:
            oZipFile = ZipFileWrapper(sFileName)
            bResult = self._unzip_heart(oZipFile)
        except Exception, _oExcept:
            return False
        return bResult

    def _unzip_heart(self, oFile):
        """Heart of the reading loop - ensure we read parents before
           children, and correct for renames that occur."""
        oLogHandler = SutekhCountLogHandler()
        oProgressDialog = ProgressDialog()
        oProgressDialog.set_description("Importing Starters")
        oLogger = Logger('Read zip file')
        dList = oFile.get_all_entries()
        # Check that we match starter regex
        bOK = False
        for sName in dList:
            oMatch = self.oStarterRegex.match(sName)
            if oMatch:
                bOK = True
                break
        if not bOK:
            oProgressDialog.destroy()
            return False # No starters in zip file
        oLogger.addHandler(oLogHandler)
        oLogHandler.set_dialog(oProgressDialog)
        oLogHandler.set_total(len(dList))
        oProgressDialog.show()
        bDone = False
        while not bDone:
            dRemaining = {}
            if self._unzip_list(oFile, dList, oLogger, dRemaining):
                bDone = len(dRemaining) == 0
                dList = dRemaining
            else:
                oProgressDialog.destroy()
                return False # Error
        oProgressDialog.destroy()
        return True

    def _unzip_list(self, oZipFile, dList, oLogger, dRemaining):
        """Extract the files left in the list."""
        dRemaining = {}
        for sName, tInfo in dList.iteritems():
            sFilename, bParentExists, sParentName = tInfo
            if sParentName is not None and sParentName in dList:
                # Do have a parent to look at, so skip for now
                dRemaining[sName] = tInfo
                continue
            elif sParentName is not None:
                # Missing parent from the file, so it the file is invalid
                return False
            elif not bParentExists:
                # Parent mentioned, but doesn't exist, so file is invalid
                return False
            # pylint: disable-msg=W0703
            # we really do want all the exceptions
            try:
                oHolder = oZipFile.read_single_card_set(sFilename)
                oLogger.info('Read %s' % sName)
                if not oHolder.name:
                    # We skip this card set
                    continue
                # We unconditionally delete the card set if it already
                # exists, as being the most sensible default
                aChildren = []
                if PhysicalCardSet.selectBy(name=oHolder.name).count() != 0:
                    oCS = IPhysicalCardSet(oHolder.name)
                    aChildren = find_children(oCS)
                    delete_physical_card_set(oHolder.name)
                oHolder.create_pcs(self.cardlookup)
                reparent_all_children(oHolder.name, aChildren)
                if self.parent.find_cs_pane_by_set_name(oHolder.name):
                    # Already open, so update to changes
                    update_open_card_sets(self.parent, oHolder.name)
                self.reload_pcs_list()
            except Exception, oException:
                sMsg = "Failed to import card set %s.\n\n%s" % (sName,
                        oException)
                do_complaint_error(sMsg)
                return False
        return True

    def _toggle_starter(self, oToggle):
        """Toggle the show info flag"""
        self.bShowInfo = oToggle.get_active()
        # Update the card text pane to reflect changes
        self.parent.set_card_text(self.oLastCard)
        if self.bShowInfo:
            self.parent.config_file.set_plugin_key('show starters', 'Yes')
        else:
            self.parent.config_file.set_plugin_key('show starters', 'No')

    def set_card_text(self, oPhysCard):
        """Update the card text pane with the starter info"""
        self.oLastCard = oPhysCard
        if not self.bShowInfo:
            return # Do nothing
        oAbsCard = oPhysCard.abstractCard
        if not _check_precon(oAbsCard):
            return
        # Get frame
        oCardTextBuf = self.parent.card_text_pane.view.text_buffer
        # Find the starter decks
        aStarters = []
        for oCS in PhysicalCardSet.select():
            oMatch = self.oStarterRegex.match(oCS.name)
            if oMatch:
                sExpName = oMatch.groups()[0]
                if _check_exp_name(sExpName, oAbsCard):
                    aStarters.append((oCS, oMatch.groups()[0],
                        oMatch.groups()[1]))
        # Find the card in the starter decks
        aInfo = []
        for oCS, sExpName, sDeckName in aStarters:
            oFilter = FilterAndBox([SpecificCardIdFilter(oAbsCard.id),
                    PhysicalCardSetFilter(oCS.name)])
            iCount = oFilter.select(MapPhysicalCardToPhysicalCardSet).count()
            if iCount > 0:
                aInfo.append("%s (%s) (x %d)" % (sDeckName, sExpName, iCount))
        if aInfo:
            # Move to after the expansionsa
            oTempIter = oCardTextBuf.get_cur_iter()
            oCardTextBuf.set_cur_iter_to_mark('expansion')
            oCardTextBuf.tag_text("\n")
            oCardTextBuf.labelled_list('Preconstructed Decks', aInfo,
                    'starters')
            oCardTextBuf.set_cur_iter(oTempIter)

plugin = StarterInfoPlugin
