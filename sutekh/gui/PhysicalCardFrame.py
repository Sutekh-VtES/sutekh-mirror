# PhysicalCardFrame.py
# Frame holding the Physical Card List
# Copyright 2005,2006,2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006,2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.gui.PhysicalCardController import PhysicalCardController

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
                self.__oC.view.getModel(),"PhysicalCard"))

        self.addParts(self.__oC)

    view = property(fget=lambda self: self.__oC.view, doc="Associated View Object")
    name = property(fget=lambda self: self.__sName, doc="Frame Name")
    type = property(fget=lambda self: self._sType, doc="Frame Type")

    def cleanup(self):
        pass

    def addParts(self, oPhysController):
        wMbox = gtk.VBox(False, 2)

        oToolbar = gtk.VBox(False,2)
        bInsertToolbar = False
        for oPlugin in self._aPlugins:
            oW = oPlugin.getToolbarWidget()
            if oW is not None:
                oToolbar.pack_start(oW)
                bInsertToolbar = True
        if bInsertToolbar:
            wMbox.pack_start(oToolbar, False, False)

        wMbox.pack_start(AutoScrolledWindow(oPhysController.view), expand=True)

        self.add(wMbox)
        self.show_all()
