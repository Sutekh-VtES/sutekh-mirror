# CardSetListModel.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""The gtk.TreeModel for the card set lists."""

from sutekh.core.Filters import FilterAndBox, NullFilter, SpecificCardFilter, \
        PhysicalCardSetFilter, SpecificCardIdFilter, \
        MultiPhysicalCardSetMapFilter, SpecificPhysCardIdFilter, \
        PhysicalCardFilter
from sutekh.core.SutekhObjects import PhysicalCard, IExpansion, \
        MapPhysicalCardToPhysicalCardSet, IAbstractCard, IPhysicalCard, \
        IPhysicalCardSet, PhysicalCardSet
from sutekh.gui.CardListModel import CardListModel, norm_path

# pylint: disable-msg=C0103
# We break our usual convention here
# consts for the different modes we need (iExtraLevelsMode)
NO_SECOND_LEVEL, SHOW_EXPANSIONS, SHOW_CARD_SETS, EXPANSIONS_AND_CARD_SETS, \
        CARD_SETS_AND_EXPANSIONS = range(5)
# Different card display modes (iShowCardMode)
THIS_SET_ONLY, ALL_CARDS, PARENT_CARDS, CHILD_CARDS = range(4)
# Different Parent card count modes (iParentCountMode)
IGNORE_PARENT, PARENT_COUNT, MINUS_THIS_SET, MINUS_SETS_IN_USE = range(4)
# pylint: enable-msg=C0103

class CardSetModelRow(object):
    """Object which holds the data needed for a card set row."""

    def __init__(self, bEditable, iExtraLevelsMode):
        self.dExpansions = {}
        self.dChildCardSets = {}
        self.dParentExpansions = {}
        self.iCount = 0
        self.iParentCount = 0
        self.iExtraLevelsMode = iExtraLevelsMode
        self.bEditable = bEditable

    def get_parent_count(self):
        """Get the parent count"""
        return self.iParentCount

    def get_inc_dec_flags(self, iCnt):
        """Deermine the status of the button flags."""
        if self.bEditable:
            return True, (iCnt > 0)
        return False, False

    def get_card_count(self):
        """Extract a card count from the grouped iterator"""
        return self.iCount

    def get_expansion_info(self):
        """Get information about expansions"""
        dCardExpansions = {}
        if self.iExtraLevelsMode in [SHOW_EXPANSIONS,
                EXPANSIONS_AND_CARD_SETS]:
            for sExpName, iCnt in self.dExpansions.iteritems():
                bIncCard, bDecCard = self.get_inc_dec_flags(iCnt)
                iParCnt = self.dParentExpansions.get(sExpName, 0)
                dCardExpansions[sExpName] = [iCnt, iParCnt, bIncCard, bDecCard]
        else:
            for sChildSet in self.dChildCardSets:
                dCardExpansions[sChildSet] = {}
                if not self.dExpansions.has_key(sChildSet):
                    continue
                for sExpName, iCnt in self.dExpansions[sChildSet].iteritems():
                    bIncCard, bDecCard = self.get_inc_dec_flags(iCnt)
                    iParCnt = self.dParentExpansions.get(sExpName, 0)
                    dCardExpansions[sChildSet][sExpName] = [iCnt, iParCnt,
                            bIncCard, bDecCard]
        return dCardExpansions

    def get_child_info(self):
        """Get information about child card sets"""
        dChildren = {}
        if self.iExtraLevelsMode in [SHOW_CARD_SETS, CARD_SETS_AND_EXPANSIONS]:
            for sCardSet, iCnt in self.dChildCardSets.iteritems():
                bIncCard, bDecCard = self.get_inc_dec_flags(iCnt)
                dChildren[sCardSet] = [iCnt, self.iParentCount, bIncCard,
                        bDecCard]
        else:
            for sExpName in self.dExpansions:
                iParCnt = self.dParentExpansions.get(sExpName, 0)
                dChildren[sExpName] = {}
                if not self.dChildCardSets.has_key(sExpName):
                    # No children for this expansion
                    continue
                for sCardSet, iCnt in \
                        self.dChildCardSets[sExpName].iteritems():
                    bIncCard, bDecCard = self.get_inc_dec_flags(iCnt)
                    dChildren[sExpName][sCardSet] = [iCnt, iParCnt, bIncCard,
                            bDecCard]
        return dChildren

