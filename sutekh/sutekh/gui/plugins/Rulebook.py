# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar+sutekh@gmail.com>
# GPL - see COPYING for details

"""Downloads rulebook HTML pages and makes them available via the Help menu."""

import datetime
import os
from io import BytesIO
import webbrowser
import zipfile
from logging import Logger

from gi.repository import Gtk

from sutekh.base.Utility import prefs_dir, ensure_dir_exists
from sutekh.base.io.UrlOps import urlopen_with_timeout
from sutekh.base.gui.FileOrUrlWidget import FileOrUrlWidget
from sutekh.base.gui.GuiDataPack import gui_error_handler, progress_fetch_data
from sutekh.base.gui.SutekhDialog import SutekhDialog, do_exception_complaint
from sutekh.base.gui.SutekhFileWidget import add_filter
from sutekh.base.gui.ProgressDialog import (ProgressDialog,
                                            SutekhCountLogHandler)

from sutekh.io.DataPack import DOC_URL, find_data_pack, find_all_data_packs
from sutekh.gui.PluginManager import SutekhPlugin


class RulebookConfigDialog(SutekhDialog):
    # pylint: disable=too-many-public-methods
    # Gtk Widget, so has many public methods
    """Dialog for configuring the Rulebook plugin."""

    sDocUrl = DOC_URL

    def __init__(self, oParent, bFirstTime=False):
        super().__init__(
            'Configure Rulebook Info Plugin', oParent,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            ("_OK", Gtk.ResponseType.OK,
             "_Cancel", Gtk.ResponseType.CANCEL))
        oDescLabel = Gtk.Label()
        if not bFirstTime:
            oDescLabel.set_markup('<b>Choose how to configure the rulebook'
                                  ' plugin</b>')
        else:
            oDescLabel.set_markup('<b>Choose how to configure the rulebook'
                                  ' plugin</b>\nChoose cancel to skip '
                                  'configuring the plugin\nYou will not be '
                                  'prompted again')
        self.oFileWidget = FileOrUrlWidget(oParent, "Choose location for "
                                           "rulebook zip file",
                                           {'Sutekh Datapack': self.sDocUrl})
        add_filter(self.oFileWidget, 'Zip Files', ['*.zip', '*.ZIP'])
        # pylint: disable=no-member
        # pylint doesn't pick up vbox methods correctly
        self.vbox.pack_start(oDescLabel, False, False, 0)
        self.vbox.pack_start(self.oFileWidget, False, False, 0)
        if bFirstTime:
            # description is longer, so request should be taller
            self.set_size_request(340, 240)
        else:
            self.set_size_request(340, 200)

        self.show_all()

    def get_data(self):
        """Return the zip file data containing the rulebooks"""
        sFile, _bUrl = self.oFileWidget.get_file_or_url()
        sData = None
        if sFile == self.sDocUrl:
            # Downloading from sutekh datapack, so need magic to get right file
            sZipUrl, sHash = find_data_pack('rulebooks',
                                            fErrorHandler=gui_error_handler)
            if not sZipUrl:
                # failed to get datapack
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


