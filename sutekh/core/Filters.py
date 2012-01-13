# Filters.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

# pylint: disable-msg=W0231, W0223, C0302
# W0231 - the base classes don't have useful __init__ methods, so we
# generally don't call __init__ when creating a new filter
# W0223 - not every abstract method is immediately overridden
# C0302 - the module is long, but keeping the filters together is the best
# option

"""Define all the filters provided in sutekh"""

from sutekh.core.SutekhObjects import AbstractCard, IAbstractCard, ICreed, \
        IVirtue, IClan, IDiscipline, IExpansion, ITitle, ISect, ICardType, \
        IPhysicalCardSet, IRarityPair, IRarity, Clan, \
        Discipline, CardType, Title, Creed, Virtue, Sect, Expansion, \
        RarityPair, PhysicalCardSet, PhysicalCard, IDisciplinePair, \
        MapPhysicalCardToPhysicalCardSet, Artist, Keyword, IArtist, IKeyword, \
        CRYPT_TYPES
from sqlobject import SQLObjectNotFound, AND, OR, NOT, LIKE, func, \
        IN as SQLOBJ_IN
from sqlobject.sqlbuilder import Table, Alias, LEFTJOINOn, Select, \
        SQLTrueClause as TRUE

# Compability Patches


# pylint: disable-msg=C0103
# IN name is from SQLObject
def IN(oCol, oListOrSelect):
    """Check explicitly for empty lists passed to the IN operator.

       Some databases engines (MySQL) don't handle them so just return False
       instead.
       """
    if not oListOrSelect:
        return False
    else:
        return SQLOBJ_IN(oCol, oListOrSelect)
# pylint: enable-msg=C0103


# Filter Base Class
class Filter(object):
    """Base class for all filters"""

    types = ()

    @classmethod
    def get_values(cls):
        """Used by GUI tools and FilterParser to get/check acceptable values"""
        # We can't do this as an attribute, since we need a database connection
        # to fill in the values most times
        raise NotImplementedError

    # pylint: disable-msg=R0201
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
        raise NotImplementedError

    def _get_joins(self):
        """joins needed by the filter"""
        raise NotImplementedError

    def is_physical_card_only(self):
        """Return true if this filter only operates on physical cards.

           Mainly used to handle various corner cases in the gui."""
        return 'PhysicalCard' in self.types and \
                'AbstractCard' not in self.types


# Collections of Filters
class FilterBox(Filter, list):
    """Base class for filter collections."""

    # pylint: disable-msg=W0212
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

    # W0212 applies here too
    types = property(fget=lambda self: self._get_types(),
            doc="types supported by this filter")


class FilterAndBox(FilterBox):
    """AND a list of filters."""

    # pylint: disable-msg=W0142, W0212
    # W0142 - *magic is needed by SQLObject
    # W0212 - we intentinally access protected members
    def _get_expression(self):
        """Combine filters with AND"""
        return AND(*[x._get_expression() for x in self])


class FilterOrBox(FilterBox):
    """OR a list of filters."""

    # pylint: disable-msg=W0142, W0212
    # W0142 - *magic is needed by SQLObject
    # W0212 - we intentinally access protected members
    def _get_expression(self):
        """Combine filters with OR"""
        return OR(*[x._get_expression() for x in self])


# NOT Filter
class FilterNot(Filter):
    """NOT (negate) a filter."""

    def __init__(self, oSubFilter):
        self.__oSubFilter = oSubFilter

    def _get_joins(self):
        """Joins for not is null, as they are used in the sub-select"""
        return []

    # pylint: disable-msg=W0212
    # W0212 - we are delibrately accesing protected members her
    # and in _get_expression
    types = property(fget=lambda self: self.__oSubFilter.types,
            doc="types supported by this filter")

    def _get_expression(self):
        """The expression for the NOT filter.

           We generate a suitable subselect from self._oSubFilter, and
           negate the results of that.
           """
        # pylint: disable-msg=E1101
        # E1101 - avoid SQLObject method not detected problems
        oExpression = self.__oSubFilter._get_expression()
        aJoins = self.__oSubFilter._get_joins()
        if 'AbstractCard' in self.__oSubFilter.types:
            return NOT(IN(AbstractCard.q.id, Select(AbstractCard.q.id,
                oExpression, join=aJoins)))
        elif 'PhysicalCard' in self.__oSubFilter.types:
            return NOT(IN(PhysicalCard.q.id, Select(PhysicalCard.q.id,
                oExpression, join=aJoins)))
        elif 'PhysicalCardSet' in self.__oSubFilter.types:
            return NOT(IN(PhysicalCardSet.q.id, Select(PhysicalCardSet.q.id,
                oExpression, join=aJoins)))
        else:
            raise RuntimeError("FilterNot unable to handle sub-filter type.")


