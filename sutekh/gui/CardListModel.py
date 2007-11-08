# CardListModel.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk, gobject
import sets
from sutekh.core.Filters import FilterAndBox, SpecificCardFilter, NullFilter, PhysicalExpansionFilter, \
        PhysicalCardFilter, PhysicalCardSetFilter
from sutekh.core.Groupings import CardTypeGrouping
from sutekh.core.SutekhObjects import AbstractCard, IAbstractCard, PhysicalCardSet, \
        PhysicalCard

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
    def load(self):
        """
        The CardListModel has reloaded itself.
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

class CardListModel(gtk.TreeStore):
    """
    Provides a card list specific API for accessing a gtk.TreeStore.
    """
    # FIXME: Use spaces to ensure it sorts first, and is 
    # visually distinct. Very much the wrong solution, I feel
 
    sUnknownExpansion = '  Unspecified Expansion'

    def __init__(self):
        # STRING is the card name, INT is the card count
        super(CardListModel, self).__init__(gobject.TYPE_STRING, gobject.TYPE_INT,
                gobject.TYPE_BOOLEAN, gobject.TYPE_BOOLEAN)
        self._dName2Iter = {}
        self._dNameExpansion2Iter = {}

        self.cardclass = AbstractCard # card class to use
        self.listenclass = AbstractCard # card class to listen for events on
        self.groupby = CardTypeGrouping # grouping class to use
        self.basefilter = None # base filter defines the card list
        self.applyfilter = False # whether to apply the select filter
        self.selectfilter = None # additional filters for selecting from the list

        self.listeners = {} # dictionary of CardListModelListeners

        self.bExpansions = False
        self.bEditable = False

    store = property(fget=lambda self: self._oGtkStore)
    cardclass = property(fget=lambda self: self._cCardClass, fset=lambda self, x: setattr(self, '_cCardClass', x))
    listenclass = property(fget=lambda self: self._cListenClass, fset=lambda self, x: setattr(self, '_cListenClass', x))
    groupby = property(fget=lambda self: self._cGroupBy, fset=lambda self, x: setattr(self, '_cGroupBy', x))
    basefilter = property(fget=lambda self: self._oBaseFilter, fset=lambda self, x: setattr(self, '_oBaseFilter', x))
    applyfilter = property(fget=lambda self: self._bApplyFilter, fset=lambda self, x: setattr(self, '_bApplyFilter', x))
    selectfilter = property(fget=lambda self: self._oSelectFilter, fset=lambda self, x: setattr(self, '_oSelectFilter', x))

    def addListener(self, oListener):
        self.listeners[oListener] = None

    def removeListener(self, oListener):
        del self.listeners[oListener]

    def check_inc_card(self, oCard):
        """Helper function to check whether card can be incremented"""
        if type(self.basefilter) is PhysicalCardSetFilter:
            # Can't inc if there are no physical cards
            bIncCard = iCnt < PhysicalCard.selectBy(abstractCardID=oCard.id).count()
        else:
            # always possible for PhysicalCardList and 
            # AbstractCardSet's 
            bIncCard = True
        return bIncCard

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
        fGetCard, fGetCount, fGetExpanInfo, oGroupedIter = self.groupedCardIterator(oCardIter)

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
                if self.bEditable:
                    bDecCard = True
                    bIncCard = self.check_inc_card(oCard)
                else:
                    bIncCard = False
                    bDecCard = False
                self.set(oChildIter,
                    0, oCard.name,
                    1, iCnt,
                    2, bIncCard,
                    3, bDecCard
                )
                if self.bExpansions:
                    # fill in the numbers for all possible expansions for
                    # the card
                    dExpansionInfo = self.getExpansionInfo(oCard, fGetExpanInfo(oItem))
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
            oListener.load()

    def check_inc_dec_expansion(self, oCard, sExpansion, iCnt):
        if type(self.basefilter) is PhysicalCardSetFilter:
            if sExpansion != self.sUnknownExpansion:
                iThisExID = [x.expasion.id for x in oCard.rarity if x.expansion.name == sExpansion][0]
                iCardCnt = PhysicalCard.selectBy(abstractCardID=oCard.id,
                        expansionID=iThisExpID).count()
            else:
                iCardCnt = PhysicalCard.selectBy(abstractCardID=oCard.id,
                        expansionID=None).count()
            bDecCard = iCnt > 0
            bIncCard = iCnt < iCardCnt
        else:
            if sExpansion != self.sUnknownExpansion:
                bDecCard = iCnt > 0
                bIncCard = PhysicalCard.selectBy(abstractCardID=oCard.id,
                        expansionID=None).count() > 0
            else:
                bDecCard = False
                bIncCard = False
        return bIncCard, bDecCard

    def getExpansionInfo(self, oCard, dExpanInfo):
        # We always list Unspecfied expansions, even when there
        # are none
        dExpansions = {self.sUnknownExpansion : [0, False, False]}
        dCount = {self.sUnknownExpansion : 0}
        if self.bEditable:
            # All possible expansions listed in the dictionary when editing
            if type(self.basefilter) is PhysicalCardSetFilter:
                for oPC in PhysicalCard.selectBy(abstractCardID=oCard.id):
                    if oPC.expansion is not None:
                        sName = oPC.expansion.name
                    else:
                        sName = self.sUnknownExpansion
                    dExpansions.setdefault(sName, [0, False, False])
                    dCount.setdefault(sName, 0)
                    dCount[sName] += 1
            else:
                # We don't need the join filter's give us, since we have oCard
                iNoneCnt = PhysicalCard.selectBy(abstractCardID=oCard.id,
                        expansionID=None).count()
                for oP in oCard.rarity:
                    dExpansions.setdefault(oP.expansion.name, [0, False, iNoneCnt > 0])
        for oExpansion, iCnt in dExpanInfo.iteritems():
            bDecCard = False
            bIncCard = False
            if oExpansion is not None:
                sKey = oExpansion.name
            else:
                sKey = self.sUnknownExpansion
            if self.bEditable:
                if type(self.basefilter) is PhysicalCardSetFilter:
                    if sKey in dCount.keys():
                        iCardCnt = dCount[sKey]
                    else:
                        iCardCnt = 0
                    bDecCard = iCnt > 0
                    # Cards of the expansion available to select
                    bIncCard = iCnt < iCardCnt 
                else:
                    if oExpansion is not None:
                        bDecCard = iCnt > 0
                        # Can only increase a expansion if there are unknown
                        # cards to move across
                        bIncCard = iNoneCnt > 0
                    # For PhysicalCardList, we never touch Unknown directly
                    # It's manipulated by changing other expansions
            dExpansions[sKey] = [iCnt, bDecCard, bIncCard]
        return dExpansions

    def listenIncCard(self, sCardName, iChg):
        """listen for a IncCard Signal on listenclass"""


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
            aCards = oCardIter
        else:
            fGetCard = lambda x:x[0]
            fGetCount = lambda x:x[1][0]
            fGetExpanInfo = lambda x:x[1][1]

            # Count by Abstract Card
            dAbsCards = {}
            for oCard in oCardIter:
                dAbsCards.setdefault(oCard.abstractCard, [0, {}])
                dAbsCards[oCard.abstractCard][0] += 1
                if self.bExpansions:
                    dExpanInfo = dAbsCards[oCard.abstractCard][1]
                    dExpanInfo.setdefault(oCard.expansion, 0)
                    dExpanInfo[oCard.expansion] += 1

            aCards = list(dAbsCards.iteritems())
            aCards.sort(lambda x, y: cmp(x[0].name, y[0].name))

        # Iterate over groups
        return fGetCard, fGetCount, fGetExpanInfo, self.groupby(aCards, fGetCard)

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
        oIter = self.get_iter(oPath)
        if self.iter_depth(oIter) == 2:
            # Expansion section - we want the card before this
            # according to the docs this is assured to be the
            # correct path to it
            oIter = self.get_iter(norm_path(oPath)[0:2])
        return self.getNameFromIter(oIter)

    def getAllFromPath(self, oPath):
        oIter = self.get_iter(oPath)
        iDepth = self.iter_depth(oIter)
        if iDepth == 2:
            sName = self.getNameFromIter(self.get_iter(norm_path(oPath)[0:2]))
            sExpansion = self.get_value(oIter, 0)
        else:
            sName = self.getNameFromIter(oIter)
            sExpansion = self.sUnknownExpansion
        iCount = self.get_value(oIter, 1)
        return sName, sExpansion, iCount, iDepth

    def getExpansionNameFromPath(self, oPath):
        oIter = self.get_iter(oPath)
        if self.iter_depth(oIter) != 2:
            return None
        return self.getNameFromIter(oIter)

    def getNameFromIter(self, oIter):
        # For some reason the string comes back from the
        # tree store having been encoded *again* despite
        # displaying correctly, so we decode it here.
        # I hope all systems encode with utf-8. :(
        sCardName = self.get_value(oIter, 0).decode("utf-8")
        return sCardName

    def incCard(self, oPath):
        sCardName = self.getCardNameFromPath(oPath)
        self.alterCardCount(sCardName, +1)

    def decCard(self, oPath):
        sCardName = self.getCardNameFromPath(oPath)
        self.alterCardCount(sCardName, -1)

    def incCardExpansionByName(self, sCardName, sExpansion):
        """Increases the expansion count for this card without
           changing total card count. Should be paired with
           calls to incCardByName or decCardExpansionByName for 
           consistency
        """
        if sExpansion is None:
            sExpansion = self.sUnknownExpansion
        if self._dNameExpansion2Iter.has_key(sCardName) and \
                self._dNameExpansion2Iter[sCardName].has_key(sExpansion):
            self.alterCardExpansionCount(sCardName, sExpansion, +1)

    def decCardExpansionByName(self, sCardName, sExpansion):
        """Decreases the expansion count for this card without
           changing total card count. Should be paired with
           calls to decCardByName or incCardExpansionByName for 
           consistency
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

    def alterCardExpansionCount(self, sCardName, sExpansion, iChg):
        # Need to readjust inc, dec flags for all these cards
        oCard = IAbstractCard(sCardName)
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
                self.set(oIter,
                        1, iCnt,
                        2, bIncCard,
                        3, bDecCard)

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
                if self.bEditable:
                    # Same logic as in load
                    bIncCard = self.check_inc_card(oCard)
                    self.set(oIter, 2, bIncCard)
                    self.set(oIter, 3, True)
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

        if iCnt <= 0:
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

        fGetCard, fGetCount, fGetExpanInfo, oGroupedIter = self.groupedCardIterator(oCardIter)

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
                if self.bEditable:
                    bDecCard = True
                    bIncCard = self.check_inc_card(oCard)
                else:
                    bDecCard = False
                    bIncCard = False
                self.set(oChildIter,
                    0, oCard.name,
                    1, iCnt,
                    2, bIncCard,
                    3, bDecCard
                )
                self._dName2Iter.setdefault(oCard.name, []).append(oChildIter)

                if self.bExpansions:
                    # Create Space for children, which alterExpansionCount
                    # calls will sort out the values of
                    self._dNameExpansion2Iter.setdefault(oCard.name,{})
                    if self.bEditable:
                        if type(self.basefilter) is PhysicalCardSetFilter:
                            for oPC in PhysicalCard.selectBy(abstractCardID=oCard.id):
                                if oPC.expansion is not None:
                                    sExpName = oPC.expansion.name
                                else:
                                    sExpName = self.sUnknownExpansion
                                oExpandIter = self.append(oChildIter)
                                self._dNameExpansion2Iter[oCard.name].setdefault(sExpName, []).append(oExpandIter)
                                bIncCard, bDecCard = self.check_inc_dec_expansion(
                                        oCard, sExpName, 0)
                                self.set(oExpandIter,
                                        0, sExpName,
                                        1, 0,
                                        2, bIncCard,
                                        3, bDecCard
                                        )
                        else:
                            aList = [self.sUnknownExpansion] + sorted([oP.expansion.name for oP in oCard.rarity])
                            for sExpName in aList:
                                oExpandIter = self.append(oChildIter)
                                self._dNameExpansion2Iter[oCard.name].setdefault(sExpName, []).append(oExpandIter)
                                bIncCard, bDecCard = self.check_inc_dec_expansion(
                                        oCard, sExpName, 0)
                                self.set(oExpandIter,
                                        0, sExpName,
                                        1, 0,
                                        2, bIncCard,
                                        3, bDecCard
                                        )
                    else:
                        for sExpName, iCnt in fGetExpanInfo(oItem):
                            oExpandIter = self.append(oChildIter)
                            self._dNameExpansion2Iter[oCard.name].setdefault(sExpName, []).append(oExpandIter)
                            self.set(oExpandIter,
                                    0, sExpName,
                                    1, 0)

            # Update Group Section
            self.set(oSectionIter,
                1, iGrpCnt
            )

        # Notify Listeners
        oCard = IAbstractCard(sCardName)
        for oListener in self.listeners:
            oListener.addNewCard(oCard)
