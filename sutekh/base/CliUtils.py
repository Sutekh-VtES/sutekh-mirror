# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2014 Neil Muller <drnlmuller+sutekh@gmail.com>
#     (split off from SutekhCli to be more reusable)
# GPL - see COPYING for details
"""
functions to help the CLI programs
"""

from sqlobject import SQLObjectNotFound
from .core.BaseObjects import (IPhysicalCardSet, IAbstractCard, PhysicalCard,
                               MapPhysicalCardToPhysicalCardSet)
from .core.BaseFilters import (PhysicalCardSetFilter, FilterAndBox,
                               PhysicalCardFilter)
from .core.FilterParser import FilterParser
from .core.CardSetUtilities import format_cs_list


def run_filter(sFilter, sCardSet):
    """Run the given filter, returing a dictionary of cards and counts"""
    oCardSet = None
    if sCardSet:
        oCardSet = IPhysicalCardSet(sCardSet)
    oParser = FilterParser()
    oFilter = oParser.apply(sFilter).get_filter()

    dResults = {}
    if oCardSet:
        # Filter the given card set
        # pylint: disable-msg=E1101
        # E1101: SQLObject + PyProtocols magic confuses pylint
        oBaseFilter = PhysicalCardSetFilter(oCardSet.name)
        oJointFilter = FilterAndBox([oBaseFilter, oFilter])
        aResults = oJointFilter.select(MapPhysicalCardToPhysicalCardSet)
        for oCard in aResults:
            oAbsCard = IAbstractCard(oCard)
            dResults.setdefault(oAbsCard, 0)
            dResults[oAbsCard] += 1
    else:
        # Filter cardlist
        # pylint: disable-msg=E1101
        # E1101: SQLObject + PyProtocols magic confuses pylint
        oBaseFilter = PhysicalCardFilter()
        oJointFilter = FilterAndBox([oBaseFilter, oFilter])
        aResults = oJointFilter.select(PhysicalCard)
        for oCard in aResults:
            oAbsCard = IAbstractCard(oCard)
            # flag non-cardset case for print_card_filter_list
            dResults.setdefault(oAbsCard, 0)

    return dResults


def print_card_filter_list(dResults, fPrintCard, bDetailed, sEncoding):
    """Print a dictionary of cards returned by runfilter"""

    for oCard in sorted(dResults, key=lambda x: x.name):
        iCnt = dResults[oCard]
        if iCnt:
            print '%3d x %s' % (
                iCnt, oCard.name.encode(sEncoding, 'xmlcharrefreplace'))
        else:
            print oCard.name.encode(sEncoding, 'xmlcharrefreplace')
        if bDetailed:
            fPrintCard(oCard, sEncoding)


def print_card_list(sTreeRoot, sEncoding):
    """Print a a list of card sets, handling potential encoding issues
       and a starting point for the tree."""
    if sTreeRoot is not None:
        try:
            # pylint: disable-msg=E1101
            # SQLObject confuse pylint
            oCS = IPhysicalCardSet(sTreeRoot)
            print ' %s' % oCS.name.encode(sEncoding, 'xmlcharrefreplace')
            print format_cs_list(oCS, '    ').encode(sEncoding,
                                                     'xmlcharrefreplace')
        except SQLObjectNotFound:
            print 'Unable to load card set', sTreeRoot
            return False
    else:
        print format_cs_list().encode(sEncoding, 'xmlcharrefreplace')
    return True


def do_print_card(sCardName, fPrintCard, sEncoding):
    """Print a card, handling possible encoding issues."""
    try:
        # pylint: disable-msg=E1103
        # E1103: PyProtocols magic confuses pylint
        try:
            oCard = IAbstractCard(sCardName)
        except UnicodeDecodeError, oErr:
            if sEncoding != 'ascii':
                # Are there better choices than --print-encoding?
                oCard = IAbstractCard(sCardName.decode(sEncoding))
            else:
                print 'Unable to interpret card name:'
                print oErr
                print 'Please specify a suitable --print-encoding'
                return False
        print oCard.name.encode(sEncoding, 'xmlcharrefreplace')
        fPrintCard(oCard, sEncoding)
    except SQLObjectNotFound:
        print 'Unable to find card %s' % sCardName
        return False
    return True
