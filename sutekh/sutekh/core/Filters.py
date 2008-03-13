# Filters.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

from sutekh.core.SutekhObjects import AbstractCard, IAbstractCard, \
                                 ICreed, IVirtue, IClan, IDiscipline, \
                                 IExpansion, ITitle, ISect, ICardType, \
                                 IPhysicalCardSet, IAbstractCardSet, \
                                 IRarityPair, IRarity, \
                                 Clan, Discipline, CardType, Title, \
                                 Creed, Virtue, Sect, Expansion, \
                                 RarityPair, PhysicalCardSet, PhysicalCard, \
                                 AbstractCardSet
from sqlobject import AND, OR, NOT, LIKE, func, IN as SQLOBJ_IN
from sqlobject.sqlbuilder import Table, Alias, LEFTJOINOn, Select, TRUE, FALSE

# Compability Patches

def IN(oCol,oListOrSelect):
    """Check explicitly for empty lists passed to the IN operator.
    
       Some databases engines (MySQL) don't handle them so just return False
       instead.
       """
    if not oListOrSelect:
        return False
    else:
        return SQLOBJ_IN(oCol,oListOrSelect)

# Filter Base Class

class Filter(object):
    @classmethod
    def get_values(cls):
        """Used by GUI tools and FilterParser to get/check acceptable values"""
        # We can't do this as an attribute, since we need a database connection
        # to fill in the values most times
        raise NotImplementedError

    def select(self, CardClass):
        """CardClass.select(...) applying the filter to the selection."""
        return CardClass.select(self._getExpression(), join=self._getJoins())

    def _getExpression(self):
        raise NotImplementedError

    def _getJoins(self):
        raise NotImplementedError

    def _makeTableAlias(self, sTable):
        """
        In order to allow multiple filters to be AND together, filters need
        to create aliases of mapping tables so that, for example:

            FilterAndBox([DisciplineFilter('dom'), DisciplineFilter('obf')])

        produces a list of cards which have both dominate and obfuscate
        rather than an empty list.  The two discipline filters above need to
        join the abstract card table with two different copies of the
        mapping table to discipline pairs.
        """
        return Alias(sTable)

# Collections of Filters

class FilterBox(Filter, list):
    """Base class for filter collections."""

    def _getJoins(self):
        aJoins = []
        for x in self:
            aJoins.extend(x._getJoins())
        return aJoins

    def _getTypes(self):
        """
        Get types for a composite filter.
        This is the intersection of the types of the subfilters
        """
        aTypes = []
        if len(self) > 0:
            for sType in self[0].types:
                iLen = len([x for x in self if sType in x.types])
                if iLen == len(self):
                    aTypes.append(sType)
        return aTypes

    types = property(fget= lambda self: self._getTypes())

class FilterAndBox(FilterBox):
    """AND a list of filters."""

    def _getExpression(self):
        return AND(*[x._getExpression() for x in self])

class FilterOrBox(FilterBox):
    """OR a list of filters."""

    def _getExpression(self):
        return OR(*[x._getExpression() for x in self])

# NOT Filter

class FilterNot(Filter):
    """NOT (negate) a filter."""

    def __init__(self, oSubFilter):
        self.__oSubFilter = oSubFilter

    def _getJoins(self):
        return []

    types = property(fget= lambda self: self.__oSubFilter.types)

    def _getExpression(self):
        oX = self.__oSubFilter._getExpression()
        aJ = self.__oSubFilter._getJoins()
        if 'AbstractCard' in self.__oSubFilter.types:
            return NOT(IN(AbstractCard.q.id, Select(AbstractCard.q.id, oX, join=aJ)))
        elif 'PhysicalCard' in self.__oSubFilter.types:
            return NOT(IN(PhysicalCard.q.id, Select(PhysicalCard.q.id, oX, join=aJ)))
        elif 'PhysicalCardSet' in self.__oSubFilter.types:
            return NOT(IN(PhysicalCardSet.q.id, Select(PhysicalCardSet.q.id, oX, join=aJ)))
        elif 'AbstractCardSet' in self.__oSubFilter.types:
            return NOT(IN(AbstractCardSet.q.id, Select(AbstractCardSet.q.id, oX, join=aJ)))

# Null Filter

class NullFilter(Filter):
    """Return everything."""

    types = ['AbstractCard', 'PhysicalCard', 'AbstractCardSet', 'PhysicalCardSet']

    def _getExpression(self):
        return TRUE # SQLite doesn't like True. Postgres doesn't like 1.

    def _getJoins(self):
        return []

