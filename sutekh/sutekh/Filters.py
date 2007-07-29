# Filters.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Minor modifications copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

from sutekh.SutekhObjects import AbstractCard, IAbstractCard, PhysicalCard, \
                                 ICreed, IVirtue, IClan, IDiscipline, \
                                 IExpansion, ITitle, ISect, ICardType, \
                                 IPhysicalCardSet, IAbstractCardSet, \
                                 IRarityPair, IRarity
from sqlobject import AND, OR, LIKE, IN, func
from sqlobject.sqlbuilder import Table, Alias

# Filter Base Class

class Filter(object):
    def getExpression(self):
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
    pass

class FilterAndBox(FilterBox):
    def getExpression(self):
        return AND(*[x.getExpression() for x in self])

class FilterOrBox(FilterBox):
    def getExpression(self):
        return OR(*[x.getExpression() for x in self])

# Individual Filters

class ClanFilter(Filter):
    def __init__(self,sClan):
        self.__oClan = IClan(sClan)

    def getExpression(self):
        oT = self._makeTableAlias('abs_clan_map')
        return AND(AbstractCard.q.id == oT.q.abstract_card_id,
                   oT.q.clan_id == self.__oClan.id)

class MultiClanFilter(Filter):
    def __init__(self,aClans):
        self.__aClanIds = [IClan(x).id for x in aClans]

    def getExpression(self):
        oT = self._makeTableAlias('abs_clan_map')
        return AND(AbstractCard.q.id == oT.q.abstract_card_id,
                   IN(oT.q.clan_id,self.__aClanIds))

class DisciplineFilter(Filter):
    def __init__(self,sDiscipline):
        self.__aPairIds = [oP.id for oP in IDiscipline(sDiscipline).pairs]

    def getExpression(self):
        oT = self._makeTableAlias('abs_discipline_pair_map')
        return AND(AbstractCard.q.id == oT.q.abstract_card_id,
                   IN(oT.q.discipline_pair_id, self.__aPairIds))

class MultiDisciplineFilter(Filter):
    def __init__(self,aDisciplines):
        oPairs = []
        for sDis in aDisciplines:
            oPairs += IDiscipline(sDis).pairs
        self.__aPairIds = [oP.id for oP in oPairs]

    def getExpression(self):
        oT = self._makeTableAlias('abs_discipline_pair_map')
        return AND(AbstractCard.q.id == oT.q.abstract_card_id,
                   IN(oT.q.discipline_pair_id, self.__aPairIds))

class ExpansionFilter(Filter):
    def __init__(self,sExpansion):
        self.__aPairIds = [oP.id for oP in IExpansion(sExpansion).pairs]

    def getExpression(self):
        oT = self._makeTableAlias('abs_rarity_pair_map')
        return AND(AbstractCard.q.id == oT.q.abstract_card_id,
                   IN(oT.q.rarity_pair_id, self._aPairIds))

class MultiExpansionFilter(Filter):
    def __init__(self,aExpansions):
        oPairs = []
        for sExp in aExpansions:
            oPairs += IExpansion(sExp).pairs
        self.__aPairIds = [oP.id for oP in oPairs]

    def getExpression(self):
        oT = self._makeTableAlias('abs_rarity_pair_map')
        return AND(AbstractCard.q.id == oT.q.abstract_card_id,
                   IN(oT.q.rarity_pair_id, self.__aPairIds))

class ExpansionRarityFilter(Filter):
    """ Filter on Expansion & Rarity combo """

    def __init__(self,tExpanRarity):
        """ We use a tuple for Expansion and Rarity here to keep the
            same calling convention as for the Multi Filter"""
        sExpansion, sRarity = tExpanRarity
        self.__iExRarId = IRarityPair( (IExpansion(sExpansion),
                IRarity(sRarity)) ).id

    def getExpression(self):
        oT = self._makeTableAlias('abs_rarity_pair_map')
        return AND(AbstractCard.q.id == oT.q.abstract_card_id,
                   (oT.q.rarity_pair_id == self.__iExRarId ))

class MultiExpansionRarityFilter(Filter):
    def __init__(self,aExpansionRarities):
        """  Called with a list of Expansion+Rarity pairs"""
        self.__aIds=[]
        for sExpansion, sRarity in aExpansionRarities:
            self.__aIds.append(IRarityPair( (IExpansion(sExpansion),
                IRarity(sRarity)) ).id)

    def getExpression(self):
        oT = self._makeTableAlias('abs_rarity_pair_map')
        return AND(AbstractCard.q.id == oT.q.abstract_card_id,
                   IN (oT.q.rarity_pair_id,self.__aIds ))

