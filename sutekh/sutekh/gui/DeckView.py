# DeckView.py
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

from CardListView import EditableCardListView
from DeleteDeckDialog import DeleteDeckDialog
from Filters import DeckFilter
from SutekhObjects import PhysicalCard, PhysicalCardSet

class DeckView(EditableCardListView):
    def __init__(self,oWindow,oController,sName):
        super(DeckView,self).__init__(oController,oWindow)        
        self.deckName = sName
        
        self._oModel.basefilter = DeckFilter(self.deckName)
        self._oModel.cardclass = PhysicalCard       
        self.load()
                   
    def dragCard(self, btn, context, selection_data, info, time):
        if self._oSelection.count_selected_rows()<1:
            return
        oModel, oPathList = self._oSelection.get_selected_rows()
        selectData = "Deck:"+self.deckName
        for oPath in oPathList:
            oIter = oModel.get_iter(oPath)
            sCardName = oModel.get_value(oIter,0)
            number = str(oModel.get_value(oIter,1))
            selectData = selectData + "\n" + number + "_" + sCardName
        selection_data.set(selection_data.target, 8, selectData)

    def cardDrop(self, w, context, x, y, data, info, time):
        if data and data.format == 8 and data.data[:5] == "Phys:":
            # Card is from the Physical card view, so we only get one
            #print data.data[5:]
            cards=data.data.splitlines()
            for name in cards[1:]:
               self.addCard(name)
            context.finish(True, False, time)
        else:
            if data and data.format == 8 and data.data[:5] == "Deck:":
                # Card is from a deck, so extract deckname
                cards=data.data.splitlines()
                sourceDeckName = cards[0][5:]
                if sourceDeckName != self.deckName:
                    # different deck, so try and add number cards
                    # We rely on addCard to prevent stuff becoming 
                    # inconsistent
                    for candidate in cards[1:]:
                        [number, name] = candidate.split('_')
                        for j in range(int(number)):
                            self.addCard(name)
                context.finish(True,False, time)
            else:
                context.finish(False, False, time)

    def deleteDeck(self):
        # Check if deck is empty
        oPCS = PhysicalCardSet.byName(self.deckName)
        if len(oPCS.cards)>0:
            # Not empty
            Dialog = DeleteDeckDialog(self._oWin,self.deckName)
            Dialog.run()
            if not Dialog.getResult():
                return False # not deleting 
        # Either deck empty, or user agreed to delete
        deck = PhysicalCardSet.byName(self.deckName)
        PhysicalCardSet.delete(deck.id)
        # Tell Window to clean up
        return True