# Base Classes for Common Filter Idioms

class SingleFilter(Filter):
    """Base class for filters on single items which connect to AbstractCard via a mapping table.

       Sub-class should set self._oMapTable, self._oMapField and self._oId.
       """

    def _getJoins(self):
        return [LEFTJOINOn(None, self._oMapTable, AbstractCard.q.id == self._oMapTable.q.abstract_card_id)]

    def _getExpression(self):
        return self._oIdField == self._oId

class MultiFilter(Filter):
    """Base class for filters on multiple items which connect to AbstractCard via a mapping table.

       Sub-class should set self._oMapTable, self._oMapField and self._aIds.
       """

    def _getJoins(self):
        return [LEFTJOINOn(None, self._oMapTable, AbstractCard.q.id == self._oMapTable.q.abstract_card_id)]

    def _getExpression(self):
        return IN(self._oIdField, self._aIds)

class DirectFilter(Filter):
    """Base class for filters which query AbstractTable directly."""

    def _getJoins(self):
        return []

# Useful utiltiy function for filters using with
def split_list(aList):
    """Split a list of 'X with Y' strings into (X, Y) tuples"""
    aResults = []
    for sWithString in aList:
        try:
            sVal1, sVal2 = sWithString.split(' with ')
            aResults.append( (sVal1, sVal2) )
        except ValueError:
            return []
    return aResults

# Individual Filters

class ClanFilter(SingleFilter):
    types = ['AbstractCard', 'PhysicalCard']
    def __init__(self, sClan):
        self._oId = IClan(sClan).id
        self._oMapTable = self._makeTableAlias('abs_clan_map')
        self._oIdField = self._oMapTable.q.clan_id

class MultiClanFilter(MultiFilter):
    keyword = "Clan"
    islistfilter = True
    description = "Clan"
    helptext = "a list of clans"
    types = ['AbstractCard', 'PhysicalCard']

    def __init__(self, aClans):
        self._aIds = [IClan(x).id for x in aClans]
        self._oMapTable = self._makeTableAlias('abs_clan_map')
        self._oIdField = self._oMapTable.q.clan_id

    @classmethod
    def get_values(cls):
        return [x.name for x in Clan.select().orderBy('name')]

class DisciplineFilter(MultiFilter):
    types = ['AbstractCard', 'PhysicalCard']
    def __init__(self, sDiscipline):
        self._aIds = [oP.id for oP in IDiscipline(sDiscipline).pairs]
        self._oMapTable = self._makeTableAlias('abs_discipline_pair_map')
        self._oIdField = self._oMapTable.q.discipline_pair_id

class MultiDisciplineFilter(MultiFilter):
    keyword = "Discipline"
    description = "Discipline"
    helptext = "a list of disciplines"
    islistfilter = True
    types = ['AbstractCard', 'PhysicalCard']

    def __init__(self, aDisciplines):
        oPairs = []
        for sDis in aDisciplines:
            oPairs += IDiscipline(sDis).pairs
        self._aIds = [oP.id for oP in oPairs]
        self._oMapTable = self._makeTableAlias('abs_discipline_pair_map')
        self._oIdField = self._oMapTable.q.discipline_pair_id

    @classmethod
    def get_values(cls):
        return [x.fullname for x in Discipline.select().orderBy('name')]

class ExpansionFilter(MultiFilter):
    types = ['AbstractCard', 'PhysicalCard']
    def __init__(self, sExpansion):
        self._aIds = [oP.id for oP in IExpansion(sExpansion).pairs]
        self._oMapTable = self._makeTableAlias('abs_rarity_pair_map')
        self._oIdField = self._oMapTable.q.rarity_pair_id

class MultiExpansionFilter(MultiFilter):
    types = ['AbstractCard', 'PhysicalCard']
    def __init__(self, aExpansions):
        oPairs = []
        for sExp in aExpansions:
            oPairs += IExpansion(sExp).pairs
        self._aIds = [oP.id for oP in oPairs]
        self._oMapTable = self._makeTableAlias('abs_rarity_pair_map')
        self._oIdField = self._oMapTable.q.rarity_pair_id

class ExpansionRarityFilter(SingleFilter):
    types = ['AbstractCard', 'PhysicalCard']
    """ Filter on Expansion & Rarity combo """

    def __init__(self, tExpanRarity):
        """ We use a tuple for Expansion and Rarity here to keep the
            same calling convention as for the Multi Filter"""
        sExpansion, sRarity = tExpanRarity
        self._oId = IRarityPair((IExpansion(sExpansion), IRarity(sRarity))).id
        self._oMapTable = self._makeTableAlias('abs_rarity_pair_map')
        self._oIdField = self._oMapTable.q.rarity_pair_id

