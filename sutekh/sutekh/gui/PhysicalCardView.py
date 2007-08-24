# PhysicalCardView.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

from sutekh.gui.CardListView import EditableCardListView
from sutekh.core.Filters import PhysicalCardFilter
from sutekh.core.SutekhObjects import PhysicalCard

class PhysicalCardView(EditableCardListView):
    def __init__(self,oController,oWindow,oConfig):
        super(PhysicalCardView,self).__init__(oController,oWindow,oConfig)

        self._oModel.basefilter = PhysicalCardFilter()
        self._oModel.cardclass = PhysicalCard
        self._oWin = oWindow
        self.load()

    def cardDrop(self, w, context, x, y, data, info, time):
        if data and data.format == 8 and data.data[:5] == "Abst:":
            cards = data.data.splitlines()
            for name in cards[1:]:
                self.addCard(name)
            context.finish(True, False, time)
        else:
            context.finish(False, False, time)

    def dragCard(self, btn, context, selection_data, info, time):
        if self._oSelection.count_selected_rows()<1:
            return
        oModel, oPathList = self._oSelection.get_selected_rows()
        selectData = "Phys:"
        for oPath in oPathList:
            oIter = oModel.get_iter(oPath)
            sCardName = oModel.get_value(oIter,0)
            selectData = selectData + "\n" + sCardName
        selection_data.set(selection_data.target, 8, selectData)

    def getWindow(self):
        return self._oWin
