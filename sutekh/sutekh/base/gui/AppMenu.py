# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Menu for the Main Application Window"""

from gi.repository import Gtk
from .ProfileManagement import ProfileMngDlg
from .SutekhMenu import SutekhMenu
from .SutekhFileWidget import ImportDialog
from .GuiCardSetFunctions import import_cs
from .SutekhDialog import do_complaint_error

from ..Utility import is_memory_db


class AppMenu(SutekhMenu):
    """Base class for the Main application Menu.

       This provides access to the major pane management actions, the
       global file actions, the help system, and any global plugins.
       """
    # pylint: disable=too-many-public-methods, too-many-instance-attributes
    # Gtk.Widget, so many public methods
    # We keep a lot of state here (menu's available, etc.)
    def __init__(self, oWindow, oConfig):
        super().__init__(oWindow)
        self._oConfig = oConfig
        self._create_file_menu()
        self._create_pane_menu()
        self._create_rulebook_menu()
        self.add_plugins_to_menus(oWindow)
        self._create_help_menu()
        oWindow.add_to_menu_list("Full Card List",
                                 self.physical_cl_set_sensitive)
        oWindow.add_to_menu_list("Card Set List",
                                 self.pcs_list_pane_set_sensitive)
        oWindow.add_to_menu_list("Card Text",
                                 self.add_card_text_set_sensitive)
        oWindow.add_to_menu_list("Log View Frame",
                                 self.add_log_pane_set_sensitive)
        # enable mnemonics + accelerators for the main menu
        self.activate_accels()

        # subclasses need to provide this
        self.cIdentifyFile = None

    # pylint: disable=attribute-defined-outside-init
    # these are called from __init__
    def _create_file_menu(self):
        """Create the File Menu"""
        oMenu = self.create_submenu(self, "_File")
        # items

        self.create_submenu(oMenu, 'Backup')
        oImport = self.create_submenu(oMenu, "Import Card Set")

        self.create_menu_item("Load Saved Card Set from File", oImport,
                              self.do_import_card_set)

        oMenu.add(Gtk.SeparatorMenuItem())

        oDownloadMenu = self.create_submenu(oMenu, 'Data Downloads')
        self._add_download_menu(oDownloadMenu)

        oMenu.add(Gtk.SeparatorMenuItem())

        oPrefsMenu = self.create_submenu(oMenu, 'Preferences')
        self._add_prefs_menu(oPrefsMenu)

        self.create_menu_item('Manage Profiles', oMenu,
                              self.do_manage_profiles)

        self.create_menu_item('Save Current Pane Set', oMenu,
                              self.do_save_pane_set)

        self.create_menu_item('Restore saved configuration', oMenu,
                              self.do_restore)

        oMenu.add(Gtk.SeparatorMenuItem())

        self.create_menu_item(
            "_Quit", oMenu,
            lambda iItem: self._oMainWindow.action_close(self._oMainWindow,
                                                         None))

    def _add_prefs_menu(self, oPrefsMenu):
        """Add the File Preferences menu"""
        self._dMenus["File Preferences"] = oPrefsMenu

        oCheckForUpdates = Gtk.CheckMenuItem(label='Check for Cardlist updates'
                                             ' on startup')
        oCheckForUpdates.set_inconsistent(False)
        if self._oConfig.get_check_for_updates():
            oCheckForUpdates.set_active(True)
        else:
            oCheckForUpdates.set_active(False)
        oCheckForUpdates.connect('activate', self.do_toggle_check_for_updates)
        oPrefsMenu.add(oCheckForUpdates)

        oNameDisplay = Gtk.CheckMenuItem(
            label='Use "something ..., the" name display')
        oNameDisplay.set_inconsistent(False)
        if self._oConfig.get_postfix_the_display():
            oNameDisplay.set_active(True)
        else:
            oNameDisplay.set_active(False)
        oNameDisplay.connect('activate', self.do_postfix_the_display)
        oPrefsMenu.add(oNameDisplay)

        oSaveOnExit = Gtk.CheckMenuItem(label='Save Pane Set on Exit')
        oSaveOnExit.set_inconsistent(False)
        if self._oConfig.get_save_on_exit():
            oSaveOnExit.set_active(True)
        else:
            oSaveOnExit.set_active(False)
        oSaveOnExit.connect('activate', self.do_toggle_save_on_exit)
        oPrefsMenu.add(oSaveOnExit)

        oSavePos = Gtk.CheckMenuItem(label='Save Exact Pane Positions')
        oSavePos.set_inconsistent(False)
        if self._oConfig.get_save_precise_pos():
            oSavePos.set_active(True)
        else:
            oSavePos.set_active(False)
        oSavePos.connect('activate', self.do_toggle_save_precise_pos)
        oPrefsMenu.add(oSavePos)

        oSaveWinSize = Gtk.CheckMenuItem(label='Save Window Size')
        oSaveWinSize.set_inconsistent(False)
        if self._oConfig.get_save_window_size():
            oSaveWinSize.set_active(True)
        else:
            oSaveWinSize.set_active(False)
        oSaveOnExit.connect('activate', self.do_toggle_save_window_size)
        oPrefsMenu.add(oSaveWinSize)

    def _add_download_menu(self, oDownloadMenu):
        """Add the File Download menu"""
        oImportItem = self.create_menu_item(
            "Import new Full Card List and rulings",
            oDownloadMenu, self.do_import_new_card_list)
        # Need to have memory connection available for this
        if is_memory_db():
            oImportItem.set_sensitive(False)

    def _create_pane_menu(self):
        """Create the 'Pane Actions' menu"""
        oMenu = self.create_submenu(self, '_Pane Actions')

        self.create_menu_item("Equalize _pane sizes", oMenu,
                              self.equalize_panes, "<Ctrl>p")

        self._oAddHorzPane = self.create_menu_item(
            "Split current pane _horizontally (|)", oMenu,
            self.add_pane_horizontal)
        self._oAddHorzPane.set_sensitive(False)

        self._oAddVertPane = self.create_menu_item(
            "Split current pane _vertically (-)", oMenu,
            self.add_pane_vertical)
        self._oAddVertPane.set_sensitive(False)

        self._add_add_submenu(oMenu)
        self._add_replace_submenu(oMenu)

        oMenu.add(Gtk.SeparatorMenuItem())

        self._oDelPane = self.create_menu_item(
            "_Remove current pane", oMenu,
            self._oMainWindow.menu_remove_frame, "<Ctrl>w")
        self._oDelPane.set_sensitive(False)

    def _add_add_submenu(self, oMenuWidget):
        """Create a submenu for the add pane options"""
        oAddMenu = self.create_submenu(oMenuWidget, 'Add Pane')

        self.create_menu_item("Add New Blank Pane", oAddMenu,
                              self._oMainWindow.add_pane_end)

        self._oAddPCLPane = self.create_menu_item(
            "Add Full Card List", oAddMenu,
            self._oMainWindow.add_new_physical_card_list)
        self._oAddPCLPane.set_sensitive(True)

        self._oAddCardText = self.create_menu_item(
            "Add Card Text Pane", oAddMenu,
            self._oMainWindow.add_new_card_text)
        self._oAddCardText.set_sensitive(True)

        self._oAddPCSListPane = self.create_menu_item(
            "Add Card Set List", oAddMenu,
            self._oMainWindow.add_new_pcs_list)
        self._oAddPCSListPane.set_sensitive(True)

        self._oAddLogPane = self.create_menu_item(
            "Add Log Message Pane", oAddMenu,
            self._oMainWindow.add_new_log_view_frame)
        self._oAddLogPane.set_sensitive(True)

    def _add_replace_submenu(self, oMenuWidget):
        """Create a submenu for the replace pane options"""
        self._oReplaceMenu = self.create_submenu(oMenuWidget, 'Replace Pane')

        self._oReplacePCLPane = self.create_menu_item(
            "Replace current pane with Full Card List", self._oReplaceMenu,
            self._oMainWindow.replace_with_physical_card_list)
        self._oReplacePCLPane.set_sensitive(True)

        self._oReplaceCardText = self.create_menu_item(
            "Replace current pane with Card Text Pane", self._oReplaceMenu,
            self._oMainWindow.replace_with_card_text)
        self._oReplaceCardText.set_sensitive(True)

        self._oReplacePCSListPane = self.create_menu_item(
            "Replace current pane with Card Set List", self._oReplaceMenu,
            self._oMainWindow.replace_with_pcs_list)
        self._oReplacePCSListPane.set_sensitive(True)

        self._oReplaceLogPane = self.create_menu_item(
            "Replace current pane with Log Message Pane", self._oReplaceMenu,
            self._oMainWindow.replace_with_log_view_frame)
        self._oReplaceLogPane.set_sensitive(True)

    def _create_rulebook_menu(self):
        """Create the menu for rulebook items"""
        # setup sub menu
        self.create_menu_item_with_submenu(self, "_Rulebook")

    def _create_help_menu(self):
        """Create the menu for help items"""
        # setup sub menu
        oMenuItem = self.create_menu_item_with_submenu(self, "_Help")
        oMenu = oMenuItem.get_submenu()
        oMenuItem.set_right_justified(True)
        self._add_help_items(oMenu)
        # Add filter help menu items
        self.create_menu_item("Card Filter Help", oMenu,
                              self.show_card_filter_help)
        self.create_menu_item("Card Set Filter Help", oMenu,
                              self.show_card_set_filter_help)
        self.oHelpLast = self.create_menu_item(
            "Last shown help page", oMenu, self._oMainWindow.show_last_help)
        self.oHelpLast.set_sensitive(False)
        oMenu.add(Gtk.SeparatorMenuItem())
        self._add_about_dialog(oMenu)

    def _add_help_items(self, oHelpMenu):
        """Hook for adding the help items"""
        # Subclasses should provide this
        raise NotImplementedError

    def _add_about_dialog(self, oHelpMenu):
        """Hook for adding about and other dialogs to the help menu"""
        # Subclasses should provide this
        raise NotImplementedError

    def set_show_last_help(self):
        """Make the 'Last shown help page' option active"""
        self.oHelpLast.set_sensitive(True)

    # pylint: enable=attribute-defined-outside-init

    def del_pane_set_sensitive(self, bValue):
        """Set the 'pane can be removed' option to bValue"""
        self._oDelPane.set_sensitive(bValue)

    def replace_pane_set_sensitive(self, bValue):
        """Set the 'replace pane' option to bValue"""
        self._oReplaceMenu.get_attach_widget().set_sensitive(bValue)

    def add_card_text_set_sensitive(self, bValue):
        """Set the options for adding the Card Text Frame to bValue"""
        self._oReplaceCardText.set_sensitive(bValue)
        self._oAddCardText.set_sensitive(bValue)

    def pcs_list_pane_set_sensitive(self, bValue):
        """Set the options for adding the list of PhysicalCardSets to bValue"""
        self._oReplacePCSListPane.set_sensitive(bValue)
        self._oAddPCSListPane.set_sensitive(bValue)

    def physical_cl_set_sensitive(self, bValue):
        """Set the options for adding the card collection to bValue"""
        self._oReplacePCLPane.set_sensitive(bValue)
        self._oAddPCLPane.set_sensitive(bValue)

    def add_log_pane_set_sensitive(self, bValue):
        """Set the options for adding the list of PhysicalCardSets to bValue"""
        self._oAddLogPane.set_sensitive(bValue)
        self._oReplaceLogPane.set_sensitive(bValue)

    def set_split_vertical_active(self, bValue):
        """Set the split vertical pane option to bValue"""
        self._oAddVertPane.set_sensitive(bValue)

    def set_split_horizontal_active(self, bValue):
        """Set the split horizontal pane option to bValue"""
        self._oAddHorzPane.set_sensitive(bValue)

    def do_import_card_set(self, _oWidget):
        """Import a card set from a XML File."""
        oFileChooser = ImportDialog("Select Card Set(s) to Import",
                                    self._oMainWindow)
        oFileChooser.add_filter_with_pattern('XML Files', ['*.xml'])
        oFileChooser.run()
        sFileName = oFileChooser.get_name()
        if sFileName is not None:
            # pylint: disable=not-callable
            # subclasses will provide a callable cIdentifyFile
            oIdParser = self.cIdentifyFile()
            # pylint: enable=not-callable
            oIdParser.id_file(sFileName)
            if oIdParser.can_parse():
                fIn = open(sFileName, 'r')
                oParser = oIdParser.get_parser()
                import_cs(fIn, oParser, self._oMainWindow)
            else:
                do_complaint_error("File is not a CardSet XML File.")

    def do_import_new_card_list(self, _oWidget):
        """Refresh the full card list and rulings files."""
        if self._oMainWindow.do_refresh_card_list():
            self._oMainWindow.reload_all()

    def do_postfix_the_display(self, _oWidget):
        """Save the current pane layout"""
        bChoice = not self._oConfig.get_postfix_the_display()
        self._oConfig.set_postfix_the_display(bChoice)

    def do_manage_profiles(self, _oWidget):
        """Display the Profile management dialog"""
        oDlg = ProfileMngDlg(self._oMainWindow, self._oConfig)
        oDlg.run()
        oDlg.destroy()

    def do_save_pane_set(self, _oWidget):
        """Save the current pane layout"""
        self._oMainWindow.save_frames()

    def do_toggle_save_on_exit(self, _oWidget):
        """Toggle the 'Save Pane layout on exit' option"""
        bChoice = not self._oConfig.get_save_on_exit()
        self._oConfig.set_save_on_exit(bChoice)
        # Gtk can handle the rest for us

    def do_toggle_check_for_updates(self, _oWidget):
        """Toggle the 'Check for Updates on startup' option"""
        bChoice = not self._oConfig.get_check_for_updates()
        self._oConfig.set_check_for_updates(bChoice)

    def do_toggle_save_precise_pos(self, _oWidget):
        """Toggle save precise pane positions option"""
        bChoice = not self._oConfig.get_save_precise_pos()
        self._oConfig.set_save_precise_pos(bChoice)

    def do_toggle_save_window_size(self, _oWidget):
        """Toggle save window size option"""
        bChoice = not self._oConfig.get_save_window_size()
        self._oConfig.set_save_window_size(bChoice)

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

    def show_card_filter_help(self, _oMenuWidget):
        """Show the card filter help"""
        self._oMainWindow.show_card_filter_help()

    def show_card_set_filter_help(self, _oMenuWidget):
        """Show the card set filter help"""
        self._oMainWindow.show_card_set_filter_help()
