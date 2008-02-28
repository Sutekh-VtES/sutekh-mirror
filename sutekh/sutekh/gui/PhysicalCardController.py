# PhysicalCardController.py
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sqlobject import SQLObjectNotFound
from sutekh.gui.DBSignals import send_reload_signal
from sutekh.gui.SutekhDialog import do_complaint
from sutekh.gui.PhysicalCardView import PhysicalCardView
from sutekh.core.SutekhObjects import PhysicalCard, \
        AbstractCard, IExpansion, \
        MapPhysicalCardToPhysicalCardSet

class PhysicalCardController(object):
    def __init__(self, oFrame, oConfig, oMainWindow):
        self.__oMainWin = oMainWindow
        self.__oConfig = oConfig
        self.__oFrame = oFrame
        self.__oView = PhysicalCardView(self, oMainWindow, oConfig)
        self._sFilterType = 'PhysicalCard'

    view = property(fget=lambda self: self.__oView, doc="Associated View")
    model = property(fget=lambda self: self.__oView._oModel, doc="View's Model")
    frame = property(fget=lambda self: self.__oFrame, doc="Associated Frame")
    config_file = property(fget=lambda self: self.__oConfig)
    filtertype = property(fget=lambda self: self._sFilterType, doc="Associated Type")

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
                        PhysicalCard.delete(oPhysCard.id)
                        self.model.decCardExpansionByName(oC.name, None)
                        self.model.decCardByName(oC.name)
                        send_reload_signal(oC)
                        return True
                    else:
                        aCandsExpansion.append(oPhysCard)
                dPCS[oPhysCard] = [iCount, [x.physicalCardSet for x in aCardSetMapping]]
            if len(aCandsExpansion) > 0:
                # ditto
                oPhysCard = aCandsExpansion[-1]
                sExpName = oPhysCard.expansion.name
                PhysicalCard.delete(oPhysCard.id)
                self.model.decCardExpansionByName(oC.name, sExpName)
                self.model.decCardByName(oC.name)
                send_reload_signal(oC)
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
            iResponse = do_complaint(sText, gtk.MESSAGE_QUESTION,
                    gtk.BUTTONS_YES_NO, True)
            if iResponse == gtk.RESPONSE_YES:
                # User agrees
                # Delete card from all the PhysicalCardSets first
                for oPCS in aPCS:
                    oPCS.removePhysicalCard(oPhysCard.id)
                oExpansion = oPhysCard.expansion
                PhysicalCard.delete(oPhysCard.id)
                if oExpansion is not None:
                    self.model.decCardExpansionByName(oC.name, oExpansion.name)
                else:
                    self.model.decCardExpansionByName(oC.name, None)
                self.model.decCardByName(oC.name)
                # SQLObject Events should take care of updating any open card sets
                send_reload_signal(oC)
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
            self.model.decCardExpansionByName(oC.name, sExpansion)
            self.model.incCardExpansionByName(oC.name, None)
            send_reload_signal(oC)
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
            self.model.incCardByName(oC.name)
            self.model.incCardExpansionByName(oC.name, sExpansion)
            send_reload_signal(oC)
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
            self.model.decCardExpansionByName(oC.name, None)
            self.model.incCardExpansionByName(oC.name, sExpansion)
            send_reload_signal(oC)
        return True

    def set_card_text(self, sCardName):
        self.__oMainWin.set_card_text(sCardName)

