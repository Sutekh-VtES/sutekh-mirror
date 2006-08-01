# Groupings.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

from SutekhObjects import *
from sqlobject import AND, OR, LIKE
from sqlobject.sqlbuilder import Table

# Base Grouping Class

class IterGrouping(object):
    def __init__(self,oIter,fKeys):
        """
        oIter: Iterable to group.
        fKeys: Function which maps an item from the iterable
               to a list of keys. Keys must be hashable.
        """
        self.__oIter = oIter
        self.__fKeys = fKeys

    def __iter__(self):
        dKeyItem = {}
        for x in self.__oIter:
            a = self.__fKeys(x)
            if len(a) == 0:
                dKeyItem.setdefault(None,[]).append(x)
            else:
                for y in a:
                    dKeyItem.setdefault(y,[]).append(x)
         
        a = dKeyItem.keys()
        a.sort()
        
        for key in a:
            yield key, dKeyItem[key]        			
			
# Individual Groupings
#
# If you need to group PhysicalCards,
# set fGetCard to lambda x: x.abstractCard

class CardTypeGrouping(IterGrouping):
    def __init__(self,oIter,fGetCard=lambda x:x):
        super(CardTypeGrouping,self).__init__(oIter,lambda x: [y.name for y in fGetCard(x).cardtype])
	
class ClanGrouping(IterGrouping):
    def __init__(self,oIter,fGetCard=lambda x:x):
        super(ClanGrouping,self).__init__(oIter,lambda x: [y.name for y in fGetCard(x).clan])

class DisciplineGrouping(IterGrouping):
    def __init__(self,oIter,fGetCard=lambda x:x):
        super(DisciplineGrouping,self).__init__(oIter,lambda x: [y.name for y in fGetCard(x).clan])

class ExpansionGrouping(IterGrouping):
    def __init__(self,oIter,fGetCard=lambda x:x):
        super(ExpansionGrouping,self).__init__(oIter,lambda x: [y.expansion.name for y in fGetCard(x).rarity])

class RarityGrouping(IterGrouping):
    def __init__(self,oIter,fGetCard=lambda x:x):
        super(RarityGrouping,self).__init__(oIter,lambda x: [y.rarity.name for y in fGetCard(x).rarity])
