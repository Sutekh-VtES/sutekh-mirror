# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2012 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Adds info about the TWDA decks cards are found in"""

import re
import datetime
from logging import Logger
from io import BytesIO

from gi.repository import Gtk

from sqlobject import SQLObjectNotFound

from sutekh.base.core.BaseTables import (PhysicalCardSet, PhysicalCard,
                                         MapPhysicalCardToPhysicalCardSet)
from sutekh.base.core.BaseAdapters import IAbstractCard, IPhysicalCardSet
from sutekh.base.core.BaseFilters import (FilterOrBox, FilterAndBox,
                                          SpecificCardFilter,
                                          MultiPhysicalCardSetMapFilter)
from sutekh.base.io.UrlOps import urlopen_with_timeout, fetch_data, HashError
from sutekh.base.gui.SutekhDialog import (SutekhDialog, NotebookDialog,
                                          do_complaint_error)
from sutekh.base.gui.ProgressDialog import (ProgressDialog,
                                            SutekhCountLogHandler)
from sutekh.base.gui.GuiCardSetFunctions import unzip_files_into_db
from sutekh.base.gui.FileOrUrlWidget import FileOrUrlWidget
from sutekh.base.gui.SutekhFileWidget import add_filter
from sutekh.base.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.base.gui.GuiDataPack import gui_error_handler

from sutekh.io.DataPack import find_all_data_packs, DOC_URL
from sutekh.io.ZipFileWrapper import ZipFileWrapper
from sutekh.gui.PluginManager import SutekhPlugin


class BinnedCountLogHandler(SutekhCountLogHandler):
    """Wrapped around SutekhCountLogHandler to handle downloading
       multiple files with a single progess dialog"""

    def __init__(self):
        super().__init__()
        self.fTotBins = 0.0
        self.fBinFrac = 0.0

    def set_tot_bins(self, iBins):
        """Set the total bins for the update steps"""
        self.fTotBins = float(iBins)

    def inc_cur_bin(self):
        """Move to the next bin"""
        self.fBinFrac += 1 / self.fTotBins
        # We require a call to set_total to set these
        self.iCount = 0
        self.fTot = 0.0

    def emit(self, _oRecord):
        """Scale the progress bar to just be a fraction of the current bin"""
        if self.oDialog is None:
            return
        self.iCount += 1
        fBinPos = self.iCount / (self.fTot * self.fTotBins)
        fBarPos = self.fBinFrac + fBinPos
        self.oDialog.update_bar(fBarPos)


class TWDAConfigDialog(SutekhDialog):
    # pylint: disable=too-many-public-methods
    # Gtk Widget, so has many public methods
    """Dialog for configuring the TWDA plugin."""

    sDocUrl = DOC_URL

    def __init__(self, oParent, bFirstTime=False):
        super().__init__(
            'Configure TWDA Info Plugin',
            oParent,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            ("_OK", Gtk.ResponseType.OK,
             "_Cancel", Gtk.ResponseType.CANCEL))
        oDescLabel = Gtk.Label()
        if not bFirstTime:
            oDescLabel.set_markup('<b>Choose how to configure the'
                                  ' Tournament Winning Deck Archive (TWDA)'
                                  ' info plugin</b>')
        else:
            oDescLabel.set_markup('<b>Choose how to configure the'
                                  ' Tournament Winning Deck Archive (TWDA)'
                                  ' info plugin</b>\nChoose cancel to skip'
                                  ' configuring the plugin\nYou will not be'
                                  ' prompted again')
        self.oFileWidget = FileOrUrlWidget(oParent, "Choose location for "
                                           "TWDA decks",
                                           {'Sutekh Datapack': self.sDocUrl})
        add_filter(self.oFileWidget, 'Zip Files', ['*.zip', '*.ZIP'])
        # pylint: disable=no-member
        # pylint doesn't pick up vbox methods correctly
        self.vbox.pack_start(oDescLabel, False, False, 0)
        self.vbox.pack_start(Gtk.HSeparator(), False, False, 0)
        self.vbox.pack_start(self.oFileWidget, False, False, 0)

        self.set_size_request(350, 300)

        self.show_all()

    def is_url(self):
        """Check if the user has chosen an url"""
        _sFile, bUrl = self.oFileWidget.get_file_or_url()
        return bUrl

    def get_file_data(self):
        """Get data from a physical file"""
        _sFile, bUrl = self.oFileWidget.get_file_or_url()
        if bUrl:
            return None
        return self.oFileWidget.get_binary_data()

    def get_url_data(self):
        """Return the relevant data from the url given.

           Returns a tuple of arrays (urls, dates, hashes)"""
        _sFile, bUrl = self.oFileWidget.get_file_or_url()
        if not bUrl:
            return None, None, None
        # Get data from sutekh datapacks
        return find_all_data_packs('twd', fErrorHandler=gui_error_handler)


