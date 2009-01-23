# PaneMenu.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Base class for the frame menu's
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Base class for the pane menus"""

from sutekh.gui.SutekhMenu import SutekhMenu

class PaneMenu(SutekhMenu):
    # pylint: disable-msg=R0904, R0922
    # R0904 - gtk.Widget, so many public methods
    # R0922 - we use this in other files
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
        self.create_menu_item("_Specify Filter", oMenu, self.set_active_filter,
                '<Ctrl>s')
        self.oApply = self.create_check_menu_item("_Apply Filter", oMenu,
                self.toggle_apply_filter, False, "<Ctrl>t")
        self.oApply.set_inconsistent(False)

    def create_edit_menu(self):
        """Create the 'Edit' menu, and populate it."""
        oMenu = self.create_submenu(self, "_Edit")
        self.add_edit_menu_actions(oMenu)

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

    def add_common_actions(self, oMenu):
        """Actions common to all card lists"""
        self.create_menu_item("Expand All", oMenu, self.expand_all,
                '<Ctrl>plus')
        self.create_menu_item("Collapse All", oMenu, self.collapse_all,
                '<Ctrl>minus')

    def add_edit_menu_actions(self, oMenu):
        """Add the search item to the Edit Menu."""
        self.create_menu_item('_Search', oMenu, self.show_search_dialog,
                '<Ctrl>f')

    def expand_all(self, oWidget):
        """Expand all the rows in the card set."""
        raise NotImplementedError

    def collapse_all(self, oWidget):
        """Collapse all the rows in the card set."""
        raise NotImplementedError

    def show_search_dialog(self, oWidget):
        """Show the search dialog"""
        raise NotImplementedError

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

    def show_search_dialog(self, oWidget):
        """Show the search dialog"""
        self._oController.view.searchdialog.show_all()

