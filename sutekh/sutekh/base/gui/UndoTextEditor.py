# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# TextView Object that displays an HTML file
# Copyright 2020 Neil Muller <drnlmuller+sutekh@gmail.com>
# License: GPL - See COPYRIGHT file for details

# This is a simple editor widget for the card text properties,
# Adding a undo / redo stack and simple search functionality

"""A widget that holds a text view with a text buffer that implements
   some useful functions -- undo, redo and search."""

from gi.repository import Gtk

from .SutekhDialog import do_info_message
from .AutoScrolledWindow import AutoScrolledWindow


class SearchDialog(Gtk.Dialog):
    """Search dialog for the text view"""

    def __init__(self, oParent):
        super().__init__(title="Search", transient_for=oParent, modal=True)
        self.add_buttons("_Find", Gtk.ResponseType.OK,
                         "_Cancel", Gtk.ResponseType.CANCEL)
        self.vbox.pack_start(Gtk.Label("Enter text to search for"),
                             False, False, 0)
        self._oEntry = Gtk.Entry()
        self.vbox.pack_start(self._oEntry, True, True, 0)
        self.show_all()

    def get_text(self):
        """Get the entry text"""
        return self._oEntry.get_text()


class Insert:
    """Details of an insert text event"""

    def __init__(self, oStartIter, sText, iLen):
        self._iStartPos = oStartIter.get_offset()
        self._iLen = iLen
        self._sText = sText

    def undo(self, oBuffer):
        """undo the operation"""
        oStartIter = oBuffer.get_iter_at_offset(self._iStartPos)
        oEndIter = oBuffer.get_iter_at_offset(self._iStartPos + self._iLen)
        oBuffer.delete(oStartIter, oEndIter)
        oBuffer.place_cursor(oStartIter)
        return oBuffer.create_mark(None, oStartIter, False)

    def redo(self, oBuffer):
        """redo the operation"""
        oStartIter = oBuffer.get_iter_at_offset(self._iStartPos)
        oBuffer.insert(oStartIter, self._sText)
        oEndIter = oBuffer.get_iter_at_offset(self._iStartPos + self._iLen)
        oBuffer.place_cursor(oEndIter)
        return oBuffer.create_mark(None, oEndIter, False)


class Delete:
    """Details of a delete text event"""

    def __init__(self, oStartIter, oEndIter, sText):
        self._iStart = oStartIter.get_offset()
        self._iEnd = oEndIter.get_offset()
        self._sText = sText

    def undo(self, oBuffer):
        """undo the operation"""
        oStartIter = oBuffer.get_iter_at_offset(self._iStart)
        oBuffer.insert(oStartIter, self._sText)
        oEndIter = oBuffer.get_iter_at_offset(self._iEnd)
        oBuffer.place_cursor(oEndIter)
        return oBuffer.create_mark(None, oEndIter, False)

    def redo(self, oBuffer):
        """redo the operation"""
        oStartIter = oBuffer.get_iter_at_offset(self._iStart)
        oEndIter = oBuffer.get_iter_at_offset(self._iEnd)
        oBuffer.delete(oStartIter, oEndIter)
        oBuffer.place_cursor(oStartIter)
        return oBuffer.create_mark(None, oStartIter, False)


class UndoEditBuffer(Gtk.TextBuffer):
    """A text buffer with an automatically managed undo/redo stack"""

    def __init__(self):
        super().__init__()
        self._aUndoStack = []
        self._aRedoStack = []

        # Flag for if we're in a Undo/Redo stack
        self.bUndoRedo = False

        self.connect('insert-text', self.handle_insert_text)
        self.connect('delete-range', self.handle_delete_text)

    def handle_insert_text(self, _oBuffer, oTextIter, sText, iLen):
        """Handle the 'insert-text' signal"""
        if self.bUndoRedo:
            # In a undo / redo action, so we do nothing here
            # and just fall through to the default handler
            return
        # Clear any redo stack, as this is a new action
        self._aRedoStack = []
        oAction = Insert(oTextIter, sText, iLen)
        self._aUndoStack.append(oAction)

    def handle_delete_text(self, _oBuffer, oStartIter, oEndIter):
        """Handle the 'delete-text' signal"""
        if self.bUndoRedo:
            # In a undo / redo action, so we do nothing here and
            # just fall through to the default handler
            return
        # Clear any redo stack, as this is a new action
        self._aRedoStack = []
        sText = self.get_text(oStartIter, oEndIter, False)
        oAction = Delete(oStartIter, oEndIter, sText)
        self._aUndoStack.append(oAction)

    def undo(self):
        """Undo the last action in the undo stack"""
        if not self._aUndoStack:
            return None
        oAction = self._aUndoStack.pop()
        self._aRedoStack.append(oAction)
        self.bUndoRedo = True
        oCursorMark = oAction.undo(self)
        self.bUndoRedo = False
        return oCursorMark

    def redo(self):
        """Rodo the last action in the redo stack"""
        if not self._aRedoStack:
            return None
        oAction = self._aRedoStack.pop()
        self._aUndoStack.append(oAction)
        self.bUndoRedo = True
        oCursorMark = oAction.redo(self)
        self.bUndoRedo = False
        return oCursorMark

    def find_next(self, sText):
        """Find the next occurance of the text, looping to the start
           of the buffer if needed"""
        # Current cursor position
        oCurIter = self.get_iter_at_mark(self.get_insert())
        oEndIter = self.get_end_iter()
        oMatch = oCurIter.forward_search(sText, 0, oEndIter)
        if oMatch is None:
            # redo the search from the start to oCurIter
            oStart = self.get_start_iter()
            # We search to end to avoid issues where the cursor
            # is in the middle of the desired string
            oMatch = oStart.forward_search(sText, 0, oEndIter)

        if oMatch is None:
            do_info_message("Search string not found")
            return None

        # Match found - tuple of (start, end) iters
        self.place_cursor(oMatch[0])
        return self.create_mark(None, oMatch[0], False)


