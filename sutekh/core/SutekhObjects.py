# SutekhObjects.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

# pylint: disable-msg=C0111, C0321, C0302
# C0111 - No point in docstrings for these classes, really
# C0321 - Compactness of single line definitions is good here
# C0302 - lots of lines as we want all these related definitions in one file

"""The database definitions and pyprotocols adaptors for Sutekh"""

from sutekh.core.CachedRelatedJoin import CachedRelatedJoin, \
        SOCachedRelatedJoin
from sutekh.core.Abbreviations import CardTypes, Clans, Creeds, Disciplines, \
        Expansions, Rarities, Sects, Titles, Virtues
# pylint: disable-msg=E0611
# pylint doesn't parse sqlobject's column declaration magic correctly
from sqlobject import sqlmeta, SQLObject, IntCol, UnicodeCol, RelatedJoin, \
       EnumCol, MultipleJoin, BoolCol, DatabaseIndex, ForeignKey, \
       SQLObjectNotFound
# pylint: enable-msg=E0611
from protocols import advise, Interface

# Interfaces


class IAbstractCard(Interface): pass


class IPhysicalCard(Interface): pass


class IPhysicalCardSet(Interface): pass


class IRarityPair(Interface): pass


class IExpansion(Interface): pass


class IExpansionName(Interface): pass


class IRarity(Interface): pass


class IDisciplinePair(Interface): pass


class IDiscipline(Interface): pass


class IClan(Interface): pass


class ICardType(Interface): pass


class ISect(Interface): pass


class ITitle(Interface): pass


class ICreed(Interface): pass


class IVirtue(Interface): pass


class IRuling(Interface): pass


class IArtist(Interface): pass


class IKeyword(Interface): pass

# pylint: enable-msg=C0321
# Table Objects

# pylint: disable-msg=W0232, R0902, W0201, C0103
# W0232: Most of the classes defined here don't have __init__ methods by design
# R0902: We aren't worried about the number of insance variables
# W0201: We don't care about attributes defined outside init, by design
# C0103: We use different naming conventions for the table columns

# We try to avoid limiting the length of unicode columns but we have
# to provide a length for alternate id columns and index columns.
# For these we default to 512 characters.

MAX_ID_LENGTH = 512


class VersionTable(SQLObject):
    TableName = UnicodeCol(alternateID=True, length=50)
    Version = IntCol(default=None)
    tableversion = 1


class AbstractCard(SQLObject):
    advise(instancesProvide=[IAbstractCard])

    tableversion = 5
    sqlmeta.lazyUpdate = True

    canonicalName = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    name = UnicodeCol()
    text = UnicodeCol()
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
    discipline = CachedRelatedJoin('DisciplinePair',
            intermediateTable='abs_discipline_pair_map',
            createRelatedTable=False)
    rarity = CachedRelatedJoin('RarityPair',
            intermediateTable='abs_rarity_pair_map',
            createRelatedTable=False)
    clan = CachedRelatedJoin('Clan',
            intermediateTable='abs_clan_map', createRelatedTable=False)
    cardtype = CachedRelatedJoin('CardType', intermediateTable='abs_type_map',
            createRelatedTable=False)
    sect = CachedRelatedJoin('Sect', intermediateTable='abs_sect_map',
            createRelatedTable=False)
    title = CachedRelatedJoin('Title', intermediateTable='abs_title_map',
            createRelatedTable=False)
    creed = CachedRelatedJoin('Creed', intermediateTable='abs_creed_map',
            createRelatedTable=False)
    virtue = CachedRelatedJoin('Virtue', intermediateTable='abs_virtue_map',
            createRelatedTable=False)
    rulings = CachedRelatedJoin('Ruling', intermediateTable='abs_ruling_map',
            createRelatedTable=False)
    artists = CachedRelatedJoin('Artist', intermediateTable='abs_artist_map',
            createRelatedTable=False)
    keywords = CachedRelatedJoin('Keyword',
            intermediateTable='abs_keyword_map', createRelatedTable=False)

    physicalCards = MultipleJoin('PhysicalCard')


class PhysicalCard(SQLObject):
    advise(instancesProvide=[IPhysicalCard])

    tableversion = 2
    abstractCard = ForeignKey('AbstractCard')
    abstractCardIndex = DatabaseIndex(abstractCard)
    # Explicitly allow None as expansion
    expansion = ForeignKey('Expansion', notNull=False)
    sets = RelatedJoin('PhysicalCardSet', intermediateTable='physical_map',
            createRelatedTable=False)


