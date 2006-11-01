# MainMenu.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from SutekhObjects import PhysicalCardSet, AbstractCardSet
from CreateCardSetDialog import CreateCardSetDialog
from LoadCardSetDialog import LoadCardSetDialog

class MainMenu(gtk.MenuBar,object):
    def __init__(self,oController,oWindow):
        super(MainMenu,self).__init__()
        self.__oC = oController
        self.__oWin = oWindow

        self.__createFileMenu()
        self.__createCardSetMenu()
        self.__createFilterMenu()

    def __createFileMenu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("File")
        wMenu = gtk.Menu()
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

        iQuit = gtk.MenuItem("Quit")
        iQuit.connect('activate', lambda iItem: self.__oC.actionQuit())

        wMenu.add(iQuit)

        self.add(iMenu)

    def __createCardSetMenu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("CardSet")
        wMenu = gtk.Menu()
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
        pass

    def doImportCardSet(self,widget):
        pass

    def doCreatePCS(self,widget):
        # Popup Create PhysicalCardSet Dialog
        Dialog=CreateCardSetDialog(self.__oWin,"Physical")
        Dialog.run()
        Name=Dialog.getName()
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
        PhysicalCardSet(name=Name) # Create PhysicalCardSet
        self.__oC.createNewPhysicalCardSetWindow(Name)

    def doCreateACS(self,widget):
        # Popup Create AbstractCardSet Dialog
        Dialog=CreateCardSetDialog(self.__oWin,"Abstract")
        Dialog.run()
        Name=Dialog.getName()
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
        AbstractCardSet(name=Name) # Create New Abstract Card Set
        self.__oC.createNewAbstractCardSetWindow(Name)

    def doLoadPCS(self,widget):
        # Popup Load Dialog
        Dialog=LoadCardSetDialog(self.__oWin,"Physical")
        Dialog.run()
        Name=Dialog.getName()
        if Name != None:
            window = self.__oC.createNewPhysicalCardSetWindow(Name)
            if window != None:
                window.load()

    def doLoadACS(self,widget):
        # Popup Load Dialog
        Dialog=LoadCardSetDialog(self.__oWin,"Abstract")
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
