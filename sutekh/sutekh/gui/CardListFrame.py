# CardListFrame.py
# Base class for other Frames.
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details


import gtk
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.gui.BasicFrame import BasicFrame

class CardListFrame(BasicFrame):
    def __init__(self, oMainWindow, oConfig):
        super(CardListFrame, self).__init__(oMainWindow)
        self._oConfig = oConfig

        self._oC = None
        self._cModelType = None

    view = property(fget=lambda self: self._oC.view, doc="Associated View Object")
    menu = property(fget=lambda self: self._oMenu, doc="Frame Menu")
    type = property(fget=lambda self: self._cModelType.sqlmeta.table, doc="Frame Type")

    def init_plugins(self):
        self._aPlugins = []
        for cPlugin in self._oMainWindow.plugin_manager.get_card_list_plugins():
            self._aPlugins.append(cPlugin(self._oC.view,
                self._oC.view.getModel(), self._cModelType))

    def reload(self):
        """Reload frame contents"""
        # Needs to be exposed to the main window for major database changes
        self._oC.view.reload_keep_expanded()

    def get_toolbar_plugins(self):
        oToolbar = gtk.VBox(False, 2)
        bInsertToolbar = False
        for oPlugin in self._aPlugins:
            oW = oPlugin.get_toolbar_widget()
            if oW is not None:
                oToolbar.pack_start(oW)
                bInsertToolbar = True
        if bInsertToolbar:
            return oToolbar
        else:
            return None

    def add_parts(self):
        wMbox = gtk.VBox(False, 2)

        wMbox.pack_start(self._oTitle, False, False)
        wMbox.pack_start(self._oMenu, False, False)

        oToolbar = self.get_toolbar_plugins()
        if oToolbar is not None:
            wMbox.pack_start(oToolbar, False, False)

        wMbox.pack_start(AutoScrolledWindow(self._oC.view), expand=True)

        self.add(wMbox)
        self.show_all()
