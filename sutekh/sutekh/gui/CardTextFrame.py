# CardTextFrame.py
# The Card Text Frame
# Copyright 2005,2006,2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006,2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.gui.CardTextView import CardTextView

class CardTextFrame(gtk.Frame, object):
    def __init__(self, oMainWindow):
        super(CardTextFrame,self).__init__()
        self.__oMainWindow = oMainWindow
        self.__oTitle = gtk.Label("Card Text")
        self.__sName = "Card Text"
        self.__oTextView = CardTextView(oMainWindow)
        self.add_parts(self.__oTextView)

        self.__oBaseStyle = self.__oTitle.get_style().copy()
        self.__oFocStyle = self.__oTitle.get_style().copy()
        # Don't start overly narrow
        self.set_size_request(200, 100)
        oMap = self.__oTitle.get_colormap()
        oHighlighted = oMap.alloc_color("purple")
        self.__oFocStyle.fg[gtk.STATE_NORMAL] = oHighlighted

    view = property(fget=lambda self: self.__oTextView, doc="Associated View Object")
    name = property(fget=lambda self: self.__sName, doc="Frame Name")
    type = property(fget=lambda self: self.__sName, doc="Frame Type")

    def cleanup(self):
        pass

    def reload(self):
        pass

    def add_parts(self, oCardText):
        wMbox = gtk.VBox(False, 2)

        wMbox.pack_start(self.__oTitle, False, False)

        wMbox.pack_start(AutoScrolledWindow(oCardText), True, True)

        self.add(wMbox)
        self.show_all()

    def set_focussed_title(self):
        self.__oTitle.set_style(self.__oFocStyle)

    def set_unfocussed_title(self):
        self.__oTitle.set_style(self.__oBaseStyle)
