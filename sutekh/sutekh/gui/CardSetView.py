# CardSetView.py
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.gui.CardListView import EditableCardListView
from sutekh.gui.CardListModel import PhysicalCardSetCardListModel, CardListModel
from sutekh.core.Filters import AbstractCardSetFilter
from sutekh.core.SutekhObjects import PhysicalCardSet, \
        AbstractCardSet, MapAbstractCardToAbstractCardSet
from sutekh.SutekhUtility import delete_physical_card_set, delete_abstract_card_set

class CardSetView(EditableCardListView):
    def __init__(self, oMainWindow, oController, sName, cSetType, oConfig):
        if cSetType is PhysicalCardSet:
            # cardclass is the actual physicalcard
            oModel = PhysicalCardSetCardListModel(sName)
        elif cSetType is AbstractCardSet:
            # Need MapAbstractCardToAbstractCardSet here, so filters do the right hing
            oModel = CardListModel()
        super(CardSetView, self).__init__(oController, oMainWindow, oConfig, oModel)
        self.sSetName = sName
        self.cSetType = cSetType
        if cSetType is AbstractCardSet:
            self._oModel.cardclass = MapAbstractCardToAbstractCardSet
            self._oModel.basefilter = AbstractCardSetFilter(self.sSetName)
        self.sDragPrefix = self.cSetType.sqlmeta.table + ":" + self.sSetName
        self.load()

    def card_drop(self, w, context, x, y, data, info, time):
        if not data or data.format != 8:
            # Don't accept cards when editable
            context.finish(False, False, time)
        else:
            sSource, aCardInfo = self.split_selection_data(data.data)
            if sSource == "Sutekh Pane:":
                self._oC.frame.drag_drop_handler(w, context, x, y, data, info, time)
            elif not self._oModel.bEditable:
                context.finish(False, False, time)
            elif sSource == self.sDragPrefix:
                # Can't drag to oneself
                context.finish(False, False, time)
            # Rules are - we can always drag from the PhysicalCard List
            # and from cardsets of the same type,
            # but only ACS's can recieve cards from the AbstractCard List
            aSources=sSource.split(':')
            if aSources[0] in ["Phys", self.cSetType.sqlmeta.table]:
                # Add the cards, Count Matters
                for iCount, sCardName, sExpansion in aCardInfo:
                    for iLoop in range(iCount):
                        self.addCard(sCardName, sExpansion)
                context.finish(True, False, time)
            elif aSources[0] == "Abst" and self.cSetType is AbstractCardSet:
                # from Abstract list, so iCount doesn't matter
                for iCount, sCardName, sExpansion in aCardInfo:
                    self.addCard(sCardName, sExpansion)
                context.finish(True, False, time)
            else:
                context.finish(False, False, time)

    def deleteCardSet(self):
        # Check if CardSet is empty
        oCS = self.cSetType.byName(self.sSetName)
        if len(oCS.cards)>0:
            oDialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_WARNING,
                    gtk.BUTTONS_OK_CANCEL, "Card Set Not Empty. Really Delete?")
            iResponse = oDialog.run()
            oDialog.destroy()
            if iResponse == gtk.RESPONSE_CANCEL:
                return False # not deleting
        # Got this far, so delete the card set
        if self.cSetType is PhysicalCardSet:
            delete_physical_card_set(self.sSetName)
        else:
            delete_abstract_card_set(self.sSetName)
        # Tell Window to clean up
        return True
