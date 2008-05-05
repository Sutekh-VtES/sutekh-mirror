# CardListModel.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""The gtk.TreeModel for the card lists."""

from sutekh.core.Filters import PhysicalCardSetFilter
from sutekh.core.SutekhObjects import PhysicalCard, IExpansion, \
        MapPhysicalCardToPhysicalCardSet
from sutekh.gui.CardListModel import CardListModel


class CardSetCardListModel(CardListModel):
    # pylint: disable-msg=R0904
    # inherit a lot of public methods for gtk
    """CardList Model specific to lists of physical cards.

       Handles the constraint that the available number of cards
       is determined by the Physical Card Collection.
       """
    def __init__(self, sSetName):
        super(CardSetCardListModel, self).__init__()
        self._cCardClass = MapPhysicalCardToPhysicalCardSet
        self._oBaseFilter = PhysicalCardSetFilter(sSetName)
        self.bExpansions = True

    def check_inc_dec_card(self, oCard, iCnt):
        """Helper function to check whether card can be incremented"""
        if not self.bEditable:
            return False, False
        else:
            return (iCnt <
                    PhysicalCard.selectBy(abstractCardID=oCard.id).count(),
                    iCnt > 0)

    def check_inc_dec_expansion(self, oCard, sExpansion, iCnt):
        """Helper function to check status of expansions"""
        # pylint: disable-msg=E1101
        # SQLObject confuses pylint
        if sExpansion != self.sUnknownExpansion:
            iThisExpID = IExpansion(sExpansion).id
            iCardCnt = PhysicalCard.selectBy(abstractCardID=oCard.id,
                    expansionID=iThisExpID).count()
        else:
            iCardCnt = PhysicalCard.selectBy(abstractCardID=oCard.id,
                    expansionID=None).count()
        bDecCard = iCnt > 0
        bIncCard = iCnt < iCardCnt
        return bIncCard, bDecCard

    def get_expansion_info(self, oCard, dExpanInfo):
        """Get information about expansions"""
        dExpansions = {}
        return dExpansions
        if not self.bExpansions:
            return dExpansions
        if self.bEditable:
            # Need to find all possible expansions in the PhysicalCard List
            dCount = {}
            for oPC in PhysicalCard.selectBy(abstractCardID=oCard.id):
                if oPC.expansion is not None:
                    sName = oPC.expansion.name
                else:
                    sName = self.sUnknownExpansion
                # There is a Physical Card here, so by default bIncCard must
                # be true. Loop below will correct this when needed
                dExpansions.setdefault(sName, [0, False, True])
                dCount.setdefault(sName, 0)
                dCount[sName] += 1
        for oExpansion, iCnt in dExpanInfo.iteritems():
            bDecCard = False
            bIncCard = False
            if oExpansion is not None:
                sKey = oExpansion.name
            else:
                sKey = self.sUnknownExpansion
            if self.bEditable:
                iCardCnt = dCount.get(sKey, 0) # Return 0 for unknown keys
                bDecCard = iCnt > 0
                # Are cards of this expansion still available in the PC list?
                bIncCard = iCnt < iCardCnt
            dExpansions[sKey] = [iCnt, bDecCard, bIncCard]
        return dExpansions

    def check_expansion_iter_stays(self, oCard, sExpansion, iCnt):
        """Check if the expansion entry should remain in the table"""
        # pylint: disable-msg=E1101
        # SQLObject confuses pylint
        if iCnt > 0:
            return True
        if self.bEditable:
            # Only stays visible if cards in the PhysicalCardList with
            # this expansion
            if sExpansion != self.sUnknownExpansion:
                iThisExpID = IExpansion(sExpansion).id
                iCardCnt = PhysicalCard.selectBy(abstractCardID=oCard.id,
                        expansionID=iThisExpID).count()
            else:
                iCardCnt = PhysicalCard.selectBy(abstractCardID=oCard.id,
                        expansionID=None).count()
            return iCardCnt > 0
        else:
            # Not editable, and iCnt == 0, so remove
            return False

    def get_add_card_expansion_info(self, oCard, dExpanInfo):
        """Get the expansions to list for a newly added card"""
        if not self.bExpansions:
            return []
        if self.bEditable:
            aAddedExpansions = []
            for oPC in PhysicalCard.selectBy(abstractCardID=oCard.id):
                if oPC.expansion is not None:
                    sExpName = oPC.expansion.name
                else:
                    sExpName = self.sUnknownExpansion
                if sExpName not in aAddedExpansions:
                    # Only each expansion once
                    aAddedExpansions.append(sExpName)
        else:
            aAddedExpansions = dExpanInfo.keys()
        return aAddedExpansions

