# CardListModel.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk, gobject
import sets
from sutekh.gui.SQLObjectEvents import IncCardSignal, DecCardSignal
from sutekh.core.Filters import FilterAndBox, SpecificCardFilter, NullFilter, PhysicalExpansionFilter
from sutekh.core.Groupings import CardTypeGrouping
from sutekh.core.SutekhObjects import AbstractCard, IAbstractCard

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

    def alterCardCount(self,oCard,iChg):
        """
        The count of the given card has been altered by iChg.
        oCard: AbstractCard for the card altered (the actual card may be a Physical Card).
        """
        pass

    def addNewCard(self,oCard):
        """
        A single copy of the given card has been added.
        oCard: AbstractCard for the card altered (the actual card may be a Physical Card).
        """
        pass

class CardListModel(gtk.TreeStore):
    """
    Provides a card list specific API for accessing a gtk.TreeStore.
    """

    def __init__(self):
        # STRING is the card name, INT is the card count
        super(CardListModel,self).__init__(gobject.TYPE_STRING,gobject.TYPE_INT,
                gobject.TYPE_BOOLEAN,gobject.TYPE_BOOLEAN)
        self._dName2Iter = {}

        self.cardclass = AbstractCard # card class to use
        self.listenclass = AbstractCard # card class to listen for events on
        self.groupby = CardTypeGrouping # grouping class to use
        self.basefilter = None # base filter defines the card list
        self.applyfilter = False # whether to apply the select filter
        self.selectfilter = None # additional filters for selecting from the list

        self.listeners = {} # dictionary of CardListModelListeners

        self.bExpansions = False
        self.bAllExpansions = False

    store = property(fget=lambda self: self._oGtkStore)
    cardclass = property(fget=lambda self: self._cCardClass, fset=lambda self,x: setattr(self,'_cCardClass',x))
    listenclass = property(fget=lambda self: self._cListenClass, fset=lambda self,x: setattr(self,'_cListenClass',x))
    groupby = property(fget=lambda self: self._cGroupBy, fset=lambda self,x: setattr(self,'_cGroupBy',x))
    basefilter = property(fget=lambda self: self._oBaseFilter, fset=lambda self,x: setattr(self,'_oBaseFilter',x))
    applyfilter = property(fget=lambda self: self._bApplyFilter, fset=lambda self,x: setattr(self,'_bApplyFilter',x))
    selectfilter = property(fget=lambda self: self._oSelectFilter, fset=lambda self,x: setattr(self,'_oSelectFilter',x))

    def addListener(self,oListener):
        self.listeners[oListener] = None

    def removeListener(self,oListener):
        del self.listeners[oListener]

    def load(self):
        """
        Clear and reload the underlying store. For use after initialisation or when
        the filter or grouping changes.
        """
        self.clear()
        self._dName2Iter = {}
        self._dGroupName2Iter = {}

        oCardIter = self.getCardIterator(self.getCurrentFilter())
        fGetCard, fGetCount, oGroupedIter = self.groupedCardIterator(oCardIter)

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
                self.set(oChildIter,
                    0, oCard.name,
                    1, iCnt,
                    2, True,
                    3, True
                )
                if self.bExpansions:
                    # fill in the numbers for all possible expansions for
                    # the card
                    for sExpansion, iExpCnt in self.getExpansionInfo(oCard):
                        oExpansionIter = self.append(oChildIter)
                        self.set(oExpansionIter,
                                0, sExpansion,
                                1, iExpCnt,
                                2, True,
                                3, iExpCnt > 0)
                self._dName2Iter.setdefault(oCard.name,[]).append(oChildIter)

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

    def getExpansionInfo(self, oCard):
        aResult = []
        aExpansions = sets.Set([oP.expansion.name for oP in oCard.rarity]+[None])
        for sExpansion in sorted(aExpansions):
             oFilter = self.combineFilterWithBase(SpecificCardFilter(oCard.name))
             oFullFilter = FilterAndBox([oFilter,PhysicalExpansionFilter(sExpansion)])
             iExpCnt = oFullFilter.select(self.cardclass).distinct().count()
             if self.bAllExpansions or iExpCnt > 0:
                  if sExpansion is None:
                       sExpansion = 'Unspecified Expansion'
                  aResult.append((sExpansion,iExpCnt))
        return aResult

    def listenIncCard(self, sCardName, iChg):
        """listen for a IncCard Signal on listenclass"""


    def getCardIterator(self,oFilter):
        """
        Return an interator over the card model. The filter is
        combined with self.basefilter. None may be used to retrieve
        the entire card list (with only the base filter restriciting which cards appear).
        """
        oFilter = self.combineFilterWithBase(oFilter)

        return oFilter.select(self.cardclass).distinct()

    def groupedCardIterator(self,oCardIter):
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
            aCards = oCardIter
        else:
            fGetCard = lambda x:x[0]
            fGetCount = lambda x:x[1]

            # Count by Abstract Card
            dAbsCards = {}
            for oCard in oCardIter:
                dAbsCards.setdefault(oCard.abstractCard,0)
                dAbsCards[oCard.abstractCard] += 1

            aCards = list(dAbsCards.iteritems())
            aCards.sort(lambda x,y: cmp(x[0].name,y[0].name))

        # Iterate over groups
        return fGetCard, fGetCount, self.groupby(aCards,fGetCard)

    def getCurrentFilter(self):
        if self.applyfilter:
            return self.selectfilter
        else:
            return None

    def combineFilterWithBase(self,oOtherFilter):
        if self.basefilter is None and oOtherFilter is None:
            return NullFilter()
        elif self.basefilter is None:
            return oOtherFilter
        elif oOtherFilter is None:
            return self.basefilter
        else:
            return FilterAndBox([self.basefilter,oOtherFilter])

    def getCardNameFromPath(self,oPath):
        oIter = self.get_iter(oPath)
        if self.iter_depth(oIter) == 2:
            # Expansion section - we want the card before this
            # according to the docs this is assured to be the
            # correct path to it
            oIter = self.get_iter(oPath[0:2])
        return self.getNameFromIter(oIter)

    def getExpansionNameFromPath(self,oPath):
        oIter = self.get_iter(oPath)
        if self.iter_depth(oIter) != 2:
            return None
        return self.getNameFromIter(oIter)

    def getNameFromIter(self,oIter):
        # For some reason the string comes back from the
        # tree store having been encoded *again* despite
        # displaying correctly, so we decode it here.
        # I hope all systems encode with utf-8. :(
        sCardName = self.get_value(oIter,0).decode("utf-8")
        return sCardName

    def incCard(self,oPath):
        sCardName = self.getCardNameFromPath(oPath)
        self.alterCardCount(sCardName,+1)

    def decCard(self,oPath):
        sCardName = self.getCardNameFromPath(oPath)
        self.alterCardCount(sCardName,-1)

    def incCardByName(self,sCardName):
        if self._dName2Iter.has_key(sCardName):
            # card already in the list
            self.alterCardCount(sCardName,+1)
        else:
            # new card
            self.addNewCard(sCardName)

    def alterCardCount(self,sCardName,iChg):
        """
        Alter the card count of a card which is in the
        current list (i.e. in the card set and not filtered
        out) by iChg.
        """
        for oIter in self._dName2Iter[sCardName]:
            oGrpIter = self.iter_parent(oIter)
            iCnt = self.get_value(oIter,1) + iChg
            iGrpCnt = self.get_value(oGrpIter,1) + iChg

            if iCnt > 0:
                self.set(oIter,1,iCnt)
            else:
                self.remove(oIter)

            if iGrpCnt > 0:
                self.set(oGrpIter,1,iGrpCnt)
            else:
                sGroupName = self.get_value(oGrpIter,0)
                del self._dGroupName2Iter[sGroupName]
                self.remove(oGrpIter)

        if iCnt <= 0:
            del self._dName2Iter[sCardName]

        # Notify Listeners
        oCard = IAbstractCard(sCardName)
        for oListener in self.listeners:
            oListener.alterCardCount(oCard,iChg)

    def addNewCard(self,sCardName):
        """
        If the card sCardName is not in the current list
        (i.e. is not in the card set or is filtered out)
        see if it should be filtered out or if it should be
        visible. If it should be visible, add it to the appropriate
        groups.
        """
        oFilter = self.combineFilterWithBase(self.getCurrentFilter())
        oFullFilter = FilterAndBox([SpecificCardFilter(sCardName),oFilter])

        oCardIter = oFullFilter.select(self.cardclass).distinct()

        fGetCard, fGetCount, oGroupedIter = self.groupedCardIterator(oCardIter)

        # Iterate over groups
        for sGroup, oGroupIter in oGroupedIter:
            # Check for null group
            if sGroup is None:
                sGroup = '<< None >>'

            # Find Group Section
            if self._dGroupName2Iter.has_key(sGroup):
                oSectionIter = self._dGroupName2Iter[sGroup]
                iGrpCnt = self.get_value(oSectionIter,1)
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
                self.set(oChildIter,
                    0, oCard.name,
                    1, iCnt
                )
                self._dName2Iter.setdefault(oCard.name,[]).append(oChildIter)

            # Update Group Section
            self.set(oSectionIter,
                1, iGrpCnt
            )

        # Notify Listeners
        oCard = IAbstractCard(sCardName)
        for oListener in self.listeners:
            oListener.addNewCard(oCard)
