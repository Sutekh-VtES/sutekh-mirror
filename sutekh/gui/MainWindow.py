# MainWindow.py
# The Main App Window
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow

class MainWindow(gtk.Window,object):
    def __init__(self,oController):
        super(MainWindow,self).__init__()
        self.__oC = oController

        self.connect('destroy', lambda wWin: self.__oC.actionQuit())

        self.set_title("Sutekh: Whitewolf CardList")
        self.set_default_size(300, 600)

    def addParts(self,oMenu,oAbstractCards):
        wMbox = gtk.VBox(False, 2)

        wMbox.pack_start(oMenu, False, False)

        wMbox.pack_start(AutoScrolledWindow(oAbstractCards), True, True)

        self.add(wMbox)
        self.show_all()
