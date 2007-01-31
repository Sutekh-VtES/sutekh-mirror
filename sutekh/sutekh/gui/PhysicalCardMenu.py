# PhysicalCardMenu.py
# Menu for the Physical Card View
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from ExportDialog import ExportDialog
from PhysicalCardWriter import PhysicalCardWriter

class PhysicalCardMenu(gtk.MenuBar,object):
    def __init__(self,oController,oWindow):
        super(PhysicalCardMenu,self).__init__()
        self.__oC = oController
        self.__oWindow = oWindow

        self.__dMenus={}
        self.__createFileMenu()
        self.__createFilterMenu()
        self.__createPluginMenu()

    def __createFileMenu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("File")
        wMenu = gtk.Menu()
        self.__dMenus["File"]=wMenu
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
        self.__dMenus["Filter"]=wMenu
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
                    self.__dMenus[sMenu].add(oMI)
                else:
                    # Plugins acts as a catchall Menu
                    wMenu.add(oMI)
        self.add(iMenu)

    def doExport(self,widget):
        oFileChooser=ExportDialog("Save Physical Card List As",self.__oWindow)
        oFileChooser.run()
        sFileName=oFileChooser.getName()
        if sFileName is not None:
            fOut=file(sFileName,'w')
            oW=PhysicalCardWriter()
            oW.write(fOut)
            fOut.close()

    def getApplyFilter(self):
        return self.iApply.get_active()

    def setApplyFilter(self,state):
        self.iApply.set_active(state)
