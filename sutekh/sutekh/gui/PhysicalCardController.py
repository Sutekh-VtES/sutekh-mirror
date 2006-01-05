from sqlobject import SQLObjectNotFound
from PhysicalCardView import PhysicalCardView
from SutekhObjects import *

class PhysicalCardController(object):
    def __init__(self,oMasterController):
        self.__oView = PhysicalCardView(self)
        self.__oC = oMasterController
        
    def getView(self):
        return self.__oView
    
    def decCard(self,sName):
        try:
            oC = AbstractCard.byName(sName)
        except SQLObjectNotFound:
            return
        # Go from Name to Abstract Card ID to Physical card ID 
        # which is needed for delete
        # find Physical cards cards with this name
        cardCands=PhysicalCard.selectBy(abstractCardID=oC.id)
        # check we found something?
        if cardCands.count()==0:
            return
        # delete last from list (habit)
        PhysicalCard.delete(cardCands[-1].id)
        # Removed card, so reload list - NM
        self.__oView.load()
    
    def incCard(self,sName):
        try:
            oC = AbstractCard.byName(sName)
        except SQLObjectNotFound:
            return
        oPC = PhysicalCard(abstractCard=oC)
        # Inc'ed card, so reload list - NM
        self.__oView.load()
    
    def addCard(self,sName):
        try:
            oC = AbstractCard.byName(sName)
        except SQLObjectNotFound:
            return
        oPC = PhysicalCard(abstractCard=oC)
        self.__oView.load()
        
    def setCardText(self,sCardName):
        self.__oC.setCardText(sCardName)