class DisciplineLevelFilter(Filter):
    def __init__(self,tDiscLevel):
        sDiscipline,sLevel=tDiscLevel
        # By construction, the list should have only 1 element
        self.__iDiscId = [oP.id for oP in IDiscipline(sDiscipline).pairs
                if oP.level==sLevel][0]

    def getExpression(self):
        oT = self._makeTableAlias('abs_discipline_pair_map')
        return AND(AbstractCard.q.id == oT.q.abstract_card_id,
                   (oT.q.discipline_pair_id == self.__iDiscId))

class MultiDisciplineLevelFilter(Filter):
    def __init__(self,aDiscLevels):
        self.__aDiscIds=[]
        for sDiscipline,sLevel in aDiscLevels:
            self.__aDiscIds.extend([oP.id for oP in IDiscipline(sDiscipline).pairs
                    if oP.level==sLevel])

    def getExpression(self):
        oT = self._makeTableAlias('abs_discipline_pair_map')
        return AND(AbstractCard.q.id == oT.q.abstract_card_id,
                   IN(oT.q.discipline_pair_id, self.__aDiscIds))

class CardTypeFilter(Filter):
    def __init__(self,sCardType):
        self.__oType = ICardType(sCardType)

    def getExpression(self):
        oT = self._makeTableAlias('abs_type_map')
        return AND(AbstractCard.q.id == oT.q.abstract_card_id,
                   oT.q.card_type_id == self.__oType.id)

class MultiCardTypeFilter(Filter):
    def __init__(self,aCardTypes):
        self.__aTypeIds = [ICardType(x).id for x in aCardTypes]

    def getExpression(self):
        oT = self._makeTableAlias('abs_type_map')
        return AND(AbstractCard.q.id == oT.q.abstract_card_id,
                   IN(oT.q.card_type_id,self.__aTypeIds))

class SectFilter(Filter):
    def __init__(self,sSect):
        self.__oSect = ISect(sSect)

    def getExpression(self):
        oT = self._makeTableAlias('abs_sect_map')
        return AND(AbstractCard.q.id == oT.q.abstract_card_id,
                   oT.q.sect_id == self.__oSect.id)

class MultiSectFilter(Filter):
    def __init__(self,aSects):
        self.__aSectIds = [ISect(x).id for x in aSects]

    def getExpression(self):
        oT = self._makeTableAlias('abs_sect_map')
        return AND(AbstractCard.q.id == oT.q.abstract_card_id,
                   IN(oT.q.sect_id,self.__aSectIds))

class TitleFilter(Filter):
    def __init__(self,sTitle):
        self.__oTitle = ITitle(sTitle)

    def getExpression(self):
        oT = self._makeTableAlias('abs_title_map')
        return AND(AbstractCard.q.id == oT.q.abstract_card_id,
                   oT.q.title_id == self.__oTitle.id)

class MultiTitleFilter(Filter):
    def __init__(self,aTitles):
        self.__aTitleIds = [ITitle(x).id for x in aTitles]

    def getExpression(self):
        oT = self._makeTableAlias('abs_title_map')
        return AND(AbstractCard.q.id == oT.q.abstract_card_id,
                   IN(oT.q.title_id,self.__aTitleIds))

class CreedFilter(Filter):
    def __init__(self,sCreed):
        self.__oCreed = ICreed(sCreed)

    def getExpression(self):
        oT = self._makeTableAlias('abs_creed_map')
        return AND(AbstractCard.q.id == oT.q.abstract_card_id,
                   oT.q.creed_id == self.__oCreed.id)

class MultiCreedFilter(Filter):
    def __init__(self,aCreeds):
        self.__aCreedIds = [ICreed(x).id for x in aCreeds]

    def getExpression(self):
        oT = self._makeTableAlias('abs_creed_map')
        return AND(AbstractCard.q.id == oT.q.abstract_card_id,
                   IN(oT.q.creed_id,self.__aCreedIds))

