# CardSetManagementMenu.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Menu for the CardSet View's
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Menu for the card set list"""

import gtk

class CardSetManagementMenu(gtk.MenuBar, object):
    """Card Set List Management menu.

       Allows managing the list of card sets (adding new card sets,
       opening card sets, deleting card sets) and filtering the list.
       """
    # pylint: disable-msg=R0904
    # gtk.Widget, so menu public methods
    def __init__(self, oFrame, oWindow, sName):
        super(CardSetManagementMenu, self).__init__()
        self.__oWindow = oWindow
        self.__oFrame = oFrame
        self.__sName = sName
        self.__sSetTypeName = sName.replace(' List', '')
        self.__dMenus = {}
        self.__add_actions_menu()
        self.__add_filter_menu()

    # pylint: disable-msg=W0201
    # called from __init__, so OK
    def __add_actions_menu(self):
        """Add the Actions Menu"""
        oMenuItem = gtk.MenuItem("Actions")
        oMenu = gtk.Menu()
        oMenuItem.set_submenu(oMenu)
        self.__dMenus["Actions"] = oMenu
        oCreate = gtk.MenuItem('Create New ' + self.__sSetTypeName)
        oMenu.add(oCreate)
        oCreate.connect('activate', self.__oFrame.create_new_card_set)
        if self.__sSetTypeName == "Physical Card Set":
            oInUse = gtk.MenuItem('Mark/UnMark %s as in use' %
                    self.__sSetTypeName)
            oMenu.add(oInUse)
            oInUse.connect('activate', self.__oFrame.toggle_in_use_flag)
        oDelete = gtk.MenuItem('Delete selected ' + self.__sSetTypeName)
        oMenu.add(oDelete)
        oDelete.connect('activate', self.__oFrame.delete_card_set)
        oSep = gtk.SeparatorMenuItem()
        oMenu.add(oSep)
        oClose = gtk.MenuItem('Remove This Pane')
        oMenu.add(oClose)
        oClose.connect('activate', self.__oFrame.close_menu_item)
        self.add(oMenuItem)

    def __add_filter_menu(self):
        """Add Menu for filtering the Card Set List"""
        oMenuItem = gtk.MenuItem('Filter')
        oMenu = gtk.Menu()
        self.__dMenus["Filter"] = oMenu
        oMenuItem.set_submenu(oMenu)
        oFilter = gtk.MenuItem('Specify Filter')
        oMenu.add(oFilter)
        oFilter.connect('activate', self.__oFrame.set_filter)
        self.oApply = gtk.CheckMenuItem('Apply Filter')
        self.oApply.set_inconsistent(False)
        self.oApply.set_active(False)
        oMenu.add(self.oApply)
        self.oApply.connect('toggled', self.toggle_apply)
        self.add(oMenuItem)

    # pylint: enable-msg=W0201

    def set_apply_filter(self, bState):
        """Set the filter applied status to bState"""
        self.oApply.set_active(bState)

    def get_apply_filter(self):
        """Get the filter applied state"""
        return self.oApply.active

    # pylint: disable-msg=W0613
    # oWidget required by function signature
    def toggle_apply(self, oWidget):
        """Handle menu toggle events"""
        self.__oFrame.reload()

