# CardSetListModel.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""The gtk.TreeModel for the card lists."""

from sutekh.core.Filters import FilterAndBox, SpecificCardFilter, NullFilter, \
        PhysicalCardSetFilter
from sutekh.core.SutekhObjects import PhysicalCard, IExpansion, AbstractCard, \
        MapPhysicalCardToPhysicalCardSet, IAbstractCard, IPhysicalCard
from sutekh.gui.CardListModel import CardListModel


class CardSetCardListModel(CardListModel):
    # pylint: disable-msg=R0904, R0902
    # inherit a lot of public methods for gtk, need local attributes for state
    """CardList Model specific to lists of physical cards.

       Handles the constraint that the available number of cards
       is determined by the Physical Card Collection.
       """
    def __init__(self, sSetName):
        super(CardSetCardListModel, self).__init__()
        self._cCardClass = MapPhysicalCardToPhysicalCardSet
        self._oBaseFilter = PhysicalCardSetFilter(sSetName)
        self.bExpansions = True
        self.bAddAllAbstractCards = False
        self.bEditable = False

    def load(self):
        # pylint: disable-msg=R0914
        # we use many local variables for clarity
        """
        Clear and reload the underlying store. For use after initialisation or when
        the filter or grouping changes.
        """
        self.clear()
        self._dName2Iter = {}
        self._dNameExpansion2Iter = {}
        self._dGroupName2Iter = {}

        oCardIter = self.get_card_iterator(self.get_current_filter())
        fGetCard, fGetCount, fGetExpanInfo, oGroupedIter, aAbsCards = \
                self.grouped_card_iter(oCardIter)

        self.oEmptyIter = None

        # Iterate over groups
        for sGroup, oGroupIter in oGroupedIter:
            # Check for null group
            if sGroup is None:
                sGroup = '<< None >>'

            # Create Group Section
            oSectionIter = self.append(None)
            self._dGroupName2Iter[sGroup] = oSectionIter

            # Fill in Cards
            iGrpCnt = 0
            for oItem in oGroupIter:
                oCard, iCnt = fGetCard(oItem), fGetCount(oItem)
                iGrpCnt += iCnt
                oChildIter = self.append(oSectionIter)
                bIncCard, bDecCard = self.check_inc_dec_card(oCard, iCnt)
                self.set(oChildIter,
                    0, oCard.name,
                    1, iCnt,
                    2, 0,
                    3, bIncCard,
                    4, bDecCard
                )
                dExpansionInfo = self.get_expansion_info(oCard,
                        fGetExpanInfo(oItem))
                # fill in the numbers for all possible expansions for
                # the card
                for sExpansion in sorted(dExpansionInfo):
                    self._add_expansion(oChildIter, oCard.name, sExpansion,
                            dExpansionInfo[sExpansion])
                self._dName2Iter.setdefault(oCard.name, []).append(oChildIter)


            # Update Group Section
            self.set(oSectionIter,
                0, sGroup,
                1, iGrpCnt,
                2, 0,
                3, False,
                4, False
            )

        if not self._dName2Iter:
            # Showing nothing
            self.oEmptyIter = self.append(None)
            sText = self._get_empty_text()
            self.set(self.oEmptyIter, 0, sText, 1, 0, 2, 0, 3, False, 4, False)

        # Notify Listeners
        for oListener in self.dListeners:
            oListener.load(aAbsCards)


    def check_inc_dec_card(self, oCard, iCnt):
        """Helper function to check whether card can be incremented"""
        if not self.bEditable:
            return False, False
        else:
            return (iCnt <
                    PhysicalCard.selectBy(abstractCardID=oCard.id).count(),
                    iCnt > 0)

    def _add_expansion(self, oChildIter, sCardName, sExpansion, tExpInfo):
        """Add an expansion to the card list model."""
        oExpansionIter = self.append(oChildIter)
        iExpCnt, bDecCard, bIncCard = tExpInfo
        self.set(oExpansionIter,
                0, sExpansion,
                1, iExpCnt,
                2, 0,
                3, bIncCard,
                4, bDecCard)
        self._dNameExpansion2Iter.setdefault(sCardName,
                {}).setdefault(sExpansion, []).append(oExpansionIter)


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


    def grouped_card_iter(self, oCardIter):
        """
        Handles the differences in the way AbstractCards and PhysicalCards
        are grouped and returns a triple of fGetCard (the function used to
        retrieve a card from an item), fGetCount (the function used to
        retrieve a card count from an item) and oGroupedIter (an iterator
        over the card groups)
        """
        # Define iterable and grouping function based on cardclass
        aAbsCards = []
        fGetCard = lambda x:x[0]
        fGetCount = lambda x:x[1][0]
        fGetExpanInfo = lambda x:x[1][1]

        # Count by Abstract Card
        dAbsCards = {}
        if self.bAddAllAbstractCards:
            # Also include all the abstract cards
            oAbsFilter = self.get_current_filter()
            if oAbsFilter is None:
                oAbsFilter = NullFilter()
            if 'AbstractCard' in oAbsFilter.types:
                oAbsCardIter = oAbsFilter.select(AbstractCard)
                for oAbsCard in oAbsCardIter:
                    dAbsCards.setdefault(oAbsCard, [0, {}])
            # If the filter is PhysicalCard specific we ignore it, as
            # AbstractCards don't have that information, so we cannot
            # decide when to display 0 counts properly
        for oCard in oCardIter:
            # pylint: disable-msg=E1101
            # sqlobject confuses pylint
            oPhysCard = IPhysicalCard(oCard)
            oAbsCard = IAbstractCard(oPhysCard)
            aAbsCards.append(oAbsCard)
            dAbsCards.setdefault(oAbsCard, [0, {}])
            dAbsCards[oAbsCard][0] += 1
            if self.bExpansions:
                dExpanInfo = dAbsCards[oAbsCard][1]
                dExpanInfo.setdefault(oPhysCard.expansion, 0)
                dExpanInfo[oPhysCard.expansion] += 1

        aCards = list(dAbsCards.iteritems())
        aCards.sort(lambda x, y: cmp(x[0].name, y[0].name))

        # Iterate over groups
        return (fGetCard, fGetCount, fGetExpanInfo,
                self.groupby(aCards, fGetCard), aAbsCards)



    def inc_card(self, oPath):
        """
        Add a copy of the card at oPath from the model
        """
        sCardName = self.get_card_name_from_path(oPath)
        self.alter_card_count(sCardName, +1)

    def dec_card(self, oPath):
        """
        Remove a copy of the card at oPath from the model
        """
        sCardName = self.get_card_name_from_path(oPath)
        self.alter_card_count(sCardName, -1)

    def inc_card_expansion_by_name(self, sCardName, sExpansion):
        """
        Increases the expansion count for this card without changing the
        total card count. Should be paired with calls to inc_card_by_name
        or dec_card_expansion_by_name for consistency
        """
        if sExpansion is None:
            sExpansion = self.sUnknownExpansion
        if self._dNameExpansion2Iter.has_key(sCardName):
            if self._dNameExpansion2Iter[sCardName].has_key(sExpansion):
                self.alter_card_expansion_count(sCardName, sExpansion, +1)
            else:
                self.add_new_card_expansion(sCardName, sExpansion)

    def dec_card_expansion_by_name(self, sCardName, sExpansion):
        """
        Decreases the expansion count for this card without changing total
        card count. Should be paired with calls to dec_card_by_name or
        inc_card_expansion_by_name for consistency
        """
        if sExpansion is None:
            sExpansion = self.sUnknownExpansion
        if self._dNameExpansion2Iter.has_key(sCardName) and \
                self._dNameExpansion2Iter[sCardName].has_key(sExpansion):
            self.alter_card_expansion_count(sCardName, sExpansion, -1)

    def inc_card_by_name(self, sCardName):
        """Increase the count for the card named sCardName, add a new
           card entry is nessecary."""
        if self._dName2Iter.has_key(sCardName):
            # card already in the list
            self.alter_card_count(sCardName, +1)
        else:
            # new card
            self.add_new_card(sCardName)

    def dec_card_by_name(self, sCardName):
        """Decrease the count for the card sCardName"""
        if self._dName2Iter.has_key(sCardName):
            self.alter_card_count(sCardName, -1)

    def add_new_card_expansion(self, sCardName, sExpansion):
        """Add a card with expansion to the model"""
        oCard = IAbstractCard(sCardName)
        aParenIters = self._dName2Iter[sCardName]
        self._dNameExpansion2Iter[sCardName][sExpansion] = []
        # pylint: disable-msg=W0612
        # x is loop variable here
        aSiblings = [None for x in aParenIters]
        for sThisExp in sorted(self._dNameExpansion2Iter[sCardName]):
            if sThisExp == sExpansion:
                iCnt = 1
                if self.bEditable:
                    bIncCard, bDecCard = self.check_inc_dec_expansion(
                            oCard, sThisExp, iCnt)
                else:
                    bIncCard, bDecCard = False, False
                for oParent, oSibling in zip(aParenIters, aSiblings):
                    oIter = self.insert_after(oParent, oSibling)
                    self.set(oIter,
                            0, sThisExp,
                            1, iCnt,
                            2, 0,
                            3, bIncCard,
                            4, bDecCard)
                    self._dNameExpansion2Iter[sCardName][
                            sExpansion].append(oIter)
            else:
                aSiblings = self._dNameExpansion2Iter[sCardName][sThisExp]

        # Notify Listeners
        for oListener in self.dListeners:
            oListener.add_new_card_expansion(oCard, sExpansion)

    def alter_card_expansion_count(self, sCardName, sExpansion, iChg):
        """Adjust the count for the given card + expansion combination by
           iChg."""
        # Need to readjust inc, dec flags for all these cards
        oCard = IAbstractCard(sCardName)
        bDelDictEntry = False
        if not self._dNameExpansion2Iter.has_key(sCardName):
            # Can be called by CardSetController with non-existant card
            return
        for sThisExp, aList in \
                self._dNameExpansion2Iter[sCardName].iteritems():
            for oIter in aList:
                iCnt = self.get_value(oIter, 1)
                if sThisExp == sExpansion:
                    iCnt += iChg
                if self.bEditable:
                    bIncCard, bDecCard = self.check_inc_dec_expansion(
                            oCard, sThisExp, iCnt)
                else:
                    bIncCard, bDecCard = False, False
                if self.check_expansion_iter_stays(oCard, sThisExp, iCnt):
                    self.set(oIter,
                            1, iCnt,
                            2, 0,
                            3, bIncCard,
                            4, bDecCard)
                else:
                    self.remove(oIter)
                    bDelDictEntry = True
        if bDelDictEntry:
            del self._dNameExpansion2Iter[sCardName][sExpansion]

        # Notify Listeners
        for oListener in self.dListeners:
            oListener.alter_card_expansion_count(oCard, sExpansion, iChg)

    def alter_card_count(self, sCardName, iChg):
        """
        Alter the card count of a card which is in the
        current list (i.e. in the card set and not filtered
        out) by iChg.
        """
        oCard = IAbstractCard(sCardName)
        for oIter in self._dName2Iter[sCardName]:
            oGrpIter = self.iter_parent(oIter)
            iCnt = self.get_value(oIter, 1) + iChg
            iGrpCnt = self.get_value(oGrpIter, 1) + iChg

            if iCnt > 0:
                self.set(oIter, 1, iCnt, 2, 0)
                bIncCard, bDecCard = self.check_inc_dec_card(oCard, iCnt)
                self.set(oIter, 3, bIncCard)
                self.set(oIter, 4, bDecCard)
            elif self.bAddAllAbstractCards:
                # Need to clean up all the children
                self.set(oIter, 1, iCnt, 2, 0)
                bIncCard, bDecCard = self.check_inc_dec_card(oCard, iCnt)
                self.set(oIter, 3, bIncCard)
                self.set(oIter, 4, bDecCard)
                if self._dNameExpansion2Iter.has_key(sCardName):
                    self._clear_expansion_iters(sCardName)
            else:
                if self._dNameExpansion2Iter.has_key(sCardName):
                    self._remove_expansion_iters(sCardName)
                self.remove(oIter)

            if iGrpCnt > 0 or self.bAddAllAbstractCards:
                self.set(oGrpIter, 1, iGrpCnt, 2, 0)
            else:
                sGroupName = self.get_value(oGrpIter, 0)
                del self._dGroupName2Iter[sGroupName]
                self.remove(oGrpIter)

        if iCnt <= 0 and not self.bAddAllAbstractCards:
            del self._dName2Iter[sCardName]

        if self.oEmptyIter and iChg > 0:
            # Can no longer be empty
            self.remove(self.oEmptyIter)
            self.oEmptyIter = None
        elif iChg < 0 and not self._dName2Iter:
            self.oEmptyIter = self.append(None)
            sText = self._get_empty_text()
            self.set(self.oEmptyIter, 0, sText, 1, 0, 2, 0, 3, False, 4, False)

        # Notify Listeners
        for oListener in self.dListeners:
            oListener.alter_card_count(oCard, iChg)

    def add_new_card(self, sCardName):
        # pylint: disable-msg=R0914
        # we use many local variables for clarity
        """
        If the card sCardName is not in the current list
        (i.e. is not in the card set or is filtered out)
        see if it should be filtered out or if it should be
        visible. If it should be visible, add it to the appropriate
        groups.
        """
        oFilter = self.combine_filter_with_base(self.get_current_filter())
        oFullFilter = FilterAndBox([SpecificCardFilter(sCardName), oFilter])

        oCardIter = oFullFilter.select(self.cardclass).distinct()

        # pylint: disable-msg=W0612
        # Not interested in aAbsCards here, but we need the rest
        fGetCard, fGetCount, fGetExpanInfo, oGroupedIter, aAbsCards = \
                self.grouped_card_iter(oCardIter)
        # Iterate over groups
        for sGroup, oGroupIter in oGroupedIter:
            # Check for null group
            if sGroup is None:
                sGroup = '<< None >>'

            # Find Group Section
            if self._dGroupName2Iter.has_key(sGroup):
                oSectionIter = self._dGroupName2Iter[sGroup]
                iGrpCnt = self.get_value(oSectionIter, 1)
            else:
                oSectionIter = self.append(None)
                self._dGroupName2Iter[sGroup] = oSectionIter
                iGrpCnt = 0
                self.set(oSectionIter,
                    0, sGroup,
                    1, iGrpCnt,
                    2, 0,
                )

            # Add Cards
            for oItem in oGroupIter:
                oCard, iCnt = fGetCard(oItem), fGetCount(oItem)
                iGrpCnt += iCnt
                oChildIter = self.append(oSectionIter)
                bIncCard, bDecCard = self.check_inc_dec_card(oCard, iCnt)
                self.set(oChildIter,
                    0, oCard.name,
                    1, iCnt,
                    2, 0,
                    3, bIncCard,
                    4, bDecCard
                )
                self._dName2Iter.setdefault(oCard.name, []).append(oChildIter)

                aExpansions = self.get_add_card_expansion_info(oCard,
                        fGetExpanInfo(oItem))

                for sExpName in aExpansions:
                    self._dNameExpansion2Iter.setdefault(oCard.name, {})
                    # For models with expansions, this will be paired with a
                    # call to inc Expansion count. We rely on this to sort
                    # out details - here we just create the needed space.
                    self._add_expansion(oChildIter, oCard.name, sExpName,
                            (0, False, False))

            # Update Group Section
            self.set(oSectionIter,
                1, iGrpCnt,
                2, 0,
            )

        if self.oEmptyIter and oCardIter.count() > 0:
            # remove previous note
            self.remove(self.oEmptyIter)
            self.oEmptyIter = None

        # Notify Listeners
        oCard = IAbstractCard(sCardName)
        for oListener in self.dListeners:
            oListener.add_new_card(oCard)
