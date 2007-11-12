# MainMenu.py
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sqlobject import sqlhub, connectionForURI
from sutekh.core.SutekhObjects import ObjectList
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
        self.__create_about_menu()

    def __create_file_menu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("File")
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

        iSaveWindows = gtk.MenuItem('Save Current Pane Set')
        iSaveWindows.connect('activate', self.do_save_pane_set)
        wPrefsMenu.add(iSaveWindows)

        iSaveOnExit = gtk.CheckMenuItem('Save Pane Set on Exit')
        iSaveOnExit.set_inconsistent(False)
        if self.__oConfig.getSaveOnExit():
            iSaveOnExit.set_active(True)
        else:
            iSaveOnExit.set_active(False)
        iSaveOnExit.connect('activate', self.do_toggle_save_on_exit)
        wPrefsMenu.add(iSaveOnExit)

        iSeperator3 = gtk.SeparatorMenuItem()
        wMenu.add(iSeperator3)

        iQuit = gtk.MenuItem("Quit")
        iQuit.connect('activate', lambda iItem: self.__oWin.action_quit(self.__oWin))

        wMenu.add(iQuit)

        self.add(iMenu)

    def __create_pane_menu(self):
        iMenu = gtk.MenuItem("Pane Actions")
        wMenu = gtk.Menu()
        self.__dMenus["Pane"] = wMenu
        iMenu.set_submenu(wMenu)

        self.__oAddACLPane = gtk.MenuItem("Add Whitewolf Card List")
        wMenu.add(self.__oAddACLPane)
        self.__oAddACLPane.connect("activate", self.__oWin.add_abstract_card_list)
        self.__oAddACLPane.set_sensitive(True)

        self.__oAddPCLPane = gtk.MenuItem("Add Physical Card Collection List")
        wMenu.add(self.__oAddPCLPane)
        self.__oAddPCLPane.connect("activate", self.__oWin.add_physical_card_list)
        self.__oAddPCLPane.set_sensitive(True)

        self.__oAddCardText = gtk.MenuItem("Add Card Text Pane")
        wMenu.add(self.__oAddCardText)
        self.__oAddCardText.connect("activate", self.__oWin.add_card_text)
        self.__oAddCardText.set_sensitive(True)

        self.__oAddACSListPane = gtk.MenuItem("Add Abstract Card Set List")
        wMenu.add(self.__oAddACSListPane)
        self.__oAddACSListPane.connect("activate", self.__oWin.add_acs_list)
        self.__oAddACSListPane.set_sensitive(True)

        self.__oAddPCSListPane = gtk.MenuItem("Add Physical Card Set List")
        wMenu.add(self.__oAddPCSListPane)
        self.__oAddPCSListPane.connect("activate", self.__oWin.add_pcs_list)
        self.__oAddPCSListPane.set_sensitive(True)

        iSeperator = gtk.SeparatorMenuItem()
        wMenu.add(iSeperator)

        self.__oDelPane = gtk.MenuItem("Remove currently focussed pane")
        wMenu.add(self.__oDelPane)
        self.__oDelPane.connect("activate", self.__oWin.menu_remove_pane)
        self.__oDelPane.set_sensitive(False)

        self.add(iMenu)

    def del_pane_set_sensitive(self, bValue):
        self.__oDelPane.set_sensitive(bValue)

    def add_card_text_set_sensitive(self, bValue):
        self.__oAddCardText.set_sensitive(bValue)

    def pcs_list_pane_set_sensitive(self, bValue):
        self.__oAddPCLPane.set_sensitive(bValue)

    def acs_list_pane_set_sensitive(self, bValue):
        self.__oAddACLPane.set_sensitive(bValue)

    def abstract_card_list_set_sensitive(self, bValue):
        self.__oAddACLPane.set_sensitive(bValue)

    def physical_card_list_set_sensitive(self, bValue):
        self.__oAddPCLPane.set_sensitive(bValue)

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
                    Complaint = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR,
                            gtk.BUTTONS_CLOSE, "Can only do this when the current Card List is empty")
                    Complaint.connect("response", lambda dlg, resp: dlg.destroy())
                    Complaint.run()
            else:
                Complaint = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR,
                    gtk.BUTTONS_CLOSE, "File is not a PhysicalCard XML File.")
                Complaint.connect("response", lambda dlg, resp: dlg.destroy())
                Complaint.run()

    def do_import_card_set(self, oWidget):
        oFileChooser = ImportDialog("Select Card Set(s) to Import", self.__oWin)
        oFileChooser.run()
        sFileName = oFileChooser.getName()
        if sFileName is not None:
            oP = IdentifyXMLFile()
            (sType, sName, bExists) = oP.idFile(sFileName)
            if sType == 'PhysicalCardSet' or sType == 'AbstractCardSet':
                if bExists:
                    Complaint = gtk.MessageDialog(None, 0, gtk.MESSAGE_WARNING,
                            gtk.BUTTONS_OK_CANCEL, "This would delete the existing CardSet " + sName)
                    response = Complaint.run()
                    Complaint.destroy()
                    if response == gtk.RESPONSE_CANCEL:
                        return
                    else:
                        # Delete the card set
                        if sType == 'PhysicalCardSet':
                            delete_physical_card_set(sName)
                        else:
                            delete_abstract_card_set(sName)
                if sType == "AbstractCardSet":
                    oF = AbstractCardSetXmlFile(sFileName, lookup=self.__oWin.cardLookup)
                    oF.read()
                    self.__oWin.add_abstract_card_set(sName)
                else:
                    oF = PhysicalCardSetXmlFile(sFileName, lookup=self.__oWin.cardLookup)
                    oF.read()
                    self.__oWin.add_physical_card_set(sName)
            else:
                Complaint = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR,
                    gtk.BUTTONS_CLOSE, "File is not a CardSet XML File.")
                Complaint.connect("response", lambda dlg, resp: dlg.destroy())
                Complaint.run()

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
                    Complaint = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR,
                        gtk.BUTTONS_CLOSE, sMsg)
                    Complaint.run()
                    Complaint.destroy()
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
                Complaint = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR,
                    gtk.BUTTONS_OK_CANCEL, sMesg)
                response = Complaint.run()
                Complaint.destroy()
                if response == gtk.RESPONSE_OK:
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
                    Complaint = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR,
                        gtk.BUTTONS_CLOSE, sMesg)
                else:
                    sMesg = "Import Completed\n"
                    sMesg += "Eveything seems to have gone OK"
                    Complaint = gtk.MessageDialog(None, 0, gtk.MESSAGE_INFO,
                        gtk.BUTTONS_CLOSE, sMesg)
                Complaint.run()
                Complaint.destroy()
            self.__oWin.reload_all()

    def do_save_pane_set(self, oWidget):
        self.__oWin.save_panes()

    def do_toggle_save_on_exit(self, oWidget):
        bChoice = not self.__oConfig.getSaveOnExit()
        self.__oConfig.setSaveOnExit(bChoice)
        # gtk can handle the rest for us
