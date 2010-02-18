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
from sutekh.core.DBSignals import listen_changed, disconnect_changed

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
                if not sChildSet in self.dExpansions:
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
            iParCnt = self.iParentCount
            for sCardSet, iCnt in self.dChildCardSets.iteritems():
                bIncCard, bDecCard = self.get_inc_dec_flags(iCnt)
                dChildren[sCardSet] = [iCnt, iParCnt, bIncCard, bDecCard]
        else:
            for sExpName in self.dExpansions:
                iParCnt = self.dParentExpansions.get(sExpName, 0)
                dChildren[sExpName] = {}
                if not sExpName in self.dChildCardSets:
                    # No children for this expansion
                    continue
                for sCardSet, iCnt in \
                        self.dChildCardSets[sExpName].iteritems():
                    bIncCard, bDecCard = self.get_inc_dec_flags(iCnt)
                    dChildren[sExpName][sCardSet] = [iCnt, iParCnt,
                            bIncCard, bDecCard]
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
        listen_changed(self.card_changed, PhysicalCardSet)

    def cleanup(self):
        # FIXME: We should make sure that all the references go
        """Remove the signal handler - avoids issues when card sets are
           deleted, but the objects are still around."""
        disconnect_changed(self.card_changed, PhysicalCardSet)

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
            sText = self._get_empty_text()
            self.oEmptyIter = self.append(None, (sText, self.format_count(0),
                '0', False, False, [], []))

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

        # Disable sorting while we do the insertions
        iSortColumn, iSortOrder = self.get_sort_column_id()
        # iSortColumn can be None or 0
        # None => defaults, so we do nothing, but 0 is a column to sort on
        # so we do need to unset in that case
        if iSortColumn is not None:
            # gtk+ docs says this disables sorting
            self.set_sort_column_id(-2, 0)

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
            # We reverse, so we can prepend rather than append -
            # this is a lot faster for long lists.
            for oCard, oRow in reversed(oGroupIter):
                iCnt = oRow.get_card_count()
                iParCnt = oRow.get_parent_count()
                iGrpCnt += iCnt
                iParGrpCnt += iParCnt
                bIncCard, bDecCard = self.check_inc_dec(iCnt)
                oChildIter = self.prepend(oSectionIter)
                self.set(oChildIter, 0, oCard.name,
                    1, self.format_count(iCnt),
                    2, self.format_parent_count(iParCnt, iCnt),
                    3, bIncCard, 4, bDecCard)
                self._dName2Iter.setdefault(oCard.name, []).append(oChildIter)
                self._add_children(oChildIter, oRow)
            # Update Group Section
            aTexts, aIcons = self.lookup_icons(sGroup)
            if aTexts:
                self.set(oSectionIter,
                        0, sGroup,
                        1, self.format_count(iGrpCnt),
                        2, self.format_parent_count(iParGrpCnt, iGrpCnt),
                        3, False,
                        4, False,
                        5, aTexts,
                        6, aIcons,
                        )
            else:
                self.set(oSectionIter,
                        0, sGroup,
                        1, self.format_count(iGrpCnt),
                        2, self.format_parent_count(iParGrpCnt, iGrpCnt),
                        3, False,
                        4, False,
                        )

        self._check_if_empty()
        # Restore sorting

        if iSortColumn is not None:
            self.set_sort_column_id(iSortColumn, iSortOrder)

        # Notify Listeners
        for oListener in self.dListeners:
            oListener.load(aAbsCards)

    def _add_children(self, oChildIter, oRow):
        """Add the needed children for a card in the model."""
        dExpansionInfo = oRow.get_expansion_info()
        dChildInfo = oRow.get_child_info()
        sCardName = self.get_name_from_iter(oChildIter)
        if self.iExtraLevelsMode == SHOW_EXPANSIONS:
            for sExpansion in sorted(dExpansionInfo):
                self._add_extra_level(oChildIter, sExpansion,
                        dExpansionInfo[sExpansion],
                        (2, sCardName))
        elif self.iExtraLevelsMode == SHOW_CARD_SETS:
            for sChildSet in sorted(dChildInfo):
                self._add_extra_level(oChildIter, sChildSet,
                        dChildInfo[sChildSet],
                        (2, sCardName))
        elif self.iExtraLevelsMode == EXPANSIONS_AND_CARD_SETS:
            for sExpansion in sorted(dExpansionInfo):
                oSubIter = self._add_extra_level(oChildIter,
                        sExpansion, dExpansionInfo[sExpansion],
                        (2, sCardName))
                for sChildSet in sorted(dChildInfo[sExpansion]):
                    self._add_extra_level(oSubIter, sChildSet,
                            dChildInfo[sExpansion][sChildSet],
                            (3, (sCardName, sExpansion)))
        elif self.iExtraLevelsMode == CARD_SETS_AND_EXPANSIONS:
            for sChildSet in sorted(dChildInfo):
                oSubIter = self._add_extra_level(oChildIter,
                        sChildSet, dChildInfo[sChildSet],
                        (2, sCardName))
                for sExpansion in sorted(dExpansionInfo[sChildSet]):
                    self._add_extra_level(oSubIter, sExpansion,
                            dExpansionInfo[sChildSet][sExpansion],
                            (3, (sCardName, sChildSet)))

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
                4, bDecCard
                )

    def _add_extra_level(self, oParIter, sName, tInfo, tKeyInfo):
        """Add an extra level iterator to the card list model."""
        iCnt, iParCnt, bIncCard, bDecCard = tInfo
        iDepth, oKey = tKeyInfo
        oIter = self.append(oParIter)
        # Rely on the defaults to handle icons + textlist
        # Since we skip the handling here, this is about 15% faster on
        # large loads such as All Cards + Expansions + Card Sets
        self.set(oIter, 0, sName, 1, self.format_count(iCnt),
            2, self.format_parent_count(iParCnt, iCnt), 3, bIncCard,
            4, bDecCard)
        if iDepth == 2:
            self._dNameSecondLevel2Iter.setdefault(oKey, {})
            self._dNameSecondLevel2Iter[oKey].setdefault(sName,
                    []).append(oIter)
        elif iDepth == 3:
            self._dName2nd3rdLevel2Iter.setdefault(oKey, {})
            self._dName2nd3rdLevel2Iter[oKey].setdefault(sName,
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
           card set
           """
        oIter = self.get_iter(oPath)
        iDepth = self.iter_depth(oIter)
        if iDepth == 1:
            sName = self.get_name_from_iter(oIter)
            sExpansion = None
        elif iDepth == 2 and (self.iExtraLevelsMode == SHOW_EXPANSIONS
                or self.iExtraLevelsMode == EXPANSIONS_AND_CARD_SETS):
            sName = self.get_name_from_iter(self.get_iter(
                norm_path(oPath)[0:2]))
            sExpansion = self.get_value(oIter, 0)
        elif iDepth == 2 and (self.iExtraLevelsMode == SHOW_CARD_SETS or
                self.iExtraLevelsMode == CARD_SETS_AND_EXPANSIONS):
            sName = self.get_name_from_iter(self.get_iter(
                norm_path(oPath)[0:2]))
            sExpansion = None
        elif iDepth == 3 and self.iExtraLevelsMode == EXPANSIONS_AND_CARD_SETS:
            sName = self.get_name_from_iter(self.get_iter(
                norm_path(oPath)[0:2]))
            sExpansion = self.get_name_from_iter(
                    self.get_iter(norm_path(oPath)[0:3]))
        elif iDepth == 3 and self.iExtraLevelsMode == CARD_SETS_AND_EXPANSIONS:
            sName = self.get_name_from_iter(self.get_iter(
                norm_path(oPath)[0:2]))
            sExpansion = self.get_value(oIter, 0)
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
        if iDepth == 0 or iDepth == 3 or (iDepth == 2 and
                self.iExtraLevelsMode in [SHOW_EXPANSIONS,
                    EXPANSIONS_AND_CARD_SETS]):
            return {} # Not at the right level
        dResult = {}
        if self.iExtraLevelsMode == SHOW_EXPANSIONS or \
            self.iExtraLevelsMode == EXPANSIONS_AND_CARD_SETS:
            # Can read off the data from the model, so do so
            oChildIter = self.iter_children(oIter)
            while oChildIter:
                oChildPath = self.get_path(oChildIter)
                sCardName, sExpansion, iCount, iDepth = \
                        self.get_drag_info_from_path(oChildPath)
                dResult[sExpansion] = iCount
                oChildIter = self.iter_next(oChildIter)
        elif iDepth == 1:
            # Need to get expansion info from the database
            sCardName = self.get_name_from_iter(self.get_iter(oPath))
            oCardIter = self.get_card_iterator(
                    SpecificCardFilter(sCardName))
            # pylint: disable-msg=E1101
            # Pyprotocols confuses pylint
            for oCard in oCardIter:
                oPhysCard = IPhysicalCard(oCard)
                sExpansion = self.get_expansion_name(oPhysCard.expansion)
                dResult.setdefault(sExpansion, 0)
                dResult[sExpansion] += 1
        elif self.iExtraLevelsMode == CARD_SETS_AND_EXPANSIONS:
            # can read info from the model
            oChildIter = self.iter_children(oIter)
            while oChildIter:
                oChildPath = self.get_path(oChildIter)
                sCardName, sExpansion, iCount, iDepth = \
                        self.get_drag_info_from_path(oChildPath)
                dResult[sExpansion] = iCount
                oChildIter = self.iter_next(oChildIter)
        else:
            # Need to get the cards in the specified card set
            sCardName = self.get_name_from_iter(self.get_iter(
                norm_path(oPath)[0:2]))
            sCardSetName = self.get_name_from_iter(self.get_iter(oPath))
            oCardIter = self.get_card_iterator(
                    SpecificCardFilter(sCardName))
            oCSFilter = FilterAndBox([self._dCache['child filters'][
                sCardSetName], SpecificCardFilter(sCardName) ])
            for oCard in oCSFilter.select(self.cardclass).distinct():
                # pylint: disable-msg=E1101
                # Pyprotocols confuses pylint
                oPhysCard = IPhysicalCard(oCard)
                sExpansion = self.get_expansion_name(oPhysCard.expansion)
                dResult.setdefault(sExpansion, 0)
                dResult[sExpansion] += 1
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
            if not 'child filters' in self._dCache:
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
                self._dCache['child card sets'][sName] = {}
                for oCard in [IPhysicalCard(x) for x in
                        oFullFilter.select(self.cardclass).distinct()]:
                    dChildCardCache[sName].setdefault(oCard.abstractCard,
                            []).append(oCard)
                    self._dCache['child cards'].setdefault(oCard, 0)
                    self._dCache['child abstract cards'].setdefault(
                            oCard.abstractCard.id, 0)
                    self._dCache['child cards'][oCard] += 1
                    self._dCache['child abstract cards'][
                            oCard.abstractCard.id] += 1
                    self._dCache['child card sets'][sName].setdefault(
                            oCard, 0)
                    self._dCache['child card sets'][sName][oCard] += 1
        elif self.iShowCardMode == CHILD_CARDS and \
                self._dCache['child filters']:
            # Need to setup the cache
            oFullFilter = FilterAndBox([self._dCache['all children filter'],
                oCurFilter])
            for oCard in [IPhysicalCard(x) for x in oFullFilter.select(
                    self.cardclass).distinct()]:
                self._dCache['child cards'].setdefault(oCard, 0)
                self._dCache['child abstract cards'].setdefault(
                        oCard.abstractCard.id, 0)
                self._dCache['child cards'][oCard] += 1
                self._dCache['child abstract cards'][
                        oCard.abstractCard.id] += 1
        return dChildCardCache

    def _get_parent_list(self, oCurFilter):
        """Get a list object for the cards in the parent card set."""
        # pylint: disable-msg=E1101
        # SQLObject + PyProtocols confuse pylint
        if self._oCardSet.parent and not (
                self.iParentCountMode == IGNORE_PARENT and
                self.iShowCardMode != PARENT_CARDS):
            # It's tempting to use get_card_iterator here, but that
            # obviously doesn't work because of _oBaseFilter
            self._dCache['parent filter'] = PhysicalCardSetFilter(
                    self._oCardSet.parent.name)
            oParentFilter = FilterAndBox([self._dCache['parent filter'],
                oCurFilter])
            aParentCards = [IPhysicalCard(x) for x in
                    oParentFilter.select(self.cardclass).distinct()]
            for oPhysCard in aParentCards:
                self._dCache['parent cards'].setdefault(oPhysCard, 0)
                self._dCache['parent abstract cards'].setdefault(
                        oPhysCard.abstractCard.id, 0)
                self._dCache['parent cards'][oPhysCard] += 1
                self._dCache['parent abstract cards'][
                        oPhysCard.abstractCard.id] += 1

    def _get_extra_cards(self, oCurFilter):
        """Return any extra cards not in this card set that need to be
           considered for the current mode."""
        # pylint: disable-msg=E1101
        # Pyprotocols confuses pylint
        if self.iShowCardMode == ALL_CARDS:
            oFullFilter = FilterAndBox([PhysicalCardFilter(), oCurFilter])
            aExtraCards = [x for x in
                    oFullFilter.select(PhysicalCard).distinct()]
        elif self.iShowCardMode == PARENT_CARDS and self._oCardSet.parent:
            # Since we handle numbers later, this works
            aExtraCards = self._dCache['parent cards']
        elif self.iShowCardMode == CHILD_CARDS and \
                self._dCache['child filters']:
            aExtraCards = self._dCache['child cards']
        else:
            # No point in doing the extra work
            aExtraCards = []
        return aExtraCards

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
        dPhysCards = {}

        self._dCache['parent cards'] = {}
        self._dCache['parent abstract cards'] = {}
        self._dCache['child cards'] = {}
        self._dCache['child abstract cards'] = {}
        self._dCache['sibling cards'] = {}
        self._dCache['sibling abstract cards'] = {}
        self._dCache['child card sets'] = {}

        if oCardIter.count() == 0 and self.iShowCardMode == THIS_SET_ONLY:
            # Short circuit the more expensive checks if we've got no cards
            # and can't influence this card set
            return (self.groupby([], lambda x: x[0]), [])

        oCurFilter = self.get_current_filter()
        if oCurFilter is None:
            oCurFilter = NullFilter()

        dChildCardCache = self._get_child_filters(oCurFilter)
        self._get_parent_list(oCurFilter)

        # Other card show modes
        aExtraCards = self._get_extra_cards(oCurFilter)

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
            dPhysCards.setdefault(oPhysCard, 0)
            dPhysCards[oPhysCard] += 1
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

        self._add_parent_info(dAbsCards, dPhysCards)

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
            aChildCards = []
            if oAbsCard in dChildCardCache[sCardSetName]:
                aChildCards = dChildCardCache[sCardSetName][oAbsCard]
            if self.iExtraLevelsMode == SHOW_CARD_SETS or \
                    self.iExtraLevelsMode == CARD_SETS_AND_EXPANSIONS:
                iChildCnt = len(aChildCards)
                if iChildCnt > 0 or self.iShowCardMode == ALL_CARDS or \
                        self.bEditable:
                    # We treat card sets like expansion, showing all of them
                    # when editable or showing all cards.
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
                    if not dChildInfo:
                        for oRarityPair in oAbsCard.rarity:
                            sExpName = self.get_expansion_name(
                                    oRarityPair.expansion)
                            dChildInfo.setdefault(sExpName, {})
                        dChildInfo.setdefault(self.sUnknownExpansion, {})
                    for sExpName in dChildInfo:
                        dChildInfo[sExpName].setdefault(sCardSetName, 0)
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
        if not 'sibling filter' in self._dCache:
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
                self._dCache['sibling cards'].setdefault(oPhysCard, 0)
                self._dCache['sibling abstract cards'].setdefault(
                        oAbsCard.id, 0)
                self._dCache['sibling cards'][oPhysCard] += 1
                self._dCache['sibling abstract cards'][oAbsCard.id] += 1
        return dSiblingCards

    def _update_parent_info(self, oAbsCard, oSetInfo, dPhysCards):
        """Update the parent counts with info from this set"""
        # pylint: disable-msg=E1103, E1101
        # pyprotocols confusion
        dParentExp = oSetInfo.dParentExpansions
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
                    if not sExpansion in dParentExp:
                        if sExpansion != self.sUnknownExpansion:
                            oPhysCard = IPhysicalCard((oAbsCard,
                                IExpansion(sExpansion)))
                        else:
                            oPhysCard = IPhysicalCard((oAbsCard, None))
                        # Query the database
                        if oPhysCard in dPhysCards:
                            dParentExp[sExpansion] = -dPhysCards[oPhysCard]

    def _add_parent_info(self, dAbsCards, dPhysCards):
        """Add the parent count info into the mix"""
        # pylint: disable-msg=E1101
        # Pyprotocols confuses pylint
        if (self.iParentCountMode == IGNORE_PARENT and
                self.iShowCardMode != PARENT_CARDS) or \
                        not self._oCardSet.parent:
            return # No point in doing anything at all
        if self.iParentCountMode == MINUS_SETS_IN_USE:
            dSiblingCards = self._get_sibling_cards()
            for oAbsCard, oRow in dAbsCards.iteritems():
                if oAbsCard in dSiblingCards:
                    for oPhysCard in dSiblingCards[oAbsCard]:
                        oRow.iParentCount -= 1
                        sExpansion = self.get_expansion_name(
                                oPhysCard.expansion)
                        oRow.dParentExpansions.setdefault(sExpansion, 0)
                        oRow.dParentExpansions[sExpansion] -= 1

        if self.iParentCountMode == MINUS_THIS_SET:
            for oAbsCard, oRow in dAbsCards.iteritems():
                oRow.iParentCount = -oRow.iCount
                self._update_parent_info(oAbsCard, oRow, dPhysCards)

        for oPhysCard in self._dCache['parent cards']:
            # pylint: disable-msg=E1101
            # Pyprotocols confuses pylint
            oAbsCard = oPhysCard.abstractCard
            if oAbsCard in dAbsCards:
                sExpansion = self.get_expansion_name(oPhysCard.expansion)
                dParentExp = dAbsCards[oAbsCard].dParentExpansions
                dParentExp.setdefault(sExpansion, 0)
                if self.iParentCountMode != IGNORE_PARENT:
                    iNum = self._dCache['parent cards'][oPhysCard]
                    dAbsCards[oAbsCard].iParentCount += iNum
                    dParentExp[sExpansion] += iNum

    def _remove_sub_iters(self, sCardName):
        """Remove the children rows for the card entry sCardName"""
        if not sCardName in self._dNameSecondLevel2Iter:
            # Nothing to clean up (not showing second level, etc.)
            return
        aSecondLevelKeys = self._dNameSecondLevel2Iter[sCardName].keys()
        # We remove values in the loop, so we need this copy
        for sValue in aSecondLevelKeys:
            self._remove_second_level(sCardName, sValue)

    def _remove_second_level(self, sCardName, sValue):
        """Remove a second level entry and everything below it"""
        if not sCardName in self._dNameSecondLevel2Iter or \
                not sValue in self._dNameSecondLevel2Iter[sCardName]:
            return # Nothing to do
        tSLKey = (sCardName, sValue)
        if tSLKey in self._dName2nd3rdLevel2Iter:
            for sName in self._dName2nd3rdLevel2Iter[tSLKey]:
                for oIter in self._dName2nd3rdLevel2Iter[tSLKey][sName]:
                    self.remove(oIter)
            del self._dName2nd3rdLevel2Iter[tSLKey]
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
        if self.iParentCountMode != IGNORE_PARENT and self._oCardSet.parent:
            if oPhysCard in self._dCache['parent cards']:
                iParCnt = self._dCache['parent cards'][oPhysCard]
            else:
                # Because of how we construct the cache, we may have
                # missing entries
                oParentFilter = FilterAndBox([
                    SpecificPhysCardIdFilter(oPhysCard.id),
                    self._dCache['parent filter']])
                iParCnt = oParentFilter.select(
                        self.cardclass).distinct().count()
                # Cache this lookup for the future
                self._dCache['parent cards'][oPhysCard] = iParCnt
                self._dCache['parent abstract cards'].setdefault(
                        oPhysCard.abstractCard.id, 0)
                self._dCache['parent abstract cards'][
                        oPhysCard.abstractCard.id] += iParCnt
            if self.iParentCountMode == MINUS_THIS_SET:
                if iThisSetCnt is None:
                    iThisSetCnt = self.get_card_iterator(
                            SpecificPhysCardIdFilter(oPhysCard.id)).count()
                iParCnt -= iThisSetCnt
            elif self.iParentCountMode == MINUS_SETS_IN_USE:
                if self._dCache['sibling filter']:
                    if oPhysCard in self._dCache['sibling cards']:
                        iParCnt -= self._dCache['sibling cards'][oPhysCard]
                    else:
                        oInUseFilter = FilterAndBox([
                            SpecificPhysCardIdFilter(oPhysCard.id),
                            self._dCache['sibling filter']])
                        iSibCnt = oInUseFilter.select(
                                self.cardclass).distinct().count()
                        iParCnt -= iSibCnt
                        self._dCache['sibling cards'][oPhysCard] = iSibCnt
                        self._dCache['sibling abstract cards'].setdefault(
                                oPhysCard.abstractCard.id, 0)
                        self._dCache['sibling abstract cards'][
                                oPhysCard.abstractCard.id] += iSibCnt
        return iParCnt

    def _add_new_group(self, sGroup):
        """Handle the addition of a new group entry from add_new_card"""
        aTexts, aIcons = self.lookup_icons(sGroup)
        if aTexts:
            oSectionIter = self.append(None, (sGroup, self.format_count(0),
                self.format_parent_count(0, 0), False, False, aTexts, aIcons))
        else:
            oSectionIter = self.append(None, (sGroup, self.format_count(0),
                self.format_parent_count(0, 0), False, False, [], []))
        return oSectionIter

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

        bNonZero = False

        # pylint: disable-msg=W0612
        # Not interested in aAbsCards here, but we need the GroupedIter
        oGroupedIter, aAbsCards = self.grouped_card_iter(oCardIter)

        # Iterate over groups
        for sGroup, oGroupIter in oGroupedIter:
            # Check for null group
            if sGroup is None:
                sGroup = '<< None >>'

            # Find Group Section
            if sGroup in self._dGroupName2Iter:
                oSectionIter = self._dGroupName2Iter[sGroup]
                iGrpCnt = self.get_int_value(oSectionIter, 1)
                iParGrpCnt = self.get_int_value(oSectionIter, 2)
            else:
                iGrpCnt = 0
                iParGrpCnt = 0
                oSectionIter = self._add_new_group(sGroup)
                self._dGroupName2Iter[sGroup] = oSectionIter
            # Add Cards
            for oCard, oRow in oGroupIter:
                # Due to the various view modes, we aren't assured of
                # getting back only the new card from get_grouped_iterator,
                # so this check is needed
                if oAbsCard.id != oCard.id:
                    continue
                iCnt = oRow.get_card_count()
                if iCnt > 0:
                    bNonZero = True
                iParCnt = oRow.get_parent_count()
                iGrpCnt += iCnt
                iParGrpCnt += iParCnt
                bIncCard, bDecCard = self.check_inc_dec(iCnt)
                oChildIter = self.append(oSectionIter)
                self.set(oChildIter, 0, oCard.name,
                    1, self.format_count(iCnt),
                    2, self.format_parent_count(iParCnt, iCnt),
                    3, bIncCard, 4, bDecCard)
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
        if bNonZero:
            for oListener in self.dListeners:
                oListener.add_new_card(oAbsCard)

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
        """Utility function. Returns true if changes to the child card sets
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

    def _update_cache(self, oPhysCard, iChg, sType):
        """Update the number in the card cache"""
        sPhysCache = "%s cards" % sType
        if oPhysCard in self._dCache[sPhysCache]:
            sAbsCache = "%s abstract cards" % sType
            self._dCache[sPhysCache][oPhysCard] += iChg
            self._dCache[sAbsCache][oPhysCard.abstractCard.id] += iChg

    def _update_child_set_cache(self, oPhysCard, iChg, sName):
        """Update the number in the card cache"""
        if sName in self._dCache['child card sets'] and \
                oPhysCard in self._dCache['child card sets'][sName]:
            self._dCache['child card sets'][sName][oPhysCard] += iChg

    def _clean_cache(self, oPhysCard, sType):
        """Remove zero entries from the card cache"""
        sPhysCache = "%s cards" % sType
        if oPhysCard in self._dCache[sPhysCache] and \
                self._dCache[sPhysCache][oPhysCard] == 0:
            del self._dCache[sPhysCache][oPhysCard]
            sAbsCache = "%s abstract cards" % sType
            if self._dCache[sAbsCache][oPhysCard.abstractCard.id] == 0:
                del self._dCache[sAbsCache][oPhysCard.abstractCard.id]

    def _clean_child_set_cache(self, oPhysCard, sName):
        """Update the number in the card cache"""
        if sName in self._dCache['child card sets'] and \
                oPhysCard in self._dCache['child card sets'][sName] and \
                self._dCache['child card sets'][sName][oPhysCard] == 0:
            del self._dCache['child card sets'][sName][oPhysCard]

    def card_changed(self, oCardSet, oPhysCard, iChg):
        """Listen on card changes.

           We listen to the special signal, so we can hook in after the
           database has been updated. This simplifies the update logic
           as we can query the database and obtain accurate results.
           Does rely on everyone calling send_changed_signal.
           """
        # pylint: disable-msg=E1101, R0912
        # E1101 - Pyprotocols confuses pylint
        # R0912 - need to consider several cases, so lots of branches
        sCardName = oPhysCard.abstractCard.name
        if oCardSet.id == self._oCardSet.id:
            # Changing a card from this card set
            if self._oCardSet.inuse:
                self._update_cache(oPhysCard, iChg, 'sibling')
            if sCardName in self._dName2Iter:
                self.alter_card_count(oPhysCard, iChg)
            elif iChg > 0:
                self.add_new_card(oPhysCard) # new card
            if self._oCardSet.inuse:
                self._clean_cache(oPhysCard, 'sibling')
        elif self.changes_with_children() and oCardSet.parent and \
                oCardSet.inuse and oCardSet.parent.id == self._oCardSet.id:
            # Changing a child card set
            self._update_cache(oPhysCard, iChg, 'child')
            self._update_child_set_cache(oPhysCard, iChg, oCardSet.name)
            if sCardName in self._dName2Iter:
                self.alter_child_count(oPhysCard, oCardSet.name, iChg)
            elif iChg > 0 and oPhysCard not in self._dCache['child cards']:
                self.add_new_card(oPhysCard)
            self._clean_cache(oPhysCard, 'child')
            self._clean_child_set_cache(oPhysCard, oCardSet.name)
        elif self.changes_with_parent() and oCardSet.id == \
                self._oCardSet.parent.id:
            # Changing parent card set
            self._update_cache(oPhysCard, iChg, 'parent')
            if sCardName in self._dName2Iter:
                # update cache
                self.alter_parent_count(oPhysCard, iChg)
            elif iChg > 0 and oPhysCard not in self._dCache['parent cards']:
                # New card that we haven't seen before, so see if we need
                # to add it
                self.add_new_card(oPhysCard)
            self._clean_cache(oPhysCard, 'parent')
        elif self.changes_with_siblings() and oCardSet.parent and \
                oCardSet.inuse and oCardSet.parent.id == \
                self._oCardSet.parent.id:
            # Changing sibling card set
            self._update_cache(oPhysCard, iChg, 'sibling')
            if sCardName in self._dName2Iter:
                # This is only called when using MINUS_SETS_IN_USE,
                # So this changes the available pool of parent cards (by -iChg)
                # There's no possiblity of this adding or deleting a card from
                # the model
                self.alter_parent_count(oPhysCard, -iChg, False)
            self._clean_cache(oPhysCard, 'sibling')
        # Doesn't affect us, so ignore

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

    def _check_child_card_entries(self, oIter):
        """Loop over the card level entries, calling check_card_iter_stays.
           Return true if at least one card entry stays."""
        oChildIter = self.iter_children(oIter)
        while oChildIter:
            if self.check_card_iter_stays(oChildIter):
                return True
            oChildIter = self.iter_next(oChildIter)
        return False

    def check_child_iter_stays(self, oIter, oPhysCard):
        """Check if an expansion or child card set iter stays"""
        # Conditions vary with cards shown and the editable flag.
        # This routine works on the assumption that we only need to
        # get the result right when the parent row isn't being removed.
        # If the parent row is to be removed, returning the wrong result
        # here doesn't matter - this simplifies the logic a bit
        # pylint: disable-msg=E1101
        # E1101: PyProtocols confuses pylint
        iCnt = self.get_int_value(oIter, 1)
        if iCnt > 0 or self.bEditable:
            # When editing, we don't delete 0 entries unless the card vanishes
            return True
        iDepth = self.iter_depth(oIter)
        if iDepth == 3 and self.iExtraLevelsMode in [EXPANSIONS_AND_CARD_SETS,
                CARD_SETS_AND_EXPANSIONS]:
            # Since we're not editable here, we always remove these
            return False
        iParCnt = self.get_int_value(oIter, 2)
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
            if oPhysCard in self._dCache['parent cards']:
                bResult = self._dCache['parent cards'][oPhysCard] > 0
        elif self.iShowCardMode == CHILD_CARDS and \
                self.iExtraLevelsMode == SHOW_EXPANSIONS:
            # check the cache
            if oPhysCard in self._dCache['child cards'] and \
                    self._dCache['child cards'][oPhysCard] > 0:
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
            # Check the parent card cache
            oAbsCard = IAbstractCard(self.get_name_from_iter(oIter))
            if oAbsCard.id in self._dCache['parent abstract cards']:
                bResult = self._dCache['parent abstract cards'][
                        oAbsCard.id] > 0
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
                if oAbsCard.id in self._dCache['child abstract cards']:
                    bResult = self._dCache['child abstract cards'][
                            oAbsCard.id] > 0
        return bResult

    def check_group_iter_stays(self, oIter):
        """Check if we need to remove the top-level item"""
        # Conditions for removal vary with the cards shown
        if self.iShowCardMode == ALL_CARDS:
            return True # We don't remove group entries
        iCnt = self.get_int_value(oIter, 1)
        if iCnt > 0:
            # Count is non-zero, so we stay
            return True
        iParCnt = self.get_int_value(oIter, 2)
        if self.iShowCardMode == PARENT_CARDS and iParCnt > 0:
            # Obviously parent cards present
            return True
        elif self.iShowCardMode == PARENT_CARDS and \
                self.iParentCountMode not in [PARENT_COUNT, MINUS_THIS_SET]:
            return self._check_child_card_entries(oIter)
        elif self.iShowCardMode == CHILD_CARDS:
            return self._check_child_card_entries(oIter)
        return False

    def _update_3rd_level_card_sets(self, oPhysCard, iChg, iParChg,
            bCheckAddRemove):
        """Update the third level for EXPANSIONS_AND_CARD_SETS"""
        sCardName = oPhysCard.abstractCard.name
        sExpName = self.get_expansion_name(oPhysCard.expansion)
        tExpKey = (sCardName, sExpName)
        if tExpKey in self._dName2nd3rdLevel2Iter:
            bRemoveChild = False
            # Update the 3rd level
            iParCnt = None
            for aIterList in self._dName2nd3rdLevel2Iter[tExpKey].itervalues():
                for oSubIter in aIterList:
                    iCnt = self.get_int_value(oSubIter, 1)
                    if not iParCnt:
                        iParCnt = self._update_parent_count(oSubIter, iChg,
                                iParChg)
                    self._update_entry(oSubIter, iCnt, iParCnt)
                    if bRemoveChild or (bCheckAddRemove and
                            (iChg < 0 or iParChg < 0) and
                            not self.check_child_iter_stays(oSubIter,
                                oPhysCard)):
                        bRemoveChild = True
                        self.remove(oSubIter)
            if bRemoveChild:
                del self._dName2nd3rdLevel2Iter[tExpKey]

    def _add_3rd_level_card_sets(self, oPhysCard, iParCnt):
        """Add 3rd level entries for the EXPANSIONS_AND_CARD_SETS mode"""
        sCardName = oPhysCard.abstractCard.name
        sExpName = self.get_expansion_name(oPhysCard.expansion)
        #for sCardSet, oSetFilter in self._dCache['child filters'].iteritems():
        for sCardSet, oSetFilter in self._dCache['child filters'].iteritems():
            iCnt = 0
            if sCardSet in self._dCache['child card sets'] and \
                    oPhysCard in self._dCache['child card sets'][sCardSet]:
                iCnt = self._dCache['child card sets'][sCardSet][oPhysCard]
            else:
                oFilter = FilterAndBox([SpecificPhysCardIdFilter(oPhysCard.id),
                    oSetFilter])
                iCnt = oFilter.select(self.cardclass).distinct().count()
                # Cache this lookup
                self._dCache['child card sets'].setdefault(sCardSet, {})
                self._dCache['child card sets'][sCardSet][oPhysCard] = iCnt
            if iCnt > 0:
                # We can ignore the iCnt == 0 cases (bEditable
                # True, etc.), since we know those entries
                # would already be showing if required.
                bIncCard, bDecCard = self.check_inc_dec(iCnt)
                for oIter in self._dNameSecondLevel2Iter[sCardName][sExpName]:
                    self._add_extra_level(oIter, sCardSet, (iCnt, iParCnt,
                        bIncCard, bDecCard), (3, (sCardName, sExpName)))

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
        if sCardName in self._dNameSecondLevel2Iter and \
                sExpName in self._dNameSecondLevel2Iter[sCardName]:
            iCnt = None
            for oChildIter in self._dNameSecondLevel2Iter[sCardName][sExpName]:
                if not iCnt:
                    iCnt = self.get_int_value(oChildIter, 1) + iChg
                    iParCnt = self._update_parent_count(oChildIter, iChg,
                            iParChg)
                self._update_entry(oChildIter, iCnt, iParCnt)
                if bRemove or (bCheckAddRemove and
                        (iChg < 0 or iParChg < 0) and
                        not self.check_child_iter_stays(oChildIter,
                            oPhysCard)):
                    bRemove = True
            if not bRemove:
                self._update_3rd_level_card_sets(oPhysCard, iChg, iParChg,
                        bCheckAddRemove)
        elif iChg > 0 or (iParChg > 0 and self.iShowCardMode == PARENT_CARDS
                and bCheckAddRemove):
            bIncCard, bDecCard = self.check_inc_dec(iChg)
            iParCnt = self._get_parent_count(oPhysCard, iChg)
            for oIter in self._dName2Iter[sCardName]:
                self._add_extra_level(oIter, sExpName, (iChg, iParCnt,
                    bIncCard, bDecCard), (2, sCardName))
                if self.iExtraLevelsMode == EXPANSIONS_AND_CARD_SETS \
                        and self.iShowCardMode not in [ALL_CARDS,
                                CHILD_CARDS]:
                    self._add_3rd_level_card_sets(oPhysCard, iParCnt)
        if bRemove:
            self._remove_second_level(sCardName, sExpName)

    def _update_2nd_3rd_level_parent_counts(self, oPhysCard, iChg):
        """Update the parent counts for CARD_SETS and CARD_SETS_AND_EXPANSIONS
           modes."""
        sCardName = oPhysCard.abstractCard.name
        # Loop over all the children, and modify the count
        # if needed
        if sCardName in self._dNameSecondLevel2Iter:
            sExpName = self.get_expansion_name(oPhysCard.expansion)
            for sValue in self._dNameSecondLevel2Iter[sCardName]:
                for oChildIter in self._dNameSecondLevel2Iter[sCardName][
                        sValue]:
                    iParCnt = self.get_int_value(oChildIter, 2) + iChg
                    iCnt = self.get_int_value(oChildIter, 1)
                    self._update_entry(oChildIter, iCnt, iParCnt)
                tExpKey = (sCardName, sValue)
                if tExpKey in self._dName2nd3rdLevel2Iter:
                    for sName in self._dName2nd3rdLevel2Iter[tExpKey]:
                        if self.iExtraLevelsMode == CARD_SETS_AND_EXPANSIONS \
                                and sName != sExpName:
                            continue
                        for oSubIter in self._dName2nd3rdLevel2Iter[tExpKey][
                                sName]:
                            iParCnt = self.get_int_value(oSubIter, 2) + iChg
                            iCnt = self.get_int_value(oSubIter, 1)
                            self._update_entry(oSubIter, iCnt, iParCnt)

    def _update_3rd_level_expansions(self, oPhysCard):
        """Add expansion level items for CARD_SETS_AND_EXPANSIONS mode if
           needed."""
        sCardName = oPhysCard.abstractCard.name
        sExpName = self.get_expansion_name(oPhysCard.expansion)
        iParCnt = None
        for sCardSetName in self._dNameSecondLevel2Iter[sCardName]:
            tCSKey = (sCardName, sCardSetName)
            if not tCSKey in self._dName2nd3rdLevel2Iter or not \
                    sExpName in self._dName2nd3rdLevel2Iter[tCSKey] and \
                    oPhysCard in self._dCache['child cards']:
                # check if we need to add a entry
                if sCardSetName in self._dCache['child card sets'] and \
                        oPhysCard in self._dCache['child card sets'][
                                sCardSetName]:
                    iCnt = self._dCache['child card sets'][sCardSetName][
                            oPhysCard]
                else:
                    oFilter = FilterAndBox([
                        self._dCache['child filters'][sCardSetName],
                        SpecificPhysCardIdFilter(oPhysCard.id)])
                    iCnt = oFilter.select(self.cardclass).distinct().count()
                    # Cache this lookup
                    self._dCache['child card sets'].setdefault(sCardSetName,
                            {})
                    self._dCache['child card sets'][sCardSetName][
                            oPhysCard] = iCnt
                if iCnt > 0:
                    # We need to add the expansion here
                    if iParCnt is None:
                        iParCnt = self._get_parent_count(oPhysCard)
                    bIncCard, bDecCard = self.check_inc_dec(iCnt)
                    for oChildIter in self._dNameSecondLevel2Iter[sCardName][
                            sCardSetName]:
                        self._add_extra_level(oChildIter, sExpName, (iCnt,
                            iParCnt, bIncCard, bDecCard), (3, (sCardName,
                                sCardSetName)))

    def alter_card_count(self, oPhysCard, iChg):
        """Alter the card count of a card which is in the current list
           (i.e. in the card set and not filtered out) by iChg."""
        # pylint: disable-msg=E1101
        # PyProtocols confuses pylint here
        oCard = IAbstractCard(oPhysCard)
        sCardName = oCard.name
        bRemove = False
        bChecked = False # flag to avoid repeated work
        for oIter in self._dName2Iter[sCardName]:
            oGrpIter = self.iter_parent(oIter)
            iCnt = self.get_int_value(oIter, 1) + iChg
            iGrpCnt = self.get_int_value(oGrpIter, 1) + iChg
            iParGrpCnt = self.get_int_value(oGrpIter, 2)
            self.set(oIter, 1, self.format_count(iCnt))
            iParCnt = self.get_int_value(oIter, 2)
            if self._card_count_changes_parent():
                iParCnt -= iChg
                iParGrpCnt -= iChg

            if not bChecked and not self.check_card_iter_stays(oIter):
                bRemove = True
            bChecked = True

            if bRemove:
                self._remove_sub_iters(sCardName)
                self.remove(oIter)
                iParGrpCnt -= iParCnt
            else:
                self._update_entry(oIter, iCnt, iParCnt)

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
                        sCardName in self._dNameSecondLevel2Iter:
            if self._card_count_changes_parent():
                # Need to update the parent counts for the child entry
                self._update_2nd_3rd_level_parent_counts(oPhysCard, -iChg)
            if self.iExtraLevelsMode == CARD_SETS_AND_EXPANSIONS and iChg > 0:
                # We may need to add a expansion entry to below this card set,
                # so we check
                self._update_3rd_level_expansions(oPhysCard)

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
        # update cache
        bRemove = False
        bChecked = False # flag so we don't revist decisions
        if not bCheckAddRemove:
            bChecked = True # skip check
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
            if not bChecked and not self.check_card_iter_stays(oIter):
                bRemove = True
            bChecked = True
            if bRemove:
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
                self._update_2nd_3rd_level_parent_counts(oPhysCard, iChg)

        self._check_if_empty()

    def alter_child_count_card_sets(self, oPhysCard, sCardSetName, iChg):
        """Handle the alter child card case when showing child sets as the
           second level without expansions."""
        # pylint: disable-msg = E1101
        # PyProtocols confuses pylint
        sCardName = oPhysCard.abstractCard.name
        if sCardName in self._dNameSecondLevel2Iter and \
                sCardSetName in self._dNameSecondLevel2Iter[sCardName]:
            # Alter the count
            bRemove = False
            for oIter in self._dNameSecondLevel2Iter[sCardName][sCardSetName]:
                iCnt = self.get_int_value(oIter, 1) + iChg
                # We can't change parent counts, so no need to
                # consider them
                self.set(oIter, 1, self.format_count(iCnt))
                if bRemove or not \
                        self.check_child_iter_stays(oIter, oPhysCard):
                    bRemove = True
            if bRemove:
                self._remove_second_level(sCardName, sCardSetName)
        elif iChg > 0:
            # Need to add an entry
            iCnt = 1
            bIncCard, bDecCard = self.check_inc_dec(iCnt)
            for oIter in self._dName2Iter[sCardName]:
                iParCnt = self.get_int_value(oIter, 2)
                self._add_extra_level(oIter, sCardSetName,
                        (iCnt, iParCnt, bIncCard, bDecCard),
                        (2, sCardName))

    def _add_child_3rd_level_exp_entry(self, oPhysCard, sCardSetName,
            tExpKey):
        """Add the third level expansion entry when dealing with adding cards
           to a child card set"""
        # pylint: disable-msg = E1101
        # PyProtocols confuses pylint
        iCnt = 1
        sCardName, sExpName = tExpKey
        iThisCSCnt = self.get_card_iterator(SpecificPhysCardIdFilter(
            oPhysCard.id)).count()
        iParCnt = self._get_parent_count(oPhysCard, iThisCSCnt)
        bIncCard, bDecCard = self.check_inc_dec(iCnt)
        for oIter in self._dNameSecondLevel2Iter[sCardName][sCardSetName]:
            self._add_extra_level(oIter, sExpName, (iCnt, iParCnt, bIncCard,
                bDecCard), (3, (sCardName, sCardSetName)))

    def alter_child_count(self, oPhysCard, sCardSetName, iChg):
        """Adjust the count for the card in the given card set by iChg"""
        # Child card set number changes can't change the values displayed
        # for card level items, but they can cause card level items to vanish
        # So we don't need to loop over the card level, merely the sub-levels,
        # but we do need to check if the card is removed at the end
        # pylint: disable-msg = E1101
        # PyProtocols confuses pylint
        sCardName = oPhysCard.abstractCard.name
        if (self.iExtraLevelsMode == SHOW_EXPANSIONS and
                self.iShowCardMode == CHILD_CARDS) \
                        or self.iExtraLevelsMode == EXPANSIONS_AND_CARD_SETS:
            self.alter_child_count_expansions(oPhysCard, sCardSetName, iChg)
        elif self.iExtraLevelsMode == SHOW_CARD_SETS:
            self.alter_child_count_card_sets(oPhysCard, sCardSetName, iChg)
        elif self.iExtraLevelsMode == CARD_SETS_AND_EXPANSIONS:
            self.alter_child_count_card_sets_exps(oPhysCard, sCardSetName,
                    iChg)
        # Check if we need to cleanup any card entries
        bRemove = False
        if len(self._dName2Iter[sCardName]) > 0 and iChg < 0:
            # Test if we need to remove entries
            oIter = self._dName2Iter[sCardName][0]
            iParCnt = self.get_int_value(oIter, 2)
            bRemove = not self.check_card_iter_stays(oIter)
        if bRemove:
            # Remove the card entry
            for oIter in self._dName2Iter[sCardName]:
                oGrpIter = self.iter_parent(oIter)
                iGrpCnt = self.get_int_value(oGrpIter, 1)
                iParGrpCnt = self.get_int_value(oGrpIter, 2) - iParCnt
                self._remove_sub_iters(sCardName)
                self.remove(oIter)
                self.set(oGrpIter, 2, self.format_parent_count(iParGrpCnt,
                    iGrpCnt))
                if not self.check_group_iter_stays(oGrpIter):
                    sGroupName = self.get_value(oGrpIter, 0)
                    del self._dGroupName2Iter[sGroupName]
                    self.remove(oGrpIter)
            del self._dName2Iter[sCardName]
        self._check_if_empty()

    def _inc_exp_child_set_count(self, tExpKey, sCardSetName):
        """Increment the count (from alter_child_child_count_expansions)
           when showing expansion & child card sets"""
        sCardName, sExpName = tExpKey
        if tExpKey in self._dName2nd3rdLevel2Iter and sCardSetName in \
                self._dName2nd3rdLevel2Iter[tExpKey]:
            # Update counts
            for oIter in self._dName2nd3rdLevel2Iter[tExpKey][sCardSetName]:
                iCnt = self.get_int_value(oIter, 1) + 1
                self.set(oIter, 1, self.format_count(iCnt))
        else:
            # We need to add 2nd3rd level entries
            # Since we're adding this entry, it must be 1
            iCnt = 1
            for oIter in self._dNameSecondLevel2Iter[sCardName][sExpName]:
                iParCnt = self.get_int_value(oIter, 2)
                bIncCard, bDecCard = self.check_inc_dec(iCnt)
                self._add_extra_level(oIter, sCardSetName, (iCnt, iParCnt,
                    bIncCard, bDecCard), (3, (sCardName, sExpName)))

    def alter_child_count_expansions(self, oPhysCard, sCardSetName, iChg):
        """Handle the alter child card case when showing expansions as the
           second level."""
        # pylint: disable-msg = E1101
        # PyProtocols confuses pylint
        sCardName = oPhysCard.abstractCard.name
        sExpName = self.get_expansion_name(oPhysCard.expansion)
        tExpKey = (sCardName, sExpName)
        # Check if we need to add or remove an expansion entry
        if iChg > 0:
            if (not sCardName in self._dNameSecondLevel2Iter or not
                    sExpName in self._dNameSecondLevel2Iter[sCardName]) \
                            and self.iShowCardMode == CHILD_CARDS:
                iCnt = 0 # 2nd level is expansions, so count is 0
                iParCnt = self._get_parent_count(oPhysCard, iCnt)
                bIncCard, bDecCard = self.check_inc_dec(iCnt)
                for oIter in self._dName2Iter[sCardName]:
                    self._add_extra_level(oIter, sExpName,
                            (iCnt, iParCnt, bIncCard, bDecCard),
                            (2, sCardName))
            if self.iExtraLevelsMode == EXPANSIONS_AND_CARD_SETS and \
                    sExpName in self._dNameSecondLevel2Iter[sCardName]:
                self._inc_exp_child_set_count(tExpKey, sCardSetName)
        elif sCardName in self._dNameSecondLevel2Iter and \
                sExpName in self._dNameSecondLevel2Iter[sCardName]:
            if tExpKey in self._dName2nd3rdLevel2Iter and \
                    sCardSetName in self._dName2nd3rdLevel2Iter[tExpKey]:
                bRemove = False
                for oIter in self._dName2nd3rdLevel2Iter[tExpKey][
                        sCardSetName]:
                    iCnt = self.get_int_value(oIter, 1) + iChg
                    self.set(oIter, 1, self.format_count(iCnt))
                    if bRemove or not self.check_child_iter_stays(oIter,
                            oPhysCard):
                        bRemove = True
                        self.remove(oIter)
                if bRemove:
                    del self._dName2nd3rdLevel2Iter[tExpKey]
            bRemove = False
            for oIter in self._dNameSecondLevel2Iter[sCardName][sExpName]:
                if bRemove or not self.check_child_iter_stays(oIter,
                        oPhysCard):
                    bRemove = True
            if bRemove:
                self._remove_second_level(sCardName, sExpName)

    def alter_child_count_card_sets_exps(self, oPhysCard, sCardSetName, iChg):
        """Handle the alter child card case when showing child sets as the
           second level with expansions"""
        # pylint: disable-msg = E1101
        # PyProtocols confuses pylint
        sCardName = oPhysCard.abstractCard.name
        sExpName = self.get_expansion_name(oPhysCard.expansion)
        tExpKey = (sCardName, sExpName)
        if sCardName in self._dNameSecondLevel2Iter and \
                sCardSetName in self._dNameSecondLevel2Iter[sCardName]:
            # Alter counts, checking if we need a
            # new 3rd level entry, or to remove any entries
            bRemove = False
            tCSKey = (sCardName, sCardSetName)
            for oIter in self._dNameSecondLevel2Iter[sCardName][sCardSetName]:
                iCnt = self.get_int_value(oIter, 1) + iChg
                iParCnt = self.get_int_value(oIter, 2)
                self.set(oIter, 1, self.format_count(iCnt))
                if not self.check_child_iter_stays(oIter, oPhysCard):
                    bRemove = True
            if bRemove:
                self._remove_second_level(sCardName, sCardSetName)
            elif tCSKey in self._dName2nd3rdLevel2Iter and \
                    sExpName in self._dName2nd3rdLevel2Iter[tCSKey]:
                # Update entry
                bRemove = False
                for oIter in self._dName2nd3rdLevel2Iter[tCSKey][sExpName]:
                    iCnt = self.get_int_value(oIter, 1) + iChg
                    iParCnt = self.get_int_value(oIter, 2)
                    self.set(oIter, 1, self.format_count(iCnt))
                    if bRemove or not self.check_child_iter_stays(oIter,
                            oPhysCard):
                        self.remove(oIter)
                        bRemove = True
                if bRemove:
                    del self._dName2nd3rdLevel2Iter[tCSKey][sExpName]
            else:
                self._add_child_3rd_level_exp_entry(oPhysCard, sCardSetName,
                        tExpKey)
        else:
            # Add a card set entry
            iCnt = 1
            bIncCard, bDecCard = self.check_inc_dec(iCnt)
            for oIter in self._dName2Iter[sCardName]:
                iParCnt = self.get_int_value(oIter, 2)
                self._add_extra_level(oIter, sCardSetName,
                        (iCnt, iParCnt, bIncCard, bDecCard),
                        (2, sCardName))
            self._add_child_3rd_level_exp_entry(oPhysCard, sCardSetName,
                    tExpKey)
