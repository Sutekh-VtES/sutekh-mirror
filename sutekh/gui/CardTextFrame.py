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
        self.set_name('card text')

    type = property(fget=lambda self: "Card Text", doc="Frame Type")

    def add_parts(self):
        wMbox = gtk.VBox(False, 2)
        self.set_title("Card Text")

        wMbox.pack_start(self._oTitle, False, False)

        wMbox.pack_start(AutoScrolledWindow(self._oView), True, True)


        aDragTargets = [ ('STRING', 0, 0),
                         ('text/plain', 0, 0) ]

        self._oView.drag_dest_set(gtk.DEST_DEFAULT_ALL,
                aDragTargets,
                gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        self._oView.connect('drag-data-received', self.drag_drop_handler)
        self._oView.connect('drag-motion', self.drag_motion)

        self.add(wMbox)
        self.show_all()

