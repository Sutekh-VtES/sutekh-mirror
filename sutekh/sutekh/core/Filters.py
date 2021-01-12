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

from sqlobject.sqlbuilder import LEFTJOINOn
from sqlobject import SQLObjectNotFound, OR, LIKE, func

from sutekh.base.core.BaseTables import AbstractCard
from sutekh.base.core.BaseAdapters import ICardType
# pylint: disable=unused-import
# We want sutekh.core.Filters to import all the filters elsewhere,
# so we import filters we don't use here
from sutekh.base.core.BaseFilters import (IN, Filter, FilterAndBox,
                                          FilterOrBox, FilterNot, NullFilter,
                                          SingleFilter, MultiFilter,
                                          DirectFilter,
                                          PhysicalCardFilter,
                                          SpecificCardFilter,
                                          CardNameFilter,
                                          SpecificCardIdFilter,
                                          CardTypeFilter,
                                          SpecificPhysCardIdFilter,
                                          CardSetMultiCardCountFilter,
                                          PhysicalCardSetFilter,
                                          MultiPhysicalCardSetFilter,
                                          PhysicalCardSetInUseFilter,
                                          CardSetNameFilter, ExpansionFilter,
                                          MultiExpansionFilter,
                                          CardSetDescriptionFilter,
                                          CardSetAuthorFilter,
                                          CardSetAnnotationsFilter,
                                          ParentCardSetFilter,
                                          MultiExpansionRarityFilter,
                                          CSPhysicalCardSetInUseFilter,
                                          ExpansionRarityFilter,
                                          MultiCardTypeFilter,
                                          BaseCardTextFilter,
                                          KeywordFilter, MultiKeywordFilter,
                                          PrintingFilter,
                                          MultiPrintingFilter,
                                          PhysicalExpansionFilter,
                                          MultiPhysicalExpansionFilter,
                                          PhysicalPrintingFilter,
                                          MultiPhysicalPrintingFilter,
                                          ArtistFilter,
                                          MultiArtistFilter,
                                          split_list, make_table_alias)
# pylint: enable=unused-import

from sutekh.core.SutekhTables import (SutekhAbstractCard, Clan, Discipline,
                                      Title, Creed, Virtue, Sect, CRYPT_TYPES)
from sutekh.core.SutekhAdapters import (ICreed, IVirtue, IClan, IDiscipline,
                                        ITitle, ISect, IDisciplinePair)


class SutekhCardFilter(Filter):
    """Base class for filters that required joining SutekhAbstractCard
       to AbstractCard.

       Needs a table alias for when multiple filters are combined."""

    def __init__(self):
        self._oMapTable = make_table_alias('sutekh_abstract_card')
        super().__init__()

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_joins(self):
        # pylint: disable=no-member
        # avoid SQLObject method not detected problems
        return [LEFTJOINOn(None, self._oMapTable,
                           AbstractCard.q.id == self._oMapTable.q.id)]


# Individual Filters
class ClanFilter(SingleFilter):
    """Filter on Card's clan"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sClan):
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
        self._aIds = [IClan(x).id for x in aClans]
        self._oMapTable = make_table_alias('abs_clan_map')
        self._oIdField = self._oMapTable.q.clan_id

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return [x.name for x in Clan.select().orderBy('name')]


class DisciplineFilter(MultiFilter):
    """Filter on a card's disciplines"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sDiscipline):
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
        oPairs = []
        for sDis in aDisciplines:
            oPairs += IDiscipline(sDis).pairs
        self._aIds = [oP.id for oP in oPairs]
        self._oMapTable = make_table_alias('abs_discipline_pair_map')
        self._oIdField = self._oMapTable.q.discipline_pair_id

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return [x.fullname for x in Discipline.select().orderBy('name')]


class DisciplineLevelFilter(MultiFilter):
    """Filter on discipline & level combo"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, tDiscLevel):
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
        self._aIds = []
        if isinstance(aDiscLevels[0], str):
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

    # pylint: disable=missing-docstring
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


class CryptCardFilter(MultiFilter):
    """Filter on crypt card types"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self):
        self._aIds = [ICardType(x).id for x in CRYPT_TYPES]
        self._oMapTable = make_table_alias('abs_type_map')
        self._oIdField = self._oMapTable.q.card_type_id


class SectFilter(SingleFilter):
    """Filter on Sect"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sSect):
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
        self._aIds = [ISect(x).id for x in aSects]
        self._oMapTable = make_table_alias('abs_sect_map')
        self._oIdField = self._oMapTable.q.sect_id

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return [x.name for x in Sect.select().orderBy('name')]


class TitleFilter(SingleFilter):
    """Filter on Title"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sTitle):
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
        self._aIds = [ITitle(x).id for x in aTitles]
        self._oMapTable = make_table_alias('abs_title_map')
        self._oIdField = self._oMapTable.q.title_id

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return [x.name for x in Title.select().orderBy('name')]


