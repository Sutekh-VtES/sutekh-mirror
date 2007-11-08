# PhysicalCardController.py
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sqlobject import SQLObjectNotFound
from sqlobject.events import Signal
from sutekh.gui.PhysicalCardView import PhysicalCardView
from sutekh.gui.PhysicalCardMenu import PhysicalCardMenu
from sutekh.core.SutekhObjects import PhysicalCard, \
        AbstractCard, PhysicalCardSet, IExpansion, \
        MapPhysicalCardToPhysicalCardSet

class ReloadSignal(Signal):
    """Syncronisation signal for card sets. Needs to be sent after
       changes are commited to the database, so card sets can reload
       properly
    """

class PhysicalCardController(object):
    def __init__(self, oFrame, oConfig, oMainWindow):
        self.__oMainWin = oMainWindow
        self.__oFrame = oFrame
        self.__oView = PhysicalCardView(self, oMainWindow, oConfig)
        self._sFilterType = 'PhysicalCard'

    view = property(fget=lambda self: self.__oView, doc="Associated View")
    frame = property(fget=lambda self: self.__oFrame, doc="Associated Frame")
    filtertype = property(fget=lambda self: self._sFilterType, doc="Associated Type")

    def getView(self):
        return self.__oView

    def decCard(self, sName, sExpansion):
        """
        Returns True if a card was successfully removed, False otherwise.
        """
        try:
            oC = AbstractCard.byCanonicalName(sName.lower())
        except SQLObjectNotFound:
            return False

        if sExpansion is None:
            # Removing a card in the list
            cardCands = PhysicalCard.selectBy(abstractCardID=oC.id)
            # check we found something?
            if cardCands.count() == 0:
                raise RuntimeError("Model inconsistent with the database")
            # Logic is:
            # Prefer cards with no expansion set and in no PCS
            # else cards in no PCS
            # else card in the fewest PCS's
            dPCS = {}
            aCandsExpansion = []
            for oPhysCard in cardCands.reversed():
                aCardSetMapping = list(MapPhysicalCardToPhysicalCardSet.selectBy(physicalCardID=oPhysCard.id))
                iCount = len(aCardSetMapping)
                if iCount == 0:
                    if oPhysCard.expansion is None:
                        # OK, can delete this one and be done with it
                        self.view._oModel.decCardExpansionByName(oC.name, None)
                        self.view._oModel.decCardByName(oC.name)
                        PhysicalCard.delete(oPhysCard.id)
                        PhysicalCard.sqlmeta.send(ReloadSignal, oC)
                        return True
                    else:
                        aCandsExpansion.append(oPhysCard)
                dPCS[oPhysCard] = [iCount, [x.physicalCardSet for x in aCardSetMapping]]
            if len(aCandsExpansion) > 0:
                # ditto
                oPhysCard = aCandsExpansion[-1]
                self.view._oModel.decCardExpansionByName(oC.name, oPhysCard.expansion.name)
                self.view._oModel.decCardByName(oC.name)
                PhysicalCard.delete(oPhysCard.id)
                PhysicalCard.sqlmeta.send(ReloadSignal, oC)
                return True
            # All physical cards are assigned to PhysicalCardSets, so find the
            # one in the fewest
            aList = sorted(dPCS.items(),key=lambda x: x[1][0], reverse=True)
            # Sort by count, take the last one as smallest
            oPhysCard, (iCnt, aPCS) = aList[-1]
            # This is probably overcomplicated, need to revisit this sometime
            # Prompt the user for confirmation
            if iCnt > 1:
                sText = "Card Present in the following %d Physical Card Sets:\n" % iCnt
            else:
                sText = "Card Present in the following Physical Card Set:\n"
            for oPCS in aPCS:
                sText += "<span foreground = \"blue\">" + oPCS.name + "</span>\n"
            sText += "<b>Really Delete?</b>"
            oDialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_QUESTION,
                    gtk.BUTTONS_YES_NO, None)
            oDialog.set_markup(sText)
            iResponse = oDialog.run()
            oDialog.destroy()
            if iResponse == gtk.RESPONSE_YES:
                # User agrees
                # Delete card from all the PhysicalCardSets first
                for oPCS in aPCS:
                    oPCS.removePhysicalCard(oPhysCard.id)
                if oPhysCard.expansion is not None:
                    self.view._oModel.decCardExpansionByName(oC.name, oPhysCard.expansion.name)
                else:
                    self.view._oModel.decCardExpansionByName(oC.name, None)
                self.view._oModel.decCardByName(oC.name)
                PhysicalCard.delete(oPhysCard.id)
                # SQLObject Events should take care of updating any open card sets
                PhysicalCard.sqlmeta.send(ReloadSignal, oC)
        else:
            # We are fiddling between the expansions
            oThisExpansion = IExpansion(sExpansion)
            aPhysCards = list(PhysicalCard.selectBy(abstractCardID=oC.id, expansionID=oThisExpansion.id))
            if len(aPhysCards) < 1:
                raise RuntimeError("Model inconsistent with the database")
            oThisCard = aPhysCards[-1] # last card, general principles
            # Update card
            oThisCard.expansion = None
            oThisCard.sync()
            # Update model
            self.view._oModel.decCardExpansionByName(oC.name, sExpansion)
            self.view._oModel.incCardExpansionByName(oC.name, None)
            PhysicalCard.sqlmeta.send(ReloadSignal, oC)
            return True

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

        if sExpansion is None:
            # Adding a new card to the list
            oPC = PhysicalCard(abstractCard=oC, expansion=None)
            self.view._oModel.incCardByName(oC.name)
            self.view._oModel.incCardExpansionByName(oC.name, sExpansion)
            PhysicalCard.sqlmeta.send(ReloadSignal, oC)
        else:
            # We are fiddling between the expansions
            # Find a card with no expansion
            aPhysCards = list(PhysicalCard.selectBy(abstractCardID=oC.id, expansionID=None))
            if len(aPhysCards) < 1:
                raise RuntimeError("Model inconsistent with the database")
            oThisCard = aPhysCards[-1] # last card, general principles
            # Update card
            oThisCard.expansion = IExpansion(sExpansion)
            oThisCard.sync()
            # Update model
            self.view._oModel.decCardExpansionByName(oC.name, None)
            self.view._oModel.incCardExpansionByName(oC.name, sExpansion)
            PhysicalCard.sqlmeta.send(ReloadSignal, oC)
        return True

    def setCardText(self, sCardName):
        self.__oMainWin.set_card_text(sCardName)

