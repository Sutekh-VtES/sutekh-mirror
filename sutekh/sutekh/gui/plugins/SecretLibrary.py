# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar+sutekh@gmail.com>
# GPL - see COPYING for details

"""Plugin for interacting with the Secret Library website."""

import logging
import re

from io import StringIO
from urllib.parse import urlencode

from gi.repository import Gtk
import keyring
from sqlobject import SQLObjectNotFound

from sutekh.base.Utility import move_articles_to_back
from sutekh.base.core.BaseTables import PhysicalCardSet
from sutekh.base.core.BaseAdapters import IAbstractCard, IKeyword
from sutekh.base.core.BaseFilters import FilterNot
from sutekh.base.gui.SutekhDialog import SutekhDialog, do_complaint_error
from sutekh.base.gui.GuiCardSetFunctions import import_cs
from sutekh.base.gui.GuiDataPack import gui_error_handler

from sutekh.SutekhInfo import SutekhInfo
from sutekh.core.Filters import CryptCardFilter
from sutekh.io.SLDeckParser import SLDeckParser
from sutekh.io.WriteSLDeck import SL_FIXES
from sutekh.io.DataPack import urlopen_with_timeout
from sutekh.io.SLInventoryParser import SLInventoryParser
from sutekh.gui.PluginManager import SutekhPlugin


def canonical_to_sl(sName):
    """Convert a canonical card name to a Secret Library name."""
    if sName in SL_FIXES:
        sName = SL_FIXES[sName]
    sName = move_articles_to_back(sName)
    return sName.encode('latin1')


class ImportExportBase(SutekhDialog):
    # pylint: disable=too-many-public-methods, too-many-instance-attributes
    # Gtk Widget, so has many public methods
    # we use a lot of attributes to pass the data around
    """Base class for import and export dialogs."""

    # pylint: disable=attribute-defined-outside-init, too-many-arguments
    # we define attributes outside __init__, but it's OK because of
    # plugin structure
    # We needs lots of parameters for flexibility here
    def _setup_vbox(self, sTitlePhrase, sSourcePhrase, aDeckWidgets,
                    aInvWidgets, sUsername, sPassword):
        """Set up Secret Library configuration dialog."""

        self.vbox.set_spacing(10)

        oDescLabel = Gtk.Label()
        oDescLabel.set_markup('<b>%s Secret Library</b>' % (sTitlePhrase,))

        self.vbox.pack_start(oDescLabel, False, False, 0)

        # Deck / Inventory Selector

        self._sNewName = ""
        self._oAsDeckButton = Gtk.RadioButton(group=None, label="Deck")
        self._oAsInvButton = Gtk.RadioButton(group=self._oAsDeckButton,
                                             label="Inventory")
        self._oAsDeckButton.connect("toggled", self._deck_inv_changed)

        self.vbox.pack_start(
            Gtk.Label(label="%s ..." % (sSourcePhrase,)), False, False, 0)
        self.vbox.pack_start(self._oAsDeckButton, False, False, 0)
        self.vbox.pack_start(self._oAsInvButton, False, False, 0)

        # Deck / Inventory specific widgets

        self._oDeckInvVbox = Gtk.VBox()
        self._aDeckWidgets = aDeckWidgets
        self._aInvWidgets = aInvWidgets
        self.vbox.pack_start(self._oDeckInvVbox, False, False, 0)
        self._deck_inv_changed(self._oAsDeckButton)

        # API URL

        self._oUrlEntry = Gtk.ComboBoxText()
        self._oUrlEntry.append_text(SecretLibrary.SL_API_URL)
        self._oUrlEntry.set_active(0)

        self.vbox.pack_start(Gtk.Label(label="Secret Library API URL"),
                             False, False, 0)
        self.vbox.pack_start(self._oUrlEntry, False, False, 0)

        # Username

        self._oUsernameEntry = Gtk.Entry()
        if sUsername:
            self._oUsernameEntry.set_text(sUsername)

        self.vbox.pack_start(Gtk.Label(label="Username"), False, False, 0)
        self.vbox.pack_start(self._oUsernameEntry, True, True, 0)

        # Password

        self._oPasswordEntry = Gtk.Entry()
        self._oPasswordEntry.set_visibility(False)
        if sPassword:
            self._oPasswordEntry.set_text(sPassword)

        self.vbox.pack_start(Gtk.Label(label="Password"), False, False, 0)
        self.vbox.pack_start(self._oPasswordEntry, True, True, 0)

    # pylint: enable=attribute-defined-outside-init

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

    def get_auth(self):
        """Return the username and password entered."""
        return self._oUsernameEntry.get_text(), self._oPasswordEntry.get_text()

    def get_sl_type(self):
        """Return whether the card set should be treated as a Secret Library
           deck or inventory.
           """
        if self._oAsDeckButton.get_active():
            return "deck"
        return "inventory"


