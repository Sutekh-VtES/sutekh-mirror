# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Menu for the Main Application Window"""

from gi.repository import Gtk

from sutekh.io.IdentifyXMLFile import IdentifyXMLFile
from sutekh.base.gui.AppMenu import AppMenu

from sutekh.base.Utility import is_memory_db


class MainMenu(AppMenu):
    """The Main application Menu.

       Extends AppMenu with the various sutekh specific options.
       """
    # pylint: disable=too-many-public-methods, too-many-instance-attributes
    # Gtk.Widget, so many public methods
    # We keep a lot of state here (menu's available, etc.)
    def __init__(self, oWindow, oConfig):
        super().__init__(oWindow, oConfig)
        self.cIdentifyFile = IdentifyXMLFile

    def _add_download_menu(self, oDownloadMenu):
        """Extend the File Download menu"""
        super()._add_download_menu(oDownloadMenu)
        oCheckItem = self.create_menu_item('Check for updated cardlist',
                                           oDownloadMenu,
                                           self.check_updated_cardlist)
        if is_memory_db():
            # Need to have memory connection available for this
            oCheckItem.set_sensitive(False)
        self.create_menu_item('Download VTES icons', oDownloadMenu,
                              self.download_icons)

    def _add_prefs_menu(self, oPrefsMenu):
        """Extend the Preferences menu"""
        super()._add_prefs_menu(oPrefsMenu)
        oShowErrata = Gtk.CheckMenuItem(
            label='Show Errata Markers')
        oShowErrata.set_inconsistent(False)
        if self._oConfig.get_show_errata_markers():
            oShowErrata.set_active(True)
        else:
            oShowErrata.set_active(False)
        oShowErrata.connect('activate', self.do_show_errata)
        oPrefsMenu.add(oShowErrata)

    def _add_help_items(self, oHelpMenu):
        """Create the menu for help items"""
        # setup sub menu
        self.create_menu_item("Sutekh Tutorial", oHelpMenu,
                              self.show_tutorial)
        self.create_menu_item("Sutekh Manual", oHelpMenu,
                              self.show_manual, 'F1')

    def _add_about_dialog(self, oHelpMenu):
        """Add about dialog entry with the correct name"""
        self.create_menu_item("About Sutekh", oHelpMenu,
                              self._oMainWindow.show_about_dialog)

    def show_tutorial(self, _oMenuWidget):
        """Show the Sutekh Tutorial"""
        self._oMainWindow.show_tutorial()

    def show_manual(self, _oMenuWidget):
        """Show the Sutekh Tutorial"""
        self._oMainWindow.show_manual()

    def download_icons(self, _oWidget):
        """Call on the icon manager to download the icons."""
        self._oMainWindow.icon_manager.download_with_progress()

    def check_updated_cardlist(self, _oWidget):
        """Check for an updated cardlist datapack."""
        self._oMainWindow.check_updated_cardlist()

    def do_show_errata(self, _oWidget):
        """Save the current pane layout"""
        bChoice = not self._oConfig.get_show_errata_markers()
        self._oConfig.set_show_errata_markers(bChoice)
