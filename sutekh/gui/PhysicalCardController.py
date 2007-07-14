# PhysicalCardController.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

from sqlobject import SQLObjectNotFound
from sutekh.gui.PhysicalCardView import PhysicalCardView
from sutekh.gui.PhysicalCardMenu import PhysicalCardMenu
from sutekh.gui.DeleteCardDialog import DeleteCardDialog
from sutekh.SutekhObjects import PhysicalCard, AbstractCard, PhysicalCardSet

class PhysicalCardController(object):
    def __init__(self,oWindow,oMasterController):
        self.__oView = PhysicalCardView(self,oWindow)
        self.__oC = oMasterController
        self.__oWin = oWindow

        # setup plugins before the menu (which needs a list of plugins)
        self.__aPlugins = []
        for cPlugin in oMasterController.getPluginManager().getCardListPlugins():
            self.__aPlugins.append(cPlugin(self.__oView,self.__oView.getModel(),'PhysicalCard'))

        self.__oMenu = PhysicalCardMenu(self,self.__oWin)

    def getView(self):
        return self.__oView

    def getMenu(self):
        return self.__oMenu

    def getPlugins(self):
        return self.__aPlugins

    def decCard(self,sName):
        """
        Returns True if a card was successfully removed, False otherwise.
        """
        try:
            oC = AbstractCard.byCanonicalName(sName.lower())
        except SQLObjectNotFound:
            return False

        # Go from Name to Abstract Card ID to Physical card ID
        # which is needed for delete
        # find Physical cards cards with this name
        cardCands = PhysicalCard.selectBy(abstractCardID=oC.id)

        # check we found something?
        if cardCands.count()==0:
            return False

        # Loop throgh list and see if we can find a card
        # not present in any PCS
        dPCS = {}
        aPhysicalCardSets = PhysicalCardSet.select()
        for card in cardCands.reversed():
            idtodel = card.id
            dPCS[idtodel]=[0,[]]
            for oPCS in aPhysicalCardSets:
                subset=[x for x in oPCS.cards if x.id == idtodel]
                if len(subset)>0:
                    dPCS[idtodel][0]+=1;
                    dPCS[idtodel][1].append(oPCS.name)
            if dPCS[idtodel][0]==0:
                # OK, can delete this one and be done with it
                PhysicalCard.delete(idtodel)
                return True
        # All physical cards are assigned to PhysicalCardSets, so find the
        # one in the fewest
        T=min(dPCS.values())
        aList=[x for x in dPCS if T is dPCS[x]]
        idtodel=aList[-1]
        candtodel=dPCS[idtodel]
        # This is probably overcomplicated, need to revisit this sometime
        # Prompt the user for confirmation
        Dialog = DeleteCardDialog(self.__oWin,candtodel[1])
        Dialog.run()
        if Dialog.getResult():
            # User agrees
            # Delete card from all the PhysicalCardSets first
            for sPCS in candtodel[1]:
                oPC = PhysicalCardSet.byName(sPCS)
                oPC.removePhysicalCard(idtodel)
            PhysicalCard.delete(idtodel)
            # Reload everything
            self.__oC.reloadAllPhysicalCardSets()
            return True

    def incCard(self,sName):
        """
        Returns True if a card was successfully added, False otherwise.
        """
        return self.addCard(sName)

    def addCard(self,sName,sExpansion=None):
        """
        Returns True if a card was successfully added, False otherwise.
        """
        try:
            oC = AbstractCard.byCanonicalName(sName.lower())
        except SQLObjectNotFound:
            return False

        oPC = PhysicalCard(abstractCard=oC,expansion=sExpansion)
        return True

    def setCardText(self,sCardName):
        self.__oC.setCardText(sCardName)

    def getFilter(self,oWidget):
        self.__oView.getFilter(self.__oMenu)

    def runFilter(self,oWidget):
        self.__oView.runFilter(self.__oMenu.getApplyFilter())
