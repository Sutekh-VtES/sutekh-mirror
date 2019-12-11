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
                         Keyword, Ruling, RarityPair, Expansion, Printing,
                         PrintingProperty, Rarity, CardType, Artist)
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
def IPrinting(oUnknown):
    """Default Printing adapter"""
    return fail_adapt(oUnknown, 'Printing')


@singledispatch
def IPrintingProperty(oUnknown):
    """Default PrintingProperty adapter"""
    return fail_adapt(oUnknown, 'PrintingProperty')


@singledispatch
def IPrintingName(oUnknown):
    """Default Printing Name adapter"""
    return fail_adapt(oUnknown, 'PrintingName')

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


@singledispatch
def ILookupHint(oUnknown):
    """The base for keyword adaption"""
    return fail_adapt(oUnknown, 'LookupHints')


# pylint: disable=missing-docstring
# Not a lot of value to docstrings for these classes and methods
# Abbreviation lookup based adapters
class StrAdaptMeta(type):
    """Metaclass for the string adapters."""
    # pylint: disable=super-init-not-called
    # no point in calling type's init
    # http://lists.logilab.org/pipermail/python-projects/2007-July/001249.html
    def __init__(cls, _sName, _aBases, _dDict):
        # pylint: disable=no-value-for-parameter
        # pylint incorrectly thinks this is an unbound call.
        cls.make_object_cache()

    # pylint: disable=attribute-defined-outside-init
    # make_object_cache called from init
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
    # pylint: disable=no-member
    # metaclass confuses pylint
    __metaclass__ = StrAdaptMeta

    @classmethod
    def lookup(cls, sName):
        return cls.fetch(CardTypes.canonical(sName), CardType)


ICardType.register(CardType, passthrough)

ICardType.register(basestring, CardTypeAdapter.lookup)


class ExpansionAdapter(Adapter):
    # pylint: disable=no-member
    # metaclass confuses pylint
    __metaclass__ = StrAdaptMeta

    @classmethod
    def lookup(cls, sName):
        return cls.fetch(Expansions.canonical(sName), Expansion)


IExpansion.register(Expansion, passthrough)

IExpansion.register(basestring, ExpansionAdapter.lookup)


@IExpansion.register(Printing)
def exp_name_from_print(oPrint):
    """Retrun the expansion for a printing."""
    return oPrint.expansion


class RarityAdapter(Adapter):
    # pylint: disable=no-member
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
        # pylint: disable=no-member
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
                oCard = None
                try:
                    # pylint: disable=no-member
                    # SQLObject confuses pylint
                    oCard = AbstractCard.byCanonicalName(
                        oLookup.value.lower())
                except SQLObjectNotFound:
                    # Try encoded version, for older SQLObject versions
                    try:
                        # pylint: disable=no-member
                        # SQLObject confuses pylint
                        oCard = AbstractCard.byCanonicalName(
                            oLookup.value.encode('utf8').lower())
                    except SQLObjectNotFound:
                        # Possible error in the lookup data - warn about it,
                        # but we don't want to fail here.
                        logging.warn("Unable to create %s mapping (%s -> %s)",
                                     oLookup.domain, oLookup.lookup,
                                     oLookup.value)
                if oCard is not None:
                    for sKey in [oLookup.lookup,
                                 oLookup.lookup.encode('utf8')]:
                        cls.__dCache[sKey] = oCard
                        cls.__dCache[sKey.lower()] = oCard

    @classmethod
    def lookup(cls, sName):
        oCard = cls.__dCache.get(sName, None)
        if oCard is None:
            # pylint: disable=no-member
            # SQLObject confuses pylint
            oExp = None
            for sCand in [sName, move_articles_to_front(sName),
                          sName.encode('utf8'),
                          move_articles_to_front(sName.encode('utf8'))]:
                try:
                    oCard = AbstractCard.byCanonicalName(sCand.lower())
                    cls.__dCache[sCand] = oCard
                    oExp = None
                    break
                except SQLObjectNotFound as oExp:
                    # We will handle the failure case after the loop
                    continue
            # pylint: disable=raising-bad-type
            # We're only raising if this is not None, so we're OK
            if oExp:
                raise oExp
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


IArtist.register(Artist, passthrough)


@IArtist.register(basestring)
def artist_from_string(sArtistName):
    """Adapter for string -> Artist"""
    # pylint: disable=no-member
    # SQLObject confuses pylint
    return Artist.byCanonicalName(sArtistName.encode('utf8').lower())


IPrintingProperty.register(PrintingProperty, passthrough)


