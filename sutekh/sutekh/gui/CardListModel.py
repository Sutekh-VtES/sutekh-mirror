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
        IPhysicalCard

def norm_path(oPath):
    """Transform string paths to tuple paths"""
    # Some widgets give us a path string, others a tuple,
    # to deal with tuples when moving between expansions and
    # card names
    if isinstance(oPath, str):
        oNormPath = tuple([int(x) for x in oPath.split(':')])
    else:
        oNormPath = oPath
    return oNormPath


class CardListModelListener(object):
    """Listens to updates, i.e. .load(...), .alter_card_count(...),
       .add_new_card(..) calls, to CardListModels."""
    def load(self, aAbsCards):
        """The CardListModel has reloaded itself. aAbsCards is the list of
           AbstractCards loaded."""
        pass

    def alter_card_count(self, oCard, iChg):
        """The count of the given card has been altered by iChg.

           oCard: AbstractCard for the card altered (the actual card may be
           a Physical Card).
           """
        pass

    def add_new_card(self, oCard):
        """A single copy of the given card has been added to this set.

           oCard: AbstractCard for the card altered (the actual card may be
           a Physical Card).
           """
        pass

class CardListModel(gtk.TreeStore):
    # pylint: disable-msg=R0904, R0902
    # inherit a lot of public methods for gtk, need local attributes for state
    """Provides a card list specific API for accessing a gtk.TreeStore."""
    # Use spaces to ensure it sorts first
    # Could possibly be more visually distinct, but users can filter
    # on unknown expansions if needed.

    sUnknownExpansion = '  Unspecified Expansion'

    def __init__(self):
        # STRING is the card name, INT is the card count
        super(CardListModel, self).__init__(str, int, int, bool, bool,
                gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT,
                gtk.gdk.Color, gtk.gdk.Color)
        # name, count, parent count, showInc, showDec, text_list, icons
        self._dName2Iter = {}
        self._dNameExpansion2Iter = {}
        self._dGroupName2Iter = {}

        self._cGroupBy = CardTypeGrouping # grouping class to use
        # base filter defines the card list
        self._oBaseFilter = PhysicalCardFilter()
        self._cCardClass = PhysicalCard # card class to use
        self._bApplyFilter = False # whether to apply the select filter
        # additional filters for selecting from the list
        self._oSelectFilter = None

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
        for oExpansion in dExpanInfo:
            aExpansions.append(self.get_expansion_name(oExpansion))
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

    def load(self):
        # pylint: disable-msg=R0914
        # we use many local variables for clarity
        """Clear and reload the underlying store. For use after initialisation
           or when the filter or grouping changes."""
        self.clear()
        self._dName2Iter = {}
        self._dNameExpansion2Iter = {}
        self._dGroupName2Iter = {}

        oCardIter = self.get_card_iterator(self.get_current_filter())
        fGetCard, _fGetCount, fGetExpanInfo, oGroupedIter, aAbsCards = \
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
            for oItem in oGroupIter:
                oCard = fGetCard(oItem)
                oChildIter = self.append(oSectionIter)
                self.set(oChildIter,
                    0, oCard.name,
                    5, [],
                    6, [],
                )
                aExpansionInfo = self.get_expansion_info(oCard,
                        fGetExpanInfo(oItem))
                for sExpansion in aExpansionInfo:
                    oExpansionIter = self.append(oChildIter)
                    self.set(oExpansionIter,
                            0, sExpansion,
                            5, [],
                            6, [])
                    self._dNameExpansion2Iter.setdefault(oCard.name,
                            {}).setdefault(sExpansion, []).append(
                                    oExpansionIter)
                self._dName2Iter.setdefault(oCard.name, []).append(oChildIter)

            # Update Group Section
            aTexts, aIcons = self.lookup_icons(sGroup)
            if aTexts:
                self.set(oSectionIter,
                    0, sGroup,
                    5, aTexts,
                    6, aIcons,
                )
            else:
                self.set(oSectionIter,
                    0, sGroup,
                    5, [],
                    6, [],
                )

        if not self._dName2Iter:
            # Showing nothing
            self.oEmptyIter = self.append(None)
            sText = self._get_empty_text()
            self.set(self.oEmptyIter, 0, sText, 5, [], 6, [])

        # Notify Listeners
        for oListener in self.dListeners:
            oListener.load(aAbsCards)

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
        aAbsCards = []
        fGetCard = lambda x:x[0]
        fGetCount = lambda x:x[1][0]
        fGetExpanInfo = lambda x:x[1][1]

        # Count by Abstract Card
        dAbsCards = {}

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

        # Iterate over groups
        return (fGetCard, fGetCount, fGetExpanInfo,
                self.groupby(aCards, fGetCard), aAbsCards)

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
        if self.iter_depth(oIter) > 1:
            # Child of the card name
            # According to the docs, this will be the correct path
            oIter = self.get_iter(norm_path(oPath)[0:2])
        return self.get_name_from_iter(oIter)

    def get_all_from_iter(self, oIter):
        """Get all relevent information about the current iter.

           Returns the tuple (CardName, Expansion info, Card Count,
           depth in the  model), where depth in the model is 1 for the top
           level of cards, and 2 for the expansion level.
           """
        iDepth = self.iter_depth(oIter)
        if iDepth == 2:
            sName = self.get_name_from_iter(self.iter_parent(oIter))
            sExpansion = self.get_value(oIter, 0)
        else:
            sName = self.get_name_from_iter(oIter)
            sExpansion = None
        iCount = self.get_value(oIter, 1)
        return sName, sExpansion, iCount, iDepth


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
        sCardName = self.get_value(oIter, 0).decode("utf-8")
        return sCardName

    def get_card_count_from_iter(self, oIter):
        """Return the card count for a given iterator"""
        return self.get_value(oIter, 1)

    def get_parent_count_from_iter(self, oIter):
        """Return the parent count for a given iterator"""
        return self.get_value(oIter, 2)

    def _get_empty_text(self):
        """Get the correct text for an empty model."""
        if self.get_card_iterator(None).count() == 0:
            sText = 'Empty'
        else:
            sText = 'No Cards found'
        return sText
