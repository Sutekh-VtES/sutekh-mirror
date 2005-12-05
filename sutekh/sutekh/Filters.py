from SutekhObjects import *

# Filter Base Class

class Filter(object):
    pass

# Collections of Filters
    
class FilterBox(Filter):
    pass
    
class FilterAndBox(FilterBox):
    pass
    
class FilterOrBox(FilterBox):
    pass

# Individual Filters

class ClanFilter(Filter):
    pass
    
class DisciplineFilter(Filter):
    pass
    
class CardTypeFilter(Filter):
    pass
