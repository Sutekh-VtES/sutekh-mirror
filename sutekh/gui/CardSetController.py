# CardSetController.py
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

from sqlobject import SQLObjectNotFound
from sqlobject.events import listen, RowUpdateSignal, RowDestroySignal
from sutekh.gui.CardSetView import CardSetView
from sutekh.gui.CardSetMenu import CardSetMenu
from sutekh.core.SutekhObjects import AbstractCardSet, PhysicalCardSet, \
        AbstractCard, PhysicalCard

class CardSetController(object):
    def __init__(self, sName, cType, oConfig, oMainWindow, oFrame):
        self._oMainWindow = oMainWindow
        self._oMenu = None
        self._oFrame = oFrame
        self._oView = CardSetView(oMainWindow, self, sName, cType, oConfig)
        self._sFilterType = None

    view = property(fget=lambda self: self._oView, doc="Associated View")
    frame = property(fget=lambda self: self._oFrame, doc="Associated Frame")
    filtertype = property(fget=lambda self: self._sFilterType, doc="Associated Type")

    def getView(self):
        return self._oView

    def getModel(self):
        return self._oView._oModel

    def getWin(self):
        return self.__oWin

    def getMenu(self):
        return self._oMenu

    def getPlugins(self):
        return self.__aPlugins

    def setCardText(self,sCardName):
        self._oMainWindow.set_card_text(sCardName)

class PhysicalCardSetController(CardSetController):
    def __init__(self, sName, oConfig, oMainWindow, oFrame):
        super(PhysicalCardSetController,self).__init__(
                sName, PhysicalCardSet, oConfig, oMainWindow, oFrame)
        self.__oPhysCardSet = PhysicalCardSet.byName(sName)
        self._sFilterType = 'PhysicalCard'
        listen(self.physical_card_deleted, PhysicalCard, RowDestroySignal)
        listen(self.physical_card_changed, PhysicalCard, RowUpdateSignal)

    def physical_card_deleted(self, oPhysCard):
        """Listen on physical card removals. Needed so we can
           updated the model if a card in this set is deleted
        """
        print oPhysCard

    def physical_card_changed(self, oPhysCard, dChanges):
        """Listen on physical cards changed. Needed so we can
           update the model if a card in this set is changed
        """
        print oPhysCard, dChanges

    def decCard(self, sName, sExpansion):
        """
        Returns True if a card was successfully removed, False otherwise.
        """
        print "PCS: decCard", sName, sExpansion
        return
        try:
            oC = AbstractCard.byCanonicalName(sName.lower())
        except SQLObjectNotFound:
            return False

        # find if there's a physical card of that name in the Set
        aSubset = [x for x in self.__oPhysCardSet.cards if x.abstractCardID == oC.id]
        if len(aSubset) > 0:
            # Remove last card (habit)
            self.__oPhysCardSet.removePhysicalCard(aSubset[-1].id)
            return True
        return False

    def incCard(self, sName, sExpansion):
        """
        Returns True if a card was successfully added, False otherwise.
        """
        return self.addCard(sName, sExpansion)

    def addCard(self, sName, sExpansion):
        """
        Returns True if a card was successfully added, False otherwise.
        """
        print "PCS: addCard", sName, sExpansion
        return
        try:
            oC = AbstractCard.byCanonicalName(sName.lower())
        except SQLObjectNotFound:
            return False

        # Find all Physicalcards with this name
        oPhysCards = PhysicalCard.selectBy(abstractCardID=oC.id)
        if oPhysCards.count() > 0:
            # Card exists
            for oCard in oPhysCards:
                # Add first Physical card not already in Set
                # Limits us to number of cards in PhysicalCards
                if oCard not in self.__oPhysCardSet.cards:
                    self.__oPhysCardSet.addPhysicalCard(oCard.id)
                    return True
        # Got here, so we failed to add
        return False

class AbstractCardSetController(CardSetController):
    def __init__(self, sName, oConfig, oMainWindow, oFrame):
        super(AbstractCardSetController,self).__init__(
                sName, AbstractCardSet, oConfig, oMainWindow, oFrame)
        self.__oAbsCardSet = AbstractCardSet.byName(sName)
        self._sFilterType = 'AbstractCard'

    def decCard(self, sName, sExpansion):
        """
        Returns True if a card was successfully removed, False otherwise.
        """
        try:
            oC = AbstractCard.byCanonicalName(sName.lower())
        except SQLObjectNotFound:
            return False
        # find if there's a abstract card of that name in the Set
        oDBClass = self.view._oModel.cardclass
        aSubSet = list(oDBClass.selectBy(abstractCardID=oC.id,
            abstractCardSetID=self.__oAbsCardSet.id))
        if len(aSubSet) > 0:
            oDBClass.delete(aSubSet[-1].id)
            self.view._oModel.alterCardCount(oC.name, -1)
            return True
        return False

    def incCard(self, sName, sExpansion):
        """
        Returns True if a card was successfully added, False otherwise.
        """
        return self.addCard(sName, sExpansion)

    def addCard(self, sName, sExpansion):
        """
        Returns True if a card was successfully added, False otherwise.
        """
        try:
            oC = AbstractCard.byCanonicalName(sName.lower())
        except SQLObjectNotFound:
            return False
        # Add to the Set
        # This is much simpler than for PhysicalCardSets, as we don't have
        # to worry about whether the card exists in PhysicalCards or not
        self.__oAbsCardSet.addAbstractCard(oC.id)
        self.view._oModel.incCardByName(oC.name)
        return True
