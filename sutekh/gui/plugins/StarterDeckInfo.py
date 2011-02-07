# StarterDeckInfo.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Adds info about the starter decks cards are found in"""

from sutekh.core.SutekhObjects import PhysicalCardSet, \
        MapPhysicalCardToPhysicalCardSet, IPhysicalCardSet
from sutekh.core.Filters import PhysicalCardSetFilter, \
        FilterAndBox, SpecificCardIdFilter
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.gui.CardTextView import CardTextViewListener
from sutekh.gui.ProgressDialog import ProgressDialog, SutekhCountLogHandler
from sutekh.gui.SutekhDialog import SutekhDialog, do_exception_complaint, \
        do_complaint_error
from sutekh.core.CardSetUtilities import delete_physical_card_set, \
        find_children
from sutekh.io.ZipFileWrapper import ZipFileWrapper
from sutekh.gui.GuiCardSetFunctions import reparent_all_children, \
        update_open_card_sets
from sutekh.gui.FileOrUrlWidget import FileOrUrlWidget, fetch_data
from sutekh.gui.SutekhFileWidget import add_filter
import re
import gtk
import urllib2
from logging import Logger
from StringIO import StringIO


class StarterConfigDialog(SutekhDialog):
    # pylint: disable-msg=R0904
    # R0904 - gtk Widget, so has many public methods
    """Dialog for configuring the Starter plugin."""

    sDocUrl = 'http://sourceforge.net/apps/trac/sutekh/wiki/' \
            'UserDocumentation?format=txt'

    sZipUrlBase = 'http://sourceforge.net/apps/trac/sutekh/raw-attachment'

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
        self.oFileWidget = FileOrUrlWidget(oParent, "Choose localtion for "
                "Starter decks", {'Sutekh Wiki': self.sDocUrl})
        add_filter(self.oFileWidget, 'Zip Files', ['*.zip', '*.ZIP'])
        # pylint: disable-msg=E1101
        # pylint doesn't pick up vbox methods correctly
        self.vbox.pack_start(oDescLabel, False, False)
        self.vbox.pack_start(self.oFileWidget, False, False)
        self.set_size_request(300, 200)

        self.show_all()

    def _get_zip_data(self):
        """Extract the zip file from the UserDocumentation page on the
           wiki"""
        # Extract the first zip file from this
        oFile = urllib2.urlopen(self.sDocUrl)
        for sLine in oFile.readlines():
            if sLine.find('.zip') != -1:
                # Extract the zip file name
                # Assumption - rst attachment, and the 1st zip file in
                # the list
                sZipRef = sLine.split('[')[1].split(' ')[0]
                break
        # Build up the url
        sZipRef = sZipRef.replace('attachment:', '')
        # We need to split off the zip file name and the path bits
        sZipName, sPath = sZipRef.split(':', 1)
        sPath = sPath.replace(':', '/')
        sZipUrl = '/'.join((self.sZipUrlBase, sPath, sZipName))
        oFile = urllib2.urlopen(sZipUrl)
        return fetch_data(oFile)

    def get_data(self):
        """Return the zip file data containing the decks"""
        sFile, _bUrl = self.oFileWidget.get_file_or_url()
        sData = None
        if sFile == self.sDocUrl:
            # Downloading from sutekh wiki, so need magic to get right file
            sData = self._get_zip_data()
        elif sFile:
            sData = self.oFileWidget.get_binary_data()
        return sData


def _is_precon(oRarityPair):
    """Return true if the rarity is a precon one"""
    if oRarityPair.rarity.name == 'Precon' or \
            oRarityPair.rarity.name == 'Demo':
        return True
    return False


def _check_precon(oAbsCard):
    """Check if we have at least one precon rarity for this card"""
    for oPair in oAbsCard.rarity:
        if _is_precon(oPair):
            return True
    return False


def _check_exp_name(sExpName, oAbsCard):
    """Check that expansion is one of the precon expansions of the card"""
    for oPair in oAbsCard.rarity:
        if oPair.expansion.name.lower() == sExpName.lower() and \
                _is_precon(oPair):
            return True
    return False


