# SecretLibrary.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar+sutekh@gmail.com>
# GPL - see COPYING for details

"""Plugin for interacting with the Secret Library website."""

import gtk
import urllib2
import urllib
import StringIO
import re
import unicodedata
from sutekh.SutekhInfo import SutekhInfo
from sutekh.core.SutekhObjects import PhysicalCardSet, IAbstractCard, \
    canonical_to_csv
from sutekh.core.Filters import CryptCardFilter, FilterNot
from sutekh.io.SLDeckParser import SLDeckParser
from sutekh.io.SLInventoryParser import SLInventoryParser
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error
from sutekh.gui.GuiCardSetFunctions import import_cs
from sutekh.gui.PluginManager import SutekhPlugin


def canonical_to_sl(sName):
    """Convert a canonical card name to a Secret Library name."""
    sName = canonical_to_csv(sName)
    return unicodedata.normalize('NFKD', sName).encode('ascii', 'ignore')


class ImportExportBase(SutekhDialog):
    # pylint: disable-msg=R0904, R0902
    # R0904 - gtk Widget, so has many public methods
    # R0902 - we use a lot of attributes to pass the data around
    """Base class for import and export dialogs."""

    _sCachedUsername = None
    _sCachedPassword = None

    # pylint: disable-msg=W0201
    # we define attributes outside __init__, but it's OK because of plugin
    # structure
    def _setup_vbox(self, sTitlePhrase, sSourcePhrase, aDeckWidgets,
                    aInvWidgets):
        """Set up Secret Library configuration dialog."""

        # pylint: disable-msg=E1101
        # pylint doesn't pick up vbox methods correctly

        self.vbox.set_spacing(10)

        oDescLabel = gtk.Label()
        oDescLabel.set_markup('<b>%s Secret Library</b>' % (sTitlePhrase,))

        self.vbox.pack_start(oDescLabel, False, False)

        # Deck / Inventory Selector

        self._sNewName = ""
        self._oAsDeckButton = gtk.RadioButton(None, "Deck")
        self._oAsInvButton = gtk.RadioButton(self._oAsDeckButton, "Inventory")
        self._oAsDeckButton.connect("toggled", self._deck_inv_changed)

        self.vbox.pack_start(
            gtk.Label("%s ..." % (sSourcePhrase,)), False, False)
        self.vbox.pack_start(self._oAsDeckButton, False, False)
        self.vbox.pack_start(self._oAsInvButton, False, False)

        # Deck / Inventory specific widgets

        self._oDeckInvVbox = gtk.VBox()
        self._aDeckWidgets = aDeckWidgets
        self._aInvWidgets = aInvWidgets
        self.vbox.pack_start(self._oDeckInvVbox, False, False)
        self._deck_inv_changed(self._oAsDeckButton)

        # API URL

        self._oUrlEntry = gtk.combo_box_entry_new_text()
        self._oUrlEntry.append_text(SecretLibrary.SL_API_URL)
        self._oUrlEntry.set_active(0)

        self.vbox.pack_start(gtk.Label("Secret Library API URL"), False, False)
        self.vbox.pack_start(self._oUrlEntry, False, False)

        # Username

        self._oUsernameEntry = gtk.Entry()
        if self._sCachedUsername:
            self._oUsernameEntry.set_text(self._sCachedUsername)

        self.vbox.pack_start(gtk.Label("Username"), False, False)
        self.vbox.pack_start(self._oUsernameEntry)

        # Password

        self._oPasswordEntry = gtk.Entry()
        self._oPasswordEntry.set_visibility(False)
        if self._sCachedPassword:
            self._oPasswordEntry.set_text(self._sCachedPassword)

        self.vbox.pack_start(gtk.Label("Password"), False, False)
        self.vbox.pack_start(self._oPasswordEntry)

    # pylint: enable-msg=W0201

    def _deck_inv_changed(self, _oWidget):
        """Handle a change in whether we're importing/exporting to/from a
           deck or an inventory.
           """
        if self._oAsDeckButton.get_active():
            aNewChildren = self._aDeckWidgets
        else:
            aNewChildren = self._aInvWidgets

        for oWidget in self._oDeckInvVbox.get_children():
            self._oDeckInvVbox.remove(oWidget)

        for oWidget in aNewChildren:
            self._oDeckInvVbox.add(oWidget)

        self._oDeckInvVbox.show_all()

    def get_api_url(self):
        """Return the current API URL."""
        return self._oUrlEntry.get_active_text()

    def get_username(self):
        """Return the username entered."""
        ImportExportBase._sCachedUsername = self._oUsernameEntry.get_text()
        return self._sCachedUsername

    def get_password(self):
        """Return the password entered."""
        ImportExportBase._sCachedPassword = self._oPasswordEntry.get_text()
        return self._sCachedPassword

    def get_sl_type(self):
        """Return whether the card set should be treated as a Secret Library
           deck or inventory.
           """
        if self._oAsDeckButton.get_active():
            return "deck"
        else:
            return "inventory"


