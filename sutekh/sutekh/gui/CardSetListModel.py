# CardSetListModel.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# pylint: disable-msg=C0302
# C0302 - This covers a lot of cases, and splitting it into multiple
# files won't gain any clarity

"""The gtk.TreeModel for the card set lists."""

from sutekh.core.Filters import FilterAndBox, NullFilter, PhysicalCardFilter, \
        PhysicalCardSetFilter, SpecificCardIdFilter, \
        MultiPhysicalCardSetMapFilter, SpecificPhysCardIdFilter, \
        MultiSpecificCardIdFilter
from sutekh.core.SutekhObjects import PhysicalCard, IAbstractCard, \
        MapPhysicalCardToPhysicalCardSet, IPhysicalCard, IPhysicalCardSet, \
        PhysicalCardSet, canonical_to_csv
from sutekh.gui.CardListModel import CardListModel, USE_ICONS, HIDE_ILLEGAL
from sutekh.core.DBSignals import listen_changed, disconnect_changed
import gtk

# consts for the different modes we need (iExtraLevelsMode)
NO_SECOND_LEVEL, SHOW_EXPANSIONS, SHOW_CARD_SETS, EXP_AND_CARD_SETS, \
        CARD_SETS_AND_EXP = range(5)
# Different card display modes (iShowCardMode)
THIS_SET_ONLY, ALL_CARDS, PARENT_CARDS, CHILD_CARDS = range(4)
# Different Parent card count modes (iParentCountMode)
IGNORE_PARENT, PARENT_COUNT, MINUS_THIS_SET, MINUS_SETS_IN_USE = range(4)
# Colour constants to save constant lookups
BLACK = gtk.gdk.color_parse('black')
RED = gtk.gdk.color_parse('red')

#
# config text lookup -- keep in sync with configspec.ini
#

EXTRA_LEVEL_OPTION = "extra levels"
EXTRA_LEVEL_LOOKUP = {
    "none": NO_SECOND_LEVEL,
    "expansions": SHOW_EXPANSIONS,
    "card sets": SHOW_CARD_SETS,
    "expansions then card sets": EXP_AND_CARD_SETS,
    "card sets then expansions": CARD_SETS_AND_EXP,
}

SHOW_CARD_OPTION = "cards to show"
SHOW_CARD_LOOKUP = {
    "this set only": THIS_SET_ONLY,
    "all cards": ALL_CARDS,
    "parent cards": PARENT_CARDS,
    "child cards": CHILD_CARDS,
}

PARENT_COUNT_MODE = "parent count mode"
PARENT_COUNT_LOOKUP = {
    "ignore parent": IGNORE_PARENT,
    "parent count": PARENT_COUNT,
    "parent minus this set": MINUS_THIS_SET,
    "parent minus sets in use": MINUS_SETS_IN_USE,
}


