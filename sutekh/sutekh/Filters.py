from SutekhObjects import *
from sqlobject import AND, OR, LIKE

# Filter Base Class

class Filter(object):
    def getExpression(self):
        raise NotImplementedError

# Collections of Filters
    
class FilterBox(Filter,list):
    pass
    
class FilterAndBox(FilterBox):
    def getExpression(self):
        return AND(*self)
    
class FilterOrBox(FilterBox):
    def getExpression(self):
        return OR(*self)

# Individual Filters

class ClanFilter(Filter):
    pass
    
class DisciplineFilter(Filter):
    pass
    
class CardTypeFilter(Filter):
    pass

class CardTextFilter(Filter):
    def __init__(self,sPattern):
        self.__sPattern = sPattern
        
    def getExpression(self):
        return LIKE(AbstractCard.q.text,'%' + self.__sPattern + '%')
