# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

# pylint: disable=super-init-not-called, abstract-method, too-many-lines
# the base classes don't have useful __init__ methods, so we
# generally don't call __init__ when creating a new filter
# not every abstract method is immediately overridden
# the module is long, but keeping the filters together is the best
# option

"""Define all the filters provided in sutekh"""

# pylint: disable=deprecated-module
# We need string.punctation for best_guess_filter
import string
# pylint: enable=deprecated-module

from sqlobject import (SQLObjectNotFound, AND, OR, NOT, LIKE, func, sqlhub,
                       IN as SQLOBJ_IN)
from sqlobject.sqlbuilder import (Table, Alias, LEFTJOINOn, Select,
                                  SQLTrueClause as TRUE)

from .BaseTables import (AbstractCard, CardType, Expansion, RarityPair,
                         PhysicalCardSet, PhysicalCard, Artist, Keyword,
                         Printing,
                         MapPhysicalCardToPhysicalCardSet)
from .BaseAdapters import (IAbstractCard, IPhysicalCardSet, IRarityPair,
                           IExpansion, ICardType, IRarity, IArtist,
                           IPrinting, IPrintingName, IKeyword)


# Compability Patches


# pylint: disable=invalid-name
# IN name is from SQLObject
def IN(oCol, oListOrSelect):
    """Check explicitly for empty lists passed to the IN operator.

       Some databases engines (MySQL) don't handle them so just return False
       instead.
       """
    if not oListOrSelect:
        return False
    return SQLOBJ_IN(oCol, oListOrSelect)
# pylint: enable=invalid-name


# Filter Base Class
class Filter:
    """Base class for all filters"""

    types = ()

    @classmethod
    def get_values(cls):
        """Used by GUI tools and FilterParser to get/check acceptable values"""
        # We can't do this as an attribute, since we need a database connection
        # to fill in the values most times
        raise NotImplementedError  # pragma: no cover

    # pylint: disable=no-self-use
    # children need to be able to override this.
    def involves(self, _oCardSet):
        """Return true if the filter results change when oCardSet changes"""
        return self.is_physical_card_only()

    def select(self, cCardClass):
        """cCardClass.select(...) applying the filter to the selection."""
        return cCardClass.select(self._get_expression(),
                                 join=self._get_joins())

    def _get_expression(self):
        """Actual filter expression"""
        raise NotImplementedError  # pragma: no cover

    def _get_joins(self):
        """joins needed by the filter"""
        raise NotImplementedError  # pragma: no cover

    def is_physical_card_only(self):
        """Return true if this filter only operates on physical cards.

           Mainly used to handle various corner cases in the gui."""
        return 'PhysicalCard' in self.types and \
                'AbstractCard' not in self.types


# Collections of Filters
class FilterBox(Filter, list):
    """Base class for filter collections."""

    # pylint: disable=protected-access
    # we delibrately access protected members
    def _get_joins(self):
        """The joins required for the composite filter

           This is the union of the joins of the subfilters
           """
        aJoins = []
        for oSubFilter in self:
            aJoins.extend(oSubFilter._get_joins())
        return aJoins

    def _get_types(self):
        """Get types for a composite filter.

           This is the intersection of the types of the subfilters
           """
        aTypes = []
        if self:
            for sType in self[0].types:
                iLen = len([x for x in self if sType in x.types])
                if iLen == len(self):
                    aTypes.append(sType)
        return aTypes

    def involves(self, oCardSet):
        """Return true if any of the child results change with oCardSet"""
        bResult = False
        for oSubFilter in self:
            bResult = bResult or oSubFilter.involves(oCardSet)
        return bResult

    # We allow protected access here too
    types = property(fget=lambda self: self._get_types(),
                     doc="types supported by this filter")


class FilterAndBox(FilterBox):
    """AND a list of filters."""

    # pylint: disable=protected-access
    # we intentinally access protected members
    def _get_expression(self):
        """Combine filters with AND"""
        return AND(*[x._get_expression() for x in self])


class FilterOrBox(FilterBox):
    """OR a list of filters."""

    # pylint: disable=protected-access
    # we intentinally access protected members
    def _get_expression(self):
        """Combine filters with OR"""
        return OR(*[x._get_expression() for x in self])


# NOT Filter
class FilterNot(Filter):
    """NOT (negate) a filter."""

    def __init__(self, oSubFilter):
        self.__oSubFilter = oSubFilter
        if self.__oSubFilter is None:
            # Can happen if we're given a filter without values set
            # We use NotNull, so we end up matching everything
            self.__oSubFilter = NotNullFilter()

    def _get_joins(self):
        """Joins for not is null, as they are used in the sub-select"""
        return []

    # pylint: disable=protected-access
    # we are delibrately accesing protected members her
    # and in _get_expression
    types = property(fget=lambda self: self.__oSubFilter.types,
                     doc="types supported by this filter")

    def _get_expression(self):
        """The expression for the NOT filter.

           We generate a suitable subselect from self._oSubFilter, and
           negate the results of that.
           """
        # pylint: disable=no-member
        # SQLObject methods not detected by pylint
        oExpression = self.__oSubFilter._get_expression()
        aJoins = self.__oSubFilter._get_joins()
        if 'AbstractCard' in self.__oSubFilter.types:
            return NOT(IN(AbstractCard.q.id, Select(AbstractCard.q.id,
                                                    oExpression,
                                                    join=aJoins)))
        if 'PhysicalCard' in self.__oSubFilter.types:
            return NOT(IN(PhysicalCard.q.id, Select(PhysicalCard.q.id,
                                                    oExpression,
                                                    join=aJoins)))
        if 'PhysicalCardSet' in self.__oSubFilter.types:
            return NOT(IN(PhysicalCardSet.q.id, Select(PhysicalCardSet.q.id,
                                                       oExpression,
                                                       join=aJoins)))
        raise RuntimeError("FilterNot unable to handle sub-filter type.")