class MultiExpansionRarityFilter(MultiFilter):
    keyword = "Expansion_with_Rarity"
    description = "Expansion with Rarity"
    helptext = "a list of expansions and rarities (each element specified as an expansion with associated rarity)"
    iswithfilter = True
    islistfilter = True
    types = ['AbstractCard', 'PhysicalCard']

    def __init__(self, aExpansionRarities):
        """  Called with a list of Expansion + Rarity pairs"""
        self._aIds = []
        if type(aExpansionRarities[0]) is str:
            aValues = split_list(aExpansionRarities)
        else:
            aValues = aExpansionRarities
        for sExpansion, sRarity in aValues:
            self._aIds.append(IRarityPair( (IExpansion(sExpansion),
                IRarity(sRarity)) ).id)
        self._oMapTable = self._makeTableAlias('abs_rarity_pair_map')
        self._oIdField = self._oMapTable.q.rarity_pair_id

    @classmethod
    def get_values(cls):
        aExpansions = [x.name for x in Expansion.select().orderBy('name')
                if x.name[:5] != 'Promo']
        aResults = []
        for sExpan in aExpansions:
            oE = IExpansion(sExpan)
            aRarities = [x.rarity.name for x in RarityPair.selectBy(expansion = oE)]
            for sRarity in aRarities:
                aResults.append(sExpan + ' with ' + sRarity)
        return aResults

class DisciplineLevelFilter(MultiFilter):
    types = ['AbstractCard', 'PhysicalCard']
    def __init__(self, tDiscLevel):
        sDiscipline, sLevel = tDiscLevel
        sLevel = sLevel.lower()
        assert sLevel in ['inferior', 'superior']
        # There will be 0 or 1 ids
        self._aIds = [oP.id for oP in IDiscipline(sDiscipline).pairs if oP.level == sLevel]
        self._oMapTable = self._makeTableAlias('abs_discipline_pair_map')
        self._oIdField = self._oMapTable.q.discipline_pair_id

class MultiDisciplineLevelFilter(MultiFilter):
    keyword = "Discipline_with_Level"
    description = "Discipline with Level"
    helptext = "a list of disciplines with levels (each element specified as a discipline with associated level, i.e. superior or inferior)"
    iswithfilter = True
    islistfilter = True
    types = ['AbstractCard', 'PhysicalCard']

    def __init__(self, aDiscLevels):
        self._aIds = []
        if type(aDiscLevels[0]) is str:
            aValues = split_list(aDiscLevels)
        else:
            aValues = aDiscLevels
        for sDiscipline, sLevel in aValues:
            sLevel = sLevel.lower()
            assert sLevel in ['inferior', 'superior']
            self._aIds.extend([oP.id for oP in IDiscipline(sDiscipline).pairs
                    if oP.level == sLevel])
        self._oMapTable = self._makeTableAlias('abs_discipline_pair_map')
        self._oIdField = self._oMapTable.q.discipline_pair_id

    @classmethod
    def get_values(cls):
        oTemp = MultiDisciplineFilter([])
        aDisciplines = oTemp.get_values()
        aResults = []
        for disc in aDisciplines:
            aResults.append(disc + ' with inferior')
            aResults.append(disc + ' with superior')
        return aResults

class CardTypeFilter(SingleFilter):
    types = ['AbstractCard', 'PhysicalCard']
    def __init__(self, sCardType):
        self._oId = ICardType(sCardType).id
        self._oMapTable = self._makeTableAlias('abs_type_map')
        self._oIdField = self._oMapTable.q.card_type_id

class MultiCardTypeFilter(MultiFilter):
    keyword = "CardType"
    description = "Card Type"
    helptext = "a list of card types"
    islistfilter = True
    types = ['AbstractCard', 'PhysicalCard']

    def __init__(self, aCardTypes):
        self._aIds = [ICardType(x).id for x in aCardTypes]
        self._oMapTable = self._makeTableAlias('abs_type_map')
        self._oIdField = self._oMapTable.q.card_type_id

    @classmethod
    def get_values(cls):
        return [x.name for x in CardType.select().orderBy('name')]

class SectFilter(SingleFilter):
    types = ['AbstractCard', 'PhysicalCard']
    def __init__(self, sSect):
        self._oId = ISect(sSect).id
        self._oMapTable = self._makeTableAlias('abs_sect_map')
        self._oIdField = self._oMapTable.q.sect_id

