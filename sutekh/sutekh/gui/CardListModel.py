# CardListModel.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk, gobject
from sutekh.core.Filters import FilterAndBox, SpecificCardFilter, NullFilter, \
        PhysicalCardFilter, PhysicalCardSetFilter
from sutekh.core.Groupings import CardTypeGrouping
from sutekh.core.SutekhObjects import AbstractCard, IAbstractCard, \
        PhysicalCard, IExpansion

def norm_path(oPath):
    """Transform string paths to tuple paths"""
    # Some widgets give us a path string, others a tuple,
    # to deal with tuples when moving between expansions and
    # card names
    if type(oPath) is str:
        oNormPath = tuple([int(x) for x in oPath.split(':')])
    else:
        oNormPath = oPath
    return oNormPath

class CardListModelListener(object):
    """
    Listens to updates, i.e. .load(...), .alterCardCount(...), .addNewCard(..) calls,
    to CardListModels.
    """
    def load(self, aAbsCards):
        """
        The CardListModel has reloaded itself.
        aAbsCards is the list of AbstractCards loaded
        """
        pass

    def alterCardCount(self, oCard, iChg):
        """
        The count of the given card has been altered by iChg.
        oCard: AbstractCard for the card altered (the actual card may be a Physical Card).
        """
        pass

    def addNewCard(self, oCard):
        """
        A single copy of the given card has been added.
        oCard: AbstractCard for the card altered (the actual card may be a Physical Card).
        """
        pass

    def add_new_card_expansion(self, oCard, sExpansion):
        """
        A new expansion of the given card has been added.
        oCard: AbstractCard for the card altered (the actual card may be a Physical Card).
        """
        pass

    def alter_card_expansion_count(self, oCard, sExpansion, iChg):
        """
        The count of the given Expansion has been altered by iChg.
        oCard: AbstractCard for the card altered (the actual card may be a Physical Card).
        """
        pass