class CachedFilter(Filter):
    """A filter which caches joins and expression lookups"""

    def __init__(self, oFilter):
        # pylint: disable=protected-access
        # We delibrately access the protected members here, as that's
        # the point
        self._oSubFilter = oFilter
        self._oExpression = oFilter._get_expression()
        self._aJoins = oFilter._get_joins()

    def _get_expression(self):
        return self._oExpression

    def _get_joins(self):
        return self._aJoins

    # pylint: disable=protected-access
    # we are delibrately accesing protected members her
    types = property(fget=lambda self: self._oSubFilter.types,
                     doc="types supported by this filter")


# Null Filter
class NullFilter(Filter):
    """Return everything."""

    types = ('AbstractCard', 'PhysicalCard', 'PhysicalCardSet')

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_expression(self):
        return TRUE  # SQLite doesn't like True. Postgres doesn't like 1.

    def _get_joins(self):
        return []


# NotNullFilter
class NotNullFilter(NullFilter):
    """Return nothing"""

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_expression(self):
        return NOT(TRUE)  # See Null Filter


# Base Classes for Common Filter Idioms
class SingleFilter(Filter):
    """Base class for filters on single items which connect to AbstractCard
       via a mapping table.

       Sub-class should set self._oMapTable, self._oMapField and self._oId.
       """
    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression & _get_joins
    def _get_joins(self):
        # pylint: disable=no-member
        # SQLObject methods not detected by pylint
        return [LEFTJOINOn(None, self._oMapTable,
                           AbstractCard.q.id ==
                           self._oMapTable.q.abstract_card_id)]

    def _get_expression(self):
        # pylint: disable=no-member
        # SQLObject methods not detected by pylint
        return self._oIdField == self._oId


class MultiFilter(Filter):
    """Base class for filters on multiple items which connect to AbstractCard
       via a mapping table.

       Sub-class should set self._oMapTable, self._oMapField and self._aIds.
       """

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression & _get_joins
    def _get_joins(self):
        # pylint: disable=no-member
        # SQLObject methods not detected by pylint
        return [LEFTJOINOn(None, self._oMapTable,
                           AbstractCard.q.id ==
                           self._oMapTable.q.abstract_card_id)]

    def _get_expression(self):
        # pylint: disable=no-member
        # SQLObject methods not detected by pylint
        return IN(self._oIdField, self._aIds)


class DirectFilter(Filter):
    """Base class for filters which query AbstractTable directly."""

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_joins(self):
        return []


# Useful utiltiy function for filters using with
def split_list(aList):
    """Split a list of 'X with Y' strings into (X, Y) tuples"""
    aResults = []
    for sWithString in aList:
        try:
            sVal1, sVal2 = sWithString.split(' with ')
            aResults.append((sVal1, sVal2))
        except ValueError:
            return []
    return aResults


def make_table_alias(sTable):
    """In order to allow multiple filters to be AND together, filters need
       to create aliases of mapping tables so that, for example:

           FilterAndBox([DisciplineFilter('dom'), DisciplineFilter('obf')])

       produces a list of cards which have both dominate and obfuscate
       rather than an empty list.  The two discipline filters above need to
       join the abstract card table with two different copies of the
       mapping table to discipline pairs.
       """
    return Alias(sTable)


class ExpansionFilter(MultiFilter):
    """Filter AbstractCard on Expansion name"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sExpansion):
        self._aIds = [oP.id for oP in IExpansion(sExpansion).pairs]
        self._oMapTable = make_table_alias('abs_rarity_pair_map')
        self._oIdField = self._oMapTable.q.rarity_pair_id


class MultiExpansionFilter(MultiFilter):
    """Filter AbstractCard on multiple Expansion names"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, aExpansions):
        oPairs = []
        for sExp in aExpansions:
            oPairs += IExpansion(sExp).pairs
        self._aIds = [oP.id for oP in oPairs]
        self._oMapTable = make_table_alias('abs_rarity_pair_map')
        self._oIdField = self._oMapTable.q.rarity_pair_id


class ExpansionRarityFilter(SingleFilter):
    """Filter on Expansion & Rarity combo """
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, tExpanRarity):
        """ We use a tuple for Expansion and Rarity here to keep the
            same calling convention as for the Multi Filter"""
        sExpansion, sRarity = tExpanRarity
        self._oId = IRarityPair((IExpansion(sExpansion), IRarity(sRarity))).id
        self._oMapTable = make_table_alias('abs_rarity_pair_map')
        self._oIdField = self._oMapTable.q.rarity_pair_id