class MultiSectFilter(MultiFilter):
    keyword = "Sect"
    description = "Sect"
    helptext = "a list of sects"
    islistfilter = True
    types = ['AbstractCard', 'PhysicalCard']

    def __init__(self, aSects):
        self._aIds = [ISect(x).id for x in aSects]
        self._oMapTable = self._makeTableAlias('abs_sect_map')
        self._oIdField = self._oMapTable.q.sect_id

    @classmethod
    def get_values(cls):
        return [x.name for x in Sect.select().orderBy('name')]

class TitleFilter(SingleFilter):
    types = ['AbstractCard', 'PhysicalCard']
    def __init__(self, sTitle):
        self._oId = ITitle(sTitle).id
        self._oMapTable = self._makeTableAlias('abs_title_map')
        self._oIdField = self._oMapTable.q.title_id

class MultiTitleFilter(MultiFilter):
    keyword = "Title"
    description = "Title"
    helptext = "a list of titles"
    islistfilter = True
    types = ['AbstractCard', 'PhysicalCard']

    def __init__(self, aTitles):
        self._aIds = [ITitle(x).id for x in aTitles]
        self._oMapTable = self._makeTableAlias('abs_title_map')
        self._oIdField = self._oMapTable.q.title_id

    @classmethod
    def get_values(cls):
        return [x.name for x in Title.select().orderBy('name')]

class CreedFilter(SingleFilter):
    types = ['AbstractCard', 'PhysicalCard']
    def __init__(self, sCreed):
        self._oId = ICreed(sCreed).id
        self._oMapTable = self._makeTableAlias('abs_creed_map')
        self._oIdField = self._oMapTable.q.creed_id

class MultiCreedFilter(MultiFilter):
    keyword = "Creed"
    description = "Creed"
    helptext = "a list of creeds"
    islistfilter = True
    types = ['AbstractCard', 'PhysicalCard']

    def __init__(self, aCreeds):
        self._aIds = [ICreed(x).id for x in aCreeds]
        self._oMapTable = self._makeTableAlias('abs_creed_map')
        self._oIdField = self._oMapTable.q.creed_id

    @classmethod
    def get_values(cls):
        return [x.name for x in Creed.select().orderBy('name')]

class VirtueFilter(SingleFilter):
    types = ['AbstractCard', 'PhysicalCard']
    def __init__(self, sVirtue):
        self._oId = IVirtue(sVirtue).id
        self._oMapTable = self._makeTableAlias('abs_virtue_map')
        self._oIdField = self._oMapTable.q.virtue_id

class MultiVirtueFilter(MultiFilter):
    keyword = "Virtue"
    description = "Virtue"
    helptext = "a list of virtues"
    islistfilter = True
    types = ['AbstractCard', 'PhysicalCard']

    def __init__(self, aVirtues):
        self._aIds = [IVirtue(x).id for x in aVirtues]
        self._oMapTable = self._makeTableAlias('abs_virtue_map')
        self._oIdField = self._oMapTable.q.virtue_id

    @classmethod
    def get_values(cls):
        return [x.fullname for x in Virtue.select().orderBy('name')]

class GroupFilter(DirectFilter):
    types = ['AbstractCard', 'PhysicalCard']
    def __init__(self, iGroup):
        self.__iGroup = iGroup

    def _getExpression(self):
        return AbstractCard.q.group == self.__iGroup

class MultiGroupFilter(DirectFilter):
    keyword = "Group"
    description = "Group"
    helptext = "a list of groups"
    islistfilter = True
    types = ['AbstractCard', 'PhysicalCard']

    def __init__(self, aGroups):
        self.__aGroups = [int(sV) for sV in aGroups]

    @classmethod
    def get_values(cls):
        return [str(x) for x in range(1, 6)]

    def _getExpression(self):
        return IN(AbstractCard.q.group, self.__aGroups)

class CapacityFilter(DirectFilter):
    types = ['AbstractCard', 'PhysicalCard']
    def __init__(self, iCap):
        self.__iCap = iCap

    def _getExpression(self):
        return AbstractCard.q.capacity == self.__iCap

class MultiCapacityFilter(DirectFilter):
    keyword = "Capacity"
    description = "Capacity"
    helptext = "a list of capacities"
    islistfilter = True
    types = ['AbstractCard', 'PhysicalCard']

    def __init__(self, aCaps):
        self.__aCaps = [int(sV) for sV in aCaps]

    @classmethod
    def get_values(cls):
        return [str(x) for x in range(1, 12)]

    def _getExpression(self):
        return IN(AbstractCard.q.capacity, self.__aCaps)

