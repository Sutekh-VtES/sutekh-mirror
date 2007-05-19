# MainMenu.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sqlobject import sqlhub, connectionForURI
from sutekh.SutekhObjects import PhysicalCardSet, AbstractCardSet, ObjectList
from sutekh.gui.CreateCardSetDialog import CreateCardSetDialog
from sutekh.gui.LoadCardSetDialog import LoadCardSetDialog
from sutekh.gui.ImportDialog import ImportDialog
from sutekh.gui.WWFilesDialog import WWFilesDialog
from sutekh.XmlFileHandling import PhysicalCardXmlFile, PhysicalCardSetXmlFile, \
                                   AbstractCardSetXmlFile
from sutekh.IdentifyXMLFile import IdentifyXMLFile
from sutekh.DatabaseUpgrade import copyToNewAbstractCardDB, createFinalCopy
from sutekh.SutekhUtility import refreshTables, readWhiteWolfList, readRulings
from sutekh.ZipFileWrapper import ZipFileWrapper

class MainMenu(gtk.MenuBar,object):
    def __init__(self,oController,oWindow):
        super(MainMenu,self).__init__()
        self.__oC = oController
        self.__oWin = oWindow
        self.__dMenus={}
        self.__createFileMenu()
        self.__createFilterMenu()
        self.__createPluginMenu()
        self.__createAboutMenu()

    def __createFileMenu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("File")
        wMenu = gtk.Menu()
        self.__dMenus["File"]=wMenu
        iMenu.set_submenu(wMenu)

        # items
        iImportPhysical = gtk.MenuItem("Import Physical Card List from File")
        iImportPhysical.connect('activate', self.doImportPhysicalCardList)
        wMenu.add(iImportPhysical)

        iImportCardSet = gtk.MenuItem("Import Card Set from File")
        iImportCardSet.connect('activate', self.doImportCardSet)
        wMenu.add(iImportCardSet)

        iSeperator=gtk.SeparatorMenuItem()
        wMenu.add(iSeperator)

        if sqlhub.processConnection.uri() != "sqlite:///:memory:":
            # Need to have memory connection available for this
            iImportNewCardList = gtk.MenuItem("Import new White Wolf cardlist and rulings")
            iImportNewCardList.connect('activate', self.doImportNewCardList)
            wMenu.add(iImportNewCardList)
            iSeperator2=gtk.SeparatorMenuItem()
            wMenu.add(iSeperator2)

        iQuit = gtk.MenuItem("Quit")
        iQuit.connect('activate', lambda iItem: self.__oC.actionQuit())

        wMenu.add(iQuit)

        self.add(iMenu)

    def __createFilterMenu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("Filter")
        wMenu = gtk.Menu()
        self.__dMenus["Filter"]=wMenu
        iMenu.set_submenu(wMenu)

        # items
        iFilter = gtk.MenuItem("Specify Filter")
        wMenu.add(iFilter)
        iFilter.connect('activate', self.__oC.getFilter)

        self.iApply=gtk.CheckMenuItem("Apply Filter")
        self.iApply.set_inconsistent(False)
        self.iApply.set_active(False)
        wMenu.add(self.iApply)
        self.iApply.connect('activate', self.__oC.runFilter)

        self.add(iMenu)

    def __createPluginMenu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("Plugins")
        wMenu = gtk.Menu()
        self.__dMenus["Plugins"]=wMenu
        iMenu.set_submenu(wMenu)
        # plugins
        for oPlugin in self.__oC.getPlugins():
            oMI=oPlugin.getMenuItem()
            if oMI is not None:
                sMenu=oPlugin.getDesiredMenu()
                # Add to the requested menu if supplied
                if sMenu in self.__dMenus.keys():
                    if sMenu=="Plugins":
                        bShowPluginMenu=True
                    self.__dMenus[sMenu].add(oMI)
                else:
                    # Plugins acts as a catchall Menu
                    wMenu.add(oMI)
        self.add(iMenu)
        if len(wMenu.get_children())==0:
            iMenu.set_sensitive(False)

    def __createAboutMenu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("About")
        wMenu = gtk.Menu()
        self.__dMenus["About"] = wMenu
        iMenu.set_submenu(wMenu)

        self.iAbout = gtk.MenuItem("About Sutekh")
        self.iAbout.connect('activate', self.__oC.showAboutDialog)
        wMenu.add(self.iAbout)

        self.add(iMenu)

    def setLoadPhysicalState(self,openSets):
        # Determine if physLoad should be greyed out or not
        # physLoad is active if a PhysicalCardSet exists that isn't open
        state = False
        oSets = PhysicalCardSet.select()
        for oPCS in oSets:
            if oPCS.name not in openSets.keys():
                state = True
        self.physLoad.set_sensitive(state)

    def setLoadAbstractState(self,openSets):
        # Determine if loadAbs should be greyed out or not (as for loadPhys)
        state = False
        oSets = AbstractCardSet.select()
        for oACS in oSets:
            if oACS.name not in openSets.keys():
                state = True
        self.absLoad.set_sensitive(state)

    def doImportPhysicalCardList(self,widget):
        oFileChooser=ImportDialog("Select Card List to Import",self.__oWin)
        oFileChooser.run()
        sFileName=oFileChooser.getName()
        if sFileName is not None:
            oP=IdentifyXMLFile()
            (sType,sName,bExists)=oP.idFile(sFileName)
            if sType=='PhysicalCard':
                if not bExists:
                    oF=PhysicalCardXmlFile(sFileName)
                    oF.read()
                else:
                    Complaint = gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
                            gtk.BUTTONS_CLOSE,"Can only do this when the current Card List is empty")
                    response=Complaint.run()
                    Complaint.destroy()
            else:
                Complaint = gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
                                              gtk.BUTTONS_CLOSE,"File is not a PhysicalCard XML File.")
                Complaint.connect("response",lambda dlg, resp: dlg.destroy())
                Complaint.run()

    def doImportCardSet(self,widget):
        oFileChooser=ImportDialog("Select Card Set(s) to Import",self.__oWin)
        oFileChooser.run()
        sFileName=oFileChooser.getName()
        if sFileName is not None:
            oP=IdentifyXMLFile()
            (sType,sName,bExists)=oP.idFile(sFileName)
            if sType=='PhysicalCardSet' or sType=='AbstractCardSet':
                if bExists:
                    Complaint = gtk.MessageDialog(None,0,gtk.MESSAGE_WARNING,
                            gtk.BUTTONS_OK_CANCEL,"This would delete the existing CardSet "+sName)
                    response=Complaint.run()
                    Complaint.destroy()
                    if response==gtk.RESPONSE_CANCEL:
                        return
                if sType=="AbstractCardSet":
                    oF=AbstractCardSetXmlFile(sFileName)
                else:
                    oF=PhysicalCardSetXmlFile(sFileName)
                oF.read()
            else:
                Complaint = gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
                                              gtk.BUTTONS_CLOSE,"File is not a CardSet XML File.")
                Complaint.connect("response",lambda dlg, resp: dlg.destroy())

    def doImportNewCardList(self,widget):
        oWWFilesDialog=WWFilesDialog(self.__oWin)
        oWWFilesDialog.run()
        (sCLFileName,sRulingsFileName,sBackupFile) = oWWFilesDialog.getNames()
        oWWFilesDialog.destroy()
        if sCLFileName is not None:
            if sBackupFile is not None:
                try:
                    oFile=ZipFileWrapper(sBackupFile)
                    oFile.doDumpAllToZip()
                except Exception, e:
                    sMsg = "Failed to write backup.\n\n" + str(e) \
                           +"\nNot touching the database further"
                    Complaint = gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
                       gtk.BUTTONS_CLOSE,sMsg)
                    Complaint.run()
                    Complaint.destroy()
                    return
            tempConn=connectionForURI("sqlite:///:memory:")
            #tempConn=connectionForURI("sqlite:///tmp/test.db")
            oldConn=sqlhub.processConnection
            refreshTables(ObjectList,tempConn)
            # WhiteWolf Parser uses sqlhub connection
            sqlhub.processConnection=tempConn
            readWhiteWolfList(sCLFileName)
            if sRulingsFileName is not None:
                readRulings(sRulingsFileName)
            copyToNewAbstractCardDB(oldConn,tempConn)
            # OK, update complete, copy back from tempConn
            sqlhub.processConnection=oldConn
            createFinalCopy(tempConn)
            self.__oC.reloadAll()

    def getApplyFilter(self):
        return self.iApply.get_active()

    def setApplyFilter(self,state):
        self.iApply.set_active(state)
