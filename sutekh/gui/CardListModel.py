# CardListModel.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""The gtk.TreeModel for the card lists."""

import gtk, gobject
from sutekh.core.Filters import FilterAndBox, NullFilter, PhysicalCardFilter
from sutekh.core.Groupings import CardTypeGrouping
from sutekh.core.SutekhObjects import IAbstractCard, PhysicalCard, \
        IPhysicalCard, canonical_to_csv
from sutekh.gui.ConfigFile import ConfigFileListener

class CardListModelListener(object):
    """Listens to updates, i.e. .load(...), .alter_card_count(...),
       .add_new_card(..) calls, to CardListModels."""
    def load(self, aPhysCards):
        """The CardListModel has reloaded itself. aPhysCards is the list of
           PhysicalCards loaded."""
        pass

    def alter_card_count(self, oCard, iChg):
        """The count of the given card has been altered by iChg.

           oCard: PhysicalCard for the card altered
           """
        pass

    def add_new_card(self, oCard, iCnt):
        """The card has been added to this set iCnt times.

           oCard: PhysicalCard for the cards altered
           """
        pass

    # pylint: disable-msg=R0201
    # Default of returning true is correct
    def check_card_visible(self, _oPhysCard):
        """Check if a card should be shown in the model.

           return False if the card should be hidden, True otherwise.
           oPhysCard is always a physical card."""

        return True