class MultiExpansionRarityFilter(MultiFilter):
    """Filter on multiple Expansion & Rarity combos"""
    keyword = "Expansion_with_Rarity"
    description = "Expansion with Rarity"
    helptext = "a list of expansions and rarities (each element specified" \
            " as an expansion with associated rarity).\nReturns all matching" \
            " cards."
    iswithfilter = True
    islistfilter = True
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, aExpansionRarities):
        """  Called with a list of Expansion + Rarity pairs"""
        self._aIds = []
        if isinstance(aExpansionRarities[0], str):
            aValues = split_list(aExpansionRarities)
        else:
            aValues = aExpansionRarities
        for sExpansion, sRarity in aValues:
            self._aIds.append(IRarityPair((IExpansion(sExpansion),
                                           IRarity(sRarity))).id)
        self._oMapTable = make_table_alias('abs_rarity_pair_map')
        self._oIdField = self._oMapTable.q.rarity_pair_id

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        aExpansions = [x.name for x in Expansion.select().orderBy('name')
                       if x.name[:5] != 'Promo']
        aResults = []
        for sExpan in aExpansions:
            oExpansion = IExpansion(sExpan)
            aRarities = [x.rarity.name for x in
                         RarityPair.selectBy(expansion=oExpansion)]
            for sRarity in aRarities:
                aResults.append(sExpan + ' with ' + sRarity)
        return aResults


class PrintingFilter(DirectFilter):
    """Filter on Printing Names"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sPrinting):
        """We filter for cards which appeared in a specific printing"""
        # This is a bit messy, but we extract all the physical cards
        # that belong to the printing, then filter on their abstract
        # card id's
        self._aIds = set()
        oPrinting = IPrinting(sPrinting)
        for oCard in PhysicalCard.selectBy(printing=oPrinting):
            self._aIds.add(oCard.abstractCardID)

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_expression(self):
        # pylint: disable=no-member
        # SQLObject confuses pylint
        return IN(AbstractCard.q.id, self._aIds)


class MultiPrintingFilter(DirectFilter):
    """Filter on multiple Printings"""
    keyword = "Printing"
    description = "Non-Default Printing"
    helptext = "a list of printings.\nReturns all cards that have appeared " \
            "in the specific printings."
    islistfilter = True
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, aPrintings):
        """  Called with a list of Printing Names"""
        self._aIds = set()
        # See comments on PrintingFilter
        for sPrint in aPrintings:
            oPrinting = IPrinting(sPrint)
            for oCard in PhysicalCard.selectBy(printing=oPrinting):
                self._aIds.add(oCard.abstractCardID)

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        """We restrict ourselves to non-standard printings, since the standard
           ones are covered by the expansion filters"""
        aExpPrint = [IPrintingName(x) for x in Printing.select()
                     if x.expansion.name[:5] != 'Promo' and x.name is not None]
        return sorted(aExpPrint)

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_expression(self):
        # pylint: disable=no-member
        # SQLObject confuses pylint
        return IN(AbstractCard.q.id, self._aIds)


class CardTypeFilter(SingleFilter):
    """Filter on card type"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sCardType):
        self._oId = ICardType(sCardType).id
        self._oMapTable = make_table_alias('abs_type_map')
        self._oIdField = self._oMapTable.q.card_type_id


class MultiCardTypeFilter(MultiFilter):
    """Filter on multiple card types"""
    keyword = "CardType"
    description = "Card Type"
    helptext = "a list of card types.\nReturns all cards of the given types"
    islistfilter = True
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, aCardTypes):
        self._aIds = [ICardType(x).id for x in aCardTypes]
        self._oMapTable = make_table_alias('abs_type_map')
        self._oIdField = self._oMapTable.q.card_type_id

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return [x.name for x in CardType.select().orderBy('name')]


class ArtistFilter(SingleFilter):
    """Filter on Card's artist"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sArtist):
        self._oId = IArtist(sArtist).id
        self._oMapTable = make_table_alias('abs_artist_map')
        self._oIdField = self._oMapTable.q.artist_id


class MultiArtistFilter(MultiFilter):
    """Filter on multiple artists"""
    keyword = "Artist"
    islistfilter = True
    description = "Artist"
    helptext = "a list of artists\nReturns all cards where one or more of" \
             " the specified artists has created art for the card."
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, aArtists):
        self._aIds = [IArtist(x).id for x in aArtists]
        self._oMapTable = make_table_alias('abs_artist_map')
        self._oIdField = self._oMapTable.q.artist_id

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return [x.name for x in Artist.select().orderBy('name')]


class KeywordFilter(SingleFilter):
    """Filter on Card's keyword"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sKeyword):
        self._oId = IKeyword(sKeyword).id
        self._oMapTable = make_table_alias('abs_keyword_map')
        self._oIdField = self._oMapTable.q.keyword_id


