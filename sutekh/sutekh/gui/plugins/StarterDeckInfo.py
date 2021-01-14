# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Adds info about the starter decks cards are found in"""

import re
import datetime
from io import BytesIO

from gi.repository import Gtk

from sqlobject import SQLObjectNotFound

from sutekh.base.core.BaseTables import (PhysicalCardSet,
                                         MapPhysicalCardToPhysicalCardSet)
from sutekh.base.core.BaseAdapters import (IRarityPair, IPhysicalCardSet,
                                           IExpansion)
from sutekh.base.core.BaseFilters import (PhysicalCardSetFilter,
                                          FilterAndBox, SpecificCardIdFilter)
from sutekh.base.core.DBSignals import (listen_row_destroy, listen_row_update,
                                        listen_row_created,
                                        disconnect_row_destroy,
                                        disconnect_row_update,
                                        disconnect_row_created)
from sutekh.base.io.UrlOps import urlopen_with_timeout
from sutekh.base.gui.MessageBus import MessageBus
from sutekh.base.gui.SutekhDialog import (SutekhDialog,
                                          do_complaint_error)
from sutekh.base.gui.GuiCardSetFunctions import unzip_files_into_db
from sutekh.base.gui.FileOrUrlWidget import FileOrUrlWidget
from sutekh.base.gui.GuiDataPack import gui_error_handler, progress_fetch_data
from sutekh.base.gui.SutekhFileWidget import add_filter

from sutekh.io.ZipFileWrapper import ZipFileWrapper
from sutekh.io.DataPack import DOC_URL, find_data_pack, find_all_data_packs
from sutekh.gui.PluginManager import SutekhPlugin


DEMO_HOLDERS = ["Demo Decks", "White Wolf Demo Decks"]

STORYLINE_HOLDERS = ["Storyline Decks", "White Wolf Storyline Decks"]

STARTER_HOLDERS = ["White Wolf Starter Decks", "Starter Decks"]


def _get_cs_to_remove(oZipFile):
    """Handle card sets that are marked as removed in the starter
       info file."""
    sRemovedInfo = oZipFile.get_info_file('removed_decks.txt').decode('ascii')
    if not sRemovedInfo:
        # No removed info, so skip
        return []
    aToDelete = []
    for sLine in sRemovedInfo.splitlines():
        if sLine.startswith('#'):
            # Ignore comment
            continue
        sName = sLine.strip()
        aToDelete.append(sName)
    return aToDelete

def find_holder(aHolders):
    """Returns the first of the given holders that exists in the database,
       or None if all are missing."""
    for sCandidate in aHolders:
        try:
            oHolder = IPhysicalCardSet(sCandidate)
            return oHolder
        except SQLObjectNotFound:
            # We silence the error and move on to the next candidate
            pass
    return None


class StarterConfigDialog(SutekhDialog):
    # pylint: disable=too-many-public-methods
    # Gtk Widget, so has many public methods
    """Dialog for configuring the Starter plugin."""

    sDocUrl = DOC_URL

    def __init__(self, oParent, bFirstTime=False):
        super().__init__(
            'Configure Starter Info Plugin', oParent,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            ("_OK", Gtk.ResponseType.OK, "_Cancel", Gtk.ResponseType.CANCEL))
        oDescLabel = Gtk.Label()
        if not bFirstTime:
            oDescLabel.set_markup('<b>Choose how to configure the starter info'
                                  ' plugin</b>')
        else:
            oDescLabel.set_markup('<b>Choose how to configure the starter '
                                  'info plugin</b>\nChoose cancel to skip '
                                  'configuring the plugin\nYou will not be '
                                  'prompted again')
        self.oFileWidget = FileOrUrlWidget(oParent, "Choose location for "
                                           "Starter decks",
                                           {'Sutekh Datapack': self.sDocUrl})
        add_filter(self.oFileWidget, 'Zip Files', ['*.zip', '*.ZIP'])
        # pylint: disable=no-member
        # pylint doesn't pick up vbox methods correctly
        self.vbox.pack_start(oDescLabel, False, False, 0)
        self.vbox.pack_start(Gtk.HSeparator(), False, False, 0)
        self.vbox.pack_start(self.oFileWidget, False, False, 0)
        # Add check boxes for the decmo and storyline deck questions
        self.oExcludeStoryDecks = Gtk.CheckButton(
            'Exclude the Storyline Decks')
        self.oExcludeDemoDecks = Gtk.CheckButton('Exclude the WW Demo Decks')

        # Check to see if cards are available
        try:
            _oSkip = IRarityPair(('White Wolf 2003 Demo', 'Demo'))
        except SQLObjectNotFound:
            self.oExcludeDemoDecks.set_active(True)
            self.oExcludeDemoDecks.set_sensitive(False)

        try:
            _oSkip = IRarityPair(('Nergal Storyline', 'Storyline'))
        except SQLObjectNotFound:
            self.oExcludeStoryDecks.set_active(True)
            self.oExcludeStoryDecks.set_sensitive(False)

        self.vbox.pack_start(self.oExcludeStoryDecks, False, False, 0)
        self.vbox.pack_start(self.oExcludeDemoDecks, False, False, 0)

        self.set_size_request(350, 300)

        self.show_all()

    def get_excluded_decks(self):
        """Return selections for excluded decks"""
        return (self.oExcludeStoryDecks.get_active(),
                self.oExcludeDemoDecks.get_active())

    def get_data(self):
        """Return the zip file data containing the decks"""
        sFile, _bUrl = self.oFileWidget.get_file_or_url()
        sData = None
        if sFile == self.sDocUrl:
            # Downloading from sutekh datapack, so need magic to get right file
            sZipUrl, sHash = find_data_pack('starters',
                                            fErrorHandler=gui_error_handler)
            if not sZipUrl:
                # Error getting the data pack, so we fail
                return None
            oFile = urlopen_with_timeout(sZipUrl,
                                         fErrorHandler=gui_error_handler,
                                         bBinary=True)
            if oFile:
                sData = progress_fetch_data(oFile, None, sHash)
            else:
                sData = None
        elif sFile:
            sData = self.oFileWidget.get_binary_data()
        return sData


