# AbstractCardView.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Minor modifications copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk, pango
from sutekh.gui.CardListView import CardListView

class AbstractCardView(CardListView):
    def __init__(self, oController, oMainWindow, oConfig):
        super(AbstractCardView,self).__init__(oController, oMainWindow, oConfig)

        oCell = gtk.CellRendererText()
        oCell.set_property('style', pango.STYLE_ITALIC)
        oColumn = gtk.TreeViewColumn("Collection", oCell, text=0)
        self.append_column(oColumn)

        self.sDragPrefix = 'Abst:'

        self.load()