class MultiKeywordFilter(MultiFilter):
    """Filter on multiple keywords"""
    keyword = "Keyword"
    islistfilter = True
    description = "Keyword"
    helptext = "a list of keywords\nReturns all cards where one or more of" \
             " the specified keywords is associated with the card."
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, aKeywords):
        self._aIds = [IKeyword(x).id for x in aKeywords]
        self._oMapTable = make_table_alias('abs_keyword_map')
        self._oIdField = self._oMapTable.q.keyword_id

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return [x.keyword for x in Keyword.select().orderBy('keyword')]


class BaseCardTextFilter(DirectFilter):
    """Base for filters on Card Text

       This defines the basics of a card text filter, without any special
       logic for dealing with specially formatted text."""
    keyword = "CardText"
    description = "Card Text"
    helptext = "the desired card text to search for (% and _ can be used as " \
            "wildcards).\nReturns all cards whose text contains this string."
    istextentry = True
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sPattern):
        self._sPattern = sPattern.lower()

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return ''

    def _get_expression(self):
        # pylint: disable=no-member
        # SQLObject methods not detected by pylint
        return LIKE(func.LOWER(AbstractCard.q.text),
                    '%' + self._sPattern + '%')


class CardNameFilter(DirectFilter):
    """Filter on the name of the card"""
    keyword = "CardName"
    description = "Card Name"
    helptext = "the text to be matched against card names (% and _ can be " \
            "used as wildcards).\nReturns all cards whose name contains " \
            "this string"
    istextentry = True
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sPattern):
        self.__sPattern = sPattern.lower()

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return ''

    def _get_expression(self):
        # pylint: disable=no-member
        # SQLObject methods not detected by pylint
        return LIKE(AbstractCard.q.canonicalName,
                    '%' + self.__sPattern + '%')


class PhysicalCardFilter(Filter):
    """Filter for converting a filter on abstract cards to a filter on
       physical cards."""
    def __init__(self):
        # Specifies Physical Cards, intended to be anded with other filters
        pass

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_joins(self):
        # This is one of the filters allowed to
        # pass the AbstractCard table as a joining table.
        # The join is needed so filtering on abstract card properties can work
        # pylint: disable=no-member
        # SQLObject methods not detected by pylint
        oTable = Table('physical_card')
        return [LEFTJOINOn(None, AbstractCard,
                           AbstractCard.q.id == oTable.abstract_card_id)]

    def _get_expression(self):
        return TRUE  # SQLite doesn't like True. Postgres doesn't like 1.


class AbstractCardFilter(Filter):
    """Filter for converting a filter on physical cards to a filter on
       abstract cards."""
    # Not used in the gui, as it's quite fragile due to database differences.
    # Kept for documentation purposes and for use when directly using the
    # Filters.
    # Because of how SQL handles NULLs, combining this filter with
    # FilterNot(PhysicalX) will still only match cards in the PhysicalCard
    # list. This is hard to fix, partly due to the database differences
    # mentioned.
    #
    # FilterBox([AbstractCardFilter, PhysicalCardFilter, X]) is almost
    # certainly not going to do the right thing, due to the multiple joins
    # involved. We should never do that.
    def __init__(self):
        # speficies AbstractCards, intended to be and'ed with other filters
        pass

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_joins(self):
        # pylint: disable=no-member
        # SQLObject methods not detected by pylint
        oTable = Table('abstract_card')
        return [LEFTJOINOn(None, PhysicalCard,
                           PhysicalCard.q.abstractCardID == oTable.id)]

    def _get_expression(self):
        return TRUE  # See PhysicalCardFilter


