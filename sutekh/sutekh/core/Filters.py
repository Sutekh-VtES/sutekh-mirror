# Filters.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Minor modifications copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

from sutekh.core.SutekhObjects import AbstractCard, IAbstractCard, \
                                 ICreed, IVirtue, IClan, IDiscipline, \
                                 IExpansion, ITitle, ISect, ICardType, \
                                 IPhysicalCardSet, IAbstractCardSet, \
                                 IRarityPair, IRarity, \
                                 Clan, Discipline, CardType, Title,\
                                 Creed, Virtue, Sect, Expansion, \
                                 RarityPair
from sqlobject import AND, OR, LIKE, IN, func
from sqlobject.sqlbuilder import Table, Alias, LEFTJOINOn

# Filter Base Class

class Filter(object):
    def getValues(self):
        """Used by GUI tools and FilterParser to get/check acceptable values"""
        # We can't do this as an attribute, since we need a database connection
        # to fill in the values most times
        raise NotImplementedError

    def select(self,CardClass):
        """CardClass.select(...) applying the filter to the selection."""
        return CardClass.select(self._getExpression(),join=self._getJoins())

    def _getExpression(self):
        raise NotImplementedError

    def _getJoins(self):
        raise NotImplementedError

    def _makeTableAlias(self,sTable):
        """
        In order to allow multiple filters to be AND together, filters need
        to create aliases of mapping tables so that, for example:

            FilterAndBox([DisciplineFilter('dom'),DisciplineFilter('obf')])

        produces a list of cards which have both dominate and obfuscate
        rather than an empty list.  The two discipline filters above need to
        join the abstract card table with two different copies of the
        mapping table to discipline paits.
        """
        return Alias(sTable)

# Collections of Filters

class FilterBox(Filter,list):
    """Base class for filter collections."""

    def _getJoins(self):
        aJoins = []
        for x in self:
            aJoins.extend(x._getJoins())
        return aJoins

class FilterAndBox(FilterBox):
    """AND a list of filters."""

    def _getExpression(self):
        return AND(*[x._getExpression() for x in self])

class FilterOrBox(FilterBox):
    """OR a list of filters."""

    def _getExpression(self):
        return OR(*[x._getExpression() for x in self])

# Null Filter

class NullFilter(Filter):
    """Return everything."""

    def _getExpression(self):
        return None

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
        return IN(self._oIdField,self._aIds)

class DirectFilter(Filter):
    """Base class for filters which query AbstractTable directly."""

    def _getJoins(self):
        return []

# Individual Filters

class ClanFilter(SingleFilter):
    def __init__(self,sClan):
        self._oId = IClan(sClan).id
        self._oMapTable = self._makeTableAlias('abs_clan_map')
        self._oIdField = self._oMapTable.q.clan_id

class MultiClanFilter(MultiFilter):
    keyword = "Clan"
    description = "Clan"
    helptext = "a list of clans"

    def __init__(self,aClans):
        self._aIds = [IClan(x).id for x in aClans]
        self._oMapTable = self._makeTableAlias('abs_clan_map')
        self._oIdField = self._oMapTable.q.clan_id

    def getValues(self):
        return [x.name for x in Clan.select().orderBy('name')]

class DisciplineFilter(MultiFilter):
    def __init__(self,sDiscipline):
        self._aIds = [oP.id for oP in IDiscipline(sDiscipline).pairs]
        self._oMapTable = self._makeTableAlias('abs_discipline_pair_map')
        self._oIdField = self._oMapTable.q.discipline_pair_id

class MultiDisciplineFilter(MultiFilter):
    keyword = "Discipline"
    description = "Discipline"
    helptext = "a list of disciplines"

    def __init__(self,aDisciplines):
        oPairs = []
        for sDis in aDisciplines:
            oPairs += IDiscipline(sDis).pairs
        self._aIds = [oP.id for oP in oPairs]
        self._oMapTable = self._makeTableAlias('abs_discipline_pair_map')
        self._oIdField = self._oMapTable.q.discipline_pair_id

    def getValues(self):
        return [x.fullname for x in Discipline.select().orderBy('name')]