class CostFilter(DirectFilter):
    types = ['AbstractCard', 'PhysicalCard']
    # Should this exclude Vamps & Imbued, if we search for
    # cards without cost?
    def __init__(self, iCost):
        self.__iCost = iCost

    def _getExpression(self):
        return AbstractCard.q.cost == self.__iCost

class MultiCostFilter(DirectFilter):
    keyword = "Cost"
    description = "Cost"
    helptext = "a list of costs"
    islistfilter = True
    types = ['AbstractCard', 'PhysicalCard']

    def __init__(self, aCost):
        self.__aCost = [int(sV) for sV in aCost if sV != 'X']
        if 'X' in aCost:
            self.__aCost.append(-1)

    @classmethod
    def get_values(cls):
        return [str(x) for x in range(0, 7)] + ['X']

    def _getExpression(self):
        return IN(AbstractCard.q.cost, self.__aCost)

class CostTypeFilter(DirectFilter):
    types = ['AbstractCard', 'PhysicalCard']
    def __init__(self, sCostType):
        self.__sCostType = sCostType.lower()
        assert self.__sCostType in ["blood", "pool", "conviction", None]

    def _getExpression(self):
        return AbstractCard.q.costtype == self.__sCostType.lower()

class MultiCostTypeFilter(DirectFilter):
    keyword = "CostType"
    islistfilter = True
    description = "Cost Type"
    helptext = "a list of cost types"
    types = ['AbstractCard', 'PhysicalCard']

    def __init__(self, aCostTypes):
        self.__aCostTypes = [x.lower() for x in aCostTypes if x is not None]
        for sCostType in self.__aCostTypes:
            assert sCostType in ["blood", "pool", "conviction"]
        if None in aCostTypes:
            self.__aCostTypes.append(None)

    @classmethod
    def get_values(cls):
        return ["blood", "pool", "conviction"]

    def _getExpression(self):
        return IN(AbstractCard.q.costtype, self.__aCostTypes)

class LifeFilter(DirectFilter):
    types = ['AbstractCard', 'PhysicalCard']
    # Will only return imbued, unless we ever parse life from retainers & allies
    def __init__(self, iLife):
        self.__iLife = iLife

    def _getExpression(self):
        return AbstractCard.q.life == self.__iLife

class MultiLifeFilter(DirectFilter):
    keyword = "Life"
    description = "Life"
    helptext = "a list of life values"
    islistfilter = True
    types = ['AbstractCard', 'PhysicalCard']

    def __init__(self, aLife):
        self.__aLife = [int(sV) for sV in aLife]

    @classmethod
    def get_values(cls):
        return [str(x) for x in range(1, 8)]

    def _getExpression(self):
        return IN(AbstractCard.q.life, self.__aLife)

class CardTextFilter(DirectFilter):
    keyword = "CardText"
    description = "Card Text"
    helptext = "the desired card text to search for (% can be used as a wildcard)"
    istextentry = True
    types = ['AbstractCard', 'PhysicalCard']

    def __init__(self, sPattern):
        self.__sPattern = sPattern.lower()

    @classmethod
    def get_values(cls):
        return ''

    def _getExpression(self):
        return LIKE(func.LOWER(AbstractCard.q.text), '%' + self.__sPattern + '%')

class CardNameFilter(DirectFilter):
    keyword = "CardName"
    description = "Card Name"
    helptext = "the text to be matched against card names (% can be used as a wildcard)"
    istextentry = True
    types = ['AbstractCard', 'PhysicalCard']

    def __init__(self, sPattern):
        self.__sPattern = sPattern

    @classmethod
    def get_values(cls):
        return ''

    def _getExpression(self):
        return LIKE(AbstractCard.q.canonicalName, '%' + self.__sPattern.lower() + '%')

class PhysicalCardFilter(Filter):
    def __init__(self):
        # Specifies Physical Cards, intended to be anded with other filters
        pass

    def _getJoins(self):
        # This, AbstractCardSetFilter and PhysicalCardSetFilter are the only filters allowed to pass the AbstractCard table as a joining table.
        # The join is needed so filtering on abstract card properties can work
        oT = Table('physical_card')
        return [LEFTJOINOn(None, AbstractCard, AbstractCard.q.id == oT.abstract_card_id)]

    def _getExpression(self):
        return TRUE # SQLite doesn't like True. Postgres doesn't like 1.

