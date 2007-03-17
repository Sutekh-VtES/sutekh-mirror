# SutekhObjects.py
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

from sutekh.SutekhObjects import *

class SutekhObjectCache(object):
    """Holds references to commonly used database objects so that they don't get
       removed from the cache during big reads.
       
       Including AbstractCard in the cache gives about a 40% speed up on
       filtering at the cost of using about 3MB extra memory.
       
       Including Ruling costs about an extra 1MB for no real speed up, but
       we threw it in anyway (on the assumption it may be useful sometime
       in the future).
       """

    def __init__(self):
        aTypesToCache = [ RarityPair, Rarity, DisciplinePair, Discipline,
                          Clan, CardType, Expansion, AbstractCard, Ruling ]

        self._dCache = {}
        for cType in aTypesToCache:
            self._dCache[cType] = list(cType.select())
