# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# The Card Text Frame
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Simple frame that holds a widget in a scrolled window."""

from gi.repository import Gtk
from .AutoScrolledWindow import AutoScrolledWindow
from .BasicFrame import BasicFrame, pack_resizable


class ScrolledFrame(BasicFrame):
    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so many public methods
    """Frame which holds a view in a scrolled window.

       Provides basic frame actions (drag-n-drop, focus behaviour), and
       sets names and such correctly.
       """

    _sName = 'scrolled'

    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so lots of public methods
    def __init__(self, oView, oMainWindow):
        super().__init__(oMainWindow)
        self._oView = oView
        self.add_parts()
        self.set_name(self._sName.lower())

    # pylint: disable=protected-access
    # allow access via these properties
    type = property(fget=lambda self: self._sName, doc="Frame Type")
    # pylint: enable=protected-access

    def add_parts(self):
        """Add Widget + title widgets to the Frame."""
        oBox = Gtk.VBox(homogeneous=False, spacing=2)
        self.set_title(self._sName)

        pack_resizable(oBox, self._oTitle)

        oBox.pack_start(AutoScrolledWindow(self._oView), True, True, 0)

        self.set_drop_handler(self._oView)

        self.add(oBox)
        self.show_all()

    def update_to_new_db(self):
        """Ensure we update cached results so DB changes don't cause odd
           results"""
        self._oView.update_to_new_db()

    def get_menu_name(self):
        """Get the menu key"""
        return self._sName
