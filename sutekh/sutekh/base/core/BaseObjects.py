# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

# pylint: disable=C0111, C0302
# C0111 - No point in docstrings for these classes, really
# C0302 - lots of lines as we want all these related definitions in one file

"""The base database definitions and pyprotocols adapters"""

import logging

from singledispatch import singledispatch

# pylint: disable=E0611
# pylint doesn't parse sqlobject's column declaration magic correctly
from sqlobject import (sqlmeta, SQLObject, IntCol, UnicodeCol, RelatedJoin,
                       MultipleJoin, BoolCol, DatabaseIndex, ForeignKey,
                       SQLObjectNotFound, DateCol)
from sqlobject.inheritance import InheritableSQLObject
# pylint: enable=E0611

from sutekh.core.Abbreviations import CardTypes, Expansions, Rarities

from ..Utility import move_articles_to_front
from .CachedRelatedJoin import CachedRelatedJoin


# Adaption helper functions

def fail_adapt(oUnknown, sCls):
    """Generic failed to adapt handler"""
    raise NotImplementedError("Can't adapt %r to %s" % (oUnknown, sCls))


def passthrough(oObj):
    """Passthrough adapter for calling Ixxx() on an object of type xxx"""
    return oObj


# Base adapters

@singledispatch
def IAbstractCard(oUnknown):
    """Default AbstractCard adapter"""
    fail_adapt(oUnknown, 'AbstractCard')


@singledispatch
def IPhysicalCard(oUnknown):
    """Default PhysicalCard adapter"""
    fail_adapt(oUnknown, 'PhysicalCard')


@singledispatch
def IPhysicalCardSet(oUnknown):
    """Default PhysicalCardSet adapter"""
    fail_adapt(oUnknown, 'PhysicalCardSet')


@singledispatch
def IRarityPair(oUnknown):
    """Default RarityPair adapter"""
    fail_adapt(oUnknown, 'RarityPair')


@singledispatch
def IExpansion(oUnknown):
    """Default Expansion adapter"""
    fail_adapt(oUnknown, 'Expansion')


@singledispatch
def IExpansionName(oUnknown):
    """Default Expansion Name adapter"""
    fail_adapt(oUnknown, 'ExpansionName')


@singledispatch
def IRarity(oUnknown):
    """Default Rarirty adapter"""
    fail_adapt(oUnknown, 'Rarity')


@singledispatch
def ICardType(oUnknown):
    """Default CardType adapter"""
    fail_adapt(oUnknown, 'CardType')


@singledispatch
def IRuling(oUnknown):
    """Default Ruling adapter"""
    fail_adapt(oUnknown, 'Ruling')


@singledispatch
def IArtist(oUnknown):
    """The base for artist adaption"""
    fail_adapt(oUnknown, 'Artist')


@singledispatch
def IKeyword(oUnknown):
    """The base for keyword adaption"""
    fail_adapt(oUnknown, 'Keyword')


# pylint: enable=C0321
# Table Objects

# pylint: disable=W0232, R0902, W0201, C0103
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


class AbstractCard(InheritableSQLObject):

    tableversion = 7
    sqlmeta.lazyUpdate = True

    canonicalName = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    name = UnicodeCol()
    text = UnicodeCol()

    # Most of these names are singular when they should be plural
    # since they refer to lists. We've decided to live with the
    # inconsistency for old columns but do the right thing for new
    # ones.
    rarity = CachedRelatedJoin('RarityPair',
                               intermediateTable='abs_rarity_pair_map',
                               joinColumn="abstract_card_id",
                               createRelatedTable=False)
    cardtype = CachedRelatedJoin('CardType', intermediateTable='abs_type_map',
                                 joinColumn="abstract_card_id",
                                 createRelatedTable=False)
    rulings = CachedRelatedJoin('Ruling', intermediateTable='abs_ruling_map',
                                joinColumn="abstract_card_id",
                                createRelatedTable=False)
    artists = CachedRelatedJoin('Artist', intermediateTable='abs_artist_map',
                                joinColumn="abstract_card_id",
                                createRelatedTable=False)
    keywords = CachedRelatedJoin('Keyword',
                                 intermediateTable='abs_keyword_map',
                                 joinColumn="abstract_card_id",
                                 createRelatedTable=False)

    physicalCards = MultipleJoin('PhysicalCard')


class PhysicalCard(SQLObject):

    tableversion = 2
    abstractCard = ForeignKey('AbstractCard')
    abstractCardIndex = DatabaseIndex(abstractCard)
    # Explicitly allow None as expansion
    expansion = ForeignKey('Expansion', notNull=False)
    sets = RelatedJoin('PhysicalCardSet', intermediateTable='physical_map',
                       createRelatedTable=False)


