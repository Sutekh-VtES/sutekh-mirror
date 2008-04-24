# AbstractCardListMenu.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>,
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""WW card list menu."""

from sutekh.gui.PaneMenu import CardListMenu

class AbstractCardListMenu(CardListMenu):
    """Menu for the White Wolf card list (abstract card list).

       Provide actions specific to the WW card list, filtering support
       and plugins.
       """
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    def __init__(self, oFrame, oController, oWindow):
        super(AbstractCardListMenu, self).__init__(oFrame, oWindow,
                oController)

        self.__create_abstract_cl_menu()
        self.create_edit_menu()
        self.create_filter_menu()
        self.create_plugins_menu('_Plugins', self._oFrame)

    # pylint: disable-msg=W0201
    # these functions are called from __init__, so OK
    def __create_abstract_cl_menu(self):
        """Actions menu for the Abstract Card list."""
        # setup sub menu
        oMenu = self.create_submenu(self, "_Actions")
        # items
        self.add_common_actions(oMenu)

    def create_edit_menu(self):
        """Create the 'Edit' menu, and populate it."""
        oMenu = self.create_submenu(self, "_Edit")
        self.create_menu_item('Copy selection', oMenu, self.copy_selection,
                '<Ctrl>c')

    # pylint: enable-msg=W0201
