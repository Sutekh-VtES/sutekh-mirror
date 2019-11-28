# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2019 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Widget for displaying the card text for the given card."""

import gtk
import pango


class LogTextBuffer(gtk.TextBuffer):
    """Text buffer for displaying log messages.
       """

    # pylint: disable=too-many-public-methods
    # gtk.Widget, so many public methods
    def __init__(self):
        super(LogTextBuffer, self).__init__(None)


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

    def set_log_messages(self, aMessages):
        print("set_log_messages called")
        print("With", aMessages)