def _is_precon(oRarityPair):
    """Return true if the rarity is a precon one"""
    if oRarityPair.rarity.name == 'Precon' or \
            oRarityPair.rarity.name == 'Demo' or \
            oRarityPair.rarity.name == 'Fixed':
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


class StarterInfoPlugin(SutekhPlugin):
    """Plugin providing access to starter deck info."""
    dTableVersions = {PhysicalCardSet: (5, 6, 7)}
    aModelsSupported = ("MainWindow",)

    dGlobalConfig = {
        'show starters': 'option("Yes", "No", "Unasked", default="Unasked")',
    }

    # FIXME: Expose this to the user?
    oStarterRegex = re.compile(r'^\[(.*)\] (.*) Starter')
    oDemoRegex = re.compile(r'^\[(.*)\] (.*) Demo Deck')
    oFixedRegex = re.compile(
        r'^\[(.*)\] (.*) (Set|([A,B])|Bundle ([0-9])|Bundle|Box)$')

    # Groups to check for additional information about the matching set
    aPostfixes = [3, 4]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.oToggle = None
        self.oLastCard = None
        self.bShowInfo = False
        self._aStarters = []
        # Flag to avoid crashing if we call cleanup early
        # (which may happen in the test suite)
        self._bDoSignalCleanup = False

    def cleanup(self):
        """Remove the listener"""
        if self._bDoSignalCleanup:
            disconnect_row_update(self.card_set_changed, PhysicalCardSet)
            disconnect_row_destroy(self.card_set_added_deleted,
                                   PhysicalCardSet)
            disconnect_row_created(self.card_set_added_deleted,
                                   PhysicalCardSet)
            MessageBus.unsubscribe(MessageBus.Type.CARD_TEXT_MSG,
                                   'post_set_text', self.post_set_card_text)
        super().cleanup()

    def get_menu_item(self):
        """Overrides method from base class.

           Adds the menu item on the MainWindow if the starters can be found.
           """
        MessageBus.subscribe(MessageBus.Type.CARD_TEXT_MSG, 'post_set_text',
                             self.post_set_card_text)
        # Listen for card set changes to manage the cache
        listen_row_update(self.card_set_changed, PhysicalCardSet)
        listen_row_destroy(self.card_set_added_deleted, PhysicalCardSet)
        listen_row_created(self.card_set_added_deleted, PhysicalCardSet)
        self._bDoSignalCleanup = True

        # Make sure we add the tag we need
        oCardTextView = self.parent.card_text_pane.view
        oCardTextView.text_buffer.add_list_tag('starters')

        self.oToggle = Gtk.CheckMenuItem(label="Show Starter Information")
        self.oToggle.connect('toggled', self._toggle_starter)
        self.oToggle.set_active(False)
        if self.check_enabled():
            sPrefsValue = self.get_config_item('show starters')
            if sPrefsValue == 'Yes':
                self.oToggle.set_active(True)
        else:
            self.oToggle.set_sensitive(False)
        oDownload = Gtk.MenuItem(label="Download starter decks")
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

    def check_for_updates(self):
        """Check to see if the starter decks need to be updated."""
        sPrefsValue = self.get_config_item('show starters')
        # Only check if we're meant to show the starters
        if sPrefsValue.lower() != 'yes':
            return None
        aUrls, aDates, _aHashes = find_all_data_packs(
            'starters', fErrorHandler=gui_error_handler)
        if not aUrls:
            # Timeout means we skip trying anything
            return None
        if self._check_for_starters_to_download(aUrls[0], aDates[0]):
            return "Updated starter deck information available"
        return None

    def do_update(self):
        """Download the starter decks, if requested."""
        sPrefsValue = self.get_config_item('show starters')
        # Only check if we're meant to show the starters
        if sPrefsValue.lower() != 'yes':
            return
        aUrls, aDates, aHashes = find_all_data_packs(
            'starters', fErrorHandler=gui_error_handler)

        if self._check_for_starters_to_download(aUrls[0], aDates[0]):
            # Check to see if cards are available
            bExcludeDemoDecks = False
            bExcludeStorylineDecks = False
            try:
                _oSkip = IRarityPair(('White Wolf 2003 Demo', 'Demo'))
            except SQLObjectNotFound:
                bExcludeDemoDecks = True
            try:
                _oSkip = IRarityPair(('Nergal Storyline', 'Storyline'))
            except SQLObjectNotFound:
                bExcludeStorylineDecks = True
            oHolder = find_holder(STARTER_HOLDERS)
            if oHolder:
                # We assume missing Holders are due to user choice, so we
                # try to honour those. People can always use the explicit
                # download option to recover accidental deletions
                if not bExcludeDemoDecks:
                    bExcludeDemoDecks = find_holder(DEMO_HOLDERS) is None
                if not bExcludeStorylineDecks:
                    bExcludeStorylineDecks = \
                        find_holder(STORYLINE_HOLDERS) is None
            oFile = urlopen_with_timeout(aUrls[0],
                                         fErrorHandler=gui_error_handler,
                                         bBinary=True)
            if oFile:
                sData = progress_fetch_data(oFile, None, aHashes[0])
            else:
                sData = None
            if not sData:
                do_complaint_error('Unable to access zipfile data')
            elif not self._unzip_file(sData, bExcludeStorylineDecks,
                                      bExcludeDemoDecks):
                do_complaint_error('Unable to successfully unzip zipfile')

    def _check_for_starters_to_download(self, sUrl, sDate):
        """Check for any decks we need to download."""
        if not sUrl:
            return False
        # Check if we need to download this url
        oHolder = find_holder(STARTER_HOLDERS)
        if oHolder is None:
            # No starters, so assume we need to download
            return True
        # Existing TWDA entry, so check dates
        try:
            oUrlDate = datetime.datetime.strptime(sDate, '%Y-%m-%d')
        except ValueError:
            oUrlDate = None
        sUpdated = "Date Updated:"
        oDeckDate = None
        if not oHolder.annotations:
            # No date information, so we assume we need to download
            return True
        for sLine in oHolder.annotations.splitlines():
            if sLine.startswith(sUpdated):
                sDate = sLine.split(sUpdated)[1][1:11]
                try:
                    oDeckDate = datetime.datetime.strptime(sDate, '%Y-%m-%d')
                except ValueError:
                    pass
        if oDeckDate is None or oUrlDate is None:
            # Unable to extract the dates correctly, so we treat this as
            # something to replace
            return True
        if oDeckDate < oUrlDate:
            # Url is newer, so we replace
            return True
        return False

    def setup(self):
        """1st time setup tasks"""
        sPrefsValue = self.get_config_item('show starters')
        if sPrefsValue == 'Unasked':
            self.set_config_item('show starters', 'No')
            if not self.check_enabled():
                # First time
                oDialog = StarterConfigDialog(self.parent, True)
                self.handle_response(oDialog)

    def do_download(self, _oMenuWidget):
        """Prompt the user to download/setup decks"""
        oDialog = StarterConfigDialog(self.parent)
        self.handle_response(oDialog)

    def handle_response(self, oDialog):
        """Handle the response from the config dialog"""
        iResponse = oDialog.run()
        if iResponse == Gtk.ResponseType.OK:
            sData = oDialog.get_data()
            (bExcludeStoryDecks, bExcludeDemoDecks) = \
                oDialog.get_excluded_decks()
            if not sData:
                do_complaint_error('Unable to access zipfile data')
            elif not self._unzip_file(sData, bExcludeStoryDecks,
                                      bExcludeDemoDecks):
                do_complaint_error('Unable to successfully unzip zipfile')
        if self.check_enabled():
            self.oToggle.set_sensitive(True)
        else:
            self.oToggle.set_sensitive(False)
        # cleanup
        oDialog.destroy()

    def _unzip_file(self, sData, bExcludeStoryDecks, bExcludeDemoDecks):
        """Unzip a file containing the decks."""
        oZipFile = ZipFileWrapper(BytesIO(sData))
        dList = oZipFile.get_all_entries()
        # Check that we match starter regex
        bOK = False
        for sName in dList:
            oMatch = self.oStarterRegex.match(sName)
            if oMatch:
                bOK = True
                break
        if not bOK:
            return False  # No starters in zip file

        aExcluded = []
        if bExcludeStoryDecks:
            aExcluded.extend(STORYLINE_HOLDERS)
        if bExcludeDemoDecks:
            aExcluded.extend(DEMO_HOLDERS)

        aToDelete = _get_cs_to_remove(oZipFile)

        return unzip_files_into_db([oZipFile], "Adding Starter Decks",
                                   self.parent, aToDelete, aExcluded)

    def _toggle_starter(self, oToggle):
        """Toggle the show info flag"""
        self.bShowInfo = oToggle.get_active()
        # Update the card text pane to reflect changes
        MessageBus.publish(MessageBus.Type.CARD_TEXT_MSG, 'set_card_text',
                           self.oLastCard)
        if self.bShowInfo:
            self.set_config_item('show starters', 'Yes')
        else:
            self.set_config_item('show starters', 'No')

    def card_set_changed(self, _oCardSet, _dChanges):
        """We listen for card set events, and invalidate the cache"""
        self._aStarters = []

    def card_set_added_deleted(self, _oCardSet, _dKW=None, _fPostFuncs=None):
        """We listen for card set additions & deletions, and
           invalidate the cache when that occurs"""
        self._aStarters = []

    def _cache_starters(self):
        """Lookup the starter decks and cache them to avoid repeated queries"""
        for oCS in PhysicalCardSet.select():
            for _sType, oRegex in (('Starters', self.oStarterRegex),
                                   ('Fixed', self.oFixedRegex),
                                   ('Demos', self.oDemoRegex)):
                oMatch = oRegex.match(oCS.name)
                if oMatch:
                    self._aStarters.append(oCS)

    def _get_card_set_info(self, oAbsCard):
        """Find preconstructed card sets that contain the card"""
        if not self._aStarters:
            self._cache_starters()
        dMatches = {'Starters': [], 'Demos': [], 'Fixed': []}
        for oCS in self._aStarters:
            for sType, oRegex in (('Starters', self.oStarterRegex),
                                  ('Fixed', self.oFixedRegex),
                                  ('Demos', self.oDemoRegex)):
                oMatch = oRegex.match(oCS.name)
                if oMatch:
                    sCandExpName = oMatch.groups()[0]
                    # Canonicalise the expansion name, so we can handle cases
                    # Where we want to use the marketing name, even when
                    # it doesn't map to the canonical expansion name
                    try:
                        oExp = IExpansion(sCandExpName)
                        sExpName = oExp.name
                    except SQLObjectNotFound:
                        # Just fall through and fail on the next check
                        sExpName = sCandExpName
                    if _check_exp_name(sExpName, oAbsCard):
                        sDeckName = oMatch.groups()[1]
                        for iPostfix in self.aPostfixes:
                            if len(oMatch.groups()) <= iPostfix:
                                break
                            if oMatch.groups()[iPostfix]:
                                sDeckName += ' ' + oMatch.groups()[iPostfix]
                        dMatches[sType].append((oCS, oMatch.groups()[0],
                                                sDeckName))

        # Find the card in the starter decks
        dInfo = {'Starters': [], 'Demos': [], 'Fixed': []}
        for sType, aResults in dMatches.items():
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

    def post_set_card_text(self, oPhysCard):
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
            oCardTextBuf.labelled_list('Preconstructed Decks',
                                       dInfo['Starters'], 'starters')

        if dInfo['Fixed']:
            oCardTextBuf.set_cur_iter_to_mark('expansion')
            oCardTextBuf.tag_text("\n")
            oCardTextBuf.labelled_list('Fixed Distribution Sets',
                                       dInfo['Fixed'], 'starters')

        oCardTextBuf.set_cur_iter(oTempIter)


plugin = StarterInfoPlugin
