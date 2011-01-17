# PhysicalCardView.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Provide a TreeView for the physical card collection"""

import gtk
from sutekh.gui.CardListView import CardListView
from sutekh.gui.CardListModel import CardListModel
from sutekh.gui.CellRendererIcons import CellRendererIcons


class PhysicalCardView(CardListView):
    # pylint: disable-msg=R0904, R0902, R0901
    # R0904 - gtk.Widget, so many public methods
    # R0902 - We need to track a fair amount of state, so many attributes
    # R0901 - many ancestors, due to our object hierachy on top of the quite
    # deep gtk one
    """The card list view for the physical card collection.

       Special cases Editable card list with those properties
       needed for the card collection - the drag prefix, the
       card_drop handling and handling of pasted data.
       """
    sDragPrefix = 'Phys:'

    def __init__(self, oController, oWindow, oConfig):
        oModel = CardListModel(oConfig)
        oModel.enable_sorting()
        super(PhysicalCardView, self).__init__(oController, oWindow,
                oModel, oConfig)

        # Setup columns for default view
        self.oNameCell = CellRendererIcons(5)

        oColumn = gtk.TreeViewColumn("Cards", self.oNameCell, text=0,
                textlist=5, icons=6)
        oColumn.set_expand(True)
        oColumn.set_resizable(True)
        oColumn.set_sort_column_id(0)
        self.append_column(oColumn)

        self.set_expander_column(oColumn)
