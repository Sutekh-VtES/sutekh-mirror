# CardTextWindow.py
# The Card Text Window
# Copyright 2005,2006,2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from AutoScrolledWindow import AutoScrolledWindow

class CardTextWindow(gtk.Window,object):
    def __init__(self,oController):
        super(CardTextWindow,self).__init__()
        self.__oC = oController

        self.connect('destroy', lambda wWin: self.__oC.actionQuit())

        self.set_title("Sutekh: Card Text")
        self.set_default_size(300, 600)

    def addParts(self,oCardText):
        wMbox = gtk.VBox(False, 2)

        wMbox.pack_start(AutoScrolledWindow(oCardText), True, True)

        self.add(wMbox)
        self.show_all()
