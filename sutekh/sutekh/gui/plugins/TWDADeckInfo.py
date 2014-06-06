# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2012 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Adds info about the TWDA decks cards are found in"""

from sutekh.base.core.BaseObjects import (PhysicalCardSet,
                                          MapPhysicalCardToPhysicalCardSet,
                                          IPhysicalCardSet, PhysicalCard,
                                          IAbstractCard)
from sutekh.base.core.BaseFilters import (FilterOrBox, FilterAndBox,
                                          SpecificCardFilter,
                                          MultiPhysicalCardSetMapFilter)
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.base.gui.ProgressDialog import (ProgressDialog,
                                            SutekhCountLogHandler)
from sutekh.base.gui.SutekhDialog import (SutekhDialog, do_exception_complaint,
                                          do_complaint_error)
from sutekh.base.core.CardSetUtilities import (delete_physical_card_set,
                                               find_children, has_children)
from sutekh.io.ZipFileWrapper import ZipFileWrapper
from sutekh.base.io.UrlOps import urlopen_with_timeout, fetch_data
from sutekh.io.DataPack import find_all_data_packs, DOC_URL
from sutekh.base.gui.GuiCardSetFunctions import (reparent_all_children,
                                                 update_open_card_sets)
from sutekh.base.gui.FileOrUrlWidget import FileOrUrlWidget
from sutekh.base.gui.SutekhFileWidget import add_filter
from sutekh.base.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.base.gui.GuiDataPack import gui_error_handler
import re
import gtk
import datetime
from logging import Logger
from StringIO import StringIO
from sqlobject import sqlhub, SQLObjectNotFound


