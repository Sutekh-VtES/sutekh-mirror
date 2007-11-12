# PhysicalCardView.py
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

from sutekh.gui.CardListView import EditableCardListView
from sutekh.gui.CardListModel import PhysicalCardListModel

class PhysicalCardView(EditableCardListView):
    def __init__(self, oController, oWindow, oConfig):

        oModel = PhysicalCardListModel()
        super(PhysicalCardView, self).__init__(oController, oWindow, oConfig, oModel)

        self._oC = oController
        self.sDragPrefix = 'Phys:'
        self.load()

    def card_drop(self, w, context, x, y, data, info, time):
        if not self._oModel.bEditable or not data or data.format != 8:
            # Don't accept cards when editable
            context.finish(False, False, time)
        else:
            sSource, aCardInfo = self.split_selection_data(data.data)
            # We can only drag from the AbstractCard List
            # We can't drag from the card sets
            if sSource in ['Abst:']:
                # Add the cards
                for iCount, sCardName, sExpansion in aCardInfo:
                    # We are adding new cards, so only 1 of each
                    self.addCard(sCardName, sExpansion)
                context.finish(True, False, time)
            else:
                context.finish(False, False, time)