class RulebookPlugin(SutekhPlugin):
    """Plugin allowing downloading of rulebook HTML pages and making them
       available via the Plugins menu.
       """
    aModelsSupported = ("MainWindow",)

    dGlobalConfig = {
        'rulebook path': 'string(default=None)',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._oRulebookDlg = None
        # TODO: First menu item is a hackish way to get at the parent Rulebook
        #       menu. Remove this once the plugin API provides a better way to
        #       add and remove items from a top-level menu.
        self._oFirstMenuItem = None
        self._sPrefsPath = None

    def _read_index(self):
        """Read the list of rulebooks from the index.txt file.

           Return a list of (filename, title) tuples.
           """
        sIndexFile = os.path.join(self._sPrefsPath, 'index.txt')
        if not os.path.isfile(sIndexFile):
            return []
        aRulebooks = []
        with open(sIndexFile, 'r') as oFile:
            for sLine in oFile:
                sFilename, sSep, sTitle = sLine.partition(':')
                if not sSep:
                    continue
                aRulebooks.append((sFilename.strip(), sTitle.strip()))
        return aRulebooks

    def get_menu_item(self):
        """Overrides method from base class.

           Adds the menu item on the MainWindow if the files can be found.
           """
        # Need to set this up here, after register_with_config has been called
        self._sPrefsPath = self.get_config_item('rulebook path')
        if self._sPrefsPath is None:
            self._sPrefsPath = os.path.join(prefs_dir('Sutekh'), 'rulebook')
            self.set_config_item('rulebook path', self._sPrefsPath)

        oConfigMenuItem = Gtk.MenuItem(label="Download Rulebook Files")
        oConfigMenuItem.connect("activate", self.config_activate)

        aMenuList = [('Data Downloads', oConfigMenuItem)]

        for oItem in self._recreate_menu_items():
            aMenuList.append(('Rulebook', oItem))

        return aMenuList

    def check_for_updates(self):
        """Check to see if the rulebooks need to be updated."""
        sIndexFile = os.path.join(self._sPrefsPath, 'index.txt')
        if not os.path.isfile(sIndexFile):
            return None
        aUrls, aDates, _aHashes = find_all_data_packs(
            'rulebooks', fErrorHandler=gui_error_handler)
        if not aUrls:
            # Timeout means we skip trying anything
            return None
        try:
            oUrlDate = datetime.datetime.strptime(aDates[0], '%Y-%m-%d')
        except ValueError:
            # Maybe should error here
            return None
        # We use the date of the index file as reference point
        oFileDate = datetime.datetime.fromtimestamp(os.path.getmtime(sIndexFile))
        if oFileDate < oUrlDate:
            return "Updated rulebook and rulings available"
        return None

    def do_update(self):
        """Download rulebooks and update the menu"""
        sZipUrl, sHash = find_data_pack('rulebooks',
                                        fErrorHandler=gui_error_handler)
        if not sZipUrl:
            return
        oFile = urlopen_with_timeout(sZipUrl,
                                     fErrorHandler=gui_error_handler,
                                     bBinary=True)
        if not oFile:
            return
        # pylint: disable=broad-except
        # We do want everything here
        try:
            sData = progress_fetch_data(oFile, None, sHash)
            oRawFile = BytesIO(sData)
            oZipFile = zipfile.ZipFile(oRawFile, 'r')
            self._unpack_zip_with_prog_bar(oZipFile)
        except Exception:
            do_exception_complaint('Unable to successfully download or '
                                   'the rulebook files')
        # pylint: enable=broad-except
        self._update_menu()

    def _recreate_menu_items(self):
        """Read the index file, update the first menu item hack
           and return the list of menu items.
           """
        aItems = []
        for sFilename, sTitle in self._read_index():
            oItem = Gtk.MenuItem(label=sTitle)
            oItem.connect("activate", self.rulebook_activate, sFilename)
            aItems.append(oItem)
        if not aItems:
            oItem = Gtk.MenuItem(label='No rulebooks')
            oItem.set_sensitive(False)
            aItems.append(oItem)
        self._oFirstMenuItem = aItems[0]
        return aItems

    def _update_menu(self):
        """Read index file and update which menu items are active
           accordingly.
           """
        oRulebookMenu = self._oFirstMenuItem.get_parent()
        for oChild in oRulebookMenu.get_children():
            oRulebookMenu.remove(oChild)

        for oItem in self._recreate_menu_items():
            oRulebookMenu.append(oItem)

        oRulebookMenu.show_all()

    def setup(self):
        """Prompt the user to download/setup the rulebook the first time"""
        sIndexTxt = os.path.join(self._sPrefsPath, 'index.txt')
        if not os.path.exists(sIndexTxt):
            # Looks like the first time
            oDialog = RulebookConfigDialog(self.parent, True)
            self.handle_config_response(oDialog)
            # Don't get called next time
            ensure_dir_exists(self._sPrefsPath)
            if not os.path.exists(sIndexTxt):
                fIndexTxt = open(sIndexTxt, "wb")
                fIndexTxt.close()

    def config_activate(self, _oMenuWidget):
        """Launch the configuration dialog."""
        oDialog = RulebookConfigDialog(self.parent, False)
        self.handle_config_response(oDialog)

    def rulebook_activate(self, _oMenuWidget, sFilename):
        """Show HTML file associated with the sName."""
        sPath = os.path.join(self._sPrefsPath, sFilename)
        sPath = os.path.abspath(sPath)
        sDrive, sPath = os.path.splitdrive(sPath)
        # os.path.splitdrive assumes that drives have the form "X:"
        # so do the same in our replace.
        sPath = sDrive.replace(":", "|") + sPath
        sPath = sPath.replace(os.path.sep, "/")
        if not sPath.startswith("/"):
            sPath = "/" + sPath
        sUrl = "file:///" + sPath
        webbrowser.open(sUrl)

    def _link_resource(self, sLocalUrl):
        """Return a file-like object which sLocalUrl can be read from."""
        sResource = os.path.join(self._sPrefsPath, sLocalUrl)
        if os.path.exists(sResource):
            return open(sResource, 'rb')
        else:
            raise ValueError("Unknown resource %s" % sLocalUrl)

    def handle_config_response(self, oConfigDialog):
        """Handle the response from the config dialog"""
        iResponse = oConfigDialog.run()

        if iResponse == Gtk.ResponseType.OK:
            # pylint: disable=broad-except
            # we want to catch all errors here
            try:
                sData = oConfigDialog.get_data()
                if sData:
                    oRawFile = BytesIO(sData)
                    oZipFile = zipfile.ZipFile(oRawFile, 'r')
                    self._unpack_zip_with_prog_bar(oZipFile)
                # else is the error path, but we'll have already shown
                # a complaint (timeout, etc), so just do nothing
            except Exception:
                do_exception_complaint('Unable to successfully download or '
                                       'copy some or all of the rulebook '
                                       'files')

        self._update_menu()

        # get rid of the dialog
        oConfigDialog.destroy()

    def _unpack_zip_with_prog_bar(self, oZipFile):
        """Unpack the contenst of the zip file showing progress as we go."""
        oLogHandler = SutekhCountLogHandler()
        oProgressDialog = ProgressDialog()
        oProgressDialog.set_description("Importing Rulebooks")
        oLogger = Logger('Read zip file')

        oLogger.addHandler(oLogHandler)
        oLogHandler.set_dialog(oProgressDialog)
        oLogHandler.set_total(len(oZipFile.infolist()))
        oProgressDialog.show()

        try:
            self._unpack_zipfile(oZipFile, oLogger)
        finally:
            oProgressDialog.destroy()

    def _unpack_zipfile(self, oZipFile, oLogger):
        """Unpack the contents of the zip file into the preferences folder."""
        ensure_dir_exists(self._sPrefsPath)

        for oItem in oZipFile.infolist():
            sBasename = os.path.basename(oItem.filename)
            oLogger.info('Read %s' % sBasename)
            sFile = os.path.join(self._sPrefsPath, sBasename)
            oData = oZipFile.read(oItem.filename)

            oFile = open(sFile, 'wb')
            oFile.write(oData)
            oFile.close()


plugin = RulebookPlugin
