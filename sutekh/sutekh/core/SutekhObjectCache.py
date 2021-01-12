# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Cache various objects used by sutekh to speed up database queries."""

from sutekh.core.SutekhTables import (SutekhAbstractCard, Clan,
                                      Discipline, DisciplinePair, Sect,
                                      Title, Creed, Virtue)
from sutekh.base.core.ObjectCache import ObjectCache


class SutekhObjectCache(ObjectCache):
    """Add Sutekh specific classes to the generic database cache.
       """

    def __init__(self):
        aExtraTypesToCache = [Discipline, DisciplinePair, Clan,
                              Creed, Virtue, Sect, Title,
                              SutekhAbstractCard]
        super().__init__(aExtraTypesToCache)