class ImportDialog(ImportExportBase):
    # pylint: disable-msg=R0904
    # R0904 - gtk Widget, so has many public methods
    """Dialog for importing card sets from the Secret Library."""

    def __init__(self, oParent):
        super(ImportDialog, self).__init__('Import from Secret Library',
                oParent, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                 gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        self._oDeckId = gtk.Entry()
        aDeckWidgets = [
            gtk.Label("Deck Id Number"),
            self._oDeckId,
        ]

        self._setup_vbox("Import from", "Import from", aDeckWidgets, [])

        self.show_all()

    def get_deck_id(self):
        """Get the Secret Library Deck Id (if exporting as a deck)"""
        if self.get_sl_type() != "deck":
            return None
        return self._oDeckId.get_text()


class ExportDialog(ImportExportBase):
    # pylint: disable-msg=R0904
    # R0904 - gtk Widget, so has many public methods
    """Dialog for exporting cards sets to the Secret Library."""

    def __init__(self, oParent):
        super(ExportDialog, self).__init__('Export to Secret Library',
                oParent, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                 gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        self._oPublic = gtk.CheckButton("Make deck public")
        aDeckWidgets = [self._oPublic]

        self._oPurge = gtk.CheckButton("Purge inventory on upload")
        aInvWidgets = [self._oPurge]

        self._setup_vbox("Export to", "Export as", aDeckWidgets, aInvWidgets)

        self.show_all()

    def get_public(self):
        """Return True if the exported deck should be marked as public."""
        return self._oPublic.get_active()

    def get_purge_inventory(self):
        """Return True if the inventory should be purged before exporting."""
        return self._oPurge.get_active()


class SecretLibrary(SutekhPlugin):
    """Provides ability to export and import cards directly
       to and from the Secret Library.
       """

    dTableVersions = {PhysicalCardSet: (5, 6)}
    aModelsSupported = (PhysicalCardSet, "MainWindow")

    SL_USER_AGENT = "Sutekh Secret Library Plugin"
    SL_AGENT_VERSION = SutekhInfo.VERSION_STR

    SL_API_URL = "http://www.secretlibrary.info/api.php"

    def get_menu_item(self):
        """Register on the 'Export Card Set' or 'Import Card Set' Menu"""
        if not self.check_versions() or not self.check_model_type():
            return None

        if self.model is None:
            oMenuItem = gtk.MenuItem("Import from Secret Library")
            oMenuItem.connect("activate", self.make_import_dialog)
            sSection = 'Import Card Set'
        else:
            oMenuItem = gtk.MenuItem("Export to Secret Library")
            oMenuItem.connect("activate", self.make_export_dialog)
            sSection = 'Export Card Set'

        return (sSection, oMenuItem)

    def make_import_dialog(self, _oWidget):
        """Create the importing dialog"""
        oDialog = ImportDialog(self.parent)
        self.handle_import_response(oDialog)

    def make_export_dialog(self, _oWidget):
        """Create the exporting dialog"""
        oDialog = ExportDialog(self.parent)
        self.handle_export_response(oDialog)

    def handle_import_response(self, oImportDialog):
        """Handle the import dialog response."""
        iResponse = oImportDialog.run()

        if iResponse == gtk.RESPONSE_OK:
            if oImportDialog.get_sl_type() == "deck":
                dData = {
                    'sl_deck_retrieve': '1',
                    'sl_user_agent': self.SL_USER_AGENT,
                    'sl_agent_version': self.SL_AGENT_VERSION,
                    'username': oImportDialog.get_username(),
                    'password': oImportDialog.get_password(),
                    'deck_id': oImportDialog.get_deck_id(),
                }
                sUrl = oImportDialog.get_api_url()
                self._import_deck(sUrl, dData)
            else:
                dData = {
                    'sl_inventory_export': '1',
                    'sl_user_agent': self.SL_USER_AGENT,
                    'sl_agent_version': self.SL_AGENT_VERSION,
                    'username': oImportDialog.get_username(),
                    'password': oImportDialog.get_password(),
                }
                sUrl = oImportDialog.get_api_url()
                self._import_inventory(sUrl, dData)

        # get rid of the dialog
        oImportDialog.destroy()

    def handle_export_response(self, oExportDialog):
        """Handle the export dialog response."""
        iResponse = oExportDialog.run()

        if iResponse == gtk.RESPONSE_OK:
            if oExportDialog.get_sl_type() == "deck":
                dData = {
                    # title, author, description, crypt and library filled
                    # by self._export_deck
                    'sl_deck_submit': '1',
                    'sl_user_agent': self.SL_USER_AGENT,
                    'sl_agent_version': self.SL_AGENT_VERSION,
                    'username': oExportDialog.get_username(),
                    'password': oExportDialog.get_password(),
                    'public': oExportDialog.get_public() and '1' or '0',
                }
                sUrl = oExportDialog.get_api_url()
                self._export_deck(sUrl, dData)
            else:
                dData = {
                    # inventory_crypt and inventory_library filled in by
                    # self._export_inventory
                    'sl_inventory_import': '1',
                    'sl_user_agent': self.SL_USER_AGENT,
                    'sl_agent_version': self.SL_AGENT_VERSION,
                    'username': oExportDialog.get_username(),
                    'password': oExportDialog.get_password(),
                }
                if oExportDialog.get_purge_inventory():
                    dData['inventory_purge'] = '1'
                sUrl = oExportDialog.get_api_url()
                self._export_inventory(sUrl, dData)

        # get rid of the dialog
        oExportDialog.destroy()

    SL_ERROR_RE = re.compile("^(?P<code>\d+)\:.*$")

    def _check_sl_result(self, sLine):
        """Inspect the line for a Secret Library error report.
           Return True if no error is found, False otherwise. Pops up an
           error dialog to the user if an error is found.
           """
        oMatch = self.SL_ERROR_RE.match(sLine)
        if oMatch:
            if int(oMatch.group('code')) != 0:
                do_complaint_error(
                        "The Secret Library site returned the error:\n"
                        + sLine.strip())
                return False
        return True

    def _import_deck(self, sApiUrl, dData):
        """Import a Secret Library deck as a card set."""
        sData = urllib.urlencode(dData)
        oParser = SLDeckParser()

        oReq = urllib2.Request(url=sApiUrl, data=sData)
        fReq = urllib2.urlopen(oReq)
        try:
            fIn = StringIO.StringIO(fReq.read())
        finally:
            fReq.close()

        sFirstLine = fIn.readline()
        fIn.seek(0)

        if self._check_sl_result(sFirstLine):
            import_cs(fIn, oParser, self.parent)

    def _import_inventory(self, sApiUrl, dData):
        """Import a Secret Library inventory as a card set."""
        sData = urllib.urlencode(dData)
        oParser = SLInventoryParser()

        oReq = urllib2.Request(url=sApiUrl, data=sData)
        fReq = urllib2.urlopen(oReq)
        try:
            fIn = StringIO.StringIO(fReq.read())
        finally:
            fReq.close()

        sFirstLine = fIn.readline()
        fIn.seek(0)

        if self._check_sl_result(sFirstLine):
            import_cs(fIn, oParser, self.parent)

    def _export_deck(self, sApiUrl, dData):
        """Export a card set to the Secret Library as a deck."""
        oCardSet = self.get_card_set()

        dData['title'] = oCardSet.name
        dData['author'] = oCardSet.author
        dData['description'] = oCardSet.comment
        dData['crypt'], dData['library'] = self._cs_as_deck()

        sData = urllib.urlencode(dData)

        oReq = urllib2.Request(url=sApiUrl, data=sData)
        fReq = urllib2.urlopen(oReq)
        try:
            sResponse = fReq.read()
        finally:
            fReq.close()

        self._check_sl_result(sResponse)

    def _export_inventory(self, sApiUrl, dData):
        """Export a card set to the Secret Library as an inventory."""
        dData['inventory_crypt'], dData['inventory_library'] = \
                self._cs_as_inventory()

        sData = urllib.urlencode(dData)

        oReq = urllib2.Request(url=sApiUrl, data=sData)
        fReq = urllib2.urlopen(oReq)
        try:
            sResponse = fReq.read()
        finally:
            fReq.close()

        self._check_sl_result(sResponse)

    def _cs_as_deck(self):
        """Convert a card set to an SL (crypt, library) string pair."""
        # populate crypt
        aCrypt = []
        oCryptFilter = CryptCardFilter()
        oCryptIter = self.model.get_card_iterator(oCryptFilter)

        for oCard in oCryptIter:
            # pylint: disable-msg=E1101
            # E1101: PyProtocols confuses pylint
            oAbsCard = IAbstractCard(oCard)
            sCsvName = canonical_to_sl(oAbsCard.name)
            sCsvName = sCsvName.replace('(Advanced)', '(Adv)')
            aCrypt.append(sCsvName)

        # populate library
        aLibrary = []
        oLibraryFilter = FilterNot(oCryptFilter)
        oLibraryIter = self.model.get_card_iterator(oLibraryFilter)

        for oCard in oLibraryIter:
            # pylint: disable-msg=E1101
            # E1101: PyProtocols confuses pylint
            oAbsCard = IAbstractCard(oCard)
            aLibrary.append(canonical_to_sl(oAbsCard.name))

        return "\n".join(aCrypt), "\n".join(aLibrary)

    def _cs_as_inventory(self):
        """Convert a card set to an SL (inventory_crypt, inventory_library)
           string pair.
           """
        # populate crypt dict
        dCrypt = {}
        oCryptFilter = CryptCardFilter()
        oCryptIter = self.model.get_card_iterator(oCryptFilter)

        for oCard in oCryptIter:
            oAbsCard = IAbstractCard(oCard)
            dCrypt.setdefault(oAbsCard, 0)
            dCrypt[oAbsCard] += 1

        # populate library dict
        dLibrary = {}
        oLibraryFilter = FilterNot(oCryptFilter)
        oLibraryIter = self.model.get_card_iterator(oLibraryFilter)

        for oCard in oLibraryIter:
            oAbsCard = IAbstractCard(oCard)
            dLibrary.setdefault(oAbsCard, 0)
            dLibrary[oAbsCard] += 1

        # create crypt strings
        aCrypt = []
        for oAbsCard, iCnt in dCrypt.iteritems():
            sCsvName = canonical_to_sl(oAbsCard.name)
            sCsvName = sCsvName.replace('(Advanced)', '(Adv)')
            # Secret library doesn't like "'s here, it seems.
            sCsvName = sCsvName.replace('"', '')
            # TODO: populate wanted field sensibly.
            # HAVE; WANTED; Card Name
            aCrypt.append("%d;%d;%s" % (iCnt, iCnt, sCsvName))
        aCrypt.sort()

        # create library strings
        aLibrary = []
        for oAbsCard, iCnt in dLibrary.iteritems():
            sCsvName = canonical_to_sl(oAbsCard.name)
            # TODO: populate wanted field sensibly.
            # HAVE; WANTED; Card Name
            aLibrary.append("%d;%d;%s" % (iCnt, iCnt, sCsvName))

        return "\n".join(aCrypt), "\n".join(aLibrary)


plugin = SecretLibrary
