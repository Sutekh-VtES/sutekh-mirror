# DeckMenu.py
# Menu for the Deck View
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk

class DeckMenu(gtk.MenuBar,object):
    def __init__(self,oController,oWindow,Name):
        super(DeckMenu,self).__init__()
        self.__oC = oController
        self.__oWindow = oWindow
        self.deckName = Name
        
        self.__createDeckMenu()
        self.__createFilterMenu()
        self.__createPluginMenu()
        
    def __createDeckMenu(self):
        iMenu = gtk.MenuItem("Deck Actions")
        wMenu=gtk.Menu()
        iMenu.set_submenu(wMenu)

        iClose=gtk.MenuItem("Close Deck ("+self.deckName+")")
        wMenu.add(iClose)
        iClose.connect("activate", self.deckClose)

        iAddConstraint = gtk.MenuItem("Add Constraint")
        wMenu.add(iAddConstraint)

        self.removeConstraint= gtk.Action("RemoveCon","Remove Constraint",None,None)
        wMenu.add(self.removeConstraint.create_menu_item())
        self.removeConstraint.set_sensitive(False)

        iSeperator=gtk.SeparatorMenuItem()
        wMenu.add(iSeperator)
        
        iDelete=gtk.MenuItem("Delete Deck ("+self.deckName+")")
        # Possible enhancement, make deck names italic - looks like it requires
        # playing with menuitem attributes (or maybe gtk.Action)
        iDelete.connect("activate", self.deckDelete)
        wMenu.add(iDelete)

        self.add(iMenu)
  
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

    def __createPluginMenu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("Plugins")
        wMenu = gtk.Menu()
        iMenu.set_submenu(wMenu)
        
        # plugins
        for oPlugin in self.__oC.getPlugins():
            wMenu.add(oPlugin.getMenuItem())
            
        self.add(iMenu)

    def deckClose(self,widget):
        self.__oWindow.closeDeck(widget)

    def deckAnalyze(self,widget):
        self.__oWindow.analyzeDeck()

    def deckDelete(self,widget):
        self.__oWindow.deleteDeck()


    def getApplyFilter(self):
        return self.iApply.get_active()

    def setApplyFilter(self,state):
        self.iApply.set_active(state)
