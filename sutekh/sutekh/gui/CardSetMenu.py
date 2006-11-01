# CardSetMenu.py
# Menu for the CardSet View's
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk

class CardSetMenu(gtk.MenuBar,object):
    def __init__(self,oController,oWindow,sName):
        super(CardSetMenu,self).__init__()
        self.__oC = oController
        self.__oWindow = oWindow
        self.sSetName = sName
        self.__createCardSetMenu()
        self.__createFilterMenu()
        self.__createPluginMenu()

    def __createCardSetMenu(self):
        iMenu = gtk.MenuItem("Card Set Actions")
        wMenu=gtk.Menu()
        iMenu.set_submenu(wMenu)
        iExport = gtk.MenuItem("Export Card Set ("+self.sSetName+") to File")
        wMenu.add(iExport)
        iExport.connect('activate', self.doExport)
        iClose=gtk.MenuItem("Close Card Set ("+self.sSetName+")")
        wMenu.add(iClose)
        iClose.connect("activate", self.cardSetClose)
        iDelete=gtk.MenuItem("Delete Card Set ("+self.sSetName+")")
        # Possible enhancement, make card set names italic.
        # Looks like it requires playing with menuitem attributes
        # (or maybe gtk.Action)
        iDelete.connect("activate", self.cardSetDelete) 
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
        # Add the Menu
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

    def doExport(self,widget):
        pass

    def cardSetClose(self,widget):
        self.__oWindow.closeCardSet(widget)

    def cardSetDelete(self,widget):
        self.__oWindow.deleteCardSet()

    def getApplyFilter(self):
        return self.iApply.get_active()

    def setApplyFilter(self,state):
        self.iApply.set_active(state)