@IPrintingProperty.register(basestring)
def print_property_from_string(sPropertyValue):
    """Adapter for string -> Artist"""
    # pylint: disable=no-member
    # SQLObject confuses pylint
    return PrintingProperty.byCanonicalValue(
        sPropertyValue.encode('utf8').lower())


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


class PrintingAdapter(Adapter):

    __dCache = {}

    @classmethod
    def make_object_cache(cls):
        cls.__dCache = {}
        # pre-populate cache with mappings to default printings
        # (name is None)
        try:
            # pylint: disable=singleton-comparison
            # This comparison is a SQLObject construction
            for oPrinting in Printing.select(
                    PhysicalCard.q.name == None):
                cls.__dCache[(oPrinting.expansionID, None)] = oPrinting
        except AttributeError:
            # Old SQLObject doesn't like this construction if the database
            # is empty, so, as we can't sensibly fill the cache anyway, we
            # just skip
            pass

    @classmethod
    def lookup(cls, tData):
        oExp, sPrintingName = tData
        oPrinting = cls.__dCache.get((oExp.id, sPrintingName), None)
        if oPrinting is None:
            oPrinting = Printing.selectBy(expansion=oExp,
                                          name=sPrintingName).getOne()
            cls.__dCache[(oExp.id, sPrintingName)] = oPrinting
        return oPrinting


IPrinting.register(Printing, passthrough)


IPrinting.register(tuple, PrintingAdapter.lookup)


@IPrintingName.register(Printing)
def get_exp_printing_name(oPrint):
    """Return the canonical name of a printing"""
    sExpName = oPrint.expansion.name
    if oPrint.name:
        sName = '%s (%s)' % (sExpName, oPrint.name)
    else:
        sName = sExpName
    return sName


class PrintingNameAdapter(Adapter):
    """Converts PhysicalCard printing to name, used a lot in the gui"""

    __dCache = {}
    sUnknownExpansion = '  Unspecified Expansion'  # canonical version

    @classmethod
    def make_object_cache(cls):
        cls.__dCache = {}

    @classmethod
    def lookup(cls, oPhysCard):
        sName = cls.__dCache.get(oPhysCard.printingID, None)
        if sName is None:
            if oPhysCard.printingID:
                sName = get_exp_printing_name(oPhysCard.printing)
            else:
                sName = cls.sUnknownExpansion
            cls.__dCache[oPhysCard.printingID] = sName
        return sName


IPrintingName.register(PhysicalCard, PrintingNameAdapter.lookup)


class PrintingStringAdapter(Adapter):
    """Reverse the PrintingName Lookups"""

    __dCache = {}

    @classmethod
    def make_object_cache(cls):
        cls.__dCache = {}
        # pre-populate cache with all known printings
        # (name is None)
        try:
            for oPrinting in Printing.select():
                sPrintName = get_exp_printing_name(oPrinting)
                cls.__dCache[sPrintName] = oPrinting
        except AttributeError:
            # Old SQLObject doesn't like this construction if the database
            # is empty, so, as we can't sensibly fill the cache anyway, we
            # just skip
            pass

    @classmethod
    def lookup(cls, sName):
        return cls.__dCache[sName]


IPrinting.register(basestring, PrintingStringAdapter.lookup)


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
                    PhysicalCard.q.printing == None):
                oAbsCard = oPhysicalCard.abstractCard
                cls.__dCache[(oAbsCard.id, None)] = oPhysicalCard
        except AttributeError:
            # Old SQLObject doesn't like this construction if the database
            # is empty, so, as we can't sensibly fill the cache anyway, we
            # just skip
            pass

    @classmethod
    def lookup(cls, tData):
        # pylint: disable=no-member
        # SQLObject confuses pylint
        oAbsCard, oPrinting = tData
        # oExp may be None, so we don't use oExp.id here
        oPhysicalCard = cls.__dCache.get((oAbsCard.id, oPrinting), None)
        if oPhysicalCard is None:
            oPhysicalCard = PhysicalCard.selectBy(abstractCard=oAbsCard,
                                                  printing=oPrinting).getOne()
            cls.__dCache[(oAbsCard.id, oPrinting)] = oPhysicalCard
        return oPhysicalCard


IPhysicalCard.register(tuple, PhysicalCardAdapter.lookup)


IPhysicalCard.register(PhysicalCard, passthrough)


@ILookupHint.register(tuple)
def lookup_hint_from_tuple(tData):
    """Lookup a hint from a (domain, key) tuple"""
    sDomain, sKey = tData
    return LookupHints.selectBy(domain=sDomain,
                                lookup=sKey).getOne()