class CardSetMultiCardCountFilter(DirectFilter):
    """Filter on number of cards in the Physical Card Set"""
    keyword = "CardCount"
    description = "Card Count"
    helptext = "a list of card numbers from a chosen card set (filters on " \
            "number of cards in the Card Set).\nReturns a list of cards " \
            "that have the chosen counts in the given card set."
    isfromfilter = True
    islistfilter = True
    types = ('PhysicalCard',)

    def __init__(self, aData):
        # aData is a list or tuple of the form (aCounts, sCardSetName)
        # Selects cards with a count in the range specified by aCounts from
        # the Physical Card Set sCardSetName
        # We rely on the joins to limit this to the appropriate card sets
        # pylint: disable=no-member
        # SQLObject methods not detected by pylint
        aIds = []
        try:
            aCounts, aCardSetName = aData
            if not isinstance(aCardSetName, list):
                aCardSetName = [aCardSetName]
            for sCardSetName in aCardSetName:
                try:
                    oCS = IPhysicalCardSet(sCardSetName)
                    aIds.append(oCS.id)
                except SQLObjectNotFound:
                    aCounts = []
        except ValueError:
            aCounts = []
        # strip whitespace before comparing stuff
        # aCounts may be a single string, so we can't use 'for x in aCounts'
        aCounts = {x.strip() for x in list(aCounts)}
        self._oFilters = []
        self._aCardSetIds = aIds
        self._oZeroQuery = None
        if '0' in aCounts:
            aCounts.remove('0')
            self._oZeroQuery = Select(
                PhysicalCard.q.abstractCardID,
                where=IN(MapPhysicalCardToPhysicalCardSet.q.physicalCardSetID,
                         aIds),
                join=LEFTJOINOn(
                    PhysicalCard, MapPhysicalCardToPhysicalCardSet,
                    PhysicalCard.q.id ==
                    MapPhysicalCardToPhysicalCardSet.q.physicalCardID),
                groupBy=PhysicalCard.q.abstractCardID,
                having=func.COUNT(PhysicalCard.q.abstractCardID) > 0)
        if '>30' in aCounts:
            aCounts.remove('>30')
            oGreater30Query = Select(
                PhysicalCard.q.abstractCardID,
                where=IN(MapPhysicalCardToPhysicalCardSet.q.physicalCardSetID,
                         aIds),
                join=LEFTJOINOn(
                    PhysicalCard, MapPhysicalCardToPhysicalCardSet,
                    PhysicalCard.q.id ==
                    MapPhysicalCardToPhysicalCardSet.q.physicalCardID),
                groupBy=(PhysicalCard.q.abstractCardID,
                         MapPhysicalCardToPhysicalCardSet.q.physicalCardSetID),
                having=func.COUNT(PhysicalCard.q.abstractCardID) > 30)
            self._oFilters.append(oGreater30Query)
        if aCounts:
            # SQLite doesn't like strings here, so convert to int
            oCountFilter = Select(
                PhysicalCard.q.abstractCardID,
                where=IN(MapPhysicalCardToPhysicalCardSet.q.physicalCardSetID,
                         aIds),
                join=LEFTJOINOn(
                    PhysicalCard, MapPhysicalCardToPhysicalCardSet,
                    PhysicalCard.q.id ==
                    MapPhysicalCardToPhysicalCardSet.q.physicalCardID),
                groupBy=(PhysicalCard.q.abstractCardID,
                         MapPhysicalCardToPhysicalCardSet.q.physicalCardSetID),
                having=IN(func.COUNT(PhysicalCard.q.abstractCardID),
                          [int(x) for x in aCounts]))
            self._oFilters.append(oCountFilter)

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        # Should this have a more staggered range split? 0..20, 20-30,
        # 30-40, >40 type thing?
        aCardSets = [x.name for x in PhysicalCardSet.select().orderBy('name')]
        aValues = [str(x) for x in range(0, 31)] + ['>30']
        return (aValues, aCardSets)

    def _get_expression(self):
        # We duplicate subselect logic here, rather than letting the database
        # handle it, because mysql handles this case very poorly, resulting in
        # horrible performance.  This approach, while ugly, is at least
        # reasonably fast on all the databases we're concerned with.
        # We create the actual filters here, which filter for cards with the
        # correct numbers as we can't create the lists in __init__ since
        # the numbers can change between calls to _get_expression
        # pylint: disable=no-member
        # SQLObject methods not detected by pylint
        aFinalFilters = []
        oConn = sqlhub.processConnection
        if self._oZeroQuery:
            oQuery = oConn.sqlrepr(self._oZeroQuery)
            aNonZeroIds = oConn.queryAll(oQuery)
            aFinalFilters.append(NOT(IN(PhysicalCard.q.abstractCardID,
                                        aNonZeroIds)))
        if self._oFilters:
            for oFilter in self._oFilters:
                # OR(*self._oFilters) doesn't do what I expected here, so
                # we manually fiddle stuff to get the right result
                oQuery = oConn.sqlrepr(oFilter)
                aIds = oConn.queryAll(oQuery)
                aFinalFilters.append(IN(PhysicalCard.q.abstractCardID, aIds))
        return OR(*aFinalFilters)

    def involves(self, oCardSet):
        return oCardSet.id in self._aCardSetIds


class PhysicalExpansionFilter(DirectFilter):
    """Filter PhysicalCard based on the PhysicalCard expansion"""
    types = ('PhysicalCard',)

    # We must be calling this with a PhysicalCardFilter for sensible results,
    # so we don't need any special join magic
    def __init__(self, sExpansion):
        self._aPrintings = []
        if sExpansion is not None:
            iId = IExpansion(sExpansion).id
            # Find all the printings with this ID
            self._aPrintings = [x.id for x in Printing.selectBy(expansion=iId)]


    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_expression(self):
        oTable = Table('physical_card')
        if self._aPrintings:
            return IN(oTable.printing_id, self._aPrintings)
        # None case
        # pylint: disable=singleton-comparison
        # Must be a comparison so SQLObject generates the correct SQL
        return oTable.printing_id == None