class MultiPhysicalCardCountFilter(DirectFilter):
    keyword = "PhysicalCardCount"
    description = "Physical Card Count"
    helptext = "a list of card numbers (filters on number of cards in the Physical Card list)"
    islistfilter = True
    types = ['AbstractCard', 'PhysicalCard']

    def __init__(self, aCounts):
        # Selects cards with a count in the range specified by aCounts
        aCounts = set(aCounts)
        self._oFilters = []
        if '0' in aCounts:
            aCounts.remove('0')
            # Doesn't seem to be a way to do a DISTINCT using sqlbuilder.Select,
            # so we fudge it with GROUP BY
            oZeroQuery = NOT(IN(AbstractCard.q.id, Select(PhysicalCard.q.abstractCardID,
                groupBy=PhysicalCard.q.abstractCardID)))
            self._oFilters.append(oZeroQuery)
        if '>30' in aCounts:
            aCounts.remove('>30')
            oGreater30Query = IN(AbstractCard.q.id, Select(PhysicalCard.q.abstractCardID,
                groupBy=PhysicalCard.q.abstractCardID,
                having=func.COUNT(PhysicalCard.q.abstractCardID) > 30))
            self._oFilters.append(oGreater30Query)
        if len(aCounts) > 0:
            # SQLite doesn't like strings here, so convert to int
            oCountFilter = IN(AbstractCard.q.id, Select(PhysicalCard.q.abstractCardID,
                groupBy=PhysicalCard.q.abstractCardID,
                having=IN(func.COUNT(PhysicalCard.q.abstractCardID),
                    [int(x) for x in aCounts])))
            self._oFilters.append(oCountFilter)

    @classmethod
    def get_values(cls):
        # Should this have a more staggered range split? 0..20, 20-30, 30-40, >40 type thing?
        return [str(x) for x in range(0, 30)] + ['>30']

    def _getExpression(self):
        return OR(*self._oFilters)

class PhysicalExpansionFilter(DirectFilter):
    types = ['PhysicalCard']
    # We must be calling this with a PhysicalCardFilter for sensible results,
    # so we don't need any special join magic
    def __init__(self, sExpansion):
        if sExpansion is not None:
            self._iId = IExpansion(sExpansion).id
        else:
            # physical Expansion can explicity be None
            self._iId = None

    def _getExpression(self):
        oT = Table('physical_card')
        return oT.expansion_id == self._iId

class MultiPhysicalExpansionFilter(DirectFilter):
    keyword = "PhysicalExpansion"
    description = "Physical Expansion"
    helptext = "a list of expansions (selects of physical cards with in the specified expansion)"
    types = ['PhysicalCard']
    islistfilter = True
    __sUnspec = '  Unspecified Expansion'

    def __init__(self, aExpansions):
        self._aIds = []
        self.__bOrUnspec = False
        for sExpansion in aExpansions:
            if sExpansion is not None and sExpansion != self.__sUnspec:
                self._aIds.append(IExpansion(sExpansion).id)
            else:
                self.__bOrUnspec = True

    @classmethod
    def get_values(cls):
        aExpansions = [cls.__sUnspec]
        aExpansions.extend([x.name for x in Expansion.select().orderBy('name')
                if x.name[:5] != 'Promo'])
        return aExpansions

    def _getExpression(self):
        oT = Table('physical_card')
        # None in the IN statement doesn't do the right thing for me
        if self.__bOrUnspec and len(self._aIds) > 0:
            return OR(IN(oT.expansion_id, self._aIds), oT.expansion_id == None)
        elif self.__bOrUnspec:
            # Psycopg2 doesn't like IN(a, []) constructions
            return oT.expansion_id == None
        else:
            return IN(oT.expansion_id, self._aIds)

class PhysicalCardSetFilter(Filter):
    types = ['PhysicalCard']
    def __init__(self, sName):
        # Select cards belonging to a PhysicalCardSet
        self.__iDeckId = IPhysicalCardSet(sName).id
        self.__oT = self._makeTableAlias('physical_map')
        self.__oPT = Table('physical_card')

    def _getJoins(self):
        # The join on the AbstractCard table is needed to enable filtering physical
        # card sets on abstract card propeties, since the base class for
        # physical card sets is the mapping table
        # Only this, PhysicalCardFilter and AbstractCardSetFilter can join to
        # the AbstractCard table like this
        return [LEFTJOINOn(None, AbstractCard, AbstractCard.q.id == self.__oPT.abstract_card_id),
                LEFTJOINOn(None, self.__oT, self.__oPT.id == self.__oT.q.physical_card_id)]

    def _getExpression(self):
        return self.__oT.q.physical_card_set_id == self.__iDeckId

