# CardSetManagementMenu.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
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
        self.__sSetTypeName = sName.replace(' List', '')
        self.__dMenus = {}
        self.add_actions_menu()
        self.add_filter_menu()

    def add_actions_menu(self):
        iMenu = gtk.MenuItem("Actions")
        wMenu = gtk.Menu()
        iMenu.set_submenu(wMenu)
        self.__dMenus["Actions"] = wMenu
        iCreate = gtk.MenuItem('Create New ' + self.__sSetTypeName)
        wMenu.add(iCreate)
        iCreate.connect('activate', self.__oFrame.create_new_card_set)
        if self.__sSetTypeName == "Physical Card Set":
            iInUse = gtk.MenuItem('Mark/UnMark ' + self.__sSetTypeName + ' as in use')
            wMenu.add(iInUse)
            iInUse.connect('activate', self.__oFrame.toggle_in_use_flag)
        iDelete = gtk.MenuItem('Delete selected ' + self.__sSetTypeName)
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
        self.__dMenus["Filter"] = wMenu
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
