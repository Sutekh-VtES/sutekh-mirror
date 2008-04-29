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
    _cModelType = None

    def __init__(self, oMainWindow):
        super(CardListFrame, self).__init__(oMainWindow)
        self._aPlugins = []
        self._oConfig = oMainWindow.config_file

        self._oController = None

    # pylint: disable-msg=W0212
    # We allow access via these properties
    view = property(fget=lambda self: self._oController.view,
            doc="Associated View Object")
    menu = property(fget=lambda self: self._oMenu, doc="Frame Menu")
    type = property(fget=lambda self: self._cModelType.sqlmeta.table,
            doc="Frame Type")
    plugins = property(fget=lambda self: self._aPlugins,
            doc="Plugins enabled for this frame.")
    # pylint: enable-msg=W0212

    def init_plugins(self):
        """Loop through the plugins, and enable those appropriate for us."""
        for cPlugin in \
                self._oMainWindow.plugin_manager.get_card_list_plugins():
            self._aPlugins.append(cPlugin(self._oController.view,
                self._oController.view.get_model(), self._cModelType))

    def reload(self):
        """Reload frame contents"""
        # Needs to be exposed to the main window for major database changes
        self._oController.view.reload_keep_expanded()

    def get_toolbar_plugins(self):
        """Register plugins on the frame toolbar."""
        oToolbar = gtk.VBox(False, 2)
        bInsertToolbar = False
        for oPlugin in self._aPlugins:
            oWidget = oPlugin.get_toolbar_widget()
            if oWidget is not None:
                oToolbar.pack_start(oWidget)
                bInsertToolbar = True
        if bInsertToolbar:
            return oToolbar
        else:
            return None

    def add_parts(self):
        """Add the elements to the Frame."""
        oMbox = gtk.VBox(False, 2)

        oMbox.pack_start(self._oTitle, False, False)
        oMbox.pack_start(self._oMenu, False, False)

        oToolbar = self.get_toolbar_plugins()
        if oToolbar is not None:
            oMbox.pack_start(oToolbar, False, False)

        oMbox.pack_start(AutoScrolledWindow(self._oController.view),
                expand=True)

        self.add(oMbox)
        self._oController.view.load()
        self.show_all()