class PhysicalCardSet(SQLObject):
    tableversion = 7
    name = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    author = UnicodeCol(default='')
    comment = UnicodeCol(default='')
    annotations = UnicodeCol(default='')
    inuse = BoolCol(default=False)
    parent = ForeignKey('PhysicalCardSet', default=None)
    cards = RelatedJoin('PhysicalCard', intermediateTable='physical_map',
                        createRelatedTable=False)
    parentIndex = DatabaseIndex(parent)


class RarityPair(SQLObject):
    tableversion = 1
    expansion = ForeignKey('Expansion')
    rarity = ForeignKey('Rarity')
    cards = RelatedJoin('AbstractCard',
                        intermediateTable='abs_rarity_pair_map',
                        createRelatedTable=False)
    expansionRarityIndex = DatabaseIndex(expansion, rarity, unique=True)


class Expansion(SQLObject):

    tableversion = 4
    name = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    shortname = UnicodeCol(default=None)
    releasedate = DateCol(default=None)
    pairs = MultipleJoin('RarityPair')


class Rarity(SQLObject):

    tableversion = 3
    name = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    shortname = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)


class CardType(SQLObject):

    tableversion = 2
    name = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    cards = RelatedJoin('AbstractCard', intermediateTable='abs_type_map',
                        createRelatedTable=False)


class Ruling(SQLObject):

    tableversion = 2
    text = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    code = UnicodeCol()
    url = UnicodeCol(default=None)
    cards = RelatedJoin('AbstractCard', intermediateTable='abs_ruling_map',
                        createRelatedTable=False)


class Artist(SQLObject):

    tableversion = 1
    canonicalName = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    name = UnicodeCol()
    cards = RelatedJoin('AbstractCard', intermediateTable='abs_artist_map',
                        createRelatedTable=False)


class Keyword(SQLObject):

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


class MapAbstractCardToCardType(SQLObject):
    class sqlmeta:
        table = 'abs_type_map'

    tableversion = 1

    abstractCard = ForeignKey('AbstractCard', notNull=True)
    cardType = ForeignKey('CardType', notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard, unique=False)
    cardTypeIndex = DatabaseIndex(cardType, unique=False)


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


class LookupHints(SQLObject):

    # This is a collection of lookup hints for use in various
    # places.
    # The domain field is used to indicate which domain the lookup
    # will be used for, while the (lookup, value) are the lookup
    # pairs

    tableversion = 1

    domain = UnicodeCol(length=MAX_ID_LENGTH)
    lookup = UnicodeCol()
    value = UnicodeCol()


# pylint: enable=W0232, R0902, W0201, C0103

# List of Tables to be created, dropped, etc.

BASE_TABLE_LIST = [AbstractCard, Expansion, PhysicalCard, PhysicalCardSet,
                   Rarity, RarityPair, CardType, Ruling, Artist, Keyword,
                   LookupHints,
                   # Mapping tables from here on out
                   MapPhysicalCardToPhysicalCardSet,
                   MapAbstractCardToRarityPair,
                   MapAbstractCardToRuling,
                   MapAbstractCardToCardType,
                   MapAbstractCardToArtist,
                   MapAbstractCardToKeyword,
                  ]

# For reloading the Physical Card Sets
PHYSICAL_SET_LIST = [PhysicalCardSet, MapPhysicalCardToPhysicalCardSet]

# For database upgrades, etc.
PHYSICAL_LIST = [PhysicalCard] + PHYSICAL_SET_LIST


# Object Maker API
class BaseObjectMaker(object):
    """Creates all kinds of program Objects from simple strings.

       All the methods will return either a copy of an existing object
       or a new object.
       """
    # pylint: disable=R0201, R0913
    # we want SutekhObjectMaker self-contained, so these are all methods.
    # This needs all these arguments
    def _make_object(self, cObjClass, fAdapter, cAbbreviation, sObj,
                     bShortname=False, bFullname=False):
        try:
            return fAdapter(sObj)
        except SQLObjectNotFound:
            sObj = cAbbreviation.canonical(sObj)
            dKw = {'name': sObj}
            if bShortname:
                dKw['shortname'] = cAbbreviation.shortname(sObj)
            if bFullname:
                dKw['fullname'] = cAbbreviation.fullname(sObj)
            # pylint: disable=W0142
            # ** magic OK here
            return cObjClass(**dKw)

    def make_card_type(self, sType):
        return self._make_object(CardType, ICardType, CardTypes, sType)

    def make_expansion(self, sExpansion):
        return self._make_object(Expansion, IExpansion, Expansions, sExpansion,
                                 bShortname=True)

    def make_rarity(self, sRarity):
        return self._make_object(Rarity, IRarity, Rarities, sRarity,
                                 bShortname=True)

    def make_abstract_card(self, sCard):
        # Subclasses should implement this
        # XXX: Should we define some of the common logic here
        # and just provide a hook for creating the object if it
        # doesn't exist?
        raise NotImplementedError

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
    """Metaclass for the string adapters."""
    # pylint: disable=W0231, C0203
    # W0231 - no point in calling type's init
    # C0203 - pylint's buggy here, see
    # http://lists.logilab.org/pipermail/python-projects/2007-July/001249.html
    def __init__(cls, _sName, _aBases, _dDict):
        cls.make_object_cache()

    # pylint: disable=W0201
    # W0201 - make_object_cache called from init
    def make_object_cache(cls):
        cls.__dCache = {}

    def fetch(cls, sName, oCls):
        oObj = cls.__dCache.get(sName, None)
        if oObj is None:
            oObj = oCls.byName(sName.encode('utf8'))
            cls.__dCache[sName] = oObj

        return oObj