class UndoEditView(Gtk.VBox):
    """This is the edit view.

       We provide a simple toolbar and a scrollable text view for the actual
       editing operations"""

    def __init__(self, sTitle, oParent):
        super().__init__()
        self._oBuffer = UndoEditBuffer()
        self._oView = Gtk.TextView()
        self._oView.set_buffer(self._oBuffer)
        self._oToolbar = Gtk.Toolbar()
        self._oParent = oParent
        self._oToolbar.set_style(Gtk.ToolbarStyle.BOTH)
        self.pack_start(Gtk.Label(label=sTitle), False, False, 0)
        self.pack_start(self._oToolbar, False, False, 0)
        self.pack_start(AutoScrolledWindow(self._oView), True, True, 0)

        # Add toolbar items

        oUndo = Gtk.ToolButton(label="Undo")
        oUndo.set_icon_name("edit-undo")
        oUndo.connect('clicked', self.do_undo)
        oRedo = Gtk.ToolButton(label="Redo")
        oRedo.set_icon_name("edit-redo")
        oRedo.connect('clicked', self.do_redo)
        oSearch = Gtk.ToolButton(label="Find")
        oSearch.set_icon_name("edit-find")
        oSearch.connect('clicked', self.search)

        self._oToolbar.insert(oSearch, 0)
        self._oToolbar.insert(Gtk.SeparatorToolItem(), 0)
        self._oToolbar.insert(oRedo, 0)
        self._oToolbar.insert(oUndo, 0)
        # Invisible separator to Right Align toolbar menu
        oAlign = Gtk.SeparatorToolItem()
        oAlign.set_draw(False)
        oAlign.set_expand(True)
        self._oToolbar.insert(oAlign, 0)

        self._oToolbar.set_icon_size(Gtk.IconSize.SMALL_TOOLBAR)

    def set_text(self, oText):
        """Set the text in the buffer"""
        # Flag this as not undoable.
        self._oBuffer.bUndoRedo = True
        self._oBuffer.set_text('')
        if oText is not None:
            self._oBuffer.set_text(oText)
        self._oBuffer.bUndoRedo = False

    def get_all_text(self):
        """Get all the text in the buffer"""
        return self._oBuffer.get_text(self._oBuffer.get_start_iter(),
                                      self._oBuffer.get_end_iter(),
                                      False)

    def do_undo(self, _oWidget):
        """Do the undo operation"""
        oMark = self._oBuffer.undo()
        if not oMark:
            # Nothing happend, so the stack is empty
            return
        self._oView.scroll_to_mark(oMark, 0.25, False, 0, 0)
        self._oBuffer.delete_mark(oMark)

    def do_redo(self, _oWidget):
        """Do the redo operation"""
        oMark = self._oBuffer.redo()
        if not oMark:
            # Nothing happend, so the stack is empty
            return
        self._oView.scroll_to_mark(oMark, 0.25, False, 0, 0)
        self._oBuffer.delete_mark(oMark)

    def search(self, _oWidget):
        """Search for text in the buffer"""
        oDlg = SearchDialog(self._oParent)
        iRes = oDlg.run()
        if iRes == Gtk.ResponseType.OK:
            sText = oDlg.get_text()
            oMark = self._oBuffer.find_next(sText)
            if oMark:
                self._oView.scroll_to_mark(oMark, 0.25, False, 0, 0)
        oDlg.destroy()
