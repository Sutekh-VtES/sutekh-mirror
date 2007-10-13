# PhysicalCardFrame.py
# Frame holding the Physical Card List
# Copyright 2005,2006,2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006,2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow

class PhysicalCardFrame(gtk.Frame, object):
    def __init__(self, oMainWindow):
        super(PhysicalCardFrame, self).__init__()
        self.__oMainWindow = oMainWindow
        self.set_label('Physical Card List')

    def addParts(self, oPhysController):
        wMbox = gtk.VBox(False, 2)

        wMbox.pack_start(oPhysController.getMenu(),False,False)
        oToolbar = gtk.VBox(False,2)
        bInsertToolbar = False
        for oPlugin in oPhysController.getPlugins():
            oW = oPlugin.getToolbarWidget()
            if oW is not None:
                oToolbar.pack_start(oW)
                bInsertToolbar = True
        if bInsertToolbar:
            wMbox.pack_start(oToolbar, False, False)

        wMbox.pack_start(AutoScrolledWindow(oPhysController.getView()), expand=True)

        self.add(wMbox)
        self.show_all()

    def getManager(self):
        return self.__oC.getManager()
