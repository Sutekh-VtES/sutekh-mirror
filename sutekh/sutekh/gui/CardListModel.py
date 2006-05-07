# CardListModel.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk, gobject
from Filters import *
from Groupings import *
from SutekhObjects import *

class CardListModel(gtk.TreeStore):
    """
    Provides a card list specific API for accessing a gtk.TreeStore.
    """
    
    def __init__(self):
        # STRING is the card name, INT is the card count
        super(CardListModel,self).__init__(gobject.TYPE_STRING,gobject.TYPE_INT)
        
        self.cardclass = AbstractCard # card class to use, or option is PhysicalCard
        self.groupby = CardTypeGrouping # grouping class to use
        self.basefilter = None # base filter defines the card list
        self.applyfilter = False # whether to apply the select filter
        self.selectfilter = None # additional filters for selecting from the list
           
    store = property(fget=lambda self: self._oGtkStore)
    cardclass = property(fget=lambda self: self._cCardClass, fset=lambda self,x: setattr(self,'_cCardClass',x)) 
    groupby = property(fget=lambda self: self._cGroupBy, fset=lambda self,x: setattr(self,'_cGroupBy',x))
    basefilter = property(fget=lambda self: self._oBaseFilter, fset=lambda self,x: setattr(self,'_oBaseFilter',x))
    applyfilter = property(fget=lambda self: self._bApplyFilter, fset=lambda self,x: setattr(self,'_bApplyFilter',x))
    selectfilter = property(fget=lambda self: self._oSelectFilter, fset=lambda self,x: setattr(self,'_oSelectFilter',x))

    def load(self):
        """
        Clear and reload the underlying store. For use after initialisation or when
        the filter or grouping changes.
        """
        self.clear()

        oFilter = self.getCompleteFilterExpression()		
        oCardIter = self.cardclass.select(oFilter).distinct()

        # Define iterable and grouping function based on cardclass
        if self.cardclass is PhysicalCard:
            fGetCard = lambda x:x[0]
            fGetCount = lambda x:x[1]
            
            # Count by Abstract Card
            dAbsCards = {}
            for oCard in oCardIter:
                dAbsCards.setdefault(oCard.abstractCard,0)
                dAbsCards[oCard.abstractCard] += 1

            aCards = list(dAbsCards.iteritems())
            aCards.sort(lambda x,y: cmp(x[0].name,y[0].name))
        else:
            fGetCard = lambda x:x
            fGetCount = lambda x:0            
            aCards = oCardIter
 		
        # Iterate over groups
        for sGroup, oGroupIter in self.groupby(aCards,fGetCard):
            # Check for null group
            if sGroup is None:
                sGroup = '<< None >>'
        		
            # Create Group Section
            oSectionIter = self.append(None)
			
            # Fill in Cards
            iGrpCnt = 0
            for oItem in oGroupIter:
                oCard, iCnt = fGetCard(oItem), fGetCount(oItem)
                iGrpCnt += iCnt
                oChildIter = self.append(oSectionIter)
                self.set(oChildIter,
                    0, oCard.name,
                    1, iCnt
                )
                
            # Update Group Section
            self.set(oSectionIter,
                0, sGroup,
                1, iGrpCnt
            )

    def getCompleteFilterExpression(self):
        if self.basefilter is None:
            if not self.applyfilter or self.selectfilter is None:
                return None
            else:
                return self.selectfilter.getExpression()
        else:
            if not self.applyfilter or self.selectfilter is None:
                return self.basefilter.getExpression()
            else:
                return FilterAndBox([self.basefilter,self.selectfilter]).getExpression()            

    def getCardNameFromPath(self,oPath):
        oIter = self.get_iter(oPath)
        return self.getCardNameFromIter(oIter)
        
    def getCardNameFromIter(self,oIter):
        sCardName = self.get_value(oIter,0)
        return sCardName
        
    def incCard(self,oPath):
        oIter = self.get_iter(oPath)
        oGrpIter = self.iter_parent(oIter)
        
        iCnt = self.get_value(oIter,1)
        self.set(oIter,1,iCnt+1)
        
        iGrpCnt = self.get_value(oGrpIter,1)        
        self.set(oGrpIter,1,iGrpCnt+1)
        
    def decCard(self,oPath):
        oIter = self.get_iter(oPath)
        oGrpIter = self.iter_parent(oIter)
        
        iCnt = self.get_value(oIter,1)
        if iCnt > 1:
            self.set(oIter,1,iCnt-1)
        else:
            self.remove(oIter)
        
        iGrpCnt = self.get_value(oGrpIter,1)
        if iGrpCnt > 1:
            self.set(oGrpIter,1,iGrpCnt-1)
        else:
            self.remove(oGrpIter)