class MultiPhysicalCardSetFilter(Filter):
    keyword = "PhysicalSet"
    description = "Physical Sets"
    helptext = "a list of deck names (selects physical cards in the specified decks)"
    islistfilter = True
    types = ['PhysicalCard']

    # We don't need the join as in PhysicalCardSetFilter, because this is
    # never the base filter in the gui

    def __init__(self, aNames):
        # Select cards belonging to the PhysicalCardSet
        self.__aDeckIds = []
        for sName in aNames:
            self.__aDeckIds.append(IPhysicalCardSet(sName).id)
        self.__oT = self._makeTableAlias('physical_map')
        self.__oPT = Table('physical_card')

    @classmethod
    def get_values(cls):
        aNames = []
        for oCS in PhysicalCardSet.select():
            aNames.append(oCS.name)
        return aNames

    def _getJoins(self):
        return [LEFTJOINOn(None, self.__oT, self.__oPT.id == self.__oT.q.physical_card_id)]

    def _getExpression(self):
        return IN(self.__oT.q.physical_card_set_id, self.__aDeckIds)

class PhysicalCardSetInUseFilter(Filter):
    keyword = "SetsInUse"
    description = "In Physical Card Sets in Use"
    helptext = "Selects physical cards in the Physical Card Sets marked as in use. This filter takes no parameters."
    types = ['PhysicalCard']

    def __init__(self):
        # Select cards belonging to the PhysicalCardSet in use
        self.__aDeckIds = []
        for oCS in PhysicalCardSet.select():
            if oCS.inuse:
                self.__aDeckIds.append(oCS.id)
        self.__oT = self._makeTableAlias('physical_map')
        self.__oPT = Table('physical_card')

    @classmethod
    def get_values(cls):
        return None

    def _getJoins(self):
        return [LEFTJOINOn(None, self.__oT, self.__oPT.id == self.__oT.q.physical_card_id)]

    def _getExpression(self):
        # We avoid IN(a, []) as it is fragile.
        # This + MultiPhysicalExpansionFilter are the only filters
        # the gui calls where this is possible with valid input, so
        # we treat as a special cases.
        if len(self.__aDeckIds) > 0:        
            return IN(self.__oT.q.physical_card_set_id, self.__aDeckIds)
        else:                                                   
            return FALSE # IN(a, []) is false

class AbstractCardSetFilter(SingleFilter):
    types = ['AbstractCard', 'PhysicalCard']
    def __init__(self, sName):
        # Select cards belonging to a AbstractCardSet
        self._oId = IAbstractCardSet(sName).id
        self._oMapTable = Table('abstract_map')
        self._oIdField = self._oMapTable.abstract_card_set_id

    def _getJoins(self):
        # This, PhysicalCardSetFilter and PhysicalCardFilter are the only filters allowed to pass the AbstractCard table as a joining table.
        # The join is needed so filtering on abstract card properties can work
        return [LEFTJOINOn(None, AbstractCard, AbstractCard.q.id == self._oMapTable.abstract_card_id)]

class SpecificCardFilter(DirectFilter):
    types = ['AbstractCard', 'PhysicalCard']
    def __init__(self, oCard):
        self.__iCardId = IAbstractCard(oCard).id

    def _getExpression(self):
        return AbstractCard.q.id == self.__iCardId


# Card Set Filters
# These filters are designed to select card sets from the database
# rather than cards, hence they aren't intended to be joined

# base filters, to be subclassed to PhysicalCardSet or AbstractClassSet
# as needed
class CardSetNameFilter(DirectFilter):
    keyword = "CardSetName"
    description = "Card Set Name"
    helptext = "the text to be matched against card set names.\n   % can be used as a wildcard"
    istextentry = True

    def __init__(self, sPattern):
        self.__sPattern = sPattern.lower()
        # Subclasses will replace this with the correct table
        self._oT = None

    @classmethod
    def get_values(cls):
        return ''

    def _getExpression(self):
        return LIKE(func.LOWER(self._oT.name), '%' + self.__sPattern + '%')

class CardSetDescriptionFilter(DirectFilter):
    keyword = "CardSetDescription"
    description = "Card Set Description"
    helptext = "the text to be matched against card set description.\n   % can be used as a wildcard"
    istextentry = True

    def __init__(self, sPattern):
        self.__sPattern = sPattern.lower()
        # Subclasses will replace this with the correct table
        self._oT = None

    @classmethod
    def get_values(cls):
        return ''

    def _getExpression(self):
        return LIKE(func.LOWER(self._oT.comment), '%' + self.__sPattern + '%')