class ExpansionFilter(MultiFilter):
    def __init__(self,sExpansion):
        self._aIds = [oP.id for oP in IExpansion(sExpansion).pairs]
        self._oMapTable = self._makeTableAlias('abs_rarity_pair_map')
        self._oIdField = self._oMapTable.q.rarity_pair_id

class MultiExpansionFilter(MultiFilter):
    def __init__(self,aExpansions):
        oPairs = []
        for sExp in aExpansions:
            oPairs += IExpansion(sExp).pairs
        self._aIds = [oP.id for oP in oPairs]
        self._oMapTable = self._makeTableAlias('abs_rarity_pair_map')
        self._oIdField = self._oMapTable.q.rarity_pair_id

class ExpansionRarityFilter(SingleFilter):
    """ Filter on Expansion & Rarity combo """

    def __init__(self,tExpanRarity):
        """ We use a tuple for Expansion and Rarity here to keep the
            same calling convention as for the Multi Filter"""
        sExpansion, sRarity = tExpanRarity
        self._oId = IRarityPair((IExpansion(sExpansion),IRarity(sRarity))).id
        self._oMapTable = self._makeTableAlias('abs_rarity_pair_map')
        self._oIdField = self._oMapTable.q.rarity_pair_id

class MultiExpansionRarityFilter(MultiFilter):
    keyword = "Expansion_with_Rarity"
    description = "Expansion with Rarity"
    helptext = "a list of expansions and rarities,\n   each element specified as an expansion with associated rarity'"
    iswithfilter = True

    def __init__(self,aExpansionRarities):
        """  Called with a list of Expansion + Rarity pairs"""
        self._aIds = []
        for sExpansion, sRarity in aExpansionRarities:
            self._aIds.append(IRarityPair( (IExpansion(sExpansion),
                IRarity(sRarity)) ).id)
        self._oMapTable = self._makeTableAlias('abs_rarity_pair_map')
        self._oIdField = self._oMapTable.q.rarity_pair_id

    def getValues(self):
        aExpansions = [x.name for x in Expansion.select().orderBy('name')
                if x.name[:5] != 'Promo']
        aResults = []
        for sExpan in aExpansions:
            oE = IExpansion(sExpan)
            aRarities = [x.rarity.name for x in RarityPair.selectBy(expansion = oE)]
            for sRarity in aRarities:
                aResults.append(sExpan + ' with ' + sRarity)
        return aResults

class DisciplineLevelFilter(SingleFilter):
    def __init__(self,tDiscLevel):
        sDiscipline,sLevel = tDiscLevel
        # By construction, the list should have only 1 element
        self._oId = [oP.id for oP in IDiscipline(sDiscipline).pairs
                if oP.level == sLevel][0]
        self._oMapTable = self._makeTableAlias('abs_discipline_pair_map')
        self._oIdField = self._oMapTable.q.discipline_pair_id

class MultiDisciplineLevelFilter(MultiFilter):
    keyword = "Discipline_with_Level"
    description = "Discipline with Level"
    helptext = "a list of discipline with levels,\n   each element specified as a discipline with level'"
    iswithfilter = True

    def __init__(self,aDiscLevels):
        self._aIds = []
        for sDiscipline,sLevel in aDiscLevels:
            self._aIds.extend([oP.id for oP in IDiscipline(sDiscipline).pairs
                    if oP.level == sLevel])
        self._oMapTable = self._makeTableAlias('abs_discipline_pair_map')
        self._oIdField = self._oMapTable.q.discipline_pair_id

    def getValues(self):
        oTemp = MultiDisciplineFilter([])
        aDisciplines = oTemp.getValues()
        aResults = []
        for disc in aDisciplines:
            aResults.append(disc + ' with inferior')
            aResults.append(disc + ' with superior')
        return aResults

class CardTypeFilter(SingleFilter):
    def __init__(self,sCardType):
        self._oId = ICardType(sCardType).id
        self._oMapTable = self._makeTableAlias('abs_type_map')
        self._oIdField = self._oMapTable.q.card_type_id

class MultiCardTypeFilter(MultiFilter):
    keyword = "CardType"
    description = "Card Type"
    helptext = "a list of card types"

    def __init__(self,aCardTypes):
        self._aIds = [ICardType(x).id for x in aCardTypes]
        self._oMapTable = self._makeTableAlias('abs_type_map')
        self._oIdField = self._oMapTable.q.card_type_id

    def getValues(self):
        return [x.name for x in CardType.select().orderBy('name')]