class MultiPhysicalExpansionFilter(DirectFilter):
    """Filter PhysicalCard based on a list of PhysicalCard expansions"""
    keyword = "PhysicalExpansion"
    description = "Physical Expansion"
    helptext = "a list of expansions.\nSelects cards with their expansion " \
            "set to the chosen expansions.\nThis will return all the " \
            "printings in a given expansion."
    types = ('PhysicalCard',)
    islistfilter = True
    __sUnspec = '  Unspecified Expansion'

    def __init__(self, aExpansions):
        self._aIds = []
        self.__bOrUnspec = False
        for sExpansion in aExpansions:
            if sExpansion is not None and sExpansion != self.__sUnspec:
                iId = IExpansion(sExpansion).id
                self._aIds.extend([x.id for x in
                                   Printing.selectBy(expansion=iId)])
            else:
                self.__bOrUnspec = True

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        aExpansions = [cls.__sUnspec]
        aExpansions.extend([x.name for x in Expansion.select().orderBy('name')
                            if x.name[:5] != 'Promo'])
        return aExpansions

    def _get_expression(self):
        oTable = Table('physical_card')
        # None in the IN statement doesn't do the right thing for me
        # pylint: disable=singleton-comparison
        # == None syntax required for SQLObject
        if self.__bOrUnspec and self._aIds:
            return OR(IN(oTable.printing_id, self._aIds),
                      oTable.printing_id == None)
        if self.__bOrUnspec:
            # Psycopg2 doesn't like IN(a, []) constructions
            return oTable.printing_id == None
        return IN(oTable.printing_id, self._aIds)


class PhysicalPrintingFilter(DirectFilter):
    """Filter PhysicalCard based on the PhysicalCard printing"""
    types = ('PhysicalCard',)

    # We must be calling this with a PhysicalCardFilter for sensible results,
    # so we don't need any special join magic
    def __init__(self, sExpPrint):
        self._iPrintID = None
        if sExpPrint is not None:
            oPrinting = IPrinting(sExpPrint)
            self._iPrintID = oPrinting.id

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_expression(self):
        oTable = Table('physical_card')
        return oTable.printing_id == self._iPrintID

class MultiPhysicalPrintingFilter(DirectFilter):
    """Filter PhysicalCard based on a list of PhysicalCard printings."""
    keyword = "PhysicalPrinting"
    description = "Physical Printing"
    helptext = "a list of printings.\nSelects cards with their printing " \
            "set to the chosen printings.\nThis will only return cards " \
            "with the specified printings, and will exclude cards from the " \
            "same expansion that aren't part of the given printing."
    types = ('PhysicalCard',)
    islistfilter = True
    __sUnspec = '  Unspecified Expansion'

    def __init__(self, aPrintings):
        self._aIds = []
        self.__bOrUnspec = False
        for sExpPrint in aPrintings:
            if sExpPrint is not None and sExpPrint != self.__sUnspec:
                iId = IPrinting(sExpPrint).id
                self._aIds.append(iId)
            else:
                self.__bOrUnspec = True

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        aExpPrint = [cls.__sUnspec]
        aExpPrint.extend([IPrintingName(x) for x in Printing.select()
                          if x.expansion.name[:5] != 'Promo'])
        return sorted(aExpPrint)

    def _get_expression(self):
        oTable = Table('physical_card')
        # None in the IN statement doesn't do the right thing for me
        # pylint: disable=singleton-comparison
        # == None syntax required for SQLObject
        if self.__bOrUnspec and self._aIds:
            return OR(IN(oTable.printing_id, self._aIds),
                      oTable.printing_id == None)
        if self.__bOrUnspec:
            # Psycopg2 doesn't like IN(a, []) constructions
            return oTable.printing_id == None
        return IN(oTable.printing_id, self._aIds)


class PhysicalCardSetFilter(Filter):
    """Filter on Physical Card Set membership"""
    types = ('PhysicalCard',)

    def __init__(self, sName):
        # Select cards belonging to a PhysicalCardSet
        self.__iCardSetId = IPhysicalCardSet(sName).id
        self.__oTable = Table('physical_map')

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_joins(self):
        # The join on the AbstractCard table is needed to enable filtering
        # physical card sets on abstract card propeties, since the base class
        # for physical card sets is the mapping table.
        # This is one of the only filters allowed to join like this
        # pylint: disable=no-member
        # SQLObject methods not detected by pylint
        return [
            LEFTJOINOn(None, PhysicalCard,
                       PhysicalCard.q.id == self.__oTable.physical_card_id),
            LEFTJOINOn(None, AbstractCard,
                       AbstractCard.q.id == PhysicalCard.q.abstractCardID),
        ]

    def _get_expression(self):
        return self.__oTable.physical_card_set_id == self.__iCardSetId

    def involves(self, oCardSet):
        return oCardSet.id == self.__iCardSetId


class MultiPhysicalCardSetFilter(Filter):
    """Filter on a list of Physical Card Sets"""
    keyword = "Card_Sets"
    description = "Card Sets"
    helptext = "a list of card sets names\nSelects cards in the " \
            "specified sets."
    islistfilter = True
    types = ('PhysicalCard',)

    # We don't need the join as in PhysicalCardSetFilter, because this is
    # never the base filter in the gui

    def __init__(self, aNames):
        # Select cards belonging to the PhysicalCardSet
        self.__aCardSetIds = []
        for sName in aNames:
            try:
                self.__aCardSetIds.append(IPhysicalCardSet(sName).id)
            except SQLObjectNotFound:
                # May happen if config has been edited, or pointed to new
                # database and so forth, convert to a more informative error
                raise RuntimeError(
                    "Unable to load Card Set (%s) for filter" % sName)
        self.__oTable = make_table_alias('physical_map')
        self.__oPT = Table('physical_card')

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        aNames = []
        for oCS in PhysicalCardSet.select():
            aNames.append(oCS.name)
        return aNames

    def _get_joins(self):
        return [LEFTJOINOn(None, self.__oTable,
                           self.__oPT.id == self.__oTable.q.physical_card_id)]

    def _get_expression(self):
        return IN(self.__oTable.q.physical_card_set_id, self.__aCardSetIds)

    def involves(self, oCardSet):
        return oCardSet.id in self.__aCardSetIds


