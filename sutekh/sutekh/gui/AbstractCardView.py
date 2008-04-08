# AbstractCardView.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""CardListView for the White wolf card list"""

import gtk, pango
from sutekh.gui.CardListView import CardListView
from sutekh.gui.CardListModel import CardListModel

class AbstractCardView(CardListView):
    """CardListView for the WW Card List

       Since this card list isn't editable, this is very simple
       """
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    def __init__(self, oController, oMainWindow, oConfig):
        oModel = CardListModel()
        super(AbstractCardView, self).__init__(oController, oMainWindow,
                oConfig, oModel)

        oCell = gtk.CellRendererText()
        oCell.set_property('style', pango.STYLE_ITALIC)
        oColumn = gtk.TreeViewColumn("Collection", oCell, text=0)
        self.append_column(oColumn)
        oColumn.set_sort_column_id(0)

        self.sDragPrefix = 'Abst:'

        self.load()
