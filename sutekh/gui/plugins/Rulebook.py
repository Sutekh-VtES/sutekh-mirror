# Rulebook.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar+sutekh@gmail.com>
# GPL - see COPYING for details

"""Downloads rulebook HTML pages and makes them available via the Help menu."""

from sutekh.io.DataPack import find_data_pack, DOC_URL
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.gui.FileOrUrlWidget import FileOrUrlWidget
from sutekh.gui.SutekhDialog import SutekhDialog, do_exception_complaint
from sutekh.gui.FileOrUrlWidget import fetch_data
from sutekh.gui.SutekhFileWidget import add_filter
from sutekh.gui.ProgressDialog import ProgressDialog, SutekhCountLogHandler
from sutekh.SutekhUtility import prefs_dir, ensure_dir_exists
import gtk
import os
import StringIO
import urllib2
import webbrowser
import zipfile
from logging import Logger


class RulebookConfigDialog(SutekhDialog):
    # pylint: disable-msg=R0904
    # R0904 - gtk Widget, so has many public methods
    """Dialog for configuring the Rulebook plugin."""

    sDocUrl = DOC_URL

    def __init__(self, oParent, bFirstTime=False):
        super(RulebookConfigDialog, self).__init__(
                'Configure Rulebook Info Plugin', oParent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL,
                    gtk.RESPONSE_CANCEL))
        oDescLabel = gtk.Label()
        if not bFirstTime:
            oDescLabel.set_markup('<b>Choose how to configure the rulebook'
                    ' plugin</b>')
        else:
            oDescLabel.set_markup('<b>Choose how to configure the rulebook'
                    ' plugin</b>\nChoose cancel to skip configuring the '
                    ' plugin\nYou will not be prompted again')
        self.oFileWidget = FileOrUrlWidget(oParent, "Choose location for "
                "rulebook zip file", {'Sutekh Wiki': self.sDocUrl})
        add_filter(self.oFileWidget, 'Zip Files', ['*.zip', '*.ZIP'])
        # pylint: disable-msg=E1101
        # pylint doesn't pick up vbox methods correctly
        self.vbox.pack_start(oDescLabel, False, False)
        self.vbox.pack_start(self.oFileWidget, False, False)
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
            # Downloading from sutekh wiki, so need magic to get right file
            sZipUrl = find_data_pack('rulebooks')
            oFile = urllib2.urlopen(sZipUrl)
            sData = fetch_data(oFile)
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

    # pylint: disable-msg=W0142
    # ** magic OK here
    def __init__(self, *args, **kwargs):
        super(RulebookPlugin, self).__init__(*args, **kwargs)
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
        for sLine in open(sIndexFile, 'rU'):
            sFilename, sSep, sTitle = sLine.partition(':')
            if not sSep:
                continue
            aRulebooks.append((sFilename.strip(), sTitle.strip()))
        return aRulebooks

    def get_menu_item(self):
        """Overrides method from base class.

           Adds the menu item on the MainWindow if the files can be found.
           """
        if not self.check_versions() or not self.check_model_type():
            return None

        # Need to set this up here, after register_with_config has been called
        self._sPrefsPath = self.get_config_item('rulebook path')
        if self._sPrefsPath is None:
            self._sPrefsPath = os.path.join(prefs_dir('Sutekh'), 'rulebook')
            self.set_config_item('rulebook path', self._sPrefsPath)

        oConfigMenuItem = gtk.MenuItem("Download Rulebook Files")
        oConfigMenuItem.connect("activate", self.config_activate)

        aMenuList = [('Data Downloads', oConfigMenuItem)]

        for oItem in self._recreate_menu_items():
            aMenuList.append(('Rulebook', oItem))

        return aMenuList

    def _recreate_menu_items(self):
        """Read the index file, update the first menu item hack
           and return the list of menu items.
           """
        aItems = []
        for sFilename, sTitle in self._read_index():
            oItem = gtk.MenuItem(sTitle)
            oItem.connect("activate", self.rulebook_activate, sFilename)
            aItems.append(oItem)
        if not aItems:
            oItem = gtk.MenuItem('No rulebooks')
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
            return file(sResource, 'rb')
        else:
            raise ValueError("Unknown resource %s" % sLocalUrl)

    def handle_config_response(self, oConfigDialog):
        """Handle the response from the config dialog"""
        iResponse = oConfigDialog.run()

        if iResponse == gtk.RESPONSE_OK:
            # pylint: disable-msg=W0703
            # we want to catch all errors here
            try:
                oRawFile = StringIO.StringIO(oConfigDialog.get_data())
                oZipFile = zipfile.ZipFile(oRawFile, 'r')
                self._unpack_zipfile_with_progress_bar(oZipFile)
            except Exception:
                do_exception_complaint('Unable to successfully download or '
                                       'copy some or all of the rulebook '
                                       'files')

        self._update_menu()

        # get rid of the dialog
        oConfigDialog.destroy()

    def _unpack_zipfile_with_progress_bar(self, oZipFile):
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