class CreedFilter(SingleFilter):
    """Filter on Creed"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sCreed):
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
        self._aIds = [ICreed(x).id for x in aCreeds]
        self._oMapTable = make_table_alias('abs_creed_map')
        self._oIdField = self._oMapTable.q.creed_id

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return [x.name for x in Creed.select().orderBy('name')]


class VirtueFilter(SingleFilter):
    """Filter on Virtue"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sVirtue):
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
        self._aIds = [IVirtue(x).id for x in aVirtues]
        self._oMapTable = make_table_alias('abs_virtue_map')
        self._oIdField = self._oMapTable.q.virtue_id

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return [x.fullname for x in Virtue.select().orderBy('name')]


class GroupFilter(SutekhCardFilter):
    """Filter on Group"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, iGroup):
        super().__init__()
        self.__iGroup = iGroup

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_expression(self):
        return self._oMapTable.q.grp == self.__iGroup


class MultiGroupFilter(SutekhCardFilter):
    """Filter on multiple Groups"""
    keyword = "Group"
    description = "Group"
    helptext = "a list of groups.\nReturns all cards belonging to the " \
            "listed group."
    islistfilter = True
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, aGroups):
        super().__init__()
        self.__aGroups = [int(sV) for sV in aGroups if sV != 'Any']
        if 'Any' in aGroups:
            self.__aGroups.append(-1)

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        # pylint: disable=no-member
        # avoid SQLObject method not detected problems
        iMax = SutekhAbstractCard.select().max(SutekhAbstractCard.q.group)
        return [str(x) for x in range(1, iMax + 1)] + ['Any']

    def _get_expression(self):
        return IN(self._oMapTable.q.grp, self.__aGroups)


class CapacityFilter(SutekhCardFilter):
    """Filter on Capacity"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, iCap):
        super().__init__()
        self.__iCap = iCap

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_expression(self):
        return self._oMapTable.q.capacity == self.__iCap


class MultiCapacityFilter(SutekhCardFilter):
    """Filter on a list of Capacities"""
    keyword = "Capacity"
    description = "Capacity"
    helptext = "a list of capacities.\nReturns all cards of the selected" \
            " capacities"
    islistfilter = True
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, aCaps):
        super().__init__()
        self.__aCaps = [int(sV) for sV in aCaps]

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        # pylint: disable=no-member
        # avoid SQLObject method not detected problems
        iMax = SutekhAbstractCard.select().max(SutekhAbstractCard.q.capacity)
        return [str(x) for x in range(1, iMax + 1)]

    def _get_expression(self):
        return IN(self._oMapTable.q.capacity, self.__aCaps)


class CostFilter(SutekhCardFilter):
    """Filter on Cost"""
    types = ('AbstractCard', 'PhysicalCard')

    # Should this exclude Vamps & Imbued, if we search for
    # cards without cost?
    def __init__(self, iCost):
        super().__init__()
        self.__iCost = iCost
        # Handle 0 correctly
        if not iCost:
            self.__iCost = None

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_expression(self):
        return self._oMapTable.q.cost == self.__iCost


class MultiCostFilter(SutekhCardFilter):
    """Filter on a list of Costs"""
    keyword = "Cost"
    description = "Cost"
    helptext = "a list of costs.\nReturns all cards with the given costs."
    islistfilter = True
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, aCost):
        super().__init__()
        self.__aCost = [int(sV) for sV in aCost if sV != 'X']
        self.__bZeroCost = False
        if 'X' in aCost:
            self.__aCost.append(-1)
        if 0 in self.__aCost:
            self.__bZeroCost = True
            self.__aCost.remove(0)

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        # pylint: disable=no-member
        # avoid SQLObject method not detected problems
        iMax = SutekhAbstractCard.select().max(SutekhAbstractCard.q.cost)
        return [str(x) for x in range(0, iMax + 1)] + ['X']

    def _get_expression(self):
        # pylint: disable=singleton-comparison
        # == None syntax needed by SQLObject
        if self.__bZeroCost:
            if self.__aCost:
                return OR(IN(self._oMapTable.q.cost, self.__aCost),
                          self._oMapTable.q.cost == None)
            return self._oMapTable.q.cost == None
        return IN(self._oMapTable.q.cost, self.__aCost)


