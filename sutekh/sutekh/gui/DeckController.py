# DeckController.py
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

from sqlobject import SQLObjectNotFound
from DeckView import DeckView
from DeckMenu import DeckMenu
from SutekhObjects import *

class DeckController(object):
    def __init__(self,oWindow,oMasterController,sDeckName):
        self.__oView = DeckView(oWindow,self,sDeckName)
        self.__oWin = oWindow
        self.__oC = oMasterController
        self.__oDeck = PhysicalCardSet.byName(sDeckName)
        self.__oMenu = DeckMenu(self,self.__oWin,self.__oDeck.name)
        
    def getView(self):
        return self.__oView

    def getModel(self):
        return self.__oView._oModel

    def getMenu(self):
        return self.__oMenu
    
    def decCard(self,sName):
        """
        Returns True if a card was successfully removed, False otherwise.
        """
        try:
            oC = AbstractCard.byName(sName)
        except SQLObjectNotFound:
            return False
            
        # find if there's a physical card of that name in the deck
        aSubset = [x for x in self.__oDeck.cards if x.abstractCardID == oC.id]
        
        if len(aSubset) > 0:
            # Remove last card (habit)
            self.__oDeck.removePhysicalCard(aSubset[-1].id)
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
            oC = AbstractCard.byName(sName)
        except SQLObjectNotFound:
            return False
            
        # Find all Physicalcards with this name
        oPhysCards = PhysicalCard.selectBy(abstractCardID=oC.id)
        if oPhysCards.count() > 0:
            # Card exists
            for oCard in oPhysCards:
                # Add first Physical card not already in deck
                # Limits us to number of cards in PhysicalCards
                # Need to extend this to handle constraints
                if oCard not in self.__oDeck.cards:
                    self.__oDeck.addPhysicalCard(oCard.id)
                    break
            return True
            
        return False

    def setCardText(self,sCardName):
        self.__oC.setCardText(sCardName)

    def getFilter(self,widget):
        self.__oView.getFilter(self.__oMenu)

    def runFilter(self,widget):
        self.__oView.runFilter(self.__oMenu.getApplyFilter())