class BinnedCountLogHandler(SutekhCountLogHandler):
    """Wrapped around SutekhCountLogHandler to handle downloading
       multiple files with a single progess dialog"""

    def __init__(self):
        super(BinnedCountLogHandler, self).__init__()
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
    # pylint: disable-msg=R0904
    # R0904 - gtk Widget, so has many public methods
    """Dialog for configuring the TWDA plugin."""

    sDocUrl = DOC_URL

    def __init__(self, oParent, bFirstTime=False):
        super(TWDAConfigDialog, self).__init__(
            'Configure TWDA Info Plugin',
            oParent,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_OK, gtk.RESPONSE_OK,
             gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        oDescLabel = gtk.Label()
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
                                           {'Sutekh Wiki': self.sDocUrl})
        add_filter(self.oFileWidget, 'Zip Files', ['*.zip', '*.ZIP'])
        # pylint: disable-msg=E1101
        # pylint doesn't pick up vbox methods correctly
        self.vbox.pack_start(oDescLabel, False, False)
        self.vbox.pack_start(gtk.HSeparator(), False, False)
        self.vbox.pack_start(self.oFileWidget, False, False)

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
        # Get data from sutekh wiki
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

    # pylint: disable-msg=W0142
    # ** magic OK here
    def __init__(self, *args, **kwargs):
        super(TWDAInfoPlugin, self).__init__(*args, **kwargs)
        self.oAllTWDA = None
        self.oAnyTWDA = None

    def get_menu_item(self):
        """Overrides method from base class.

           Adds the menu item to the analyze menu.
           """
        if not self.check_versions() or not self.check_model_type():
            return None
        if self.model is None:
            # Add entry to the data download menu
            oDownload = gtk.MenuItem("Download TWDA decks")
            oDownload.connect('activate', self.do_download)
            return ('Data Downloads', oDownload)
        # Add entries to the analyze list
        oTWDMenu = gtk.MenuItem('Find TWDA decks containing ... ')
        oSubMenu = gtk.Menu()
        oTWDMenu.set_submenu(oSubMenu)
        self.oAllTWDA = gtk.MenuItem("ALL selected cards")
        oSubMenu.add(self.oAllTWDA)
        self.oAllTWDA.connect("activate", self.find_twda, "all")
        self.oAnyTWDA = gtk.MenuItem("ANY selected cards")
        oSubMenu.add(self.oAnyTWDA)
        self.oAnyTWDA.connect("activate", self.find_twda, "any")
        if self.check_enabled():
            self.oAnyTWDA.set_sensitive(True)
            self.oAllTWDA.set_sensitive(True)
        else:
            self.oAnyTWDA.set_sensitive(False)
            self.oAllTWDA.set_sensitive(False)
        return ('Analyze', oTWDMenu)

    def cleanup(self):
        """Disconnect the database listeners"""
        super(TWDAInfoPlugin, self).cleanup()

    def _get_selected_cards(self):
        """Extract selected cards from the selection."""
        dSelected = self.view.process_selection()
        aAbsCards = []
        for sCardName in dSelected:
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oCard = IAbstractCard(sCardName)
            aAbsCards.append(oCard)

        return aAbsCards

    def find_twda(self, _oWidget, sMode):
        """Find decks which match the given search"""
        aAbsCards = self._get_selected_cards()
        if not aAbsCards:
            do_complaint_error('Need to select some cards for this plugin')
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

        # pylint: disable-msg=E1101
        # Pyprotocols confuses pylint
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
        oDlg = SutekhDialog("TWDA matches", self.parent,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        oDlg.set_default_size(700, 600)
        # We create tabs for each year, and then list card
        # sets below them
        if dCardSets:
            self._fill_dlg(oDlg, dCardSets, sMatchText)
        else:
            self._empty_dlg(oDlg, sMatchText)

        oDlg.show_all()
        oDlg.run()
        oDlg.destroy()

    def _fill_dlg(self, oDlg, dCardSets, sMatchText):
        """Add info about the card sets to the dialog"""
        aParents = set([oCS.parent.name for oCS in dCardSets])
        dPages = {}
        oNotebook = gtk.Notebook()
        oNotebook.set_scrollable(True)
        oNotebook.popup_enable()
        oDlg.vbox.pack_start(oNotebook, expand=True)
        for sName in sorted(aParents):
            oInfo = gtk.VBox(False, 2)
            oTitle = gtk.Label(sName.replace("TWDA ", ""))
            oNotebook.append_page(AutoScrolledWindow(oInfo, True),
                                  oTitle)
            oInfo.pack_start(gtk.Label(sMatchText), expand=False, padding=6)
            iCardSets = len([x for x in dCardSets if x.parent.name == sName])
            oInfo.pack_start(gtk.Label("%d Card Sets" % iCardSets),
                             expand=False, padding=4)
            dPages[sName] = oInfo

        for oCS in sorted(dCardSets, key=lambda x: x.name):
            oInfo = dPages[oCS.parent.name]
            oName = gtk.Label(oCS.name)
            aCardInfo = []
            for sName in sorted(dCardSets[oCS]):
                aCardInfo.append(u"  - %s \u00D7 %d" % (sName,
                                 dCardSets[oCS][sName]))
            oCards = gtk.Label('\n'.join(aCardInfo))
            oButton = gtk.Button("Open cardset")
            oButton.connect('clicked', self._open_card_set, oCS)
            oInfo.pack_start(oName, expand=False)
            oInfo.pack_start(oCards, expand=False)
            oInfo.pack_start(oButton, expand=False)
            oInfo.pack_start(gtk.HSeparator(), expand=False)

    def _empty_dlg(self, oDlg, sMatchText):
        """Add an nothing found notice to dialog"""
        oLabel = gtk.Label("No decks found statisfying %s" % sMatchText)
        oDlg.vbox.pack_start(oLabel)

    def _open_card_set(self, _oButton, oCS):
        """Wrapper around open_cs to handle being called directly from a
           gtk widget"""
        self.open_cs(oCS.name)

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
            if not self.check_enabled():
                oDialog = TWDAConfigDialog(self.parent, True)
                self.handle_response(oDialog)

    def do_download(self, _oMenuWidget):
        """Prompt the user to download/setup decks"""
        oDialog = TWDAConfigDialog(self.parent)
        self.handle_response(oDialog)

    def handle_response(self, oDialog):
        """Handle running and responding to the download dialog"""
        iResponse = oDialog.run()
        if iResponse == gtk.RESPONSE_OK:
            if oDialog.is_url():
                aUrls, aDates, _aHashes = oDialog.get_url_data()
                if not aUrls:
                    do_complaint_error('Unable to access TWD data')
                elif not self._get_decks(aUrls, aDates):
                    do_complaint_error(
                        'Unable to successfully download TWD data')
            else:
                self._unzip_twda_file(oDialog.get_file_data())
        # cleanup
        oDialog.destroy()

    def _get_decks(self, aUrls, aDates):
        """Unzip a file containing the decks."""
        aToUnzip = []
        aToReplace = []
        aZipHolders = []
        iZipCount = 0

        # pylint: disable-msg=E1101
        # Pyprotocols confuses pylint
        for sUrl, sDate in zip(aUrls, aDates):
            if not sUrl:
                return False
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
                aToUnzip.append((sUrl, sTWDA))
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
                aToUnzip.append((sUrl, sTWDA))
                aToReplace.append(sTWDA)
            elif oTWDDate < oUrlDate:
                # Url is newer, so we replace
                aToUnzip.append((sUrl, sTWDA))
                aToReplace.append(sTWDA)
        # Delete all TWDA entries in the holders we replace
        # We do this to handle card sets being removed from the TWDA
        # correctly
        oOldConn = sqlhub.processConnection
        oTrans = oOldConn.transaction()
        sqlhub.processConnection = oTrans
        for oCS in list(PhysicalCardSet.select()):
            if not oCS.parent:
                continue
            if oCS.parent.name in aToReplace:
                delete_physical_card_set(oCS.name)
        oTrans.commit(close=True)
        sqlhub.processConnection = oOldConn

        oLogHandler = BinnedCountLogHandler()
        oProgressDialog = ProgressDialog()
        oProgressDialog.set_description("Downlaoding TWDA data")
        oLogger = Logger('Download zip files')
        oLogger.addHandler(oLogHandler)
        oLogHandler.set_dialog(oProgressDialog)
        oLogHandler.set_tot_bins(len(aToUnzip))
        oProgressDialog.show()
        for sUrl, sTWDA in aToUnzip:
            oFile = urlopen_with_timeout(sUrl,
                                         fErrorHandler=gui_error_handler)
            oProgressDialog.set_description('Downloading %s' % sTWDA)
            sData = fetch_data(oFile, oLogHandler=oLogHandler,
                               fErrorHandler=gui_error_handler)
            oZipFile = ZipFileWrapper(StringIO(sData))
            aZipHolders.append(oZipFile)
            iZipCount += len(oZipFile.get_all_entries())
            oLogHandler.inc_cur_bin()
        oProgressDialog.destroy()

        oLogHandler = SutekhCountLogHandler()
        aExistingList = [x.name for x in PhysicalCardSet.select()]
        oProgressDialog = ProgressDialog()
        oProgressDialog.set_description("Adding TWDA Data")
        oLogger = Logger('Read zip file')
        oLogger.addHandler(oLogHandler)
        oLogHandler.set_dialog(oProgressDialog)
        oLogHandler.set_total(iZipCount)
        oProgressDialog.show()
        aCSList = []
        for oZipFile in aZipHolders:
            if not self._unzip_single_file(oZipFile, oLogger):
                # Abort on errors
                oProgressDialog.destroy()
                return False
            aCSList.extend(oZipFile.get_all_entries().keys())
        oProgressDialog.destroy()
        self._clean_empty(aCSList, aExistingList)
        self.reload_pcs_list()
        return True

    def _unzip_twda_file(self, oFile):
        """Unzip a single zip file containing all the TWDA entries"""
        oLogHandler = SutekhCountLogHandler()
        oProgressDialog = ProgressDialog()
        oProgressDialog.set_description("Importing TWDA Data")
        oLogger = Logger('Read zip file')
        aExistingList = [x.name for x in PhysicalCardSet.select()]
        dList = oFile.get_all_entries()
        # Check that we match holder regex
        bOK = False
        for sName in dList:
            oMatch = self.oTWDARegex.match(sName)
            if oMatch:
                bOK = True
                break
        if not bOK:
            oProgressDialog.destroy()
            return False  # No TWDA holders in zip file
        oLogger.addHandler(oLogHandler)
        oLogHandler.set_dialog(oProgressDialog)
        oLogHandler.set_total(len(dList))
        oProgressDialog.show()
        # delete all existing TWDA decks
        # We do this to handle card sets being removed from the TWDA
        # correctly
        aDecks = self._get_twda_names()
        for sName in aDecks:
            delete_physical_card_set(sName)
        if not self._unzip_single_file(oFile, oLogger):
            oProgressDialog.destroy()
            return False
        # Cleanup
        self._clean_empty(oFile.get_all_entries().keys(), aExistingList)
        self.reload_pcs_list()
        oProgressDialog.destroy()
        return True

    def _unzip_single_file(self, oFile, oLogger):
        """Heart of the reading loop - ensure we read parents before
           children, and correct for renames that occur."""
        dList = oFile.get_all_entries()
        bDone = False
        while not bDone:
            dRemaining = {}
            if self._unzip_list(oFile, dList, oLogger, dRemaining):
                bDone = len(dRemaining) == 0
                dList = dRemaining
            else:
                self.reload_pcs_list()
                return False  # Error
        return True

    def _unzip_list(self, oZipFile, dList, oLogger, dRemaining):
        """Extract the files left in the list."""
        oOldConn = sqlhub.processConnection
        oTrans = oOldConn.transaction()
        sqlhub.processConnection = oTrans
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
                    # Ensure we restore with the correct parent
                    # if it differs from the holder parent
                    if oCS.parent:
                        oHolder.parent = oCS.parent.name
                    delete_physical_card_set(oHolder.name)
                oHolder.create_pcs(self.cardlookup)
                reparent_all_children(oHolder.name, aChildren)
                if self.parent.find_cs_pane_by_set_name(oHolder.name):
                    # Already open, so update to changes
                    update_open_card_sets(self.parent, oHolder.name)
            except Exception, oException:
                sMsg = "Failed to import card set %s.\n\n%s" % (
                    sName, oException)
                do_exception_complaint(sMsg)
                oTrans.commit(close=True)
                sqlhub.processConnection = oOldConn
                return False
        oTrans.commit(close=True)
        sqlhub.processConnection = oOldConn
        return True

    # pylint: disable-msg=R0201
    # Method for consistency with _unzip methods
    def _clean_empty(self, aMyList, aExistingList):
        """Remove any newly created sets in that have no cards AND no
           children"""
        for sName in aMyList:
            if sName in aExistingList:
                continue  # Not a card set we added
            try:
                oCS = IPhysicalCardSet(sName)
            except SQLObjectNotFound:
                # set not there, so skip
                continue
            # pylint: disable-msg=E1101
            # QLObject + PyProtocols confuses pylint
            if has_children(oCS):
                continue
            if len(oCS.cards) > 0:
                continue  # has cards
            delete_physical_card_set(sName)

    # pylint: enable-msg=R0201

plugin = TWDAInfoPlugin