class CachedFilter(Filter):
    """A filter which caches joins and expression lookups"""

    def __init__(self, oFilter):
        # pylint: disable-msg=W0212
        # We delibrately access the protected members here, as that's
        # the point
        self._oSubFilter = oFilter
        self._oExpression = oFilter._get_expression()
        self._aJoins = oFilter._get_joins()

    def _get_expression(self):
        return self._oExpression

    def _get_joins(self):
        return self._aJoins

    # pylint: disable-msg=W0212
    # W0212 - we are delibrately accesing protected members her
    types = property(fget=lambda self: self._oSubFilter.types,
            doc="types supported by this filter")


# Null Filter
class NullFilter(Filter):
    """Return everything."""

    types = ('AbstractCard', 'PhysicalCard', 'PhysicalCardSet')

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_expression(self):
        return TRUE  # SQLite doesn't like True. Postgres doesn't like 1.

    def _get_joins(self):
        return []


# Base Classes for Common Filter Idioms
class SingleFilter(Filter):
    """Base class for filters on single items which connect to AbstractCard
       via a mapping table.

       Sub-class should set self._oMapTable, self._oMapField and self._oId.
       """
    # pylint: disable-msg=E1101, C0111
    # E1101 - We expect subclasses to provide _oMapTable and friends
    # C0111 - don't need docstrings for _get_expression & _get_joins
    def _get_joins(self):
        return [LEFTJOINOn(None, self._oMapTable,
            AbstractCard.q.id == self._oMapTable.q.abstract_card_id)]

    def _get_expression(self):
        return self._oIdField == self._oId


class MultiFilter(Filter):
    """Base class for filters on multiple items which connect to AbstractCard
       via a mapping table.

       Sub-class should set self._oMapTable, self._oMapField and self._aIds.
       """

    # pylint: disable-msg=E1101, C0111
    # E1101 - We expect subclasses to provide _oMapTable and friends
    # C0111 - don't need docstrings for _get_expression & _get_joins
    def _get_joins(self):
        return [LEFTJOINOn(None, self._oMapTable,
            AbstractCard.q.id == self._oMapTable.q.abstract_card_id)]

    def _get_expression(self):
        return IN(self._oIdField, self._aIds)


class DirectFilter(Filter):
    """Base class for filters which query AbstractTable directly."""

    # pylint: disable-msg=C0111
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


# Individual Filters
class ClanFilter(SingleFilter):
    """Filter on Card's clan"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sClan):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self._oId = IClan(sClan).id
        self._oMapTable = make_table_alias('abs_clan_map')
        self._oIdField = self._oMapTable.q.clan_id


class MultiClanFilter(MultiFilter):
    """Filter on multiple clans"""
    keyword = "Clan"
    islistfilter = True
    description = "Clan"
    helptext = "a list of clans\nReturns all cards which require or are of" \
             " the specified clans"
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, aClans):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self._aIds = [IClan(x).id for x in aClans]
        self._oMapTable = make_table_alias('abs_clan_map')
        self._oIdField = self._oMapTable.q.clan_id

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return [x.name for x in Clan.select().orderBy('name')]


class DisciplineFilter(MultiFilter):
    """Filter on a card's disciplines"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sDiscipline):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self._aIds = [oP.id for oP in IDiscipline(sDiscipline).pairs]
        self._oMapTable = make_table_alias('abs_discipline_pair_map')
        self._oIdField = self._oMapTable.q.discipline_pair_id


class MultiDisciplineFilter(MultiFilter):
    """Filter on multiple disciplines"""
    keyword = "Discipline"
    description = "Discipline"
    helptext = "a list of disciplines.\nReturns a list of all cards which " \
            "have or require the selected disciplines."
    islistfilter = True
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, aDisciplines):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        oPairs = []
        for sDis in aDisciplines:
            oPairs += IDiscipline(sDis).pairs
        self._aIds = [oP.id for oP in oPairs]
        self._oMapTable = make_table_alias('abs_discipline_pair_map')
        self._oIdField = self._oMapTable.q.discipline_pair_id

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return [x.fullname for x in Discipline.select().orderBy('name')]


class ExpansionFilter(MultiFilter):
    """Filter AbstractCard on Expansion name"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sExpansion):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self._aIds = [oP.id for oP in IExpansion(sExpansion).pairs]
        self._oMapTable = make_table_alias('abs_rarity_pair_map')
        self._oIdField = self._oMapTable.q.rarity_pair_id


class MultiExpansionFilter(MultiFilter):
    """Filter AbstractCard on multiple Expansion names"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, aExpansions):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
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
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
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
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self._aIds = []
        if isinstance(aExpansionRarities[0], basestring):
            aValues = split_list(aExpansionRarities)
        else:
            aValues = aExpansionRarities
        for sExpansion, sRarity in aValues:
            self._aIds.append(IRarityPair((IExpansion(sExpansion),
                IRarity(sRarity))).id)
        self._oMapTable = make_table_alias('abs_rarity_pair_map')
        self._oIdField = self._oMapTable.q.rarity_pair_id

    # pylint: disable-msg=C0111
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


