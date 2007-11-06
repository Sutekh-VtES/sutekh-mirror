# AbstractCardListFrame.py
# Display the Abstract Card List
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.gui.AbstractCardListController import AbstractCardListController
from sutekh.gui.AbstractCardListMenu import AbstractCardListMenu
from sutekh.core.SutekhObjects import AbstractCard

class AbstractCardListFrame(gtk.Frame, object):
    def __init__(self, oMainWindow, oConfig):
        super(AbstractCardListFrame, self).__init__()
        self.__oMainWindow = oMainWindow

        self.set_label("Whitewolf CardList")
        self.__sName = "Whitewolf CardList"
        self.__sType = "Abstract Cards"
        self.__oC = AbstractCardListController(self, oConfig, oMainWindow)

        self._aPlugins = []
        for cPlugin in self.__oMainWindow.plugin_manager.getCardListPlugins():
            self._aPlugins.append(cPlugin(self.__oC.view,
                self.__oC.view.getModel(), AbstractCard))

        self._oMenu = AbstractCardListMenu(self, self.__oC, oMainWindow)

        self.addParts()

    view = property(fget=lambda self: self.__oC.view, doc="Associated View Object")
    name = property(fget=lambda self: self.__sName, doc="Frame Name")
    type = property(fget=lambda self: self.__sType, doc="Frame Type")
    menu = property(fget=lambda self: self._oMenu, doc="Frame Menu")

    def cleanup(self):
        pass

    def close_frame(self):
        self.__oMainWindow.remove_pane(self)
        self.destroy()

    def addParts(self):
        wMbox = gtk.VBox(False, 2)

        wMbox.pack_start(self._oMenu, False, False)

        oToolbar = gtk.VBox(False, 2)
        bInsertToolbar = False
        for oPlugin in self._aPlugins:
            oW = oPlugin.getToolbarWidget()
            if oW is not None:
                oToolbar.pack_start(oW)
                bInsertToolbar = True
        if bInsertToolbar:
            wMbox.pack_start(oToolbar, False, False)

        wMbox.pack_start(AutoScrolledWindow(self.__oC.view), True, True)

        self.add(wMbox)
        self.show_all()
