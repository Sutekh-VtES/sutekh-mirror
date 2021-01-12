# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Base class for other Frames.
# Copyright 2019 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Base class for Sutekh Frames"""

from gi.repository import Gtk

from .AutoScrolledWindow import AutoScrolledWindow
from .BasicFrame import BasicFrame, pack_resizable
from .LogViewMenu import LogViewMenu
from .LogTextView import LogTextView


class LogViewFrame(BasicFrame):
    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so many public methods
    """The frame holding the log message view.

       The LogHandler is created by the main window, so it's
       there from the start, not tied to this frame.
       """

    _sName = 'Log View Frame'

    def __init__(self, oMainWindow):
        super().__init__(oMainWindow)
        self.set_name("log frame")
        self._oView = LogTextView()
        self._oMenu = LogViewMenu(self, oMainWindow)

        self.set_title('Log Messages View')

        self.add_parts()

        oMainWindow.gui_log_handler.set_widget(self)

    # pylint: disable=protected-access
    # explicitly allow access to these values via thesep properties
    type = property(fget=lambda self: self._sName, doc="Frame Type")
    view = property(fget=lambda self: self._oView, doc="View")
    # pylint: enable=protected-access

    def reload(self):
        """Reload frame contents"""
        self._oView.set_log_messages(self._oMainWindow.gui_log_handler.aQueue)

    def do_queued_reload(self):
        """Do a deferred reload if one was set earlier"""
        self._bNeedReload = False
        self.reload()

    def add_parts(self):
        """Add the menu and text view to the frame"""
        oMbox = Gtk.VBox(homogeneous=False, spacing=2)

        pack_resizable(oMbox, self._oTitle)
        pack_resizable(oMbox, self._oMenu)
        oMbox.pack_end(AutoScrolledWindow(self._oView), True, True, 0)

        self.add(oMbox)
        self.show_all()

        self.set_drag_handler(self._oMenu)
        self.set_drop_handler(self._oMenu)

    def cleanup(self, bQuit=False):
        """Cleanup reference held in the log handler"""
        self._oMainWindow.gui_log_handler.unset_widget()
        super().cleanup(bQuit)

    def get_menu_name(self):
        """Get the menu key"""
        return self._sName

    def set_filter_level(self, iNewLevel):
        """Set the filter level and reload the messages"""
        self._oView.set_filter_level(iNewLevel)
        self.reload()
