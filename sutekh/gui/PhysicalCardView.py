# PhysicalCardView.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

from sutekh.gui.CardListView import EditableCardListView
from sutekh.core.Filters import PhysicalCardFilter
from sutekh.core.SutekhObjects import PhysicalCard

class PhysicalCardView(EditableCardListView):
    def __init__(self, oController, oWindow, oConfig):
        super(PhysicalCardView, self).__init__(oController, oWindow, oConfig)

        self._oModel.basefilter = PhysicalCardFilter()
        self._oModel.cardclass = PhysicalCard
        self._oWin = oWindow
        self._oModel.bExpansions = True
        self._oC = oController
        self.sDragPrefix = 'Phys:'
        self.load()

    def cardDrop(self, w, context, x, y, data, info, time):
        if not self._oModel.bEditable or not data or data.format != 8:
            # Don't accept cards when editable
            context.finish(False, False, time)
        else:
            sSource, aCardInfo = self.split_selection_data(data.data)
            print sSource
            print aCardInfo
            if sSource in []:
                # Add the cards
                for iCount, sCardName, sExpansion in aCardInfo:
                    # We are adding new cards, so only 1 of each
                    self.addCard(sCardName, sExpansion)
                context.finish(True, False, time)
            else:
                context.finish(False, False, time)

    def getWindow(self):
        return self._oWin

    def getModel(self):
        return self._oModel

    def getController(self):
        return self._oC
