# PhysicalCardFrame.py
# Frame holding the Physical Card List
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.gui.PhysicalCardController import PhysicalCardController
from sutekh.gui.PhysicalCardMenu import PhysicalCardMenu
from sutekh.core.SutekhObjects import PhysicalCard

class PhysicalCardFrame(gtk.Frame, object):
    def __init__(self, oMainWindow, oConfig):
        super(PhysicalCardFrame, self).__init__()
        self.__oMainWindow = oMainWindow
        self.__oConfig = oConfig
        self.set_label("Physical Card List")
        self.__sName = "Physical Card List"
        self._sType = "Physical Cards"
        self.__oC = PhysicalCardController(self, oConfig, oMainWindow)

        self._aPlugins = []
        for cPlugin in self.__oMainWindow.plugin_manager.getCardListPlugins():
            self._aPlugins.append(cPlugin(self.__oC.view,
                self.__oC.view.getModel(), PhysicalCard))

        self._oMenu = PhysicalCardMenu(self, self.__oC, oMainWindow)
        self.addParts()

    view = property(fget=lambda self: self.__oC.view, doc="Associated View Object")
    name = property(fget=lambda self: self.__sName, doc="Frame Name")
    type = property(fget=lambda self: self._sType, doc="Frame Type")
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

        wMbox.pack_start(AutoScrolledWindow(self.__oC.view), expand=True)

        self.add(wMbox)
        self.show_all()
