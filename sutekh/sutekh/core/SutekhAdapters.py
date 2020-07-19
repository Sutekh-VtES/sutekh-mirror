# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""The singledispatch adapters for Sutekh"""

from functools import singledispatch

from sutekh.base.core.BaseAdapters import (Adapter, StrAdaptMeta,
                                           fail_adapt, passthrough)

from sutekh.core.SutekhTables import (Clan, Creed, Discipline, DisciplinePair,
                                      Sect, Title, Virtue)
from sutekh.core.Abbreviations import (Clans, Creeds, Disciplines, Sects,
                                       Titles, Virtues)


# pylint: disable=missing-docstring
# Not a lot of value to docstrings for these classes and methods
# Default adapters
@singledispatch
def IDisciplinePair(oUnknown):
    """Default DisplincePair adapter"""
    return fail_adapt(oUnknown, 'DisciplinePair')


@singledispatch
def IDiscipline(oUnknown):
    """Default Displince adapter"""
    return fail_adapt(oUnknown, 'Discipline')


@singledispatch
def IClan(oUnknown):
    """Default Clan adapter"""
    return fail_adapt(oUnknown, 'Clan')


@singledispatch
def ISect(oUnknown):
    """Default Sect adapter"""
    return fail_adapt(oUnknown, 'Sect')


@singledispatch
def ITitle(oUnknown):
    """Default Title adapter"""
    return fail_adapt(oUnknown, 'Title')


@singledispatch
def ICreed(oUnknown):
    """Default Creed adapter"""
    return fail_adapt(oUnknown, 'Creed')


@singledispatch
def IVirtue(oUnknown):
    """Default Virtue adapter"""
    return fail_adapt(oUnknown, 'Virtue')


# Abbreviation lookup based adapters
class ClanAdapter(Adapter, metaclass=StrAdaptMeta):

    @classmethod
    def lookup(cls, sName):
        return cls.fetch(Clans.canonical(sName), Clan)


IClan.register(Clan, passthrough)

IClan.register(str, ClanAdapter.lookup)


class CreedAdapter(Adapter, metaclass=StrAdaptMeta):

    @classmethod
    def lookup(cls, sName):
        return cls.fetch(Creeds.canonical(sName), Creed)


ICreed.register(Creed, passthrough)

ICreed.register(str, CreedAdapter.lookup)


class DisciplineAdapter(Adapter, metaclass=StrAdaptMeta):

    @classmethod
    def lookup(cls, sName):
        return cls.fetch(Disciplines.canonical(sName), Discipline)


IDiscipline.register(Discipline, passthrough)

IDiscipline.register(str, DisciplineAdapter.lookup)


class SectAdapter(Adapter, metaclass=StrAdaptMeta):

    @classmethod
    def lookup(cls, sName):
        return cls.fetch(Sects.canonical(sName), Sect)


ISect.register(Sect, passthrough)

ISect.register(str, SectAdapter.lookup)


class TitleAdapter(Adapter, metaclass=StrAdaptMeta):

    @classmethod
    def lookup(cls, sName):
        return cls.fetch(Titles.canonical(sName), Title)


ITitle.register(Title, passthrough)

ITitle.register(str, TitleAdapter.lookup)


class VirtueAdapter(Adapter, metaclass=StrAdaptMeta):

    @classmethod
    def lookup(cls, sName):
        return cls.fetch(Virtues.canonical(sName), Virtue)


IVirtue.register(Virtue, passthrough)

IVirtue.register(str, VirtueAdapter.lookup)

# Other Adapters


class DisciplinePairAdapter(Adapter):

    __dCache = {}

    @classmethod
    def make_object_cache(cls):
        cls.__dCache = {}

    @classmethod
    def lookup(cls, tData):
        # pylint: disable=no-member
        # adapters confuses pylint
        oDis = IDiscipline(tData[0])
        sLevel = str(tData[1])

        oPair = cls.__dCache.get((oDis.id, sLevel), None)
        if oPair is None:
            oPair = DisciplinePair.selectBy(discipline=oDis,
                                            level=sLevel).getOne()
            cls.__dCache[(oDis.id, sLevel)] = oPair

        return oPair


IDisciplinePair.register(DisciplinePair, passthrough)

IDisciplinePair.register(tuple, DisciplinePairAdapter.lookup)
