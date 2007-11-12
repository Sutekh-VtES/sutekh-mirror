# CardSetMenu.py
# Menu for the CardSet View's
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk

class CardSetManagementMenu(gtk.MenuBar, object):
    def __init__(self, oFrame, oWindow, sName):
        super(CardSetManagementMenu, self).__init__()
        self.__oWindow = oWindow
        self.__oFrame = oFrame
        self.__sName = sName
        self.__sSetName = sName.replace(' List', '')
        self.add_actions_menu()
        self.add_filter_menu()

    def add_actions_menu(self):
        iMenu = gtk.MenuItem(self.__sName + ' Actions')
        wMenu = gtk.Menu()
        iMenu.set_submenu(wMenu)
        iCreate = gtk.MenuItem('Create New ' + self.__sSetName)
        wMenu.add(iCreate)
        iCreate.connect('activate', self.__oFrame.create_new_card_set)
        iDelete = gtk.MenuItem('Delete selected ' + self.__sSetName)
        wMenu.add(iDelete)
        iDelete.connect('activate', self.__oFrame.delete_card_set)
        iSep = gtk.SeparatorMenuItem()
        wMenu.add(iSep)
        iClose = gtk.MenuItem('Remove This Pane')
        wMenu.add(iClose)
        iClose.connect('activate', self.__oFrame.close_menu_item)
        self.add(iMenu)

    def add_filter_menu(self):
        iMenu = gtk.MenuItem('Filter')
        wMenu = gtk.Menu()
        iMenu.set_submenu(wMenu)
        iFilter = gtk.MenuItem('Specify Filter')
        wMenu.add(iFilter)
        iFilter.connect('activate', self.__oFrame.set_filter)
        self.iApply = gtk.CheckMenuItem('Apply Filter')
        self.iApply.set_inconsistent(False)
        self.iApply.set_active(False)
        wMenu.add(self.iApply)
        self.iApply.connect('toggled', self.toggle_apply)
        self.add(iMenu)

    def toggle_apply(self, oWidget):
        self.__oFrame.reload()

    def set_apply_filter(self, bState):
        self.iApply.set_active(bState)

    def get_apply_filter(self):
        return self.iApply.active
