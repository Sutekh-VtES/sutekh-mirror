# MainMenu.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sqlobject import sqlhub
from sutekh.core.CardLookup import LookupFailed
from sutekh.gui.SutekhDialog import do_complaint_error, do_complaint_warning
from sutekh.gui.ImportDialog import ImportDialog
from sutekh.gui.GuiDBManagement import refresh_WW_card_list
from sutekh.io.XmlFileHandling import PhysicalCardXmlFile, \
        PhysicalCardSetXmlFile, AbstractCardSetXmlFile
from sutekh.io.IdentifyXMLFile import IdentifyXMLFile
from sutekh.SutekhUtility import delete_physical_card_set, \
        delete_abstract_card_set

class MainMenu(gtk.MenuBar, object):
    def __init__(self, oWindow, oConfig):
        super(MainMenu, self).__init__()
        self.__oWin = oWindow
        self.__dMenus = {}
        self.__oConfig = oConfig
        self.__create_file_menu()
        self.__create_pane_menu()
        self.__create_plugin_menu()
        self.__create_about_menu()
        oWindow.add_to_menu_list("My Collection",
                self.physical_card_list_set_sensitive)
        oWindow.add_to_menu_list("White Wolf Card List",
                self.abstract_card_list_set_sensitive)
        oWindow.add_to_menu_list("Physical Card Set List",
                self.pcs_list_pane_set_sensitive)
        oWindow.add_to_menu_list("Abstract Card Set List",
                self.acs_list_pane_set_sensitive)
        oWindow.add_to_menu_list("Card Text",
                self.add_card_text_set_sensitive)

    def __create_file_menu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("_File")
        oMenu = gtk.Menu()
        self.__dMenus["File"] = oMenu
        iMenu.set_submenu(oMenu)

        # items
        iImportPhysical = gtk.MenuItem("Import Collection from File")
        iImportPhysical.connect('activate', self.do_import_physical_card_list)
        oMenu.add(iImportPhysical)

        iImportCardSet = gtk.MenuItem("Import Card Set from File")
        iImportCardSet.connect('activate', self.do_import_card_set)
        oMenu.add(iImportCardSet)

        iSeperator = gtk.SeparatorMenuItem()
        oMenu.add(iSeperator)

        if sqlhub.processConnection.uri() != "sqlite:///:memory:":
            # Need to have memory connection available for this
            iImportNewCardList = gtk.MenuItem(
                    "Import new White Wolf Card List and rulings")
            iImportNewCardList.connect('activate',
                    self.do_import_new_card_list)
            oMenu.add(iImportNewCardList)
            iSeperator2 = gtk.SeparatorMenuItem()
            oMenu.add(iSeperator2)

        wPrefsMenu = gtk.Menu()
        iPrefsItem = gtk.MenuItem('Preferences')
        iPrefsItem.set_submenu(wPrefsMenu)
        oMenu.add(iPrefsItem)

        iSavePanes = gtk.MenuItem('Save Current Pane Set')
        iSavePanes.connect('activate', self.do_save_pane_set)
        wPrefsMenu.add(iSavePanes)

        iSaveOnExit = gtk.CheckMenuItem('Save Pane Set on Exit')
        iSaveOnExit.set_inconsistent(False)
        if self.__oConfig.getSaveOnExit():
            iSaveOnExit.set_active(True)
        else:
            iSaveOnExit.set_active(False)
        iSaveOnExit.connect('activate', self.do_toggle_save_on_exit)
        wPrefsMenu.add(iSaveOnExit)

        iSavePos = gtk.CheckMenuItem('Save Exact Pane Positions')
        iSavePos.set_inconsistent(False)
        if self.__oConfig.get_save_precise_pos():
            iSavePos.set_active(True)
        else:
            iSavePos.set_active(False)
        iSavePos.connect('activate', self.do_toggle_save_precise_pos)
        wPrefsMenu.add(iSavePos)

        iSaveWinSize = gtk.CheckMenuItem('Save Window Size')
        iSaveWinSize.set_inconsistent(False)
        if self.__oConfig.get_save_window_size():
            iSaveWinSize.set_active(True)
        else:
            iSaveWinSize.set_active(False)
        iSaveOnExit.connect('activate', self.do_toggle_save_window_size)
        wPrefsMenu.add(iSaveWinSize)


        iRestoreConfig = gtk.MenuItem('Restore saved configuration')
        oMenu.add(iRestoreConfig)
        iRestoreConfig.connect('activate', self.do_restore)

        iSeperator3 = gtk.SeparatorMenuItem()
        oMenu.add(iSeperator3)

        iQuit = gtk.MenuItem("_Quit")
        iQuit.connect('activate',
                lambda iItem: self.__oWin.action_quit(self.__oWin))

        oMenu.add(iQuit)

        self.add(iMenu)

    def __create_pane_menu(self):
        iMenu = gtk.MenuItem("Pane _Actions")
        oMenu = gtk.Menu()
        self.__dMenus["Pane"] = oMenu
        iMenu.set_submenu(oMenu)

        oEqualizePanes = gtk.MenuItem("Equalize pane sizes")
        oMenu.add(oEqualizePanes)
        oEqualizePanes.connect("activate", self.equalize_panes)


        self.__oAddHorzPane = gtk.MenuItem("Split current pane _horizontally (|)")
        oMenu.add(self.__oAddHorzPane)
        self.__oAddHorzPane.connect("activate", self.add_pane_horizontal)
        self.__oAddHorzPane.set_sensitive(False)

        self.__oAddVertPane = gtk.MenuItem("Split current pane _vertically (-)")
        oMenu.add(self.__oAddVertPane)
        self.__oAddVertPane.connect("activate", self.add_pane_vertical)
        self.__oAddVertPane.set_sensitive(False)

        self._add_add_submenu(oMenu)
        self._add_replace_submenu(oMenu)

        iSeperator = gtk.SeparatorMenuItem()
        oMenu.add(iSeperator)

        self.__oDelPane = gtk.MenuItem("_Remove current pane")
        oMenu.add(self.__oDelPane)
        self.__oDelPane.connect("activate", self.__oWin.menu_remove_frame)
        self.__oDelPane.set_sensitive(False)

        self.add(iMenu)


    def _add_add_submenu(self, oMenuWidget):
        """Create a submenu for the add pane options"""
        wAddMenu = gtk.Menu()
        oAddMenu = gtk.MenuItem('Add New Pane')
        oAddMenu.set_submenu(wAddMenu)
        oMenuWidget.add(oAddMenu)


        oAddNewPane = gtk.MenuItem(
                "Add New Blank Pane")
        wAddMenu.add(oAddNewPane)
        oAddNewPane.connect("activate",
                self.__oWin.add_pane_end)

        self.__oAddACLPane = gtk.MenuItem(
                "Add White Wolf Card List")
        wAddMenu.add(self.__oAddACLPane)
        self.__oAddACLPane.connect("activate",
                self.__oWin.add_new_abstract_card_list)
        self.__oAddACLPane.set_sensitive(True)

        self.__oAddPCLPane = gtk.MenuItem(
                "Add My Collection List")
        wAddMenu.add(self.__oAddPCLPane)
        self.__oAddPCLPane.connect("activate",
                self.__oWin.add_new_physical_card_list)
        self.__oAddPCLPane.set_sensitive(True)

        self.__oAddCardText = gtk.MenuItem(
                "Add Card Text Pane")
        wAddMenu.add(self.__oAddCardText)
        self.__oAddCardText.connect("activate",
                self.__oWin.add_new_card_text)
        self.__oAddCardText.set_sensitive(True)

        self.__oAddACSListPane = gtk.MenuItem(
                "Add Abstract Card Set List")
        wAddMenu.add(self.__oAddACSListPane)
        self.__oAddACSListPane.connect("activate",
                self.__oWin.add_new_acs_list)
        self.__oAddACSListPane.set_sensitive(True)

        self.__oAddPCSListPane = gtk.MenuItem(
                "Add Physical Card Set List")
        wAddMenu.add(self.__oAddPCSListPane)
        self.__oAddPCSListPane.connect("activate",
                self.__oWin.add_new_pcs_list)
        self.__oAddPCSListPane.set_sensitive(True)

    def _add_replace_submenu(self, oMenuWidget):
        """Create a submenu for the replace pane options"""
        wReplaceMenu = gtk.Menu()
        oReplaceMenu = gtk.MenuItem('Replace Pane')
        oReplaceMenu.set_submenu(wReplaceMenu)
        oMenuWidget.add(oReplaceMenu)

        self.__oReplaceWithACLPane = gtk.MenuItem(
                "Replace current pane with White Wolf Card List")
        wReplaceMenu.add(self.__oReplaceWithACLPane)
        self.__oReplaceWithACLPane.connect("activate",
                self.__oWin.replace_with_abstract_card_list)
        self.__oReplaceWithACLPane.set_sensitive(True)

        self.__oReplaceWithPCLPane = gtk.MenuItem(
                "Replace current pane with My Collection List")
        wReplaceMenu.add(self.__oReplaceWithPCLPane)
        self.__oReplaceWithPCLPane.connect("activate",
                self.__oWin.replace_with_physical_card_list)
        self.__oReplaceWithPCLPane.set_sensitive(True)

        self.__oReplaceWithCardText = gtk.MenuItem(
                "Replace current pane with Card Text Pane")
        wReplaceMenu.add(self.__oReplaceWithCardText)
        self.__oReplaceWithCardText.connect("activate",
                self.__oWin.replace_with_card_text)
        self.__oReplaceWithCardText.set_sensitive(True)

        self.__oReplaceWithACSListPane = gtk.MenuItem(
                "Replace current pane with Abstract Card Set List")
        wReplaceMenu.add(self.__oReplaceWithACSListPane)
        self.__oReplaceWithACSListPane.connect("activate",
                self.__oWin.replace_with_acs_list)
        self.__oReplaceWithACSListPane.set_sensitive(True)

        self.__oReplaceWithPCSListPane = gtk.MenuItem(
                "Replace current pane with Physical Card Set List")
        wReplaceMenu.add(self.__oReplaceWithPCSListPane)
        self.__oReplaceWithPCSListPane.connect("activate",
                self.__oWin.replace_with_pcs_list)
        self.__oReplaceWithPCSListPane.set_sensitive(True)


    def __create_plugin_menu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("Plugins")
        oMenu = gtk.Menu()
        self.__dMenus["Plugins"] = oMenu
        # plugins
        for oPlugin in self.__oWin._aPlugins:
            oPlugin.add_to_menu(self.__dMenus, oMenu)
        iMenu.set_submenu(oMenu)
        self.add(iMenu)
        if len(oMenu.get_children()) == 0:
            iMenu.set_sensitive(False)

    def del_pane_set_sensitive(self, bValue):
        self.__oDelPane.set_sensitive(bValue)

    def add_card_text_set_sensitive(self, bValue):
        self.__oReplaceWithCardText.set_sensitive(bValue)
        self.__oAddCardText.set_sensitive(bValue)

    def pcs_list_pane_set_sensitive(self, bValue):
        self.__oReplaceWithPCSListPane.set_sensitive(bValue)
        self.__oAddPCSListPane.set_sensitive(bValue)

    def acs_list_pane_set_sensitive(self, bValue):
        self.__oReplaceWithACSListPane.set_sensitive(bValue)
        self.__oAddACSListPane.set_sensitive(bValue)

    def abstract_card_list_set_sensitive(self, bValue):
        self.__oReplaceWithACLPane.set_sensitive(bValue)
        self.__oAddACLPane.set_sensitive(bValue)

    def physical_card_list_set_sensitive(self, bValue):
        self.__oReplaceWithPCLPane.set_sensitive(bValue)
        self.__oAddPCLPane.set_sensitive(bValue)

    def set_split_vertical_active(self, bValue):
        self.__oAddVertPane.set_sensitive(bValue)

    def set_split_horizontal_active(self, bValue):
        self.__oAddHorzPane.set_sensitive(bValue)

    def __create_about_menu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("About")
        oMenu = gtk.Menu()
        self.__dMenus["About"] = oMenu
        iMenu.set_submenu(oMenu)

        self.iAbout = gtk.MenuItem("About Sutekh")
        self.iAbout.connect('activate', self.__oWin.show_about_dialog)
        oMenu.add(self.iAbout)

        self.add(iMenu)

    def do_import_physical_card_list(self, oWidget):
        oFileChooser = ImportDialog("Select Card List to Import", self.__oWin)
        oFileChooser.run()
        sFileName = oFileChooser.getName()
        if sFileName is not None:
            oParser = IdentifyXMLFile()
            (sType, sName, bExists) = oParser.idFile(sFileName)
            if sType == 'PhysicalCard':
                if not bExists:
                    oFile = PhysicalCardXmlFile(sFileName, lookup=self.__oWin.cardLookup)
                    oFile.read()
                    self.__oWin.reload_all()
                else:
                    do_complaint_error ( "Can only do this when the current Card List is empty")
            else:
                do_complaint_error("File is not a PhysicalCard XML File.")

    def do_import_card_set(self, oWidget):
        oFileChooser = ImportDialog("Select Card Set(s) to Import", self.__oWin)
        oFileChooser.run()
        sFileName = oFileChooser.getName()
        if sFileName is not None:
            oParser = IdentifyXMLFile()
            (sType, sName, bExists) = oParser.idFile(sFileName)
            if sType == 'PhysicalCardSet' or sType == 'AbstractCardSet':
                if bExists:
                    iResponse = do_complaint_warning("This would delete the existing CardSet " + sName)
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
                        oFile = AbstractCardSetXmlFile(sFileName, lookup=self.__oWin.cardLookup)
                        oFile.read()
                        self.__oWin.replace_with_abstract_card_set(sName, oFrame)
                    else:
                        oFile = PhysicalCardSetXmlFile(sFileName, lookup=self.__oWin.cardLookup)
                        oFile.read()
                        self.__oWin.replace_with_physical_card_set(sName, oFrame)
                except LookupFailed:
                    # Remove window, since we didn't succeed
                    # Should this dialog be here?
                    do_complaint_error("Import failed. Unable to find matches for all the cards in the cardset.")
                    self.__oWin.remove_frame(oFrame)
            else:
                do_complaint_error("File is not a CardSet XML File.")

    def do_import_new_card_list(self, oWidget):
        if refresh_WW_card_list(self.__oWin):
            self.__oWin.reload_all()

    def do_save_pane_set(self, oWidget):
        self.__oWin.save_frames()

    def do_toggle_save_on_exit(self, oWidget):
        bChoice = not self.__oConfig.getSaveOnExit()
        self.__oConfig.setSaveOnExit(bChoice)
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
        self.__oWin.set_all_panes_equal()

    def add_pane_horizontal(self, oMenuWidget):
        self.__oWin.add_pane(False)

    def add_pane_vertical(self, oMenuWidget):
        self.__oWin.add_pane(True)

    def do_restore(self, oMenuWidget):
        self.__oWin.restore_from_config()
