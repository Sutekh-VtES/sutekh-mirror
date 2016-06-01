# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Handle the multi pane UI for Sutkeh
# Copyright 2007, 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - See COPYING for details

"""Main window for Sutekh."""

import gtk
import logging
import datetime
import zipfile
from StringIO import StringIO
from sqlobject import SQLObjectNotFound
from sutekh.core.SutekhObjectCache import SutekhObjectCache
from sutekh.io.PhysicalCardSetWriter import PhysicalCardSetWriter
from sutekh.io.WwUrls import WW_CARDLIST_DATAPACK
from sutekh.io.DataPack import find_all_data_packs
from sutekh.base.io.UrlOps import urlopen_with_timeout, HashError
from sutekh.base.io.BaseZipFileWrapper import ZipEntryProxy
from sutekh.base.core.BaseObjects import IAbstractCard
from sutekh.base.core.DBUtility import flush_cache
from sutekh.gui.AboutDialog import SutekhAboutDialog
from sutekh.gui.MainMenu import MainMenu
from sutekh.gui.PluginManager import PluginManager
from sutekh.gui.GuiDBManagement import GuiDBManager
from sutekh.gui import SutekhIcon
from sutekh.gui.GuiIconManager import GuiIconManager
from sutekh.gui.CardTextFrame import CardTextFrame
from sutekh.base.gui.SutekhDialog import do_complaint, do_complaint_error
from sutekh.base.gui.AppMainWindow import AppMainWindow
from sutekh.base.gui.GuiUtils import save_config
from sutekh.base.gui.GuiDataPack import gui_error_handler, progress_fetch_data
from sutekh.base.gui.UpdateDialog import UpdateDialog


class SutekhMainWindow(AppMainWindow):
    """Window that has a configurable number of panes."""
    # pylint: disable=R0904, R0902
    # R0904 - gtk.Widget, so many public methods
    # R0902 - we need to keep a lot of state, so many instance attributes
    def __init__(self):
        super(SutekhMainWindow, self).__init__()
        self._cPCSWriter = PhysicalCardSetWriter
        self._sResourceName = 'sutekh'
        # We can shrink the window quite small
        self.set_size_request(100, 100)
        # But we start at a reasonable size
        self.set_default_size(800, 600)

        self._cDBManager = GuiDBManager

        # Set Default Window Icon for all Windows
        gtk.window_set_default_icon(SutekhIcon.SUTEKH_ICON)

        # Sutekh lookup cache
        self.__oSutekhObjectCache = None

    def _verify_database(self):
        """Check that the database is correctly populated"""
        try:
            _oCard = IAbstractCard('Ossian')
        except SQLObjectNotFound:
            # Log error so verbose picks it up
            logging.warn('Ossian not found in the database')
            # Inform the user
            iResponse = do_complaint(
                'Database is missing cards. Try import the cardlist now?',
                gtk.MESSAGE_ERROR, gtk.BUTTONS_YES_NO, False)
            if iResponse == gtk.RESPONSE_YES:
                self.do_refresh_card_list()

        # Create object cache
        self.__oSutekhObjectCache = SutekhObjectCache()

    def setup(self, oConfig):
        """After database checks are passed, setup what we need to display
           data from the database."""
        # Load plugins
        oPluginManager = PluginManager()
        # Create global icon manager
        oIconManager = GuiIconManager(oConfig.get_icon_path())
        oCardTextPane = CardTextFrame(self, oIconManager)

        self._do_app_setup(oConfig, oCardTextPane, oIconManager,
                           oPluginManager)
        # Check for updated card list
        self.check_updated_cardlist()

    def _create_app_menu(self):
        """Create the main application menu."""
        self._oMenu = MainMenu(self, self._oConfig)

    def update_to_new_db(self):
        """Resync panes against the database.

           Needed because ids aren't kept across re-reading the WW
           cardlist, since card sets with children are always created
           before there children are added.
           """
        # Flush the caches, so we don't hit stale lookups
        flush_cache()
        # Reset the lookup cache holder
        self.__oSutekhObjectCache = SutekhObjectCache()
        # We publish here, after we've cleared the caches
        super(SutekhMainWindow, self).update_to_new_db()

    def clear_cache(self):
        """Remove the cached set of objects, for card list reloads, etc."""
        del self.__oSutekhObjectCache

    # pylint: disable=R0201
    # convienent to have this as a method
    def show_about_dialog(self, _oWidget):
        """Display the about dialog"""
        oDlg = SutekhAboutDialog()
        oDlg.run()
        oDlg.destroy()

    # pylint: enable=R0201

    def show_tutorial(self):
        """Show the HTML Tutorial"""
        self._do_html_dialog("Tutorial.html")

    def show_manual(self):
        """Show the HTML Manual"""
        self._do_html_dialog("Manual.html")

    def check_updated_cardlist(self):
        """Check if an updated cardlist is available"""
        aUrls, aDates, aHashes = find_all_data_packs(
            WW_CARDLIST_DATAPACK, fErrorHandler=gui_error_handler)
        if not aUrls:
            # probable timeout, so bail
            return
        oCLDate = datetime.datetime.strptime(aDates[0], '%Y-%m-%d').date()
        oLastDate = self.config_file.get_last_update_date()
        if oLastDate < oCLDate:
            # There has been a cardlist update, so query the user
            oDlg = UpdateDialog(["CardList and Rulings"])
            iResponse = oDlg.run()
            oDlg.destroy()
            if iResponse != gtk.RESPONSE_OK:
                return
            # Get the datapack and unzip the files
            oFile = urlopen_with_timeout(aUrls[0],
                                         fErrorHandler=gui_error_handler)
            try:
                sData = progress_fetch_data(oFile, sHash=aHashes[0],
                                            sDesc="Downloading datapack")
            except HashError:
                do_complaint_error("Checksum failed for cardlist.\n"
                                   "Aborting update")
                return
            # Extract the individual files from the datapack
            oZipFile = zipfile.ZipFile(StringIO(sData), 'r')
            aNames = oZipFile.namelist()
            aFiles = []
            # Order required for GuiDBManagement
            for sName in ['cardlist.txt', 'extra_list.txt',
                          'expansiondates.csv', 'rulings.html']:
                if sName not in aNames:
                    do_complaint_error("Datapack is missing %s" % sName)
                    return
                oFile = ZipEntryProxy(oZipFile.read(sName))
                if sName == 'extra_list.txt':
                    aFiles.append(oFile)
                else:
                    aFiles.append([oFile])
            # We set the updated date to the value from the datapack, rather
            # than the current time, to protect against local clock issues
            # making things wierd.
            self.do_refresh_card_list(oCLDate, aFiles)
            # Saving immediately to ensure we record the update seems
            # the safest thing to do here, although it's different from
            # how we usually treat the config file.
            save_config(self.config_file)