class MultiPhysicalCardSetMapFilter(Filter):
    """Filter on a list of Physical Card Sets"""
    # This does the same join magic as for PhysicalCardSetFilter, so
    # it can be used for checking other card sets

    def __init__(self, aNames):
        # Select cards belonging to the PhysicalCardSet
        self.__aCardSetIds = []
        for sName in aNames:
            self.__aCardSetIds.append(IPhysicalCardSet(sName).id)
        self.__oTable = Table('physical_map')

    # pylint: disable=missing-docstring
    # don't need docstrings for get_values & _get_joins
    def _get_joins(self):
        # pylint: disable=no-member
        # SQLObject methods not detected by pylint
        return [
            LEFTJOINOn(None, PhysicalCard,
                       PhysicalCard.q.id == self.__oTable.physical_card_id),
            LEFTJOINOn(None, AbstractCard,
                       AbstractCard.q.id == PhysicalCard.q.abstractCardID),
        ]

    def _get_expression(self):
        return IN(self.__oTable.physical_card_set_id, self.__aCardSetIds)


class PhysicalCardSetInUseFilter(Filter):
    """Filter on a membership of Physical Card Sets marked in use"""
    keyword = "SetsInUse"
    description = "In the 'In Use' children of"
    helptext = "list of card sets\nSelects cards in the Card Sets marked " \
            "as in use that are children of the given card sets."
    islistfilter = True
    types = ('PhysicalCard',)

    def __init__(self, aParCardSets):
        # Select cards belonging to the PhysicalCardSet in use
        self.__aCardSetIds = []
        for oCS in PhysicalCardSet.select():
            if oCS.inuse and oCS.parent and oCS.parent.name in aParCardSets:
                self.__aCardSetIds.append(oCS.id)
        self.__oTable = make_table_alias('physical_map')
        self.__oPT = Table('physical_card')

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        aInUseCardSets = PhysicalCardSet.selectBy(inuse=True)
        aParents = set()
        for oSet in aInUseCardSets:
            if oSet.parent:
                aParents.add(oSet.parent.name)
        return list(aParents)

    def _get_joins(self):
        return [LEFTJOINOn(None, self.__oTable,
                           self.__oPT.id == self.__oTable.q.physical_card_id)]

    def _get_expression(self):
        return IN(self.__oTable.q.physical_card_set_id, self.__aCardSetIds)

    def involves(self, oCardSet):
        return oCardSet.id in self.__aCardSetIds


class SpecificCardFilter(DirectFilter):
    """This filter matches a single card.

       It is used in the GUI to test if a card is in the filter results set.
       """
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, oCard):
        self.__iCardId = IAbstractCard(oCard).id

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_expression(self):
        # pylint: disable=no-member
        # SQLObject methods not detected by pylint
        return AbstractCard.q.id == self.__iCardId


class SpecificCardIdFilter(DirectFilter):
    """This filter matches a single card by id."""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, iCardId):
        self.__iCardId = iCardId

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_expression(self):
        # pylint: disable=no-member
        # SQLObject methods not detected by pylint
        return AbstractCard.q.id == self.__iCardId


class MultiSpecificCardIdFilter(DirectFilter):
    """This filter matches multiple cards by id."""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, aCardIds):
        self.__aCardIds = aCardIds

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_expression(self):
        # pylint: disable=no-member
        # SQLObject methods not detected by pylint
        return IN(AbstractCard.q.id, self.__aCardIds)


class SpecificPhysCardIdFilter(DirectFilter):
    """This filter matches a single physical card by id.

       It is used in the GUI to test if a card is in the filter results set.
       """
    types = ('PhysicalCard',)

    def __init__(self, iCardId):
        self.__iCardId = iCardId

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_expression(self):
        # pylint: disable=no-member
        # SQLObject methods not detected by pylint
        return PhysicalCard.q.id == self.__iCardId

# Card Set Filters
# These filters are designed to select card sets from the database
# rather than cards, hence they aren't intended to be joined


# base filters, to be subclassed to PhysicalCardSet or AbstractClassSet
# as needed
class CardSetNameFilter(DirectFilter):
    """Filters on Card Set Name"""
    keyword = "CardSetName"
    description = "Card Set Name"
    helptext = "the text to be matched against card set names. " \
            "(% and _ can be used as wildcards.)\nReturns all card sets " \
            "whose name contains the given string."
    istextentry = True
    types = ('PhysicalCardSet',)

    def __init__(self, sPattern):
        self.__sPattern = sPattern.lower()
        self.oTable = Table('physical_card_set')

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return ''

    def _get_expression(self):
        return LIKE(func.LOWER(self.oTable.name),
                    '%' + self.__sPattern + '%')


