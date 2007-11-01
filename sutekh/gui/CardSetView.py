# CardSetView.py
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

from sutekh.gui.CardListView import EditableCardListView
from sutekh.gui.DeleteCardSetDialog import DeleteCardSetDialog
from sutekh.core.Filters import PhysicalCardSetFilter, AbstractCardSetFilter
from sutekh.core.SutekhObjects import PhysicalCard, PhysicalCardSet, AbstractCardSet, \
        MapAbstractCardToAbstractCardSet

class CardSetView(EditableCardListView):
    def __init__(self, oMainWindow, oController, sName, sSetType, oConfig):
        super(CardSetView,self).__init__(oController, oMainWindow, oConfig)
        self.sSetName = sName
        self.sSetType = sSetType
        if sSetType == PhysicalCardSet.sqlmeta.table:
            # cardclass is the actual physicalcard
            self._oModel.cardclass = PhysicalCard
            self._oModel.basefilter = PhysicalCardSetFilter(self.sSetName)
            self._oModel.bExpansions = True
        elif sSetType == AbstractCardSet.sqlmeta.table:
            # Need MapAbstractCardToAbstractCardSet here, so filters do the right hing
            self._oModel.cardclass = MapAbstractCardToAbstractCardSet
            self._oModel.basefilter = AbstractCardSetFilter(self.sSetName)
        else:
            # Should this be an error condition?
            self._oModel.basefilter = None

        self.sDragPrefix = self.sSetType + ":" + self.sSetName
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
                    if sSource == 'Abs':
                        # from Abstract list, so iCount doesn't matter
                        self.addCard(sCardName, sExpansion)
                    else:
                        # iCount matters
                        for iLoop in range(iCount):
                            self.addCard(sCardName, sExpansion)
                context.finish(True, False, time)
            else:
                context.finish(False, False, time)

    def deleteCardSet(self):
        # Check if CardSet is empty
        if self.sSetType == PhysicalCardSet.sqlmeta.table:
            oCS = PhysicalCardSet.byName(self.sSetName)
            Dialog = DeleteCardSetDialog(self._oWin, self.sSetName, "Physical Card Set")
        else:
            oCS = AbstractCardSet.byName(self.sSetName)
            Dialog = DeleteCardSetDialog(self._oWin, self.sSetName, "Abstract Card Set")
        if len(oCS.cards)>0:
            # Not empty, ask user if we should delete it
            Dialog.run()
            if not Dialog.getResult():
                return False # not deleting
            # User agreed, so clear the CardSet
            if self.sSetType == PhysicalCardSet.sqlmeta.table:
                for oC in oCS.cards:
                    oCS.removePhysicalCard(oC)
            else:
                for oC in oCS.cards:
                    oCS.removeAbstractCard(oC)
        # Card Set now empty
        if self.sSetType == PhysicalCardSet.sqlmeta.table:
            cardSet = PhysicalCardSet.byName(self.sSetName)
            PhysicalCardSet.delete(cardSet.id)
        else:
            cardSet = AbstractCardSet.byName(self.sSetName)
            AbstractCardSet.delete(cardSet.id)
        # Tell Window to clean up
        return True