class TWDAInfoPlugin(SutekhPlugin):
    """Plugin providing access to TWDA decks."""
    dTableVersions = {PhysicalCardSet: (5, 6, 7)}
    aModelsSupported = (PhysicalCardSet, PhysicalCard, 'MainWindow')

    # pattern for TWDA holders
    oTWDARegex = re.compile('^TWDA ([0-9]{4})$')

    dGlobalConfig = {
        'twda configured': 'option("Yes", "No", "Unasked", default="Unasked")',
    }

    sMenuName = "Find TWDA decks containing"

    sHelpCategory = "card_sets:analysis"

    sHelpText = """If you have downloaded the database of tournament winning
                   decks, this allows you to search the tournament winning
                   deck archive for decks containing specific combinations of
                   cards.

                   You can either search for all the selected cards or for
                   those that contain at least 1 of the selected cards.

                   The results are grouped by year, and list the number of
                   matching card found in each listed deck. The matching
                   decks can be opened as new panes by choosing the
                   "Open cardset" option.

                   The results dialog in not modal, so it's possible to
                   examine the opened card sets closely without closing
                   the search results."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.oAllTWDA = None
        self.oAnyTWDA = None

    def get_menu_item(self):
        """Overrides method from base class.

           Adds the menu item to the analyze menu.
           """
        if self.model is None:
            # Add entry to the data download menu
            oDownload = Gtk.MenuItem(label="Download TWDA decks")
            oDownload.connect('activate', self.do_download)
            return ('Data Downloads', oDownload)
        # Add entries to the analyze list
        oTWDMenu = Gtk.MenuItem(label=self.sMenuName + ' ... ')
        oSubMenu = Gtk.Menu()
        oTWDMenu.set_submenu(oSubMenu)
        self.oAllTWDA = Gtk.MenuItem(label="ALL selected cards")
        oSubMenu.add(self.oAllTWDA)
        self.oAllTWDA.connect("activate", self.find_twda, "all")
        self.oAnyTWDA = Gtk.MenuItem(label="ANY selected cards")
        oSubMenu.add(self.oAnyTWDA)
        self.oAnyTWDA.connect("activate", self.find_twda, "any")
        if self.check_enabled():
            self.oAnyTWDA.set_sensitive(True)
            self.oAllTWDA.set_sensitive(True)
        else:
            self.oAnyTWDA.set_sensitive(False)
            self.oAllTWDA.set_sensitive(False)
        return ('Analyze', oTWDMenu)

    def find_twda(self, _oWidget, sMode):
        """Find decks which match the given search"""
        # Only want the distinct cards - numbers are unimportant
        aAbsCards = set(self._get_selected_abs_cards())
        if not aAbsCards:
            do_complaint_error('Need to select some cards for this plugin')
            return
        if len(aAbsCards) > 20:
            do_complaint_error('Too many cards selected (%d). Please select '
                               'no more than 20 cards' % len(aAbsCards))
            return
        aCardFilters = []
        iTotCards = len(aAbsCards)
        for oCard in aAbsCards:
            aCardFilters.append(SpecificCardFilter(oCard))
        # needs to be OR, since we're matching against the card to card set
        # mapping table
        oCardFilter = FilterOrBox(aCardFilters)
        aNames = self._get_twda_names()
        oMapFilter = MultiPhysicalCardSetMapFilter(aNames)
        oFullFilter = FilterAndBox([oCardFilter, oMapFilter])

        # pylint: disable=no-member
        # SQLObject confuses pylint
        dCardSets = {}
        for oMapCard in oFullFilter.select(MapPhysicalCardToPhysicalCardSet):
            oCS = oMapCard.physicalCardSet
            sCardName = IAbstractCard(oMapCard).name
            dCardSets.setdefault(oCS, {})
            dCardSets[oCS].setdefault(sCardName, 0)
            dCardSets[oCS][sCardName] += 1

        if sMode == 'all' and iTotCards > 1:
            # This is a little clunky, but, because of how we construct the
            # filters, we currently have the any match set, so we need to
            # filter this down to those that match all the cards
            for oCS in list(dCardSets):
                if len(dCardSets[oCS]) != iTotCards:
                    # Not all, so drop this one
                    del dCardSets[oCS]

        sCards = '",  "'.join(sorted([x.name for x in aAbsCards]))
        if sMode == 'any':
            sMatchText = 'Matching ANY of "%s"' % sCards
        else:
            sMatchText = 'Matching ALL of "%s"' % sCards

        # Create a dialog showing the results
        if dCardSets:
            oDlg = self._fill_dlg(dCardSets, sMatchText)
        else:
            oDlg = self._empty_dlg(sMatchText)

        oDlg.set_default_size(700, 600)
        oDlg.show_all()
        oDlg.show()

    def _fill_dlg(self, dCardSets, sMatchText):
        """Add info about the card sets to the dialog"""
        oDlg = NotebookDialog("TWDA matches", self.parent,
                              Gtk.DialogFlags.DESTROY_WITH_PARENT,
                              ("_Close", Gtk.ResponseType.CLOSE))
        aParents = set([oCS.parent.name for oCS in dCardSets])
        dPages = {}
        oDlg.connect('response', lambda dlg, but: dlg.destroy())
        # We create tabs for each year, and then list card
        # sets below them
        for sName in sorted(aParents):
            oInfo = Gtk.VBox(homogeneous=False, spacing=2)
            oDlg.add_widget_page(AutoScrolledWindow(oInfo),
                                 sName.replace("TWDA ", ""))
            oInfo.pack_start(Gtk.Label(label=sMatchText), False, True, 6)
            iCardSets = len([x for x in dCardSets if x.parent.name == sName])
            oInfo.pack_start(Gtk.Label(label="%d Card Sets" % iCardSets),
                             False, True, 4)
            dPages[sName] = oInfo

        for oCS in sorted(dCardSets, key=lambda x: x.name):
            oInfo = dPages[oCS.parent.name]
            oName = Gtk.Label(label=oCS.name)
            aCardInfo = []
            for sName in sorted(dCardSets[oCS]):
                aCardInfo.append(
                    u"  - %s \u00D7 %d" % (sName, dCardSets[oCS][sName]))
            oCards = Gtk.Label(label='\n'.join(aCardInfo))
            oButton = Gtk.Button(label="Open cardset")
            oButton.connect('clicked', self._open_card_set, oCS)
            oInfo.pack_start(oName, False, True, 0)
            oInfo.pack_start(oCards, False, True, 0)
            oInfo.pack_start(oButton, False, True, 0)
            oInfo.pack_start(Gtk.HSeparator(), False, True, 0)
        return oDlg

    def _empty_dlg(self, sMatchText):
        """Add an nothing found notice to dialog"""
        # pylint: disable=no-member
        # Gtk confuses pylint
        oDlg = SutekhDialog("No TWDA matches", self.parent,
                            Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            ("_Close", Gtk.ResponseType.CLOSE))
        oDlg.connect('response', lambda dlg, but: dlg.destroy())
        oLabel = Gtk.Label(label="No decks found statisfying %s" % sMatchText)
        oDlg.vbox.pack_start(oLabel, True, True, 0)
        return oDlg

    def _open_card_set(self, _oButton, oCS):
        """Wrapper around open_cs to handle being called directly from a
           Gtk widget"""
        self._open_cs(oCS.name)

    def check_enabled(self):
        """check for TWD decks in the database and disable menu if not"""
        bEnabled = False
        for oCS in PhysicalCardSet.select():
            oMatch = self.oTWDARegex.match(oCS.name)
            if oMatch:
                bEnabled = True
                break
        return bEnabled

    def _get_twda_names(self):
        """Get names of all the TWDA entries in the current database"""
        aNames = []
        for oCS in PhysicalCardSet.select():
            if not oCS.parent or not oCS.inuse:
                continue
            oMatch = self.oTWDARegex.match(oCS.parent.name)
            if oMatch:
                aNames.append(oCS.name)
        return aNames

    def _get_twda_holders(self):
        """Return all the TWDA holders in the current database"""
        aHolders = []
        for oCS in PhysicalCardSet.select():
            oMatch = self.oTWDARegex.match(oCS.name)
            if oMatch:
                aHolders.append(oCS)
        return aHolders

    def setup(self):
        """1st time setup tasks"""
        sPrefsValue = self.get_config_item('twda configured')
        if sPrefsValue == 'Unasked':
            # First time
            self.set_config_item('twda configured', 'No')
            oDialog = TWDAConfigDialog(self.parent, True)
            self.handle_response(oDialog)

    def do_download(self, _oMenuWidget):
        """Prompt the user to download/setup decks"""
        oDialog = TWDAConfigDialog(self.parent)
        self.handle_response(oDialog)

    def handle_response(self, oDialog):
        """Handle running and responding to the download dialog"""
        iResponse = oDialog.run()
        if iResponse == Gtk.ResponseType.OK:
            if oDialog.is_url():
                aUrls, aDates, aHashes = oDialog.get_url_data()
                if not aUrls:
                    do_complaint_error('Unable to access TWD data')
                elif not self._get_decks(aUrls, aDates, aHashes):
                    do_complaint_error(
                        "Didn't find any TWD data to download")
                else:
                    # Successful download, so we're configured
                    self.set_config_item('twda configured', 'Yes')
            else:
                if self._unzip_twda_file(oDialog.get_file_data()):
                    # Success, so we're configured
                    self.set_config_item('twda configured', 'Yes')
        # cleanup
        oDialog.destroy()

    def check_for_updates(self):
        """Check for any updates at startup."""
        sPrefsValue = self.get_config_item('twda configured')
        if sPrefsValue.lower() != 'yes':
            return None
        aUrls, aDates, aHashes = find_all_data_packs(
            'twd', fErrorHandler=gui_error_handler)
        if not aUrls:
            # Timeout means we skip trying anything
            return None
        aToUnzip, _aToReplace = self._get_decks_to_download(aUrls, aDates,
                                                            aHashes)
        if aToUnzip:
            aMessages = ["The following TWDA updates are available: "]
            for _sUrl, sTWDA, _sHash in aToUnzip:
                aMessages.append("<b>%s</b>" % sTWDA)
            return '\n'.join(aMessages)
        return None

    def do_update(self):
        """Handle the 'download stuff' respone from the startup check"""
        sPrefsValue = self.get_config_item('twda configured')
        if sPrefsValue.lower() != 'yes':
            return
        aUrls, aDates, aHashes = find_all_data_packs(
            'twd', fErrorHandler=gui_error_handler)
        if not self._get_decks(aUrls, aDates, aHashes):
            do_complaint_error("Didn't find any TWD data to download")

    def _get_decks_to_download(self, aUrls, aDates, aHashes):
        """Check for any decks we need to download."""
        aToUnzip = []
        aToReplace = []

        for sUrl, sDate, sHash in zip(aUrls, aDates, aHashes):
            if not sUrl:
                return False, False
            # Check if we need to download this url
            # This is a bit crude, but works because we control the format
            sZipName = sUrl.split('/')[-1]
            sTWDA = sZipName.replace('Sutekh_', '').replace('.zip', '')
            # Drop any suffix to the TWDA name
            sTWDA = sTWDA[:9].replace('_', ' ')
            try:
                oHolder = IPhysicalCardSet(sTWDA)
            except SQLObjectNotFound:
                # New TWDA holder, so add it to the list
                aToUnzip.append((sUrl, sTWDA, sHash))
                continue
            # Existing TWDA entry, so check dates
            try:
                oUrlDate = datetime.datetime.strptime(sDate, '%Y-%m-%d')
            except ValueError:
                oUrlDate = None
            sTWDUpdated = "Date Updated:"
            oTWDDate = None
            for sLine in oHolder.annotations.splitlines():
                if sLine.startswith(sTWDUpdated):
                    sTWDDate = sLine.split(sTWDUpdated)[1][1:11]
                    try:
                        oTWDDate = datetime.datetime.strptime(sTWDDate,
                                                              '%Y-%m-%d')
                    except ValueError:
                        pass
            if oTWDDate is None or oUrlDate is None:
                # Unable to extract the dates correctly, so we treat this as
                # something to replace
                aToUnzip.append((sUrl, sTWDA, sHash))
                aToReplace.append(sTWDA)
            elif oTWDDate < oUrlDate:
                # Url is newer, so we replace
                aToUnzip.append((sUrl, sTWDA, sHash))
                aToReplace.append(sTWDA)
        return aToUnzip, aToReplace

    def _get_decks(self, aUrls, aDates, aHashes):
        """Unzip a file containing the decks."""
        aZipHolders = []
        aToUnzip, aToReplace = self._get_decks_to_download(aUrls, aDates,
                                                           aHashes)
        if not aToUnzip:
            return False
        # We download everything first, so we don't delete card sets which
        # fail to download.
        oBinLogHandler = BinnedCountLogHandler()
        oProgressDialog = ProgressDialog()
        oProgressDialog.set_description("Downloading TWDA data")
        oLogger = Logger('Download zip files')
        oLogger.addHandler(oBinLogHandler)
        oBinLogHandler.set_dialog(oProgressDialog)
        oBinLogHandler.set_tot_bins(len(aToUnzip))
        oProgressDialog.show()
        # We sort the list of urls to download for cosmetic reasons
        for sUrl, sTWDA, sHash in sorted(aToUnzip, key=lambda x: x[1]):
            oFile = urlopen_with_timeout(sUrl,
                                         fErrorHandler=gui_error_handler,
                                         bBinary=True)
            oProgressDialog.set_description('Downloading %s' % sTWDA)
            try:

                sData = fetch_data(oFile, sHash=sHash,
                                   oLogHandler=oBinLogHandler,
                                   fErrorHandler=gui_error_handler)
            except HashError:
                do_complaint_error("Checksum failed for %s\nSkipping"
                                   % sTWDA)
                # Don't delete this, since we're not replacing it
                aToReplace.remove(sTWDA)
                continue
            oZipFile = ZipFileWrapper(BytesIO(sData))
            aZipHolders.append(oZipFile)
            oBinLogHandler.inc_cur_bin()
        oProgressDialog.destroy()

        # Bomb out if we're going to end up doing nothing
        if not aZipHolders:
            return False

        # Delete all TWDA entries in the holders we replace
        # We do this to handle card sets being removed from the TWDA
        # correctly
        aToDelete = []
        for oCS in list(PhysicalCardSet.select()):
            if not oCS.parent:
                continue
            if oCS.parent.name in aToReplace:
                aToDelete.append(oCS.name)

        return unzip_files_into_db(aZipHolders, "Adding TWDA Data",
                                   self.parent, aToDelete)

    def _unzip_twda_file(self, oFile):
        """Unzip a single zip file containing all the TWDA entries"""
        dList = oFile.get_all_entries()
        # Check that we match holder regex
        bOK = False
        for sName in dList:
            oMatch = self.oTWDARegex.match(sName)
            if oMatch:
                bOK = True
                break
        if not bOK:
            return False  # No TWDA holders in zip file
        # delete all existing TWDA decks
        # We do this to handle card sets being removed from the TWDA
        # correctly
        aToDelete = self._get_twda_names()
        return unzip_files_into_db([oFile], "Adding TWDA Data", self.parent,
                                   aToDelete)


plugin = TWDAInfoPlugin