class SectFilter(SingleFilter):
    def __init__(self,sSect):
        self._oId = ISect(sSect).id
        self._oMapTable = self._makeTableAlias('abs_sect_map')
        self._oIdField = self._oMapTable.q.sect_id

class MultiSectFilter(MultiFilter):
    keyword = "Sect"
    description = "Sect"
    helptext = "a list of sects"

    def __init__(self,aSects):
        self._aIds = [ISect(x).id for x in aSects]
        self._oMapTable = self._makeTableAlias('abs_sect_map')
        self._oIdField = self._oMapTable.q.sect_id

    def getValues(self):
        return [x.name for x in Sect.select().orderBy('name')]

class TitleFilter(SingleFilter):
    def __init__(self,sTitle):
        self._oId = ITitle(sTitle).id
        self._oMapTable = self._makeTableAlias('abs_title_map')
        self._oIdField = self._oMapTable.q.title_id

class MultiTitleFilter(MultiFilter):
    keyword = "Title"
    description = "Title"
    helptext = "a list of titles"

    def __init__(self,aTitles):
        self._aIds = [ITitle(x).id for x in aTitles]
        self._oMapTable = self._makeTableAlias('abs_title_map')
        self._oIdField = self._oMapTable.q.title_id

    def getValues(self):
        return [x.name for x in Title.select().orderBy('name')]

class CreedFilter(SingleFilter):
    def __init__(self,sCreed):
        self._oId = ICreed(sCreed).id
        self._oMapTable = self._makeTableAlias('abs_creed_map')
        self._oIdField = self._oMapTable.q.creed_id

class MultiCreedFilter(MultiFilter):
    keyword = "Creed"
    description = "Creed"
    helptext = "a list of creeds"

    def __init__(self,aCreeds):
        self._aIds = [ICreed(x).id for x in aCreeds]
        self._oMapTable = self._makeTableAlias('abs_creed_map')
        self._oIdField = self._oMapTable.q.creed_id

    def getValues(self):
        return [x.name for x in Creed.select().orderBy('name')]

class VirtueFilter(SingleFilter):
    def __init__(self,sVirtue):
        self._oId = IVirtue(sVirtue).id
        self._oMapTable = self._makeTableAlias('abs_virtue_map')
        self._oIdField = self._oMapTable.q.virtue_id

class MultiVirtueFilter(MultiFilter):
    keyword = "Virtue"
    description = "Virtue"
    helptext = "a list of virtues"

    def __init__(self,aVirtues):
        self._aIds = [IVirtue(x).id for x in aVirtues]
        self._oMapTable = self._makeTableAlias('abs_virtue_map')
        self._oIdField = self._oMapTable.q.virtue_id

    def getValues(self):
        return [x.fullname for x in Virtue.select().orderBy('name')]

class GroupFilter(DirectFilter):
    def __init__(self,iGroup):
        self.__iGroup = iGroup

    def _getExpression(self):
        return AbstractCard.q.group == self.__iGroup

class MultiGroupFilter(DirectFilter):
    keyword = "Group"
    description = "Group"
    helptext = "a list of groups"
    isnumericfilter = True

    def __init__(self,aGroups):
        self.__aGroups = aGroups

    def getValues(self):
        return range(1,6)

    def _getExpression(self):
        return IN(AbstractCard.q.group,self.__aGroups)

class CapacityFilter(DirectFilter):
    def __init__(self,iCap):
        self.__iCap = iCap

    def _getExpression(self):
        return AbstractCard.q.capacity == self.__iCap

class MultiCapacityFilter(DirectFilter):
    keyword = "Capacity"
    description = "Capacity"
    helptext = "a list of capacities"
    isnumericfilter = True

    def __init__(self,aCaps):
        self.__aCaps = aCaps

    def getValues(self):
        return range(1,12)

    def _getExpression(self):
        return IN(AbstractCard.q.capacity,self.__aCaps)

class CostFilter(DirectFilter):
    # Should this exclude Vamps & Imbued, if we search for
    # cards without cost?
    def __init__(self,iCost):
        self.__iCost = iCost

    def _getExpression(self):
        return AbstractCard.q.cost == self.__iCost

