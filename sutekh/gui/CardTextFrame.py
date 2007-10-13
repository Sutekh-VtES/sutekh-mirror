# CardTextFrame.py
# The Card Text Frame
# Copyright 2005,2006,2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006,2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow

class CardTextFrame(gtk.Frame, object):
    def __init__(self, oMainWindow):
        super(CardTextFrame,self).__init__()
        self.__oMainWindow = oMainWindow
        self.set_label('Card Text')

    def addParts(self, oCardText):
        wMbox = gtk.VBox(False, 2)

        wMbox.pack_start(AutoScrolledWindow(oCardText), True, True)

        self.add(wMbox)
        self.show_all()
