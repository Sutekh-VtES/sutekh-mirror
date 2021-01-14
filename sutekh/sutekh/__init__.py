# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""This is the sutekh package.
   """

# Do importing

from sutekh.base.core.BaseTables import (AbstractCard, PhysicalCard,
                                         PhysicalCardSet, RarityPair,
                                         Expansion, Rarity, CardType,
                                         Ruling)

from sutekh.core.SutekhTables import DisciplinePair, Discipline, Clan

from sutekh.base.core.BaseFilters import (FilterAndBox, FilterOrBox,
                                          CardTypeFilter,
                                          MultiCardTypeFilter,
                                          PhysicalCardSetFilter,
                                          PhysicalCardFilter,
                                          ExpansionFilter,
                                          MultiExpansionFilter,
                                          PhysicalExpansionFilter,
                                          CardNameFilter,
                                          MultiPhysicalExpansionFilter,
                                          CardSetNameFilter,
                                          CardSetDescriptionFilter,
                                          CardSetAuthorFilter,
                                          CardSetAnnotationsFilter)
from sutekh.base.core.DBUtility import make_adapter_caches

from sutekh.core.Filters import (ClanFilter, DisciplineFilter, CardTextFilter,
                                 MultiDisciplineFilter, MultiClanFilter,
                                 GroupFilter, MultiGroupFilter)

from sutekh.base.core.BaseGroupings import (CardTypeGrouping,
                                            ExpansionGrouping,
                                            RarityGrouping)
from sutekh.core.Groupings import ClanGrouping, DisciplineGrouping

from sutekh.core.CardListTabulator import CardListTabulator

from sutekh.SutekhCli import main_with_args


# start() method for use when working in the Python interpreter
# pylint: disable=dangerous-default-value
def start(aArgs=['sutekh']):  # pragma: no cover
    """Initialise SQLObject connection and so forth, for working in the
       python interpreter"""
    main_with_args(aArgs)
    # Also initialise the caches, so adapters, etc work
    make_adapter_caches()

# What we expose to import *

ALL = [
    # Sutekh Objects
    AbstractCard, PhysicalCard, PhysicalCardSet,
    RarityPair, Expansion, Rarity, DisciplinePair, Discipline,
    Clan, CardType, Ruling,
    # Filters
    FilterAndBox, FilterOrBox, ClanFilter, DisciplineFilter,
    CardTypeFilter, CardTextFilter, MultiCardTypeFilter,
    MultiDisciplineFilter, MultiClanFilter, PhysicalCardSetFilter,
    PhysicalCardFilter, GroupFilter, MultiGroupFilter,
    ExpansionFilter, MultiExpansionFilter, CardNameFilter,
    CardSetNameFilter, CardSetAuthorFilter, CardSetDescriptionFilter,
    CardSetAnnotationsFilter, PhysicalExpansionFilter,
    MultiPhysicalExpansionFilter,
    # Groupings
    CardTypeGrouping, ClanGrouping, DisciplineGrouping,
    ExpansionGrouping, RarityGrouping,
    # Misc
    start, CardListTabulator,
]

__all__ = [x.__name__ for x in ALL]
