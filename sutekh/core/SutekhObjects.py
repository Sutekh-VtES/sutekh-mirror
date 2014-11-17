# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

# pylint: disable=C0111, C0302
# C0111 - No point in docstrings for these classes, really
# C0302 - lots of lines as we want all these related definitions in one file

"""The database definitions and pyprotocols adapters for Sutekh"""

from sutekh.base.core.CachedRelatedJoin import CachedRelatedJoin
from sutekh.core.Abbreviations import (Clans, Creeds, Disciplines, Sects,
                                       Titles, Virtues)
from sutekh.base.core.BaseObjects import (AbstractCard, BaseObjectMaker,
                                          IAbstractCard, Adapter,
                                          BASE_TABLE_LIST, MAX_ID_LENGTH,
                                          StrAdaptMeta)

# pylint: disable=E0611
# pylint doesn't parse sqlobject's column declaration magic correctly
from sqlobject import (SQLObject, IntCol, UnicodeCol, RelatedJoin,
                       EnumCol, MultipleJoin, DatabaseIndex, ForeignKey,
                       SQLObjectNotFound)
# pylint: enable=E0611
from protocols import advise, Interface


# Interfaces
class IDisciplinePair(Interface):
    pass


class IDiscipline(Interface):
    pass


class IClan(Interface):
    pass


class ISect(Interface):
    pass


class ITitle(Interface):
    pass


class ICreed(Interface):
    pass


class IVirtue(Interface):
    pass


# pylint: enable=C0321
# Table Objects

# pylint: disable=W0232, R0902, W0201, C0103
# W0232: Most of the classes defined here don't have __init__ methods by design
# R0902: We aren't worried about the number of insance variables
# W0201: We don't care about attributes defined outside init, by design
# C0103: We use different naming conventions for the table columns


class SutekhAbstractCard(AbstractCard):
    """The abstract card specialised to the needs of VtES."""

    _inheritable = False
    tableversion = 1

    search_text = UnicodeCol(default="")
    group = IntCol(default=None, dbName='grp')
    capacity = IntCol(default=None)
    cost = IntCol(default=None)
    life = IntCol(default=None)
    costtype = EnumCol(enumValues=['pool', 'blood', 'conviction', None],
                       default=None)
    level = EnumCol(enumValues=['advanced', None], default=None)

    # Most of these names are singular when they should be plural
    # since they refer to lists. We've decided to live with the
    # inconsistency for old columns but do the right thing for new
    # ones.
    discipline = CachedRelatedJoin(
        'DisciplinePair', intermediateTable='abs_discipline_pair_map',
        joinColumn="abstract_card_id", createRelatedTable=False)
    clan = CachedRelatedJoin('Clan', joinColumn="abstract_card_id",
                             intermediateTable='abs_clan_map',
                             createRelatedTable=False)
    sect = CachedRelatedJoin('Sect', intermediateTable='abs_sect_map',
                             joinColumn="abstract_card_id",
                             createRelatedTable=False)
    title = CachedRelatedJoin('Title', intermediateTable='abs_title_map',
                              joinColumn="abstract_card_id",
                              createRelatedTable=False)
    creed = CachedRelatedJoin('Creed', intermediateTable='abs_creed_map',
                              joinColumn="abstract_card_id",
                              createRelatedTable=False)
    virtue = CachedRelatedJoin('Virtue', intermediateTable='abs_virtue_map',
                               joinColumn="abstract_card_id",
                               createRelatedTable=False)


class DisciplinePair(SQLObject):
    advise(instancesProvide=[IDisciplinePair])

    tableversion = 1
    discipline = ForeignKey('Discipline')
    level = EnumCol(enumValues=['inferior', 'superior'])
    disciplineLevelIndex = DatabaseIndex(discipline, level, unique=True)
    cards = RelatedJoin('SutekhAbstractCard',
                        intermediateTable='abs_discipline_pair_map',
                        otherColumn="abstract_card_id",
                        createRelatedTable=False)


class Discipline(SQLObject):
    advise(instancesProvide=[IDiscipline])

    tableversion = 3
    name = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    fullname = UnicodeCol(default=None)
    pairs = MultipleJoin('DisciplinePair')


