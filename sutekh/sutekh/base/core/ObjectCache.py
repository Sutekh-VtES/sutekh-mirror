# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Base class for the generic database object cache."""


from .BaseTables import (AbstractCard, RarityPair, Rarity, CardType,
                         Expansion, Ruling, PhysicalCard, Keyword, Artist)
from .DBUtility import init_cache


class ObjectCache:
    """Holds references to commonly used database objects so that they don't
       get removed from the cache during big reads.

       Including AbstractCard in the cache gives about a 40% speed up on
       filtering at the cost of using about 3MB extra memory.

       Including Ruling costs about an extra 1MB for no real speed up, but
       we threw it in anyway (on the assumption it may be useful sometime
       in the future).
       """

    def __init__(self, aExtraTypesToCache):
        self._dCache = {}
        aTypesToCache = [Rarity, Expansion, RarityPair, CardType,
                         Ruling, Keyword, Artist, AbstractCard,
                         PhysicalCard] + aExtraTypesToCache
        for cType in aTypesToCache:
            self._dCache[cType] = list(cType.select())

        init_cache()
