# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Handle the multi pane UI for Sutkeh
# Copyright 2007, 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - See COPYING for details

"""Main window for Sutekh."""

import logging
import datetime

from gi.repository import Gtk

from sqlobject import SQLObjectNotFound

from sutekh.base.core.BaseAdapters import IAbstractCard
from sutekh.base.core.DBUtility import (CARDLIST_UPDATE_DATE, flush_cache,
                                        get_metadata_date)

from sutekh.base.gui.AppMainWindow import AppMainWindow
from sutekh.base.gui.GuiDataPack import gui_error_handler
from sutekh.base.gui.SutekhDialog import do_complaint
from sutekh.base.gui.UpdateDialog import UpdateDialog

from sutekh.core.SutekhObjectCache import SutekhObjectCache

from sutekh.io.PhysicalCardSetWriter import PhysicalCardSetWriter
from sutekh.io.WwUrls import WW_CARDLIST_DATAPACK
from sutekh.io.DataPack import find_all_data_packs

from sutekh.gui.AboutDialog import SutekhAboutDialog
from sutekh.gui.MainMenu import MainMenu
from sutekh.gui.PluginManager import PluginManager
from sutekh.gui.GuiDBManagement import GuiDBManager
from sutekh.gui import SutekhIcon
from sutekh.gui.GuiIconManager import GuiIconManager
from sutekh.gui.CardTextFrame import CardTextFrame


class SutekhMainWindow(AppMainWindow):
    """Window that has a configurable number of panes."""
    # pylint: disable=too-many-public-methods, too-many-instance-attributes
    # Gtk.Widget, so many public methods
    # we need to keep a lot of state, so many instance attributes
    def __init__(self):
        super().__init__()
        self._cPCSWriter = PhysicalCardSetWriter
        self._sResourceName = 'sutekh'
        # We can shrink the window quite small
        self.set_size_request(100, 100)
        # But we start at a reasonable size
        self.set_default_size(800, 600)

        self._cDBManager = GuiDBManager

        # Set Default Window Icon for all Windows
        Gtk.Window.set_default_icon(SutekhIcon.SUTEKH_ICON)

        # Sutekh lookup cache
        self.__oSutekhObjectCache = None

    def _verify_database(self):
        """Check that the database is correctly populated"""
        try:
            _oCard = IAbstractCard('Ossian')
        except SQLObjectNotFound:
            # Log error so verbose picks it up
            logging.warning('Ossian not found in the database')
            # Inform the user
            iResponse = do_complaint(
                'Database is missing cards. Try import the cardlist now?',
                Gtk.MessageType.ERROR, Gtk.ButtonsType.YES_NO, False)
            if iResponse == Gtk.ResponseType.YES:
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
        super().update_to_new_db()

    def clear_cache(self):
        """Remove the cached set of objects, for card list reloads, etc."""
        del self.__oSutekhObjectCache

    # pylint: disable=no-self-use
    # convienent to have this as a method
    def show_about_dialog(self, _oWidget):
        """Display the about dialog"""
        oDlg = SutekhAboutDialog()
        oDlg.run()
        oDlg.destroy()

    # pylint: enable=no-self-use

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
        oLastDate = get_metadata_date(CARDLIST_UPDATE_DATE)
        if oLastDate is None or oLastDate < oCLDate:
            # There has been a cardlist update, so query the user
            oDlg = UpdateDialog(["CardList and Rulings"])
            iResponse = oDlg.run()
            oDlg.destroy()
            if iResponse != Gtk.ResponseType.OK:
                return
            self.do_refresh_from_zip_url(oCLDate, aUrls[0], aHashes[0])