class Virtue(SQLObject):
    advise(instancesProvide=[IVirtue])

    tableversion = 2
    name = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    fullname = UnicodeCol(default=None)
    cards = RelatedJoin('SutekhAbstractCard',
                        intermediateTable='abs_virtue_map',
                        otherColumn="abstract_card_id",
                        createRelatedTable=False)


class Creed(SQLObject):
    advise(instancesProvide=[ICreed])

    tableversion = 2
    name = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    shortname = UnicodeCol(default=None)
    cards = RelatedJoin('SutekhAbstractCard',
                        intermediateTable='abs_creed_map',
                        otherColumn="abstract_card_id",
                        createRelatedTable=False)


class Clan(SQLObject):
    advise(instancesProvide=[IClan])

    tableversion = 3
    name = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    shortname = UnicodeCol(default=None)
    cards = RelatedJoin('SutekhAbstractCard',
                        intermediateTable='abs_clan_map',
                        otherColumn="abstract_card_id",
                        createRelatedTable=False)


class Sect(SQLObject):
    advise(instancesProvide=[ISect])

    tableversion = 2
    name = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    cards = RelatedJoin('SutekhAbstractCard',
                        intermediateTable='abs_sect_map',
                        otherColumn="abstract_card_id",
                        createRelatedTable=False)


class Title(SQLObject):
    advise(instancesProvide=[ITitle])

    tableversion = 2
    name = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    cards = RelatedJoin('SutekhAbstractCard',
                        intermediateTable='abs_title_map',
                        otherColumn="abstract_card_id",
                        createRelatedTable=False)


# Mapping Tables


class MapAbstractCardToClan(SQLObject):
    class sqlmeta:
        table = 'abs_clan_map'

    tableversion = 1

    abstractCard = ForeignKey('SutekhAbstractCard', notNull=True)
    clan = ForeignKey('Clan', notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard, unique=False)
    clanIndex = DatabaseIndex(clan, unique=False)


class MapAbstractCardToDisciplinePair(SQLObject):
    class sqlmeta:
        table = 'abs_discipline_pair_map'

    tableversion = 1

    abstractCard = ForeignKey('SutekhAbstractCard', notNull=True)
    disciplinePair = ForeignKey('DisciplinePair', notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard, unique=False)
    disciplinePairIndex = DatabaseIndex(disciplinePair, unique=False)


class MapAbstractCardToSect(SQLObject):
    class sqlmeta:
        table = 'abs_sect_map'

    tableversion = 1

    abstractCard = ForeignKey('SutekhAbstractCard', notNull=True)
    sect = ForeignKey('Sect', notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard, unique=False)
    sectIndex = DatabaseIndex(sect, unique=False)


class MapAbstractCardToTitle(SQLObject):
    class sqlmeta:
        table = 'abs_title_map'

    tableversion = 1

    abstractCard = ForeignKey('SutekhAbstractCard', notNull=True)
    title = ForeignKey('Title', notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard, unique=False)
    titleIndex = DatabaseIndex(title, unique=False)


class MapAbstractCardToCreed(SQLObject):
    class sqlmeta:
        table = 'abs_creed_map'

    tableversion = 1

    abstractCard = ForeignKey('SutekhAbstractCard', notNull=True)
    creed = ForeignKey('Creed', notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard, unique=False)
    creedIndex = DatabaseIndex(creed, unique=False)


class MapAbstractCardToVirtue(SQLObject):
    class sqlmeta:
        table = 'abs_virtue_map'

    tableversion = 1

    abstractCard = ForeignKey('SutekhAbstractCard', notNull=True)
    virtue = ForeignKey('Virtue', notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard, unique=False)
    virtueIndex = DatabaseIndex(virtue, unique=False)


# pylint: enable=W0232, R0902, W0201, C0103

# List of Tables to be created, dropped, etc.

TABLE_LIST = BASE_TABLE_LIST + [SutekhAbstractCard,
                                Discipline, DisciplinePair,
                                Clan, Sect, Title, Virtue, Creed,
                                # Mapping tables from here on out
                                MapAbstractCardToClan,
                                MapAbstractCardToDisciplinePair,
                                MapAbstractCardToSect,
                                MapAbstractCardToTitle,
                                MapAbstractCardToVirtue,
                                MapAbstractCardToCreed,
                               ]

# Generically useful constant
CRYPT_TYPES = ('Vampire', 'Imbued')


