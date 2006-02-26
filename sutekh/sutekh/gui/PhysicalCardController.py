from sqlobject import SQLObjectNotFound
from PhysicalCardView import PhysicalCardView
from PhysicalCardMenu import PhysicalCardMenu
from SutekhObjects import *
from DeleteCardDialog import DeleteCardDialog

class PhysicalCardController(object):
    def __init__(self,oWindow,oMasterController):
        self.__oView = PhysicalCardView(self,oWindow)
        self.__oC = oMasterController
        self.__oWin = oWindow
        self.__oMenu = PhysicalCardMenu(self,self.__oWin)
        
    def getView(self):
        return self.__oView
    
    def getMenu(self):
        return self.__oMenu
    
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
        # Loop throgh list and see if we can find a card
        # not present in any decks
        deckdict={}
        decks=PhysicalCardSet.select()
        for card in cardCands.reversed():
            idtodel = card.id
            deckdict[idtodel]=[0,[]]
            for deck in decks:
                subset=[x for x in deck.cards if x.id == idtodel]
                if len(subset)>0:
                    deckdict[idtodel][0]+=1;
                    deckdict[idtodel][1].append(deck.name)
            if deckdict[idtodel][0]==0:
                # OK, can delete this one and be done with it
                PhysicalCard.delete(idtodel)
                self.__oView.load()
                return
        # All physical cards are assigned to decks, so find the
        # one in the fewest
        T=min(deckdict.values())
        list=[x for x in deckdict if T is deckdict[x]]
        idtodel=list[-1]
        candtodel=deckdict[idtodel] 
        # This is probably overcomplicated, need to revisit this sometime
        # Prompt the user for confirmation
        Dialog=DeleteCardDialog(self.__oWin,candtodel[1])
        Dialog.run()
        if Dialog.getResult():
            # User agrees
            # Delete card from all the decks first
            for deck in candtodel[1]:
                oPC=PhysicalCardSet.byName(deck)
                oPC.removePhysicalCard(idtodel)
            PhysicalCard.delete(idtodel)
            # Reload everything
            self.__oC.reloadAll()
        
    
    def incCard(self,sName):
        # Identical to addCard
        self.addCard(sName)
    
    def addCard(self,sName):
        try:
            oC = AbstractCard.byName(sName)
        except SQLObjectNotFound:
            return
        oPC = PhysicalCard(abstractCard=oC)
        # Inc'ed card, so reload list - NM
        self.__oView.load()
        
    def setCardText(self,sCardName):
        self.__oC.setCardText(sCardName)


    def getFilter(self,widget):
        self.__oView.getFilter(self.__oMenu,self.__oWin)

    def runFilter(self,widget):
        self.__oView.runFilter(self.__oMenu.getApplyFilter())