class VirtueFilter(Filter):
    def __init__(self,sVirtue):
        self.__oVirtue = IVirtue(sVirtue)

    def getExpression(self):
        oT = self._makeTableAlias('abs_virtue_map')
        return AND(AbstractCard.q.id == oT.q.abstract_card_id,
                   oT.q.virtue_id == self.__oVirtue.id)

class MultiVirtueFilter(Filter):
    def __init__(self,aVirtues):
        self.__aVirtueIds = [IVirtue(x).id for x in aVirtues]

    def getExpression(self):
        oT = self._makeTableAlias('abs_virtue_map')
        return AND(AbstractCard.q.id == oT.q.abstract_card_id,
                   IN(oT.q.virtue_id,self.__aVirtueIds))

class GroupFilter(Filter):
    def __init__(self,iGroup):
        self.__iGroup = iGroup

    def getExpression(self):
        return AbstractCard.q.group == self.__iGroup

class MultiGroupFilter(Filter):
    def __init__(self,aGroups):
        self.__aGroups = aGroups

    def getExpression(self):
        return IN(AbstractCard.q.group,self.__aGroups)

class CapacityFilter(Filter):
    def __init__(self,iCap):
        self.__iCap = iCap

    def getExpression(self):
        return AbstractCard.q.capacity == self.__iCap

class MultiCapacityFilter(Filter):
    def __init__(self,aCaps):
        self.__aCaps = aCaps

    def getExpression(self):
        return IN(AbstractCard.q.capacity,self.__aCaps)

class CostFilter(Filter):
    # Should this exclude Vamps & Imbued, if we search for
    # cards without cost?
    def __init__(self,iCost):
        self.__iCost = iCost

    def getExpression(self):
        return AbstractCard.q.cost == self.__iCost

class MultiCostFilter(Filter):
    def __init__(self,aCost):
        self.__aCost = aCost

    def getExpression(self):
        return IN(AbstractCard.q.cost,self.__aCost)

class CostTypeFilter(Filter):
    def __init__(self,sCostType):
        self.__sCostType = sCostType

    def getExpression(self):
        return AbstractCard.q.costtype == self.__sCostType.lower()

class LifeFilter(Filter):
    # Will only return imbued, unless we ever parse life from retainers & allies
    def __init__(self,iLife):
        self.__iLife = iLife

    def getExpression(self):
        return AbstractCard.q.life == self.__iLife

class MultiLifeFilter(Filter):
    def __init__(self,aLife):
        self.__aLife = aLife

    def getExpression(self):
        return IN(AbstractCard.q.life,self.__aLife)

class CardTextFilter(Filter):
    def __init__(self,sPattern):
        self.__sPattern = sPattern

    def getExpression(self):
        return LIKE(func.LOWER(AbstractCard.q.text),'%' + self.__sPattern.lower() + '%')

class CardNameFilter(Filter):
    def __init__(self,sPattern):
        self.__sPattern = sPattern

    def getExpression(self):
        return LIKE(func.LOWER(AbstractCard.q.name),'%' + self.__sPattern.lower() + '%')

class PhysicalCardFilter(Filter):
    def __init__(self):
        # Specifies Physical Cards, intended to be anded with other filters
        pass

    def getExpression(self):
        oT = Table('physical_card')
        return AND(AbstractCard.q.id == oT.abstract_card_id)

class PhysicalCardSetFilter(Filter):
    def __init__(self,sName):
        # Select cards belonging to a PhysicalCardSet
        self.__iDeckId = IPhysicalCardSet(sName).id

    def getExpression(self):
        oT = self._makeTableAlias('physical_map')
        oPT = Table('physical_card')
        return AND(oT.q.physical_card_set_id == self.__iDeckId,
                   PhysicalCard.q.id == oT.q.physical_card_id,
                   AbstractCard.q.id == oPT.abstract_card_id)

class AbstractCardSetFilter(Filter):
    def __init__(self,sName):
        # Select cards belonging to a AbstractCardSet
        self.__iASCId = IAbstractCardSet(sName).id

    def getExpression(self):
        oT = self._makeTableAlias('abstract_map')
        oAT = Table('abstract_card')
        return AND(oT.q.abstract_card_set_id == self.__iASCId,
                oAT.id == oT.q.abstract_card_id)

class SpecificCardFilter(Filter):
    def __init__(self,oCard):
        self.__iCardId = IAbstractCard(oCard).id

    def getExpression(self):
        return (AbstractCard.q.id == self.__iCardId)
