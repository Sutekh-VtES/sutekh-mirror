# CardTextFrame.py
# The Card Text Frame
# Copyright 2005,2006,2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006,2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.gui.CardTextView import CardTextView
from sutekh.gui.BasicFrame import BasicFrame

class CardTextFrame(BasicFrame):
    def __init__(self, oMainWindow):
        super(CardTextFrame, self).__init__(oMainWindow)
        self._oTextView = CardTextView(oMainWindow)
        self.add_parts()

    view = property(fget=lambda self: self._oTextView, doc="Associated View Object")
    type = "Card Text"

    def add_parts(self):
        wMbox = gtk.VBox(False, 2)
        self.set_title("Card Text")

        wMbox.pack_start(self._oTitle, False, False)

        wMbox.pack_start(AutoScrolledWindow(self._oTextView), True, True)

        self.add(wMbox)
        self.show_all()
