# CardSetManagementMenu.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Menu for the CardSet View's
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Menu for the card set list"""

import gtk
from sutekh.gui.PaneMenu import PaneMenu

class CardSetManagementMenu(PaneMenu, object):
    """Card Set List Management menu.

       Allows managing the list of card sets (adding new card sets,
       opening card sets, deleting card sets) and filtering the list.
       """
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    def __init__(self, oFrame, oWindow, sName):
        super(CardSetManagementMenu, self).__init__(oFrame, oWindow)
        self.__sName = sName
        self.__sSetTypeName = sName.replace(' List', '')
        self.__create_actions_menu()
        self.create_filter_menu()

    # pylint: disable-msg=W0201
    # called from __init__, so OK
    def __create_actions_menu(self):
        """Add the Actions Menu"""
        oMenu  = self.create_submenu("Actions")
        self.create_menu_item('Create New %s' % self.__sSetTypeName, oMenu,
                self._oFrame.create_new_card_set)
        if self.__sSetTypeName == "Physical Card Set":
            self.create_menu_item(
                    'Mark/UnMark %s as in use' % self.__sSetTypeName, oMenu,
                    self._oFrame.toggle_in_use_flag)
        self.create_menu_item('Delete selected %s' % self.__sSetTypeName,
                oMenu, self._oFrame.delete_card_set, 'Delete')
        oMenu.add(gtk.SeparatorMenuItem())
        self.create_menu_item("Remove This Pane", oMenu,
                self._oFrame.close_menu_item)

    # pylint: enable-msg=W0201

    # pylint: disable-msg=W0613
    # oWidget required by function signature
    def toggle_apply_filter(self, oWidget):
        """Handle menu toggle events"""
        self._oFrame.reload()

    def set_active_filter(self, oWidget):
        """Handle the menu activate signal"""
        self._oFrame.set_filter()

