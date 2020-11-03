# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# TextView Object that displays an HTML file
# Copyright 2020 Neil Muller <drnlmuller+sutekh@gmail.com>
# License: GPL - See COPYRIGHT file for details

# This is a simple editor widget for the card text properties,
# Adding a undo / redo stack and simple search functionality

from gi.repository import Gtk

from .AutoScrolledWindow import AutoScrolledWindow


class Insert:
    """Details of an insert text event"""

    def __init__(self):
        pass

    def undo(self, oBuffer):
        """undo the operation"""

    def redo(self, oBuffer):
        """redo the operation"""


class Delete:
    """Details of a delete text event"""

    def __init__(self):
        pass

    def undo(self, oBuffer):
        """undo the operation"""

    def redo(self, oBuffer):
        """redo the operation"""


class UndoEditBuffer(Gtk.TextBuffer):

    def __init__(self):
        super().__init__()
        self.aUndoStack = []
        self.aRedoStack = []


class UndoEditView(Gtk.VBox):
    """This is the edit view.

       We provide a simple toolbar and a scrollable text view for the actual
       editing operations"""

    def __init__(self, sTitle):
        super().__init__()
        self._oBuffer = UndoEditBuffer()
        self._oView = Gtk.TextView()
        self._oView.set_buffer(self._oBuffer)
        self._oToolbar = Gtk.Toolbar()
        self._oToolbar.set_no_show_all(True)
        self._oToolbar.set_style(Gtk.ToolbarStyle.BOTH)
        self.pack_start(Gtk.Label(label=sTitle), False, False, 0)
        self.pack_start(self._oToolbar, False, False, 0)
        self.pack_start(AutoScrolledWindow(self._oView), True, True, 0)

    def set_text(self, oText):
        self._oBuffer.set_text(oText)

    def get_all_text(self):
        return self._oBuffer.get_text(self._oBuffer.get_start_iter(),
                                      self._oBuffer.get_end_iter(),
                                      False)