class PhysicalCardSet(SQLObject):
    advise(instancesProvide=[IPhysicalCardSet])

    tableversion = 6
    name = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    author = UnicodeCol(default='')
    comment = UnicodeCol(default='')
    annotations = UnicodeCol(default='')
    inuse = BoolCol(default=False)
    parent = ForeignKey('PhysicalCardSet', default=None)
    cards = RelatedJoin('PhysicalCard', intermediateTable='physical_map',
            createRelatedTable=False)


class RarityPair(SQLObject):
    advise(instancesProvide=[IRarityPair])

    tableversion = 1
    expansion = ForeignKey('Expansion')
    rarity = ForeignKey('Rarity')
    cards = RelatedJoin('AbstractCard',
            intermediateTable='abs_rarity_pair_map', createRelatedTable=False)
    expansionRarityIndex = DatabaseIndex(expansion, rarity, unique=True)


class Expansion(SQLObject):
    advise(instancesProvide=[IExpansion])

    tableversion = 3
    name = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    shortname = UnicodeCol(default=None)
    pairs = MultipleJoin('RarityPair')


class Rarity(SQLObject):
    advise(instancesProvide=[IRarity])

    tableversion = 3
    name = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    shortname = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)


class DisciplinePair(SQLObject):
    advise(instancesProvide=[IDisciplinePair])

    tableversion = 1
    discipline = ForeignKey('Discipline')
    level = EnumCol(enumValues=['inferior', 'superior'])
    disciplineLevelIndex = DatabaseIndex(discipline, level, unique=True)
    cards = RelatedJoin('AbstractCard',
            intermediateTable='abs_discipline_pair_map',
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
    cards = RelatedJoin('AbstractCard', intermediateTable='abs_virtue_map',
            createRelatedTable=False)


class Creed(SQLObject):
    advise(instancesProvide=[ICreed])

    tableversion = 2
    name = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    shortname = UnicodeCol(default=None)
    cards = RelatedJoin('AbstractCard', intermediateTable='abs_creed_map',
            createRelatedTable=False)


class Clan(SQLObject):
    advise(instancesProvide=[IClan])

    tableversion = 3
    name = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    shortname = UnicodeCol(default=None)
    cards = RelatedJoin('AbstractCard', intermediateTable='abs_clan_map',
            createRelatedTable=False)


class CardType(SQLObject):
    advise(instancesProvide=[ICardType])

    tableversion = 2
    name = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    cards = RelatedJoin('AbstractCard', intermediateTable='abs_type_map',
            createRelatedTable=False)


class Sect(SQLObject):
    advise(instancesProvide=[ISect])

    tableversion = 2
    name = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    cards = RelatedJoin('AbstractCard', intermediateTable='abs_sect_map',
            createRelatedTable=False)


class Title(SQLObject):
    advise(instancesProvide=[ITitle])

    tableversion = 2
    name = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    cards = RelatedJoin('AbstractCard', intermediateTable='abs_title_map',
            createRelatedTable=False)


class Ruling(SQLObject):
    advise(instancesProvide=[IRuling])

    tableversion = 2
    text = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    code = UnicodeCol()
    url = UnicodeCol(default=None)
    cards = RelatedJoin('AbstractCard', intermediateTable='abs_ruling_map',
            createRelatedTable=False)


class Artist(SQLObject):
    advise(instancesProvide=[IArtist])

    tableversion = 1
    canonicalName = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    name = UnicodeCol()
    cards = RelatedJoin('AbstractCard', intermediateTable='abs_artist_map',
            createRelatedTable=False)


class Keyword(SQLObject):
    advise(instancesProvide=[IKeyword])

    # For sanity, avoid keywords with commas since this is the preferred
    # character for separating lists of keywords when displaying them
    # to a user in a compact way.

    tableversion = 1
    keyword = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    cards = RelatedJoin('AbstractCard', intermediateTable='abs_keyword_map',
            createRelatedTable=False)

# Mapping Tables


class MapPhysicalCardToPhysicalCardSet(SQLObject):
    class sqlmeta:
        table = 'physical_map'

    tableversion = 1

    physicalCard = ForeignKey('PhysicalCard', notNull=True)
    physicalCardSet = ForeignKey('PhysicalCardSet', notNull=True)

    physicalCardIndex = DatabaseIndex(physicalCard, unique=False)
    physicalCardSetIndex = DatabaseIndex(physicalCardSet, unique=False)
    jointIndex = DatabaseIndex(physicalCard, physicalCardSet, unique=False)


class MapAbstractCardToRarityPair(SQLObject):
    class sqlmeta:
        table = 'abs_rarity_pair_map'

    tableversion = 1

    abstractCard = ForeignKey('AbstractCard', notNull=True)
    rarityPair = ForeignKey('RarityPair', notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard, unique=False)
    rarityPairIndex = DatabaseIndex(rarityPair, unique=False)


class MapAbstractCardToRuling(SQLObject):
    class sqlmeta:
        table = 'abs_ruling_map'

    tableversion = 1

    abstractCard = ForeignKey('AbstractCard', notNull=True)
    ruling = ForeignKey('Ruling', notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard, unique=False)
    rulingIndex = DatabaseIndex(ruling, unique=False)


class MapAbstractCardToClan(SQLObject):
    class sqlmeta:
        table = 'abs_clan_map'

    tableversion = 1

    abstractCard = ForeignKey('AbstractCard', notNull=True)
    clan = ForeignKey('Clan', notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard, unique=False)
    clanIndex = DatabaseIndex(clan, unique=False)


class MapAbstractCardToDisciplinePair(SQLObject):
    class sqlmeta:
        table = 'abs_discipline_pair_map'

    tableversion = 1

    abstractCard = ForeignKey('AbstractCard', notNull=True)
    disciplinePair = ForeignKey('DisciplinePair', notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard, unique=False)
    disciplinePairIndex = DatabaseIndex(disciplinePair, unique=False)


class MapAbstractCardToCardType(SQLObject):
    class sqlmeta:
        table = 'abs_type_map'

    tableversion = 1

    abstractCard = ForeignKey('AbstractCard', notNull=True)
    cardType = ForeignKey('CardType', notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard, unique=False)
    cardTypeIndex = DatabaseIndex(cardType, unique=False)


class MapAbstractCardToSect(SQLObject):
    class sqlmeta:
        table = 'abs_sect_map'

    tableversion = 1

    abstractCard = ForeignKey('AbstractCard', notNull=True)
    sect = ForeignKey('Sect', notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard, unique=False)
    sectIndex = DatabaseIndex(sect, unique=False)


class MapAbstractCardToTitle(SQLObject):
    class sqlmeta:
        table = 'abs_title_map'

    tableversion = 1

    abstractCard = ForeignKey('AbstractCard', notNull=True)
    title = ForeignKey('Title', notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard, unique=False)
    titleIndex = DatabaseIndex(title, unique=False)


class MapAbstractCardToCreed(SQLObject):
    class sqlmeta:
        table = 'abs_creed_map'

    tableversion = 1

    abstractCard = ForeignKey('AbstractCard', notNull=True)
    creed = ForeignKey('Creed', notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard, unique=False)
    creedIndex = DatabaseIndex(creed, unique=False)


class MapAbstractCardToVirtue(SQLObject):
    class sqlmeta:
        table = 'abs_virtue_map'

    tableversion = 1

    abstractCard = ForeignKey('AbstractCard', notNull=True)
    virtue = ForeignKey('Virtue', notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard, unique=False)
    virtueIndex = DatabaseIndex(virtue, unique=False)


class MapAbstractCardToArtist(SQLObject):
    class sqlmeta:
        table = 'abs_artist_map'

    tableversion = 1

    abstractCard = ForeignKey('AbstractCard', notNull=True)
    artist = ForeignKey('Artist', notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard, unique=False)
    artistIndex = DatabaseIndex(artist, unique=False)


class MapAbstractCardToKeyword(SQLObject):
    class sqlmeta:
        table = 'abs_keyword_map'

    tableversion = 1

    abstractCard = ForeignKey('AbstractCard', notNull=True)
    keyword = ForeignKey('Keyword', notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard, unique=False)
    keywordIndex = DatabaseIndex(keyword, unique=False)

# pylint: enable-msg=W0232, R0902, W0201, C0103

# List of Tables to be created, dropped, etc.

TABLE_LIST = [AbstractCard, Expansion,
               PhysicalCard, PhysicalCardSet,
               Rarity, RarityPair, Discipline, DisciplinePair,
               Clan, CardType, Sect, Title, Ruling, Virtue, Creed,
               Artist, Keyword,
               # Mapping tables from here on out
               MapPhysicalCardToPhysicalCardSet,
               MapAbstractCardToRarityPair,
               MapAbstractCardToRuling,
               MapAbstractCardToClan,
               MapAbstractCardToDisciplinePair,
               MapAbstractCardToCardType,
               MapAbstractCardToSect,
               MapAbstractCardToTitle,
               MapAbstractCardToVirtue,
               MapAbstractCardToCreed,
               MapAbstractCardToArtist,
               MapAbstractCardToKeyword,
               ]
# For reloading the Physical Card Sets

PHYSICAL_SET_LIST = [PhysicalCardSet,
        MapPhysicalCardToPhysicalCardSet]
# For database upgrades, etc.
PHYSICAL_LIST = [PhysicalCard] + PHYSICAL_SET_LIST

# Generically useful constant
CRYPT_TYPES = ('Vampire', 'Imbued')


# Object Maker API
class SutekhObjectMaker(object):
    """Creates all kinds of SutekhObjects from simple strings.

       All the methods will return either a copy of an existing object
       or a new object.
       """
    # pylint: disable-msg=R0201, R0913
    # we want SutekhObjectMaker self-contained, so these are all methods.
    # This needs all these arguments
    def _make_object(self, cObjClass, cInterface, cAbbreviation, sObj,
            bShortname=False, bFullname=False):
        try:
            return cInterface(sObj)
        except SQLObjectNotFound:
            sObj = cAbbreviation.canonical(sObj)
            dKw = {'name': sObj}
            if bShortname:
                dKw['shortname'] = cAbbreviation.shortname(sObj)
            if bFullname:
                dKw['fullname'] = cAbbreviation.fullname(sObj)
            # pylint: disable-msg=W0142
            # ** magic OK here
            return cObjClass(**dKw)

    def make_card_type(self, sType):
        return self._make_object(CardType, ICardType, CardTypes, sType)

    def make_clan(self, sClan):
        return self._make_object(Clan, IClan, Clans, sClan, bShortname=True)

    def make_creed(self, sCreed):
        return self._make_object(Creed, ICreed, Creeds, sCreed,
                bShortname=True)

    def make_discipline(self, sDis):
        return self._make_object(Discipline, IDiscipline, Disciplines, sDis,
                bFullname=True)

    def make_expansion(self, sExpansion):
        return self._make_object(Expansion, IExpansion, Expansions, sExpansion,
                bShortname=True)

    def make_rarity(self, sRarity):
        return self._make_object(Rarity, IRarity, Rarities, sRarity,
                bShortname=True)

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
            return AbstractCard(canonicalName=sCanonical, name=sName, text="")

    def make_physical_card(self, oCard, oExp):
        try:
            return IPhysicalCard((oCard, oExp))
        except SQLObjectNotFound:
            return PhysicalCard(abstractCard=oCard, expansion=oExp)

    def make_rarity_pair(self, sExp, sRarity):
        try:
            return IRarityPair((sExp, sRarity))
        except SQLObjectNotFound:
            oExp = self.make_expansion(sExp)
            oRarity = self.make_rarity(sRarity)
            return RarityPair(expansion=oExp, rarity=oRarity)

    def make_discipline_pair(self, sDiscipline, sLevel):
        try:
            return IDisciplinePair((sDiscipline, sLevel))
        except SQLObjectNotFound:
            oDis = self.make_discipline(sDiscipline)
            return DisciplinePair(discipline=oDis, level=sLevel)

    def make_ruling(self, sText, sCode):
        try:
            return IRuling((sText, sCode))
        except SQLObjectNotFound:
            return Ruling(text=sText, code=sCode)

    def make_keyword(self, sKeyword):
        try:
            return IKeyword(sKeyword)
        except SQLObjectNotFound:
            return Keyword(keyword=sKeyword)

    def make_artist(self, sArtist):
        try:
            return IArtist(sArtist)
        except SQLObjectNotFound:
            return Artist(canonicalName=sArtist.lower(), name=sArtist)


# Abbreviation lookup based adapters
class StrAdaptMeta(type):
    """Metaclass for the string adaptors."""
    # pylint: disable-msg=W0231, C0203
    # W0231 - no point in calling type's init
    # C0203 - pylint's buggy here, see
    # http://lists.logilab.org/pipermail/python-projects/2007-July/001249.html
    def __init__(cls, _sName, _aBases, _dDict):
        cls.make_object_cache()

    # pylint: disable-msg=W0201
    # W0201 - make_object_cache called from init
    def make_object_cache(cls):
        cls.__dCache = {}

    def fetch(cls, sName, oCls):
        oObj = cls.__dCache.get(sName, None)
        if oObj is None:
            oObj = oCls.byName(sName.encode('utf8'))
            cls.__dCache[sName] = oObj

        return oObj


class CardTypeAdapter(object):
    # pylint: disable-msg=E1101
    # metaclass confuses pylint
    __metaclass__ = StrAdaptMeta
    advise(instancesProvide=[ICardType], asAdapterForTypes=[basestring])

    def __new__(cls, sName):
        return cls.fetch(CardTypes.canonical(sName), CardType)


class ClanAdapter(object):
    # pylint: disable-msg=E1101
    # metaclass confuses pylint
    __metaclass__ = StrAdaptMeta
    advise(instancesProvide=[IClan], asAdapterForTypes=[basestring])

    def __new__(cls, sName):
        return cls.fetch(Clans.canonical(sName), Clan)


class CreedAdapter(object):
    # pylint: disable-msg=E1101
    # metaclass confuses pylint
    __metaclass__ = StrAdaptMeta
    advise(instancesProvide=[ICreed], asAdapterForTypes=[basestring])

    def __new__(cls, sName):
        return cls.fetch(Creeds.canonical(sName), Creed)


class DisciplineAdapter(object):
    # pylint: disable-msg=E1101
    # metaclass confuses pylint
    __metaclass__ = StrAdaptMeta
    advise(instancesProvide=[IDiscipline], asAdapterForTypes=[basestring])

    def __new__(cls, sName):
        return cls.fetch(Disciplines.canonical(sName), Discipline)


class ExpansionAdapter(object):
    # pylint: disable-msg=E1101
    # metaclass confuses pylint
    __metaclass__ = StrAdaptMeta
    advise(instancesProvide=[IExpansion], asAdapterForTypes=[basestring])

    def __new__(cls, sName):
        return cls.fetch(Expansions.canonical(sName), Expansion)


class RarityAdapter(object):
    # pylint: disable-msg=E1101
    # metaclass confuses pylint
    __metaclass__ = StrAdaptMeta
    advise(instancesProvide=[IRarity], asAdapterForTypes=[basestring])

    def __new__(cls, sName):
        return cls.fetch(Rarities.canonical(sName), Rarity)


class SectAdaptor(object):
    # pylint: disable-msg=E1101
    # metaclass confuses pylint
    __metaclass__ = StrAdaptMeta
    advise(instancesProvide=[ISect], asAdapterForTypes=[basestring])

    def __new__(cls, sName):
        return cls.fetch(Sects.canonical(sName), Sect)


class TitleAdapter(object):
    # pylint: disable-msg=E1101
    # metaclass confuses pylint
    __metaclass__ = StrAdaptMeta
    advise(instancesProvide=[ITitle], asAdapterForTypes=[basestring])

    def __new__(cls, sName):
        return cls.fetch(Titles.canonical(sName), Title)


class VirtueAdapter(object):
    # pylint: disable-msg=E1101
    # metaclass confuses pylint
    __metaclass__ = StrAdaptMeta
    advise(instancesProvide=[IVirtue], asAdapterForTypes=[basestring])

    def __new__(cls, sName):
        return cls.fetch(Virtues.canonical(sName), Virtue)

# Other Adapters


class RarityPairAdapter(object):
    advise(instancesProvide=[IRarityPair], asAdapterForTypes=[tuple])

    __dCache = {}

    @classmethod
    def make_object_cache(cls):
        cls.__dCache = {}

    def __new__(cls, tData):
        # pylint: disable-msg=E1101
        # adaptors confuses pylint
        oExp = IExpansion(tData[0])
        oRarity = IRarity(tData[1])

        oPair = cls.__dCache.get((oExp.id, oRarity.id), None)
        if oPair is None:
            oPair = RarityPair.selectBy(expansion=oExp,
                    rarity=oRarity).getOne()
            cls.__dCache[(oExp.id, oRarity.id)] = oPair

        return oPair


class DisciplinePairAdapter(object):
    advise(instancesProvide=[IDisciplinePair], asAdapterForTypes=[tuple])

    __dCache = {}

    @classmethod
    def make_object_cache(cls):
        cls.__dCache = {}

    def __new__(cls, tData):
        # pylint: disable-msg=E1101
        # adaptors confuses pylint
        oDis = IDiscipline(tData[0])
        sLevel = str(tData[1])

        oPair = cls.__dCache.get((oDis.id, sLevel), None)
        if oPair is None:
            oPair = DisciplinePair.selectBy(discipline=oDis,
                    level=sLevel).getOne()
            cls.__dCache[(oDis.id, sLevel)] = oPair

        return oPair


class AbstractCardAdapter(object):
    advise(instancesProvide=[IAbstractCard], asAdapterForTypes=[basestring])

    def __new__(cls, sName):
        # pylint: disable-msg=E1101
        # SQLObject confuses pylint
        try:
            oCard = AbstractCard.byCanonicalName(sName.encode('utf8').lower())
        except SQLObjectNotFound:
            # Correct for common variations
            sNewName = csv_to_canonical(sName)
            if sNewName != sName:
                oCard = AbstractCard.byCanonicalName(
                        sNewName.encode('utf8').lower())
            else:
                raise
        return oCard


class RulingAdapter(object):
    advise(instancesProvide=[IRuling], asAdapterForTypes=[tuple])

    def __new__(cls, tData):
        # pylint: disable-msg=E1101,
        # SQLObject confuses pylint
        sText, _sCode = tData
        return Ruling.byText(sText.encode('utf8'))


class KeywordAdapter(object):
    advise(instancesProvide=[IKeyword], asAdapterForTypes=[basestring])

    def __new__(cls, sKeyword):
        # pylint: disable-msg=E1101,
        # SQLObject confuses pylint
        return Keyword.byKeyword(sKeyword.encode('utf8'))


class ArtistAdapter(object):
    advise(instancesProvide=[IArtist], asAdapterForTypes=[basestring])

    def __new__(cls, sArtistName):
        # pylint: disable-msg=E1101,
        # SQLObject confuses pylint
        return Artist.byCanonicalName(sArtistName.encode('utf8').lower())


class PhysicalCardSetAdapter(object):
    advise(instancesProvide=[IPhysicalCardSet], asAdapterForTypes=[basestring])

    def __new__(cls, sName):
        # pylint: disable-msg=E1101
        # SQLObject confuses pylint
        return PhysicalCardSet.byName(sName.encode('utf8'))


class PhysicalCardToAbstractCardAdapter(object):
    advise(instancesProvide=[IAbstractCard], asAdapterForTypes=[PhysicalCard])

    __dCache = {}

    @classmethod
    def make_object_cache(cls):
        cls.__dCache = {}

    def __new__(cls, oPhysCard):
        oCard = cls.__dCache.get(oPhysCard.abstractCardID, None)
        if oCard is None:
            oCard = oPhysCard.abstractCard
            cls.__dCache[oPhysCard.abstractCardID] = oCard
        return oCard


class PhysicalCardMappingToPhysicalCardAdapter(object):
    advise(instancesProvide=[IPhysicalCard],
            asAdapterForTypes=[MapPhysicalCardToPhysicalCardSet])

    __dCache = {}

    @classmethod
    def make_object_cache(cls):
        cls.__dCache = {}

    def __new__(cls, oMapPhysCard):
        oCard = cls.__dCache.get(oMapPhysCard.physicalCardID, None)
        if oCard is None:
            oCard = oMapPhysCard.physicalCard
            cls.__dCache[oMapPhysCard.physicalCardID] = oCard
        return oCard


class PhysicalCardMappingToCardSetAdapter(object):
    advise(instancesProvide=[IPhysicalCardSet],
            asAdapterForTypes=[MapPhysicalCardToPhysicalCardSet])

    def __new__(cls, oMapPhysCard):
        return oMapPhysCard.physicalCardSet


class ExpansionNameAdapter(object):
    """Converts PhysicalCard expansionID to name, used a lot in the gui"""
    advise(instancesProvide=[IExpansionName], asAdapterForTypes=[PhysicalCard])

    __dCache = {}
    sUnknownExpansion = '  Unspecified Expansion'  # canonical version

    @classmethod
    def make_object_cache(cls):
        cls.__dCache = {}

    def __new__(cls, oPhysCard):
        sExpName = cls.__dCache.get(oPhysCard.expansionID, None)
        if sExpName is None:
            if oPhysCard.expansionID:
                sExpName = oPhysCard.expansion.name
            else:
                sExpName = cls.sUnknownExpansion
            cls.__dCache[oPhysCard.expansionID] = sExpName
        return sExpName


class PhysicalCardMappingToAbstractCardAdapter(object):
    advise(instancesProvide=[IAbstractCard],
            asAdapterForTypes=[MapPhysicalCardToPhysicalCardSet])

    __dCache = {}

    @classmethod
    def make_object_cache(cls):
        cls.__dCache = {}

    def __new__(cls, oMapPhysCard):
        oCard = cls.__dCache.get(oMapPhysCard.physicalCardID, None)
        if oCard is None:
            oCard = IAbstractCard(oMapPhysCard.physicalCard)
            cls.__dCache[oMapPhysCard.physicalCardID] = oCard
        return oCard


class PhysicalCardAdapter(object):
    advise(instancesProvide=[IPhysicalCard], asAdapterForTypes=[tuple])

    __dCache = {}

    @classmethod
    def make_object_cache(cls):
        cls.__dCache = {}
        # pre-populate cache with mappings to commonly used
        # physical card with None expansion.
        # pylint: disable-msg=E1101
        # SQLObject confuses pylint
        try:
            for oPhysicalCard in PhysicalCard.select(
                    PhysicalCard.q.expansion == None):
                oAbsCard = oPhysicalCard.abstractCard
                cls.__dCache[(oAbsCard.id, None)] = oPhysicalCard
        except AttributeError:
            # Old SQLObject doesn't like this construction if the database
            # is empty, so, as we can't sensibly fill the cache anyway, we
            # just skip
            pass

    def __new__(cls, tData):
        # pylint: disable-msg=E1101
        # SQLObject confuses pylint
        oAbsCard, oExp = tData
        # oExp may be None, so we don't use oExp.id here
        oPhysicalCard = cls.__dCache.get((oAbsCard.id, oExp), None)
        if oPhysicalCard is None:
            oPhysicalCard = PhysicalCard.selectBy(abstractCard=oAbsCard,
                    expansion=oExp).getOne()
            cls.__dCache[(oAbsCard.id, oExp)] = oPhysicalCard
        return oPhysicalCard

# pylint: enable-msg=C0111


# Flushing

def make_adaptor_caches():
    """Flush all adaptor caches."""
    for cAdaptor in [ExpansionAdapter, RarityAdapter, DisciplineAdapter,
                      ClanAdapter, CardTypeAdapter, SectAdaptor, TitleAdapter,
                      VirtueAdapter, CreedAdapter, DisciplinePairAdapter,
                      RarityPairAdapter, PhysicalCardAdapter,
                      PhysicalCardMappingToPhysicalCardAdapter,
                      PhysicalCardToAbstractCardAdapter,
                      PhysicalCardMappingToAbstractCardAdapter,
                      ExpansionNameAdapter,
                      ]:
        cAdaptor.make_object_cache()


def flush_cache():
    """Flush all the object caches - needed before importing new card lists
       and such"""
    for oJoin in AbstractCard.sqlmeta.joins:
        if type(oJoin) is SOCachedRelatedJoin:
            oJoin.flush_cache()

    make_adaptor_caches()


def init_cache():
    """Initiliase the cached join tables."""
    for oJoin in AbstractCard.sqlmeta.joins:
        if type(oJoin) is SOCachedRelatedJoin:
            oJoin.init_cache()

    make_adaptor_caches()


# helper conversion functions
# We define them here to avoid circular imports, since pretty much everything
# else requires SutekhObjects


def canonical_to_csv(sName):
    """Moves articles to the end of the name"""
    if sName.startswith('The '):
        sName = sName[4:] + ", The"
    elif sName.startswith('An '):
        sName = sName[3:] + ", An"
    elif sName.startswith('A '):
        sName = sName[2:] + ", A"
    return sName


def csv_to_canonical(sName):
    """Moves articles from the end back to the start - reverses
       cannonical_to_csv"""
    # handle case variations as well
    if sName.lower().endswith(', the'):
        sName = "The " + sName[:-5]
    elif sName.lower().endswith(', an'):
        sName = "An " + sName[:-4]
    elif sName.lower().endswith(', a'):
        sName = "A " + sName[:-3]
    # The result might be mixed case, but, as we will feed this into
    # IAbstractCard in most cases, that won't matter
    return sName
