# MainMenu.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sqlobject import sqlhub
from SutekhObjects import PhysicalCardSet, AbstractCardSet, ObjectList
from CreateCardSetDialog import CreateCardSetDialog
from LoadCardSetDialog import LoadCardSetDialog
from ImportDialog import ImportDialog
from PhysicalCardParser import PhysicalCardParser
from PhysicalCardSetParser import PhysicalCardSetParser
from AbstractCardSetParser import AbstractCardSetParser
from IdentifyXMLFile import IdentifyXMLFile
from WWFilesDialog import WWFilesDialog
from DatabaseUpgrade import copyToNewAbstractCardDB, createFinalCopy
from SutekhUtility import *

class MainMenu(gtk.MenuBar,object):
    def __init__(self,oController,oWindow):
        super(MainMenu,self).__init__()
        self.__oC = oController
        self.__oWin = oWindow
        self.__dMenus={}
        self.__createFileMenu()
        self.__createCardSetMenu()
        self.__createFilterMenu()
        self.__createPluginMenu()

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

    def __createCardSetMenu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("CardSet")
        wMenu = gtk.Menu()
        self.__dMenus["CardSet"]=wMenu
        iMenu.set_submenu(wMenu)

        # items
        iCreatePhysical = gtk.MenuItem("Create New Physical Card Set")
        iCreatePhysical.connect('activate', self.doCreatePCS)
        wMenu.add(iCreatePhysical)

        iCreateAbstract= gtk.MenuItem("Create New Abstract Card Set")
        iCreateAbstract.connect('activate', self.doCreateACS)
        wMenu.add(iCreateAbstract)

        self.physLoad=gtk.Action("PhysicalLoad","Open an Existing Physical Card Set",None,None)
        wMenu.add(self.physLoad.create_menu_item())
        self.physLoad.connect('activate', self.doLoadPCS)
        self.physLoad.set_sensitive(False)

        self.absLoad=gtk.Action("AbstractLoad","Open an Existing Abstract Card Set",None,None)
        wMenu.add(self.absLoad.create_menu_item())
        self.absLoad.connect('activate', self.doLoadACS)
        self.absLoad.set_sensitive(False)

        self.add(iMenu)
        self.setLoadPhysicalState({})
        self.setLoadAbstractState({}) # Call with an explicitly empty dict

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
        bShowPluginMenu=False
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
                    bShowPluginMenu=True
                    wMenu.add(oMI)
        if bShowPluginMenu:
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
            (sType,sName,bExists)=oP.parse(file(sFileName,'rU'))
            if sType=='PhysicalCard':
                if not bExists:
                    oP=PhysicalCardParser()
                    oP.parse(file(sFileName,'rU'))
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
            (sType,sName,bExists)=oP.parse(file(sFileName,'rU'))
            if sType=='PhysicalCardSet' or sType=='AbstractCardSet':
                if bExists:
                    Complaint = gtk.MessageDialog(None,0,gtk.MESSAGE_WARNING,
                            gtk.BUTTONS_OK_CANCEL,"This would delete the existing CardSet "+sName)
                    response=Complaint.run()
                    Complaint.destroy()
                    if response==gtk.RESPONSE_CANCEL:
                        return
                if sType=="AbstractCardSet":
                    oP=AbstractCardSetParser()
                else:
                    oP=PhysicalCardSetParser()
                oP.parse(file(sFileName,'rU'))
            else:
                Complaint = gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
                                              gtk.BUTTONS_CLOSE,"File is not a CardSet XML File.")
                Complaint.connect("response",lambda dlg, resp: dlg.destroy())

    def doImportNewCardList(self,widget):
        oWWFilesDialog=WWFilesDialog(self.__oWin)
        oWWFilesDialog.run()
        (sCLFileName,sRulingsFileName) = oWWFilesDialog.getNames()
        oWWFilesDialog.destroy()
        if sCLFileName is not None:
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

    def doCreatePCS(self,widget):
        # Popup Create PhysicalCardSet Dialog
        Dialog=CreateCardSetDialog(self.__oWin,"PhysicalCardSet")
        Dialog.run()
        (Name,sAuthor,sDesc)=Dialog.getName()
        if Name!=None:
            # Check Name isn't in use
            NameList = PhysicalCardSet.selectBy(name=Name)
            if NameList.count() != 0:
                # Complain about duplicate name
                Complaint = gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
                                              gtk.BUTTONS_CLOSE,"Chosen Physical Card Set name already in use.")
                Complaint.connect("response",lambda dlg, resp: dlg.destroy())
                Complaint.run()
                return
        else:
            return
        PhysicalCardSet(name=Name,author=sAuthor,comment=sDesc) # Create PhysicalCardSet
        self.__oC.createNewPhysicalCardSetWindow(Name)

    def doCreateACS(self,widget):
        # Popup Create AbstractCardSet Dialog
        Dialog=CreateCardSetDialog(self.__oWin,"AbstractCardSet")
        Dialog.run()
        (Name,sAuthor,sDesc)=Dialog.getName()
        if Name!=None:
            # Check Name isn't in use
            NameList = AbstractCardSet.selectBy(name=Name)
            if NameList.count() != 0:
                # Complain about duplicate name
                Complaint = gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
                                              gtk.BUTTONS_CLOSE,"Chosen Abstract Card Set name already in use.")
                Complaint.connect("response",lambda dlg, resp: dlg.destroy())
                Complaint.run()
                return
        else:
            return
        AbstractCardSet(name=Name,author=sAuthor,comment=sDesc) # Create New Abstract Card Set
        self.__oC.createNewAbstractCardSetWindow(Name)

    def doLoadPCS(self,widget):
        # Popup Load Dialog
        Dialog=LoadCardSetDialog(self.__oWin,"PhysicalCardSet")
        Dialog.run()
        Name=Dialog.getName()
        if Name != None:
            window = self.__oC.createNewPhysicalCardSetWindow(Name)
            if window != None:
                window.load()

    def doLoadACS(self,widget):
        # Popup Load Dialog
        Dialog=LoadCardSetDialog(self.__oWin,"AbstractCardSet")
        Dialog.run()
        Name=Dialog.getName()
        if Name != None:
            window = self.__oC.createNewAbstractCardSetWindow(Name)
            if window != None:
                window.load()


    def getApplyFilter(self):
        return self.iApply.get_active()

    def setApplyFilter(self,state):
        self.iApply.set_active(state)