class MultiCostFilter(DirectFilter):
    keyword = "Cost"
    description = "Cost"
    helptext = "a list of costs"
    isnumericfilter = True

    def __init__(self,aCost):
        self.__aCost = aCost

    def getValues(self):
        return range(0,7) + ['X']

    def _getExpression(self):
        return IN(AbstractCard.q.cost,self.__aCost)

class CostTypeFilter(DirectFilter):
    def __init__(self,sCostType):
        self.__sCostType = sCostType

    def _getExpression(self):
        return AbstractCard.q.costtype == self.__sCostType.lower()

class MultiCostTypeFilter(DirectFilter):
    keyword = "CostType"
    description = "Cost Type"
    helptext = "a list of cost types"

    def __init__(self,aCostTypes):
        self.__aCostTypes = [x.lower() for x in aCostTypes]

    def getValues(self):
        return ["blood","pool","conviction"]

    def _getExpression(self):
        return IN(AbstractCard.q.costtype,self.__aCostTypes)

class LifeFilter(DirectFilter):
    # Will only return imbued, unless we ever parse life from retainers & allies
    def __init__(self,iLife):
        self.__iLife = iLife

    def _getExpression(self):
        return AbstractCard.q.life == self.__iLife

class MultiLifeFilter(DirectFilter):
    keyword = "Life"
    description = "Life"
    helptext = "a list of life values"
    isnumericfilter = True

    def __init__(self,aLife):
        self.__aLife = aLife

    def getValues(self):
        return range(1,8)

    def _getExpression(self):
        return IN(AbstractCard.q.life,self.__aLife)

class CardTextFilter(DirectFilter):
    keyword = "CardText"
    description = "Card Text"
    helptext = "the desired card text to search for. \n   % can be used as a wildcard"
    istextentry = True

    def __init__(self,sPattern):
        self.__sPattern = sPattern

    def getValues(self):
        return None

    def _getExpression(self):
        return LIKE(func.LOWER(AbstractCard.q.text),'%' + self.__sPattern.lower() + '%')

class CardNameFilter(DirectFilter):
    keyword = "CardName"
    description = "Card Name"
    helptext = "the text to be matched against card names.\n   % can be used as a wildcard"
    istextentry = True

    def __init__(self,sPattern):
        self.__sPattern = sPattern

    def getValues(self):
        return None

    def _getExpression(self):
        return LIKE(func.LOWER(AbstractCard.q.name),'%' + self.__sPattern.lower() + '%')

class PhysicalCardFilter(Filter):
    def __init__(self):
        # Specifies Physical Cards, intended to be anded with other filters
        pass

    def _getJoins(self):
        # This at PhysicalCardSetFilter are the only filters allowed to pass the AbstractCard table as a joining table.
        oT = Table('physical_card')
        return [LEFTJOINOn(None, AbstractCard, AbstractCard.q.id == oT.abstract_card_id)]

    def _getExpression(self):
        return True

class PhysicalCardSetFilter(Filter):
    def __init__(self,sName):
        # Select cards belonging to a PhysicalCardSet
        self.__iDeckId = IPhysicalCardSet(sName).id
        self.__oT = self._makeTableAlias('physical_map')
        self.__oPT = Table('physical_card')

    def _getJoins(self):
        # This and PhysicalCardFilter are the only filters allowed to pass the AbstractCard table as a joining table.
        return [LEFTJOINOn(None, AbstractCard, AbstractCard.q.id == self.__oPT.abstract_card_id),
                LEFTJOINOn(None, self.__oT, self.__oPT.id == self.__oT.q.physical_card_id)]

    def _getExpression(self):
        return self.__oT.q.physical_card_set_id == self.__iDeckId

class AbstractCardSetFilter(SingleFilter):
    def __init__(self,sName):
        # Select cards belonging to a AbstractCardSet
        self._oId = IAbstractCardSet(sName).id
        self._oMapTable = self._makeTableAlias('abstract_map')
        self._oIdField = self._oMapTable.q.abstract_card_set_id

class SpecificCardFilter(DirectFilter):
    def __init__(self,oCard):
        self.__iCardId = IAbstractCard(oCard).id

    def _getExpression(self):
        return AbstractCard.q.id == self.__iCardId