class CardSetCardListModel(CardListModel):
    # pylint: disable-msg=R0904, R0902
    # inherit a lot of public methods for gtk, need local attributes for state
    """CardList Model specific to lists of physical cards.

       Handles the display of the cards, their expansions and child card set
       entries. Updates the model to correspond to database changes in
       response to calls from CardSetController.
       """
    def __init__(self, sSetName):
        super(CardSetCardListModel, self).__init__()
        self._cCardClass = MapPhysicalCardToPhysicalCardSet
        self._oBaseFilter = PhysicalCardSetFilter(sSetName)
        self._oCardSet = IPhysicalCardSet(sSetName)
        self._dCache = {}
        self.iExtraLevelsMode = SHOW_EXPANSIONS
        self.bChildren = False
        self.iShowCardMode = THIS_SET_ONLY
        self.bEditable = False
        self._dNameSecondLevel2Iter = {}
        self._dName2nd3rdLevel2Iter = {}
        self.iParentCountMode = PARENT_COUNT
        self.sEditColour = None

    def format_count(self, iCnt):
        """Format the card count accorindly"""
        if self.bEditable and self.sEditColour:
            return '<i><span foreground="%s">%d</span></i>' % \
                    (self.sEditColour, iCnt)
        else:
            return '<i>%d</i>' % iCnt

    def format_parent_count(self, iParCnt, iCnt):
        """Format the parent card count"""
        if (self.iParentCountMode == PARENT_COUNT and iParCnt < iCnt) or \
                iParCnt < 0:
            return '<i><span foreground="red">%d</span></i>' % iParCnt
        else:
            return '<i>%d</i>' % iParCnt

    def _check_if_empty(self):
        """Add the empty entry if needed"""
        if not self._dName2Iter:
            # Showing nothing
            self.oEmptyIter = self.append(None)
            sText = self._get_empty_text()
            self.set(self.oEmptyIter, 0, sText, 1, self.format_count(0), 2,
                    '0', 3, False, 4, False)

    def load(self):
        # pylint: disable-msg=R0914
        # we use many local variables for clarity
        """Clear and reload the underlying store. For use after initialisation,
           when the filter or grouping changes or when card set relationships
           change.
           """
        self.clear()
        self._dName2Iter = {}
        self._dNameSecondLevel2Iter = {}
        self._dName2nd3rdLevel2Iter = {}
        self._dGroupName2Iter = {}
        # Clear cache (we can't do this in grouped_card_iter, since that
        # is also called by add_new_card)
        self._dCache = {}

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
            for oCard, oRow in oGroupIter:
                iCnt = oRow.get_card_count()
                iParCnt = oRow.get_parent_count()
                iGrpCnt += iCnt
                iParGrpCnt += iParCnt
                oChildIter = self.append(oSectionIter)
                bIncCard, bDecCard = self.check_inc_dec(iCnt)
                self.set(oChildIter,
                    0, oCard.name,
                    1, self.format_count(iCnt),
                    2, self.format_parent_count(iParCnt, iCnt),
                    3, bIncCard,
                    4, bDecCard
                )
                self._dName2Iter.setdefault(oCard.name, []).append(oChildIter)
                self._add_children(oChildIter, oRow)
            # Update Group Section
            self.set(oSectionIter,
                0, sGroup,
                1, self.format_count(iGrpCnt),
                2, self.format_parent_count(iParGrpCnt, iGrpCnt),
                3, False,
                4, False
            )

        self._check_if_empty()

        # Notify Listeners
        for oListener in self.dListeners:
            oListener.load(aAbsCards)

    def _add_children(self, oChildIter, oRow):
        """Add the needed children for a card in the model."""
        dExpansionInfo = oRow.get_expansion_info()
        dChildInfo = oRow.get_child_info()
        if self.iExtraLevelsMode == SHOW_EXPANSIONS:
            for sExpansion in sorted(dExpansionInfo):
                self._add_extra_level(oChildIter, sExpansion,
                        dExpansionInfo[sExpansion])
        elif self.iExtraLevelsMode == SHOW_CARD_SETS:
            for sChildSet in sorted(dChildInfo):
                self._add_extra_level(oChildIter, sChildSet,
                        dChildInfo[sChildSet])
        elif self.iExtraLevelsMode == EXPANSIONS_AND_CARD_SETS:
            for sExpansion in sorted(dExpansionInfo):
                oSubIter = self._add_extra_level(oChildIter,
                        sExpansion, dExpansionInfo[sExpansion])
                for sChildSet in sorted(dChildInfo[sExpansion]):
                    self._add_extra_level(oSubIter, sChildSet,
                            dChildInfo[sExpansion][sChildSet])
        elif self.iExtraLevelsMode == CARD_SETS_AND_EXPANSIONS:
            for sChildSet in sorted(dChildInfo):
                oSubIter = self._add_extra_level(oChildIter,
                        sChildSet, dChildInfo[sChildSet])
                for sExpansion in dExpansionInfo[sChildSet]:
                    self._add_extra_level(oSubIter, sExpansion,
                            dExpansionInfo[sChildSet][sExpansion])

    def check_inc_dec(self, iCnt):
        """Helper function to get correct flags"""
        if not self.bEditable:
            return False, False
        return True, (iCnt > 0)

    def _update_entry(self, oIter, iCnt, iParCnt):
        """Update an oIter with the count and parent count"""
        bIncCard, bDecCard = self.check_inc_dec(iCnt)
        self.set(oIter, 1, self.format_count(iCnt),
                2, self.format_parent_count(iParCnt, iCnt),
                3, bIncCard,
                4, bDecCard)

    def _add_extra_level(self, oParIter, sName, tInfo):
        """Add an extra level iterator to the card list model."""
        oIter = self.append(oParIter)
        iCnt, iParCnt, bIncCard, bDecCard = tInfo
        self.set(oIter,
                0, sName,
                1, self.format_count(iCnt),
                2, self.format_parent_count(iParCnt, iCnt),
                3, bIncCard,
                4, bDecCard)
        # Add to the cache
        oPath = self.get_path(oIter)
        # get_card_name_from_path works regardless of level
        sCardName = self.get_card_name_from_path(oPath)
        iDepth = self.iter_depth(oIter)
        if iDepth == 2:
            self._dNameSecondLevel2Iter.setdefault(sCardName, {})
            self._dNameSecondLevel2Iter[sCardName].setdefault(sName,
                    []).append(oIter)
        elif iDepth == 3:
            sSecondLevelName = self.get_name_from_iter(oParIter)
            tKey = (sCardName, sSecondLevelName)
            self._dName2nd3rdLevel2Iter.setdefault(tKey, {})
            self._dName2nd3rdLevel2Iter[tKey].setdefault(sName,
                    []).append(oIter)
        return oIter

    def get_exp_name_from_path(self, oPath):
        """Get the expansion information from the model, returning None
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

    def get_all_names_from_path(self, oPath):
        """Get all the relevant names from the path (cardname, expansion
           and card set), returning None for any that can't be determined.

           This is mainly used by the button signals for editing.
           """
        oIter = self.get_iter(oPath)
        iDepth = self.iter_depth(oIter)
        if iDepth == 0:
            # Top Level item, so no info at all
            return None, None, None
        sCardName = self.get_name_from_iter(self.get_iter(norm_path(
            oPath)[0:2]))
        sExpName = None
        sCardSetName = None
        # Get the expansion name
        if self.iExtraLevelsMode in [SHOW_EXPANSIONS,
                EXPANSIONS_AND_CARD_SETS]:
            if iDepth == 2:
                sExpName = self.get_name_from_iter(oIter)
            elif iDepth == 3:
                sExpName = self.get_name_from_iter(self.get_iter(norm_path(
                    oPath)[0:3]))
        elif self.iExtraLevelsMode == CARD_SETS_AND_EXPANSIONS and \
                iDepth == 3:
            sExpName = self.get_name_from_iter(oIter)
        # Get the card set name
        if self.iExtraLevelsMode in [SHOW_CARD_SETS,
                CARD_SETS_AND_EXPANSIONS]:
            if iDepth == 2:
                sCardSetName = self.get_name_from_iter(oIter)
            elif iDepth == 3:
                sCardSetName = self.get_name_from_iter(self.get_iter(norm_path(
                    oPath)[0:3]))
        elif self.iExtraLevelsMode == EXPANSIONS_AND_CARD_SETS and \
                iDepth == 3:
            sCardSetName = self.get_name_from_iter(oIter)
        return sCardName, sExpName, sCardSetName

    def get_drag_info_from_path(self, oPath):
        """Get card name and expansion information from the path for the
           drag and drop code.

           This returns cardname of None if the path is not a card in this
           card set, such as a top-level item or card in a child card set.
           """
        oIter = self.get_iter(oPath)
        iDepth = self.iter_depth(oIter)
        if iDepth == 2 and self.iExtraLevelsMode == SHOW_EXPANSIONS:
            sName = self.get_name_from_iter(self.get_iter(
                norm_path(oPath)[0:2]))
            sExpansion = self.get_value(oIter, 0)
        elif iDepth == 1:
            sName = self.get_name_from_iter(oIter)
            sExpansion = None
        else:
            sName = None
            sExpansion = None
        iCount = self.get_int_value(oIter, 1)
        return sName, sExpansion, iCount, iDepth

    def get_drag_child_info(self, oPath):
        """Get the expansion information for the card at oPath.

           Always returns the expansions, regaredless of iExtraLevelsMode.
           """
        oIter = self.get_iter(oPath)
        iDepth = self.iter_depth(oIter)
        if iDepth != 1:
            return {} # Not at the right level
        dResult = {}
        if self.iExtraLevelsMode == SHOW_EXPANSIONS:
            # Can read off the data from the model, so do so
            oChildIter = self.iter_children(oIter)
            while oChildIter:
                oChildPath = self.get_path(oChildIter)
                sCardName, sExpansion, iCount, iDepth = \
                        self.get_drag_info_from_path(oChildPath)
                dResult[sExpansion] = iCount
                oChildIter = self.iter_next(oChildIter)
        else:
            # Need to get expansion info from the database
            sCardName = self.get_name_from_iter(self.get_iter(oPath))
            oFilter = SpecificCardFilter(sCardName)
            oCardIter = self.get_card_iterator(oFilter)
            # pylint: disable-msg=E1101
            # Pyprotocols confuses pylint
            for oCard in oCardIter:
                oPhysCard = IPhysicalCard(oCard)
                sExpName = self.get_expansion_name(oPhysCard.expansion)
                dResult.setdefault(sExpName, 0)
                dResult[sExpName] += 1
        return dResult

    def _init_expansions(self, dExpanInfo, oAbsCard):
        """Initialise the expansion dict for a card"""
        if self.bEditable:
            for oRarityPair in oAbsCard.rarity:
                dExpanInfo.setdefault(
                        self.get_expansion_name(oRarityPair.expansion), 0)
            dExpanInfo.setdefault(self.sUnknownExpansion, 0)

    def _init_abs(self, dAbsCards, oAbsCard):
        """Initialize the entry for oAbsCard in dAbsCards"""
        if oAbsCard not in dAbsCards:
            dAbsCards[oAbsCard] = CardSetModelRow(self.bEditable,
                    self.iExtraLevelsMode)
            if self.iExtraLevelsMode in [SHOW_EXPANSIONS,
                    EXPANSIONS_AND_CARD_SETS]:
                self._init_expansions(dAbsCards[oAbsCard].dExpansions,
                        oAbsCard)

    def _get_child_filters(self, oCurFilter):
        """Get the filters for the child card sets of this card set."""
        # pylint: disable-msg=E1101
        # SQLObject + PyProtocols confuse pylint
        if self.iExtraLevelsMode in [SHOW_CARD_SETS, EXPANSIONS_AND_CARD_SETS,
                CARD_SETS_AND_EXPANSIONS] or self.iShowCardMode == CHILD_CARDS:
            if not self._dCache.has_key('child filters') or \
                    not self._dCache['child filters']:
                self._dCache['child filters'] = {}
                aChildren = [x.name for x in
                        PhysicalCardSet.selectBy(parentID=self._oCardSet.id,
                            inuse=True)]
                if aChildren:
                    self._dCache ['all children filter'] = \
                            MultiPhysicalCardSetMapFilter(aChildren)
                    for sName in aChildren:
                        self._dCache['child filters'][sName] = \
                                PhysicalCardSetFilter(sName)
        dChildCardCache = {}
        if self.iExtraLevelsMode in [SHOW_CARD_SETS,
                EXPANSIONS_AND_CARD_SETS, CARD_SETS_AND_EXPANSIONS] and \
                        self._dCache['child filters']:
            # Cache card set lookups, to reduce database traffic
            for sName, oFilter in self._dCache['child filters'].iteritems():
                oFullFilter = FilterAndBox([oFilter, oCurFilter])
                dChildCardCache[sName] = {}
                for oCard in [IPhysicalCard(x) for x in
                        oFullFilter.select(self.cardclass).distinct()]:
                    dChildCardCache[sName].setdefault(oCard.abstractCard,
                            []).append(oCard)
        return dChildCardCache

    def _get_parent_list(self, oCurFilter):
        """Get a list object for the cards in the parent card set."""
        # pylint: disable-msg=E1101
        # SQLObject + PyProtocols confuse pylint
        if self._oCardSet.parent:
            # It's tempting to use get_card_iterator here, but that
            # obviously doesn't work because of _oBaseFilter
            oParentFilter = FilterAndBox([
                PhysicalCardSetFilter(self._oCardSet.parent.name),
                oCurFilter])
            aParentCards = [IPhysicalCard(x) for x in
                    oParentFilter.select(self.cardclass).distinct()]
        else:
            oParentFilter = None
            aParentCards = []
        return aParentCards

    def grouped_card_iter(self, oCardIter):
        """Get the data that needs to fill the model, handling the different
           CardShow modes, the different counts, the filter, etc.

           Returns a iterator over the groupings, and a list of all the
           abstract cards in the card set considered.
           """
        # pylint: disable-msg=E1101, R0914
        # E1101: SQLObject + PyProtocols confuse pylint
        # R0914: We use lots of local variables for clarity
        # Define iterable and grouping function based on cardclass
        aAbsCards = []
        dAbsCards = {}

        oCurFilter = self.get_current_filter()
        if oCurFilter is None:
            oCurFilter = NullFilter()

        dChildCardCache = self._get_child_filters(oCurFilter)
        aParentCards = self._get_parent_list(oCurFilter)

        # Other card show modes
        if self.iShowCardMode == ALL_CARDS:
            oFullFilter = FilterAndBox([PhysicalCardFilter(), oCurFilter])
            aExtraCards = [x for x in
                    oFullFilter.select(PhysicalCard).distinct()]
        elif self.iShowCardMode == PARENT_CARDS and self._oCardSet.parent:
            aExtraCards = aParentCards
        elif self.iShowCardMode == CHILD_CARDS and \
                self._dCache['child filters']:
            oFullFilter = FilterAndBox([self._dCache['all children filter'],
                oCurFilter])
            aExtraCards = [IPhysicalCard(x) for x in
                    oFullFilter.select(self.cardclass).distinct()]
        else:
            # No point in doing the extra work
            aExtraCards = []

        for oPhysCard in aExtraCards:
            oAbsCard = oPhysCard.abstractCard
            self._init_abs(dAbsCards, oAbsCard)
            if self.iExtraLevelsMode == SHOW_EXPANSIONS or \
                    self.iExtraLevelsMode == EXPANSIONS_AND_CARD_SETS:
                dAbsCards[oAbsCard].dExpansions.setdefault(
                        self.get_expansion_name(oPhysCard.expansion), 0)
            dExpanInfo = dAbsCards[oAbsCard].dExpansions
            dChildInfo = dAbsCards[oAbsCard].dChildCardSets
            if not dChildInfo and self.iExtraLevelsMode in [
                    SHOW_CARD_SETS, EXPANSIONS_AND_CARD_SETS,
                    CARD_SETS_AND_EXPANSIONS]:
                self.get_child_set_info(oAbsCard, dChildInfo, dExpanInfo,
                        dChildCardCache)

        for oCard in oCardIter:
            oPhysCard = IPhysicalCard(oCard)
            sExpName = self.get_expansion_name(oPhysCard.expansion)
            oAbsCard = oPhysCard.abstractCard
            aAbsCards.append(oAbsCard)
            self._init_abs(dAbsCards, oAbsCard)
            dAbsCards[oAbsCard].iCount += 1
            dChildInfo = dAbsCards[oAbsCard].dChildCardSets
            dExpanInfo = dAbsCards[oAbsCard].dExpansions
            if self.iExtraLevelsMode == SHOW_EXPANSIONS or \
                    self.iExtraLevelsMode == EXPANSIONS_AND_CARD_SETS:
                dExpanInfo.setdefault(sExpName, 0)
                dExpanInfo[sExpName] += 1
            if self.iExtraLevelsMode in [SHOW_CARD_SETS,
                    EXPANSIONS_AND_CARD_SETS, CARD_SETS_AND_EXPANSIONS] and \
                    not dChildInfo:
                # Don't re-filter for repeated abstract cards
                self.get_child_set_info(oAbsCard, dChildInfo, dExpanInfo,
                        dChildCardCache)
            if self.iExtraLevelsMode == EXPANSIONS_AND_CARD_SETS:
                dChildInfo.setdefault(sExpName, {})


        self._add_parent_info(dAbsCards, aParentCards)

        aCards = list(dAbsCards.iteritems())
        aCards.sort(lambda x, y: cmp(x[0].name, y[0].name))

        # Iterate over groups
        return (self.groupby(aCards, lambda x: x[0]), aAbsCards)

    def get_child_set_info(self, oAbsCard, dChildInfo, dExpanInfo,
            dChildCardCache):
        """Fill in info about the child card sets for the grouped iterator"""
        # pylint: disable-msg=E1101
        # Pyprotocols confuses pylint
        for sCardSetName in dChildCardCache:
            if oAbsCard in dChildCardCache[sCardSetName]:
                aChildCards = dChildCardCache[sCardSetName][oAbsCard]
            else:
                aChildCards = []
            if self.iExtraLevelsMode == SHOW_CARD_SETS or \
                    self.iExtraLevelsMode == CARD_SETS_AND_EXPANSIONS:
                iChildCnt = len(aChildCards)
                if iChildCnt > 0 or self.iShowCardMode == ALL_CARDS or \
                        self.bEditable:
                    # FIXME: Does this check do what the user would expect?
                    dChildInfo.setdefault(sCardSetName, iChildCnt)
                    if self.iExtraLevelsMode == CARD_SETS_AND_EXPANSIONS:
                        dExpanInfo.setdefault(sCardSetName, {})
                        self._init_expansions(dExpanInfo[sCardSetName],
                                oAbsCard)
                        for oThisPhysCard in aChildCards:
                            sExpName = self.get_expansion_name(
                                    oThisPhysCard.expansion)
                            dExpanInfo[sCardSetName].setdefault(sExpName, 0)
                            dExpanInfo[sCardSetName][sExpName] += 1
            elif self.iExtraLevelsMode == EXPANSIONS_AND_CARD_SETS:
                if self.bEditable:
                    for oRarityPair in oAbsCard.rarity:
                        sExpName = self.get_expansion_name(
                                oRarityPair.expansion)
                        dChildInfo.setdefault(sExpName, {})
                        dChildInfo[sExpName].setdefault(sCardSetName, 0)
                    dChildInfo.setdefault(self.sUnknownExpansion, {})
                    dChildInfo[self.sUnknownExpansion].setdefault(
                            sCardSetName, 0)
                for oThisPhysCard in aChildCards:
                    sExpName = self.get_expansion_name(oThisPhysCard.expansion)
                    dChildInfo.setdefault(sExpName, {})
                    dChildInfo[sExpName].setdefault(sCardSetName, 0)
                    dChildInfo[sExpName][sCardSetName] += 1

    def _get_sibling_cards(self):
        """Get the list of cards in sibling card sets"""
        # pylint: disable-msg=E1101
        # pyprotocols confusion
        dSiblingCards = {}
        if not self._dCache.has_key('sibling filter') or \
                not self._dCache['sibling filter']:
            aChildren = [x.name for x in PhysicalCardSet.selectBy(
                parentID=self._oCardSet.parent.id, inuse=True)]
            if aChildren:
                self._dCache['sibling filter'] = \
                        MultiPhysicalCardSetMapFilter(aChildren)
            else:
                self._dCache['sibling filter'] = None
        if self._dCache['sibling filter']:
            aInUseCards = [(IAbstractCard(x), IPhysicalCard(x)) for x in
                    self._dCache['sibling filter'].select(
                        self.cardclass).distinct()]
            for oAbsCard, oPhysCard in aInUseCards:
                dSiblingCards.setdefault(oAbsCard, []).append(oPhysCard)
        return dSiblingCards

    def _update_parent_info(self, oAbsCard, oSetInfo, dParentExp):
        """Update the parent counts with info from this set"""
        # pylint: disable-msg=E1103, E1101
        # pyprotocols confusion
        if self.iExtraLevelsMode in [EXPANSIONS_AND_CARD_SETS,
                SHOW_EXPANSIONS]:
            # Already looked this up
            for sExpansion, iCnt in oSetInfo.dExpansions.iteritems():
                dParentExp[sExpansion] = -iCnt
        elif self.iExtraLevelsMode == CARD_SETS_AND_EXPANSIONS and \
                oSetInfo.iCount > 0:
            # We have some cards, but we don't know which, so we
            # need to get this from the database
            for dInfo in oSetInfo.dExpansions.itervalues():
                for sExpansion in dInfo:
                    if not dParentExp.has_key(sExpansion):
                        if sExpansion != self.sUnknownExpansion:
                            oPhysCard = IPhysicalCard((oAbsCard,
                                IExpansion(sExpansion)))
                        else:
                            oPhysCard = IPhysicalCard((oAbsCard, None))
                        # Query the database
                        dParentExp[sExpansion] = -self.get_card_iterator(
                                SpecificPhysCardIdFilter(oPhysCard.id)).count()

    def _add_parent_info(self, dAbsCards, aParentCards):
        """Add the parent count info into the mix"""
        # pylint: disable-msg=E1101
        # Pyprotocols confuses pylint
        if (self.iParentCountMode == IGNORE_PARENT and
                self.iShowCardMode != PARENT_CARDS) or \
                        not self._oCardSet.parent:
            return # No point in doing anything at all
        dSiblingCards = {}
        if self.iParentCountMode == MINUS_SETS_IN_USE:
            dSiblingCards = self._get_sibling_cards()
        for oAbsCard in dAbsCards:
            dParentExp = dAbsCards[oAbsCard].dParentExpansions
            if self.iParentCountMode == MINUS_THIS_SET:
                dAbsCards[oAbsCard].iParentCount = -dAbsCards[oAbsCard].iCount
                self._update_parent_info(oAbsCard, dAbsCards[oAbsCard],
                        dParentExp)
            elif oAbsCard in dSiblingCards:
                for oPhysCard in dSiblingCards[oAbsCard]:
                    dAbsCards[oAbsCard].iParentCount -= 1
                    sExpansion = self.get_expansion_name(oPhysCard.expansion)
                    dParentExp.setdefault(sExpansion, 0)
                    dParentExp[sExpansion] -= 1

        for oPhysCard in aParentCards:
            # pylint: disable-msg=E1101
            # Pyprotocols confuses pylint
            oAbsCard = oPhysCard.abstractCard
            if oAbsCard in dAbsCards:
                sExpansion = self.get_expansion_name(oPhysCard.expansion)
                dParentExp = dAbsCards[oAbsCard].dParentExpansions
                dParentExp.setdefault(sExpansion, 0)
                if self.iParentCountMode != IGNORE_PARENT:
                    dAbsCards[oAbsCard].iParentCount += 1
                    dParentExp[sExpansion] += 1

    def _remove_sub_iters(self, sCardName):
        """Remove the children rows for the card entry sCardName"""
        if not self._dNameSecondLevel2Iter.has_key(sCardName):
            # Nothing to clean up (not showing second level, etc.)
            return
        aSecondLevelKeys = self._dNameSecondLevel2Iter[sCardName].keys()
        # We remove values in the loop, so we need this copy
        for sValue in aSecondLevelKeys:
            self._remove_second_level(sCardName, sValue)

    def _remove_second_level(self, sCardName, sValue):
        """Remove a second level entry and everything below it"""
        if not self._dNameSecondLevel2Iter.has_key(sCardName) or \
                not self._dNameSecondLevel2Iter[sCardName].has_key(sValue):
            return # Nothing to do
        if self._dName2nd3rdLevel2Iter.has_key((sCardName, sValue)):
            for sName in self._dName2nd3rdLevel2Iter[(sCardName, sValue)]:
                for oIter in self._dName2nd3rdLevel2Iter[(sCardName, sValue)][
                        sName]:
                    self.remove(oIter)
            del self._dName2nd3rdLevel2Iter[(sCardName, sValue)]
        for oIter in self._dNameSecondLevel2Iter[sCardName][sValue]:
            self.remove(oIter)
        del self._dNameSecondLevel2Iter[sCardName][sValue]
        if not self._dNameSecondLevel2Iter[sCardName]:
            del self._dNameSecondLevel2Iter[sCardName]

    def _get_parent_count(self, oPhysCard, iThisSetCnt=None):
        """Get the correct parent count for the given card"""
        # pylint: disable-msg=E1101
        # PyProtocols confuses pylint
        iParCnt = 0
        if self._oCardSet.parent and self.iParentCountMode != IGNORE_PARENT:
            oParentFilter = FilterAndBox([
                SpecificPhysCardIdFilter(oPhysCard.id),
                PhysicalCardSetFilter(self._oCardSet.parent.name)])
            iParCnt = oParentFilter.select(self.cardclass).distinct().count()
            if self.iParentCountMode == MINUS_THIS_SET:
                if iThisSetCnt is None:
                    iThisSetCnt = self.get_card_iterator(
                            SpecificPhysCardIdFilter(oPhysCard.id)).count()
                iParCnt -= iThisSetCnt
            elif self.iParentCountMode == MINUS_SETS_IN_USE:
                if self._dCache['sibling filter']:
                    oInUseFilter = FilterAndBox([
                        SpecificPhysCardIdFilter(oPhysCard.id),
                        self._dCache['sibling filter']])
                    iParCnt -= oInUseFilter.select(
                            self.cardclass).distinct().count()
        return iParCnt

    def add_new_card(self, oPhysCard):
        # pylint: disable-msg=R0914
        # we use many local variables for clarity
        """If the card oPhysCard is not in the current list (i.e. is not in
           the card set or is filtered out) see if it should be visible. If it
           should be visible, add it to the appropriate groups.
           """
        oFilter = self.combine_filter_with_base(self.get_current_filter())
        oAbsCard = IAbstractCard(oPhysCard)
        # pylint: disable-msg=E1101
        # PyProtocols confuses pylint
        if self.bEditable:
            oFullFilter = FilterAndBox([SpecificCardIdFilter(oAbsCard.id),
                oFilter])
            # Checking on the physical card picks up filters on the physical
            # expansion - since we show all expansions when editing, checking
            # on the physical card when the list is editable doesn't behave as
            # one would expect, so we only check the abstract card.
        else:
            oFullFilter = FilterAndBox([SpecificPhysCardIdFilter(oPhysCard.id),
                oFilter])
        oCardIter = oFullFilter.select(self.cardclass).distinct()

        bVisible = oCardIter.count() > 0

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
                iParGrpCnt = self.get_int_value(oSectionIter, 2)
            else:
                oSectionIter = self.append(None)
                self._dGroupName2Iter[sGroup] = oSectionIter
                iGrpCnt = 0
                iParGrpCnt = 0
                self.set(oSectionIter,
                    0, sGroup,
                    1, self.format_count(iGrpCnt),
                    2, self.format_parent_count(0, iGrpCnt),
                )
            # Add Cards
            for oCard, oRow in oGroupIter:
                # Due to the various view modes, we aren't assured of
                # getting back only the new card from get_grouped_iterator,
                # so this check is needed
                if oAbsCard.id != oCard.id:
                    continue
                iCnt = oRow.get_card_count()
                iParCnt = oRow.get_parent_count()
                iGrpCnt += iCnt
                iParGrpCnt += iParCnt
                oChildIter = self.append(oSectionIter)
                bIncCard, bDecCard = self.check_inc_dec(iCnt)
                self.set(oChildIter,
                    0, oCard.name,
                    1, self.format_count(iCnt),
                    2, self.format_parent_count(iParCnt, iCnt),
                    3, bIncCard,
                    4, bDecCard
                )
                self._dName2Iter.setdefault(oCard.name, []).append(oChildIter)
                # Handle as for loading
                self._add_children(oChildIter, oRow)

            # Update Group Section
            self.set(oSectionIter,
                1, self.format_count(iGrpCnt),
                2, self.format_parent_count(iParGrpCnt, iGrpCnt)
            )

        if self.oEmptyIter and self._dName2Iter:
            # remove previous empty note
            self.remove(self.oEmptyIter)
            self.oEmptyIter = None

        # Notify Listeners
        for oListener in self.dListeners:
            oListener.add_new_card(oAbsCard, bVisible)

    def update_to_new_db(self, sSetName):
        """Update internal card set to the new DB."""
        self._oCardSet = IPhysicalCardSet(sSetName)
        self._oBaseFilter = PhysicalCardSetFilter(sSetName)

    def changes_with_parent(self):
        """Utility function. Returns true if the parent card set influences
           the currently visible set of cards."""
        # pylint: disable-msg=E1101
        # PyProtocols confuse pylint
        return (self.iParentCountMode != IGNORE_PARENT or \
                self.iShowCardMode == PARENT_CARDS) and \
                self._oCardSet.parent is not None

    def changes_with_children(self):
        """Utiltiy function. Returns true if changes to the child card sets
           influence the display."""
        return self.iShowCardMode == CHILD_CARDS or self.iExtraLevelsMode \
                in [SHOW_CARD_SETS, EXPANSIONS_AND_CARD_SETS,
                        CARD_SETS_AND_EXPANSIONS]

    def changes_with_siblings(self):
        """Utility function. Returns true if changes to the sibling card sets
           influence the display."""
        # pylint: disable-msg=E1101
        # PyProtocols confuse pylint
        return self.iParentCountMode == MINUS_SETS_IN_USE and \
                self._oCardSet.parent is not None

    def inc_card(self, oPhysCard):
        """Increase the count for the card oPhysCard, adding a new
           card entry if nessecary."""
        sCardName = oPhysCard.abstractCard.name
        if not self._dName2Iter.has_key(sCardName):
            self.add_new_card(oPhysCard) # new card
        else:
            self.alter_card_count(oPhysCard, +1)

    def dec_card(self, oPhysCard):
        """Decrease the count for the card oPhysCard, removing it from the
           view if needed."""
        sCardName = oPhysCard.abstractCard.name
        if self._dName2Iter.has_key(sCardName):
            self.alter_card_count(oPhysCard, -1)

    def inc_sibling_count(self, oPhysCard):
        """Update to an increase in the number of sibling cards."""
        sCardName = oPhysCard.abstractCard.name
        if not self._dName2Iter.has_key(sCardName):
            return # Card isn't visible
        # This is only called when iParentCountMode == MINUS_SETS_IN_USE,
        # So this decreases the available pool of parent cards
        # There's no possiblity of this deleting a card from the model
        self.alter_parent_count(oPhysCard, -1, False)

    def dec_sibling_count(self, oPhysCard):
        """Update to an increase in the number of sibling cards."""
        sCardName = oPhysCard.abstractCard.name
        if not self._dName2Iter.has_key(sCardName):
            return
        # This is only called when iParentCountMode == MINUS_SETS_IN_USE,
        # So this increase the available pool of parent cards
        # There's no possiblity of this adding a card to the model
        self.alter_parent_count(oPhysCard, +1, False)

    def inc_parent_count(self, oPhysCard):
        """Decrease the parent count for the given physical card"""
        sCardName = oPhysCard.abstractCard.name
        if not self._dName2Iter.has_key(sCardName):
            # Card isn't shown, so need to add it
            self.add_new_card(oPhysCard)
        else:
            self.alter_parent_count(oPhysCard, +1)

    def dec_parent_count(self, oPhysCard):
        """Decrease the parent count for the given physical card"""
        sCardName = oPhysCard.abstractCard.name
        if not self._dName2Iter.has_key(sCardName):
            # Card isn't shown, so nothing to do
            return
        self.alter_parent_count(oPhysCard, -1)

    def inc_child_count(self, oPhysCard, sCardSetName):
        """Add the card oPhysCard in the card set sCardSetName to the model."""
        sCardName = oPhysCard.abstractCard.name
        if not self._dName2Iter.has_key(sCardName):
            # Card isn't shown, so need to add it
            self.add_new_card(oPhysCard)
        else:
            self.alter_child_count(oPhysCard, sCardSetName, +1)

    def dec_child_count(self, oPhysCard, sCardSetName):
        """Remove the card oPhysCard in the card set sCardSetName
           from the model."""
        sCardName = oPhysCard.abstractCard.name
        if not self._dName2Iter.has_key(sCardName):
            # Card not shown, so nothing to do
            return
        self.alter_child_count(oPhysCard, sCardSetName, -1)


    def _card_count_changes_parent(self):
        """Check if a change in the card count changes the parent"""
        # pylint: disable-msg=E1101
        # pyprotocols confuses pylint
        return (self.iParentCountMode == MINUS_THIS_SET or
                (self.iParentCountMode == MINUS_SETS_IN_USE and
                    self._oCardSet.inuse)) and self._oCardSet.parent

    def _update_parent_count(self, oIter, iChg, iParChg):
        """Update the card and parent counts"""
        iParCnt = self.get_int_value(oIter, 2)
        if self.iParentCountMode != IGNORE_PARENT:
            iParCnt += iParChg
        if self._card_count_changes_parent():
            iParCnt -= iChg
        return iParCnt

    def _check_child_counts(self, oIter):
        """Loop over a level of the model, checking for non-zero counts"""
        while oIter:
            if self.get_int_value(oIter, 1) > 0:
                # Short circuit the loop
                return True
            oIter = self.iter_next(oIter)
        return False

    def check_child_iter_stays(self, oIter, oPhysCard):
        """Check if an expansion or child card set iter stays"""
        # Conditions vary with cards shown and the editable flag.
        # This routine works on the assumption that we only need to
        # get the result right when the parent row isn't being removed.
        # If the parent row is to be removed, reutrning the wrong result
        # here doesn't matter - this simplifies the logic a bit
        # pylint: disable-msg=E1101
        # E1101: PyProtocols confuses pylint
        iCnt = self.get_int_value(oIter, 1)
        iParCnt = self.get_int_value(oIter, 2)
        if iCnt > 0 or self.bEditable:
            # When editing, we don't delete 0 entries unless the card vanishes
            return True
        iDepth = self.iter_depth(oIter)
        if iDepth == 3 and self.iExtraLevelsMode in [EXPANSIONS_AND_CARD_SETS,
                CARD_SETS_AND_EXPANSIONS]:
            # Since we're not editable here, we always remove these
            return False
        bResult = False
        if self.iShowCardMode == ALL_CARDS:
            # Other than the above, we never remove entries for ALL_CARDS
            bResult = True
        elif self.iExtraLevelsMode == EXPANSIONS_AND_CARD_SETS and \
                self.iShowCardMode == CHILD_CARDS and \
                self.iter_n_children(oIter) > 0:
            # iCnt is 0, and we're not editable, so we only show this
            # row if there are non-zero entries below us
            oChildIter = self.iter_children(oIter)
            if self._check_child_counts(oChildIter):
                bResult = True
        elif self.iShowCardMode == PARENT_CARDS and \
                self.iParentCountMode in [PARENT_COUNT, MINUS_THIS_SET] and \
                self.iExtraLevelsMode in [SHOW_EXPANSIONS,
                        EXPANSIONS_AND_CARD_SETS] and iDepth == 2 and \
                iParCnt > 0:
            # cards in the parent set, obviously
            bResult = True
        elif self.iShowCardMode == PARENT_CARDS and self._oCardSet.parent \
                and self.iExtraLevelsMode in [SHOW_EXPANSIONS,
                        EXPANSIONS_AND_CARD_SETS] and iDepth == 2:
            # Check if the card actually is in the parent card set
            oFullFilter = FilterAndBox([SpecificPhysCardIdFilter(oPhysCard.id),
                PhysicalCardSetFilter(self._oCardSet.parent.name)])
            bResult = oFullFilter.select(self.cardclass).distinct().count() > 0
        elif self.iShowCardMode == CHILD_CARDS and \
                self.iExtraLevelsMode == SHOW_EXPANSIONS:
            # Need to check the database, since we can't query the model
            if self._dCache['child filters']:
                oChildFilter = FilterAndBox([
                    SpecificPhysCardIdFilter(oPhysCard.id),
                    self._dCache['all children filter']])
                if oChildFilter.select(self.cardclass).distinct().count() > 0:
                    bResult = True
        # No reason to return True
        return bResult

    def check_card_iter_stays(self, oIter):
        """Check if we need to remove a given card or not"""
        # Conditions for removal vary with the cards shown
        # pylint: disable-msg=E1101
        # Pyprotocols confuses pylint
        iCnt = self.get_int_value(oIter, 1)
        if self.iShowCardMode == ALL_CARDS or iCnt > 0:
            # We clearly don't remove entries here
            return True
        iParCnt = self.get_int_value(oIter, 2)
        bResult = False
        if self.iShowCardMode == PARENT_CARDS and iParCnt > 0 and \
                self.iParentCountMode in [PARENT_COUNT, MINUS_THIS_SET]:
            bResult = True
        elif self.iShowCardMode == PARENT_CARDS and self._oCardSet.parent:
            # Check database
            oAbsCard = IAbstractCard(self.get_name_from_iter(oIter))
            oFilter = FilterAndBox([SpecificCardIdFilter(oAbsCard.id),
                        PhysicalCardSetFilter(self._oCardSet.parent.name)])
            bResult = oFilter.select(self.cardclass).distinct().count() > 0
        elif self.iShowCardMode == CHILD_CARDS:
            if self.iExtraLevelsMode in [SHOW_CARD_SETS,
                    CARD_SETS_AND_EXPANSIONS]:
                # Check if any top level child iters have non-zero counts
                oChildIter = self.iter_children(oIter)
                bResult = self._check_child_counts(oChildIter)
            elif self.iExtraLevelsMode == EXPANSIONS_AND_CARD_SETS:
                # Check third level children
                oChildIter = self.iter_children(oIter)
                while oChildIter:
                    oGrandChild = self.iter_children(oChildIter)
                    if self._check_child_counts(oGrandChild):
                        return True
                    oChildIter = self.iter_next(oChildIter)
            elif self._dCache['child filters']:
                # Actually check the database
                oAbsCard = IAbstractCard(self.get_name_from_iter(oIter))
                oChildFilter = FilterAndBox([SpecificCardIdFilter(oAbsCard.id),
                    self._dCache['all children filter']])
                bResult = oChildFilter.select(
                            self.cardclass).distinct().count() > 0
        return bResult

    def check_group_iter_stays(self, oIter):
        """Check if we need to remove the top-level item"""
        # Conditions for removal vary with the cards shown
        if self.iShowCardMode == ALL_CARDS:
            return True # We don't remove group entries
        iCnt = self.get_int_value(oIter, 1)
        iParCnt = self.get_int_value(oIter, 2)
        if iCnt > 0:
            # Count is non-zero, so we stay
            return True
        if self.iShowCardMode == PARENT_CARDS and iParCnt > 0:
            # Obviously parent cards present
            return True
        elif self.iShowCardMode == PARENT_CARDS and \
                self.iParentCountMode not in [PARENT_COUNT, MINUS_THIS_SET]:
            # Pass this check to the children
            oChildIter = self.iter_children(oIter)
            while oChildIter:
                if self.check_card_iter_stays(oChildIter):
                    return True
                oChildIter = self.iter_next(oChildIter)
        elif self.iShowCardMode == CHILD_CARDS:
            # Pass the check to the children - we stay if at least one child
            # stays
            oChildIter = self.iter_children(oIter)
            while oChildIter:
                if self.check_card_iter_stays(oChildIter):
                    return True
                oChildIter = self.iter_next(oChildIter)
        return False

    # FIXME: There be dragons in this here code

    def _update_3rd_level_card_sets(self, oPhysCard, iChg, iParChg,
            bCheckAddRemove):
        """Update the third level for EXPANSIONS_AND_CARD_SETS"""
        sCardName = oPhysCard.abstractCard.name
        sExpName = self.get_expansion_name(oPhysCard.expansion)
        bRemoveChild = False
        if self._dName2nd3rdLevel2Iter.has_key((sCardName, sExpName)):
            # Update the 3rd level
            for aIterList in self._dName2nd3rdLevel2Iter[
                    (sCardName, sExpName)].itervalues():
                for oSubIter in aIterList:
                    iCnt = self.get_int_value(oSubIter, 1)
                    iParCnt = self._update_parent_count(oSubIter, iChg,
                            iParChg)
                    self._update_entry(oSubIter, iCnt, iParCnt)
                    if bRemoveChild or (bCheckAddRemove and not
                            self.check_child_iter_stays(oSubIter, oPhysCard)):
                        bRemoveChild = True
                        self.remove(oSubIter)
            if bRemoveChild:
                del self._dName2nd3rdLevel2Iter[(sCardName, sExpName)]

    def _add_3rd_level_card_sets(self, oPhysCard, iParCnt):
        """Add 3rd level entries for the EXPANSIONS_AND_CARD_SETS mode"""
        sCardName = oPhysCard.abstractCard.name
        sExpName = self.get_expansion_name(oPhysCard.expansion)
        for sCardSet, oSetFilter in self._dCache['child filters'].iteritems():
            oFilter = FilterAndBox([SpecificPhysCardIdFilter(oPhysCard.id),
                                oSetFilter])
            iCnt = oFilter.select(self.cardclass).distinct().count()
            if iCnt > 0:
                # We can ignore the iCnt == 0 cases (bEditable
                # True, etc.), since we know those entries
                # would already be showing if required.
                for oIter in self._dNameSecondLevel2Iter[sCardName][sExpName]:
                    bIncCard, bDecCard = self.check_inc_dec(iCnt)
                    self._add_extra_level(oIter, sCardSet, (iCnt, iParCnt,
                        bIncCard, bDecCard))

    def _update_2nd_level_expansions(self, oPhysCard, iChg, iParChg,
            bCheckAddRemove=True):
        """Update the expansion entries and the children for a changed entry
           for the SHOW_EXPANSIONS and EXPANSIONS_AND_CARD_SETS modes"""
        # We need to update the expansion count for this card
        # pylint: disable-msg=E1101
        # pyprotocols confuses pylint
        sCardName = oPhysCard.abstractCard.name
        sExpName = self.get_expansion_name(oPhysCard.expansion)
        bRemove = False
        if self._dNameSecondLevel2Iter.has_key(sCardName) and \
                self._dNameSecondLevel2Iter[sCardName].has_key(sExpName):
            for oChildIter in self._dNameSecondLevel2Iter[sCardName][sExpName]:
                iCnt = self.get_int_value(oChildIter, 1) + iChg
                iParCnt = self._update_parent_count(oChildIter, iChg, iParChg)
                self._update_entry(oChildIter, iCnt, iParCnt)
                if not self.check_child_iter_stays(oChildIter, oPhysCard) and \
                        bCheckAddRemove:
                    bRemove = True
            if not bRemove:
                self._update_3rd_level_card_sets(oPhysCard, iChg, iParChg,
                        bCheckAddRemove)
        elif iChg > 0 or (iParChg > 0 and self.iShowCardMode == PARENT_CARDS
                and bCheckAddRemove):
            for oIter in self._dName2Iter[sCardName]:
                iParCnt = self._get_parent_count(oPhysCard, iChg)
                bIncCard, bDecCard = self.check_inc_dec(iChg)
                self._add_extra_level(oIter, sExpName, (iChg, iParCnt,
                    bIncCard, bDecCard))
                if self.iExtraLevelsMode == EXPANSIONS_AND_CARD_SETS \
                        and self.iShowCardMode not in [ALL_CARDS,
                                CHILD_CARDS]:
                    self._add_3rd_level_card_sets(oPhysCard, iParCnt)
        if bRemove:
            self._remove_second_level(sCardName, sExpName)

    def alter_card_count(self, oPhysCard, iChg):
        """Alter the card count of a card which is in the current list
           (i.e. in the card set and not filtered out) by iChg."""
        # pylint: disable-msg=E1101
        # PyProtocols confuses pylint here
        oCard = IAbstractCard(oPhysCard)
        sCardName = oCard.name
        bRemove = False
        for oIter in self._dName2Iter[sCardName]:
            oGrpIter = self.iter_parent(oIter)
            iCnt = self.get_int_value(oIter, 1) + iChg
            iGrpCnt = self.get_int_value(oGrpIter, 1) + iChg
            iParGrpCnt = self.get_int_value(oGrpIter, 2)
            self.set(oIter, 1, self.format_count(iCnt))
            iParCnt = self.get_int_value(oIter, 2)
            if self.iParentCountMode == MINUS_THIS_SET \
                    and self._oCardSet.parent:
                iParCnt -= iChg
                iParGrpCnt -= iChg
            elif self.iParentCountMode == MINUS_SETS_IN_USE \
                    and self._oCardSet.parent and self._oCardSet.inuse:
                iParCnt -= iChg
                iParGrpCnt -= iChg

            if self.check_card_iter_stays(oIter):
                self._update_entry(oIter, iCnt, iParCnt)
            else:
                bRemove = True
                self._remove_sub_iters(sCardName)
                self.remove(oIter)

            self.set(oGrpIter, 1, self.format_count(iGrpCnt))
            self.set(oGrpIter, 2, self.format_parent_count(iParGrpCnt,
                iGrpCnt))
            if not self.check_group_iter_stays(oGrpIter):
                sGroupName = self.get_value(oGrpIter, 0)
                del self._dGroupName2Iter[sGroupName]
                self.remove(oGrpIter)

        if bRemove:
            del self._dName2Iter[sCardName]
        elif self.iExtraLevelsMode in [SHOW_EXPANSIONS,
                EXPANSIONS_AND_CARD_SETS]:
            self._update_2nd_level_expansions(oPhysCard, iChg, 0)
        elif self.iExtraLevelsMode in [SHOW_CARD_SETS,
                CARD_SETS_AND_EXPANSIONS] and \
                        self._dNameSecondLevel2Iter.has_key(sCardName):
            # FIXME: This badly needs refactoring as well
            if self._oCardSet.parent and (
                    self.iParentCountMode == MINUS_THIS_SET or (
                    self.iParentCountMode ==
                        MINUS_SETS_IN_USE and self._oCardSet.inuse)):
                # Need to update the parent counts for the child entry
                for sValue in self._dNameSecondLevel2Iter[sCardName]:
                    for oChildIter in \
                            self._dNameSecondLevel2Iter[sCardName][sValue]:
                        iCnt = self.get_int_value(oChildIter, 1)
                        iParCnt = self.get_int_value(oChildIter, 2) - iChg
                        self._update_entry(oChildIter, iCnt, iParCnt)
                        if self._dName2nd3rdLevel2Iter.has_key(
                                (sCardName, sValue)):
                            sExpName = self.get_expansion_name(
                                    oPhysCard.expansion)
                            if sExpName in self._dName2nd3rdLevel2Iter[
                                    (sCardName, sValue)]:
                                for oSubIter in self._dName2nd3rdLevel2Iter[
                                        (sCardName, sValue)][sExpName]:
                                    iCnt = self.get_int_value(oSubIter, 1)
                                    iParCnt = self.get_int_value(oSubIter, 2) \
                                            - iChg
                                    self._update_entry(oSubIter, iCnt, iParCnt)
            if self.iExtraLevelsMode == CARD_SETS_AND_EXPANSIONS and iChg > 0:
                # We may need to add a expansion entry to below this card set,
                # so we check
                sExpName = self.get_expansion_name(oPhysCard.expansion)
                iParCnt = None
                for sCardSetName in self._dNameSecondLevel2Iter[sCardName]:
                    oFilter = FilterAndBox([
                        PhysicalCardSetFilter(sCardSetName),
                        SpecificPhysCardIdFilter(oPhysCard.id)])
                    if not self._dName2nd3rdLevel2Iter.has_key((sCardName,
                        sCardSetName)) or not self._dName2nd3rdLevel2Iter[
                                (sCardName, sCardSetName)].has_key(sExpName):
                        # Check if we now need to add an entry for this card
                        # set
                        iCnt = oFilter.select(
                                self.cardclass).distinct().count()
                        if iCnt > 0:
                            # We need to add the expansion here
                            if iParCnt is None:
                                iParCnt = self._get_parent_count(oPhysCard)
                            bIncCard, bDecCard = self.check_inc_dec(iCnt)
                            for oChildIter in self._dNameSecondLevel2Iter[
                                    sCardName][sCardSetName]:
                                self._add_extra_level(oChildIter, sExpName,
                                        (iCnt, iParCnt, bIncCard, bDecCard))

        self._check_if_empty()

        # Notify Listeners
        for oListener in self.dListeners:
            oListener.alter_card_count(oCard, iChg)

    def alter_parent_count(self, oPhysCard, iChg, bCheckAddRemove=True):
        """Alter the parent count by iChg

           if bCheckAddRemove is False, we don't check whether anything should
           be removed from the model. This is used for sibling card set
           changes.
           """
        bRemove = False
        sCardName = oPhysCard.abstractCard.name
        for oIter in self._dName2Iter[sCardName]:
            oGrpIter = self.iter_parent(oIter)
            iParGrpCnt = self.get_int_value(oGrpIter, 2) + iChg
            iParCnt = self.get_int_value(oIter, 2) + iChg
            if self.iParentCountMode == IGNORE_PARENT:
                # We touch nothing in this case
                iParGrpCnt = 0
                iParCnt = 0
            iGrpCnt = self.get_int_value(oGrpIter, 1)
            iCnt = self.get_int_value(oIter, 1)
            self._update_entry(oIter, iCnt, iParCnt)
            self.set(oGrpIter, 2, self.format_parent_count(iParGrpCnt,
                iGrpCnt))
            if not self.check_card_iter_stays(oIter) and bCheckAddRemove:
                bRemove = True
                self._remove_sub_iters(sCardName)
                iParCnt = self.get_int_value(oIter, 2)
                iParGrpCnt = self.get_int_value(oGrpIter, 2) - iParCnt
                iGrpCnt = self.get_int_value(oGrpIter, 1)
                self.remove(oIter)
                # Fix the group counts
                self.set(oGrpIter, 2, self.format_parent_count(iParGrpCnt,
                        iGrpCnt))
                if not self.check_group_iter_stays(oGrpIter):
                    sGroupName = self.get_value(oGrpIter, 0)
                    del self._dGroupName2Iter[sGroupName]
                    self.remove(oGrpIter)

        if bRemove:
            del self._dName2Iter[sCardName]
        elif self.iExtraLevelsMode != NO_SECOND_LEVEL:
            if self.iExtraLevelsMode in [SHOW_EXPANSIONS,
                    EXPANSIONS_AND_CARD_SETS]:
                self._update_2nd_level_expansions(oPhysCard, 0, iChg,
                        bCheckAddRemove)
            elif self.iParentCountMode != IGNORE_PARENT:
                sExpName = self.get_expansion_name(oPhysCard.expansion)
                # Loop over all the children, and modify the count
                # if needed
                if self._dNameSecondLevel2Iter.has_key(sCardName):
                    for sValue in self._dNameSecondLevel2Iter[sCardName]:
                        for oChildIter in self._dNameSecondLevel2Iter[
                                sCardName][sValue]:
                            iParCnt = self.get_int_value(oChildIter, 2) \
                                    + iChg
                            iCnt = self.get_int_value(oChildIter, 1)
                            self._update_entry(oChildIter, iCnt, iParCnt)
                        if self._dName2nd3rdLevel2Iter.has_key((sCardName,
                            sValue)):
                            for sName in self._dName2nd3rdLevel2Iter[
                                    (sCardName, sValue)]:
                                if self.iExtraLevelsMode \
                                        == CARD_SETS_AND_EXPANSIONS \
                                        and sName != sExpName:
                                    continue
                                for oSubIter in \
                                        self._dName2nd3rdLevel2Iter[
                                                (sCardName, sValue)][
                                                        sName]:
                                    iParCnt = self.get_int_value(oSubIter,
                                            2) + iChg
                                    iCnt = self.get_int_value(oSubIter, 1)
                                    self._update_entry(oSubIter, iCnt,
                                            iParCnt)

        self._check_if_empty()

    def alter_child_count(self, oPhysCard, sCardSetName, iChg):
        """Adjust the count for the card in the given card set by iChg"""
        # pylint: disable-msg = E1101
        # PyProtocols confuses pylint
        oChildPCS = IPhysicalCardSet(sCardSetName)
        if not oChildPCS.inuse:
            # Shouldn't happen
            return
        bRemove = False
        sCardName = oPhysCard.abstractCard.name
        sExpName = self.get_expansion_name(oPhysCard.expansion)
        if (self.iExtraLevelsMode == SHOW_EXPANSIONS and \
                self.iShowCardMode == CHILD_CARDS) or \
                self.iExtraLevelsMode == EXPANSIONS_AND_CARD_SETS:
            # Check if we need to add or remove an expansion entry
            if iChg > 0:
                if (not self._dNameSecondLevel2Iter.has_key(sCardName) or not
                        self._dNameSecondLevel2Iter[sCardName].has_key(
                            sExpName)) and  self.iShowCardMode == CHILD_CARDS:
                    iCnt = 0 # 2nd level is expansions, so count is 0
                    iParCnt = self._get_parent_count(oPhysCard, iCnt)
                    bIncCard, bDecCard = self.check_inc_dec(iCnt)
                    for oIter in self._dName2Iter[sCardName]:
                        self._add_extra_level(oIter, sExpName,
                                (iCnt, iParCnt, bIncCard, bDecCard))
                if self.iExtraLevelsMode == EXPANSIONS_AND_CARD_SETS and \
                        self._dNameSecondLevel2Iter[sCardName].has_key(
                                sExpName):
                    if self._dName2nd3rdLevel2Iter.has_key(
                            (sCardName, sExpName)) and \
                                    self._dName2nd3rdLevel2Iter[(sCardName,
                                sExpName)].has_key(sCardSetName):
                        # Update counts
                        for oIter in self._dName2nd3rdLevel2Iter[
                                (sCardName, sExpName)][sCardSetName]:
                            iCnt = self.get_int_value(oIter, 1) + iChg
                            self.set(oIter, 1, self.format_count(iCnt))
                    else:
                        # We need to add 2nd3rd level entries
                        # Since we're adding this entry, it must be 1
                        iCnt = 1
                        for oIter in self._dNameSecondLevel2Iter[sCardName][
                                sExpName]:
                            iParCnt = self.get_int_value(oIter, 2)
                            bIncCard, bDecCard = self.check_inc_dec(iCnt)
                            self._add_extra_level(oIter, sCardSetName,
                                    (iCnt, iParCnt, bIncCard, bDecCard))

            elif self._dNameSecondLevel2Iter.has_key(sCardName) and \
                      self._dNameSecondLevel2Iter[sCardName].has_key(sExpName):
                bRemoveChild = False
                if self._dName2nd3rdLevel2Iter.has_key((sCardName,
                    sExpName)) and self._dName2nd3rdLevel2Iter[
                            (sCardName, sExpName)].has_key(
                                    sCardSetName):
                    bRemoveGC = False
                    for oSubIter in self._dName2nd3rdLevel2Iter[
                            (sCardName, sExpName)][sCardSetName]:
                        iCnt = self.get_int_value(oSubIter, 1) + \
                                iChg
                        self.set(oSubIter, 1, self.format_count(
                            iCnt))
                        if not self.check_child_iter_stays(
                                oSubIter, oPhysCard):
                            bRemoveGC = True
                            self.remove(oSubIter)
                    if bRemoveGC:
                        del self._dName2nd3rdLevel2Iter[(sCardName,
                            sExpName)]
                for oChildIter in self._dNameSecondLevel2Iter[
                        sCardName][sExpName]:
                    if not self.check_child_iter_stays(oChildIter,
                            oPhysCard):
                        bRemoveChild = True
                if bRemoveChild:
                    self._remove_second_level(sCardName, sExpName)
        elif self.iExtraLevelsMode == SHOW_CARD_SETS:
            if self._dNameSecondLevel2Iter.has_key(sCardName) and \
                    self._dNameSecondLevel2Iter[sCardName].has_key(
                            sCardSetName):
                # Alter the count
                bRemoveChild = False
                for oChildIter in self._dNameSecondLevel2Iter[
                        sCardName][sCardSetName]:
                    iCnt = self.get_int_value(oChildIter, 1) + iChg
                    # We can't change parent counts, so no need to
                    # consider them
                    self.set(oChildIter, 1, self.format_count(iCnt))
                    if not self.check_child_iter_stays(oChildIter,
                               oPhysCard):
                        bRemoveChild = True
                if bRemoveChild:
                    self._remove_second_level(sCardName, sCardSetName)
            elif iChg > 0:
                # Need to add an entry
                iCnt = 1
                bIncCard, bDecCard = self.check_inc_dec(iCnt)
                for oIter in self._dName2Iter[sCardName]:
                    iParCnt = self.get_int_value(oIter, 2)
                    self._add_extra_level(oIter, sCardSetName,
                            (iCnt, iParCnt, bIncCard, bDecCard))
        elif self.iExtraLevelsMode == CARD_SETS_AND_EXPANSIONS:
            if self._dNameSecondLevel2Iter.has_key(sCardName) and \
                    self._dNameSecondLevel2Iter[sCardName].has_key(
                            sCardSetName):
                # Alter counts, checking if we need a
                # new 3rd level entry, or to remove any entries
                bRemoveChild = False
                for oChildIter in self._dNameSecondLevel2Iter[
                        sCardName][sCardSetName]:
                    iCnt = self.get_int_value(oChildIter, 1) + iChg
                    iParCnt = self.get_int_value(oChildIter, 2)
                    self.set(oChildIter, 1, self.format_count(iCnt))
                    if not self.check_child_iter_stays(oChildIter,
                               oPhysCard):
                        bRemoveChild = True

                if self._dName2nd3rdLevel2Iter.has_key((sCardName,
                    sCardSetName)) and self._dName2nd3rdLevel2Iter[
                            (sCardName, sCardSetName)].has_key(
                                    sExpName):
                    # Update entry
                    bRemoveGC = False
                    for oSubIter in self._dName2nd3rdLevel2Iter[
                            (sCardName, sCardSetName)][sExpName]:
                        iCnt = self.get_int_value(oSubIter, 1) + iChg
                        iParCnt = self.get_int_value(oSubIter, 2)
                        self.set(oSubIter, 1, self.format_count(iCnt))
                        if not self.check_child_iter_stays(oSubIter,
                                oPhysCard):
                            self.remove(oSubIter)
                            bRemoveGC = True
                    if bRemoveGC:
                        del self._dName2nd3rdLevel2Iter[(sCardName,
                            sCardSetName)][sExpName]
                else:
                    # Need to add an entry
                    iThisCSCnt = self.get_card_iterator(
                            SpecificPhysCardIdFilter(
                                oPhysCard.id)).count()
                    iCnt = 1
                    iParCnt = self._get_parent_count(oPhysCard,
                            iThisCSCnt)
                    bIncCard, bDecCard = self.check_inc_dec(iCnt)
                    for oChildIter in self._dNameSecondLevel2Iter[
                            sCardName][sCardSetName]:
                        self._add_extra_level(oChildIter, sExpName,
                                (iCnt, iParCnt, bIncCard, bDecCard))
                if bRemoveChild:
                    self._remove_second_level(sCardName, sCardSetName)
            else:
                # Add a card set entry
                iCnt = 1
                bIncCard, bDecCard = self.check_inc_dec(iCnt)
                for oIter in self._dName2Iter[sCardName]:
                    iParCnt = self.get_int_value(oIter, 2)
                    self._add_extra_level(oIter, sCardSetName,
                            (iCnt, iParCnt, bIncCard, bDecCard))
                # Add the third level entry
                iThisCSCnt = self.get_card_iterator(
                        SpecificPhysCardIdFilter(oPhysCard.id)).count()
                iParCnt = self._get_parent_count(oPhysCard, iThisCSCnt)
                for oChildIter in self._dNameSecondLevel2Iter[
                        sCardName][sCardSetName]:
                    self._add_extra_level(oChildIter, sExpName, (iCnt,
                        iParCnt, bIncCard, bDecCard))

        # Check if we need to cleanup any card entries
        if len(self._dName2Iter[sCardName]) > 0:
            oIter = self._dName2Iter[sCardName][0]
            bRemove = not self.check_card_iter_stays(oIter)

        if bRemove:
            for oIter in self._dName2Iter[sCardName]:
                oGrpIter = self.iter_parent(oIter)
                self._remove_sub_iters(sCardName)
                self.remove(oIter)
                if not self.check_group_iter_stays(oGrpIter):
                    sGroupName = self.get_value(oGrpIter, 0)
                    del self._dGroupName2Iter[sGroupName]
                    self.remove(oGrpIter)
            del self._dName2Iter[sCardName]

        self._check_if_empty()
