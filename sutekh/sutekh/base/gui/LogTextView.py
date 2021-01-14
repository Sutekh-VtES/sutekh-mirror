# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2019 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Widget for displaying the card text for the given card."""

import logging

from gi.repository import Gtk


class LogTextBuffer(Gtk.TextBuffer):
    """Text buffer for displaying log messages.
       """

    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so many public methods
    def clear(self):
        """Clear all messages"""
        oStart, oEnd = self.get_bounds()
        self.delete(oStart, oEnd)

    def add_message(self, sMessage):
        """Append a message to the log"""
        oEnd = self.get_end_iter()
        self.insert(oEnd, sMessage)
        self.insert(oEnd, '\n')

    def get_all_text(self):
        """Get everything shown in the buffer"""
        oStart, oEnd = self.get_bounds()
        # This should be unicode
        return self.get_text(oStart, oEnd, False)


class LogTextView(Gtk.TextView):
    """TextView widget which holds the LogTextBuffer."""

    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so many public methods
    def __init__(self):
        super().__init__()
        # Can be styled as frame_name.view
        self._oBuf = LogTextBuffer()
        # Reference to top level so we can get config info and so on
        self.set_buffer(self._oBuf)
        self.set_editable(False)
        self.set_cursor_visible(False)
        self.set_wrap_mode(Gtk.WrapMode.WORD)
        self._iFilterLevel = logging.NOTSET

    def set_log_messages(self, aMessages):
        """Populate the TextBuffer with the messages, honouring
           the filter level"""
        self._oBuf.clear()
        for tMessage in aMessages:
            if tMessage[0] >= self._iFilterLevel:
                self._oBuf.add_message(tMessage[1])

    def export_buffer(self, oFile):
        """Export all the text from the buffer to the given file object"""
        sData = self._oBuf.get_all_text()
        oFile.write(sData.encode('utf8'))

    def save_to_file(self, sFileName):
        """Handling opening a file and passing it to _export_buffer"""
        if sFileName:
            # We've already checked for permission to overwrite
            with open(sFileName, 'wb') as oFile:
                self.export_buffer(oFile)

    def set_filter_level(self, iNewLevel):
        """Update the filter level."""
        self._iFilterLevel = iNewLevel