class DisciplineLevelFilter(MultiFilter):
    """Filter on discipline & level combo"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, tDiscLevel):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        sDiscipline, sLevel = tDiscLevel
        sLevel = sLevel.lower()
        assert sLevel in ('inferior', 'superior')
        # There will be 0 or 1 ids
        self._aIds = [oP.id for oP in IDiscipline(sDiscipline).pairs if
                oP.level == sLevel]
        self._oMapTable = make_table_alias('abs_discipline_pair_map')
        self._oIdField = self._oMapTable.q.discipline_pair_id


class MultiDisciplineLevelFilter(MultiFilter):
    """Filter on multiple discipline & level combos"""
    keyword = "Discipline_with_Level"
    description = "Discipline with Level"
    helptext = "a list of disciplines with levels (each element specified" \
            " as a discipline with associated level, i.e. superior or" \
            " inferior)\nReturns all matching cards."
    iswithfilter = True
    islistfilter = True
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, aDiscLevels):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self._aIds = []
        if isinstance(aDiscLevels[0], basestring):
            aValues = split_list(aDiscLevels)
        else:
            aValues = aDiscLevels
        for sDiscipline, sLevel in aValues:
            sLevel = sLevel.lower()
            assert sLevel in ('inferior', 'superior')
            self._aIds.extend([oP.id for oP in IDiscipline(sDiscipline).pairs
                    if oP.level == sLevel])
        self._oMapTable = make_table_alias('abs_discipline_pair_map')
        self._oIdField = self._oMapTable.q.discipline_pair_id

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        oTemp = MultiDisciplineFilter([])
        aDisciplines = oTemp.get_values()
        aResults = []
        for sDisc in aDisciplines:
            for sLevel in ('inferior', 'superior'):
                try:
                    # Check if the discipline pair exists
                    IDisciplinePair((sDisc, sLevel))
                except SQLObjectNotFound:
                    continue  # No, so skip this case
                aResults.append('%s with %s' % (sDisc, sLevel))
        return aResults


class CardTypeFilter(SingleFilter):
    """Filter on card type"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sCardType):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
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
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self._aIds = [ICardType(x).id for x in aCardTypes]
        self._oMapTable = make_table_alias('abs_type_map')
        self._oIdField = self._oMapTable.q.card_type_id

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return [x.name for x in CardType.select().orderBy('name')]


class CryptCardFilter(MultiFilter):
    """Filter on crypt card types"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self._aIds = [ICardType(x).id for x in CRYPT_TYPES]
        self._oMapTable = make_table_alias('abs_type_map')
        self._oIdField = self._oMapTable.q.card_type_id


class SectFilter(SingleFilter):
    """Filter on Sect"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sSect):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self._oId = ISect(sSect).id
        self._oMapTable = make_table_alias('abs_sect_map')
        self._oIdField = self._oMapTable.q.sect_id


class MultiSectFilter(MultiFilter):
    """Filter on Multiple Sects"""
    keyword = "Sect"
    description = "Sect"
    helptext = "a list of sects.\nReturns all cards belonging to the given" \
            " sects"
    islistfilter = True
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, aSects):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self._aIds = [ISect(x).id for x in aSects]
        self._oMapTable = make_table_alias('abs_sect_map')
        self._oIdField = self._oMapTable.q.sect_id

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return [x.name for x in Sect.select().orderBy('name')]


class TitleFilter(SingleFilter):
    """Filter on Title"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sTitle):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self._oId = ITitle(sTitle).id
        self._oMapTable = make_table_alias('abs_title_map')
        self._oIdField = self._oMapTable.q.title_id


class MultiTitleFilter(MultiFilter):
    """Filter on Multiple Titles"""
    keyword = "Title"
    description = "Title"
    helptext = "a list of titles.\nReturns all cards with the selected titles."
    islistfilter = True
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, aTitles):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self._aIds = [ITitle(x).id for x in aTitles]
        self._oMapTable = make_table_alias('abs_title_map')
        self._oIdField = self._oMapTable.q.title_id

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return [x.name for x in Title.select().orderBy('name')]


class CreedFilter(SingleFilter):
    """Filter on Creed"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sCreed):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self._oId = ICreed(sCreed).id
        self._oMapTable = make_table_alias('abs_creed_map')
        self._oIdField = self._oMapTable.q.creed_id


