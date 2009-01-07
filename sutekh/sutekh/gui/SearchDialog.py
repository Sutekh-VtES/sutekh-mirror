# SearchDialog.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Special search dialog for the TreeViews for displaying the card list.

   This is designed to avoid issues with the default TreeView search on
   windows with gtk 2.12"""

import gtk
import sys

class SearchDialog(gtk.Window):
    # pylint: disable-msg=R0904
    # gtk Widget, so many public methods
    """Mini dialog that contains a gtk.Entry item for handling card
       searches"""

    def __init__(self, oView, oWin):
        super(SearchDialog, self).__init__()
        self._oView = oView
        self._oWin = oWin
        self.set_transient_for(oWin)
        # We want the WM to ignore this window - this looks the best choice
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_MENU)
        self.set_modal(True)
        self.set_decorated(False)
        oFrame = gtk.Frame()
        self.oEntry = gtk.Entry(30)
        self.oEntry.set_has_frame(True)
        self.oEntry.set_inner_border(None)
        self.set_flags(gtk.CAN_FOCUS)

        oAlign = gtk.Alignment()
        oAlign.set_padding(3, 3, 3, 3)
        oAlign.add(self.oEntry)
        oFrame.add(oAlign)
        self.add(oFrame)
        self.connect('key-press-event', self._key_press)
        self.oEntry.connect('activate', lambda x: self.hide())
        # Work around wierd windows behaviour where the button-press-event
        # doesn't get delivered to us
        if sys.platform.startswith("win"):
            self.connect('button-release-event', self.check_hide)
        else:
            self.connect('button-press-event', self.check_hide)
        self.set_focus_on_map(True)
        # Hook up to the View
        oView.set_search_entry(self.oEntry)
        oView.set_enable_search(False)
        # Key combination for searching
        oView.connect_after('key-press-event',
                self.treeview_key_press_event)

    def set_text(self, sString):
        """Set the contents of the entry to sString"""
        self.oEntry.set_text(sString)
        self.oEntry.set_position(1)

    def hide(self):
        """Hide the window"""
        super(SearchDialog, self).hide()

    # pylint: disable-msg=W0613
    # Various arguments required by function signatures
    def _key_press(self, oWidget, oEvent):
        """Hide the dialog on escape"""
        if oEvent.keyval == gtk.gdk.keyval_from_name('Escape'):
            self.hide()
            return True
        return False # propogate event

    def check_hide(self, oWidget, oEvent):
        """Check if we need to hide the dialog"""
        # pylint: disable-msg=E1101
        # allocation confuses pylint
        (iXPos, iYPos) = self.get_pointer()
        oGeom = self.allocation
        if (iXPos < 0) or (iYPos < 0) or (iXPos > oGeom.width) or \
                (iYPos > oGeom.height):
            # Button event outside the dialog, so hide
            self.hide()

    def show_all(self):
        """Move the window into position when shown"""
        oWin = self._oView.get_bin_window()
        tWinPos = oWin.get_origin()
        tViewSize = oWin.get_size()
        # We first move totally off-screen, then show so we
        # can get our size
        # This is basically the same approach as the default gtk search
        # dialog takes, so we more-or-less duplicate it's behaviour
        oScreen = self._oView.get_screen()
        self.move(oScreen.get_width() + tViewSize[0],
                oScreen.get_height() +  tViewSize[1])
        super(SearchDialog, self).show_all()
        oThisWinAlloc = self.get_allocation()
        iXPos = tWinPos[0] + tViewSize[0] - oThisWinAlloc.width
        iYPos = tWinPos[1] + tViewSize[1]
        # Special case limits as gtk does
        if iXPos < 0:
            iXPos = 0
        elif iXPos + oThisWinAlloc.width > oScreen.get_width():
            iXPos = oScreen.get_width() - oThisWinAlloc.width
        if iYPos < 0:
            iYPos = 0
        elif iYPos + oThisWinAlloc.height > oScreen.get_height():
            iYPos = oScreen.get_height() - oThisWinAlloc.height
        self.move(iXPos, iYPos)
        self._oWin.set_focus(self.oEntry)
        self.oEntry.grab_focus()
        # Force the widget to be focus - probablity unsure
        self.oEntry.set_flags(gtk.HAS_FOCUS)

    # key press for searching in the tree view

    def treeview_key_press_event(self, oWidget, oEvent):
        """Handle key press events, so we display a search box with
           entry completion."""
        if oEvent.keyval in range(33, 127):
            self.show_all()
            if len(oEvent.string) > 0:
                # Add text to search dialog
                self.set_text(oEvent.string)
        # connect_after, so everything else has had it's shot
        return True

