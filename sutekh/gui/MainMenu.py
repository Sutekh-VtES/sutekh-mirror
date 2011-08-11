# MainMenu.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Menu for the Main Application Window"""

import gtk
from sqlobject import sqlhub
from sutekh.gui.SutekhDialog import do_complaint_error
from sutekh.gui.SutekhFileWidget import ImportDialog
from sutekh.gui.GuiDBManagement import refresh_ww_card_list
from sutekh.gui.GuiCardSetFunctions import import_cs
from sutekh.gui.ProfileManagement import ProfileMngDlg
from sutekh.io.IdentifyXMLFile import IdentifyXMLFile
from sutekh.io.AbstractCardSetParser import AbstractCardSetParser
from sutekh.io.PhysicalCardParser import PhysicalCardParser
from sutekh.io.PhysicalCardSetParser import PhysicalCardSetParser
from sutekh.gui.SutekhMenu import SutekhMenu


class MainMenu(SutekhMenu):
    """The Main application Menu.

       This provides access to the major pane management actions, the
       global file actions, the help system, and any global plugins.
       """
    # pylint: disable-msg=R0904, R0902
    # R0904 - gtk.Widget, so many public methods
    # R0902 - We keep a lot of state here (menu's available, etc.)
    def __init__(self, oWindow, oConfig):
        super(MainMenu, self).__init__(oWindow)
        self.__oConfig = oConfig
        self.__create_file_menu()
        self.__create_pane_menu()
        self.__create_rulebook_menu()
        self.add_plugins_to_menus(oWindow)
        self.__create_help_menu()
        oWindow.add_to_menu_list("White Wolf Card List",
                self.physical_cl_set_sensitive)
        oWindow.add_to_menu_list("Card Set List",
                self.pcs_list_pane_set_sensitive)
        oWindow.add_to_menu_list("Card Text",
                self.add_card_text_set_sensitive)
        # enable mnemonics + accelerators for the main menu
        self.activate_accels()

    # pylint: disable-msg=W0201
    # these are called from __init__
    def __create_file_menu(self):
        """Create the File Menu"""
        oMenu = self.create_submenu(self, "_File")
        # items

        self.create_submenu(oMenu, 'Backup')
        oImport = self.create_submenu(oMenu, "Import Card Set")

        self.create_menu_item("Load Saved Card Set from File", oImport,
            self.do_import_card_set)

        oMenu.add(gtk.SeparatorMenuItem())

        oDownloadMenu = self.create_submenu(oMenu, 'Data Downloads')
        self.__add_download_menu(oDownloadMenu)

        oMenu.add(gtk.SeparatorMenuItem())

        oPrefsMenu = self.create_submenu(oMenu, 'Preferences')
        self.__add_prefs_menu(oPrefsMenu)

        self.create_menu_item('Manage Profiles', oMenu,
                self.do_manage_profiles)

        self.create_menu_item('Save Current Pane Set', oMenu,
                self.do_save_pane_set)

        self.create_menu_item('Restore saved configuration', oMenu,
                self.do_restore)

        oMenu.add(gtk.SeparatorMenuItem())

        self.create_menu_item("_Quit", oMenu,
                lambda iItem: self._oMainWindow.action_close(self._oMainWindow,
                    None))

    def __add_prefs_menu(self, oPrefsMenu):
        """Add the File Preferences menu"""
        self._dMenus["File Preferences"] = oPrefsMenu

        oNameDisplay = gtk.CheckMenuItem('Use "path of ..., the" name display')
        oNameDisplay.set_inconsistent(False)
        if self.__oConfig.get_postfix_the_display():
            oNameDisplay.set_active(True)
        else:
            oNameDisplay.set_active(False)
        oNameDisplay.connect('activate', self.do_postfix_the_display)
        oPrefsMenu.add(oNameDisplay)

        oSaveOnExit = gtk.CheckMenuItem('Save Pane Set on Exit')
        oSaveOnExit.set_inconsistent(False)
        if self.__oConfig.get_save_on_exit():
            oSaveOnExit.set_active(True)
        else:
            oSaveOnExit.set_active(False)
        oSaveOnExit.connect('activate', self.do_toggle_save_on_exit)
        oPrefsMenu.add(oSaveOnExit)

        oSavePos = gtk.CheckMenuItem('Save Exact Pane Positions')
        oSavePos.set_inconsistent(False)
        if self.__oConfig.get_save_precise_pos():
            oSavePos.set_active(True)
        else:
            oSavePos.set_active(False)
        oSavePos.connect('activate', self.do_toggle_save_precise_pos)
        oPrefsMenu.add(oSavePos)

        oSaveWinSize = gtk.CheckMenuItem('Save Window Size')
        oSaveWinSize.set_inconsistent(False)
        if self.__oConfig.get_save_window_size():
            oSaveWinSize.set_active(True)
        else:
            oSaveWinSize.set_active(False)
        oSaveOnExit.connect('activate', self.do_toggle_save_window_size)
        oPrefsMenu.add(oSaveWinSize)

    def __add_download_menu(self, oDownloadMenu):
        """Add the File Download menu"""
        if sqlhub.processConnection.uri() != "sqlite:///:memory:":
            # Need to have memory connection available for this
            self.create_menu_item("Import new White Wolf Card List and"
                    " rulings", oDownloadMenu, self.do_import_new_card_list)
        self.create_menu_item('Download VTES icons', oDownloadMenu,
                self.download_icons)

    def __create_pane_menu(self):
        """Create the 'Pane Actions' menu"""
        oMenu = self.create_submenu(self, '_Pane Actions')

        self.create_menu_item("Equalize _pane sizes", oMenu,
                self.equalize_panes, "<Ctrl>p")

        self.__oAddHorzPane = self.create_menu_item("Split current pane"
                " _horizontally (|)", oMenu, self.add_pane_horizontal)
        self.__oAddHorzPane.set_sensitive(False)

        self.__oAddVertPane = self.create_menu_item("Split current pane"
                " _vertically (-)", oMenu, self.add_pane_vertical)
        self.__oAddVertPane.set_sensitive(False)

        self._add_add_submenu(oMenu)
        self._add_replace_submenu(oMenu)

        oMenu.add(gtk.SeparatorMenuItem())

        self.__oDelPane = self.create_menu_item("_Remove current pane", oMenu,
                self._oMainWindow.menu_remove_frame, "<Ctrl>w")
        self.__oDelPane.set_sensitive(False)

    def _add_add_submenu(self, oMenuWidget):
        """Create a submenu for the add pane options"""
        oAddMenu = self.create_submenu(oMenuWidget, 'Add Pane')

        self.create_menu_item("Add New Blank Pane", oAddMenu,
                self._oMainWindow.add_pane_end)

        self.__oAddPCLPane = self.create_menu_item("Add White Wolf Card List",
                oAddMenu, self._oMainWindow.add_new_physical_card_list)
        self.__oAddPCLPane.set_sensitive(True)

        self.__oAddCardText = self.create_menu_item("Add Card Text Pane",
                oAddMenu, self._oMainWindow.add_new_card_text)
        self.__oAddCardText.set_sensitive(True)

        self.__oAddPCSListPane = self.create_menu_item("Add Card Set"
                " List", oAddMenu, self._oMainWindow.add_new_pcs_list)
        self.__oAddPCSListPane.set_sensitive(True)

    def _add_replace_submenu(self, oMenuWidget):
        """Create a submenu for the replace pane options"""
        self.__oReplaceMenu = self.create_submenu(oMenuWidget, 'Replace Pane')

        self.__oReplacePCLPane = self.create_menu_item("Replace current pane"
                " with White Wolf Card List", self.__oReplaceMenu,
                self._oMainWindow.replace_with_physical_card_list)
        self.__oReplacePCLPane.set_sensitive(True)

        self.__oReplaceCardText = self.create_menu_item("Replace current pane"
                " with Card Text Pane", self.__oReplaceMenu,
                self._oMainWindow.replace_with_card_text)
        self.__oReplaceCardText.set_sensitive(True)

        self.__oReplacePCSListPane = self.create_menu_item("Replace current"
                " pane with Card Set List", self.__oReplaceMenu,
                self._oMainWindow.replace_with_pcs_list)
        self.__oReplacePCSListPane.set_sensitive(True)

    def __create_rulebook_menu(self):
        """Create the menu for rulebook items"""
        # setup sub menu
        self.create_menu_item_with_submenu(self, "_Rulebook")

    def __create_help_menu(self):
        """Create the menu for help items"""
        # setup sub menu
        oMenuItem = self.create_menu_item_with_submenu(self, "_Help")
        oMenu = oMenuItem.get_submenu()
        oMenuItem.set_right_justified(True)

        self.create_menu_item("Sutekh Tutorial", oMenu, self.show_tutorial)
        self.create_menu_item("Sutekh Manual", oMenu, self.show_manual, 'F1')
        self.oHelpLast = self.create_menu_item("Last shown help page", oMenu,
                self._oMainWindow.show_last_help)
        self.oHelpLast.set_sensitive(False)
        self.create_menu_item("About Sutekh", oMenu,
                self._oMainWindow.show_about_dialog)

    # pylint: enable-msg=W0201

    def del_pane_set_sensitive(self, bValue):
        """Set the 'pane can be removed' option to bValue"""
        self.__oDelPane.set_sensitive(bValue)

    def replace_pane_set_sensitive(self, bValue):
        """Set the 'replace pane' option to bValue"""
        self.__oReplaceMenu.get_attach_widget().set_sensitive(bValue)

    def add_card_text_set_sensitive(self, bValue):
        """Set the options for adding the Card Text Frame to bValue"""
        self.__oReplaceCardText.set_sensitive(bValue)
        self.__oAddCardText.set_sensitive(bValue)

    def pcs_list_pane_set_sensitive(self, bValue):
        """Set the options for adding the list of PhysicalCardSets to bValue"""
        self.__oReplacePCSListPane.set_sensitive(bValue)
        self.__oAddPCSListPane.set_sensitive(bValue)

    def physical_cl_set_sensitive(self, bValue):
        """Set the options for adding the card collection to bValue"""
        self.__oReplacePCLPane.set_sensitive(bValue)
        self.__oAddPCLPane.set_sensitive(bValue)

    def set_split_vertical_active(self, bValue):
        """Set the split vertical pane option to bValue"""
        self.__oAddVertPane.set_sensitive(bValue)

    def set_split_horizontal_active(self, bValue):
        """Set the split horizontal pane option to bValue"""
        self.__oAddHorzPane.set_sensitive(bValue)

    def show_tutorial(self, oMenuWidget):
        """Show the Sutekh Tutorial"""
        self._oMainWindow.show_tutorial(oMenuWidget, self.oHelpLast)

    def show_manual(self, oMenuWidget):
        """Show the Sutekh Tutorial"""
        self._oMainWindow.show_manual(oMenuWidget, self.oHelpLast)

    def do_import_card_set(self, _oWidget):
        """Import a card set from a XML File."""
        oFileChooser = ImportDialog("Select Card Set(s) to Import",
                self._oMainWindow)
        oFileChooser.add_filter_with_pattern('XML Files', ['*.xml'])
        oFileChooser.run()
        sFileName = oFileChooser.get_name()
        if sFileName is not None:
            oIdParser = IdentifyXMLFile()
            oIdParser.id_file(sFileName)
            if oIdParser.type == 'PhysicalCardSet' or \
                    oIdParser.type == 'AbstractCardSet' or \
                    oIdParser.type == 'PhysicalCard':
                fIn = file(sFileName, 'rU')
                if oIdParser.type == "AbstractCardSet":
                    oParser = AbstractCardSetParser()
                elif oIdParser.type == 'PhysicalCardSet':
                    oParser = PhysicalCardSetParser()
                else:
                    # Old style PhysicalCard list
                    oParser = PhysicalCardParser()
                import_cs(fIn, oParser, self._oMainWindow)
            else:
                do_complaint_error("File is not a CardSet XML File.")

    def do_import_new_card_list(self, _oWidget):
        """Refresh the WW card list and rulings files."""
        if refresh_ww_card_list(self._oMainWindow):
            self._oMainWindow.reload_all()

    def do_postfix_the_display(self, _oWidget):
        """Save the current pane layout"""
        bChoice = not self.__oConfig.get_postfix_the_display()
        self.__oConfig.set_postfix_the_display(bChoice)

    def do_manage_profiles(self, _oWidget):
        """Display the Profile management dialog"""
        oDlg = ProfileMngDlg(self._oMainWindow, self.__oConfig)
        oDlg.run()
        oDlg.destroy()

    def do_save_pane_set(self, _oWidget):
        """Save the current pane layout"""
        self._oMainWindow.save_frames()

    def do_toggle_save_on_exit(self, _oWidget):
        """Toggle the 'Save Pane layout on exit' option"""
        bChoice = not self.__oConfig.get_save_on_exit()
        self.__oConfig.set_save_on_exit(bChoice)
        # gtk can handle the rest for us

    def do_toggle_save_precise_pos(self, _oWidget):
        """Toggle save precise pane positions option"""
        bChoice = not self.__oConfig.get_save_precise_pos()
        self.__oConfig.set_save_precise_pos(bChoice)

    def do_toggle_save_window_size(self, _oWidget):
        """Toggle save window size option"""
        bChoice = not self.__oConfig.get_save_window_size()
        self.__oConfig.set_save_window_size(bChoice)

    def equalize_panes(self, _oWidget):
        """Ensure all panes have the same width allocated."""
        self._oMainWindow.set_all_panes_equal()

    def add_pane_horizontal(self, _oWidget):
        """Split the current pane horizontally and add a new pane."""
        self._oMainWindow.add_pane(False)

    def add_pane_vertical(self, _oWidget):
        """Split the current pane vertically and add a new pane."""
        self._oMainWindow.add_pane(True)

    def do_restore(self, _oWidget):
        """Restore the pane layout from the config file."""
        self._oMainWindow.restore_from_config()

    def download_icons(self, _oWidget):
        """Call on the icon manager to download the icons."""
        self._oMainWindow.icon_manager.download_icons()
