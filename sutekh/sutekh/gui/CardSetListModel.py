# CardSetListModel.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""The gtk.TreeModel for the card lists."""

from sutekh.core.Filters import FilterAndBox, NullFilter, SpecificCardFilter, \
        FilterOrBox, PhysicalCardSetFilter, SpecificCardIdFilter
from sutekh.core.SutekhObjects import PhysicalCard, IExpansion, \
        MapPhysicalCardToPhysicalCardSet, IAbstractCard, IPhysicalCard, \
        IPhysicalCardSet, PhysicalCardSet
from sutekh.gui.CardListModel import CardListModel

# pylint: disable-msg=C0103
# We break out usual convention here
# consts for the different modes we need
NO_SECOND_LEVEL, SHOW_EXPANSIONS, SHOW_CARD_SETS, EXPANSIONS_AND_CARD_SETS, \
        CARD_SETS_AND_EXPANSIONS = range(5)
# Different card count modes
THIS_SET_ONLY, ALL_CARDS, PARENT_CARDS, CHILD_CARDS = range(4)
# Different Parent card count modes
IGNORE_PARENT, PARENT_COUNT, MINUS_THIS_SET, MINUS_SETS_IN_USE = range(4)
# pylint: enable-msg=C0103

def get_card(oItem):
    """Extract a card name from the grouped iterator"""
    return oItem[0]

def get_card_count(oItem):
    """Extract a card count from the grouped iterator"""
    return oItem[1]['count']

def get_card_expansion_info(oItem):
    """Extract the expansion information"""
    return (oItem[1]['expansions'], oItem[1]['parent']['expansions'])

def get_card_child_set_info(oItem):
    """Extract the child card set information."""
    return oItem[1]['card sets']

