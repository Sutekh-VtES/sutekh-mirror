# PhysicalCardView.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

from sutekh.gui.CardListView import EditableCardListView
from sutekh.gui.CardListModel import PhysicalCardListModel

class PhysicalCardView(EditableCardListView):
    def __init__(self, oController, oWindow, oConfig):

        oModel = PhysicalCardListModel(oConfig.get_show_zero_count_cards())
        super(PhysicalCardView, self).__init__(oController, oWindow, oConfig, oModel)

        self._oC = oController
        self.sDragPrefix = 'Phys:'
        self.load()

    def card_drop(self, w, context, x, y, data, info, time):
        if not data or data.format != 8:
            # Don't accept cards when editable
            context.finish(False, False, time)
        else:
            sSource, aCardInfo = self.split_selection_data(data.data)
            if sSource == "Sutekh Pane:":
                self._oC.frame.drag_drop_handler(w, context, x, y, data, info, time)
            elif self._oModel.bEditable and sSource in ['Abst:']:
                # We can only drag from the AbstractCard List
                # We can't drag from the card sets
                # Add the cards
                for iCount, sCardName, sExpansion in aCardInfo:
                    # We are adding new cards, so only 1 of each
                    self.addCard(sCardName, sExpansion)
                context.finish(True, False, time)
            else:
                context.finish(False, False, time)
