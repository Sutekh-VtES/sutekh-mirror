# AbstractCardListMenu.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>,
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""WW card list menu."""

import gtk

class AbstractCardListMenu(gtk.MenuBar, object):
    """Menu for the White Wolf card list (abstract card list).

       Provide actions specific to the WW card list, filtering support
       and plugins.
       """
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    def __init__(self, oFrame, oController, oWindow):
        super(AbstractCardListMenu, self).__init__()
        self.__oController = oController
        self.__oWindow = oWindow
        self.__oFrame = oFrame
        self.__dMenus = {}

        self.__create_abstract_cl_menu()
        self.__create_filter_menu()
        self.__create_plugin_menu()

    # pylint: disable-msg=W0201
    # these functions are called from __init__, so OK
    def __create_abstract_cl_menu(self):
        """Actions menu for the Abstract Card list."""
        # setup sub menu
        oMenuItem = gtk.MenuItem("Actions")
        oMenu = gtk.Menu()
        self.__dMenus["Actions"] = oMenu
        oMenuItem.set_submenu(oMenu)
        # items

        oExpand = gtk.MenuItem("Expand All (Ctrl+)")
        oMenu.add(oExpand)
        oExpand.connect("activate", self._expand_all)

        oCollapse = gtk.MenuItem("Collapse All (Ctrl-)")
        oMenu.add(oCollapse)
        oCollapse.connect("activate", self._collapse_all)

        oClose = gtk.MenuItem("Remove This Pane")
        oMenu.add(oClose)
        oClose.connect("activate", self.__oFrame.close_menu_item)

        self.add(oMenuItem)

    def __create_filter_menu(self):
        """Filter menu for WW card list."""
        # setup sub menu
        oMenuItem = gtk.MenuItem("Filter")
        oMenu = gtk.Menu()
        oMenuItem.set_submenu(oMenu)
        self.__dMenus["Filter"] = oMenu
        # items
        oFilter = gtk.MenuItem("Specify Filter")
        oMenu.add(oFilter)
        oFilter.connect('activate', self._set_active_filter)

        self.oApply = gtk.CheckMenuItem("Apply Filter")
        self.oApply.set_inconsistent(False)
        self.oApply.set_active(False)
        oMenu.add(self.oApply)
        self.oApply.connect('toggled', self._toggle_apply)
        self.add(oMenuItem)

    def __create_plugin_menu(self):
        """Plugin Menu for WW Card List."""
        # setup sub menu
        oMenuItem = gtk.MenuItem("Plugins")
        oMenu = gtk.Menu()
        self.__dMenus["Plugins"] = oMenu
        oMenuItem.set_submenu(oMenu)
        # plugins
        for oPlugin in self.__oFrame.plugins:
            oPlugin.add_to_menu(self.__dMenus, oMenu)
        self.add(oMenuItem)
        if len(oMenu.get_children()) == 0:
            oMenuItem.set_sensitive(False)

    # pylint: enable-msg=W0201

    # pylint: disable-msg=W0613
    # oWidget required by function signature
    def _toggle_apply(self, oWidget):
        """toggle the applied state of the filter."""
        self.__oController.view.run_filter(oWidget.active)

    def _set_active_filter(self, oWidget):
        """Set the active filter for the card list."""
        self.__oController.view.get_filter(self)

    def _expand_all(self, oWidget):
        """Expand all rows in the TreeView."""
        self.__oController.view.expand_all()

    def _collapse_all(self, oWidget):
        """Collapse all rows in the TreeView."""
        self.__oController.view.collapse_all()
    # pylint: enable-msg=W0613

    def set_apply_filter(self, bState):
        """Set the applied state of the filter to bState."""
        self.oApply.set_active(bState)

