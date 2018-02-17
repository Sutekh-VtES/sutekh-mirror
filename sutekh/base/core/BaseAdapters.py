# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""The base adapters"""

import logging

from singledispatch import singledispatch

from sqlobject import SQLObjectNotFound

from .BaseTables import (LookupHints, AbstractCard, PhysicalCard,
                         PhysicalCardSet, MapPhysicalCardToPhysicalCardSet,
                         Keyword, Ruling, RarityPair, Expansion,
                         Rarity, CardType, Artist)
from .BaseAbbreviations import CardTypes, Expansions, Rarities
from ..Utility import move_articles_to_front


# Adaption helper functions
def fail_adapt(oUnknown, sCls):
    """Generic failed to adapt handler"""
    raise NotImplementedError("Can't adapt %r to %s" % (oUnknown, sCls))
    # pylint: disable=unreachable
    # We know this is unreachable, but this is to work around
    # pylint's return checker for the base adapters
    return oUnknown


def passthrough(oObj):
    """Passthrough adapter for calling Ixxx() on an object of type xxx"""
    return oObj


# Base adapters
@singledispatch
def IAbstractCard(oUnknown):
    """Default AbstractCard adapter"""
    return fail_adapt(oUnknown, 'AbstractCard')


@singledispatch
def IPhysicalCard(oUnknown):
    """Default PhysicalCard adapter"""
    return fail_adapt(oUnknown, 'PhysicalCard')


@singledispatch
def IPhysicalCardSet(oUnknown):
    """Default PhysicalCardSet adapter"""
    return fail_adapt(oUnknown, 'PhysicalCardSet')


@singledispatch
def IRarityPair(oUnknown):
    """Default RarityPair adapter"""
    return fail_adapt(oUnknown, 'RarityPair')


@singledispatch
def IExpansion(oUnknown):
    """Default Expansion adapter"""
    return fail_adapt(oUnknown, 'Expansion')


@singledispatch
def IExpansionName(oUnknown):
    """Default Expansion Name adapter"""
    return fail_adapt(oUnknown, 'ExpansionName')


@singledispatch
def IRarity(oUnknown):
    """Default Rarirty adapter"""
    return fail_adapt(oUnknown, 'Rarity')


@singledispatch
def ICardType(oUnknown):
    """Default CardType adapter"""
    return fail_adapt(oUnknown, 'CardType')


@singledispatch
def IRuling(oUnknown):
    """Default Ruling adapter"""
    return fail_adapt(oUnknown, 'Ruling')


@singledispatch
def IArtist(oUnknown):
    """The base for artist adaption"""
    return fail_adapt(oUnknown, 'Artist')


@singledispatch
def IKeyword(oUnknown):
    """The base for keyword adaption"""
    return fail_adapt(oUnknown, 'Keyword')


# pylint: disable=missing-docstring
# Not a lot of value to docstrings for these classes and methods
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
                    # pylint: disable=no-member
                    # SQLObject confuses pylint
                    oCard = AbstractCard.byCanonicalName(
                        oLookup.value.encode('utf8').lower())
                    cls.__dCache[oLookup.lookup] = oCard
                except SQLObjectNotFound:
                    # Possible error in the lookup data - warn about it, but
                    # we don't want to fail here.
                    logging.warn("Unable to create %s mapping (%s -> %s)",
                                 oLookup.domain, oLookup.lookup, oLookup.value)

    @classmethod
    def lookup(cls, sName):
        oCard = cls.__dCache.get(sName, None)
        if oCard is None:
            # pylint: disable=no-member
            # SQLObject confuses pylint
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
    # pylint: disable=no-member
    # SQLObject confuses pylint
    sText, _sCode = tData
    return Ruling.byText(sText.encode('utf8'))


IKeyword.register(Keyword, passthrough)


@IKeyword.register(basestring)
def keyword_from_string(sKeyword):
    """Adapter for string -> Keyword"""
    # pylint: disable=no-member
    # SQLObject confuses pylint
    return Keyword.byKeyword(sKeyword.encode('utf8'))


IArtist.register(Keyword, passthrough)


@IArtist.register(basestring)
def artist_from_string(sArtistName):
    """Adapter for string -> Artist"""
    # pylint: disable=no-member
    # SQLObject confuses pylint
    return Artist.byCanonicalName(sArtistName.encode('utf8').lower())


IPhysicalCardSet.register(PhysicalCardSet, passthrough)


@IPhysicalCardSet.register(basestring)
def phys_card_set_from_string(sName):
    """Adapter for string -> PhysicalCardSet"""
    # pylint: disable=no-member
    # SQLObject confuses pylint
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
        # pylint: disable=singleton-comparison
        # The '== None' is required for constructing the select statement
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