class CardSetDescriptionFilter(DirectFilter):
    """Base class for CardSet filters on Card Set Description"""
    keyword = "CardSetDescription"
    description = "Card Set Description"
    helptext = "the text to be matched against card set description. " \
            "(% and _ can be used as wildcards.)\nReturns all card sets " \
            "containing the given string in the description."
    istextentry = True
    types = ('PhysicalCardSet',)

    def __init__(self, sPattern):
        self.__sPattern = sPattern.lower()
        # Subclasses will replace this with the correct table
        self.oTable = Table('physical_card_set')

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return ''

    def _get_expression(self):
        return LIKE(func.LOWER(self.oTable.comment),
                    '%' + self.__sPattern + '%')


class CardSetAuthorFilter(DirectFilter):
    """Base class for CardSet filters on Card Set Author"""
    keyword = "CardSetAuthor"
    description = "Card Set Author"
    helptext = "the text to be matched against card set Author. " \
            "(% and _ can be used as wildcards.)\nReturns all card sets "\
            "whose author includes the given string."
    istextentry = True
    types = ('PhysicalCardSet',)

    def __init__(self, sPattern):
        self.__sPattern = sPattern.lower()
        # Subclasses will replace this with the correct table
        self.oTable = Table('physical_card_set')

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return ''

    def _get_expression(self):
        return LIKE(func.LOWER(self.oTable.author),
                    '%' + self.__sPattern + '%')


class CardSetAnnotationsFilter(DirectFilter):
    """Base class for CardSet filters on Card Set Annotations"""
    keyword = "CardSetAnnotations"
    description = "Card Set Annotations"
    helptext = "the text to be matched against card set annotations. " \
            "(% and _ can be used as wildcards.)\nReturns all card sets " \
            "where the annotations contain the given string."
    istextentry = True
    types = ('PhysicalCardSet',)

    def __init__(self, sPattern):
        self.__sPattern = sPattern.lower()
        # Subclasses will replace this with the correct table
        self.oTable = Table('physical_card_set')

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return ''

    def _get_expression(self):
        return LIKE(func.LOWER(self.oTable.annotations),
                    '%' + self.__sPattern + '%')


class ParentCardSetFilter(MultiFilter):
    """Filters on Parent's Card Set"""
    keyword = "ParentCardSet"
    description = "Parent Card Set"
    helptext = "a list names of the parent card sets.\n" \
            "Returns all card sets with one of the selected card sets " \
            "as a parent."
    islistfilter = True
    types = ('PhysicalCardSet',)

    def __init__(self, aCardSets):
        # pylint: disable=no-member
        # SQLObject methods not detected by pylint
        self._aIds = [IPhysicalCardSet(x).id for x in aCardSets]
        self._oIdField = PhysicalCardSet.q.parent

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return [x.name for x in PhysicalCardSet.select().orderBy('name')]

    # Override _get_joins, since we don't join
    def _get_joins(self):
        return []


class CSPhysicalCardSetInUseFilter(DirectFilter):
    """Filter Physical Card Set on inuse status"""
    keyword = "CSSetsInUse"
    description = "Card Set Marked as in Use"
    helptext = "This filter takes no parameters\nSelects those Card Sets " \
            " in the Card Set List that are marked as in use."
    types = ('PhysicalCardSet',)

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return None

    def _get_expression(self):
        # pylint: disable=no-member
        # SQLObject methods not detected by pylint
        # pylint: disable=singleton-comparison
        # == True syntax required for SQLObject
        return PhysicalCardSet.q.inuse == True


def best_guess_filter(sName):
    """Create a filter for selecting close matches to a card name."""
    # Set the filter on the Card List to one the does a
    # Best guess search
    sFilterString = ' ' + sName.lower() + ' '
    # Kill the's in the string
    sFilterString = sFilterString.replace(' the ', ' ')
    # Kill commas, as possible issues
    sFilterString = sFilterString.replace(',', ' ')
    # Free style punctuation
    for sPunc in string.punctuation:
        sFilterString = sFilterString.replace(sPunc, '_')
    # Stolen semi-concept from soundex - replace vowels with wildcards
    # Should these be %'s ??
    # (Should at least handle the Rotscheck variation as it stands)
    sFilterString = sFilterString.replace('a', '_')
    sFilterString = sFilterString.replace('e', '_')
    sFilterString = sFilterString.replace('i', '_')
    sFilterString = sFilterString.replace('o', '_')
    sFilterString = sFilterString.replace('u', '_')
    # Normalise spaces and Wildcard spaces
    sFilterString = ' '.join(sFilterString.split())
    sFilterString = sFilterString.replace(' ', '%')
    # Add % on outside
    sFilterString = '%' + sFilterString + '%'
    return CardNameFilter(sFilterString)


def make_illegal_filter():
    """Creates a filter that excludes not legal for tournament play cards.

       Function to handle the case that the keyword isn't in the database."""
    try:
        # We use MultiKeywordFilter to work around a performance
        # oddity of sqlite, where IN(a, b) outperforms a == b
        # for large sets
        oLegalFilter = FilterNot(MultiKeywordFilter(['not for legal play']))
    except SQLObjectNotFound:
        # Fallback to no filter
        return NullFilter()
    return oLegalFilter