class Adapter(object):
    """Base class for adapter objects.
       Makes introspection less messy,"""
    pass


class CardTypeAdapter(Adapter):
    # pylint: disable=E1101
    # metaclass confuses pylint
    __metaclass__ = StrAdaptMeta

    @classmethod
    def lookup(cls, sName):
        return cls.fetch(CardTypes.canonical(sName), CardType)


ICardType.register(CardType, passthrough)

ICardType.register(basestring, CardTypeAdapter.lookup)


class ExpansionAdapter(Adapter):
    # pylint: disable=E1101
    # metaclass confuses pylint
    __metaclass__ = StrAdaptMeta

    @classmethod
    def lookup(cls, sName):
        return cls.fetch(Expansions.canonical(sName), Expansion)


IExpansion.register(Expansion, passthrough)

IExpansion.register(basestring, ExpansionAdapter.lookup)


class RarityAdapter(Adapter):
    # pylint: disable=E1101
    # metaclass confuses pylint
    __metaclass__ = StrAdaptMeta

    @classmethod
    def lookup(cls, sName):
        return cls.fetch(Rarities.canonical(sName), Rarity)


IRarity.register(Rarity, passthrough)


IRarity.register(basestring, RarityAdapter.lookup)


# Other Adapters


class RarityPairAdapter(Adapter):

    __dCache = {}

    @classmethod
    def make_object_cache(cls):
        cls.__dCache = {}

    @classmethod
    def lookup(cls, tData):
        # pylint: disable=E1101
        # adapters confuses pylint
        oExp = IExpansion(tData[0])
        oRarity = IRarity(tData[1])

        oPair = cls.__dCache.get((oExp.id, oRarity.id), None)
        if oPair is None:
            oPair = RarityPair.selectBy(expansion=oExp,
                                        rarity=oRarity).getOne()
            cls.__dCache[(oExp.id, oRarity.id)] = oPair

        return oPair


IRarityPair.register(RarityPair, passthrough)

IRarityPair.register(tuple, RarityPairAdapter.lookup)


IAbstractCard.register(AbstractCard, passthrough)


class CardNameLookupAdapter(Adapter):
    """Adapter for card name string -> AbstractCard"""

    __dCache = {}

    @classmethod
    def make_object_cache(cls):
        cls.__dCache = {}
        # Fill in values from LookupHints
        for oLookup in LookupHints.select():
            if oLookup.domain == 'CardNames':
                try:
                    oCard = AbstractCard.byCanonicalName(
                        oLookup.value.encode('utf8').lower())
                    cls.__dCache[oLookup.lookup] = oCard
                except SQLObjectNotFound:
                    # Possible error in the lookup data - warn about it, but
                    # we don't want to fail here.
                    logging.warn("Unable to create %s mapping (%s -> %s",
                                 oLookup.domain, oLookup.lookup, oLookup.value)

    @classmethod
    def lookup(cls, sName):
        oCard = cls.__dCache.get(sName, None)
        if oCard is None:
            try:
                oCard = AbstractCard.byCanonicalName(
                    sName.encode('utf8').lower())
                cls.__dCache[sName] = oCard
            except SQLObjectNotFound:
                # Correct for common variations
                sNewName = move_articles_to_front(sName)
                if sNewName != sName:
                    oCard = AbstractCard.byCanonicalName(
                        sNewName.encode('utf8').lower())
                    cls.__dCache[sNewName] = oCard
                else:
                    raise
        return oCard


IAbstractCard.register(basestring, CardNameLookupAdapter.lookup)


IRuling.register(Ruling, passthrough)


@IRuling.register(tuple)
def ruling_from_tuple(tData):
    """Convert a (text, code) tuple to a ruling object."""
    sText, _sCode = tData
    return Ruling.byText(sText.encode('utf8'))


