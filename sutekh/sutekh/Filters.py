from SutekhObjects import *
from sqlobject import AND, OR, LIKE
from sqlobject.sqlbuilder import Table

# Filter Base Class

class Filter(object):
    def getExpression(self):
        raise NotImplementedError

# Collections of Filters
    
class FilterBox(Filter,list):
    pass
    
class FilterAndBox(FilterBox):
    def getExpression(self):
        return AND(*[x.getExpression() for x in self])
    
class FilterOrBox(FilterBox):
    def getExpression(self):
        return OR(*[x.getExpression() for x in self])

# Individual Filters

class ClanFilter(Filter):
    def __init__(self,sClan):
        self.__oClan = IClan(sClan)
        
    def getExpression(self):
        oT = Table('abs_clan_map')
        return AND(AbstractCard.q.id == oT.abstract_card_id,
                   oT.clan_id == self.__oClan.id)
    
class DisciplineFilter(Filter):
    def __init__(self,sDiscipline):
        self.__oDis = IDiscipline(sDiscipline)
        
    def getExpression(self):
        oT = Table('abs_discipline_pair_map')
        return AND(AbstractCard.q.id == oT.abstract_card_id,
                   oT.discipline_pair_id == DisciplinePair.q.id,
                   DisciplinePair.q.disciplineID == self.__oDis.id)
    
class CardTypeFilter(Filter):
    def __init__(self,sCardType):
        self.__oType = ICardType(sCardType)
        
    def getExpression(self):
        oT = Table('abs_type_map')
        return AND(AbstractCard.q.id == oT.abstract_card_id,
                   oT.card_type_id == self.__oType.id)

class CardTextFilter(Filter):
    def __init__(self,sPattern):
        self.__sPattern = sPattern
        
    def getExpression(self):
        return LIKE(AbstractCard.q.text,'%' + self.__sPattern + '%')
