# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2014 Neil Muller <drnlmuller+sutekh@gmail.com>
#     (split off from SutekhCli to be more reusable)
# GPL - see COPYING for details
"""
functions to help the CLI programs
"""

from __future__ import print_function

from sqlobject import SQLObjectNotFound
from .core.BaseTables import (PhysicalCard,
                              MapPhysicalCardToPhysicalCardSet)
from .core.BaseAdapters import IPhysicalCardSet, IAbstractCard
from .core.BaseFilters import (PhysicalCardSetFilter, FilterAndBox,
                               PhysicalCardFilter)
from .core.FilterParser import FilterParser
from .core.CardSetUtilities import format_cs_list
from .core.DBUtility import make_adapter_caches


def run_filter(sFilter, sCardSet):
    """Run the given filter, returing a dictionary of cards and counts"""
    make_adapter_caches()  # We need to have the adapters initialised
                           # for filtering to work
    oCardSet = None
    if sCardSet:
        oCardSet = IPhysicalCardSet(sCardSet)
    oParser = FilterParser()
    oFilter = oParser.apply(sFilter).get_filter()

    dResults = {}
    if oCardSet:
        # Filter the given card set
        oBaseFilter = PhysicalCardSetFilter(oCardSet.name)
        oJointFilter = FilterAndBox([oBaseFilter, oFilter])
        aResults = oJointFilter.select(MapPhysicalCardToPhysicalCardSet)
        for oCard in aResults:
            oAbsCard = IAbstractCard(oCard)
            dResults.setdefault(oAbsCard, 0)
            dResults[oAbsCard] += 1
    else:
        # Filter cardlist
        oBaseFilter = PhysicalCardFilter()
        oJointFilter = FilterAndBox([oBaseFilter, oFilter])
        aResults = oJointFilter.select(PhysicalCard)
        for oCard in aResults:
            oAbsCard = IAbstractCard(oCard)
            # flag non-cardset case for print_card_filter_list
            dResults.setdefault(oAbsCard, 0)

    return dResults


def print_card_filter_list(dResults, fPrintCard, bDetailed):
    """Print a dictionary of cards returned by runfilter"""

    for oCard in sorted(dResults, key=lambda x: x.name):
        iCnt = dResults[oCard]
        if iCnt:
            print('%3d x %s' % (iCnt, oCard.name))
        else:
            print(oCard.name)
        if bDetailed:
            fPrintCard(oCard)


def print_card_list(sTreeRoot):
    """Print a a list of card sets, handling potential encoding issues
       and a starting point for the tree."""
    if sTreeRoot is not None:
        try:
            oCS = IPhysicalCardSet(sTreeRoot)
            print(' %s' % oCS.name)
            print(format_cs_list(oCS, '    '))
        except SQLObjectNotFound:
            print('Unable to load card set', sTreeRoot)
            return False
    else:
        print(format_cs_list())
    return True


def do_print_card(sCardName, fPrintCard):
    """Print a card, handling possible encoding issues."""
    make_adapter_caches()  # Needed for lookups to work
    try:
        try:
            oCard = IAbstractCard(sCardName)
        except UnicodeDecodeError as oErr:
            print('Unable to interpret card name:')
            print(oErr)
            return False
        print(oCard.name)
        fPrintCard(oCard)
    except SQLObjectNotFound:
        print('Unable to find card %s' % sCardName)
        return False
    return True
