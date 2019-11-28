# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2019 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Widget for displaying the card text for the given card."""

import logging

import gtk
import pango


class LogTextBuffer(gtk.TextBuffer):
    """Text buffer for displaying log messages.
       """

    # pylint: disable=too-many-public-methods
    # gtk.Widget, so many public methods
    def __init__(self):
        super(LogTextBuffer, self).__init__(None)

    def clear(self):
        """Clear all messages"""
        oStart, oEnd = self.get_bounds()
        self.delete(oStart, oEnd)

    def add_message(self, sMessage):
        oEnd = self.get_end_iter()
        self.insert(oEnd, sMessage)
        self.insert(oEnd, '\n')

    def get_all_text(self):
        oStart, oEnd = self.get_bounds()
        return self.get_text(oStart, oEnd)


class LogTextView(gtk.TextView):
    """TextView widget which holds the LogTextBuffer."""

    # pylint: disable=too-many-public-methods
    # gtk.Widget, so many public methods
    # pylint: disable=property-on-old-class
    # gtk classes aren't old-style, but pylint thinks they are
    def __init__(self):
        super(LogTextView, self).__init__()
        # Can be styled as frame_name.view
        self._oBuf = LogTextBuffer()
        # Reference to top level so we can get config info and so on
        self.set_buffer(self._oBuf)
        self.set_editable(False)
        self.set_cursor_visible(False)
        self.set_wrap_mode(gtk.WRAP_WORD)
        self._iFilterLevel = logging.NOTSET

    def set_log_messages(self, aMessages):
        """Populate the TextBuffer with the messages, honouring
           the filter level"""
        self._oBuf.clear()
        for tMessage in aMessages:
            if tMessage[0] >= self._iFilterLevel:
                self._oBuf.add_message(tMessage[1])

    def export_bufffer(self, oFile):
        """Export all the text from the buffer to the given file object"""
        sData = self._oBuf.get_all_text()
        oFile.write(sData)

    def set_filter_level(self, iNewLevel):
        """Update the filter level."""
        self._iFilterLevel = iNewLevel