class CardListModel(gtk.TreeStore):
    """
    Provides a card list specific API for accessing a gtk.TreeStore.
    """
    # Use spaces to ensure it sorts first
    # Could possibly be more visually distinct, but users can filter
    # on unknown expansions if needed.

    sUnknownExpansion = '  Unspecified Expansion'

    def __init__(self):
        # STRING is the card name, INT is the card count
        super(CardListModel, self).__init__(gobject.TYPE_STRING, gobject.TYPE_INT,
                gobject.TYPE_BOOLEAN, gobject.TYPE_BOOLEAN)
        self._dName2Iter = {}
        self._dNameExpansion2Iter = {}

        self.cardclass = AbstractCard # card class to use
        self.groupby = CardTypeGrouping # grouping class to use
        self.basefilter = None # base filter defines the card list
        self.applyfilter = False # whether to apply the select filter
        self.selectfilter = None # additional filters for selecting from the list

        self.listeners = {} # dictionary of CardListModelListeners

        self.bExpansions = False
        self.bEditable = False
        self.bAddAllAbstractCards = False

    cardclass = property(fget=lambda self: self._cCardClass, fset=lambda self, x: setattr(self, '_cCardClass', x))
    groupby = property(fget=lambda self: self._cGroupBy, fset=lambda self, x: setattr(self, '_cGroupBy', x))
    basefilter = property(fget=lambda self: self._oBaseFilter, fset=lambda self, x: setattr(self, '_oBaseFilter', x))
    applyfilter = property(fget=lambda self: self._bApplyFilter, fset=lambda self, x: setattr(self, '_bApplyFilter', x))
    selectfilter = property(fget=lambda self: self._oSelectFilter, fset=lambda self, x: setattr(self, '_oSelectFilter', x))

    def addListener(self, oListener):
        self.listeners[oListener] = None

    def removeListener(self, oListener):
        del self.listeners[oListener]

    def check_inc_dec_card(self, oCard, iCnt):
        """Helper function to check whether card can be incremented"""
        if self.bEditable:
            return True, iCnt > 0
        else:
            return False, False

    def check_inc_dec_expansion(self, oCard, sExpansion, iCnt):
        """Helper function to check status of expansions"""
        # No-op for AbtractCardList and AbstractCardSet
        return False, False

    def get_add_card_expansion_info(self, oCard, dExpanInfo):
        """Get the expansions to list for a newly added card"""
        return []

    def get_expansion_info(self, oCard, dExpanInfo):
        """Get information about expansions"""
        # For AbstractCardSets and the AbstractCardList, this is basically a NOP
        return {}

    def check_expansion_iter_stays(self, oCard, sExpansion, iCnt):
        """Check if the expansion entry should remain in the table"""
        return False

    def init_info_cache(self):
        """Batch queries about the cardlist for faster processing"""
        pass

    def clear_info_cache(self):
        """Clean up the cache"""
        pass

    def load(self):
        """
        Clear and reload the underlying store. For use after initialisation or when
        the filter or grouping changes.
        """
        self.clear()
        self._dName2Iter = {}
        self._dNameExpansion2Iter = {}
        self._dGroupName2Iter = {}

        oCardIter = self.getCardIterator(self.getCurrentFilter())
        fGetCard, fGetCount, fGetExpanInfo, oGroupedIter, aAbsCards = self.groupedCardIterator(oCardIter)

        self.init_info_cache()

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
                    2, bIncCard,
                    3, bDecCard
                )
                dExpansionInfo = self.get_expansion_info(oCard, fGetExpanInfo(oItem))
                # fill in the numbers for all possible expansions for
                # the card
                for sExpansion in sorted(dExpansionInfo.keys()):
                    oExpansionIter = self.append(oChildIter)
                    iExpCnt, bDecCard, bIncCard = dExpansionInfo[sExpansion]
                    self.set(oExpansionIter,
                            0, sExpansion,
                            1, iExpCnt,
                            2, bIncCard,
                            3, bDecCard)
                    self._dNameExpansion2Iter.setdefault(oCard.name,
                            {}).setdefault(sExpansion,
                                    []).append(oExpansionIter)
                self._dName2Iter.setdefault(oCard.name, []).append(oChildIter)


            # Update Group Section
            self.set(oSectionIter,
                0, sGroup,
                1, iGrpCnt,
                2, False,
                3, False
            )

        # Notify Listeners
        for oListener in self.listeners:
            oListener.load(aAbsCards)

        self.clear_info_cache

    def getCardIterator(self, oFilter):
        """
        Return an interator over the card model. The filter is
        combined with self.basefilter. None may be used to retrieve
        the entire card list (with only the base filter restriciting which cards appear).
        """
        oFilter = self.combineFilterWithBase(oFilter)

        return oFilter.select(self.cardclass).distinct()

    def groupedCardIterator(self, oCardIter):
        """
        Handles the differences in the way AbstractCards and PhysicalCards
        are grouped and returns a triple of fGetCard (the function used to
        retrieve a card from an item), fGetCount (the function used to
        retrieve a card count from an item) and oGroupedIter (an iterator
        over the card groups)
        """
        # Define iterable and grouping function based on cardclass
        if self.cardclass is AbstractCard:
            fGetCard = lambda x:x
            fGetCount = lambda x:0
            fGetExpanInfo = lambda x:{}
            aCards = list(oCardIter)
            aCards.sort(lambda x, y: cmp(x.name, y.name))
            aAbsCards = aCards
        else:
            aAbsCards = []
            fGetCard = lambda x:x[0]
            fGetCount = lambda x:x[1][0]
            fGetExpanInfo = lambda x:x[1][1]

            # Count by Abstract Card
            dAbsCards = {}

            if self.bAddAllAbstractCards:
                # Also include all the abstract cards
                oAbsFilter = self.getCurrentFilter()
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
                oAbsCard = oCard.abstractCard
                aAbsCards.append(oAbsCard)
                dAbsCards.setdefault(oAbsCard, [0, {}])
                dAbsCards[oAbsCard][0] += 1
                if self.bExpansions:
                    dExpanInfo = dAbsCards[oAbsCard][1]
                    dExpanInfo.setdefault(oCard.expansion, 0)
                    dExpanInfo[oCard.expansion] += 1

            aCards = list(dAbsCards.iteritems())
            aCards.sort(lambda x, y: cmp(x[0].name, y[0].name))

        # Iterate over groups
        return fGetCard, fGetCount, fGetExpanInfo, self.groupby(aCards, fGetCard), aAbsCards

    def getCurrentFilter(self):
        if self.applyfilter:
            return self.selectfilter
        else:
            return None

    def combineFilterWithBase(self, oOtherFilter):
        if self.basefilter is None and oOtherFilter is None:
            return NullFilter()
        elif self.basefilter is None:
            return oOtherFilter
        elif oOtherFilter is None:
            return self.basefilter
        else:
            return FilterAndBox([self.basefilter, oOtherFilter])

    def getCardNameFromPath(self, oPath):
        """
        Get the card name associated with the current path. Handle
        the expansion level transparently.
        """
        oIter = self.get_iter(oPath)
        if self.iter_depth(oIter) == 2:
            # Expansion section - we want the card before this
            # according to the docs this is assured to be the
            # correct path to it
            oIter = self.get_iter(norm_path(oPath)[0:2])
        return self.getNameFromIter(oIter)

    def get_all_from_path(self, oPath):
        """
        Get all relevent information about the current path.
        Returns the tuple (CardName, Expansion info, Card Count,
        depth in the  model), where depth in the model is 1 for the top
        level of cards, and 2 for the expansion level.
        """
        oIter = self.get_iter(oPath)
        iDepth = self.iter_depth(oIter)
        if iDepth == 2:
            sName = self.getNameFromIter(self.get_iter(norm_path(oPath)[0:2]))
            sExpansion = self.get_value(oIter, 0)
        else:
            sName = self.getNameFromIter(oIter)
            sExpansion = None
        iCount = self.get_value(oIter, 1)
        return sName, sExpansion, iCount, iDepth

    def get_inc_dec_flags_from_path(self, oPath):
        """Get the settings of the inc + dec flags for the current path"""
        oIter = self.get_iter(oPath)
        bInc = self.get_value(oIter, 2)
        bDec = self.get_value(oIter, 3)
        return (bInc, bDec)

    def getExpansionNameFromPath(self, oPath):
        """
        Get the expansion information from the model, returing None
        if this is not at a level where the expansion is known.
        """
        oIter = self.get_iter(oPath)
        if self.iter_depth(oIter) != 2:
            return None
        return self.getNameFromIter(oIter)

    def getNameFromIter(self, oIter):
        """
        Extract the value at oIter from the model, correcting for encoding
        issues
        """
        # For some reason the string comes back from the
        # tree store having been encoded *again* despite
        # displaying correctly, so we decode it here.
        # I hope all systems encode with utf-8. :(
        sCardName = self.get_value(oIter, 0).decode("utf-8")
        return sCardName

    def incCard(self, oPath):
        """
        Add a copy of the card at oPath from the model
        """
        sCardName = self.getCardNameFromPath(oPath)
        self.alterCardCount(sCardName, +1)

    def decCard(self, oPath):
        """
        Remove a copy of the card at oPath from the model
        """
        sCardName = self.getCardNameFromPath(oPath)
        self.alterCardCount(sCardName, -1)

    def incCardExpansionByName(self, sCardName, sExpansion):
        """
        Increases the expansion count for this card without changing the
        total card count. Should be paired with calls to incCardByName
        or decCardExpansionByName for consistency
        """
        if sExpansion is None:
            sExpansion = self.sUnknownExpansion
        if self._dNameExpansion2Iter.has_key(sCardName):
            if self._dNameExpansion2Iter[sCardName].has_key(sExpansion):
                self.alterCardExpansionCount(sCardName, sExpansion, +1)
            else:
                self.add_new_card_expansion(sCardName, sExpansion)

    def decCardExpansionByName(self, sCardName, sExpansion):
        """
        Decreases the expansion count for this card without changing total
        card count. Should be paired with calls to decCardByName or
        incCardExpansionByName for consistency
        """
        if sExpansion is None:
            sExpansion = self.sUnknownExpansion
        if self._dNameExpansion2Iter.has_key(sCardName) and \
                self._dNameExpansion2Iter[sCardName].has_key(sExpansion):
            self.alterCardExpansionCount(sCardName, sExpansion, -1)

    def incCardByName(self, sCardName):
        if self._dName2Iter.has_key(sCardName):
            # card already in the list
            self.alterCardCount(sCardName, +1)
        else:
            # new card
            self.addNewCard(sCardName)

    def decCardByName(self, sCardName):
        if self._dName2Iter.has_key(sCardName):
            self.alterCardCount(sCardName, -1)

    def add_new_card_expansion(self, sCardName, sExpansion):
        """Add a card with expansion to the model"""
        oCard = IAbstractCard(sCardName)
        aParenIters = self._dName2Iter[sCardName]
        self._dNameExpansion2Iter[sCardName][sExpansion] = []
        aSiblings = [None for x in aParenIters]
        for sThisExp in sorted(self._dNameExpansion2Iter[sCardName].keys()):
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
                            2, bIncCard,
                            3, bDecCard)
                    self._dNameExpansion2Iter[sCardName][sExpansion].append(oIter)
            else:
                aSiblings = self._dNameExpansion2Iter[sCardName][sThisExp]

        # Notify Listeners
        for oListener in self.listeners:
            oListener.add_new_card_expansion(oCard, sExpansion)

    def alterCardExpansionCount(self, sCardName, sExpansion, iChg):
        # Need to readjust inc, dec flags for all these cards
        oCard = IAbstractCard(sCardName)
        bDelDictEntry = False
        if not self._dNameExpansion2Iter.has_key(sCardName):
            # Can be called by CardSetController with non-existant card
            return
        for sThisExp, aList in self._dNameExpansion2Iter[sCardName].iteritems():
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
                            2, bIncCard,
                            3, bDecCard)
                else:
                    self.remove(oIter)
                    bDelDictEntry = True
        if bDelDictEntry:
            del self._dNameExpansion2Iter[sCardName][sExpansion]

        # Notify Listeners
        for oListener in self.listeners:
            oListener.alter_card_expansion_count(oCard, sExpansion, iChg)

    def alterCardCount(self, sCardName, iChg):
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
                self.set(oIter, 1, iCnt)
                bIncCard, bDecCard = self.check_inc_dec_card(oCard, iCnt)
                self.set(oIter, 2, bIncCard)
                self.set(oIter, 3, bDecCard)
            elif self.bAddAllAbstractCards:
                # Need to clean up all the children
                self.set(oIter, 1, iCnt)
                bIncCard, bDecCard = self.check_inc_dec_card(oCard, iCnt)
                self.set(oIter, 2, bIncCard)
                self.set(oIter, 3, bDecCard)
                if self._dNameExpansion2Iter.has_key(sCardName):
                    for sExpansion in self._dNameExpansion2Iter[sCardName].keys():
                        for oExpIter in self._dNameExpansion2Iter[sCardName][sExpansion]:
                            # No cards, so impossible to manipulate expansions
                            self.set(oExpIter, 1, 0,
                                    2, False,
                                    3, False)
            else:
                # Going away, so clean up expansions if needed
                if self._dNameExpansion2Iter.has_key(sCardName):
                    for sExpansion in self._dNameExpansion2Iter[sCardName].keys():
                        for oExpIter in self._dNameExpansion2Iter[sCardName][sExpansion]:
                            self.remove(oExpIter)
                        del self._dNameExpansion2Iter[sCardName][sExpansion]
                    del self._dNameExpansion2Iter[sCardName]
                self.remove(oIter)

            if iGrpCnt > 0:
                self.set(oGrpIter, 1, iGrpCnt)
            else:
                sGroupName = self.get_value(oGrpIter, 0)
                del self._dGroupName2Iter[sGroupName]
                self.remove(oGrpIter)

        if iCnt <= 0 and not self.bAddAllAbstractCards:
            del self._dName2Iter[sCardName]

        # Notify Listeners
        for oListener in self.listeners:
            oListener.alterCardCount(oCard, iChg)

    def addNewCard(self, sCardName):
        """
        If the card sCardName is not in the current list
        (i.e. is not in the card set or is filtered out)
        see if it should be filtered out or if it should be
        visible. If it should be visible, add it to the appropriate
        groups.
        """
        oFilter = self.combineFilterWithBase(self.getCurrentFilter())
        oFullFilter = FilterAndBox([SpecificCardFilter(sCardName), oFilter])

        oCardIter = oFullFilter.select(self.cardclass).distinct()

        fGetCard, fGetCount, fGetExpanInfo, oGroupedIter, aAbsCards = self.groupedCardIterator(oCardIter)
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
                    1, iGrpCnt
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
                    2, bIncCard,
                    3, bDecCard
                )
                self._dName2Iter.setdefault(oCard.name, []).append(oChildIter)

                aExpansions = self.get_add_card_expansion_info(oCard, fGetExpanInfo(oItem))

                for sExpName in aExpansions:
                    self._dNameExpansion2Iter.setdefault(oCard.name, {})
                    oExpandIter = self.append(oChildIter)
                    # For models with expansions, this will be paired with a
                    # call to inc Expansion count. We rely on this to sort
                    # out details - here we just create the needed space.
                    self.set(oExpandIter,
                            0, sExpName,
                            1, 0,
                            2, False,
                            3, False
                            )
                    self._dNameExpansion2Iter[oCard.name].setdefault(sExpName, []).append(oExpandIter)


            # Update Group Section
            self.set(oSectionIter,
                1, iGrpCnt
            )

        # Notify Listeners
        oCard = IAbstractCard(sCardName)
        for oListener in self.listeners:
            oListener.addNewCard(oCard)

