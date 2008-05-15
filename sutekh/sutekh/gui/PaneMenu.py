# PaneMenu.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Base class for the frame menu's
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Base class for the pane menus"""

import gtk
from sutekh.gui.SutekhMenu import SutekhMenu

class PaneMenu(SutekhMenu):
    # pylint: disable-msg=R0904
    # R0904 - gtk.Widget, so many public methods
    """Base class for individual Frame menus

       This provides handling for enabling and disabling the menus
       ability to recieve acceleraotrs on focus changes.
       """
    def __init__(self, oFrame, oWindow):
        super(PaneMenu, self).__init__(oWindow)
        self._oFrame = oFrame
        self.oApply = None

    def create_filter_menu(self):
        """Create the Filter Menu."""
        oMenu = self.create_submenu(self, "F_ilter")
        oFilter = gtk.MenuItem("_Specify Filter")
        oMenu.add(oFilter)
        oFilter.connect('activate', self.set_active_filter)
        self.oApply = gtk.CheckMenuItem("_Apply Filter")
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

class CardListMenu(PaneMenu):
    # pylint: disable-msg=R0904
    # R0904 - gtk.Widget, so many public methods
    """Base class for Card List Menus

       Adds some common methods for dealing with the card lists -
       copying selections, expanding + collapsing rows, etc.
       """
    def __init__(self, oFrame, oWindow, oController):
        super(CardListMenu, self).__init__(oFrame, oWindow)
        self._oController = oController

    def add_common_actions(self, oMenu):
        """Actions common to all card lists"""
        self.create_menu_item("Expand All", oMenu, self.expand_all,
                '<Ctrl>plus')
        self.create_menu_item("Collapse All", oMenu, self.collapse_all,
                '<Ctrl>minus')
        self.create_menu_item("Remove This Pane", oMenu,
                self._oFrame.close_menu_item)

    # pylint: disable-msg=W0613
    # oWidget required by function signature for the following methods
    def toggle_apply_filter(self, oWidget):
        """Toggle the filter applied state."""
        self._oController.view.run_filter(oWidget.active)

    def set_active_filter(self, oWidget):
        """Set the current filter for the card set."""
        self._oController.view.get_filter(self)

    def expand_all(self, oWidget):
        """Expand all the rows in the card set."""
        self._oController.view.expand_all()

    def collapse_all(self, oWidget):
        """Collapse all the rows in the card set."""
        self._oController.view.collapse_all()

    def copy_selection(self, oWidget):
        """Copy the current selection to the application clipboard."""
        self._oController.view.copy_selection()