class CardSetModelRow(object):
    """Object which holds the data needed for a card set row."""
    # pylint: disable-msg=R0902
    # We do want all these attributes

    def __init__(self, bEditable, iExtraLevelsMode, oAbsCard):
        self.dExpansions = {}
        self.dChildCardSets = {}
        self.dParentExpansions = {}
        self.iCount = 0
        self.iParentCount = 0
        self.iExtraLevelsMode = iExtraLevelsMode
        self.bEditable = bEditable
        self.oAbsCard = oAbsCard
        self.oPhysCard = IPhysicalCard((self.oAbsCard, None))

    def get_parent_count(self):
        """Get the parent count"""
        return self.iParentCount

    def get_inc_dec_flags(self, iCnt):
        """Determine the status of the button flags."""
        if self.bEditable:
            return True, (iCnt > 0)
        return False, False

    def get_card_count(self):
        """Extract a card count from the grouped iterator"""
        return self.iCount

    def get_expansion_info(self):
        """Get information about expansions"""
        dCardExpansions = {}
        if self.iExtraLevelsMode in [SHOW_EXPANSIONS, EXP_AND_CARD_SETS]:
            for tKey, iCnt in self.dExpansions.iteritems():
                sExpName, oPhysCard = tKey
                bIncCard, bDecCard = self.get_inc_dec_flags(iCnt)
                iParCnt = self.dParentExpansions.get(sExpName, 0)
                dCardExpansions[sExpName] = [iCnt, iParCnt, oPhysCard,
                        bIncCard, bDecCard]
        else:
            for sChildSet in self.dChildCardSets:
                dCardExpansions[sChildSet] = {}
                if not sChildSet in self.dExpansions:
                    continue
                for tKey, iCnt in \
                        self.dExpansions[sChildSet].iteritems():
                    sExpName, oPhysCard = tKey
                    bIncCard, bDecCard = self.get_inc_dec_flags(iCnt)
                    iParCnt = self.dParentExpansions.get(sExpName, 0)
                    dCardExpansions[sChildSet][sExpName] = [iCnt, iParCnt,
                            oPhysCard, bIncCard, bDecCard]
        return dCardExpansions

    def get_child_info(self):
        """Get information about child card sets"""
        dChildren = {}
        if self.iExtraLevelsMode in [SHOW_CARD_SETS, CARD_SETS_AND_EXP]:
            iParCnt = self.iParentCount
            for sCardSet, iCnt in self.dChildCardSets.iteritems():
                bIncCard, bDecCard = self.get_inc_dec_flags(iCnt)
                dChildren[sCardSet] = [iCnt, iParCnt, self.oPhysCard, bIncCard,
                        bDecCard]
        else:
            for sExpName, oPhysCard in self.dExpansions:
                iParCnt = self.dParentExpansions.get(sExpName, 0)
                dChildren[sExpName] = {}
                if not sExpName in self.dChildCardSets:
                    # No children for this expansion
                    continue
                for sCardSet, iCnt in self.dChildCardSets[
                        sExpName].iteritems():
                    bIncCard, bDecCard = self.get_inc_dec_flags(iCnt)
                    dChildren[sExpName][sCardSet] = [iCnt, iParCnt, oPhysCard,
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
    def __init__(self, sSetName, oConfig):
        super(CardSetCardListModel, self).__init__(oConfig)
        self._cCardClass = MapPhysicalCardToPhysicalCardSet
        self._oBaseFilter = PhysicalCardSetFilter(sSetName)
        self._oCardSet = IPhysicalCardSet(sSetName)
        self._dCache = {}
        self.bChildren = False
        self.bEditable = False
        self._bPhysicalFilter = False
        self._dAbs2Iter = {}
        self._dAbs2Phys = {}
        self._dAbsSecondLevel2Iter = {}
        self._dAbs2nd3rdLevel2Iter = {}
        self._dGroupName2Iter = {}
        self.oEditColour = None
        self._oCountColour = BLACK

        self.iExtraLevelsMode = SHOW_EXPANSIONS
        self.iShowCardMode = THIS_SET_ONLY
        self.iParentCountMode = PARENT_COUNT

        listen_changed(self.card_changed, PhysicalCardSet)

    # pylint: disable-msg=W0212
    # We allow access via these properties

    frame_id = property(fget=lambda self: "pane%s" %
            (self._oController.frame.pane_id,),
            doc="Frame ID of associated card set (for selecting profiles)")

    # TODO: is this a good cardset id?
    cardset_id = property(fget=lambda self: "cs%s" % (self._oCardSet.id,),
            doc="Cardset ID of associated card set (for selecting profiles)")

    #pylint: enable-msg=W0212

    def cleanup(self):
        # FIXME: We should make sure that all the references go
        """Remove the signal handler - avoids issues when card sets are
           deleted, but the objects are still around."""
        disconnect_changed(self.card_changed, PhysicalCardSet)
        self._oController = None

    def set_count_colour(self):
        """Format the card count accordingly"""
        self._oCountColour = BLACK
        if self.bEditable and self.oEditColour:
            self._oCountColour = self.oEditColour

    def get_count_colour(self):
        """Get the current color for counts"""
        return self._oCountColour

    def set_par_count_colour(self, oIter, iParCnt, iCnt):
        """Format the parent card count"""
        if self.iParentCountMode != IGNORE_PARENT:
            oColour = BLACK
            if (self.iParentCountMode == PARENT_COUNT and iParCnt < iCnt) or \
                    iParCnt < 0:
                oColour = RED
            self.set(oIter, 7, oColour)

    def _check_if_empty(self):
        """Add the empty entry if needed"""
        if not self._dAbs2Iter:
            # Showing nothing
            sText = self._get_empty_text()
            self.oEmptyIter = self.append(None, (sText, 0, 0, False, False, [],
                [], BLACK,
                None, None))

    def load(self):
        # pylint: disable-msg=R0914
        # we use many local variables for clarity
        """Clear and reload the underlying store. For use after initialisation,
           when the filter or grouping changes or when card set relationships
           change.
           """
        self.set_count_colour()
        self.clear()
        self._dAbs2Phys = {}
        self._dAbs2Iter = {}
        self._dAbsSecondLevel2Iter = {}
        self._dAbs2nd3rdLevel2Iter = {}
        self._dGroupName2Iter = {}
        # Clear cache (we can't do this in grouped_card_iter, since that
        # is also called by add_new_card)
        self._dCache = {}

        self._bPhysicalFilter = False
        if self.applyfilter:
            self._bPhysicalFilter = self._check_filter()

        oCardIter = self.get_card_iterator(self.get_current_filter())
        oGroupedIter, aCards = self.grouped_card_iter(oCardIter)
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
            sGroup = self._fix_group_name(sGroup)

            # Create Group Section
            oSectionIter = self.prepend(None)
            self._dGroupName2Iter[sGroup] = oSectionIter

            # Fill in Cards
            iGrpCnt = 0
            iParGrpCnt = 0
            # We prepend rather than append -
            # this is a lot faster for long lists.
            for oCard, oRow in oGroupIter:
                iCnt = oRow.get_card_count()
                iParCnt = oRow.get_parent_count()
                iGrpCnt += iCnt
                iParGrpCnt += iParCnt
                bIncCard, bDecCard = self.check_inc_dec(iCnt)
                oChildIter = self.prepend(oSectionIter)
                # Direct lookup, for same reason as in CardListModel
                self.set(oChildIter, 0, oCard.name,
                    1, iCnt, 2, iParCnt,
                    3, bIncCard, 4, bDecCard,
                    8, oCard,
                    9, oRow.oPhysCard,
                    )
                self.set_par_count_colour(oChildIter, iParCnt, iCnt)
                self._dAbs2Iter.setdefault(oCard, []).append(oChildIter)
                self._add_children(oChildIter, oRow)
            # Update Group Section
            aTexts, aIcons = self.lookup_icons(sGroup)
            if aTexts:
                self.set(oSectionIter,
                        0, sGroup,
                        1, iGrpCnt,
                        2, iParGrpCnt,
                        3, False,
                        4, False,
                        5, aTexts,
                        6, aIcons,
                        8, None,
                        9, None,
                        )
            else:
                self.set(oSectionIter,
                        0, sGroup,
                        1, iGrpCnt,
                        2, iParGrpCnt,
                        3, False,
                        4, False,
                        8, None,
                        9, None,
                        )

            self.set_par_count_colour(oSectionIter, iParGrpCnt, iGrpCnt)

        self._check_if_empty()

        self._set_display_name(self._oConfig.get_postfix_the_display())
        # Restore sorting

        if iSortColumn is not None:
            self.set_sort_column_id(iSortColumn, iSortOrder)

        # Notify Listeners
        for oListener in self.dListeners:
            oListener.load(aCards)

    def _add_children(self, oChildIter, oRow):
        """Add the needed children for a card in the model."""
        dExpansionInfo = oRow.get_expansion_info()
        dChildInfo = oRow.get_child_info()
        if self.iExtraLevelsMode == SHOW_EXPANSIONS:
            for sExpansion in dExpansionInfo:
                self._add_extra_level(oChildIter, sExpansion,
                        dExpansionInfo[sExpansion],
                        (2, oRow.oAbsCard))
        elif self.iExtraLevelsMode == SHOW_CARD_SETS:
            for sChildSet in dChildInfo:
                self._add_extra_level(oChildIter, sChildSet,
                        dChildInfo[sChildSet],
                        (2, oRow.oAbsCard))
        elif self.iExtraLevelsMode == EXP_AND_CARD_SETS:
            for sExpansion in dExpansionInfo:
                oSubIter = self._add_extra_level(oChildIter,
                        sExpansion, dExpansionInfo[sExpansion],
                        (2, oRow.oAbsCard))
                for sChildSet in dChildInfo[sExpansion]:
                    self._add_extra_level(oSubIter, sChildSet,
                            dChildInfo[sExpansion][sChildSet],
                            (3, (oRow.oAbsCard, sExpansion)))
        elif self.iExtraLevelsMode == CARD_SETS_AND_EXP:
            for sChildSet in dChildInfo:
                oSubIter = self._add_extra_level(oChildIter,
                        sChildSet, dChildInfo[sChildSet],
                        (2, oRow.oAbsCard))
                for sExpansion in dExpansionInfo[sChildSet]:
                    self._add_extra_level(oSubIter, sExpansion,
                            dExpansionInfo[sChildSet][sExpansion],
                            (3, (oRow.oAbsCard, sChildSet)))

    def check_inc_dec(self, iCnt):
        """Helper function to get correct flags"""
        if not self.bEditable:
            return False, False
        return True, (iCnt > 0)

    def _update_entry(self, oIter, iCnt, iParCnt):
        """Update an oIter with the count and parent count"""
        bIncCard, bDecCard = self.check_inc_dec(iCnt)
        self.set(oIter, 1, iCnt, 2, iParCnt, 3, bIncCard, 4, bDecCard)
        self.set_par_count_colour(oIter, iParCnt, iCnt)

    def _add_extra_level(self, oParIter, sName, tInfo, tKeyInfo):
        """Add an extra level iterator to the card list model."""
        iCnt, iParCnt, oPhysCard, bIncCard, bDecCard = tInfo
        iDepth, oKey = tKeyInfo
        if iDepth == 2:
            oAbsCard = oKey
        else:
            oAbsCard = oKey[0]
        oIter = self.prepend(oParIter)
        # Rely on the defaults to handle icons + textlist
        # Since we skip the handling here, this is about 15% faster on
        # large loads such as All Cards + Expansions + Card Sets
        self.set(oIter, 0, sName, 1, iCnt, 2, iParCnt, 3, bIncCard,
                4, bDecCard, 8, oAbsCard, 9, oPhysCard)
        self.set_par_count_colour(oIter, iParCnt, iCnt)
        if iDepth == 2:
            self._dAbsSecondLevel2Iter.setdefault(oKey, {})
            self._dAbsSecondLevel2Iter[oKey].setdefault(sName,
                    []).append(oIter)
        elif iDepth == 3:
            self._dAbs2nd3rdLevel2Iter.setdefault(oKey, {})
            self._dAbs2nd3rdLevel2Iter[oKey].setdefault(sName,
                    []).append(oIter)
        return oIter

    def get_exp_name_from_path(self, oPath):
        """Get the expansion information from the model, returning None
           if this is not at a level where the expansion is known.
           """
        oIter = self.get_iter(oPath)
        if self.iter_depth(oIter) not in [2, 3]:
            return None
        sExpName = None
        if self.iExtraLevelsMode in [SHOW_EXPANSIONS, EXP_AND_CARD_SETS] and \
                self.iter_depth(oIter) == 2:
            sExpName = self.get_name_from_iter(oIter)
        elif self.iExtraLevelsMode == CARD_SETS_AND_EXP and \
                self.iter_depth(oIter) == 3:
            sExpName = self.get_name_from_iter(oIter)
        elif self.iExtraLevelsMode == EXP_AND_CARD_SETS and \
                self.iter_depth(oIter) == 3:
            # Need to get information from the parent level
            sExpName = self.get_name_from_iter(self.iter_parent(oIter))
        return sExpName

    def get_all_names_from_iter(self, oIter):
        """Get all the relevant names from the iter (cardname, expansion
           and card set), returning None for any that can't be determined.
           """
        iDepth = self.iter_depth(oIter)
        if iDepth == 0:
            # Top Level item, so no info at all
            return None, None, None
        sCardName = self.get_card_name_from_iter(oIter)
        sExpName = None
        sCardSetName = None
        # Get the expansion name
        if self.iExtraLevelsMode in [SHOW_EXPANSIONS, EXP_AND_CARD_SETS]:
            if iDepth == 2:
                sExpName = self.get_name_from_iter(oIter)
            elif iDepth == 3:
                sExpName = self.get_name_from_iter(self.iter_parent(oIter))
        elif self.iExtraLevelsMode == CARD_SETS_AND_EXP and iDepth == 3:
            sExpName = self.get_name_from_iter(oIter)
        # Get the card set name
        if self.iExtraLevelsMode in [SHOW_CARD_SETS, CARD_SETS_AND_EXP]:
            if iDepth == 2:
                sCardSetName = self.get_name_from_iter(oIter)
            elif iDepth == 3:
                sCardSetName = self.get_name_from_iter(self.iter_parent(oIter))
        elif self.iExtraLevelsMode == EXP_AND_CARD_SETS and iDepth == 3:
            sCardSetName = self.get_name_from_iter(oIter)
        return sCardName, sExpName, sCardSetName

    def get_all_names_from_path(self, oPath):
        """Get all the relevant names from the path

           Convenience wrapper around get_all_names_from_iter for cases
           when the path is easier to get than the iter (selections, etc.)
           This is mainly used by the button signals for editing.
           """
        if oPath:
            # Don' crash if oPath is None for some reason
            oIter = self.get_iter(oPath)
            return self.get_all_names_from_iter(oIter)
        return None, None, None

    def get_drag_info_from_path(self, oPath):
        """Get card name and expansion information from the path for the
           drag and drop code.

           This returns cardname of None if the path is not a card in this
           card set
           """
        oIter = self.get_iter(oPath)
        iDepth = self.iter_depth(oIter)
        if iDepth == 0:
            sName = None
        else:
            sName = self.get_card_name_from_iter(oIter)
        if iDepth < 2:
            sExpansion = None
        elif iDepth == 2 and (self.iExtraLevelsMode == SHOW_EXPANSIONS
                or self.iExtraLevelsMode == EXP_AND_CARD_SETS):
            sExpansion = self.get_value(oIter, 0)
        elif iDepth == 2 and (self.iExtraLevelsMode == SHOW_CARD_SETS or
                self.iExtraLevelsMode == CARD_SETS_AND_EXP):
            sExpansion = None
        elif iDepth == 3 and self.iExtraLevelsMode == EXP_AND_CARD_SETS:
            sExpansion = self.get_name_from_iter(self.iter_parent(oIter))
        elif iDepth == 3 and self.iExtraLevelsMode == CARD_SETS_AND_EXP:
            sExpansion = self.get_value(oIter, 0)
        iCount = self.get_value(oIter, 1)
        return sName, sExpansion, iCount, iDepth

    def get_drag_child_info(self, oPath):
        """Get the expansion information for the card at oPath.

           Always returns the expansions, regaredless of iExtraLevelsMode.
           """
        oIter = self.get_iter(oPath)
        iDepth = self.iter_depth(oIter)
        if iDepth == 0 or iDepth == 3 or (iDepth == 2 and
                self.iExtraLevelsMode in [SHOW_EXPANSIONS, EXP_AND_CARD_SETS]):
            return {} # Not at the right level
        dResult = {}
        if self.iExtraLevelsMode == SHOW_EXPANSIONS or \
            self.iExtraLevelsMode == EXP_AND_CARD_SETS:
            # Can read off the data from the model, so do so
            oChildIter = self.iter_children(oIter)
            while oChildIter:
                oChildPath = self.get_path(oChildIter)
                _sCardName, sExpansion, iCount, iDepth = \
                        self.get_drag_info_from_path(oChildPath)
                dResult[sExpansion] = iCount
                oChildIter = self.iter_next(oChildIter)
        elif iDepth == 1:
            # Need to get expansion info from the database
            oCard = self.get_abstract_card_from_path(oPath)
            oCardIter = self.get_card_iterator(
                    SpecificCardIdFilter(oCard.id))
            # pylint: disable-msg=E1101, E1103
            # Pyprotocols confuses pylint
            for oCard in oCardIter:
                oPhysCard = IPhysicalCard(oCard)
                sExpansion = self.get_expansion_name(oPhysCard.expansion)
                dResult.setdefault(sExpansion, 0)
                dResult[sExpansion] += 1
        elif self.iExtraLevelsMode == CARD_SETS_AND_EXP:
            # can read info from the model
            oChildIter = self.iter_children(oIter)
            while oChildIter:
                oChildPath = self.get_path(oChildIter)
                _sCardName, sExpansion, iCount, iDepth = \
                        self.get_drag_info_from_path(oChildPath)
                dResult[sExpansion] = iCount
                oChildIter = self.iter_next(oChildIter)
        else:
            # Need to get the cards in the specified card set
            oIter = self.get_iter(oPath)
            oCard = self.get_abstract_card_from_iter(oIter)
            sCardSetName = self.get_name_from_iter(oIter)
            oCSFilter = FilterAndBox([self._dCache['child filters'][
                sCardSetName], SpecificCardIdFilter(oCard.id)])
            for oCard in oCSFilter.select(self.cardclass).distinct():
                # pylint: disable-msg=E1101, E1103
                # Pyprotocols confuses pylint
                oPhysCard = IPhysicalCard(oCard)
                sExpansion = self.get_expansion_name(oPhysCard.expansion)
                dResult.setdefault(sExpansion, 0)
                dResult[sExpansion] += 1
        return dResult

    def _init_expansions(self, dExpanInfo, oAbsCard):
        """Initialise the expansion dict for a card"""
        if self.bEditable:
            for oPhysCard in oAbsCard.physicalCards:
                if self.check_card_visible(oPhysCard):
                    dExpanInfo.setdefault((self.get_expansion_name(
                        oPhysCard.expansion), oPhysCard), 0)

    def _init_abs(self, dAbsCards, oAbsCard):
        """Initialize the entry for oAbsCard in dAbsCards"""
        if oAbsCard not in dAbsCards:
            dAbsCards[oAbsCard] = CardSetModelRow(self.bEditable,
                    self.iExtraLevelsMode, oAbsCard)
            if self.iExtraLevelsMode in [SHOW_EXPANSIONS, EXP_AND_CARD_SETS]:
                self._init_expansions(dAbsCards[oAbsCard].dExpansions,
                        oAbsCard)
            if not self.check_card_visible(dAbsCards[oAbsCard].oPhysCard):
                # Fix the Row's Physical Card to point to the first
                # expansion, in alphabetical order
                # pylint: disable-msg=E1101
                # SQLObject confuses pylint
                aPhysCards = [x for x in oAbsCard.physicalCards if
                        self.check_card_visible(x)]
                # This is safe, since we know the None case has been excluded
                aPhysCards.sort(key=lambda x: x.expansion.name)
                dAbsCards[oAbsCard].oPhysCard = aPhysCards[0]

    def _get_child_filters(self, oCurFilter):
        """Get the filters for the child card sets of this card set."""
        # pylint: disable-msg=E1101, E1103
        # SQLObject + PyProtocols confuse pylint
        if self.iExtraLevelsMode in [SHOW_CARD_SETS, EXP_AND_CARD_SETS,
                CARD_SETS_AND_EXP] or self.iShowCardMode == CHILD_CARDS:
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
        if self.iExtraLevelsMode in [SHOW_CARD_SETS, EXP_AND_CARD_SETS,
                CARD_SETS_AND_EXP] and self._dCache['child filters']:
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
            aFilters = [self._dCache['all children filter'], oCurFilter]
            oFullFilter = FilterAndBox(aFilters)
            for oCard in [IPhysicalCard(x) for x in oFullFilter.select(
                    self.cardclass).distinct()]:
                self._dCache['child cards'].setdefault(oCard, 0)
                self._dCache['child abstract cards'].setdefault(
                        oCard.abstractCard.id, 0)
                self._dCache['child cards'][oCard] += 1
                self._dCache['child abstract cards'][
                        oCard.abstractCard.id] += 1
        return dChildCardCache

    def _get_parent_list(self, oCurFilter, oCardIter):
        """Get a list object for the cards in the parent card set."""
        # pylint: disable-msg=E1101, E1103
        # SQLObject + PyProtocols confuse pylint
        if self._oCardSet.parent and not (
                self.iParentCountMode == IGNORE_PARENT and
                self.iShowCardMode != PARENT_CARDS):
            # It's tempting to use get_card_iterator here, but that
            # obviously doesn't work because of _oBaseFilter
            self._dCache['parent filter'] = \
                    PhysicalCardSetFilter(self._oCardSet.parent.name)
            aFilters = [self._dCache['parent filter'], oCurFilter]
            if self.iShowCardMode == THIS_SET_ONLY and \
                    oCardIter.count() < 200:
                # Restrict filter to the cards in this set, to save time
                # oCardIter.count() > 0, due to check in grouped_card_iter
                aAbsCardIds = set([IAbstractCard(x).id for x in oCardIter])
                aFilters.append(MultiSpecificCardIdFilter(aAbsCardIds))
            oParentFilter = FilterAndBox(aFilters)
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
        # pylint: disable-msg=E1101, E1103
        # Pyprotocols confuses pylint
        if self.iShowCardMode == ALL_CARDS:
            if self._dCache['all cards']:
                aExtraCards = self._dCache['all cards']
            else:
                oFullFilter = FilterAndBox([PhysicalCardFilter(),
                    oCurFilter])
                aExtraCards = list(oFullFilter.select(PhysicalCard).distinct())
                self._dCache['all cards'] = aExtraCards
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

    def _init_cache(self):
        """Setup the initial cache state"""
        # preserve this across calls to add_new_card
        self._dCache.setdefault('all cards', None)
        # We always refresh these on calls to add_new_card due so
        # filter checks are taken into account
        self._dCache['parent cards'] = {}
        self._dCache['parent abstract cards'] = {}
        self._dCache['child cards'] = {}
        self._dCache['child abstract cards'] = {}
        self._dCache['sibling cards'] = {}
        self._dCache['sibling abstract cards'] = {}
        self._dCache['child card sets'] = {}
        self._dCache['visible'] = {}
        self._dCache['filtered cards'] = None
        self._dCache['current cards'] = {}

    def grouped_card_iter(self, oCardIter):
        """Get the data that needs to fill the model, handling the different
           CardShow modes, the different counts, the filter, etc.

           Returns a iterator over the groupings, and a list of all the
           abstract cards in the card set considered.
           """
        # pylint: disable-msg=E1101, R0914, R0912, R0915
        # E1101: SQLObject + PyProtocols confuse pylint
        # R0914: We use lots of local variables for clarity
        # R0912: Lots of cases to consider, so several branches
        # R0915: Artificially subdividing this further would not be useful

        # Define iterable and grouping function based on cardclass
        aCards = []
        dAbsCards = {}
        dPhysCards = {}

        self._init_cache()

        if oCardIter.count() == 0 and self.iShowCardMode == THIS_SET_ONLY:
            # Short circuit the more expensive checks if we've got no cards
            # and can't influence this card set
            return (self.groupby([], lambda x: x[0]), [])

        oCurFilter = self.get_current_filter()
        if oCurFilter is None:
            oCurFilter = NullFilter()

        if self._bPhysicalFilter:
            oFullFilter = FilterAndBox([PhysicalCardFilter(), oCurFilter])
            # This does a batched query, due to SQLObject magic, so should be
            # fairly effecient.
            self._dCache['filtered cards'] = set(
                    oFullFilter.select(PhysicalCard).distinct())
            if self.iShowCardMode == ALL_CARDS:
                # Stomp on the cache, as we have a physical filter
                self._dCache['all cards'] = self._dCache['filtered cards']

        dChildCardCache = self._get_child_filters(oCurFilter)
        self._get_parent_list(oCurFilter, oCardIter)

        # Other card show modes
        aExtraCards = self._get_extra_cards(oCurFilter)

        for oPhysCard in aExtraCards:
            if not self.check_card_visible(oPhysCard):
                continue # Skip
            oAbsCard = oPhysCard.abstractCard
            self._init_abs(dAbsCards, oAbsCard)
            if self.iExtraLevelsMode == SHOW_EXPANSIONS or \
                    self.iExtraLevelsMode == EXP_AND_CARD_SETS:
                dAbsCards[oAbsCard].dExpansions.setdefault(
                        (self.get_expansion_name(oPhysCard.expansion),
                            oPhysCard), 0)
            dExpanInfo = dAbsCards[oAbsCard].dExpansions
            dChildInfo = dAbsCards[oAbsCard].dChildCardSets
            if not dChildInfo and self.iExtraLevelsMode in [
                    SHOW_CARD_SETS, EXP_AND_CARD_SETS, CARD_SETS_AND_EXP]:
                self.get_child_set_info(oAbsCard, dChildInfo, dExpanInfo,
                        dChildCardCache)

        for oCard in oCardIter:
            oPhysCard = IPhysicalCard(oCard)
            if not self.check_card_visible(oPhysCard):
                continue # Skip
            dPhysCards.setdefault(oPhysCard, 0)
            dPhysCards[oPhysCard] += 1
            sExpName = self.get_expansion_name(oPhysCard.expansion)
            oAbsCard = oPhysCard.abstractCard
            aCards.append(oPhysCard)
            if self._bPhysicalFilter:
                # We need to be able to give the correct list of physical
                # cards to the listeners if we remove these via _clear_iter
                # We can't get this from the card set, since that's already
                # changed, and we may not be able to extract it from the model
                # (depending on mode), so we just cache this
                self._dAbs2Phys.setdefault(oAbsCard, {})
                self._dAbs2Phys[oAbsCard].setdefault(oPhysCard, 0)
                self._dAbs2Phys[oAbsCard][oPhysCard] += 1
            self._init_abs(dAbsCards, oAbsCard)
            dAbsCards[oAbsCard].iCount += 1
            dChildInfo = dAbsCards[oAbsCard].dChildCardSets
            dExpanInfo = dAbsCards[oAbsCard].dExpansions
            if self.iExtraLevelsMode == SHOW_EXPANSIONS or \
                    self.iExtraLevelsMode == EXP_AND_CARD_SETS:
                dExpanInfo.setdefault((sExpName, oPhysCard), 0)
                dExpanInfo[(sExpName, oPhysCard)] += 1
            if self.iExtraLevelsMode in [SHOW_CARD_SETS, EXP_AND_CARD_SETS,
                    CARD_SETS_AND_EXP] and not dChildInfo:
                # Don't re-filter for repeated abstract cards
                self.get_child_set_info(oAbsCard, dChildInfo, dExpanInfo,
                        dChildCardCache)
            if self.iExtraLevelsMode == EXP_AND_CARD_SETS:
                dChildInfo.setdefault(sExpName, {})

        self._add_parent_info(dAbsCards, dPhysCards)

        aAbsCards = list(dAbsCards.iteritems())

        # expire caches
        self._dCache['filtered cards'] = None
        self._dCache['visible'] = {}

        # Iterate over groups
        return (self.groupby(aAbsCards, lambda x: x[0]), aCards)

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
                    self.iExtraLevelsMode == CARD_SETS_AND_EXP:
                iChildCnt = len(aChildCards)
                if iChildCnt > 0 or self.bEditable:
                    # We treat card sets like expansion, showing all of them
                    # when editable.
                    dChildInfo.setdefault(sCardSetName, iChildCnt)
                    if self.iExtraLevelsMode == CARD_SETS_AND_EXP:
                        dExpanInfo.setdefault(sCardSetName, {})
                        self._init_expansions(dExpanInfo[sCardSetName],
                                oAbsCard)
                        for oThisPhysCard in aChildCards:
                            sExpName = self.get_expansion_name(
                                    oThisPhysCard.expansion)
                            dExpanInfo[sCardSetName].setdefault((sExpName,
                                oThisPhysCard), 0)
                            dExpanInfo[sCardSetName][(sExpName,
                                oThisPhysCard)] += 1
            elif self.iExtraLevelsMode == EXP_AND_CARD_SETS:
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
                    dChildInfo[sExpName].setdefault(
                        sCardSetName, 0)
                    dChildInfo[sExpName][sCardSetName] += 1

    def _get_sibling_cards(self):
        """Get the list of cards in sibling card sets"""
        # pylint: disable-msg=E1101, E1103
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

    def _update_parent_info(self, oSetInfo, dPhysCards):
        """Update the parent counts with info from this set"""
        # pylint: disable-msg=E1103, E1101
        # pyprotocols confusion
        dParentExp = oSetInfo.dParentExpansions
        if self.iExtraLevelsMode in [EXP_AND_CARD_SETS, SHOW_EXPANSIONS]:
            # Already looked this up
            for tKey, iCnt in oSetInfo.dExpansions.iteritems():
                sExpansion, _oPhysCard = tKey
                dParentExp[sExpansion] = -iCnt
        elif self.iExtraLevelsMode == CARD_SETS_AND_EXP and \
                oSetInfo.iCount > 0:
            # We have some cards, but we don't know which, so we
            # need to get this from the database
            for dInfo in oSetInfo.dExpansions.itervalues():
                for sExpansion, oPhysCard in dInfo:
                    if not sExpansion in dParentExp:
                        # Query the database
                        if oPhysCard in dPhysCards:
                            dParentExp[sExpansion] = -dPhysCards[oPhysCard]

    def _add_parent_info(self, dAbsCards, dPhysCards):
        """Add the parent count info into the mix"""
        # pylint: disable-msg=E1101, E1103
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
                self._update_parent_info(oRow, dPhysCards)

        for oPhysCard in self._dCache['parent cards']:
            # pylint: disable-msg=E1101
            # Pyprotocols confuses pylint
            oAbsCard = oPhysCard.abstractCard
            if oAbsCard in dAbsCards and self.check_card_visible(oPhysCard):
                sExpansion = self.get_expansion_name(oPhysCard.expansion)
                dParentExp = dAbsCards[oAbsCard].dParentExpansions
                dParentExp.setdefault(sExpansion, 0)
                if self.iParentCountMode != IGNORE_PARENT:
                    iNum = self._dCache['parent cards'][oPhysCard]
                    dAbsCards[oAbsCard].iParentCount += iNum
                    dParentExp[sExpansion] += iNum

    def _remove_sub_iters(self, oAbsCard):
        """Remove the children rows for the card entry sCardName"""
        if not oAbsCard in self._dAbsSecondLevel2Iter:
            # Nothing to clean up (not showing second level, etc.)
            return
        aSecondLevelKeys = self._dAbsSecondLevel2Iter[oAbsCard].keys()
        # We remove values in the loop, so we need this copy
        for sValue in aSecondLevelKeys:
            self._remove_second_level(oAbsCard, sValue)

    def _remove_second_level(self, oAbsCard, sValue):
        """Remove a second level entry and everything below it"""
        if not oAbsCard in self._dAbsSecondLevel2Iter or \
                not sValue in self._dAbsSecondLevel2Iter[oAbsCard]:
            return # Nothing to do
        tSLKey = (oAbsCard, sValue)
        if tSLKey in self._dAbs2nd3rdLevel2Iter:
            for sName in self._dAbs2nd3rdLevel2Iter[tSLKey]:
                for oIter in self._dAbs2nd3rdLevel2Iter[tSLKey][sName]:
                    self.remove(oIter)
            del self._dAbs2nd3rdLevel2Iter[tSLKey]
        for oIter in self._dAbsSecondLevel2Iter[oAbsCard][sValue]:
            self.remove(oIter)
        del self._dAbsSecondLevel2Iter[oAbsCard][sValue]
        if not self._dAbsSecondLevel2Iter[oAbsCard]:
            del self._dAbsSecondLevel2Iter[oAbsCard]

    def _get_parent_count(self, oPhysCard, iThisSetCnt=None):
        """Get the correct parent count for the given card"""
        # pylint: disable-msg=E1101, E1103
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
            oSectionIter = self.prepend(None, (sGroup, 0, 0, False, False,
                aTexts, aIcons, BLACK, None, None))
        else:
            oSectionIter = self.prepend(None, (sGroup, 0, 0, False, False, [],
                [], BLACK, None, None))
        return oSectionIter

    def add_new_card(self, oPhysCard):
        # pylint: disable-msg=R0914
        # we use many local variables for clarity
        """If the card oPhysCard is not in the current list (i.e. is not in
           the card set or is filtered out) see if it should be visible. If it
           should be visible, add it to the appropriate groups.
           """
        oFilter = self.get_current_filter()
        if not oFilter:
            oFilter = NullFilter()
        oAbsCard = IAbstractCard(oPhysCard)
        # pylint: disable-msg=E1101
        # PyProtocols confuses pylint
        if self._bPhysicalFilter:
            # Because we rely on this fixing any entries we removed
            # in card_changed, we need to select more cards than in
            # the non-physical case.
            # check_card_visible will fix the extra cards we might select
            oCardFilter = FilterAndBox([oFilter,
                SpecificCardIdFilter(oAbsCard.id)])
        else:
            oCardFilter = FilterAndBox([oFilter,
                SpecificPhysCardIdFilter(oPhysCard.id)])

        oCardIter = self.get_card_iterator(oCardFilter)

        iCnt = 0 # Since we'll test this later, and may skip assigning it
        oGroupedIter, _aCards = self.grouped_card_iter(oCardIter)
        bPostfix = self._oConfig.get_postfix_the_display()

        # Iterate over groups
        for sGroup, oGroupIter in oGroupedIter:
            # Check for null group
            sGroup = self._fix_group_name(sGroup)

            # Find Group Section
            if sGroup in self._dGroupName2Iter:
                oSectionIter = self._dGroupName2Iter[sGroup]
                iGrpCnt = self.get_value(oSectionIter, 1)
                iParGrpCnt = self.get_value(oSectionIter, 2)
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
                iParCnt = oRow.get_parent_count()
                iGrpCnt += iCnt
                iParGrpCnt += iParCnt
                bIncCard, bDecCard = self.check_inc_dec(iCnt)
                oChildIter = self.prepend(oSectionIter)
                # We don't do the full _set_display_name for speed here.
                sName = oCard.name
                if bPostfix:
                    sName = canonical_to_csv(sName)
                self.set(oChildIter, 0, sName,
                        1, iCnt, 2, iParCnt, 3, bIncCard, 4, bDecCard,
                        8, oCard, 9, oRow.oPhysCard,
                        )
                self.set_par_count_colour(oChildIter, iParCnt, iCnt)
                self._dAbs2Iter.setdefault(oCard, []).append(oChildIter)
                # Handle as for loading
                self._add_children(oChildIter, oRow)

            # Update Group Section
            self.set(oSectionIter, 1, iGrpCnt, 2, iParGrpCnt)
            self.set_par_count_colour(oSectionIter, iParGrpCnt, iGrpCnt)

        if self.oEmptyIter and self._dAbs2Iter:
            # remove previous empty note
            self.remove(self.oEmptyIter)
            self.oEmptyIter = None

        # Notify Listeners
        if iCnt:
            for oListener in self.dListeners:
                oListener.add_new_card(oPhysCard, iCnt)

    def update_to_new_db(self, sSetName):
        """Update internal card set to the new DB."""
        self._oCardSet = IPhysicalCardSet(sSetName)
        self._oBaseFilter = PhysicalCardSetFilter(sSetName)

    def changes_with_parent(self):
        """Utility function. Returns true if the parent card set influences
           the currently visible set of cards."""
        # pylint: disable-msg=E1101, E1103
        # PyProtocols confuse pylint
        return (self.iParentCountMode != IGNORE_PARENT or \
                self.iShowCardMode == PARENT_CARDS) and \
                self._oCardSet.parent is not None

    def changes_with_children(self):
        """Utility function. Returns true if changes to the child card sets
           influence the display."""
        return self.iShowCardMode == CHILD_CARDS or self.iExtraLevelsMode \
                in [SHOW_CARD_SETS, EXP_AND_CARD_SETS, CARD_SETS_AND_EXP]

    def changes_with_siblings(self):
        """Utility function. Returns true if changes to the sibling card sets
           influence the display."""
        # pylint: disable-msg=E1101, E1103
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

    def _needs_update(self, oAbsCard, oPhysCard):
        """Check if we need to update for this card.

           Only called in the PhysicalFilter case, where we can't
           decide based on card set properties."""
        bVisible = self.check_card_visible(oPhysCard)
        bPresent = True
        if oAbsCard not in self._dAbs2Iter:
            bPresent = False
        if not bVisible and not bPresent:
            # No need to change anything in this case
            return False
        return True

    def card_changed(self, oCardSet, oPhysCard, iChg):
        """Listen on card changes.

           We listen to the special signal, so we can hook in after the
           database has been updated. This simplifies the update logic
           as we can query the database and obtain accurate results.
           Does rely on everyone calling send_changed_signal.
           """
        # pylint: disable-msg=E1101, R0912, E1103
        # E1101, E1103 - Pyprotocols confuses pylint
        # R0912 - need to consider several cases, so lots of branches
        oAbsCard = IAbstractCard(oPhysCard)
        if self._bPhysicalFilter:
            # If we have a card count filter, any change can affect us,
            # so we always consider these cases.
            if not self._needs_update(oAbsCard, oPhysCard):
                self._dCache['visible'] = {}
                return
            dStates = {}
            if self._oController and oAbsCard in self._dAbs2Iter:
                dStates = self._oController.save_iter_state(
                        self._dAbs2Iter[oAbsCard])
            # clear existing info about the card
            self._clear_card_iter(oAbsCard)
            # We hand off to add_new_card to do the right thing
            self.add_new_card(oPhysCard)
            if self._oController and oAbsCard in self._dAbs2Iter:
                self._oController.restore_iter_state(self._dAbs2Iter[oAbsCard],
                        dStates)
        elif oCardSet.id == self._oCardSet.id:
            # Changing a card from this card set
            if self._oCardSet.inuse:
                self._update_cache(oPhysCard, iChg, 'sibling')
            if oAbsCard in self._dAbs2Iter:
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
            if oAbsCard in self._dAbs2Iter:
                self.alter_child_count(oPhysCard, oCardSet.name, iChg)
            elif iChg > 0 and oPhysCard not in self._dCache['child cards']:
                self.add_new_card(oPhysCard)
            self._clean_cache(oPhysCard, 'child')
            self._clean_child_set_cache(oPhysCard, oCardSet.name)
        elif self.changes_with_parent() and oCardSet.id == \
                self._oCardSet.parent.id:
            # Changing parent card set
            self._update_cache(oPhysCard, iChg, 'parent')
            if oAbsCard in self._dAbs2Iter:
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
            if oAbsCard in self._dAbs2Iter:
                # This is only called when using MINUS_SETS_IN_USE,
                # So this changes the available pool of parent cards (by -iChg)
                # There's no possiblity of this adding or deleting a card from
                # the model
                self.alter_parent_count(oPhysCard, -iChg, False)
            self._clean_cache(oPhysCard, 'sibling')
        # Doesn't affect us, so ignore
        # expire short-lived cache
        self._dCache['visible'] = {}

    def check_card_visible(self, oPhysCard):
        """Returns true if oPhysCard should be shown.

           In addition to the listener check for the plugin, we add
           a extra check on the filter. This is to ensure we don't display
           incorrect results when filtering on physical card properties
           and the card set changes."""
        # This cache is short-lived - it's intended to stop repeated calls to
        # the plugins & filter for the same card during an operation
        if oPhysCard in self._dCache['visible']:
            return self._dCache['visible'][oPhysCard]
        bResult = True
        if self._bPhysicalFilter:
            if self._dCache['filtered cards']:
                # During grouped_iter, this is defined
                bResult = oPhysCard in self._dCache['filtered cards']
            else:
                # We don't use the base filter, to avoid complex logic for the
                # different display modes.
                oFilter = self.get_current_filter()
                oFullFilter = FilterAndBox([PhysicalCardFilter(),
                    SpecificPhysCardIdFilter(oPhysCard.id), oFilter])
                bResult = \
                        oFullFilter.select(PhysicalCard).distinct().count() > 0
        if bResult:
            # Check the listeners
            for oListener in self.dListeners:
                bResult = bResult and oListener.check_card_visible(oPhysCard)
                if not bResult:
                    break # Failed, so bail on loop
        self._dCache['visible'][oPhysCard] = bResult
        return bResult

    def _check_filter(self):
        """Check if the filter is a physical card only filter"""
        oCurFilter = self.get_current_filter()
        if oCurFilter:
            return not ('AbstractCard' in oCurFilter.types)
        return False

    def _card_count_changes_parent(self):
        """Check if a change in the card count changes the parent"""
        # pylint: disable-msg=E1101, E1103
        # pyprotocols confuses pylint
        return (self.iParentCountMode == MINUS_THIS_SET or
                (self.iParentCountMode == MINUS_SETS_IN_USE and
                    self._oCardSet.inuse)) and self._oCardSet.parent

    def _update_parent_count(self, oIter, iChg, iParChg):
        """Update the card and parent counts"""
        iParCnt = self.get_value(oIter, 2)
        if self.iParentCountMode != IGNORE_PARENT:
            iParCnt += iParChg
        if self._card_count_changes_parent():
            iParCnt -= iChg
        return iParCnt

    def _check_child_counts(self, oIter):
        """Loop over a level of the model, checking for non-zero counts"""
        while oIter:
            if self.get_value(oIter, 1) > 0:
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
        # pylint: disable-msg=E1101, E1103
        # E1101, E1103: PyProtocols confuses pylint
        iCnt = self.get_value(oIter, 1)
        if not self.check_card_visible(oPhysCard):
            # Card doesn't match the current filter & plugins, so it must
            # vanish
            return False
        if iCnt > 0 or self.bEditable:
            # When editing, we don't delete 0 entries unless the card vanishes
            return True
        iDepth = self.iter_depth(oIter)
        if iDepth == 2 and self.iExtraLevelsMode in [SHOW_EXPANSIONS,
                EXP_AND_CARD_SETS] and self.iShowCardMode == ALL_CARDS:
            # We don't delete expansion entries in this case
            return True
        elif iDepth == 3 and self.iExtraLevelsMode in [EXP_AND_CARD_SETS,
                CARD_SETS_AND_EXP]:
            # Since we're not editable here, we always remove these
            return False
        iParCnt = self.get_value(oIter, 2)
        bResult = False
        if self.iExtraLevelsMode == EXP_AND_CARD_SETS and \
                self.iShowCardMode == CHILD_CARDS and \
                self.iter_n_children(oIter) > 0:
            # iCnt is 0, and we're not editable, so we only show this
            # row if there are non-zero entries below us
            oChildIter = self.iter_children(oIter)
            if self._check_child_counts(oChildIter):
                bResult = True
        elif self.iShowCardMode == PARENT_CARDS and \
                self.iParentCountMode in [PARENT_COUNT, MINUS_THIS_SET] and \
                self.iExtraLevelsMode in [SHOW_EXPANSIONS, EXP_AND_CARD_SETS] \
                and iDepth == 2 and iParCnt > 0:
            # cards in the parent set, obviously
            bResult = True
        elif self.iShowCardMode == PARENT_CARDS and self._oCardSet.parent \
                and self.iExtraLevelsMode in [SHOW_EXPANSIONS,
                        EXP_AND_CARD_SETS] and iDepth == 2:
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
        # pylint: disable-msg=E1101, E1103
        # Pyprotocols confuses pylint
        iCnt = self.get_value(oIter, 1)
        if self.iShowCardMode == ALL_CARDS or iCnt > 0:
            # We clearly don't remove entries here
            return True
        iParCnt = self.get_value(oIter, 2)
        bResult = False
        if self.iShowCardMode == PARENT_CARDS and iParCnt > 0 and \
                self.iParentCountMode in [PARENT_COUNT, MINUS_THIS_SET]:
            bResult = True
        elif self.iShowCardMode == PARENT_CARDS and self._oCardSet.parent:
            # Check the parent card cache
            oAbsCard = self.get_abstract_card_from_iter(oIter)
            if oAbsCard.id in self._dCache['parent abstract cards']:
                bResult = self._dCache['parent abstract cards'][
                        oAbsCard.id] > 0
        elif self.iShowCardMode == CHILD_CARDS:
            if self.iExtraLevelsMode in [SHOW_CARD_SETS, CARD_SETS_AND_EXP]:
                # Check if any top level child iters have non-zero counts
                oChildIter = self.iter_children(oIter)
                bResult = self._check_child_counts(oChildIter)
            elif self.iExtraLevelsMode == EXP_AND_CARD_SETS:
                # Check third level children
                oChildIter = self.iter_children(oIter)
                while oChildIter:
                    oGrandChild = self.iter_children(oChildIter)
                    if self._check_child_counts(oGrandChild):
                        return True
                    oChildIter = self.iter_next(oChildIter)
            elif self._dCache['child filters']:
                # Actually check the database
                oAbsCard = self.get_abstract_card_from_iter(oIter)
                if oAbsCard.id in self._dCache['child abstract cards']:
                    bResult = self._dCache['child abstract cards'][
                            oAbsCard.id] > 0
        return bResult

    def check_group_iter_stays(self, oIter):
        """Check if we need to remove the top-level item"""
        # Conditions for removal vary with the cards shown
        bResult = False
        if self.iShowCardMode == ALL_CARDS:
            # We don't remove group entries unless we have no children
            # (due to physical card filters)
            bResult = True
            if self._bPhysicalFilter:
                bResult = self.iter_n_children(oIter) > 0
            return bResult
        iCnt = self.get_value(oIter, 1)
        if iCnt > 0:
            # Count is non-zero, so we stay
            return True
        iParCnt = self.get_value(oIter, 2)
        if self.iShowCardMode == PARENT_CARDS and iParCnt > 0:
            # Obviously parent cards present
            bResult = True
        elif self.iShowCardMode == PARENT_CARDS and \
                self.iParentCountMode not in [PARENT_COUNT, MINUS_THIS_SET]:
            bResult = self._check_child_card_entries(oIter)
        elif self.iShowCardMode == CHILD_CARDS:
            bResult = self._check_child_card_entries(oIter)
        return bResult

    def _update_3rd_level_card_sets(self, oPhysCard, iChg, iParChg,
            bCheckAddRemove):
        """Update the third level for EXP_AND_CARD_SETS"""
        oAbsCard = oPhysCard.abstractCard
        sExpName = self.get_expansion_name(oPhysCard.expansion)
        tExpKey = (oAbsCard, sExpName)
        if tExpKey in self._dAbs2nd3rdLevel2Iter:
            bRemoveChild = False
            # Update the 3rd level
            iParCnt = None
            for aIterList in self._dAbs2nd3rdLevel2Iter[tExpKey].itervalues():
                for oSubIter in aIterList:
                    iCnt = self.get_value(oSubIter, 1)
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
                del self._dAbs2nd3rdLevel2Iter[tExpKey]

    def _add_3rd_level_card_sets(self, oPhysCard, iParCnt):
        """Add 3rd level entries for the EXP_AND_CARD_SETS mode"""
        oAbsCard = oPhysCard.abstractCard
        sExpName = self.get_expansion_name(oPhysCard.expansion)
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
                for oIter in self._dAbsSecondLevel2Iter[oAbsCard][sExpName]:
                    self._add_extra_level(oIter, sCardSet, (iCnt, iParCnt,
                        oPhysCard, bIncCard, bDecCard), (3, (oAbsCard,
                            sExpName)))

    def _update_2nd_level_expansions(self, oPhysCard, iChg, iParChg,
            bCheckAddRemove=True):
        """Update the expansion entries and the children for a changed entry
           for the SHOW_EXPANSIONS and EXP_AND_CARD_SETS modes"""
        # We need to update the expansion count for this card
        # pylint: disable-msg=E1101, E1103
        # pyprotocols confuses pylint
        oAbsCard = oPhysCard.abstractCard
        sExpName = self.get_expansion_name(oPhysCard.expansion)
        bRemove = False
        if oAbsCard in self._dAbsSecondLevel2Iter and \
                sExpName in self._dAbsSecondLevel2Iter[oAbsCard]:
            iCnt = None
            for oChildIter in self._dAbsSecondLevel2Iter[oAbsCard][sExpName]:
                if not iCnt:
                    iCnt = self.get_value(oChildIter, 1) + iChg
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
            for oIter in self._dAbs2Iter[oAbsCard]:
                self._add_extra_level(oIter, sExpName, (iChg, iParCnt,
                    oPhysCard, bIncCard, bDecCard), (2, oAbsCard))
                if self.iExtraLevelsMode == EXP_AND_CARD_SETS \
                        and self.iShowCardMode not in [ALL_CARDS, CHILD_CARDS]:
                    self._add_3rd_level_card_sets(oPhysCard, iParCnt)
        if bRemove:
            self._remove_second_level(oAbsCard, sExpName)

    def _update_2nd3rd_level_par_cnt(self, oPhysCard, iChg):
        """Update the parent counts for CARD_SETS and CARD_SETS_AND_EXP
           modes."""
        oAbsCard = oPhysCard.abstractCard
        # Loop over all the children, and modify the count
        # if needed
        if oAbsCard in self._dAbsSecondLevel2Iter:
            sExpName = self.get_expansion_name(oPhysCard.expansion)
            for sValue in self._dAbsSecondLevel2Iter[oAbsCard]:
                for oChildIter in self._dAbsSecondLevel2Iter[oAbsCard][
                        sValue]:
                    iParCnt = self.get_value(oChildIter, 2) + iChg
                    iCnt = self.get_value(oChildIter, 1)
                    self._update_entry(oChildIter, iCnt, iParCnt)
                tExpKey = (oAbsCard, sValue)
                if tExpKey in self._dAbs2nd3rdLevel2Iter:
                    for sName in self._dAbs2nd3rdLevel2Iter[tExpKey]:
                        if self.iExtraLevelsMode == CARD_SETS_AND_EXP \
                                and sName != sExpName:
                            continue
                        for oSubIter in self._dAbs2nd3rdLevel2Iter[tExpKey][
                                sName]:
                            iParCnt = self.get_value(oSubIter, 2) + iChg
                            iCnt = self.get_value(oSubIter, 1)
                            self._update_entry(oSubIter, iCnt, iParCnt)

    def _update_3rd_level_expansions(self, oPhysCard):
        """Add expansion level items for CARD_SETS_AND_EXP mode if
           needed."""
        oAbsCard = oPhysCard.abstractCard
        sExpName = self.get_expansion_name(oPhysCard.expansion)
        iParCnt = None
        for sCardSetName in self._dAbsSecondLevel2Iter[oAbsCard]:
            tCSKey = (oAbsCard, sCardSetName)
            if not tCSKey in self._dAbs2nd3rdLevel2Iter or not \
                    sExpName in self._dAbs2nd3rdLevel2Iter[tCSKey] and \
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
                    for oChildIter in self._dAbsSecondLevel2Iter[oAbsCard][
                            sCardSetName]:
                        self._add_extra_level(oChildIter, sExpName, (iCnt,
                            iParCnt, oPhysCard, bIncCard, bDecCard), (3,
                                (oAbsCard, sCardSetName)))

    def _clear_card_iter(self, oAbsCard):
        """Remove a card-level iter and update everything accordingly"""
        if oAbsCard not in self._dAbs2Iter:
            return # Nothing to do
        for oIter in self._dAbs2Iter[oAbsCard]:
            oGrpIter = self.iter_parent(oIter)
            iCnt = self.get_value(oIter, 1)
            iParCnt = self.get_value(oIter, 2)
            iGrpCnt = self.get_value(oGrpIter, 1) - iCnt
            iParGrpCnt = self.get_value(oGrpIter, 2) - iParCnt
            self._remove_sub_iters(oAbsCard)
            self.remove(oIter)

            self.set(oGrpIter, 1, iGrpCnt, 2, iParGrpCnt)

            if not self.check_group_iter_stays(oGrpIter):
                sGroupName = self.get_value(oGrpIter, 0)
                del self._dGroupName2Iter[sGroupName]
                self.remove(oGrpIter)
            else:
                self.set_par_count_colour(oGrpIter, iParGrpCnt, iGrpCnt)

        del self._dAbs2Iter[oAbsCard]

        self._check_if_empty()

        if oAbsCard not in self._dAbs2Phys:
            # The change didn't affect a card in the card
            # set, so we don't need to call the listeners
            return
        # Update the listeners
        for oPhysCard, iCnt in self._dAbs2Phys[oAbsCard].iteritems():
            for oListener in self.dListeners:
                oListener.alter_card_count(oPhysCard, -iCnt)
        del self._dAbs2Phys[oAbsCard]

    def alter_card_count(self, oPhysCard, iChg):
        """Alter the card count of a card which is in the current list
           (i.e. in the card set and not filtered out) by iChg."""
        # pylint: disable-msg=E1101, R0912, E1103
        # E1101, E1103: PyProtocols confuses pylint here
        # R0912: Several cases to consider, so several branches
        oAbsCard = IAbstractCard(oPhysCard)
        bRemove = False
        bChecked = False # flag to avoid repeated work
        for oIter in self._dAbs2Iter[oAbsCard]:
            oGrpIter = self.iter_parent(oIter)
            iCnt = self.get_value(oIter, 1) + iChg
            iGrpCnt = self.get_value(oGrpIter, 1) + iChg
            iParGrpCnt = self.get_value(oGrpIter, 2)
            self.set(oIter, 1, iCnt)
            iParCnt = self.get_value(oIter, 2)
            if self._card_count_changes_parent():
                iParCnt -= iChg
                iParGrpCnt -= iChg

            if not bChecked and not self.check_card_iter_stays(oIter):
                bRemove = True
            bChecked = True

            if bRemove:
                self._remove_sub_iters(oAbsCard)
                self.remove(oIter)
                iParGrpCnt -= iParCnt
            else:
                self._update_entry(oIter, iCnt, iParCnt)

            self.set(oGrpIter, 1, iGrpCnt, 2, iParGrpCnt)

            self.set_par_count_colour(oGrpIter, iParGrpCnt, iGrpCnt)
            if not self.check_group_iter_stays(oGrpIter):
                sGroupName = self.get_value(oGrpIter, 0)
                del self._dGroupName2Iter[sGroupName]
                self.remove(oGrpIter)

        if bRemove:
            del self._dAbs2Iter[oAbsCard]
        elif self.iExtraLevelsMode in [SHOW_EXPANSIONS, EXP_AND_CARD_SETS]:
            self._update_2nd_level_expansions(oPhysCard, iChg, 0)
        elif self.iExtraLevelsMode in [SHOW_CARD_SETS, CARD_SETS_AND_EXP] and \
                oAbsCard in self._dAbsSecondLevel2Iter:
            if self._card_count_changes_parent():
                # Need to update the parent counts for the child entry
                self._update_2nd3rd_level_par_cnt(oPhysCard, -iChg)
            if self.iExtraLevelsMode == CARD_SETS_AND_EXP and iChg > 0:
                # We may need to add a expansion entry to below this card set,
                # so we check
                self._update_3rd_level_expansions(oPhysCard)

        self._check_if_empty()

        # Notify Listeners
        for oListener in self.dListeners:
            oListener.alter_card_count(oPhysCard, iChg)

    def alter_parent_count(self, oPhysCard, iChg, bCheckAddRemove=True):
        """Alter the parent count by iChg

           if bCheckAddRemove is False, we don't check whether anything should
           be removed from the model. This is used for sibling card set
           changes.
           """
        bRemove = False
        bChecked = False # flag so we don't revist decisions
        if not bCheckAddRemove:
            bChecked = True # skip check
        oAbsCard = oPhysCard.abstractCard
        for oIter in self._dAbs2Iter[oAbsCard]:
            oGrpIter = self.iter_parent(oIter)
            iParGrpCnt = self.get_value(oGrpIter, 2) + iChg
            iParCnt = self.get_value(oIter, 2) + iChg
            if self.iParentCountMode == IGNORE_PARENT:
                # We touch nothing in this case
                iParGrpCnt = 0
                iParCnt = 0
            iGrpCnt = self.get_value(oGrpIter, 1)
            iCnt = self.get_value(oIter, 1)
            self._update_entry(oIter, iCnt, iParCnt)
            self.set(oGrpIter, 2, iParGrpCnt)
            self.set_par_count_colour(oGrpIter, iParGrpCnt, iGrpCnt)
            if not bChecked and not self.check_card_iter_stays(oIter):
                bRemove = True
            bChecked = True
            if bRemove:
                self._remove_sub_iters(oAbsCard)
                iParCnt = self.get_value(oIter, 2)
                iParGrpCnt = self.get_value(oGrpIter, 2) - iParCnt
                iGrpCnt = self.get_value(oGrpIter, 1)
                self.remove(oIter)
                # Fix the group counts
                self.set(oGrpIter, 2, iParGrpCnt)
                self.set_par_count_colour(oGrpIter, iParGrpCnt, iGrpCnt)
                if not self.check_group_iter_stays(oGrpIter):
                    sGroupName = self.get_value(oGrpIter, 0)
                    del self._dGroupName2Iter[sGroupName]
                    self.remove(oGrpIter)

        if bRemove:
            del self._dAbs2Iter[oAbsCard]
        elif self.iExtraLevelsMode != NO_SECOND_LEVEL:
            if self.iExtraLevelsMode in [SHOW_EXPANSIONS, EXP_AND_CARD_SETS]:
                self._update_2nd_level_expansions(oPhysCard, 0, iChg,
                        bCheckAddRemove)
            elif self.iParentCountMode != IGNORE_PARENT:
                self._update_2nd3rd_level_par_cnt(oPhysCard, iChg)

        self._check_if_empty()

    def alter_child_count_card_sets(self, oPhysCard, sCardSetName, iChg):
        """Handle the alter child card case when showing child sets as the
           second level without expansions."""
        # pylint: disable-msg = E1101, E1103
        # PyProtocols confuses pylint
        oAbsCard = oPhysCard.abstractCard
        if oAbsCard in self._dAbsSecondLevel2Iter and \
                sCardSetName in self._dAbsSecondLevel2Iter[oAbsCard]:
            # Alter the count
            bRemove = False
            for oIter in self._dAbsSecondLevel2Iter[oAbsCard][sCardSetName]:
                iCnt = self.get_value(oIter, 1) + iChg
                # We can't change parent counts, so no need to
                # consider them
                self.set(oIter, 1, iCnt)
                if bRemove or not \
                        self.check_child_iter_stays(oIter, oPhysCard):
                    bRemove = True
            if bRemove:
                self._remove_second_level(oAbsCard, sCardSetName)
        elif iChg > 0:
            # Need to add an entry
            iCnt = 1
            bIncCard, bDecCard = self.check_inc_dec(iCnt)
            for oIter in self._dAbs2Iter[oAbsCard]:
                iParCnt = self.get_value(oIter, 2)
                self._add_extra_level(oIter, sCardSetName,
                        (iCnt, iParCnt, oPhysCard, bIncCard, bDecCard),
                        (2, oAbsCard))

    def _add_child_3rd_level_exp_entry(self, oPhysCard, sCardSetName,
            tExpKey):
        """Add the third level expansion entry when dealing with adding cards
           to a child card set"""
        # pylint: disable-msg = E1101, E1103
        # PyProtocols confuses pylint
        iCnt = 1
        oAbsCard, sExpName = tExpKey
        iThisCSCnt = self.get_card_iterator(SpecificPhysCardIdFilter(
            oPhysCard.id)).count()
        iParCnt = self._get_parent_count(oPhysCard, iThisCSCnt)
        bIncCard, bDecCard = self.check_inc_dec(iCnt)
        for oIter in self._dAbsSecondLevel2Iter[oAbsCard][sCardSetName]:
            self._add_extra_level(oIter, sExpName, (iCnt, iParCnt, oPhysCard,
                bIncCard, bDecCard), (3, (oAbsCard, sCardSetName)))

    def alter_child_count(self, oPhysCard, sCardSetName, iChg):
        """Adjust the count for the card in the given card set by iChg"""
        # Child card set number changes can't change the values displayed
        # for card level items, but they can cause card level items to vanish
        # So we don't need to loop over the card level, merely the sub-levels,
        # but we do need to check if the card is removed at the end
        # pylint: disable-msg = E1101, E1103
        # PyProtocols confuses pylint
        oAbsCard = oPhysCard.abstractCard
        if (self.iExtraLevelsMode == SHOW_EXPANSIONS and
                self.iShowCardMode == CHILD_CARDS) \
                        or self.iExtraLevelsMode == EXP_AND_CARD_SETS:
            self.alter_child_count_expansions(oPhysCard, sCardSetName, iChg)
        elif self.iExtraLevelsMode == SHOW_CARD_SETS:
            self.alter_child_count_card_sets(oPhysCard, sCardSetName, iChg)
        elif self.iExtraLevelsMode == CARD_SETS_AND_EXP:
            self.alter_child_cnt_cs_exps(oPhysCard, sCardSetName,
                    iChg)
        # Check if we need to cleanup any card entries
        bRemove = False
        if len(self._dAbs2Iter[oAbsCard]) > 0 and iChg < 0:
            # Test if we need to remove entries
            oIter = self._dAbs2Iter[oAbsCard][0]
            iParCnt = self.get_value(oIter, 2)
            bRemove = not self.check_card_iter_stays(oIter)
        if bRemove:
            # Remove the card entry
            for oIter in self._dAbs2Iter[oAbsCard]:
                oGrpIter = self.iter_parent(oIter)
                iGrpCnt = self.get_value(oGrpIter, 1)
                iParGrpCnt = self.get_value(oGrpIter, 2) - iParCnt
                self._remove_sub_iters(oAbsCard)
                self.remove(oIter)
                self.set(oGrpIter, 2, iParGrpCnt)
                self.set_par_count_colour(oGrpIter, iParGrpCnt, iGrpCnt)
                if not self.check_group_iter_stays(oGrpIter):
                    sGroupName = self.get_value(oGrpIter, 0)
                    del self._dGroupName2Iter[sGroupName]
                    self.remove(oGrpIter)
            del self._dAbs2Iter[oAbsCard]
        self._check_if_empty()

    def _inc_exp_child_set_count(self, tExpKey, sCardSetName):
        """Increment the count (from alter_child_child_count_expansions)
           when showing expansion & child card sets"""
        oAbsCard, sExpName = tExpKey
        if tExpKey in self._dAbs2nd3rdLevel2Iter and sCardSetName in \
                self._dAbs2nd3rdLevel2Iter[tExpKey]:
            # Update counts
            for oIter in self._dAbs2nd3rdLevel2Iter[tExpKey][sCardSetName]:
                iCnt = self.get_value(oIter, 1) + 1
                self.set(oIter, 1, iCnt)
        else:
            # We need to add 2nd3rd level entries
            # Since we're adding this entry, it must be 1
            iCnt = 1
            for oIter in self._dAbsSecondLevel2Iter[oAbsCard][sExpName]:
                iParCnt = self.get_value(oIter, 2)
                oPhysCard = self.get_physical_card_from_iter(oIter)
                bIncCard, bDecCard = self.check_inc_dec(iCnt)
                self._add_extra_level(oIter, sCardSetName, (iCnt, iParCnt,
                    oPhysCard, bIncCard, bDecCard), (3, (oAbsCard, sExpName)))

    def alter_child_count_expansions(self, oPhysCard, sCardSetName, iChg):
        """Handle the alter child card case when showing expansions as the
           second level."""
        # pylint: disable-msg = E1101, E1103
        # PyProtocols confuses pylint
        oAbsCard = oPhysCard.abstractCard
        sExpName = self.get_expansion_name(oPhysCard.expansion)
        tExpKey = (oAbsCard, sExpName)
        # Check if we need to add or remove an expansion entry
        if iChg > 0:
            if (not oAbsCard in self._dAbsSecondLevel2Iter or not
                    sExpName in self._dAbsSecondLevel2Iter[oAbsCard]) \
                            and self.iShowCardMode == CHILD_CARDS:
                iCnt = 0 # 2nd level is expansions, so count is 0
                iParCnt = self._get_parent_count(oPhysCard, iCnt)
                bIncCard, bDecCard = self.check_inc_dec(iCnt)
                for oIter in self._dAbs2Iter[oAbsCard]:
                    self._add_extra_level(oIter, sExpName,
                            (iCnt, iParCnt, oPhysCard, bIncCard, bDecCard),
                            (2, oAbsCard))
            if self.iExtraLevelsMode == EXP_AND_CARD_SETS and \
                    sExpName in self._dAbsSecondLevel2Iter[oAbsCard]:
                self._inc_exp_child_set_count(tExpKey, sCardSetName)
        elif oAbsCard in self._dAbsSecondLevel2Iter and \
                sExpName in self._dAbsSecondLevel2Iter[oAbsCard]:
            if tExpKey in self._dAbs2nd3rdLevel2Iter and \
                    sCardSetName in self._dAbs2nd3rdLevel2Iter[tExpKey]:
                bRemove = False
                for oIter in self._dAbs2nd3rdLevel2Iter[tExpKey][
                        sCardSetName]:
                    iCnt = self.get_value(oIter, 1) + iChg
                    self.set(oIter, 1, iCnt)
                    if bRemove or not self.check_child_iter_stays(oIter,
                            oPhysCard):
                        bRemove = True
                        self.remove(oIter)
                if bRemove:
                    del self._dAbs2nd3rdLevel2Iter[tExpKey]
            bRemove = False
            for oIter in self._dAbsSecondLevel2Iter[oAbsCard][sExpName]:
                if bRemove or not self.check_child_iter_stays(oIter,
                        oPhysCard):
                    bRemove = True
            if bRemove:
                self._remove_second_level(oAbsCard, sExpName)

    def alter_child_cnt_cs_exps(self, oPhysCard, sCardSetName, iChg):
        """Handle the alter child card case when showing child sets as the
           second level with expansions"""
        # pylint: disable-msg = E1101, E1103
        # PyProtocols confuses pylint
        oAbsCard = oPhysCard.abstractCard
        sExpName = self.get_expansion_name(oPhysCard.expansion)
        tExpKey = (oAbsCard, sExpName)
        if oAbsCard in self._dAbsSecondLevel2Iter and \
                sCardSetName in self._dAbsSecondLevel2Iter[oAbsCard]:
            # Alter counts, checking if we need a
            # new 3rd level entry, or to remove any entries
            bRemove = False
            tCSKey = (oAbsCard, sCardSetName)
            for oIter in self._dAbsSecondLevel2Iter[oAbsCard][sCardSetName]:
                iCnt = self.get_value(oIter, 1) + iChg
                iParCnt = self.get_value(oIter, 2)
                self.set(oIter, 1, iCnt)
                if not self.check_child_iter_stays(oIter, oPhysCard):
                    bRemove = True
            if bRemove:
                self._remove_second_level(oAbsCard, sCardSetName)
            elif tCSKey in self._dAbs2nd3rdLevel2Iter and \
                    sExpName in self._dAbs2nd3rdLevel2Iter[tCSKey]:
                # Update entry
                bRemove = False
                for oIter in self._dAbs2nd3rdLevel2Iter[tCSKey][sExpName]:
                    iCnt = self.get_value(oIter, 1) + iChg
                    iParCnt = self.get_value(oIter, 2)
                    self.set(oIter, 1, iCnt)
                    if bRemove or not self.check_child_iter_stays(oIter,
                            oPhysCard):
                        self.remove(oIter)
                        bRemove = True
                if bRemove:
                    del self._dAbs2nd3rdLevel2Iter[tCSKey][sExpName]
            else:
                self._add_child_3rd_level_exp_entry(oPhysCard, sCardSetName,
                        tExpKey)
        else:
            # Add a card set entry
            iCnt = 1
            bIncCard, bDecCard = self.check_inc_dec(iCnt)
            for oIter in self._dAbs2Iter[oAbsCard]:
                iParCnt = self.get_value(oIter, 2)
                self._add_extra_level(oIter, sCardSetName,
                        (iCnt, iParCnt, oPhysCard, bIncCard, bDecCard),
                        (2, oAbsCard))
            self._add_child_3rd_level_exp_entry(oPhysCard, sCardSetName,
                    tExpKey)

    #
    # Per-deck option changes
    #

    def _change_level_mode(self, iLevel):
        """Set which extra information is shown."""
        if self.iExtraLevelsMode != iLevel:
            self.iExtraLevelsMode = iLevel
            return True
        return False

    def _change_count_mode(self, iLevel):
        """Set which extra information is shown."""
        if self.iShowCardMode != iLevel:
            self.iShowCardMode = iLevel
            return True
        return False

    def _change_parent_count_mode(self, iLevel):
        """Toggle the visibility of the parent col"""
        if iLevel == IGNORE_PARENT:
            self._oController.view.set_parent_count_col_vis(False)
        else:
            self._oController.view.set_parent_count_col_vis(True)
        if self.iParentCountMode == iLevel:
            return False
        self.iParentCountMode = iLevel
        return True

    def update_options(self, bSkipLoad=False):
        """Update all the per-deck options.

           bSkipLoad is set when we first call this function during the model
           creation to avoid calling load twice."""
        # pylint: disable-msg=E1101, E1103
        # Pyprotocols confuses pylint

        sExtraLevelOpt = self._oConfig.get_deck_option(
            self.frame_id, self.cardset_id, EXTRA_LEVEL_OPTION).lower()
        iExtraLevelMode = EXTRA_LEVEL_LOOKUP.get(sExtraLevelOpt,
                SHOW_EXPANSIONS)

        sShowCardOpt = self._oConfig.get_deck_option(
            self.frame_id, self.cardset_id, SHOW_CARD_OPTION).lower()
        iShowCardMode = SHOW_CARD_LOOKUP.get(sShowCardOpt, THIS_SET_ONLY)

        sParentCountOpt = self._oConfig.get_deck_option(
            self.frame_id, self.cardset_id, PARENT_COUNT_MODE).lower()
        iParentCountOpt = PARENT_COUNT_LOOKUP.get(sParentCountOpt,
                IGNORE_PARENT)
        bUseIcons = self._oConfig.get_deck_option(self.frame_id,
                self.cardset_id, USE_ICONS)

        bHideIllegal = self._oConfig.get_deck_option(self.frame_id,
                self.cardset_id, HIDE_ILLEGAL)

        bReloadELM = self._change_level_mode(iExtraLevelMode)
        bReloadSCM = self._change_count_mode(iShowCardMode)
        bReloadPCM = self._change_parent_count_mode(iParentCountOpt)
        bReloadIcons = self._change_icon_mode(bUseIcons)
        bReloadIllegal = self._change_illegal_mode(bHideIllegal)
        if not bSkipLoad and (bReloadELM or bReloadSCM or bReloadPCM
                or bReloadIcons or bReloadIllegal):
            self._oController.view.reload_keep_expanded()

    #
    # Per-deck configuration listeners
    #

    def profile_changed(self, sProfile, sKey):
        """One of the per-deck configuration items changed."""
        self.update_options()

    def frame_profile_changed(self, sFrame, sNewProfile):
        """The profile associated with a frame changed."""
        if sFrame != self.frame_id:
            return
        self.update_options()

    def cardset_profile_changed(self, sCardset, sNewProfile):
        """The profile associated with a cardset changed."""
        if sCardset != self.cardset_id:
            return
        self.update_options()