class CostTypeFilter(SutekhCardFilter):
    """Filter on cost type"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, sCostType):
        super().__init__()
        self.__sCostType = sCostType.lower()
        assert self.__sCostType in ("blood", "pool", "conviction", None)

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_expression(self):
        return self._oMapTable.q.costtype == self.__sCostType.lower()


class MultiCostTypeFilter(SutekhCardFilter):
    """Filter on a list of cost types"""
    keyword = "CostType"
    islistfilter = True
    description = "Cost Type"
    helptext = "a list of cost types.\nReturns cards requiring the selected" \
            " cost types."
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, aCostTypes):
        super().__init__()
        self.__aCostTypes = [x.lower() for x in aCostTypes if x is not None]
        for sCostType in self.__aCostTypes:
            assert sCostType in ("blood", "pool", "conviction")
        if None in aCostTypes:
            self.__aCostTypes.append(None)

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        return ["blood", "pool", "conviction"]

    def _get_expression(self):
        return IN(self._oMapTable.q.costtype, self.__aCostTypes)


class LifeFilter(SutekhCardFilter):
    """Filter on life"""
    types = ('AbstractCard', 'PhysicalCard')

    def __init__(self, iLife):
        super().__init__()
        self.__iLife = iLife

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_expression(self):
        return self._oMapTable.q.life == self.__iLife


class MultiLifeFilter(SutekhCardFilter):
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
        super().__init__()
        self.__aLife = [int(sV) for sV in aLife]

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        # pylint: disable=no-member
        # avoid SQLObject method not detected problems
        iMax = SutekhAbstractCard.select().max(SutekhAbstractCard.q.life)
        return [str(x) for x in range(1, iMax + 1)]

    def _get_expression(self):
        return IN(self._oMapTable.q.life, self.__aLife)


class CardTextFilter(BaseCardTextFilter):
    """Filter on Card Text"""

    def __init__(self, sPattern):
        super().__init__(sPattern)
        self._bBraces = '{' in self._sPattern or '}' in self._sPattern
        self._oMapTable = make_table_alias('sutekh_abstract_card')

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    def _get_joins(self):
        # pylint: disable=no-member
        # SQLObject methods not detected by pylint
        return [LEFTJOINOn(None, self._oMapTable,
                           AbstractCard.q.id == self._oMapTable.q.id)]

    @classmethod
    def get_values(cls):
        return ''

    def _get_expression(self):
        # pylint: disable=no-member
        # SQLObject methods not detected by pylint
        if self._bBraces:
            return super()._get_expression()
        return LIKE(func.LOWER(self._oMapTable.q.search_text),
                    '%' + self._sPattern + '%')


class CardFunctionFilter(DirectFilter):
    """Filter for various interesting card properties - unlock,
       stealth, etc."""
    keyword = "CardFunction"
    description = "Card Function"
    helptext = "the chosen function from the list of supported types.\n" \
            "Functions include roles such as unlock or bleed modifier.\n" \
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
    __sUnlock = 'Unlock reactions (Wake)'
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
        if self.__sUnlock in aTypes:
            aFilters.append(FilterAndBox(
                [CardTypeFilter('Reaction'),
                 FilterOrBox([CardTextFilter('this vampire untaps'),
                              CardTextFilter('this reacting vampire untaps'),
                              CardTextFilter('untap this vampire'),
                              CardTextFilter('untap this reacting vampire'),
                              CardTextFilter('as though untapped'),
                              CardTextFilter('this vampire unlocks'),
                              CardTextFilter('this reacting vampire unlocks'),
                              CardTextFilter('unlock this vampire'),
                              CardTextFilter('unlock this reacting vampire'),
                              CardTextFilter('as though unlocked'),
                              CardTextFilter('vampire wakes'),
                              CardTextFilter('minion wakes'),
                             ])
                ]))
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
            aFilters.append(FilterAndBox(
                [CardTypeFilter('Action'),
                 FilterOrBox([CardTextFilter('(D) bleed%at +_ bleed'),
                              CardTextFilter('(D) bleed%with +_ bleed')])
                ]))
        if self.__sBleedReduction in aTypes:
            # Ordering of bleed and reduce not consistent, so we
            # use an AND filter, rather than 'reduce%bleed'
            aFilters.append(FilterAndBox([CardTypeFilter('Reaction'),
                                          CardTextFilter('bleed'),
                                          CardTextFilter('reduce')]))
        self._oFilter = FilterOrBox(aFilters)

    # pylint: disable=missing-docstring
    # don't need docstrings for _get_expression, get_values & _get_joins
    @classmethod
    def get_values(cls):
        """Values supported by this filter"""
        aVals = sorted([cls.__sStealth, cls.__sIntercept, cls.__sUnlock,
                        cls.__sBounce, cls.__sEnterCombat,
                        cls.__sBleedModifier, cls.__sBleedAction,
                        cls.__sBleedReduction,
                       ])
        return aVals

    # pylint: disable=protected-access
    # we access protexted members intentionally
    def _get_joins(self):
        """Joins for the constructed filter"""
        return self._oFilter._get_joins()

    def _get_expression(self):
        """Expression for the constructed filter"""
        return self._oFilter._get_expression()
