# AbstractCardListMenu.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sqlobject import sqlhub, connectionForURI
from sutekh.core.SutekhObjects import PhysicalCardSet, AbstractCardSet, ObjectList
from sutekh.gui.ImportDialog import ImportDialog
from sutekh.gui.WWFilesDialog import WWFilesDialog
from sutekh.io.XmlFileHandling import PhysicalCardXmlFile, PhysicalCardSetXmlFile, \
                                    AbstractCardSetXmlFile
from sutekh.io.IdentifyXMLFile import IdentifyXMLFile
from sutekh.core.DatabaseUpgrade import copyToNewAbstractCardDB, createFinalCopy
from sutekh.SutekhUtility import refreshTables, readWhiteWolfList, readRulings
from sutekh.io.ZipFileWrapper import ZipFileWrapper

class AbstractCardListMenu(gtk.MenuBar, object):
    def __init__(self, oFrame, oController, oWindow):
        super(AbstractCardListMenu,self).__init__()
        self.__oC = oController
        self.__oWindow = oWindow
        self.__oFrame = oFrame
        self.__dMenus = {}

        self.__createACLMenu()
        self.__createFilterMenu()
        self.__createPluginMenu()

    def __createACLMenu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("Abstract Card List Actions")
        wMenu = gtk.Menu()
        self.__dMenus["ACS"] = wMenu
        iMenu.set_submenu(wMenu)
        # items

        iExpand = gtk.MenuItem("Expand All (Ctrl+)")
        wMenu.add(iExpand)
        iExpand.connect("activate", self.expand_all)

        iCollapse = gtk.MenuItem("Collapse All (Ctrl-)")
        wMenu.add(iCollapse)
        iCollapse.connect("activate", self.collapse_all)

        iClose = gtk.MenuItem("Close List")
        wMenu.add(iClose)
        iClose.connect("activate", self.close_list)

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

    def close_list(self, widget):
        self.__oFrame.close_frame()

    def setApplyFilter(self,state):
        self.iApply.set_active(state)

    def toggleApply(self, oWidget):
        self.__oC.view.runFilter(oWidget.active)

    def setFilter(self, oWidget):
        self.__oC.view.getFilter(self)

    def expand_all(self, oWidget):
        self.__oC.view.expand_all()

    def collapse_all(self, oWidget):
        self.__oC.view.collapse_all()