class ImportDialog(ImportExportBase):
    # pylint: disable=too-many-public-methods
    # Gtk Widget, so has many public methods
    """Dialog for importing card sets from the Secret Library."""

    def __init__(self, oParent, sUsername, sPassword):
        super().__init__(
            'Import from Secret Library', oParent,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            ("_OK", Gtk.ResponseType.OK,
             "_Cancel", Gtk.ResponseType.CANCEL))

        self._oDeckId = Gtk.Entry()
        aDeckWidgets = [
            Gtk.Label(label="Deck Id Number"),
            self._oDeckId,
        ]

        self._setup_vbox("Import from", "Import from", aDeckWidgets, [],
                         sUsername, sPassword)

        self.show_all()

    def get_deck_id(self):
        """Get the Secret Library Deck Id (if exporting as a deck)"""
        if self.get_sl_type() != "deck":
            return None
        return self._oDeckId.get_text()


class ExportDialog(ImportExportBase):
    # pylint: disable=too-many-public-methods
    # Gtk Widget, so has many public methods
    """Dialog for exporting cards sets to the Secret Library."""

    def __init__(self, oParent, sUsername, sPassword):
        super().__init__(
            'Export to Secret Library', oParent,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            ("_OK", Gtk.ResponseType.OK,
             "_Cancel", Gtk.ResponseType.CANCEL))

        self._oPublic = Gtk.CheckButton("Make deck public")
        aDeckWidgets = [self._oPublic]

        self._oPurge = Gtk.CheckButton("Purge inventory on upload")
        aInvWidgets = [self._oPurge]

        self._setup_vbox("Export to", "Export as", aDeckWidgets, aInvWidgets,
                         sUsername, sPassword)

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

    dTableVersions = {PhysicalCardSet: (5, 6, 7)}
    aModelsSupported = (PhysicalCardSet, "MainWindow")

    dGlobalConfig = {
        'username': 'string(default=None)',
    }

    SL_USER_AGENT = "Sutekh Secret Library Plugin"
    SL_AGENT_VERSION = SutekhInfo.VERSION_STR

    SL_API_URL = "https://www.secretlibrary.info/api.php"

    def __init__(self, oCardListView, oCardListModel, cModelType):
        try:
            self.oIllegal = IKeyword('not for legal play')
        except SQLObjectNotFound as oExcDetails:
            logging.warning("Illegal keyword missing (%s).", oExcDetails,
                            exc_info=1)
            self.oIllegal = None
        super().__init__(oCardListView, oCardListModel, cModelType)

    def get_menu_item(self):
        """Register on the 'Export Card Set' or 'Import Card Set' Menu"""
        if self.model is None:
            oMenuItem = Gtk.MenuItem(label="Import from Secret Library")
            oMenuItem.connect("activate", self.make_import_dialog)
            sSection = 'Import Card Set'
        else:
            oMenuItem = Gtk.MenuItem(label="Export to Secret Library")
            oMenuItem.connect("activate", self.make_export_dialog)
            sSection = 'Export Card Set'

        return (sSection, oMenuItem)

    def get_auth(self):
        """Return username and password from configuration."""
        sUsername = self.get_config_item('username')
        sPassword = None
        if sUsername:
            sPassword = keyring.get_password('www.secretlibrary.info',
                                             sUsername)
        return sUsername, sPassword

    def set_auth(self, sUsername, sPassword):
        """Set the username and password in configuration."""
        self.set_config_item('username', sUsername)
        if sPassword:
            keyring.set_password('www.secretlibrary.info',
                                 sUsername, sPassword)

    def make_import_dialog(self, _oWidget):
        """Create the importing dialog"""
        sUsername, sPassword = self.get_auth()
        oDialog = ImportDialog(self.parent, sUsername, sPassword)
        self.handle_import_response(oDialog)

    def make_export_dialog(self, _oWidget):
        """Create the exporting dialog"""
        sUsername, sPassword = self.get_auth()
        oDialog = ExportDialog(self.parent, sUsername, sPassword)
        self.handle_export_response(oDialog)

    def handle_import_response(self, oImportDialog):
        """Handle the import dialog response."""
        iResponse = oImportDialog.run()

        if iResponse == Gtk.ResponseType.OK:
            sUsername, sPassword = oImportDialog.get_auth()
            self.set_auth(sUsername, sPassword)

            if oImportDialog.get_sl_type() == "deck":
                dData = {
                    'sl_deck_retrieve': '1',
                    'sl_user_agent': self.SL_USER_AGENT,
                    'sl_agent_version': self.SL_AGENT_VERSION,
                    'username': sUsername,
                    'password': sPassword,
                    'deck_id': oImportDialog.get_deck_id(),
                }
                sUrl = oImportDialog.get_api_url()
                self._import_deck(sUrl, dData)
            else:
                dData = {
                    'sl_inventory_export': '1',
                    'sl_user_agent': self.SL_USER_AGENT,
                    'sl_agent_version': self.SL_AGENT_VERSION,
                    'username': sUsername,
                    'password': sPassword,
                }
                sUrl = oImportDialog.get_api_url()
                self._import_inventory(sUrl, dData)

        # get rid of the dialog
        oImportDialog.destroy()

    def handle_export_response(self, oExportDialog):
        """Handle the export dialog response."""
        iResponse = oExportDialog.run()

        if iResponse == Gtk.ResponseType.OK:
            sUsername, sPassword = oExportDialog.get_auth()
            self.set_auth(sUsername, sPassword)

            if oExportDialog.get_sl_type() == "deck":
                dData = {
                    # title, author, description, crypt and library filled
                    # by self._export_deck
                    'sl_deck_submit': '1',
                    'sl_user_agent': self.SL_USER_AGENT,
                    'sl_agent_version': self.SL_AGENT_VERSION,
                    'username': sUsername,
                    'password': sPassword,
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
                    'username': sUsername,
                    'password': sPassword,
                }
                if oExportDialog.get_purge_inventory():
                    dData['inventory_purge'] = '1'
                sUrl = oExportDialog.get_api_url()
                self._export_inventory(sUrl, dData)

        # get rid of the dialog
        oExportDialog.destroy()

    SL_ERROR_RE = re.compile(r"^(?P<code>\d+)\:.*$")

    def _check_sl_result(self, sResponse):
        """Inspect the line for a Secret Library error report.
           Return True if no error is found, False otherwise. Pops up an
           error dialog to the user if an error is found.
           """
        # SL sometimes has a warning before the error message, hence this
        # logic
        for sLine in sResponse.split('\n'):
            oMatch = self.SL_ERROR_RE.search(sLine)
            if oMatch:
                if int(oMatch.group('code')) != 0:
                    do_complaint_error(
                        "The Secret Library site returned the error:\n"
                        + sLine.strip())
                    return False
        return True

    def _import_deck(self, sApiUrl, dData):
        """Import a Secret Library deck as a card set."""
        sData = urlencode(dData)
        oParser = SLDeckParser()

        fReq = urlopen_with_timeout(sApiUrl, fErrorHandler=gui_error_handler,
                                    sData=sData)
        if not fReq:
            # Probably a timeout we've already complained about,
            # so we just bail out of this
            return
        try:
            fIn = StringIO(fReq.read())
        finally:
            fReq.close()

        sFirstLine = fIn.readline()
        fIn.seek(0)

        if self._check_sl_result(sFirstLine):
            import_cs(fIn, oParser, self.parent)

    def _import_inventory(self, sApiUrl, dData):
        """Import a Secret Library inventory as a card set."""
        sData = urlencode(dData)
        oParser = SLInventoryParser()

        fReq = urlopen_with_timeout(sApiUrl, fErrorHandler=gui_error_handler,
                                    sData=sData)
        if not fReq:
            # Probable timeout
            return
        try:
            fIn = StringIO(fReq.read())
        finally:
            fReq.close()

        sFirstLine = fIn.readline()
        fIn.seek(0)

        if self._check_sl_result(sFirstLine):
            import_cs(fIn, oParser, self.parent)

    def _export_deck(self, sApiUrl, dData):
        """Export a card set to the Secret Library as a deck."""
        oCardSet = self._get_card_set()

        dData['title'] = oCardSet.name
        dData['author'] = oCardSet.author
        dData['description'] = oCardSet.comment
        dData['crypt'], dData['library'] = self._cs_as_deck()

        sData = urlencode(dData)

        fReq = urlopen_with_timeout(sApiUrl, fErrorHandler=gui_error_handler,
                                    sData=sData)
        if not fReq:
            # Probable timeout
            return
        try:
            sResponse = fReq.read()
        finally:
            fReq.close()

        self._check_sl_result(sResponse)

    def _export_inventory(self, sApiUrl, dData):
        """Export a card set to the Secret Library as an inventory."""
        dData['inventory_crypt'], dData['inventory_library'] = \
                self._cs_as_inventory()

        sData = urlencode(dData)

        fReq = urlopen_with_timeout(sApiUrl, fErrorHandler=gui_error_handler,
                                    sData=sData)
        if not fReq:
            # Probable timeout
            return
        try:
            sResponse = fReq.read()
        finally:
            fReq.close()

        self._check_sl_result(sResponse)

    def _exclude(self, oAbsCard):
        """Secret Library does not support storyline cards yet, so
           exclude them"""
        if self.oIllegal not in oAbsCard.keywords:
            # Excluded cards are all not legal for play
            return False
        for oPair in oAbsCard.rarity:
            if oPair.rarity.name == 'Storyline':
                # not legal for play, storyline card, so exclude
                return True
        return False

    def _cs_as_deck(self):
        """Convert a card set to an SL (crypt, library) string pair."""
        # populate crypt
        aCrypt = []
        oCryptFilter = CryptCardFilter()
        oCryptIter = self.model.get_card_iterator(oCryptFilter)

        for oCard in oCryptIter:
            oAbsCard = IAbstractCard(oCard)
            if self._exclude(oAbsCard):
                continue
            sCsvName = canonical_to_sl(oAbsCard.name)
            sCsvName = sCsvName.replace('(Advanced)', '(Adv)')
            aCrypt.append(sCsvName)

        # populate library
        aLibrary = []
        oLibraryFilter = FilterNot(oCryptFilter)
        oLibraryIter = self.model.get_card_iterator(oLibraryFilter)

        for oCard in oLibraryIter:
            oAbsCard = IAbstractCard(oCard)
            if self._exclude(oAbsCard):
                continue
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
            if self._exclude(oAbsCard):
                continue
            dCrypt.setdefault(oAbsCard, 0)
            dCrypt[oAbsCard] += 1

        # populate library dict
        dLibrary = {}
        oLibraryFilter = FilterNot(oCryptFilter)
        oLibraryIter = self.model.get_card_iterator(oLibraryFilter)

        for oCard in oLibraryIter:
            oAbsCard = IAbstractCard(oCard)
            if self._exclude(oAbsCard):
                continue
            dLibrary.setdefault(oAbsCard, 0)
            dLibrary[oAbsCard] += 1

        # create crypt strings
        aCrypt = []
        for oAbsCard, iCnt in dCrypt.items():
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
        for oAbsCard, iCnt in dLibrary.items():
            sCsvName = canonical_to_sl(oAbsCard.name)
            # See above
            sCsvName = sCsvName.replace('"', '')
            # TODO: populate wanted field sensibly.
            # HAVE; WANTED; Card Name
            aLibrary.append("%d;%d;%s" % (iCnt, iCnt, sCsvName))

        return "\n".join(aCrypt), "\n".join(aLibrary)


plugin = SecretLibrary