class MultiCreedFilter(MultiFilter):
    """Filter on Multiple Creed"""
    keyword = "Creed"
    description = "Creed"
    helptext = "a list of creeds.\nReturns all cards requiring or of the" \
            " selected creeds"
    islistfilter = True
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, aCreeds):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self._aIds = [ICreed(x).id for x in aCreeds]
        self._oMapTable = make_table_alias('abs_creed_map')
        self._oIdField = self._oMapTable.q.creed_id

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return [x.name for x in Creed.select().orderBy('name')]


class VirtueFilter(SingleFilter):
    """Filter on Virtue"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sVirtue):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self._oId = IVirtue(sVirtue).id
        self._oMapTable = make_table_alias('abs_virtue_map')
        self._oIdField = self._oMapTable.q.virtue_id


class MultiVirtueFilter(MultiFilter):
    """Filter on Multiple Virtues"""
    keyword = "Virtue"
    description = "Virtue"
    helptext = "a list of virtues.\nReturns all cards requiring or having " \
            "the selected virtues"
    islistfilter = True
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, aVirtues):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self._aIds = [IVirtue(x).id for x in aVirtues]
        self._oMapTable = make_table_alias('abs_virtue_map')
        self._oIdField = self._oMapTable.q.virtue_id

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return [x.fullname for x in Virtue.select().orderBy('name')]


class ArtistFilter(SingleFilter):
    """Filter on Card's artist"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sArtist):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
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
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self._aIds = [IArtist(x).id for x in aArtists]
        self._oMapTable = make_table_alias('abs_artist_map')
        self._oIdField = self._oMapTable.q.artist_id

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return [x.name for x in Artist.select().orderBy('name')]


class KeywordFilter(SingleFilter):
    """Filter on Card's keyword"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sKeyword):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
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
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self._aIds = [IKeyword(x).id for x in aKeywords]
        self._oMapTable = make_table_alias('abs_keyword_map')
        self._oIdField = self._oMapTable.q.keyword_id

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return [x.keyword for x in Keyword.select().orderBy('keyword')]


class GroupFilter(DirectFilter):
    """Filter on Group"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, iGroup):
        self.__iGroup = iGroup

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_expression(self):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        return AbstractCard.q.group == self.__iGroup


class MultiGroupFilter(DirectFilter):
    """Filter on multiple Groups"""
    keyword = "Group"
    description = "Group"
    helptext = "a list of groups.\nReturns all cards belonging to the " \
            "listed group."
    islistfilter = True
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, aGroups):
        self.__aGroups = [int(sV) for sV in aGroups if sV != 'Any']
        if 'Any' in aGroups:
            self.__aGroups.append(-1)

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        # pylint: disable-msg=E1101
        # E1101 - avoid SQLObject method not detected problems
        iMax = AbstractCard.select().max(AbstractCard.q.group)
        return [str(x) for x in range(1, iMax + 1)] + ['Any']

    def _get_expression(self):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        return IN(AbstractCard.q.group, self.__aGroups)


class CapacityFilter(DirectFilter):
    """Filter on Capacity"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, iCap):
        self.__iCap = iCap

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_expression(self):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        return AbstractCard.q.capacity == self.__iCap


class MultiCapacityFilter(DirectFilter):
    """Filter on a list of Capacities"""
    keyword = "Capacity"
    description = "Capacity"
    helptext = "a list of capacities.\nReturns all cards of the selected" \
            " capacities"
    islistfilter = True
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, aCaps):
        self.__aCaps = [int(sV) for sV in aCaps]

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        # pylint: disable-msg=E1101
        # E1101 - avoid SQLObject method not detected problems
        iMax = AbstractCard.select().max(AbstractCard.q.capacity)
        return [str(x) for x in range(1, iMax + 1)]

    def _get_expression(self):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        return IN(AbstractCard.q.capacity, self.__aCaps)


class CostFilter(DirectFilter):
    """Filter on Cost"""
    types = ('AbstractCard', 'PhysicalCard')

    # Should this exclude Vamps & Imbued, if we search for
    # cards without cost?
    def __init__(self, iCost):
        self.__iCost = iCost
        # Handle 0 correctly
        if not iCost:
            self.__iCost = None

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_expression(self):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        return AbstractCard.q.cost == self.__iCost


class MultiCostFilter(DirectFilter):
    """Filter on a list of Costs"""
    keyword = "Cost"
    description = "Cost"
    helptext = "a list of costs.\nReturns all cards with the given costs."
    islistfilter = True
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, aCost):
        self.__aCost = [int(sV) for sV in aCost if sV != 'X']
        self.__bZeroCost = False
        if 'X' in aCost:
            self.__aCost.append(-1)
        if 0 in self.__aCost:
            self.__bZeroCost = True
            self.__aCost.remove(0)

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        # pylint: disable-msg=E1101
        # E1101 - avoid SQLObject method not detected problems
        iMax = AbstractCard.select().max(AbstractCard.q.cost)
        return [str(x) for x in range(0, iMax + 1)] + ['X']

    def _get_expression(self):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        if self.__bZeroCost:
            if self.__aCost:
                return OR(IN(AbstractCard.q.cost, self.__aCost),
                        AbstractCard.q.cost == None)
            else:
                return AbstractCard.q.cost == None
        return IN(AbstractCard.q.cost, self.__aCost)


class CostTypeFilter(DirectFilter):
    """Filter on cost type"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sCostType):
        self.__sCostType = sCostType.lower()
        assert self.__sCostType in ("blood", "pool", "conviction", None)

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_expression(self):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        return AbstractCard.q.costtype == self.__sCostType.lower()


