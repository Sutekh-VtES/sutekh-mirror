# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Base class for other Frames.
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Base class for Sutekh Frames"""

import gtk
import gobject

from .ScrolledFrame import ScrolledFrame
from .LogTextView import LogTextView


class LogViewFrame(ScrolledFrame):
    # pylint: disable=too-many-public-methods
    # gtk.Widget, so many public methods
    # pylint: disable=property-on-old-class
    # gtk classes aren't old-style, but pylint thinks they are
    """The frame holding the log message view.

       The LogHandler is created by the main window, so it's
       there from the start, not tied to this frame.
       """

    _sName = 'Log View Frame'

    def __init__(self, oMainWindow):
        oView = LogTextView()
        super(LogViewFrame, self).__init__(oView, oMainWindow)
        self.set_name("log frame")

        self.set_title('Log Messages View')
        oMainWindow.gui_log_handler.set_widget(self)

    def reload(self):
        """Reload frame contents"""
        self._oView.set_log_messages(self._oMainWindow.gui_log_handler.aQueue)

    def do_queued_reload(self):
        """Do a deferred reload if one was set earlier"""
        self._bNeedReload = False
        self.reload()

    def cleanup(self, bQuit=False):
        """Cleanup reference held in the log handler"""
        self._oMainWindow.gui_log_handler.unset_widget()
        super(LogViewFrame, self).cleanup(bQuit)
