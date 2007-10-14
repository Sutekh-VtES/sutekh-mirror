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
        self.__oC = PhysicalCardController(self, oConfig, oMainWindow)
        self.addParts(self.__oC)

    view = property(fget=lambda self: self.__oC.view, doc="Associated View Object")
    name = property(fget=lambda self: self.__sName, doc="Frame Name")

    def addParts(self, oPhysController):
        wMbox = gtk.VBox(False, 2)

        wMbox.pack_start(AutoScrolledWindow(oPhysController.view), expand=True)

        self.add(wMbox)
        self.show_all()
