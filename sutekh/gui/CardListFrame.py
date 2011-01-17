# CardListFrame.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Base class for other Frames.
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Basic Card List Frame."""

import gtk
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.gui.BasicFrame import BasicFrame


class CardListFrame(BasicFrame):
    # pylint: disable-msg=R0904
    # gtk.Widget, so lots of public methods
    """Base class for all the Card Lists.

       Provide common methods and basic parameters common to all the
       different CardList Frames.
       """

    def __init__(self, oMainWindow):
        super(CardListFrame, self).__init__(oMainWindow)
        self._oConfig = oMainWindow.config_file

        # Subclasses will override these
        self._oController = None
        self._oMenu = None

    # pylint: disable-msg=W0212
    # We allow access via these properties
    view = property(fget=lambda self: self._oController.view,
            doc="Associated View Object")
    menu = property(fget=lambda self: self._oMenu, doc="Frame Menu")
    type = property(fget=lambda self: self._cModelType.sqlmeta.table,
            doc="Frame Type")
    # pylint: enable-msg=W0212

    def reload(self):
        """Reload frame contents"""
        # Needs to be exposed to the main window for major database changes
        self._oController.view.reload_keep_expanded()

    def get_toolbar_plugins(self):
        """Register plugins on the frame toolbar."""
        oBox = gtk.VBox(False, 2)
        bInsertToolbar = False
        for oPlugin in self._aPlugins:
            oWidget = oPlugin.get_toolbar_widget()
            if oWidget is not None:
                oBox.pack_start(oWidget)
                bInsertToolbar = True
        if bInsertToolbar:
            oToolbar = gtk.EventBox()
            oToolbar.add(oBox)
            self.set_drag_handler(oToolbar)
            self.set_drop_handler(oToolbar)
            oToolbar.show_all()
            return oToolbar
        else:
            return None

    def do_queued_reload(self):
        """Do a deferred reload if one was set earlier"""
        if self._bNeedReload:
            self.reload()
        self._bNeedReload = False

    def add_parts(self):
        """Add the elements to the Frame."""
        oMbox = gtk.VBox(False, 2)

        oMbox.pack_start(self._oTitle, False, False)
        oMbox.pack_start(self._oMenu, False, False)

        oMbox.pack_end(AutoScrolledWindow(self._oController.view),
                expand=True)

        self.add(oMbox)
        self.show_all()

        # We want the toolbars be able to choose if they start visible
        # or not, so we need to call this after show_all
        oToolbar = self.get_toolbar_plugins()
        if oToolbar is not None:
            oMbox.pack_start(oToolbar, False, False)

        self._oController.view.load()

        self.set_drag_handler(self._oMenu)
        self.set_drop_handler(self._oMenu)
