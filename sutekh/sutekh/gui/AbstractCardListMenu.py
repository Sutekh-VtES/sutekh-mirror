# AbstractCardListMenu.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>,
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""WW card list menu."""

from sutekh.gui.PaneMenu import PaneMenu

class AbstractCardListMenu(PaneMenu, object):
    """Menu for the White Wolf card list (abstract card list).

       Provide actions specific to the WW card list, filtering support
       and plugins.
       """
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    def __init__(self, oFrame, oController, oWindow):
        super(AbstractCardListMenu, self).__init__(oFrame, oWindow)

        self.__oController = oController
        self.__create_abstract_cl_menu()
        self.__create_edit_menu()
        self.create_filter_menu()
        self.create_plugins_menu()

    # pylint: disable-msg=W0201
    # these functions are called from __init__, so OK
    def __create_abstract_cl_menu(self):
        """Actions menu for the Abstract Card list."""
        # setup sub menu
        oMenu = self.create_submenu("_Actions")
        # items
        self.create_menu_item("Expand All", oMenu, self._expand_all,
                '<Ctrl>plus')
        self.create_menu_item("Collapse All", oMenu, self._collapse_all,
                '<Ctrl>minus')
        self.create_menu_item("Remove This Pane", oMenu,
                self._oFrame.close_menu_item)

    def __create_edit_menu(self):
        """Create the 'Edit' menu, and populate it."""
        oMenu = self.create_submenu("_Edit")
        self.create_menu_item('Copy selection', oMenu, self._copy_selection,
                '<Ctrl>c')

    # pylint: enable-msg=W0201

    # pylint: disable-msg=W0613
    # oWidget required by function signature
    def toggle_apply_filter(self, oWidget):
        """toggle the applied state of the filter."""
        self.__oController.view.run_filter(oWidget.active)

    def set_active_filter(self, oWidget):
        """Set the active filter for the card list."""
        self.__oController.view.get_filter(self)

    def _expand_all(self, oWidget):
        """Expand all rows in the TreeView."""
        self.__oController.view.expand_all()

    def _collapse_all(self, oWidget):
        """Collapse all rows in the TreeView."""
        self.__oController.view.collapse_all()

    def _copy_selection(self, oWidget):
        """Copy the current selection to the application clipboard."""
        self.__oController.view.copy_selection()

    # pylint: enable-msg=W0613

