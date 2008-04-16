# PaneMenu.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Base class for the frame menu's
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Base class for the pane menus"""

import gtk

class PaneMenu(gtk.MenuBar, object):
    # pylint: disable-msg=R0904, R0921
    # R0904 - gtk.Widget, so many public methods
    # R0921 - we use this class, but not in this file
    """Base class for Menus

       This provides handling for enabling and disabling the menus
       ability to recieve acceleraotrs on focus changes.
       """
    def __init__(self, oFrame, oWindow):
        super(PaneMenu, self).__init__()
        self._oFrame = oFrame
        self._dMenus = {}
        self._bAccelActive = False
        self._oMainWindow = oWindow
        self._oAccelGroup = gtk.AccelGroup()
        self.oApply = None

    # TODO: disable / enable mnemonics as well
    def activate_accels(self):
        """Add the accelerator group for this menu from the main window"""
        if self._bAccelActive:
            return
        self._oMainWindow.add_accel_group(self._oAccelGroup)
        self._bAccelActive = True

    def remove_accels(self):
        """Remove the accelerator group for this menu from the main window"""
        if not self._bAccelActive:
            return
        self._oMainWindow.remove_accel_group(self._oAccelGroup)
        self._bAccelActive = False

    def _add_accel(self, oMenuItem, sAccelKey):
        """Parse a accelerator description & add it to the menu item"""
        (iKeyVal, iMod) = gtk.accelerator_parse(sAccelKey)
        if iKeyVal != 0:
            oMenuItem.add_accelerator('activate', self._oAccelGroup,
                iKeyVal, iMod, gtk.ACCEL_VISIBLE)

    def create_menu_item(self, sName, oMenu, fAction, sAccelKey=None):
        """Utiltiy function for creatng menu items.

           Create a menu item, connect it to fAction (if not None), and
           add an accelerator if specified."""
        oMenuItem = gtk.MenuItem(sName)
        oMenu.add(oMenuItem)
        if fAction:
            oMenuItem.connect('activate', fAction)
        if sAccelKey:
            self._add_accel(oMenuItem, sAccelKey)
        return oMenuItem

    # pylint: disable-msg=R0913
    # We need all the arguments here
    def create_check_menu_item(self, sName, oMenu, fAction, bState=False,
            sAccelKey=None):
        """Utiltiy function for creatng check menu items.

           Create a menu item, connect it to fAction (if not None), and
           add an accelerator if specified."""
        oMenuItem = gtk.CheckMenuItem(sName)
        oMenu.add(oMenuItem)
        oMenuItem.set_inconsistent(False)
        oMenuItem.set_active(bState)
        if fAction:
            oMenuItem.connect('toggled', fAction)
        if sAccelKey:
            self._add_accel(oMenuItem, sAccelKey)
        return oMenuItem

    # pylint: enable-msg=R0913

    def _create_menu_item_with_submenu(self, sName):
        """Create a MenuItme and a submenu, returning the menu_item"""
        oMenuItem = gtk.MenuItem(sName)
        oMenu = gtk.Menu()
        self._dMenus[sName] = oMenu
        oMenuItem.set_submenu(oMenu)
        self.add(oMenuItem)
        return oMenuItem

    def create_submenu(self, sName):
        """Create a submenu, and add it to the menu dictionary,
           returning the submenu"""
        # TODO: handle mnemonics in the menu name
        oMenuItem = self._create_menu_item_with_submenu(sName)
        return oMenuItem.get_submenu()

    def create_plugins_menu(self):
        """Create the plugins menu, adding the plugins from the frame."""
        oMenuItem = self._create_menu_item_with_submenu("Plugins")
        oMenu = oMenuItem.get_submenu()
        for oPlugin in self._oFrame.plugins:
            oPlugin.add_to_menu(self._dMenus, oMenu)
        if len(oMenu.get_children()) == 0:
            oMenuItem.set_sensitive(False)

    def create_filter_menu(self):
        """Create the Filter Menu."""
        oMenu = self.create_submenu("Filter")
        oFilter = gtk.MenuItem("Specify Filter")
        oMenu.add(oFilter)
        oFilter.connect('activate', self.set_active_filter)
        self.oApply = gtk.CheckMenuItem("Apply Filter")
        self.oApply.set_inconsistent(False)
        self.oApply.set_active(False)
        oMenu.add(self.oApply)
        self.oApply.connect('toggled', self.toggle_apply_filter)

    def set_active_filter(self, oWidget):
        """Abstract method to handle filter request events."""
        raise NotImplementedError

    def toggle_apply_filter(self, oWidget):
        """Abstract method to handle checkbox events."""
        raise NotImplementedError

    def set_apply_filter(self, bState):
        """Set the applied filter state to bState."""
        self.oApply.set_active(bState)

    def get_apply_filter(self):
        """Get the filter applied state"""
        return self.oApply.active