class CardListModel(gtk.TreeStore, ConfigFileListener):
    # pylint: disable-msg=R0904, R0902
    # inherit a lot of public methods for gtk, need local attributes for state
    """Provides a card list specific API for accessing a gtk.TreeStore."""
    # Use spaces to ensure it sorts first
    # Could possibly be more visually distinct, but users can filter
    # on unknown expansions if needed.

    sUnknownExpansion = '  Unspecified Expansion'

    def __init__(self, oConfig):
        # STRING is the card name, INT is the card count
        super(CardListModel, self).__init__(str, int, int, bool, bool,
                gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT,
                gtk.gdk.Color,
                gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)
        # name, count, parent count, showInc, showDec, text_list, icons,
        #       parent_color, AbstractCard, PhysicalCard

        self._cGroupBy = CardTypeGrouping # grouping class to use
        # base filter defines the card list
        self._oBaseFilter = PhysicalCardFilter()
        self._cCardClass = PhysicalCard # card class to use
        self._bApplyFilter = False # whether to apply the select filter
        # additional filters for selecting from the list
        self._oSelectFilter = None
        self._oConfig = oConfig
        self._oConfig.add_listener(self)

        self.dListeners = {} # dictionary of CardListModelListeners

        self.bExpansions = True
        self.oEmptyIter = None
        self.oIconManager = None
        self.bUseIcons = True

    # pylint: disable-msg=W0212, C0103
    # W0212 - we explicitly allow access via these properties
    # C0103 - we allow these names
    cardclass = property(fget=lambda self: self._cCardClass,
            fset=lambda self, x: setattr(self, '_cCardClass', x))
    groupby = property(fget=lambda self: self._cGroupBy,
            fset=lambda self, x: setattr(self, '_cGroupBy', x))
    basefilter = property(fget=lambda self: self._oBaseFilter,
            fset=lambda self, x: setattr(self, '_oBaseFilter', x))
    applyfilter = property(fget=lambda self: self._bApplyFilter,
            fset=lambda self, x: setattr(self, '_bApplyFilter', x))
    selectfilter = property(fget=lambda self: self._oSelectFilter,
            fset=lambda self, x: setattr(self, '_oSelectFilter', x))
    # pylint: enable-msg=W0212, C0103

    def add_listener(self, oListener):
        """Add a listener to the list of interested listeners."""
        self.dListeners[oListener] = None

    def remove_listener(self, oListener):
        """Remove a listener from the list."""
        del self.dListeners[oListener]

    # various utilty functions for checking the model state

    # Helper's for sorting

    def _sort_col(self, _oModel, oIter1, oIter2, iCol):
        """Default sort function for model"""
        oVal1 = self.get_value(oIter1, iCol)
        oVal2 = self.get_value(oIter2, iCol)
        iRes = cmp(oVal1, oVal2)
        if iRes == 0:
            iRes = self.sort_equal_iters(oIter1, oIter2)
        return iRes

    def sort_equal_iters(self, oIter1, oIter2):
        """Default sort on names (card names, expansion names, etc.)"""
        # The default sorting behaviour for equal rows can be changed by
        # hooking into this
        oVal1 = self.get_value(oIter1, 0)
        oVal2 = self.get_value(oIter2, 0)
        return cmp(oVal1, oVal2)

    def enable_sorting(self):
        """Enable default sorting setup"""
        # We don't do this in __init__, as it makes the test suite a
        # lot slower, and the tests don't need sorting anyway.
        # The view calls this to enable sorting. Not elegant, but
        # at least workable.
        self.set_sort_func(0, self._sort_col, 0)
        self.set_sort_func(1, self._sort_col, 1)
        self.set_sort_func(2, self._sort_col, 2)
        # Sort the model on the card name by default
        self.set_sort_column_id(0, gtk.SORT_ASCENDING)

    def get_expansion_info(self, _oCard, dExpanInfo):
        """Get information about expansions"""
        aExpansions = []
        if not self.bExpansions:
            return aExpansions
        for oPhysCard in dExpanInfo:
            aExpansions.append((oPhysCard,
                self.get_expansion_name(oPhysCard.expansion)))
        return aExpansions

    def get_expansion_name(self, oExpansion):
        """Utility function to return iether the name, or the appropriate
           placeholder for oExpansion is None."""
        if oExpansion:
            return oExpansion.name
        return self.sUnknownExpansion

    def lookup_icons(self, sGroup):
        """Lookup the icons for the group. Method since it's repeated in
           several places in CardSetListModel"""
        if self.oIconManager and self.bUseIcons:
            aTexts, aIcons = self.oIconManager.get_info(sGroup,
                    self.groupby)
        else:
            aTexts = aIcons = []
        return aTexts, aIcons

    # pylint: disable-msg=R0201
    # Method so it can be inherited
    def _fix_group_name(self, sGroup):
        """Fix the None group name"""
        # Utiltiy helper, so we only need to change this once
        if sGroup is None:
            return "<< None >>"
        return sGroup

    # pylint: enable-msg=R0201

    def _set_display_name(self, bPostfix):
        """Set the correct display name for the cards.

           We walk all the 1st level entries, and set the name from the
           card, based on bPostfix."""
        oIter = self.get_iter_first() # Grouping level items
        while oIter:
            oChildIter = self.iter_children(oIter)
            while oChildIter:
                sName = self.get_card_name_from_iter(oChildIter)
                if bPostfix:
                    sName = canonical_to_csv(sName)
                self.set(oChildIter, 0, sName)
                self.row_changed(self.get_path(oChildIter), oChildIter)
                oChildIter = self.iter_next(oChildIter)
            oIter = self.iter_next(oIter)

    def set_postfix_the_display(self, bPostfix):
        """Respond to config file changes. Passes straight through to
           _set_display_name so we don't need another load."""
        # Disable sorting while we touch everything
        iSortColumn, iSortOrder = self.get_sort_column_id()
        if iSortColumn is not None:
            self.set_sort_column_id(-2, 0)
        self._set_display_name(bPostfix)
        # Enable sorting
        if iSortColumn is not None:
            self.set_sort_column_id(iSortColumn, iSortOrder)

    def load(self):
        # pylint: disable-msg=R0914
        # we use many local variables for clarity
        """Clear and reload the underlying store. For use after initialisation
           or when the filter or grouping changes."""
        self.clear()

        oCardIter = self.get_card_iterator(self.get_current_filter())
        fGetCard, _fGetCount, fGetExpanInfo, oGroupedIter, aCards = \
                self.grouped_card_iter(oCardIter)

        self.oEmptyIter = None

        # Disable sorting while we do the insertions - speeds things up
        iSortColumn, iSortOrder = self.get_sort_column_id()
        if iSortColumn is not None:
            self.set_sort_column_id(-2, 0)

        # Iterate over groups
        bEmpty = True
        for sGroup, oGroupIter in oGroupedIter:
            # Check for null group
            sGroup = self._fix_group_name(sGroup)

            # Create Group Section
            oSectionIter = self.append(None)

            # Fill in Cards
            for oItem in oGroupIter:
                oCard = fGetCard(oItem)
                oChildIter = self.prepend(oSectionIter)
                # We need to lookup the card directly, since aExpansionInfo
                # may not have the info we need
                # Names will be set by _set_display_name
                self.set(oChildIter,
                    5, [],
                    6, [],
                    8, oCard,
                    9, IPhysicalCard((oCard, None)),
                )
                aExpansionInfo = self.get_expansion_info(oCard,
                        fGetExpanInfo(oItem))
                for oPhysCard, sExpansion in aExpansionInfo:
                    oExpansionIter = self.append(oChildIter)
                    self.set(oExpansionIter,
                            0, sExpansion,
                            5, [],
                            6, [],
                            8, oCard,
                            9, oPhysCard,
                            )
                bEmpty = False

            # Update Group Section
            aTexts, aIcons = self.lookup_icons(sGroup)
            if aTexts:
                self.set(oSectionIter,
                    0, sGroup,
                    5, aTexts,
                    6, aIcons,
                    8, None,
                    9, None,
                )
            else:
                self.set(oSectionIter,
                    0, sGroup,
                    5, [],
                    6, [],
                    8, None,
                    9, None,
                )

        if bEmpty:
            # Showing nothing
            self.oEmptyIter = self.append(None)
            sText = self._get_empty_text()
            self.set(self.oEmptyIter, 0, sText, 5, [], 6, [], 8, None, 9, None)
        else:
            self._set_display_name(self._oConfig.get_postfix_the_display())

        if iSortColumn is not None:
            self.set_sort_column_id(iSortColumn, iSortOrder)
        # Notify Listeners
        for oListener in self.dListeners:
            oListener.load(aCards)

    def get_card_iterator(self, oFilter):
        """Return an interator over the card model.

           The filter is combined with self.basefilter. None may be used to
           retrieve the entire card list (with only the base filter
           restriciting which cards appear).
           """
        oFilter = self.combine_filter_with_base(oFilter)

        return oFilter.select(self.cardclass).distinct()

    def grouped_card_iter(self, oCardIter):
        """Return iterator over the card list grouping.

           Returns a triple of fGetCard (the function used to
           retrieve a card from an item), fGetCount (the function used to
           retrieve a card count from an item) and oGroupedIter (an iterator
           over the card groups)
           """
        aCards = []
        fGetCard = lambda x:x[0]
        fGetCount = lambda x:x[1][0]
        fGetExpanInfo = lambda x:x[1][1]

        # Count by Abstract Card
        dAbsCards = {}

        for oCard in oCardIter:
            # pylint: disable-msg=E1101
            # sqlobject confuses pylint
            oPhysCard = IPhysicalCard(oCard)
            if not self.check_card_visible(oPhysCard):
                continue
            oAbsCard = IAbstractCard(oPhysCard)
            aCards.append(oPhysCard)
            dAbsCards.setdefault(oAbsCard, [0, {}])
            dAbsCards[oAbsCard][0] += 1
            if self.bExpansions:
                dExpanInfo = dAbsCards[oAbsCard][1]
                dExpanInfo.setdefault(oPhysCard, 0)
                dExpanInfo[oPhysCard] += 1

        aAbsCards = list(dAbsCards.iteritems())

        # Iterate over groups
        return (fGetCard, fGetCount, fGetExpanInfo,
                self.groupby(aAbsCards, fGetCard), aCards)

    def get_current_filter(self):
        """Get the current applied filter."""
        if self.applyfilter:
            return self.selectfilter
        else:
            return None

    def combine_filter_with_base(self, oOtherFilter):
        """Return the combination of oOtherFilter with the base filter.

           This handles the cases where either filter is None properly."""
        if self.basefilter is None and oOtherFilter is None:
            return NullFilter()
        elif self.basefilter is None:
            return oOtherFilter
        elif oOtherFilter is None:
            return self.basefilter
        else:
            return FilterAndBox([self.basefilter, oOtherFilter])

    def get_card_name_from_path(self, oPath):
        """Get the card name associated with the current path. Handle the
           expansion level transparently."""
        oIter = self.get_iter(oPath)
        return self.get_card_name_from_iter(oIter)

    def get_card_name_from_iter(self, oIter):
        """Get the card name associated with the current iter. Handle the
           expansion level transparently."""
        oCard = self.get_abstract_card_from_iter(oIter)
        if oCard:
            return oCard.name
        # Top level item, so just return the string
        return self.get_name_from_iter(oIter)

    def get_abstract_card_from_path(self, oPath):
        """Get the abstract card name for the current path."""
        oIter = self.get_iter(oPath)
        return self.get_abstract_card_from_iter(oIter)

    def get_physical_card_from_path(self, oPath):
        """Get the physical card name for the current path."""
        oIter = self.get_iter(oPath)
        return self.get_physical_card_from_iter(oIter)

    def check_card_visible(self, oPhysCard):
        """Returns true if oPhysCard should be shown.

           Used by plugins to allow extra filtering of cards."""
        bResult = True
        for oListener in self.dListeners:
            bResult = bResult and oListener.check_card_visible(oPhysCard)
            if not bResult:
                break # Failed, so bail on loop
        return bResult

    def get_all_iter_children(self, oIter):
        """Get a list of all the subiters of this iter"""
        aChildIters = []
        oChildIter = self.iter_children(oIter)
        while oChildIter:
            aChildIters.append(oChildIter)
            oChildIter = self.iter_next(oChildIter)
        return aChildIters

    def get_all_from_iter(self, oIter):
        """Get all relevent information about the current iter.

           Returns the tuple (CardName, Expansion info, Card Count,
           depth in the  model), where depth in the model is 1 for the top
           level of cards, and 2 for the expansion level.
           """
        iDepth = self.iter_depth(oIter)
        if iDepth == 0:
            # No card info here
            return None, None, 0, iDepth
        sCardName = self.get_card_name_from_iter(oIter)
        if iDepth == 2:
            sExpansion = self.get_value(oIter, 0)
        else:
            sExpansion = None
        iCount = self.get_value(oIter, 1)
        return sCardName, sExpansion, iCount, iDepth

    def get_all_from_path(self, oPath):
        """Get all relevent information about the current path.

           Conveince wrapper around get_all_from_iter, for use in cases when
           it's easier to get the path than the iter (selections, etc.)
           """
        if oPath:
            # Avoid crashes when oPath is None for some reason
            oIter = self.get_iter(oPath)
            return self.get_all_from_iter(oIter)
        return None, None, None, None

    def get_child_entries_from_path(self, oPath):
        """Return a list of (sExpansion, iCount) pairs for the children of
           this path"""
        oIter = self.get_iter(oPath)
        aChildren = []
        iDepth = self.iter_depth(oIter)
        if iDepth != 1:
            # No children to look at
            return aChildren
        oChildIter = self.iter_children(oIter)
        while oChildIter:
            sExpansion = self.get_value(oChildIter, 0)
            iCount = self.get_value(oChildIter, 1)
            aChildren.append((sExpansion, iCount))
            oChildIter = self.iter_next(oChildIter)
        return aChildren

    def get_inc_dec_flags_from_path(self, oPath):
        """Get the settings of the inc + dec flags for the current path"""
        oIter = self.get_iter(oPath)
        bInc = self.get_value(oIter, 3)
        bDec = self.get_value(oIter, 4)
        return (bInc, bDec)

    def get_exp_name_from_path(self, oPath):
        """Get the expansion information from the model, returing None if this
           is not at a level where the expansion is known."""
        oIter = self.get_iter(oPath)
        if self.iter_depth(oIter) != 2:
            return None
        return self.get_name_from_iter(oIter)

    def get_name_from_iter(self, oIter):
        """Extract the value at oIter from the model, correcting for encoding
           issues."""
        # For some reason the string comes back from the
        # tree store having been encoded *again* despite
        # displaying correctly, so we decode it here.
        # I hope all systems encode with utf-8. :(
        sName = self.get_value(oIter, 0).decode("utf-8")
        return sName

    def get_card_count_from_iter(self, oIter):
        """Return the card count for a given iterator"""
        return self.get_value(oIter, 1)

    def get_parent_count_from_iter(self, oIter):
        """Return the parent count for a given iterator"""
        return self.get_value(oIter, 2)

    def get_abstract_card_from_iter(self, oIter):
        """Extract the Abstract Card at oIter from the model"""
        return self.get_value(oIter, 8)

    def get_physical_card_from_iter(self, oIter):
        """Extract the Physical Card at oIter from the model"""
        return self.get_value(oIter, 9)

    def _get_empty_text(self):
        """Get the correct text for an empty model."""
        if self.get_card_iterator(None).count() == 0:
            sText = 'Empty'
        else:
            sText = 'No Cards found'
        return sText
