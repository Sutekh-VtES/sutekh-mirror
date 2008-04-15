# MainMenu.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Menu for the Main Application Window"""

import gtk
from sqlobject import sqlhub
from sutekh.core.CardLookup import LookupFailed
from sutekh.gui.SutekhDialog import do_complaint_error, do_complaint_warning
from sutekh.gui.ImportDialog import ImportDialog
from sutekh.gui.GuiDBManagement import refresh_ww_card_list
from sutekh.io.XmlFileHandling import PhysicalCardXmlFile, \
        PhysicalCardSetXmlFile, AbstractCardSetXmlFile
from sutekh.io.IdentifyXMLFile import IdentifyXMLFile
from sutekh.SutekhUtility import delete_physical_card_set, \
        delete_abstract_card_set

class MainMenu(gtk.MenuBar, object):
    """The Main application Menu.

       This provides access to the major pane management actions, the
       global file actions, the help system, and any global plugins.
       """
    # pylint: disable-msg=R0904, R0902
    # R0904 - gtk.Widget, so many public methods
    # R0902 - We keep a lot of state here (menu's available, etc.)
    def __init__(self, oWindow, oConfig):
        super(MainMenu, self).__init__()
        self.__oWin = oWindow
        self.__dMenus = {}
        self._oAccelGroup = gtk.AccelGroup()
        self.__oWin.add_accel_group(self._oAccelGroup)
        self.__oConfig = oConfig
        self.__create_file_menu()
        self.__create_pane_menu()
        self.__create_plugin_menu()
        self.__create_help_menu()
        oWindow.add_to_menu_list("My Collection",
                self.physical_cl_set_sensitive)
        oWindow.add_to_menu_list("White Wolf Card List",
                self.abstract_cl_set_sensitive)
        oWindow.add_to_menu_list("Physical Card Set List",
                self.pcs_list_pane_set_sensitive)
        oWindow.add_to_menu_list("Abstract Card Set List",
                self.acs_list_pane_set_sensitive)
        oWindow.add_to_menu_list("Card Text",
                self.add_card_text_set_sensitive)

    # pylint: disable-msg=W0201
    # these are called from __init__
    def __create_file_menu(self):
        """Create the File Menu"""
        # setup sub menu
        oMenuItem = gtk.MenuItem("_File")
        oMenu = gtk.Menu()
        self.__dMenus["File"] = oMenu
        oMenuItem.set_submenu(oMenu)

        # items
        oImportPhysical = gtk.MenuItem("Import Collection from File")
        oImportPhysical.connect('activate', self.do_import_physical_card_list)
        oMenu.add(oImportPhysical)

        oImportCardSet = gtk.MenuItem("Import Card Set from File")
        oImportCardSet.connect('activate', self.do_import_card_set)
        oMenu.add(oImportCardSet)

        oMenu.add(gtk.SeparatorMenuItem())

        if sqlhub.processConnection.uri() != "sqlite:///:memory:":
            # Need to have memory connection available for this
            oImportNewCardList = gtk.MenuItem(
                    "Import new White Wolf Card List and rulings")
            oImportNewCardList.connect('activate',
                    self.do_import_new_card_list)
            oMenu.add(oImportNewCardList)
            oMenu.add(gtk.SeparatorMenuItem())

        oPrefsMenu = gtk.Menu()
        oPrefsItem = gtk.MenuItem('Preferences')
        oPrefsItem.set_submenu(oPrefsMenu)
        oMenu.add(oPrefsItem)

        self.__add_prefs_menu(oPrefsMenu)

        oRestoreConfig = gtk.MenuItem('Restore saved configuration')
        oMenu.add(oRestoreConfig)
        oRestoreConfig.connect('activate', self.do_restore)

        oMenu.add(gtk.SeparatorMenuItem())

        oQuit = gtk.MenuItem("_Quit")
        oQuit.connect('activate',
                lambda iItem: self.__oWin.action_quit(self.__oWin))

        oMenu.add(oQuit)

        self.add(oMenuItem)

    def __add_prefs_menu(self, oPrefsMenu):
        """Add the File Preferences menu"""
        self.__dMenus["File Preferences"] = oPrefsMenu
        oSavePanes = gtk.MenuItem('Save Current Pane Set')
        oSavePanes.connect('activate', self.do_save_pane_set)
        oPrefsMenu.add(oSavePanes)

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

    def __create_pane_menu(self):
        """Create the 'Pane Actions' menu"""
        oMenuItem = gtk.MenuItem("Pane _Actions")
        oMenu = gtk.Menu()
        self.__dMenus["Pane"] = oMenu
        oMenuItem.set_submenu(oMenu)

        oEqualizePanes = gtk.MenuItem("Equalize pane sizes")
        oMenu.add(oEqualizePanes)
        oEqualizePanes.connect("activate", self.equalize_panes)

        self.__oAddHorzPane = gtk.MenuItem("Split current pane _horizontally"
                " (|)")
        oMenu.add(self.__oAddHorzPane)
        self.__oAddHorzPane.connect("activate", self.add_pane_horizontal)
        self.__oAddHorzPane.set_sensitive(False)

        self.__oAddVertPane = gtk.MenuItem("Split current pane _vertically"
                " (-)")
        oMenu.add(self.__oAddVertPane)
        self.__oAddVertPane.connect("activate", self.add_pane_vertical)
        self.__oAddVertPane.set_sensitive(False)

        self._add_add_submenu(oMenu)
        self._add_replace_submenu(oMenu)

        oMenu.add(gtk.SeparatorMenuItem())

        self.__oDelPane = gtk.MenuItem("_Remove current pane")
        oMenu.add(self.__oDelPane)
        self.__oDelPane.connect("activate", self.__oWin.menu_remove_frame)
        self.__oDelPane.set_sensitive(False)

        self.add(oMenuItem)

    def _add_add_submenu(self, oMenuWidget):
        """Create a submenu for the add pane options"""
        oAddMenu = gtk.Menu()
        oAddMenuItem = gtk.MenuItem('Add New Pane')
        self.__dMenus["Add Pane"] = oAddMenu
        oAddMenuItem.set_submenu(oAddMenu)
        oMenuWidget.add(oAddMenuItem)


        oAddNewPane = gtk.MenuItem(
                "Add New Blank Pane")
        oAddMenu.add(oAddNewPane)
        oAddNewPane.connect("activate",
                self.__oWin.add_pane_end)

        self.__oAddACLPane = gtk.MenuItem(
                "Add White Wolf Card List")
        oAddMenu.add(self.__oAddACLPane)
        self.__oAddACLPane.connect("activate",
                self.__oWin.add_new_abstract_card_list)
        self.__oAddACLPane.set_sensitive(True)

        self.__oAddPCLPane = gtk.MenuItem(
                "Add My Collection List")
        oAddMenu.add(self.__oAddPCLPane)
        self.__oAddPCLPane.connect("activate",
                self.__oWin.add_new_physical_card_list)
        self.__oAddPCLPane.set_sensitive(True)

        self.__oAddCardText = gtk.MenuItem(
                "Add Card Text Pane")
        oAddMenu.add(self.__oAddCardText)
        self.__oAddCardText.connect("activate",
                self.__oWin.add_new_card_text)
        self.__oAddCardText.set_sensitive(True)

        self.__oAddACSListPane = gtk.MenuItem(
                "Add Abstract Card Set List")
        oAddMenu.add(self.__oAddACSListPane)
        self.__oAddACSListPane.connect("activate",
                self.__oWin.add_new_acs_list)
        self.__oAddACSListPane.set_sensitive(True)

        self.__oAddPCSListPane = gtk.MenuItem(
                "Add Physical Card Set List")
        oAddMenu.add(self.__oAddPCSListPane)
        self.__oAddPCSListPane.connect("activate",
                self.__oWin.add_new_pcs_list)
        self.__oAddPCSListPane.set_sensitive(True)

    def _add_replace_submenu(self, oMenuWidget):
        """Create a submenu for the replace pane options"""
        oReplaceMenu = gtk.Menu()
        oReplaceMenuItem = gtk.MenuItem('Replace Pane')
        self.__dMenus["Replace Pane"] = oReplaceMenu
        oReplaceMenuItem.set_submenu(oReplaceMenu)
        oMenuWidget.add(oReplaceMenuItem)

        self.__oReplaceACLPane = gtk.MenuItem(
                "Replace current pane with White Wolf Card List")
        oReplaceMenu.add(self.__oReplaceACLPane)
        self.__oReplaceACLPane.connect("activate",
                self.__oWin.replace_with_abstract_card_list)
        self.__oReplaceACLPane.set_sensitive(True)

        self.__oReplacePCLPane = gtk.MenuItem(
                "Replace current pane with My Collection List")
        oReplaceMenu.add(self.__oReplacePCLPane)
        self.__oReplacePCLPane.connect("activate",
                self.__oWin.replace_with_physical_card_list)
        self.__oReplacePCLPane.set_sensitive(True)

        self.__oReplaceCardText = gtk.MenuItem(
                "Replace current pane with Card Text Pane")
        oReplaceMenu.add(self.__oReplaceCardText)
        self.__oReplaceCardText.connect("activate",
                self.__oWin.replace_with_card_text)
        self.__oReplaceCardText.set_sensitive(True)

        self.__oReplaceACSListPane = gtk.MenuItem(
                "Replace current pane with Abstract Card Set List")
        oReplaceMenu.add(self.__oReplaceACSListPane)
        self.__oReplaceACSListPane.connect("activate",
                self.__oWin.replace_with_acs_list)
        self.__oReplaceACSListPane.set_sensitive(True)

        self.__oReplacePCSListPane = gtk.MenuItem(
                "Replace current pane with Physical Card Set List")
        oReplaceMenu.add(self.__oReplacePCSListPane)
        self.__oReplacePCSListPane.connect("activate",
                self.__oWin.replace_with_pcs_list)
        self.__oReplacePCSListPane.set_sensitive(True)

    def __create_plugin_menu(self):
        """Create the 'Plugins' menu"""
        # setup sub menu
        oMenuItem = gtk.MenuItem("Plugins")
        oMenu = gtk.Menu()
        self.__dMenus["Plugins"] = oMenu
        # plugins
        for oPlugin in self.__oWin.plugins:
            oPlugin.add_to_menu(self.__dMenus, oMenu)
        oMenuItem.set_submenu(oMenu)
        self.add(oMenuItem)
        if len(oMenu.get_children()) == 0:
            oMenuItem.set_sensitive(False)

    def __create_help_menu(self):
        """Create the menu for help items"""
        # setup sub menu
        oMenuItem = gtk.MenuItem("_Help")
        oMenuItem.set_right_justified(True)
        oMenu = gtk.Menu()
        self.__dMenus["Help"] = oMenu
        oMenuItem.set_submenu(oMenu)

        self.oHelpLast = gtk.MenuItem("Last shown help page")

        self.oHelpTutorial = gtk.MenuItem("Sutekh Tutorial")
        self.oHelpTutorial.connect('activate', self.__oWin.show_tutorial,
                self.oHelpLast)
        oMenu.add(self.oHelpTutorial)
        self.oHelpManual = gtk.MenuItem("Sutekh Manual")
        self.oHelpManual.connect('activate', self.__oWin.show_manual,
                self.oHelpLast)
        oMenu.add(self.oHelpManual)
        self.oHelpManual.add_accelerator('activate', self._oAccelGroup,
                gtk.gdk.keyval_from_name('F1'), 0, gtk.ACCEL_VISIBLE)

        self.oHelpLast.connect('activate', self.__oWin.show_last_help)
        oMenu.add(self.oHelpLast)
        self.oHelpLast.set_sensitive(False)

        self.oAbout = gtk.MenuItem("About Sutekh")
        self.oAbout.connect('activate', self.__oWin.show_about_dialog)
        oMenu.add(self.oAbout)
        self.oAbout.add_accelerator('activate', self._oAccelGroup,
                ord('A'), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)

        self.add(oMenuItem)

   # pylint: enable-msg=W0201

    def del_pane_set_sensitive(self, bValue):
        """Set the 'pane can be removed' option to bValue"""
        self.__oDelPane.set_sensitive(bValue)

    def add_card_text_set_sensitive(self, bValue):
        """Set the options for adding the Card Text Frame to bValue"""
        self.__oReplaceCardText.set_sensitive(bValue)
        self.__oAddCardText.set_sensitive(bValue)

    def pcs_list_pane_set_sensitive(self, bValue):
        """Set the options for adding the list of PhysicalCardSets to bValue"""
        self.__oReplacePCSListPane.set_sensitive(bValue)
        self.__oAddPCSListPane.set_sensitive(bValue)

    def acs_list_pane_set_sensitive(self, bValue):
        """Set the options for adding the list of AbstractCardSets to bValue"""
        self.__oReplaceACSListPane.set_sensitive(bValue)
        self.__oAddACSListPane.set_sensitive(bValue)

    def abstract_cl_set_sensitive(self, bValue):
        """Set the options for adding the WW cardlist to bValue"""
        self.__oReplaceACLPane.set_sensitive(bValue)
        self.__oAddACLPane.set_sensitive(bValue)

    def physical_cl_set_sensitive(self, bValue):
        """Set the options for adding the card collection to bValue"""
        self.__oReplacePCLPane.set_sensitive(bValue)
        self.__oAddPCLPane.set_sensitive(bValue)

    def set_split_vertical_active(self, bValue):
        """Set the split veritcal pane option to bValue"""
        self.__oAddVertPane.set_sensitive(bValue)

    def set_split_horizontal_active(self, bValue):
        """Set the split horizontal pane option to bValue"""
        self.__oAddHorzPane.set_sensitive(bValue)

    # pylint: disable-msg=W0613
    # oWidget + oMenuWidget required by function signature
    def do_import_physical_card_list(self, oWidget):
        """Import a Physical Card Collection from a XML file"""
        oFileChooser = ImportDialog("Select Card List to Import", self.__oWin)
        oFileChooser.run()
        sFileName = oFileChooser.get_name()
        if sFileName is not None:
            oParser = IdentifyXMLFile()
            # pylint: disable-msg=W0612
            # sName not relevent to PhysicalCard XML files, so unused
            (sType, sName, bExists) = oParser.id_file(sFileName)
            if sType == 'PhysicalCard':
                if not bExists:
                    oFile = PhysicalCardXmlFile(sFileName,
                            oLookup=self.__oWin.cardLookup)
                    oFile.read()
                    self.__oWin.reload_all()
                else:
                    do_complaint_error ( "Can only do this when the current"
                            " Card Collection is empty")
            else:
                do_complaint_error("File is not a PhysicalCard XML File.")

    def do_import_card_set(self, oWidget):
        """Import a card set from a XML File."""
        oFileChooser = ImportDialog("Select Card Set(s) to Import",
                self.__oWin)
        oFileChooser.run()
        sFileName = oFileChooser.get_name()
        if sFileName is not None:
            oParser = IdentifyXMLFile()
            (sType, sName, bExists) = oParser.id_file(sFileName)
            if sType == 'PhysicalCardSet' or sType == 'AbstractCardSet':
                if bExists:
                    iResponse = do_complaint_warning("This would delete the"
                            " existing CardSet " + sName)
                    if iResponse == gtk.RESPONSE_CANCEL:
                        return
                    else:
                        # Delete the card set
                        if sType == 'PhysicalCardSet':
                            delete_physical_card_set(sName)
                        else:
                            delete_abstract_card_set(sName)
                oFrame = self.__oWin.add_pane_end()
                try:
                    if sType == "AbstractCardSet":
                        oFile = AbstractCardSetXmlFile(sFileName,
                                oLookup=self.__oWin.cardLookup)
                        oFile.read()
                        self.__oWin.replace_with_abstract_card_set(sName,
                                oFrame)
                    else:
                        oFile = PhysicalCardSetXmlFile(sFileName,
                                oLookup=self.__oWin.cardLookup)
                        oFile.read()
                        self.__oWin.replace_with_physical_card_set(sName,
                                oFrame)
                except LookupFailed:
                    # Remove window, since we didn't succeed
                    # Should this dialog be here?
                    do_complaint_error("Import failed. Unable to find "
                            "matches for all the cards in the cardset.")
                    self.__oWin.remove_frame(oFrame)
            else:
                do_complaint_error("File is not a CardSet XML File.")

    def do_import_new_card_list(self, oWidget):
        """Refresh the WW card list and rulings files."""
        if refresh_ww_card_list(self.__oWin):
            self.__oWin.reload_all()

    def do_save_pane_set(self, oWidget):
        """Save the current pane layout"""
        self.__oWin.save_frames()

    def do_toggle_save_on_exit(self, oWidget):
        """Toggle the 'Save Pane layout on exit' option"""
        bChoice = not self.__oConfig.get_save_on_exit()
        self.__oConfig.set_save_on_exit(bChoice)
        # gtk can handle the rest for us

    def do_toggle_save_precise_pos(self, oWidget):
        """Toggle save precise pane positions option"""
        bChoice = not self.__oConfig.get_save_precise_pos()
        self.__oConfig.set_save_precise_pos(bChoice)

    def do_toggle_save_window_size(self, oWidget):
        """Toggle save window size option"""
        bChoice = not self.__oConfig.get_save_window_size()
        self.__oConfig.set_save_window_size(bChoice)

    def equalize_panes(self, oMenuWidget):
        """Ensure all panes have the same width allocated."""
        self.__oWin.set_all_panes_equal()

    def add_pane_horizontal(self, oMenuWidget):
        """Split the current pane horizonitally and add a new pane."""
        self.__oWin.add_pane(False)

    def add_pane_vertical(self, oMenuWidget):
        """Split the current pane vertically and add a new pane."""
        self.__oWin.add_pane(True)

    def do_restore(self, oMenuWidget):
        """Restore the pane layout from the config file."""
        self.__oWin.restore_from_config()
