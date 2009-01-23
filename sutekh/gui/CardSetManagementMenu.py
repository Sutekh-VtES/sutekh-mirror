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
    def __init__(self, oFrame, oWindow, oController):
        super(CardSetManagementMenu, self).__init__(oFrame, oWindow)
        self.__sName = 'Card Set List'
        self.__sSetTypeName = 'Card Set'
        self._oController = oController
        self.__create_actions_menu()
        self.create_edit_menu()
        self.create_filter_menu()

    # pylint: disable-msg=W0201
    # called from __init__, so OK
    def __create_actions_menu(self):
        """Add the Actions Menu"""
        oMenu  = self.create_submenu(self, "_Actions")
        self.create_menu_item('Create New Card Set', oMenu,
                self._oController.create_new_card_set)
        self.create_menu_item('Edit Card Set Properties', oMenu,
                self._oController.edit_card_set_properties)
        self.create_menu_item('Mark/UnMark Card Set as in use', oMenu,
                    self._oController.toggle_in_use_flag)
        self.create_menu_item('Delete selected Card Set', oMenu,
                self._oController.delete_card_set, 'Delete')
        oMenu.add(gtk.SeparatorMenuItem())
        self.add_common_actions(oMenu)

    # pylint: enable-msg=W0201

    # pylint: disable-msg=W0613
    # oWidget required by function signature
    def toggle_apply_filter(self, oWidget):
        """Handle menu toggle events"""
        self._oController.run_filter(oWidget.active)

    def set_active_filter(self, oWidget):
        """Handle the menu activate signal"""
        self._oController.get_filter(self)

    def expand_all(self, oWidget):
        """Expand all the rows in the card set."""
        self._oController.view.expand_all()

    def collapse_all(self, oWidget):
        """Collapse all the rows in the card set."""
        self._oController.view.collapse_all()

    def show_search_dialog(self, oWidget):
        """Show the search dialog"""
        self._oController.view.searchdialog.show_all()
