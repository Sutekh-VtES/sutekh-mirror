# PhysicalCardMenu.py
# Menu for the Physical Card View
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk

class PhysicalCardMenu(gtk.MenuBar,object):
    def __init__(self,oController,oWindow):
        super(PhysicalCardMenu,self).__init__()
        self.__oC = oController
        self.__oWindow = oWindow
        
        self.__createFileMenu()
        self.__createFilterMenu()
        self.__createPluginMenu()

    def __createFileMenu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("File")
        wMenu = gtk.Menu()
        iMenu.set_submenu(wMenu)
        # items
        iExport = gtk.MenuItem("Export Physical Card List to File")
        wMenu.add(iExport)
        iExport.connect('activate', self.doExport)

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

    def doExport(self,widget):
        pass

    def getApplyFilter(self):
        return self.iApply.get_active()

    def setApplyFilter(self,state):
        self.iApply.set_active(state)
