# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

# pylint: disable=C0111
# C0111 - No point in docstrings for these classes, really

"""The base database definitions and pyprotocols adapters"""

# pylint: disable=E0611
# pylint doesn't parse sqlobject's column declaration magic correctly
from sqlobject import (sqlmeta, SQLObject, IntCol, UnicodeCol, RelatedJoin,
                       MultipleJoin, BoolCol, DatabaseIndex, ForeignKey,
                       DateCol)
from sqlobject.inheritance import InheritableSQLObject
# pylint: enable=E0611

from .CachedRelatedJoin import CachedRelatedJoin

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

    # pylint: disable=old-style-class
    class sqlmeta:
        table = 'physical_map'

    tableversion = 1

    physicalCard = ForeignKey('PhysicalCard', notNull=True)
    physicalCardSet = ForeignKey('PhysicalCardSet', notNull=True)

    physicalCardIndex = DatabaseIndex(physicalCard, unique=False)
    physicalCardSetIndex = DatabaseIndex(physicalCardSet, unique=False)
    jointIndex = DatabaseIndex(physicalCard, physicalCardSet, unique=False)


class MapAbstractCardToRarityPair(SQLObject):
    # pylint: disable=old-style-class
    class sqlmeta:
        table = 'abs_rarity_pair_map'

    tableversion = 1

    abstractCard = ForeignKey('AbstractCard', notNull=True)
    rarityPair = ForeignKey('RarityPair', notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard, unique=False)
    rarityPairIndex = DatabaseIndex(rarityPair, unique=False)


class MapAbstractCardToRuling(SQLObject):
    # pylint: disable=old-style-class
    class sqlmeta:
        table = 'abs_ruling_map'

    tableversion = 1

    abstractCard = ForeignKey('AbstractCard', notNull=True)
    ruling = ForeignKey('Ruling', notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard, unique=False)
    rulingIndex = DatabaseIndex(ruling, unique=False)


class MapAbstractCardToCardType(SQLObject):
    # pylint: disable=old-style-class
    class sqlmeta:
        table = 'abs_type_map'

    tableversion = 1

    abstractCard = ForeignKey('AbstractCard', notNull=True)
    cardType = ForeignKey('CardType', notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard, unique=False)
    cardTypeIndex = DatabaseIndex(cardType, unique=False)


class MapAbstractCardToArtist(SQLObject):
    # pylint: disable=old-style-class
    class sqlmeta:
        table = 'abs_artist_map'

    tableversion = 1

    abstractCard = ForeignKey('AbstractCard', notNull=True)
    artist = ForeignKey('Artist', notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard, unique=False)
    artistIndex = DatabaseIndex(artist, unique=False)


class MapAbstractCardToKeyword(SQLObject):
    # pylint: disable=old-style-class
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