# Object Maker API
class SutekhObjectMaker(BaseObjectMaker):
    """Creates all kinds of SutekhObjects from simple strings.

       All the methods will return either a copy of an existing object
       or a new object.
       """
    # pylint: disable=R0201, R0913
    # we want SutekhObjectMaker self-contained, so these are all methods.
    # This needs all these arguments
    def make_clan(self, sClan):
        return self._make_object(Clan, IClan, Clans, sClan, bShortname=True)

    def make_creed(self, sCreed):
        return self._make_object(Creed, ICreed, Creeds, sCreed,
                                 bShortname=True)

    def make_discipline(self, sDis):
        return self._make_object(Discipline, IDiscipline, Disciplines, sDis,
                                 bFullname=True)

    def make_sect(self, sSect):
        return self._make_object(Sect, ISect, Sects, sSect)

    def make_title(self, sTitle):
        return self._make_object(Title, ITitle, Titles, sTitle)

    def make_virtue(self, sVirtue):
        return self._make_object(Virtue, IVirtue, Virtues, sVirtue,
                                 bFullname=True)

    def make_abstract_card(self, sCard):
        try:
            return IAbstractCard(sCard)
        except SQLObjectNotFound:
            sName = sCard.strip()
            sCanonical = sName.lower()
            return SutekhAbstractCard(canonicalName=sCanonical,
                                      name=sName, text="")

    def make_discipline_pair(self, sDiscipline, sLevel):
        try:
            return IDisciplinePair((sDiscipline, sLevel))
        except SQLObjectNotFound:
            oDis = self.make_discipline(sDiscipline)
            return DisciplinePair(discipline=oDis, level=sLevel)


# Abbreviation lookup based adapters
class ClanAdapter(Adapter):
    # pylint: disable=E1101
    # metaclass confuses pylint
    __metaclass__ = StrAdaptMeta
    advise(instancesProvide=[IClan], asAdapterForTypes=[basestring])

    def __new__(cls, sName):
        return cls.fetch(Clans.canonical(sName), Clan)


class CreedAdapter(Adapter):
    # pylint: disable=E1101
    # metaclass confuses pylint
    __metaclass__ = StrAdaptMeta
    advise(instancesProvide=[ICreed], asAdapterForTypes=[basestring])

    def __new__(cls, sName):
        return cls.fetch(Creeds.canonical(sName), Creed)


class DisciplineAdapter(Adapter):
    # pylint: disable=E1101
    # metaclass confuses pylint
    __metaclass__ = StrAdaptMeta
    advise(instancesProvide=[IDiscipline], asAdapterForTypes=[basestring])

    def __new__(cls, sName):
        return cls.fetch(Disciplines.canonical(sName), Discipline)


class SectAdapter(Adapter):
    # pylint: disable=E1101
    # metaclass confuses pylint
    __metaclass__ = StrAdaptMeta
    advise(instancesProvide=[ISect], asAdapterForTypes=[basestring])

    def __new__(cls, sName):
        return cls.fetch(Sects.canonical(sName), Sect)


class TitleAdapter(Adapter):
    # pylint: disable=E1101
    # metaclass confuses pylint
    __metaclass__ = StrAdaptMeta
    advise(instancesProvide=[ITitle], asAdapterForTypes=[basestring])

    def __new__(cls, sName):
        return cls.fetch(Titles.canonical(sName), Title)


class VirtueAdapter(Adapter):
    # pylint: disable=E1101
    # metaclass confuses pylint
    __metaclass__ = StrAdaptMeta
    advise(instancesProvide=[IVirtue], asAdapterForTypes=[basestring])

    def __new__(cls, sName):
        return cls.fetch(Virtues.canonical(sName), Virtue)

# Other Adapters


class DisciplinePairAdapter(Adapter):
    advise(instancesProvide=[IDisciplinePair], asAdapterForTypes=[tuple])

    __dCache = {}

    @classmethod
    def make_object_cache(cls):
        cls.__dCache = {}

    def __new__(cls, tData):
        # pylint: disable=E1101
        # adapters confuses pylint
        oDis = IDiscipline(tData[0])
        sLevel = str(tData[1])

        oPair = cls.__dCache.get((oDis.id, sLevel), None)
        if oPair is None:
            oPair = DisciplinePair.selectBy(discipline=oDis,
                                            level=sLevel).getOne()
            cls.__dCache[(oDis.id, sLevel)] = oPair

        return oPair
