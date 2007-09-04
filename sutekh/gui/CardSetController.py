# CardSetController.py
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

from sqlobject import SQLObjectNotFound
from sutekh.gui.CardSetView import CardSetView
from sutekh.gui.CardSetMenu import CardSetMenu
from sutekh.core.SutekhObjects import AbstractCardSet, PhysicalCardSet,\
        AbstractCard, PhysicalCard

class CardSetController(object):
    def __init__(self,oWindow,oMasterController,sName,sType,oConfig):
        self.__oView = CardSetView(oWindow,self,sName,sType,oConfig)
        self.__oWin= oWindow
        self.__oC = oMasterController
        self._oMenu = None

        # setup plugins before the menu (which needs a list of plugins)
        self.__aPlugins = []
        for cPlugin in oMasterController.getPluginManager().getCardListPlugins():
            self.__aPlugins.append(cPlugin(self.__oView,self.__oView.getModel(),sType))

    def getView(self):
        return self.__oView

    def getModel(self):
        return self.__oView._oModel

    def getWin(self):
        return self.__oWin

    def getMenu(self):
        return self._oMenu

    def getPlugins(self):
        return self.__aPlugins

    def setCardText(self,sCardName):
        self.__oC.setCardText(sCardName)

    def getFilter(self,widget):
        self.__oView.getFilter(self._oMenu)

    def runFilter(self,widget):
        self.__oView.runFilter(self._oMenu.getApplyFilter())

class PhysicalCardSetController(CardSetController):
    def __init__(self,oWindow,oMasterController,sName,oConfig):
        super(PhysicalCardSetController,self).__init__(\
                oWindow,oMasterController,sName,"PhysicalCardSet",oConfig)
        self.__oPhysCardSet = PhysicalCardSet.byName(sName)
        self._oMenu = CardSetMenu(self,self.getWin(),self.getView(),self.__oPhysCardSet.name,"PhysicalCardSet")

    def decCard(self,sName):
        """
        Returns True if a card was successfully removed, False otherwise.
        """
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

    def incCard(self,sName):
        """
        Returns True if a card was successfully added, False otherwise.
        """
        return self.addCard(sName)

    def addCard(self,sName):
        """
        Returns True if a card was successfully added, False otherwise.
        """
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
    def __init__(self,oWindow,oMasterController,sName,oConfig):
        super(AbstractCardSetController,self).__init__(\
                oWindow,oMasterController,sName,"AbstractCardSet",oConfig)
        self.__oAbsCardSet = AbstractCardSet.byName(sName)
        self._oMenu = CardSetMenu(self,self.getWin(),self.getView(),self.__oAbsCardSet.name,"AbstractCardSet")

    def decCard(self,sName):
        """
        Returns True if a card was successfully removed, False otherwise.
        """
        try:
            oC = AbstractCard.byCanonicalName(sName.lower())
        except SQLObjectNotFound:
            return False
        # find if there's a abstract card of that name in the Set
        aSubset = [x for x in self.__oAbsCardSet.cards if x.id == oC.id]
        if len(aSubset) > 0:
            # FIXME: This currently removes all the cards and restore
            # X-1 of them, because of the way removeAbstractCard works
            # for AbstractCardSets. Need to get at the id field of the
            # join to avoid this
            # Remove card
            self.__oAbsCardSet.removeAbstractCard(aSubset[-1].id)
            for j in range(len(aSubset)-1):
                self.__oAbsCardSet.addAbstractCard(oC.id)
            return True
        return False

    def incCard(self,sName):
        """
        Returns True if a card was successfully added, False otherwise.
        """
        return self.addCard(sName)

    def addCard(self,sName):
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
        return True
