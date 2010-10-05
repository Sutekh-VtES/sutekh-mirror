# SutekhObjectCache.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Cache various objects used by sutekh to speed up database queries."""

from sutekh.core.SutekhObjects import AbstractCard, RarityPair, Rarity, Clan, \
        Discipline, DisciplinePair, CardType, Expansion, Ruling, Sect, Title, \
        Creed, Virtue, PhysicalCard, Keyword, Artist, init_cache


class SutekhObjectCache(object):
    """Holds references to commonly used database objects so that they don't
       get removed from the cache during big reads.

       Including AbstractCard in the cache gives about a 40% speed up on
       filtering at the cost of using about 3MB extra memory.

       Including Ruling costs about an extra 1MB for no real speed up, but
       we threw it in anyway (on the assumption it may be useful sometime
       in the future).
       """

    def __init__(self):
        aTypesToCache = [Rarity, Expansion, RarityPair, Discipline,
                DisciplinePair, Clan, CardType, AbstractCard, Ruling,
                Creed, Virtue, Sect, Title, PhysicalCard, Keyword,
                Artist]

        self._dCache = {}
        for cType in aTypesToCache:
            self._dCache[cType] = list(cType.select())

        init_cache()
