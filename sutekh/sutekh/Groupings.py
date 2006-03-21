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
                for y in self.__fKeys(x):
                    dKeyItem.setdefault(y,[]).append(x)
         
        a = dKeyItem.keys()
        a.sort()
        
        for key in a:
            yield key, dKeyItem[key]        			
			
# Individual Groupings

class CardTypeGrouping(IterGrouping):
    def __init__(self,oIter,fGetCard=lambda x:x):
        super(CardTypeGrouping,self).__init__(oIter,lambda x: [y.name for y in fGetCard(x).cardtype])
	
class ClanGrouping(IterGrouping):
    def __init__(self,oIter,fGetCard=lambda x:x):
        super(ClanGrouping,self).__init__(oIter,lambda x: [y.name for y in fGetCard(x).clan])

class DisciplineGrouping(IterGrouping):
    def __init__(self,oIter,bPhysicalCards=False):
        if not bPhysicalCards:
            super(DisciplineGrouping,self).__init__(oIter,lambda x: [y.name for y in x.clan])
        else:
            super(DisciplineGrouping,self).__init__(oIter,lambda x: [y.name for y in x.abstractCard.clan])

class ExpansionGrouping(IterGrouping):
    def __init__(self,oIter,bPhysicalCards=False):
        if not bPhysicalCards:
            super(DisciplineGrouping,self).__init__(oIter,lambda x: [y.expansion.name for y in x.rarity])
        else:
            super(DisciplineGrouping,self).__init__(oIter,lambda x: [y.expansion.name for y in x.abstractCard.rarity])

class RarityGrouping(IterGrouping):
    def __init__(self,oIter,bPhysicalCards=False):
        if not bPhysicalCards:
            super(DisciplineGrouping,self).__init__(oIter,lambda x: [y.rarity.name for y in x.rarity])
        else:
            super(DisciplineGrouping,self).__init__(oIter,lambda x: [y.rarity.name for y in x.abstractCard.rarity])    
