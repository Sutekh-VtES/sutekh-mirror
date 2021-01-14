# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Base class for other Frames.
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Basic Card List Frame."""

from gi.repository import Gtk

from .AutoScrolledWindow import AutoScrolledWindow
from .BasicFrame import BasicFrame, pack_resizable


class CardListFrame(BasicFrame):
    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so many public methods
    """Base class for all the Card Lists.

       Provide common methods and basic parameters common to all the
       different CardList Frames.
       """

    def __init__(self, oMainWindow):
        super().__init__(oMainWindow)
        self._oConfig = oMainWindow.config_file

        # Subclasses will override these
        self._oMenu = None

    # pylint: disable=protected-access
    # We allow access via these properties
    view = property(fget=lambda self: self._oController.view,
                    doc="Associated View Object")
    menu = property(fget=lambda self: self._oMenu, doc="Frame Menu")
    type = property(fget=lambda self: self._cModelType.sqlmeta.table,
                    doc="Frame Type")
    # pylint: enable=protected-access

    def reload(self):
        """Reload frame contents"""
        # Needs to be exposed to the main window for major database changes
        self._oController.view.reload_keep_expanded()

    def get_toolbar_plugins(self):
        """Register plugins on the frame toolbar."""
        oBox = Gtk.VBox(homogeneous=False, spacing=2)
        bInsertToolbar = False
        for oPlugin in self._aPlugins:
            oWidget = oPlugin.get_toolbar_widget()
            if oWidget is not None:
                oBox.pack_start(oWidget, False, True, 0)
                bInsertToolbar = True
        if bInsertToolbar:
            oToolbar = Gtk.EventBox()
            oToolbar.add(oBox)
            self.set_drag_handler(oToolbar)
            self.set_drop_handler(oToolbar)
            oToolbar.show_all()
            return oToolbar
        return None

    def do_queued_reload(self):
        """Do a deferred reload if one was set earlier"""
        if self._bNeedReload:
            self.reload()
        self._bNeedReload = False

    def add_parts(self):
        """Add the elements to the Frame."""
        oMbox = Gtk.VBox(homogeneous=False, spacing=2)

        pack_resizable(oMbox, self._oTitle)
        pack_resizable(oMbox, self._oMenu)

        oMbox.pack_end(AutoScrolledWindow(self._oController.view),
                       True, True, 0)

        self.add(oMbox)
        self.show_all()

        # We want the toolbars be able to choose if they start visible
        # or not, so we need to call this after show_all
        oToolbar = self.get_toolbar_plugins()
        if oToolbar is not None:
            pack_resizable(oMbox, oToolbar)

        self._oController.view.load()

        self.set_drag_handler(self._oMenu)
        self.set_drop_handler(self._oMenu)