IKeyword.register(Keyword, passthrough)


@IKeyword.register(basestring)
def keyword_from_string(sKeyword):
    """Adapter for string -> Keyword"""
    return Keyword.byKeyword(sKeyword.encode('utf8'))


IArtist.register(Keyword, passthrough)


@IArtist.register(basestring)
def artist_from_string(sArtistName):
    """Adapter for string -> Artist"""
    return Artist.byCanonicalName(sArtistName.encode('utf8').lower())


IPhysicalCardSet.register(PhysicalCardSet, passthrough)


@IPhysicalCardSet.register(basestring)
def phys_card_set_from_string(sName):
    """Adapter for string -> PhysicalCardSet"""
    return PhysicalCardSet.byName(sName.encode('utf8'))


class PhysicalCardToAbstractCardAdapter(Adapter):

    __dCache = {}

    @classmethod
    def make_object_cache(cls):
        cls.__dCache = {}

    @classmethod
    def lookup(cls, oPhysCard):
        oCard = cls.__dCache.get(oPhysCard.abstractCardID, None)
        if oCard is None:
            oCard = oPhysCard.abstractCard
            cls.__dCache[oPhysCard.abstractCardID] = oCard
        return oCard

IAbstractCard.register(PhysicalCard, PhysicalCardToAbstractCardAdapter.lookup)


class PhysicalCardMappingToPhysicalCardAdapter(Adapter):

    __dCache = {}

    @classmethod
    def make_object_cache(cls):
        cls.__dCache = {}

    @classmethod
    def lookup(cls, oMapPhysCard):
        oCard = cls.__dCache.get(oMapPhysCard.physicalCardID, None)
        if oCard is None:
            oCard = oMapPhysCard.physicalCard
            cls.__dCache[oMapPhysCard.physicalCardID] = oCard
        return oCard

IPhysicalCard.register(MapPhysicalCardToPhysicalCardSet,
                       PhysicalCardMappingToPhysicalCardAdapter.lookup)


@IPhysicalCardSet.register(MapPhysicalCardToPhysicalCardSet)
def map_pcs_to_pcs(oMapPhysCard):
    """Adapt a MapPhysicalCardToPhysicalCardSet to the corresponding
       PhysicalCardSet"""
    return oMapPhysCard.physicalCardSet


class ExpansionNameAdapter(Adapter):
    """Converts PhysicalCard expansionID to name, used a lot in the gui"""

    __dCache = {}
    sUnknownExpansion = '  Unspecified Expansion'  # canonical version

    @classmethod
    def make_object_cache(cls):
        cls.__dCache = {}

    @classmethod
    def lookup(cls, oPhysCard):
        sExpName = cls.__dCache.get(oPhysCard.expansionID, None)
        if sExpName is None:
            if oPhysCard.expansionID:
                sExpName = oPhysCard.expansion.name
            else:
                sExpName = cls.sUnknownExpansion
            cls.__dCache[oPhysCard.expansionID] = sExpName
        return sExpName


IExpansionName.register(PhysicalCard, ExpansionNameAdapter.lookup)


class PhysicalCardMappingToAbstractCardAdapter(Adapter):

    __dCache = {}

    @classmethod
    def make_object_cache(cls):
        cls.__dCache = {}

    @classmethod
    def lookup(cls, oMapPhysCard):
        oCard = cls.__dCache.get(oMapPhysCard.physicalCardID, None)
        if oCard is None:
            oCard = IAbstractCard(oMapPhysCard.physicalCard)
            cls.__dCache[oMapPhysCard.physicalCardID] = oCard
        return oCard

IAbstractCard.register(MapPhysicalCardToPhysicalCardSet,
                       PhysicalCardMappingToAbstractCardAdapter.lookup)


class PhysicalCardAdapter(Adapter):

    __dCache = {}

    @classmethod
    def make_object_cache(cls):
        cls.__dCache = {}
        # pre-populate cache with mappings to commonly used
        # physical card with None expansion.
        # pylint: disable=E1101
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

    @classmethod
    def lookup(cls, tData):
        # pylint: disable=E1101
        # SQLObject confuses pylint
        oAbsCard, oExp = tData
        # oExp may be None, so we don't use oExp.id here
        oPhysicalCard = cls.__dCache.get((oAbsCard.id, oExp), None)
        if oPhysicalCard is None:
            oPhysicalCard = PhysicalCard.selectBy(abstractCard=oAbsCard,
                                                  expansion=oExp).getOne()
            cls.__dCache[(oAbsCard.id, oExp)] = oPhysicalCard
        return oPhysicalCard

IPhysicalCard.register(tuple, PhysicalCardAdapter.lookup)


IPhysicalCard.register(PhysicalCard, passthrough)

# pylint: enable=C0111