class MultiCostTypeFilter(DirectFilter):
    """Filter on a list of cost types"""
    keyword = "CostType"
    islistfilter = True
    description = "Cost Type"
    helptext = "a list of cost types.\nReturns cards requiring the selected" \
            " cost types."
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, aCostTypes):
        self.__aCostTypes = [x.lower() for x in aCostTypes if x is not None]
        for sCostType in self.__aCostTypes:
            assert sCostType in ("blood", "pool", "conviction")
        if None in aCostTypes:
            self.__aCostTypes.append(None)

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return ["blood", "pool", "conviction"]

    def _get_expression(self):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        return IN(AbstractCard.q.costtype, self.__aCostTypes)


class LifeFilter(DirectFilter):
    """Filter on life"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, iLife):
        self.__iLife = iLife

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_expression(self):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        return AbstractCard.q.life == self.__iLife


class MultiLifeFilter(DirectFilter):
    """Filter on a list of list values"""
    keyword = "Life"
    description = "Life"
    helptext = "a list of life values.\nReturns allies (both library and " \
            "crypt cards) and retainers with the selected life.\n" \
            "For cases where the life varies, only the base value for life " \
            "is used."
    islistfilter = True
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, aLife):
        self.__aLife = [int(sV) for sV in aLife]

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        # pylint: disable-msg=E1101
        # E1101 - avoid SQLObject method not detected problems
        iMax = AbstractCard.select().max(AbstractCard.q.life)
        return [str(x) for x in range(1, iMax + 1)]

    def _get_expression(self):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        return IN(AbstractCard.q.life, self.__aLife)


class CardTextFilter(DirectFilter):
    """Filter on Card Text"""
    keyword = "CardText"
    description = "Card Text"
    helptext = "the desired card text to search for (% can be used as a " \
            "wildcard).\nReturns all cards whose text contains this string."
    istextentry = True
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sPattern):
        self.__sPattern = sPattern.lower().encode('utf-8')

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return ''

    def _get_expression(self):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        return LIKE(func.LOWER(AbstractCard.q.text),
                '%' + self.__sPattern + '%')


class CardNameFilter(DirectFilter):
    """Filter on the name of the card"""
    keyword = "CardName"
    description = "Card Name"
    helptext = "the text to be matched against card names (% can be used " \
            "as a wildcard).\nReturns all cards whose name contains this " \
            "string"
    istextentry = True
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sPattern):
        self.__sPattern = sPattern.lower().encode('utf-8')

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return ''

    def _get_expression(self):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        return LIKE(AbstractCard.q.canonicalName,
                '%' + self.__sPattern + '%')


class CardFunctionFilter(DirectFilter):
    """Filter for various interesting card properties - untap, stealth, etc."""
    keyword = "CardFunction"
    description = "Card Function"
    helptext = "the chosen function from the list of supported types.\n" \
            "Functions include roles such as untap or bleed modifier.\n" \
            "Returns all cards matching the given functions."
    islistfilter = True
    types = ('AbstractCard', 'PhysicalCard')

    # Currently mainly used by the Hand Simulation plugin

    # Implementation discussion
    # Because we want flexiblity here, we define these filters in terms
    # of the existing filters - this avoids needing fancy
    # logic in _get_joins, and so forth
    # The filters can only be specificed after the database connection is
    # established, hence the list of constants and if .. constuction
    # in __init__, rather than using a class dictionary or similiar scheme

    __sStealth = 'Stealth action modifiers'
    __sIntercept = 'Intercept reactions'
    __sUntap = 'Untap reactions (Wake)'
    __sBounce = 'Bleed redirection reactions (Bounce)'
    __sEnterCombat = 'Enter combat actions (Rush)'
    __sBleedModifier = 'Increased bleed action modifiers'
    __sBleedAction = 'Increased bleed actions'
    __sBleedReduction = 'Bleed reduction reactions'

    def __init__(self, aTypes):
        aFilters = []
        if self.__sStealth in aTypes:
            aFilters.append(FilterAndBox([CardTypeFilter('Action Modifier'),
                CardTextFilter('+_ stealth')]))
        if self.__sIntercept in aTypes:
            aFilters.append(FilterAndBox([CardTypeFilter('Reaction'),
                CardTextFilter('+_ intercept')]))
        if self.__sUntap in aTypes:
            aFilters.append(FilterAndBox([CardTypeFilter('Reaction'),
                FilterOrBox([CardTextFilter('this vampire untaps'),
                    CardTextFilter('this reacting vampire untaps'),
                    CardTextFilter('untap this vampire'),
                    CardTextFilter('untap this reacting vampire'),
                    CardTextFilter('as though untapped')])]))
        if self.__sBounce in aTypes:
            aFilters.append(FilterAndBox([CardTypeFilter('Reaction'),
                CardTextFilter('is now bleeding')]))
        if self.__sEnterCombat in aTypes:
            aFilters.append(FilterAndBox([CardTypeFilter('Action'),
                CardTextFilter('(D) Enter combat')]))
        if self.__sBleedModifier in aTypes:
            aFilters.append(FilterAndBox([CardTypeFilter('Action Modifier'),
                CardTextFilter('+_ bleed')]))
        if self.__sBleedAction in aTypes:
            aFilters.append(FilterAndBox([CardTypeFilter('Action'),
                FilterOrBox([CardTextFilter('(D) bleed%at +_ bleed'),
                    CardTextFilter('(D) bleed%with +_ bleed')])]))
        if self.__sBleedReduction in aTypes:
            # Ordering of bleed and reduce not consistent, so we
            # use an AND filter, rather than 'reduce%bleed'
            aFilters.append(FilterAndBox([CardTypeFilter('Reaction'),
                CardTextFilter('bleed'), CardTextFilter('reduce')]))
        self._oFilter = FilterOrBox(aFilters)

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        """Values supported by this filter"""
        aVals = sorted([cls.__sStealth, cls.__sIntercept, cls.__sUntap,
            cls.__sBounce, cls.__sEnterCombat, cls.__sBleedModifier,
            cls.__sBleedAction, cls.__sBleedReduction,
            ])
        return aVals

    # pylint: disable-msg=W0212
    # we access protexted members intentionally
    def _get_joins(self):
        """Joins for the constructed filter"""
        return self._oFilter._get_joins()

    def _get_expression(self):
        """Expression for the constructed filter"""
        return self._oFilter._get_expression()


class PhysicalCardFilter(Filter):
    """Filter for converting a filter on abstract cards to a filter on
       physical cards."""
    def __init__(self):
        # Specifies Physical Cards, intended to be anded with other filters
        pass

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_joins(self):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        # This is one of the filters allowed to
        # pass the AbstractCard table as a joining table.
        # The join is needed so filtering on abstract card properties can work
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

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_joins(self):
        # pylint: disable-msg=E1101
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
        # pylint: disable-msg=E1101
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
        aCounts = set([x.strip() for x in list(aCounts)])
        self._oFilters = []
        self._aCardSetIds = aIds
        if '0' in aCounts:
            aCounts.remove('0')
            oZeroQuery = NOT(IN(PhysicalCard.q.abstractCardID, Select(
                PhysicalCard.q.abstractCardID,
                where=IN(MapPhysicalCardToPhysicalCardSet.q.physicalCardSetID,
                    aIds),
                join=LEFTJOINOn(PhysicalCard, MapPhysicalCardToPhysicalCardSet,
                    PhysicalCard.q.id ==
                    MapPhysicalCardToPhysicalCardSet.q.physicalCardID),
                groupBy=PhysicalCard.q.abstractCardID,
                having=func.COUNT(PhysicalCard.q.abstractCardID) > 0)))
            self._oFilters.append(oZeroQuery)
        if '>30' in aCounts:
            aCounts.remove('>30')
            oGreater30Query = IN(PhysicalCard.q.abstractCardID, Select(
                PhysicalCard.q.abstractCardID,
                where=IN(MapPhysicalCardToPhysicalCardSet.q.physicalCardSetID,
                    aIds),
                join=LEFTJOINOn(PhysicalCard, MapPhysicalCardToPhysicalCardSet,
                    PhysicalCard.q.id ==
                    MapPhysicalCardToPhysicalCardSet.q.physicalCardID),
                groupBy=(PhysicalCard.q.abstractCardID,
                    MapPhysicalCardToPhysicalCardSet.q.physicalCardSetID),
                having=func.COUNT(PhysicalCard.q.abstractCardID) > 30))
            self._oFilters.append(oGreater30Query)
        if aCounts:
            # SQLite doesn't like strings here, so convert to int
            oCountFilter = IN(PhysicalCard.q.abstractCardID, Select(
                PhysicalCard.q.abstractCardID,
                where=IN(MapPhysicalCardToPhysicalCardSet.q.physicalCardSetID,
                    aIds),
                join=LEFTJOINOn(PhysicalCard, MapPhysicalCardToPhysicalCardSet,
                    PhysicalCard.q.id ==
                    MapPhysicalCardToPhysicalCardSet.q.physicalCardID),
                groupBy=(PhysicalCard.q.abstractCardID,
                    MapPhysicalCardToPhysicalCardSet.q.physicalCardSetID),
                having=IN(func.COUNT(PhysicalCard.q.abstractCardID),
                    [int(x) for x in aCounts])))
            self._oFilters.append(oCountFilter)

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        # Should this have a more staggered range split? 0..20, 20-30,
        # 30-40, >40 type thing?
        aCardSets = [x.name for x in PhysicalCardSet.select().orderBy('name')]
        aValues = [str(x) for x in range(0, 31)] + ['>30']
        return (aValues, aCardSets)

    # pylint: disable-msg=W0142
    # *magic is needed by SQLObject
    def _get_expression(self):
        return OR(*self._oFilters)

    def involves(self, oCardSet):
        return oCardSet.id in self._aCardSetIds


class PhysicalExpansionFilter(DirectFilter):
    """Filter PhysicalCard based on the PhysicalCard expansion"""
    types = ('PhysicalCard',)

    # We must be calling this with a PhysicalCardFilter for sensible results,
    # so we don't need any special join magic
    def __init__(self, sExpansion):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        if sExpansion is not None:
            self._iId = IExpansion(sExpansion).id
        else:
            # physical Expansion can explicity be None
            self._iId = None

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_expression(self):
        oTable = Table('physical_card')
        return oTable.expansion_id == self._iId


class MultiPhysicalExpansionFilter(DirectFilter):
    """Filter PhysicalCard based on a list of PhysicalCard expansions"""
    keyword = "PhysicalExpansion"
    description = "Physical Expansion"
    helptext = "a list of expansions.\nSelects cards with their expansion " \
            "set to the chosen expansions."
    types = ('PhysicalCard',)
    islistfilter = True
    __sUnspec = '  Unspecified Expansion'

    def __init__(self, aExpansions):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self._aIds = []
        self.__bOrUnspec = False
        for sExpansion in aExpansions:
            if sExpansion is not None and sExpansion != self.__sUnspec:
                self._aIds.append(IExpansion(sExpansion).id)
            else:
                self.__bOrUnspec = True

    # pylint: disable-msg=C0111
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
        if self.__bOrUnspec and self._aIds:
            return OR(IN(oTable.expansion_id, self._aIds),
                    oTable.expansion_id == None)
        elif self.__bOrUnspec:
            # Psycopg2 doesn't like IN(a, []) constructions
            return oTable.expansion_id == None
        else:
            return IN(oTable.expansion_id, self._aIds)


class PhysicalCardSetFilter(Filter):
    """Filter on Physical Card Set membership"""
    types = ('PhysicalCard',)

    def __init__(self, sName):
        # Select cards belonging to a PhysicalCardSet
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self.__iCardSetId = IPhysicalCardSet(sName).id
        self.__oTable = Table('physical_map')

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_joins(self):
        # The join on the AbstractCard table is needed to enable filtering
        # physical card sets on abstract card propeties, since the base class
        # for physical card sets is the mapping table.
        # This is one of the only filters allowed to join like this
        # pylint: disable-msg=E1101
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
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self.__aCardSetIds = []
        for sName in aNames:
            self.__aCardSetIds.append(IPhysicalCardSet(sName).id)
        self.__oTable = make_table_alias('physical_map')
        self.__oPT = Table('physical_card')

    # pylint: disable-msg=C0111
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
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self.__aCardSetIds = []
        for sName in aNames:
            self.__aCardSetIds.append(IPhysicalCardSet(sName).id)
        self.__oTable = Table('physical_map')

    # pylint: disable-msg=C0111, E1101
    # E1101 - avoid SQLObject method not detected problems
    # C0111 - don't need docstrings for get_values & _get_joins
    def _get_joins(self):
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
    helptext = "Selects cards in the Card Sets marked " \
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

    # pylint: disable-msg=C0111
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
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self.__iCardId = IAbstractCard(oCard).id

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_expression(self):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        return AbstractCard.q.id == self.__iCardId


class SpecificCardIdFilter(DirectFilter):
    """This filter matches a single card by id."""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, iCardId):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self.__iCardId = iCardId

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_expression(self):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        return AbstractCard.q.id == self.__iCardId


class MultiSpecificCardIdFilter(DirectFilter):
    """This filter matches multiple cards by id."""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, aCardIds):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self.__aCardIds = aCardIds

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_expression(self):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        return IN(AbstractCard.q.id, self.__aCardIds)


class SpecificPhysCardIdFilter(DirectFilter):
    """This filter matches a single physical card by id.

       It is used in the GUI to test if a card is in the filter results set.
       """
    types = ('PhysicalCard',)

    def __init__(self, iCardId):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self.__iCardId = iCardId

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_expression(self):
        # pylint: disable-msg=E1101
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
    helptext = "the text to be matched against card set names.\n" \
            "% can be used as a wildcard.\nReturns all card sets containing " \
            "the given string."
    istextentry = True
    types = ('PhysicalCardSet',)

    def __init__(self, sPattern):
        self.__sPattern = sPattern.lower().encode('utf-8')
        self.oTable = Table('physical_card_set')

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return ''

    def _get_expression(self):
        return LIKE(func.LOWER(self.oTable.name), '%' + self.__sPattern
                + '%')


class CardSetDescriptionFilter(DirectFilter):
    """Base class for CardSet filters on Card Set Description"""
    keyword = "CardSetDescription"
    description = "Card Set Description"
    helptext = "the text to be matched against card set description.\n" \
            "% can be used as a wildcard.\nReturns all card sets containing " \
            "the given string."
    istextentry = True
    types = ('PhysicalCardSet',)

    def __init__(self, sPattern):
        self.__sPattern = sPattern.lower().encode('utf-8')
        # Subclasses will replace this with the correct table
        self.oTable = Table('physical_card_set')

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return ''

    def _get_expression(self):
        return LIKE(func.LOWER(self.oTable.comment), '%' + self.__sPattern
                + '%')


class CardSetAuthorFilter(DirectFilter):
    """Base class for CardSet filters on Card Set Author"""
    keyword = "CardSetAuthor"
    description = "Card Set Author"
    helptext = "the text to be matched against card set Author.\n" \
            "% can be used as a wildcard.\nReturns all card sets containing " \
            "the given string."
    istextentry = True
    types = ('PhysicalCardSet',)

    def __init__(self, sPattern):
        self.__sPattern = sPattern.lower().encode('utf-8')
        # Subclasses will replace this with the correct table
        self.oTable = Table('physical_card_set')

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return ''

    def _get_expression(self):
        return LIKE(func.LOWER(self.oTable.author), '%' + self.__sPattern
                + '%')


class CardSetAnnotationsFilter(DirectFilter):
    """Base class for CardSet filters on Card Set Annotations"""
    keyword = "CardSetAnnotations"
    description = "Card Set Annotations"
    helptext = "the text to be matched against card set annotations.\n" \
            "% can be used as a wildcard.\nReturns all card sets where the " \
            "annotations contrain the given string."
    istextentry = True
    types = ('PhysicalCardSet',)

    def __init__(self, sPattern):
        self.__sPattern = sPattern.lower().encode('utf-8')
        # Subclasses will replace this with the correct table
        self.oTable = Table('physical_card_set')

    # pylint: disable-msg=C0111
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
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        self._aIds = [IPhysicalCardSet(x).id for x in aCardSets]
        self._oIdField = PhysicalCardSet.q.parent

    # pylint: disable-msg=C0111
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
    helptext = "Selects those Card Sets in the Card Set List that are " \
            "marked as in use. This filter takes no parameters."
    types = ('PhysicalCardSet',)

    # pylint: disable-msg=C0111
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return None

    def _get_expression(self):
        # pylint: disable-msg=E1101
        # SQLObject methods not detected by pylint
        return PhysicalCardSet.q.inuse == True


def make_illegal_filter():
    """Creates a filter that excludes not legal for tournament play cards.

       Handles the case that the keyword hasn't been updated yet correctly."""
    oLegalFilter = NullFilter()
    try:
        # We use MultiKeywordFilter to work around a performance
        # oddity of sqlite, where IN(a, b) outperforms a == b
        # for large sets
        oLegalFilter = FilterNot(MultiKeywordFilter(['not for legal play']))
    except SQLObjectNotFound:
        oLegalFilter = FilterNot(CardTextFilter(
            'Added to the V:EKN banned list'))
    return oLegalFilter


# The List of filters exposed to the Filter Parser - new filters should just
# be tacked on here
PARSER_FILTERS = (
        MultiCardTypeFilter, MultiCostTypeFilter, MultiClanFilter,
        MultiDisciplineFilter, MultiGroupFilter, MultiCapacityFilter,
        MultiCostFilter, MultiLifeFilter, MultiCreedFilter, MultiVirtueFilter,
        CardTextFilter, CardNameFilter, MultiSectFilter, MultiTitleFilter,
        MultiExpansionRarityFilter, MultiDisciplineLevelFilter,
        MultiPhysicalExpansionFilter, CardSetNameFilter, CardSetAuthorFilter,
        CardSetDescriptionFilter, CardSetAnnotationsFilter,
        MultiPhysicalCardSetFilter, PhysicalCardSetInUseFilter,
        CardSetMultiCardCountFilter, CSPhysicalCardSetInUseFilter,
        CardFunctionFilter, ParentCardSetFilter, MultiArtistFilter,
        MultiKeywordFilter,
        )
