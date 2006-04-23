# MainMenu.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from SutekhObjects import PhysicalCardSet
from CreateDeckDialog import CreateDeckDialog
from LoadDeckDialog import LoadDeckDialog

class MainMenu(gtk.MenuBar,object):
    def __init__(self,oController,oWindow):
        super(MainMenu,self).__init__()
        self.__oC = oController
        self.__oWin = oWindow
        
        self.__createFileMenu()
        self.__createFilterMenu()
        
    def __createFileMenu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("File")
        wMenu = gtk.Menu()
        iMenu.set_submenu(wMenu)
        
        # items
        iCreate = gtk.MenuItem("Create New Deck")
        iCreate.connect('activate', self.doCreateDeck)
        wMenu.add(iCreate)

        self.deckLoad=gtk.Action("DeckLoad","Load an Existing Deck",None,None)
        wMenu.add(self.deckLoad.create_menu_item())
        self.deckLoad.connect('activate', self.doLoadDeck)
        self.deckLoad.set_sensitive(False)

        iSeperator=gtk.SeparatorMenuItem()
        wMenu.add(iSeperator)
        
        iQuit = gtk.MenuItem("Quit")
        iQuit.connect('activate', lambda iItem: self.__oC.actionQuit())
        
        wMenu.add(iQuit)
        
        self.add(iMenu)
        self.setLoadDeckState({}) # Call with an explicitly empty dict

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

    def setLoadDeckState(self,openDecks):
        # Determine if loadDeck should be greyed out or not
        # loadDeck is greyed if a deck exists that isn't open
        state = False
        oDecks = PhysicalCardSet.select()
        for Deck in oDecks:
            if Deck.name not in openDecks:
                state = True
        self.deckLoad.set_sensitive(state)

    def doCreateDeck(self,widget):
        # Popup Create Deck Dialog
        Dialog=CreateDeckDialog(self.__oWin)
        Dialog.run()
        Name=Dialog.getName()
        if Name!=None:
            # Check Name isn't in user
            NameList = PhysicalCardSet.selectBy(name=Name)
            if NameList.count() != 0:
                # Complain about duplicate name
                Complaint = gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR, \
                      gtk.BUTTON_CLOSE,"Name already in use")
                Complaint.connect("response",lambda dlg, resp: dlg.destroy())
                Complaint.run()
                return
        else:
            return 
        PhysicalCardSet(name=Name) # Create Deck
        self.__oC.createNewDeckWindow(Name)

    def doLoadDeck(self,widget):
        # Popup Load Deck Dialog
        Dialog=LoadDeckDialog(self.__oWin)
        Dialog.run()
        Name=Dialog.getName()
        if Name != None:
            window = self.__oC.createNewDeckWindow(Name)
            if window != None:
                window.load()

    def getApplyFilter(self):
        return self.iApply.get_active()

    def setApplyFilter(self,state):
        self.iApply.set_active(state)
