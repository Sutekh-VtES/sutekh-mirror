# AbstractCardListMenu.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk

class AbstractCardListMenu(gtk.MenuBar, object):
    def __init__(self, oFrame, oController, oWindow):
        super(AbstractCardListMenu,self).__init__()
        self.__oC = oController
        self.__oWindow = oWindow
        self.__oFrame = oFrame
        self.__dMenus = {}

        self.__create_ACL_menu()
        self.__create_filter_menu()
        self.__create_plugin_menu()

    def __create_ACL_menu(self):
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

        iClose = gtk.MenuItem("Remove This Pane")
        wMenu.add(iClose)
        iClose.connect("activate", self.__oFrame.close_menu_item)

        self.add(iMenu)

    def __create_filter_menu(self):
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

    def __create_plugin_menu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("Plugins")
        wMenu = gtk.Menu()
        self.__dMenus["Plugins"] = wMenu
        iMenu.set_submenu(wMenu)
        # plugins
        for oPlugin in self.__oFrame._aPlugins:
            oMI = oPlugin.get_menu_item()
            if oMI is not None:
                sMenu = oPlugin.get_desired_menu()
                # Add to the requested menu if supplied
                if sMenu in self.__dMenus.keys():
                    self.__dMenus[sMenu].add(oMI)
                else:
                    # Plugins acts as a catchall Menu
                    wMenu.add(oMI)
        self.add(iMenu)
        if len(wMenu.get_children()) == 0:
            iMenu.set_sensitive(False)

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
