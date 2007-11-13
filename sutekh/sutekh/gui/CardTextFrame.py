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
        self._oView = CardTextView(oMainWindow)
        self.add_parts()

    type = property(fget=lambda self: "Card Text", doc="Frame Type")

    def add_parts(self):
        wMbox = gtk.VBox(False, 2)
        self.set_title("Card Text")

        wMbox.pack_start(self._oTitle, False, False)

        wMbox.pack_start(AutoScrolledWindow(self._oView), True, True)

        self.add(wMbox)
        self.show_all()
