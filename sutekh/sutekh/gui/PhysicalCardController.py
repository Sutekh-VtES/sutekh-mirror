# PhysicalCardController.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Controller for the Physical Card Collection"""

import gtk
from sqlobject import SQLObjectNotFound
from sutekh.gui.DBSignals import send_reload_signal
from sutekh.gui.SutekhDialog import do_complaint
from sutekh.gui.PhysicalCardView import PhysicalCardView
from sutekh.core.SutekhObjects import PhysicalCard, AbstractCard, \
        IExpansion, MapPhysicalCardToPhysicalCardSet

class PhysicalCardController(object):
    """Controller for the Physical Card Collection.

       Provide settings needed for the Physical Card List,
       and suitable card manipulation methods.
       """
    def __init__(self, oFrame, oConfig, oMainWindow):
        self.__oMainWin = oMainWindow
        self.__oConfig = oConfig
        self.__oFrame = oFrame
        self.__oView = PhysicalCardView(self, oMainWindow, oConfig)
        self._sFilterType = 'PhysicalCard'

    # pylint: disable-msg=W0212
    # We provide read access to these items via these properties
    view = property(fget=lambda self: self.__oView, doc="Associated View")
    model = property(fget=lambda self: self.__oView._oModel,
            doc="View's Model")
    frame = property(fget=lambda self: self.__oFrame, doc="Associated Frame")
    config_file = property(fget=lambda self: self.__oConfig,
            doc="Config file object")
    filtertype = property(fget=lambda self: self._sFilterType,
            doc="Associated Type")
    # pylint: enable-msg=W0212

    def dec_card(self, sName, sExpansion):
        """Returns True if a card was successfully removed, False otherwise."""
        # pylint: disable-msg=E1101
        # SQLObject confuses pylint
        try:
            oAbsCard = AbstractCard.byCanonicalName(sName.lower())
        except SQLObjectNotFound:
            return False

        if sExpansion is None:
            # Removing a card in the list
            aCandCards = PhysicalCard.selectBy(abstractCardID=oAbsCard.id)
            # check we found something?
            if aCandCards.count() == 0:
                raise RuntimeError("Model inconsistent with the database")
            # Logic is:
            # Prefer cards with no expansion set and in no PCS
            # else cards in no PCS
            # else card in the fewest PCS's
            dPCS = {}
            aCandsExpansion = []
            for oPhysCard in aCandCards.reversed():
                aCardSetMapping = list(
                        MapPhysicalCardToPhysicalCardSet.selectBy(
                            physicalCardID=oPhysCard.id))
                iCount = len(aCardSetMapping)
                if iCount == 0:
                    if oPhysCard.expansion is None:
                        # OK, can delete this one and be done with it
                        PhysicalCard.delete(oPhysCard.id)
                        self.model.dec_card_expansion_by_name(oAbsCard.name,
                                None)
                        self.model.dec_card_by_name(oAbsCard.name)
                        send_reload_signal(oAbsCard)
                        return True
                    else:
                        aCandsExpansion.append(oPhysCard)
                dPCS[oPhysCard] = [iCount, [x.physicalCardSet for x in
                    aCardSetMapping]]
            if len(aCandsExpansion) > 0:
                # ditto
                oPhysCard = aCandsExpansion[-1]
                sExpName = oPhysCard.expansion.name
                PhysicalCard.delete(oPhysCard.id)
                self.model.dec_card_expansion_by_name(oAbsCard.name, sExpName)
                self.model.dec_card_by_name(oAbsCard.name)
                send_reload_signal(oAbsCard)
                return True
            # All physical cards are assigned to PhysicalCardSets, so find the
            # one in the fewest
            aList = sorted(dPCS.items(), key=lambda x: x[1][0], reverse=True)
            # Sort by count, take the last one as smallest
            oPhysCard, (iCnt, aPCS) = aList[-1]
            # This is probably overcomplicated, need to revisit this sometime
            # Prompt the user for confirmation
            if iCnt > 1:
                sText = "Card Present in the following %d Physical Card" \
                        " Sets:\n" % iCnt
            else:
                sText = "Card Present in the following Physical Card Set:\n"
            for oPCS in aPCS:
                sText += '<span foreground = "blue">%s</span>\n' % oPCS.name
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
                    self.model.dec_card_expansion_by_name(oAbsCard.name,
                            oExpansion.name)
                else:
                    self.model.dec_card_expansion_by_name(oAbsCard.name, None)
                self.model.dec_card_by_name(oAbsCard.name)
                # SQLObject Events should take care of updating any open
                # card sets
                send_reload_signal(oAbsCard)
        else:
            # We are fiddling between the expansions
            oThisExpansion = IExpansion(sExpansion)
            aPhysCards = list(PhysicalCard.selectBy(abstractCardID=oAbsCard.id,
                expansionID=oThisExpansion.id))
            if len(aPhysCards) < 1:
                raise RuntimeError("Model inconsistent with the database")
            oThisCard = aPhysCards[-1] # last card, general principles
            # Update card
            oThisCard.expansion = None
            oThisCard.sync()
            # Update model
            self.model.dec_card_expansion_by_name(oAbsCard.name, sExpansion)
            self.model.inc_card_expansion_by_name(oAbsCard.name, None)
            send_reload_signal(oAbsCard)
            return True

    def inc_card(self, sName, sExpansion):
        """Returns True if a card was successfully added, False otherwise."""
        return self.add_card(sName, sExpansion)

    def add_card(self, sName, sExpansion):
        """Returns True if a card was successfully added, False otherwise."""
        # pylint: disable-msg=E1101
        # SQLObject confuses pylint
        try:
            oAbsCard = AbstractCard.byCanonicalName(sName.lower())
        except SQLObjectNotFound:
            return False

        if sExpansion is None:
            # Adding a new card to the list
            aExpansion = set([oRP.expansion for oRP in oAbsCard.rarity])
            if len(aExpansion) == 1:
                oExpansion = aExpansion.pop()
                sExpansion = oExpansion.name
            else:
                oExpansion = None
            # pylint: disable-msg=W0612
            # Creating a new PhysicalCard in the database is all that is needed
            oNewPC = PhysicalCard(abstractCard=oAbsCard, expansion=oExpansion)
            self.model.inc_card_by_name(oAbsCard.name)
            self.model.inc_card_expansion_by_name(oAbsCard.name, sExpansion)
            send_reload_signal(oAbsCard)
        else:
            # We are fiddling between the expansions
            # Find a card with no expansion
            aPhysCards = list(PhysicalCard.selectBy(abstractCardID=oAbsCard.id,
                expansionID=None))
            if len(aPhysCards) < 1:
                raise RuntimeError("Model inconsistent with the database")
            oThisCard = aPhysCards[-1] # last card, general principles
            # Update card
            oThisCard.expansion = IExpansion(sExpansion)
            oThisCard.sync()
            # Update model
            self.model.dec_card_expansion_by_name(oAbsCard.name, None)
            self.model.inc_card_expansion_by_name(oAbsCard.name, sExpansion)
            send_reload_signal(oAbsCard)
        return True

    def set_card_text(self, sCardName):
        """Set the card text to reflect the selected card."""
        self.__oMainWin.set_card_text(sCardName)

