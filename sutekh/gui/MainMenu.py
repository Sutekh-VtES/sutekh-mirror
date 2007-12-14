# MainMenu.py
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sqlobject import sqlhub, connectionForURI
from sutekh.core.SutekhObjects import ObjectList
from sutekh.core.CardLookup import LookupFailed
from sutekh.gui.SutekhDialog import do_complaint_error, do_complaint_warning
from sutekh.gui.ImportDialog import ImportDialog
from sutekh.gui.WWFilesDialog import WWFilesDialog
from sutekh.io.XmlFileHandling import PhysicalCardXmlFile, PhysicalCardSetXmlFile, \
                                    AbstractCardSetXmlFile
from sutekh.io.IdentifyXMLFile import IdentifyXMLFile
from sutekh.core.DatabaseUpgrade import copyToNewAbstractCardDB, createFinalCopy
from sutekh.SutekhUtility import refreshTables, readWhiteWolfList, readRulings, \
        delete_physical_card_set, delete_abstract_card_set
from sutekh.io.ZipFileWrapper import ZipFileWrapper

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

    def __create_file_menu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("_File")
        wMenu = gtk.Menu()
        self.__dMenus["File"] = wMenu
        iMenu.set_submenu(wMenu)

        # items
        iImportPhysical = gtk.MenuItem("Import Physical Card List from File")
        iImportPhysical.connect('activate', self.do_import_physical_card_list)
        wMenu.add(iImportPhysical)

        iImportCardSet = gtk.MenuItem("Import Card Set from File")
        iImportCardSet.connect('activate', self.do_import_card_set)
        wMenu.add(iImportCardSet)

        iSeperator = gtk.SeparatorMenuItem()
        wMenu.add(iSeperator)

        if sqlhub.processConnection.uri() != "sqlite:///:memory:":
            # Need to have memory connection available for this
            iImportNewCardList = gtk.MenuItem("Import new White Wolf cardlist and rulings")
            iImportNewCardList.connect('activate', self.do_import_new_card_list)
            wMenu.add(iImportNewCardList)
            iSeperator2 = gtk.SeparatorMenuItem()
            wMenu.add(iSeperator2)

        wPrefsMenu = gtk.Menu()
        iPrefsItem = gtk.MenuItem('Preferences')
        iPrefsItem.set_submenu(wPrefsMenu)
        wMenu.add(iPrefsItem)

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

        iRestoreConfig = gtk.MenuItem('Restore saved configuration')
        wMenu.add(iRestoreConfig)
        iRestoreConfig.connect('activate', self.do_restore)

        iSeperator3 = gtk.SeparatorMenuItem()
        wMenu.add(iSeperator3)

        iQuit = gtk.MenuItem("Quit")
        iQuit.connect('activate', lambda iItem: self.__oWin.action_quit(self.__oWin))

        wMenu.add(iQuit)

        self.add(iMenu)

    def __create_pane_menu(self):
        iMenu = gtk.MenuItem("Pane _Actions")
        wMenu = gtk.Menu()
        self.__dMenus["Pane"] = wMenu
        iMenu.set_submenu(wMenu)

        oEqualizePanes = gtk.MenuItem("Equalize pane sizes")
        wMenu.add(oEqualizePanes)
        oEqualizePanes.connect("activate", self.equalize_panes)


        self.__oAddHorzPane = gtk.MenuItem("Split current pane _horizontally")
        wMenu.add(self.__oAddHorzPane)
        self.__oAddHorzPane.connect("activate", self.add_pane_horizontal)
        self.__oAddHorzPane.set_sensitive(False)

        self.__oAddVertPane = gtk.MenuItem("Split current pane _vertically")
        wMenu.add(self.__oAddVertPane)
        self.__oAddVertPane.connect("activate", self.add_pane_vertical)
        self.__oAddVertPane.set_sensitive(False)

        self.__oReplaceWithACLPane = gtk.MenuItem("Replace current pane with Whitewolf Card List")
        wMenu.add(self.__oReplaceWithACLPane)
        self.__oReplaceWithACLPane.connect("activate", self.__oWin.replace_with_abstract_card_list)
        self.__oReplaceWithACLPane.set_sensitive(True)

        self.__oReplaceWithPCLPane = gtk.MenuItem("Replace current pane with Physical Card Collection List")
        wMenu.add(self.__oReplaceWithPCLPane)
        self.__oReplaceWithPCLPane.connect("activate", self.__oWin.replace_with_physical_card_list)
        self.__oReplaceWithPCLPane.set_sensitive(True)

        self.__oReplaceWithCardText = gtk.MenuItem("Replace current pane with Card Text Pane")
        wMenu.add(self.__oReplaceWithCardText)
        self.__oReplaceWithCardText.connect("activate", self.__oWin.replace_with_card_text)
        self.__oReplaceWithCardText.set_sensitive(True)

        self.__oReplaceWithACSListPane = gtk.MenuItem("Replace current pane with Abstract Card Set List")
        wMenu.add(self.__oReplaceWithACSListPane)
        self.__oReplaceWithACSListPane.connect("activate", self.__oWin.replace_with_acs_list)
        self.__oReplaceWithACSListPane.set_sensitive(True)

        self.__oReplaceWithPCSListPane = gtk.MenuItem("Replace current pane with Physical Card Set List")
        wMenu.add(self.__oReplaceWithPCSListPane)
        self.__oReplaceWithPCSListPane.connect("activate", self.__oWin.replace_with_pcs_list)
        self.__oReplaceWithPCSListPane.set_sensitive(True)

        iSeperator = gtk.SeparatorMenuItem()
        wMenu.add(iSeperator)

        self.__oDelPane = gtk.MenuItem("_Remove current pane")
        wMenu.add(self.__oDelPane)
        self.__oDelPane.connect("activate", self.__oWin.menu_remove_frame)
        self.__oDelPane.set_sensitive(False)

        self.add(iMenu)

    def __create_plugin_menu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("Plugins")
        wMenu = gtk.Menu()
        self.__dMenus["Plugins"] = wMenu
        # plugins
        for oPlugin in self.__oWin._aPlugins:
            oMI = oPlugin.get_menu_item()
            if oMI is not None:
                sMenu = oPlugin.get_desired_menu()
                # Add to the requested menu if supplied
                if sMenu in self.__dMenus.keys():
                    self.__dMenus[sMenu].add(oMI)
                else:
                    # Plugins acts as a catchall Menu
                    wMenu.add(oMI)
        iMenu.set_submenu(wMenu)
        self.add(iMenu)
        if len(wMenu.get_children()) == 0:
            iMenu.set_sensitive(False)

    def del_pane_set_sensitive(self, bValue):
        self.__oDelPane.set_sensitive(bValue)

    def add_card_text_set_sensitive(self, bValue):
        self.__oReplaceWithCardText.set_sensitive(bValue)

    def pcs_list_pane_set_sensitive(self, bValue):
        self.__oReplaceWithPCSListPane.set_sensitive(bValue)

    def acs_list_pane_set_sensitive(self, bValue):
        self.__oReplaceWithACSListPane.set_sensitive(bValue)

    def abstract_card_list_set_sensitive(self, bValue):
        self.__oReplaceWithACLPane.set_sensitive(bValue)

    def physical_card_list_set_sensitive(self, bValue):
        self.__oReplaceWithPCLPane.set_sensitive(bValue)

    def set_split_vertical_active(self, bValue):
        self.__oAddVertPane.set_sensitive(bValue)

    def set_split_horizontal_active(self, bValue):
        self.__oAddHorzPane.set_sensitive(bValue)

    def __create_about_menu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("About")
        wMenu = gtk.Menu()
        self.__dMenus["About"] = wMenu
        iMenu.set_submenu(wMenu)

        self.iAbout = gtk.MenuItem("About Sutekh")
        self.iAbout.connect('activate', self.__oWin.show_about_dialog)
        wMenu.add(self.iAbout)

        self.add(iMenu)

    def do_import_physical_card_list(self, oWidget):
        oFileChooser = ImportDialog("Select Card List to Import", self.__oWin)
        oFileChooser.run()
        sFileName = oFileChooser.getName()
        if sFileName is not None:
            oP = IdentifyXMLFile()
            (sType, sName, bExists) = oP.idFile(sFileName)
            if sType == 'PhysicalCard':
                if not bExists:
                    oF = PhysicalCardXmlFile(sFileName, lookup=self.__oWin.cardLookup)
                    oF.read()
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
            oP = IdentifyXMLFile()
            (sType, sName, bExists) = oP.idFile(sFileName)
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
                oFrame = self.__oWin.add_pane()
                try:
                    if sType == "AbstractCardSet":
                        oF = AbstractCardSetXmlFile(sFileName, lookup=self.__oWin.cardLookup)
                        oF.read()
                        self.__oWin.replace_with_abstract_card_set(sName, oFrame)
                    else:
                        oF = PhysicalCardSetXmlFile(sFileName, lookup=self.__oWin.cardLookup)
                        oF.read()
                        self.__oWin.replace_with_physical_card_set(sName, oFrame)
                except LookupFailed:
                    # Remove window, since we didn't succeed
                    # Should this dialog be here?
                    do_complaint_error("Import failed. Unable to find matches for all the cards in the cardset.")
                    self.__oWin.remove_frame(oFrame)
            else:
                do_complaint_error("File is not a CardSet XML File.")

    def do_import_new_card_list(self, oWidget):
        oWWFilesDialog = WWFilesDialog(self.__oWin)
        oWWFilesDialog.run()
        (sCLFileName, sRulingsFileName, sBackupFile) = oWWFilesDialog.getNames()
        oWWFilesDialog.destroy()
        if sCLFileName is not None:
            if sBackupFile is not None:
                try:
                    oFile = ZipFileWrapper(sBackupFile)
                    oFile.doDumpAllToZip()
                except Exception, e:
                    sMsg = "Failed to write backup.\n\n" + str(e) \
                        + "\nNot touching the database further"
                    do_complaint_error(sMsg)
                    return
            tempConn = connectionForURI("sqlite:///:memory:")
            oldConn = sqlhub.processConnection
            refreshTables(ObjectList, tempConn)
            # WhiteWolf Parser uses sqlhub connection
            sqlhub.processConnection = tempConn
            readWhiteWolfList(sCLFileName)
            if sRulingsFileName is not None:
                readRulings(sRulingsFileName)
            bCont = False
            # Refresh abstract card view for card lookups
            self.__oWin.reload_all()
            (bOK, aErrors) = copyToNewAbstractCardDB(oldConn, tempConn, self.__oWin.cardLookup)
            if not bOK:
                sMesg = "There was a problem copying the cardlist to the new database\n"
                for sStr in aErrors:
                    sMesg += sStr + "\n"
                sMesg += "Attempt to Continue Anyway (This is quite possibly dangerous)?"
                iResponse = do_complaint_warning(sMesg)
                if iResponse == gtk.RESPONSE_OK:
                    bCont = True
            else:
                bCont = True
            # OK, update complete, copy back from tempConn
            sqlhub.processConnection = oldConn
            if bCont:
                (bOK, aErrors) = createFinalCopy(tempConn)
                if not bOK:
                    sMesg = "There was a problem updating the database\n"
                    for sStr in aErrors:
                        sMesg += sStr + "\n"
                    sMesg += "Your database may be in an inconsistent state - sorry"
                    do_complaint_error(sMesg)
                else:
                    sMesg = "Import Completed\n"
                    sMesg += "Eveything seems to have gone OK"
                    do_complaint_error(sMesg)
            self.__oWin.reload_all()

    def do_save_pane_set(self, oWidget):
        self.__oWin.save_frames()

    def do_toggle_save_on_exit(self, oWidget):
        bChoice = not self.__oConfig.getSaveOnExit()
        self.__oConfig.setSaveOnExit(bChoice)
        # gtk can handle the rest for us

    def do_toggle_save_precise_pos(self, oWidget):
        bChoice = not self.__oConfig.get_save_precise_pos()
        self.__oConfig.set_save_precise_pos(bChoice)

    def equalize_panes(self, oMenuWidget):
        self.__oWin.set_all_panes_equal()

    def add_pane_horizontal(self, oMenuWidget):
        self.__oWin.add_pane(False)

    def add_pane_vertical(self, oMenuWidget):
        self.__oWin.add_pane(True)

    def do_restore(self, oMenuWidget):
        self.__oWin.restore_from_config()
