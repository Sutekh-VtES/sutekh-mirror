# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Menu for the Main Application Window"""

from sutekh.io.IdentifyXMLFile import IdentifyXMLFile
from sutekh.base.gui.AppMenu import AppMenu


class MainMenu(AppMenu):
    """The Main application Menu.

       Extends AppMenu with the various sutekh specific options.
       """
    # pylint: disable=R0904, R0902
    # R0904 - gtk.Widget, so many public methods
    # R0902 - We keep a lot of state here (menu's available, etc.)
    def __init__(self, oWindow, oConfig):
        super(MainMenu, self).__init__(oWindow, oConfig)
        self.cIdentifyFile = IdentifyXMLFile

    def _add_download_menu(self, oDownloadMenu):
        """Extend the File Download menu"""
        super(MainMenu, self)._add_download_menu(oDownloadMenu)
        self.create_menu_item('Check for updated cardlist', oDownloadMenu,
                              self.check_updated_cardlist)
        self.create_menu_item('Download VTES icons', oDownloadMenu,
                              self.download_icons)

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
