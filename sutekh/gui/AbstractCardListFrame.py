# AbstractCardListFrame.py
# Display the Abstract Card List
# Copyright 2005,2006,2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006,2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.gui.AbstractCardListController import AbstractCardListController

class AbstractCardListFrame(gtk.Frame, object):
    def __init__(self, oMainWindow, oConfig):
        super(AbstractCardListFrame,self).__init__()
        self.__oMainWindow = oMainWindow

        self.set_label("Whitewolf CardList")
        self.__oC = AbstractCardListController(self, oConfig, oMainWindow)

    view = property(fget=lambda self: self.__oC.view, doc="Associated View Object")

    def addParts(self, oAbstractCards):
        wMbox = gtk.VBox(False, 2)

        oToolbar = gtk.VBox(False,2)
        bInsertToolbar = False
        #for oPlugin in self.__oC.getPlugins():
        #    oW = oPlugin.getToolbarWidget()
        #    if oW is not None:
        #        oToolbar.pack_start(oW)
        #        bInsertToolbar = True
        #if bInsertToolbar:
        #    wMbox.pack_start(oToolbar, False, False)

        wMbox.pack_start(AutoScrolledWindow(oAbstractCards), True, True)

        self.add(wMbox)
        self.show_all()
