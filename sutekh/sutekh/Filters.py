# Filters.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Minor modifications copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

from SutekhObjects import *
from sqlobject import AND, OR, LIKE
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

class CardTextFilter(Filter):
    def __init__(self,sPattern):
        self.__sPattern = sPattern

    def getExpression(self):
        return LIKE(AbstractCard.q.text,'%' + self.__sPattern + '%')

class PhysicalCardFilter(Filter):
    def __init__(self):
        # Specifies Physical Cards, intended to be anded with other filters
        pass

    def getExpression(self):
        oT = Table('physical_card')
        return AND(AbstractCard.q.id == oT.abstract_card_id)

class DeckFilter(Filter):
    def __init__(self,sName):
        # Select cards belonging to a deck
        self.__iDeckId = IPhysicalCardSet(sName).id

    def getExpression(self):
        oT = self._makeTableAlias('physical_map')
        oPT = Table('physical_card')
        return AND(oT.q.physical_card_set_id == self.__iDeckId,
                   PhysicalCard.q.id == oT.q.physical_card_id,
                   AbstractCard.q.id == oPT.abstract_card_id)

class SpecificCardFilter(Filter):
    def __init__(self,oCard):
        self.__iCardId = IAbstractCard(oCard).id

    def getExpression(self):
        return (AbstractCard.q.id == self.__iCardId)