def get_par_count(oItem):
    """Get the parent count from the card info."""
    return oItem[1]['parent']['count']

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
        self._oCardSet = IPhysicalCardSet(sSetName)
        self.iExtraLevelsMode = SHOW_EXPANSIONS
        self.bChildren = False
        self.iShowCardMode = THIS_SET_ONLY
        self.bEditable = False
        self._dNameSecondLevel2Iter = {}
        self._dName2nd3rdLevel2Iter = {}
        self.iParentCountMode = PARENT_COUNT
        self.sEditColour = 'red'

    def format_count(self, iCnt):
        if self.bEditable:
            return '<i><span foreground="%s">%d</span></i>' % \
                    (self.sEditColour, iCnt)
        else:
            return '<i>%d</i>' % iCnt

    def load(self):
        # pylint: disable-msg=R0914
        # we use many local variables for clarity
        """
        Clear and reload the underlying store. For use after initialisation or when
        the filter or grouping changes.
        """
        self.clear()
        self._dName2Iter = {}
        self._dNameSecondLevel2Iter = {}
        self._dName2nd3rdLevel2Iter = {}
        self._dGroupName2Iter = {}

        oCardIter = self.get_card_iterator(self.get_current_filter())
        oGroupedIter, aAbsCards = self.grouped_card_iter(oCardIter)

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
            iParGrpCnt = 0
            for oItem in oGroupIter:
                oCard, iCnt = get_card(oItem), get_card_count(oItem)
                iParCnt = get_par_count(oItem)
                iGrpCnt += iCnt
                iParGrpCnt += iParCnt
                oChildIter = self.append(oSectionIter)
                bIncCard, bDecCard = self.check_inc_dec_card(iCnt)
                self.set(oChildIter,
                    0, oCard.name,
                    1, self.format_count(iCnt),
                    2, str(iParCnt),
                    3, bIncCard,
                    4, bDecCard
                )
                if (self.iParentCountMode == PARENT_COUNT and iParCnt < iCnt) \
                        or (iParCnt < 0):
                    self.set(oChildIter, 2,
                            '<span foreground = "red">%d</span>' % iParCnt)
                if self.iExtraLevelsMode == SHOW_EXPANSIONS:
                    dExpansionInfo = self.get_expansion_info(
                            get_card_expansion_info(oItem))
                    for sExpansion in sorted(dExpansionInfo):
                        oSubIter = self._add_extra_level(oChildIter,
                                oCard.name, sExpansion,
                                dExpansionInfo[sExpansion])
                        self._dNameSecondLevel2Iter.setdefault(oCard.name,
                                {}).setdefault(sExpansion, []).append(oSubIter)
                elif self.iExtraLevelsMode == SHOW_CARD_SETS:
                    dChildInfo = self.get_child_info(
                            get_card_child_set_info(oItem), iParCnt)
                    for sChildSet in sorted(dChildInfo):
                        oSubIter = self._add_extra_level(oChildIter,
                                oCard.name, sChildSet, dChildInfo[sChildSet])
                        self._dNameSecondLevel2Iter.setdefault(oCard.name,
                                {}).setdefault(sChildSet,
                                []).append(oSubIter)
                elif self.iExtraLevelsMode == EXPANSIONS_AND_CARD_SETS:
                    dExpansionInfo = self.get_expansion_info(
                            get_card_expansion_info(oItem))
                    dChildInfo = self.get_child_info(
                            get_card_child_set_info(oItem), 0,
                            get_card_expansion_info(oItem))
                    for sExpansion in sorted(dExpansionInfo):
                        oSubIter = self._add_extra_level(oChildIter,
                                oCard.name, sExpansion,
                                dExpansionInfo[sExpansion])
                        self._dNameSecondLevel2Iter.setdefault(oCard.name,
                                {}).setdefault(sExpansion, []).append(oSubIter)
                        for sChildSet in sorted(dChildInfo[sExpansion]):
                            oThisIter = self._add_extra_level(oSubIter,
                                    oCard.name, sChildSet,
                                    dChildInfo[sExpansion][sChildSet])
                            self._dName2nd3rdLevel2Iter.setdefault((
                                oCard.name, sExpansion), {}).setdefault(
                                    sChildSet, []).append(oThisIter)
                elif self.iExtraLevelsMode == CARD_SETS_AND_EXPANSIONS:
                    dChildInfo = self.get_child_info(
                            get_card_child_set_info(oItem), iParCnt)
                    dExpansionInfo = self.get_expansion_info(
                            get_card_expansion_info(oItem),
                            get_card_child_set_info(oItem))
                    for sChildSet in sorted(dChildInfo):
                        oSubIter = self._add_extra_level(oChildIter,
                                oCard.name, sChildSet, dChildInfo[sChildSet])
                        self._dNameSecondLevel2Iter.setdefault(oCard.name,
                                {}).setdefault(sChildSet, []).append(oSubIter)
                        for sExpansion in dExpansionInfo[sChildSet]:
                            oThisIter = self._add_extra_level(oSubIter,
                                    oCard.name, sExpansion,
                                    dExpansionInfo[sChildSet][sExpansion])
                            self._dName2nd3rdLevel2Iter.setdefault((
                                oCard.name, sChildSet), {}).setdefault(
                                    sExpansion, []).append(oThisIter)
                self._dName2Iter.setdefault(oCard.name, []).append(oChildIter)

            # Update Group Section
            self.set(oSectionIter,
                0, sGroup,
                1, self.format_count(iGrpCnt),
                2, str(iParGrpCnt),
                3, False,
                4, False
            )

        if not self._dName2Iter:
            # Showing nothing
            self.oEmptyIter = self.append(None)
            sText = self._get_empty_text()
            self.set(self.oEmptyIter, 0, sText, 1, self.format_count(0), 2,
                    '0', 3, False, 4, False)

        # Notify Listeners
        for oListener in self.dListeners:
            oListener.load(aAbsCards)


    def check_inc_dec_card(self, iCnt):
        """Helper function to check whether card can be incremented"""
        if not self.bEditable:
            return False, False
        else:
            return True, (iCnt > 0)

    def _add_extra_level(self, oChildIter, sCardName, sName, tInfo):
        """Add an extra level iterator to the card list model."""
        oIter = self.append(oChildIter)
        iCnt, iParCnt, bIncCard, bDecCard = tInfo
        self.set(oIter,
                0, sName,
                1, self.format_count(iCnt),
                2, str(iParCnt),
                3, bIncCard,
                4, bDecCard)
        # FIXME: Sort out the caching aspects for editing
        return oIter

    def check_inc_dec_expansion(self, iCnt):
        """Helper function to check status of expansions"""
        if not self.bEditable:
            return False, False
        return True, (iCnt > 0)

    def get_expansion_info(self, tExpanInfo, dChildInfo=None):
        """Get information about expansions"""
        dExpanInfo, dParents = tExpanInfo
        dExpansions = {}
        if not dChildInfo:
            for oExpansion, iCnt in dExpanInfo.iteritems():
                bIncCard = False
                bDecCard = False
                if oExpansion is not None:
                    sKey = oExpansion.name
                else:
                    sKey = self.sUnknownExpansion
                if self.bEditable:
                    bIncCard = True
                    bDecCard = iCnt > 0
                iParCnt = dParents.get(oExpansion, 0)
                dExpansions[sKey] = [iCnt, iParCnt, bIncCard, bDecCard]
        else:
            # FIXME: work out how to present editing options when showing
            # expansions + card sets
            for sChildSet in dChildInfo:
                dExpansions[sChildSet] = {}
                for oExpansion, iCnt in dExpanInfo[sChildSet].iteritems():
                    bIncCard = False
                    bDecCard = False
                    if oExpansion is not None:
                        sKey = oExpansion.name
                    else:
                        sKey = self.sUnknownExpansion
                    iParCnt = dParents.get(oExpansion, 0)
                    dExpansions[sChildSet][sKey] = [iCnt, iParCnt, bIncCard,
                            bDecCard]
        return dExpansions

    def get_child_info(self, dChildInfo, iParCnt, tExpansionInfo=None):
        """Get information about child card sets"""
        dChildren = {}
        if not tExpansionInfo:
            # FIXME: work out how to present editing options when showing
            # card sets + expansions
            for sCardSet, iCnt in dChildInfo.iteritems():
                dChildren[sCardSet] = [iCnt, iParCnt, False, False]
        else:
            # FIXME: work out how to present editing options when showing
            # card sets
            dExpansions, dParents = tExpansionInfo
            for oExpansion in dExpansions:
                if oExpansion is not None:
                    sKey = oExpansion.name
                else:
                    sKey = self.sUnknownExpansion
                dChildren[sKey] = {}
                iParCnt = dParents.get(oExpansion, 0)
                for sCardSet, iCnt in dChildInfo[oExpansion].iteritems():
                    dChildren[sKey][sCardSet] = [iCnt, iParCnt, False, False]
        return dChildren

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

    def get_exp_name_from_path(self, oPath):
        """
        Get the expansion information from the model, returing None
        if this is not at a level where the expansion is known.
        """
        oIter = self.get_iter(oPath)
        if self.iter_depth(oIter) not in [2, 3]:
            return None
        sName = None
        if self.iExtraLevelsMode in [SHOW_EXPANSIONS,
                EXPANSIONS_AND_CARD_SETS] and self.iter_depth(oIter) == 2:
            sName = self.get_name_from_iter(oIter)
        elif self.iExtraLevelsMode == CARD_SETS_AND_EXPANSIONS and \
                self.iter_depth(oIter) == 3:
            sName = self.get_name_from_iter(oIter)
        elif self.iExtraLevelsMode == EXPANSIONS_AND_CARD_SETS and \
                self.iter_depth(oIter) == 3:
            # Need to get information from the parent level
            sName = self.get_name_from_iter(self.iter_parent(oIter))
        return sName


    def grouped_card_iter(self, oCardIter):
        """
        Handles the differences in the way AbstractCards and PhysicalCards
        are grouped and returns a triple of get_card (the function used to
        retrieve a card from an item), get_card_count (the function used to
        retrieve a card count from an item) and oGroupedIter (an iterator
        over the card groups)
        """
        # Define iterable and grouping function based on cardclass
        aAbsCards = []
        dChildFilters = {}

        # pylint: disable-msg=E1101
        # SQLObject + PyProtocols confuse pylint
        if self.iExtraLevelsMode in [SHOW_CARD_SETS, EXPANSIONS_AND_CARD_SETS,
                CARD_SETS_AND_EXPANSIONS] or self.iShowCardMode == CHILD_CARDS:
            # Pre-select cards for child card sets
            aChildren = [x.name for x in
                    PhysicalCardSet.selectBy(parentID=self._oCardSet.id,
                        inuse=True)]
            dChildFilters = {}
            for sName in aChildren:
                dChildFilters[sName] = PhysicalCardSetFilter(sName)


        oCurFilter = self.get_current_filter()
        if oCurFilter is None:
            oCurFilter = NullFilter()
        if self._oCardSet.parent:
            oParentFilter = FilterAndBox([oCurFilter,
                PhysicalCardSetFilter(self._oCardSet.parent.name)])
            oParentIter = oParentFilter.select(self.cardclass).distinct()
        else:
            oParentFilter = None
            oParentIter = []

        # Count by Abstract Card
        dAbsCards = {}
        if self.iShowCardMode != THIS_SET_ONLY:
            # TODO: Revisit the logic once Card Count filters are fixed
            if self.iShowCardMode == ALL_CARDS:
                oExtraCardIter = oCurFilter.select(PhysicalCard).distinct()
            elif self.iShowCardMode == PARENT_CARDS and self._oCardSet.parent:
                # It's tempting to use get_card_iterator here, but that
                # obviously doesn't work because of _oBaseFilter
                oExtraCardIter = oParentIter
            elif self.iShowCardMode == CHILD_CARDS and dChildFilters:
                # We don't use MultiPhysicalCardSet, because of the join issues
                oChildFilter = FilterOrBox([x for x in
                    dChildFilters.itervalues()])
                oFullFilter = FilterAndBox([oCurFilter, oChildFilter])
                oExtraCardIter = oFullFilter.select(self.cardclass).distinct()
            else:
                oExtraCardIter = oCardIter
            for oCard in oExtraCardIter:
                oAbsCard = IAbstractCard(oCard)
                oPhysCard = IPhysicalCard(oCard)
                dAbsCards.setdefault(oAbsCard, {'count' : 0, 'expansions' : {},
                    'card sets' : {}, 'parent' : {}})
                dAbsCards[oAbsCard]['expansions'].setdefault(
                        oPhysCard.expansion, 0)
                dExpanInfo = dAbsCards[oAbsCard]['expansions']
                dChildInfo = dAbsCards[oAbsCard]['card sets']
                if not dChildInfo:
                    self.get_child_set_info(oAbsCard, dChildInfo, dExpanInfo,
                            dChildFilters)

        for oCard in oCardIter:
            # pylint: disable-msg=E1101
            # sqlobject confuses pylint
            oPhysCard = IPhysicalCard(oCard)
            oAbsCard = IAbstractCard(oPhysCard)
            aAbsCards.append(oAbsCard)
            dAbsCards.setdefault(oAbsCard, {'count' : 0, 'expansions' : {},
                'card sets' : {}, 'parent' : {}})
            dAbsCards[oAbsCard]['count'] += 1
            dChildInfo = dAbsCards[oAbsCard]['card sets']
            dExpanInfo = dAbsCards[oAbsCard]['expansions']
            if self.iExtraLevelsMode == SHOW_EXPANSIONS or \
                    self.iExtraLevelsMode == EXPANSIONS_AND_CARD_SETS:
                dExpanInfo.setdefault(oPhysCard.expansion, 0)
                dExpanInfo[oPhysCard.expansion] += 1
            if not dChildInfo and self.iExtraLevelsMode in [
                    SHOW_CARD_SETS, EXPANSIONS_AND_CARD_SETS,
                    CARD_SETS_AND_EXPANSIONS]:
                # Don't re-filter for repeated abstract cards
                self.get_child_set_info(oAbsCard, dChildInfo, dExpanInfo,
                        dChildFilters)
            if self.iExtraLevelsMode == EXPANSIONS_AND_CARD_SETS:
                dChildInfo.setdefault(oPhysCard.expansion, {})

        self._add_parent_info(dAbsCards, oParentIter)

        aCards = list(dAbsCards.iteritems())
        aCards.sort(lambda x, y: cmp(x[0].name, y[0].name))

        # Iterate over groups
        return (self.groupby(aCards, get_card), aAbsCards)

    def get_child_set_info(self, oAbsCard, dChildInfo, dExpanInfo,
            dChildFilters):
        """Fill in info about the child card sets for the grouped iterator"""
        # pylint: disable-msg=E1101
        # Pyprotocols confuses pylint
        oThisCardFilter = SpecificCardIdFilter(oAbsCard.id)
        for sCardSetName, oFilter in dChildFilters.iteritems():
            oFullFilter = FilterAndBox([oThisCardFilter, oFilter])
            aChildCards = oFullFilter.select(self.cardclass).distinct()
            if self.iExtraLevelsMode == SHOW_CARD_SETS or \
                    self.iExtraLevelsMode == CARD_SETS_AND_EXPANSIONS:
                iChildCnt = aChildCards.count()
                if iChildCnt > 0 or self.iShowCardMode == ALL_CARDS:
                    # FIXME: Does this check do what the user would expect?
                    dChildInfo.setdefault(sCardSetName, iChildCnt)
                    if self.iExtraLevelsMode == CARD_SETS_AND_EXPANSIONS:
                        dExpanInfo.setdefault(sCardSetName, {})
                        for oCSCard in aChildCards:
                            oThisPhysCard = IPhysicalCard(oCSCard)
                            dExpanInfo[sCardSetName].setdefault(
                                    oThisPhysCard.expansion, 0)
                            dExpanInfo[sCardSetName][oThisPhysCard.expansion] \
                                    += 1
            elif self.iExtraLevelsMode == EXPANSIONS_AND_CARD_SETS:
                for oCSCard in aChildCards:
                    oThisPhysCard = IPhysicalCard(oCSCard)
                    dChildInfo.setdefault(oThisPhysCard.expansion, {})
                    dChildInfo[oThisPhysCard.expansion].setdefault(
                            sCardSetName, 0)
                    dChildInfo[oThisPhysCard.expansion][sCardSetName] += 1

    def _add_parent_info(self, dAbsCards, oParentIter):
        """Add the parent count info into the mix"""
        # pylint: disable-msg=E1101
        # Pyprotocols confuses pylint
        oInUseFilter = None
        if self.iParentCountMode == MINUS_SETS_IN_USE:
            aChildren = [x.name for x in
                    PhysicalCardSet.selectBy(parentID=self._oCardSet.parent.id,
                        inuse=True)]
            aChildFilters = []
            for sName in aChildren:
                aChildFilters.append(PhysicalCardSetFilter(sName))
            if aChildFilters:
                oInUseFilter = FilterOrBox(aChildFilters)
        for oAbsCard in dAbsCards:
            dParentInfo = dAbsCards[oAbsCard]['parent']
            if self.iParentCountMode == MINUS_THIS_SET:
                dParentInfo.setdefault('count', -dAbsCards[oAbsCard]['count'])
                dParentInfo.setdefault('expansions', {})
                for oExpansion, iCnt in \
                        dAbsCards[oAbsCard]['expansions'].iteritems():
                    dParentInfo['expansions'][oExpansion] = -iCnt
            elif oInUseFilter and not dParentInfo.has_key('count'):
                dParentInfo.setdefault('expansions', {})
                dParentInfo.setdefault('count', 0)
                # Don't do this filter more than once per abstract card
                oThisCardFilter = SpecificCardIdFilter(oAbsCard.id)
                oFullFilter = FilterAndBox([oThisCardFilter, oInUseFilter])
                aChildCards = oFullFilter.select(self.cardclass).distinct()
                for oCSCard in aChildCards:
                    dParentInfo['count'] -= 1
                    oCSPhysCard = IPhysicalCard(oCSCard)
                    dParentInfo['expansions'].setdefault(oCSPhysCard.expansion,
                            0)
                    dParentInfo['expansions'][oCSPhysCard.expansion] -= 1
            else:
                dParentInfo.setdefault('count', 0)
                dParentInfo.setdefault('expansions', {})
        if self.iParentCountMode == IGNORE_PARENT or not self._oCardSet.parent:
            # No point in doing further work
            return
        for oCard in oParentIter:
            # pylint: disable-msg=E1101
            # Pyprotocols confuses pylint
            oAbsCard = IAbstractCard(oCard)
            if oAbsCard in dAbsCards:
                oPhysCard = IPhysicalCard(oCard)
                dParentInfo = dAbsCards[oAbsCard]['parent']
                dParentInfo['count'] += 1
                dParentInfo['expansions'].setdefault(oPhysCard.expansion, 0)
                dParentInfo['expansions'][oPhysCard.expansion] += 1

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
        if self.iExtraLevelsMode in [SHOW_EXPANSIONS,
                EXPANSIONS_AND_CARD_SETS] and \
                self._dNameSecondLevel2Iter.has_key(sCardName):
            if self._dNameSecondLevel2Iter[sCardName].has_key(sExpansion):
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
        if self.iExtraLevelsMode in [SHOW_EXPANSIONS,
                EXPANSIONS_AND_CARD_SETS] and \
                self._dNameSecondLevel2Iter.has_key(sCardName) and \
                self._dNameSecondLevel2Iter[sCardName].has_key(sExpansion):
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
        # FIXME: Needs to handle other expansion modes
        oCard = IAbstractCard(sCardName)
        aParenIters = self._dName2Iter[sCardName]
        self._dNameSecondLevel2Iter[sCardName][sExpansion] = []
        # pylint: disable-msg=W0612
        # x is loop variable here
        aSiblings = [None for x in aParenIters]
        for sThisExp in sorted(self._dNameSecondLevel2Iter[sCardName]):
            if sThisExp == sExpansion:
                iCnt = 1
                if self.bEditable:
                    bIncCard, bDecCard = self.check_inc_dec_expansion(iCnt)
                else:
                    bIncCard, bDecCard = False, False
                for oParent, oSibling in zip(aParenIters, aSiblings):
                    oIter = self.insert_after(oParent, oSibling)
                    self.set(oIter,
                            0, sThisExp,
                            1, self.format_count(iCnt),
                            2, '0',
                            3, bIncCard,
                            4, bDecCard)
                    self._dNameSecondLevel2Iter[sCardName][
                            sExpansion].append(oIter)
            else:
                aSiblings = self._dNameSecondLevel2Iter[sCardName][sThisExp]

        # Notify Listeners
        for oListener in self.dListeners:
            oListener.add_new_card_expansion(oCard, sExpansion)

    def alter_card_expansion_count(self, sCardName, sExpansion, iChg):
        """Adjust the count for the given card + expansion combination by
           iChg."""
        # Need to readjust inc, dec flags for all these cards
        oCard = IAbstractCard(sCardName)
        bDelDictEntry = False
        if not self._dNameSecondLevel2Iter.has_key(sCardName):
            # Can be called by CardSetController with non-existant card
            return
        for sThisExp, aList in \
                self._dNameSecondLevel2Iter[sCardName].iteritems():
            for oIter in aList:
                iCnt = self.get_int_value(oIter, 1)
                if sThisExp == sExpansion:
                    iCnt += iChg
                if self.bEditable:
                    bIncCard, bDecCard = self.check_inc_dec_expansion(iCnt)
                else:
                    bIncCard, bDecCard = False, False
                if self.check_expansion_iter_stays(oCard, sThisExp, iCnt):
                    self.set(oIter,
                            1, self.format_count(iCnt),
                            2, '0',
                            3, bIncCard,
                            4, bDecCard)
                else:
                    self.remove(oIter)
                    bDelDictEntry = True
        if bDelDictEntry:
            del self._dNameSecondLevel2Iter[sCardName][sExpansion]

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
            iCnt = self.get_int_value(oIter, 1) + iChg
            iGrpCnt = self.get_int_value(oGrpIter, 1) + iChg

            if iCnt > 0:
                self.set(oIter, 1, self.format_count(iCnt))
                bIncCard, bDecCard = self.check_inc_dec_card(iCnt)
                self.set(oIter, 3, bIncCard)
                self.set(oIter, 4, bDecCard)
            else:
                if self._dNameSecondLevel2Iter.has_key(sCardName):
                    self._remove_expansion_iters(sCardName)
                self.remove(oIter)

            if iGrpCnt > 0:
                self.set(oGrpIter, 1, self.format_count(iGrpCnt))
            else:
                sGroupName = self.get_value(oGrpIter, 0)
                del self._dGroupName2Iter[sGroupName]
                self.remove(oGrpIter)

        if iCnt <= 0:
            del self._dName2Iter[sCardName]

        if self.oEmptyIter and iChg > 0:
            # Can no longer be empty
            self.remove(self.oEmptyIter)
            self.oEmptyIter = None
        elif iChg < 0 and not self._dName2Iter:
            self.oEmptyIter = self.append(None)
            sText = self._get_empty_text()
            self.set(self.oEmptyIter, 0, sText, 1, self.format_count(0), 2,
                    '0', 3, False, 4, False)

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
        # Not interested in aAbsCards here, but we need the GroupedIter
        oGroupedIter, aAbsCards = self.grouped_card_iter(oCardIter)
        # Iterate over groups
        for sGroup, oGroupIter in oGroupedIter:
            # Check for null group
            if sGroup is None:
                sGroup = '<< None >>'

            # Find Group Section
            if self._dGroupName2Iter.has_key(sGroup):
                oSectionIter = self._dGroupName2Iter[sGroup]
                iGrpCnt = self.get_int_value(oSectionIter, 1)
            else:
                oSectionIter = self.append(None)
                self._dGroupName2Iter[sGroup] = oSectionIter
                iGrpCnt = 0
                self.set(oSectionIter,
                    0, sGroup,
                    1, self.format_count(iGrpCnt),
                    2, '0',
                )

            # Add Cards
            for oItem in oGroupIter:
                oCard, iCnt = get_card(oItem), get_card_count(oItem)
                iGrpCnt += iCnt
                oChildIter = self.append(oSectionIter)
                bIncCard, bDecCard = self.check_inc_dec_card(iCnt)
                self.set(oChildIter,
                    0, oCard.name,
                    1, self.format_count(iCnt),
                    2, '0',
                    3, bIncCard,
                    4, bDecCard
                )
                self._dName2Iter.setdefault(oCard.name, []).append(oChildIter)

                aExpansions = self.get_add_card_expansion_info(oCard,
                        get_card_expansion_info(oItem))

                for sExpName in aExpansions:
                    self._dNameSecondLevel2Iter.setdefault(oCard.name, {})
                    # For models with expansions, this will be paired with a
                    # call to inc Expansion count. We rely on this to sort
                    # out details - here we just create the needed space.
                    self._add_expansion(oChildIter, oCard.name, sExpName,
                            (0, False, False))

            # Update Group Section
            self.set(oSectionIter,
                1, self.format_count(iGrpCnt),
            )

        if self.oEmptyIter and oCardIter.count() > 0:
            # remove previous note
            self.remove(self.oEmptyIter)
            self.oEmptyIter = None

        # Notify Listeners
        oCard = IAbstractCard(sCardName)
        for oListener in self.dListeners:
            oListener.add_new_card(oCard)
