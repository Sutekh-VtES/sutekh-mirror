# MultiSelectComboBox.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Generic multiselect combobox for use in FilterEditor (and elsewhere)"""

import gtk
import sys
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.gui.ScrolledList import ScrolledListView


def mouse_in_button(oButton):
    """Check if mouse pointer is inside the button"""
    (iXPos, iYPos) = oButton.get_pointer()  # mouse pos relative to button
    oButtonGeom = oButton.allocation
    return (iXPos >= 0) and (iYPos >= 0) and \
            (iXPos < oButtonGeom.width) and (iYPos < oButtonGeom.height)


class MultiSelectComboBox(gtk.HBox):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """Implementation of a multiselect combo box widget."""

    def __init__(self, oParentWin):
        super(MultiSelectComboBox, self).__init__()

        self._oButton = gtk.Button(" - ")
        self._oButton.connect('clicked', self.__show_list)
        self.pack_start(self._oButton)

        self._oTreeView = ScrolledListView(" ... ")
        self._oTreeView.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

        oScrolled = AutoScrolledWindow(self._oTreeView)
        self._aOldSelection = []

        self._oDialog = gtk.Dialog("Select ...", None,
                gtk.DIALOG_MODAL | gtk.DIALOG_NO_SEPARATOR |
                gtk.DIALOG_DESTROY_WITH_PARENT)
        self._oDialog.set_decorated(False)
        # pylint: disable-msg=E1101
        # action_area, vbox confuses pylint
        self._oDialog.action_area.set_size_request(-1, 0)
        self._oDialog.vbox.pack_start(oScrolled)
        self._oDialog.connect('key-press-event', self.__hide_on_return)
        # Catch tail of the event queue to handle pressing to close
        self._oDialog.connect('event-after', self.__grab_event)

        self._bInButton = False
        self._oParentWin = oParentWin

    def __grab_event(self, _oWidget, oEvent):
        """Hook into the event-after chain, so we can check if any uncaught
           events refer to the original button."""
        # This is a bit convuluted, but seems the best
        # we can do.
        # If the popup dialog isn't modal, it can't reliably receive focus, and
        # there are undesireable interactions with the default keybindings on
        # the parent dialog.
        # If it's modal, the button can't catch any events. Thus we fake
        # limited non-modality here by testing for each event of interest
        # ourselves. This will all go away if the popup is redone as a
        # widget, rather than as a tweaked dialog window
        if oEvent.type == gtk.gdk.BUTTON_PRESS or (
                sys.platform.startswith("win") and
                oEvent.type == gtk.gdk.BUTTON_RELEASE):
            # Mouse clicked
            if oEvent.button == 1:
                if mouse_in_button(self._oButton):
                    # Left button
                    self.__hide_list()
                # Ignore other buttons
                # Should right button act the same as escape?
        elif oEvent.type == gtk.gdk.ENTER_NOTIFY:
            # Mouse has entered the button, so mark as active
            if mouse_in_button(self._oButton):
                self._bInButton = True
                self._oButton.set_state(gtk.STATE_PRELIGHT)
        elif oEvent.type == gtk.gdk.LEAVE_NOTIFY and self._bInButton:
            # Leave the button, so unhighlight
            self._bInButton = False
            self._oButton.set_state(gtk.STATE_NORMAL)
        # always propogate events onward, which should be completely
        # safe, since we're in event-after
        return False

    def __show_list(self, _oButton):
        """Drop down the list of possible selections."""
        self._aOldSelection = self.get_selection()

        oParent = self.get_parent_window()

        tWinPos = oParent.get_origin()
        # Need coordinates relative to root window
        # pylint: disable-msg=E1101
        # allocation confuses pylint
        tButtonPos = (self._oButton.allocation.x, self._oButton.allocation.y)
        tShift = (5, self._oButton.allocation.height)

        tDialogPos = (tWinPos[0] + tButtonPos[0] + tShift[0],
                tWinPos[1] + tButtonPos[1] + tShift[1])

        self._oDialog.set_keep_above(True)  # Keep this above the dialog
        self._oDialog.set_transient_for(self._oParentWin)
        self._oDialog.show_all()
        # WM behaviour means that move is unlikely to work before _oDialog
        # is shown
        self._oDialog.move(tDialogPos[0], tDialogPos[1])
        self._bInButton = False

    def __hide_on_return(self, _oWidget, oEvent):
        """Hide the list when return or escape is pressed."""
        if oEvent.type is gtk.gdk.KEY_PRESS:
            sKeyName = gtk.gdk.keyval_name(oEvent.keyval)
            if sKeyName in ('Return', 'Escape'):
                if sKeyName == 'Escape':
                    self.set_selected_rows(self._aOldSelection)
                self.__hide_list()
                return True  # event handled
        return False  # process further

    def __hide_list(self):
        """Hide the list of options"""
        self._oDialog.hide_all()
        self.__update_button_text()

    def __update_button_text(self):
        """Update the text to reflect the selected items."""
        aSelection = self.get_selection()
        if aSelection:
            self._oButton.set_label(", ".join(aSelection))
        else:
            self._oButton.set_label(" - ")

    def fill_list(self, aVals):
        """Fill the list store with the given values"""
        self._oTreeView.store.fill_list(aVals)

    def set_list_size(self, iWidth, iHeight):
        """Set size of the drop-down list"""
        self._oDialog.set_size_request(iWidth, iHeight)

    def set_sensitive(self, bValue):
        """Control the sensitivity of the button"""
        self._oButton.set_sensitive(bValue)

    def get_selection(self):
        """Return a list of the selected elements of the list"""
        return self._oTreeView.get_selected_data()

    def set_selected_rows(self, aRowsToSelect):
        """Set the selected rows in the drop-down to aRowsToSelect"""
        self._oTreeView.set_selected_rows(aRowsToSelect)