class StarterInfoPlugin(SutekhPlugin, CardTextViewListener):
    """Plugin providing access to CardImageFrame."""
    dTableVersions = {PhysicalCardSet: (5, 6)}
    aModelsSupported = ("MainWindow",)

    dGlobalConfig = {
        'show starters': 'option("Yes", "No", default="No")',
    }

    # FIXME: Expose this to the user?
    oStarterRegex = re.compile('^\[(.*)\] (.*) Starter')
    oDemoRegex = re.compile('^\[(.*)\] (.*) Demo Deck')

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
                    self.get_config_item('show starters')
            if sPrefsValue == 'Yes':
                self.oToggle.set_active(True)
        else:
            self.oToggle.set_sensitive(False)
        oDownload = gtk.MenuItem("Download starter decks")
        oDownload.connect('activate', self.do_download)
        return [('Preferences', self.oToggle), ('Data Downloads', oDownload)]

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
        sPrefsValue = self.get_config_item('show starters')
        if sPrefsValue is None:
            # First time
            self.set_config_item('show starters', 'No')
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
            sData = oDialog.get_data()
            if not sData:
                do_complaint_error('Unable to access zipfile data')
            elif not self._unzip_file(sData):
                do_complaint_error('Unable to successfully unzip zipfile')
        if self.check_enabled():
            self.oToggle.set_sensitive(True)
        else:
            self.oToggle.set_sensitive(False)
        # cleanup
        oDialog.destroy()

    def _unzip_file(self, sData):
        """Unzip a file containing the decks."""
        bResult = False
        oZipFile = ZipFileWrapper(StringIO(sData))
        bResult = self._unzip_heart(oZipFile)
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
            return False  # No starters in zip file
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
                return False  # Error
        oProgressDialog.destroy()
        return True

    def _unzip_list(self, oZipFile, dList, oLogger, dRemaining):
        """Extract the files left in the list."""
        for sName, tInfo in dList.iteritems():
            sFilename, _bIgnore, sParentName = tInfo
            if sParentName is not None and sParentName in dList:
                # Do have a parent to look at later, so skip for now
                dRemaining[sName] = tInfo
                continue
            elif sParentName is not None:
                if PhysicalCardSet.selectBy(name=sParentName).count() == 0:
                    # Missing parent, so it the file is invalid
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
                    # pylint: disable-msg=E1101, E1103
                    # pyprotocols confuses pylint
                    oCS = IPhysicalCardSet(oHolder.name)
                    aChildren = find_children(oCS)
                    if oCS.parent:
                        # Ensure we restore with the correct parent
                        oHolder.parent = oCS.parent.name
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
                do_exception_complaint(sMsg)
                return False
        return True

    def _toggle_starter(self, oToggle):
        """Toggle the show info flag"""
        self.bShowInfo = oToggle.get_active()
        # Update the card text pane to reflect changes
        self.parent.set_card_text(self.oLastCard)
        if self.bShowInfo:
            self.set_config_item('show starters', 'Yes')
        else:
            self.set_config_item('show starters', 'No')

    def _get_card_set_info(self, oAbsCard):
        """Find preconstructed card sets that contain the card"""
        dMatches = {'Starters': [], 'Demos': []}
        for oCS in PhysicalCardSet.select():
            for sType, oRegex in (('Starters', self.oStarterRegex),
                    ('Demos', self.oDemoRegex)):
                oMatch = oRegex.match(oCS.name)
                if oMatch:
                    sExpName = oMatch.groups()[0]
                    if _check_exp_name(sExpName, oAbsCard):
                        dMatches[sType].append((oCS, oMatch.groups()[0],
                            oMatch.groups()[1]))
        # Find the card in the starter decks
        dInfo = {'Starters': [], 'Demos': []}
        for sType, aResults in dMatches.iteritems():
            for oCS, sExpName, sDeckName in sorted(aResults,
                    key=lambda x: (x[1], x[2])):
                # Sort by exp, name
                oFilter = FilterAndBox([SpecificCardIdFilter(oAbsCard.id),
                        PhysicalCardSetFilter(oCS.name)])
                iCount = oFilter.select(
                        MapPhysicalCardToPhysicalCardSet).count()
                if iCount > 0:
                    dInfo[sType].append("x %(count)d %(exp)s (%(cardset)s)" % {
                        'count': iCount,
                        'exp': sExpName,
                        'cardset': sDeckName,
                        })
        return dInfo

    def set_card_text(self, oPhysCard):
        """Update the card text pane with the starter info"""
        self.oLastCard = oPhysCard
        if not self.bShowInfo:
            return  # Do nothing
        oAbsCard = oPhysCard.abstractCard
        if not _check_precon(oAbsCard):
            return
        # Find the starter decks
        dInfo = self._get_card_set_info(oAbsCard)
        # Get frame
        oCardTextBuf = self.parent.card_text_pane.view.text_buffer
        oTempIter = oCardTextBuf.get_cur_iter()
        # We do things in this order, so demo decks appear after the starters
        if dInfo['Demos']:
            # Move to after the expansionsa
            oCardTextBuf.set_cur_iter_to_mark('expansion')
            oCardTextBuf.tag_text("\n")
            oCardTextBuf.labelled_list('Demonstration Decks', dInfo['Demos'],
                    'starters')
        if dInfo['Starters']:
            oCardTextBuf.set_cur_iter_to_mark('expansion')
            oCardTextBuf.tag_text("\n")
            oCardTextBuf.labelled_list('Preconstrcuted Decks',
                    dInfo['Starters'], 'starters')
        oCardTextBuf.set_cur_iter(oTempIter)

plugin = StarterInfoPlugin
