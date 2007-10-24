# PhysicalCardMenu.py
# Menu for the Physical Card View
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.gui.ExportDialog import ExportDialog
from sutekh.io.XmlFileHandling import PhysicalCardXmlFile

class PhysicalCardMenu(gtk.MenuBar,object):
    def __init__(self, oFrame, oController, oWindow):
        super(PhysicalCardMenu,self).__init__()
        self.__oC = oController
        self.__oWindow = oWindow
        self.__oFrame = oFrame

        self.__dMenus = {}
        self.__createPCLMenu()
        self.__createFilterMenu()
        self.__createPluginMenu()

    def __createPCLMenu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("Physical Card List Actions")
        wMenu = gtk.Menu()
        self.__dMenus["PCS"] = wMenu
        iMenu.set_submenu(wMenu)
        # items
        iExport = gtk.MenuItem("Export Physical Card List to File")
        wMenu.add(iExport)
        iExport.connect('activate', self.doExport)

        self.iViewExpansions = gtk.CheckMenuItem('Show Card Expansions in the Pane')
        self.iViewExpansions.set_inconsistent(False)
        self.iViewExpansions.set_active(True)
        self.iViewExpansions.connect('toggled', self.toggleExpansion)
        wMenu.add(self.iViewExpansions)

        self.add(iMenu)

    def __createFilterMenu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("Filter")
        wMenu = gtk.Menu()
        iMenu.set_submenu(wMenu)
        self.__dMenus["Filter"] = wMenu
        # items
        iFilter = gtk.MenuItem("Specify Filter")
        wMenu.add(iFilter)
        iFilter.connect('activate', self.setFilter)

        self.iApply = gtk.CheckMenuItem("Apply Filter")
        self.iApply.set_inconsistent(False)
        self.iApply.set_active(False)
        wMenu.add(self.iApply)
        self.iApply.connect('toggled', self.toggleApply)
        self.add(iMenu)

    def __createPluginMenu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("Plugins")
        wMenu = gtk.Menu()
        self.__dMenus["Plugins"] = wMenu
        iMenu.set_submenu(wMenu)
        # plugins
        for oPlugin in self.__oFrame._aPlugins:
            oMI = oPlugin.getMenuItem()
            if oMI is not None:
                sMenu = oPlugin.getDesiredMenu()
                # Add to the requested menu if supplied
                if sMenu in self.__dMenus.keys():
                    self.__dMenus[sMenu].add(oMI)
                else:
                    # Plugins acts as a catchall Menu
                    wMenu.add(oMI)
        self.add(iMenu)
        if len(wMenu.get_children()) == 0:
            iMenu.set_sensitive(False)

    def doExport(self,widget):
        oFileChooser = ExportDialog("Save Physical Card List As",self.__oWindow)
        oFileChooser.run()
        sFileName = oFileChooser.getName()
        if sFileName is not None:
            oW = PhysicalCardXmlFile(sFileName)
            oW.write()

    def setApplyFilter(self,state):
        self.iApply.set_active(state)

    def toggleApply(self, oWidget):
        self.__oC.view.runFilter(oWidget.active)

    def toggleExpansion(self, oWidget):
        self.__oC.view._oModel.bExpansions = oWidget.active
        self.__oC.view.load()

    def setFilter(self, oWidget):
        self.__oC.view.getFilter(self)