class CardSetAuthorFilter(DirectFilter):
    keyword = "CardSetAuthor"
    description = "Card Set Author"
    helptext = "the text to be matched against card set Author.\n   % can be used as a wildcard"
    istextentry = True

    def __init__(self, sPattern):
        self.__sPattern = sPattern.lower()
        # Subclasses will replace this with the correct table
        self._oT = None

    @classmethod
    def get_values(cls):
        return ''

    def _getExpression(self):
        return LIKE(func.LOWER(self._oT.author), '%' + self.__sPattern + '%')

class CardSetAnnotationsFilter(DirectFilter):
    keyword = "CardSetAnnotations"
    description = "Card Set Annotations"
    helptext = "the text to be matched against card set annotations.\n   % can be used as a wildcard"
    istextentry = True

    def __init__(self, sPattern):
        self.__sPattern = sPattern.lower()
        # Subclasses will replace this with the correct table
        self._oT = None

    @classmethod
    def get_values(cls):
        return ''

    def _getExpression(self):
        return LIKE(func.LOWER(self._oT.annotations), '%' + self.__sPattern + '%')

# Abstract Card Set subclasses

class AbstractCardSetNameFilter(CardSetNameFilter):
    keyword = "AbstractCardSetName"
    description = "Abstract Card Set Name"
    types = ['AbstractCardSet']

    def __init__(self, sPattern):
        super(AbstractCardSetNameFilter, self).__init__(sPattern)
        self._oT = Table('abstract_card_set')

class AbstractCardSetDescriptionFilter(CardSetDescriptionFilter):
    keyword = "AbstractCardSetDescription"
    description = "Abstract Card Set Description"
    types = ['AbstractCardSet']

    def __init__(self, sPattern):
        super(AbstractCardSetDescriptionFilter, self).__init__(sPattern)
        self._oT = Table('abstract_card_set')

class AbstractCardSetAuthorFilter(CardSetAuthorFilter):
    keyword = "AbstractCardSetAuthor"
    description = "Abstract Card Set Author"
    types = ['AbstractCardSet']

    def __init__(self, sPattern):
        super(AbstractCardSetAuthorFilter, self).__init__(sPattern)
        self._oT = Table('abstract_card_set')

class AbstractCardSetAnnotationsFilter(CardSetAnnotationsFilter):
    keyword = "AbstractCardSetAnnotations"
    description = "Abstract Card Set Annotations"
    types = ['AbstractCardSet']

    def __init__(self, sPattern):
        super(AbstractCardSetAnnotationsFilter, self).__init__(sPattern)
        self._oT = Table('abstract_card_set')

# Physical Card Set subclasses

class PhysicalCardSetNameFilter(CardSetNameFilter):
    keyword = "PhysicalCardSetName"
    description = "Physical Card Set Name"
    types = ['PhysicalCardSet']

    def __init__(self, sPattern):
        super(PhysicalCardSetNameFilter, self).__init__(sPattern)
        self._oT = Table('physical_card_set')

class PhysicalCardSetDescriptionFilter(CardSetDescriptionFilter):
    keyword = "PhysicalCardSetDescription"
    description = "Physical Card Set Description"
    types = ['PhysicalCardSet']

    def __init__(self, sPattern):
        super(PhysicalCardSetDescriptionFilter, self).__init__(sPattern)
        self._oT = Table('physical_card_set')

class PhysicalCardSetAuthorFilter(CardSetAuthorFilter):
    keyword = "PhysicalCardSetAuthor"
    description = "Physical Card Set Author"
    types = ['PhysicalCardSet']

    def __init__(self, sPattern):
        super(PhysicalCardSetAuthorFilter, self).__init__(sPattern)
        self._oT = Table('physical_card_set')

class PhysicalCardSetAnnotationsFilter(CardSetAnnotationsFilter):
    keyword = "PhysicalCardSetAnnotations"
    description = "Physical Card Set Annotations"
    types = ['PhysicalCardSet']

    def __init__(self, sPattern):
        super(PhysicalCardSetAnnotationsFilter, self).__init__(sPattern)
        self._oT = Table('physical_card_set')

class PCSPhysicalCardSetInUseFilter(DirectFilter):
    keyword = "PCSSetsInUse"
    description = "Physical Card Set Marked as in Use"
    helptext = "Selects those Physical Card Sets in the Physical Card Set List that are marked as in use. This filter takes no parameters."
    types = ['PhysicalCardSet']

    @classmethod
    def get_values(cls):
        return None

    def _getExpression(self):
        return PhysicalCardSet.q.inuse == True

