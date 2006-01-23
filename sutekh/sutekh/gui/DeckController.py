from sqlobject import SQLObjectNotFound
from DeckView import DeckView
from SutekhObjects import *

class DeckController(object):
    def __init__(self,oWindow,oMasterController,deckName):
        self.__oView = DeckView(oWindow,self,deckName)
        self.__oC = oMasterController
        self.deckName=deckName
        
    def getView(self):
        return self.__oView
    
    def decCard(self,sName):
        try:
            oC = AbstractCard.byName(sName)
        except SQLObjectNotFound:
            return
        # find if there's a physical card of that name in the deck
        deck = PhysicalCardSet.byName(self.deckName)
        subset=[x for x in deck.cards if x.abstractCardID==oC.id]
        if len(subset)>0:
            # Remove last card (habit)
            deck.removePhysicalCard(subset[-1].id)
            # reload
            self.__oView.load()
            
    def incCard(self,sName):
        self.addCard(sName)
    
    def addCard(self,sName):
        try:
            oC = AbstractCard.byName(sName)
        except SQLObjectNotFound:
            return
        # Select current deck
        try:
            deck = PhysicalCardSet.byName(self.deckName)
        except SQLObjectNotFound:
            return
        # Find all Physicalcards with this name
        Physcards=PhysicalCard.selectBy(abstractCardID=oC.id)
        if Physcards.count()>0:
            # Card exists
            for card in Physcards:
                # Add first Physical card not already in deck
                # Limits us to number of cards in PhysicalCards
                # Need to extend this to handle constraints
                if card not in deck.cards:
                    deck.addPhysicalCard(card.id)
                    break
            # Inc'ed card, so reload list - NM
            self.__oView.load()

    def setCardText(self,sName):
        pass