class PhysicalCardListModel(CardListModel):
    def __init__(self,bAddAllAbstractCards):
        super(PhysicalCardListModel, self).__init__()
        self._oBaseFilter = PhysicalCardFilter()
        self._cCardClass = PhysicalCard
        self.bExpansions = True
        self.bAddAllAbstractCards = bAddAllAbstractCards

    def init_info_cache(self):
        self._dNoneCountCache = {}
        if self.bEditable:
            for oPhysCard in PhysicalCard.selectBy(expansionID=None):
                self._dNoneCountCache.setdefault(oPhysCard.abstractCard, 0)
                self._dNoneCountCache[oPhysCard.abstractCard] += 1

    def clear_info_cache(self):
        del self._dNoneCountCache

    def check_inc_dec_expansion(self, oCard, sExpansion, iCnt):
        """Helper function to check status of expansions"""
        if sExpansion != self.sUnknownExpansion:
            bDecCard = iCnt > 0
            bIncCard = PhysicalCard.selectBy(abstractCardID=oCard.id,
                    expansionID=None).count() > 0
        else:
            bDecCard = False
            bIncCard = False
        return bIncCard, bDecCard

    def get_expansion_info(self, oCard, dExpanInfo):
        """Get information about expansions"""
        dExpansions = {}
        if not self.bExpansions:
            return dExpansions
        if self.bEditable:
            # All possible expansions listed in the dictionary when editing
            # None entry always shows for Physical Card List when editable
            dExpansions[self.sUnknownExpansion] = [0, False, False]
            # Cards may be missing from _dNoneCountCache (show all abstract cards, etc.)
            iNoneCnt = self._dNoneCountCache.get(oCard, 0)
            for oP in oCard.rarity:
                dExpansions.setdefault(oP.expansion.name, [0, False, iNoneCnt > 0])
        for oExpansion, iCnt in dExpanInfo.iteritems():
            bDecCard = False
            bIncCard = False
            if oExpansion is not None:
                sKey = oExpansion.name
            else:
                sKey = self.sUnknownExpansion
            # For PhysicalCardList, we never touch Unknown directly
            # It's manipulated by changing other expansions
            if self.bEditable and oExpansion is not None:
                # Can only increase a expansion if there are unknown
                # cards to move across
                bIncCard = iNoneCnt > 0
                bDecCard = iCnt > 0
            dExpansions[sKey] = [iCnt, bDecCard, bIncCard]
        return dExpansions

    def check_expansion_iter_stays(self, oCard, sExpansion, iCnt):
        """Check if the expansion entry should remain in the table"""
        if iCnt > 0 or self.bEditable:
            # All expansions visible when editing the PhysicalCardList
            return True
        else:
            return False

    def get_add_card_expansion_info(self, oCard, dExpanInfo):
        """Get the expansions to list for a newly added card"""
        if not self.bExpansions:
            return []
        if self.bEditable:
            aExpansions = set([oP.expansion.name for oP in oCard.rarity])
            aList = [self.sUnknownExpansion] + sorted(list(aExpansions))
        else:
            aList = dExpanInfo.keys()
        return aList

class PhysicalCardSetCardListModel(CardListModel):
    def __init__(self, sSetName):
        super(PhysicalCardSetCardListModel, self).__init__()
        self._cCardClass = PhysicalCard
        self._oBaseFilter = PhysicalCardSetFilter(sSetName)
        self.bExpansions = True

    def check_inc_dec_card(self, oCard, iCnt):
        """Helper function to check whether card can be incremented"""
        if not self.bEditable:
            return False, False
        else:
            return iCnt < PhysicalCard.selectBy(abstractCardID=oCard.id).count(), iCnt > 0

    def check_inc_dec_expansion(self, oCard, sExpansion, iCnt):
        """Helper function to check status of expansions"""
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
        if iCnt > 0:
            return True
        if self.bEditable:
            # Only stays visible if cards in the PhysicalCardList with this expansion
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

