# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Utility functions for dealing with managing the CardSet Objects"""

from sqlobject import SQLObjectNotFound, sqlhub
from .BaseObjects import PhysicalCardSet


def check_cs_exists(sName):
    """Return True if a card set with the given name exists in the
       database."""
    return PhysicalCardSet.selectBy(name=sName).count() != 0


def get_loop(oCardSet):
    """Return a list names of the card sets in the loop."""
    aLoop = [oCardSet]
    oParent = oCardSet.parent
    while oParent not in aLoop and oParent:
        aLoop.append(oParent)
        oParent = oParent.parent
    if not oParent:
        # No parent case
        return []
    if oParent != oCardSet:
        # oCardSet is not actually part of the loop
        return get_loop(oParent)
    return aLoop


def get_loop_names(oCardSet):
    """Return a list names of the card sets in the loop."""
    aLoopNames = []
    aLoop = get_loop(oCardSet)
    if aLoop:
        aLoopNames = [x.name for x in aLoop]
        aLoopNames.reverse()
    return aLoopNames


def detect_loop(oCardSet):
    """Checks whether the given card set lead to a loop"""
    aSeen = [oCardSet]
    oParent = oCardSet.parent
    while oParent:
        if oParent in aSeen:
            return True  # we have a loop
        aSeen.append(oParent)
        oParent = oParent.parent
    return False  # we've hit none, so no loop


def break_loop(oCardSet):
    """Break the loop that oCardSet leads into"""
    sName = None
    aLoop = get_loop(oCardSet)
    if aLoop:
        # Break the first entry in the loop, as being a good a choice as
        # any
        oCS = aLoop[0]
        oCS.parent = None
        oCS.syncUpdate()
        sName = oCS.name
    return sName


def delete_physical_card_set(sSetName):
    """Unconditionally delete a PCS and its contents"""
    # pylint: disable=E1101
    # SQLObject confuse pylint
    def _delete_cards(oCS):
        """Remove cards from the card set.

           Intended to be wrapped in a transaction for speed."""
        for oCard in oCS.cards:
            oCS.removePhysicalCard(oCard)
    try:
        oCS = PhysicalCardSet.byName(sSetName)
        aChildren = find_children(oCS)
        for oChildCS in aChildren:
            oChildCS.parent = oCS.parent
            oChildCS.syncUpdate()
        if hasattr(sqlhub.processConnection, 'commit'):
            # We're already in a transaction, so just delete
            _delete_cards(oCS)
        else:
            # wrap this in a transaction for speed
            sqlhub.doInTransaction(_delete_cards, oCS)
        PhysicalCardSet.delete(oCS.id)
        return True
    except SQLObjectNotFound:
        return False


def find_children(oCardSet):
    """Find all the children of the given card set"""
    # pylint: disable=E1101
    # SQLObject confuses pylint
    if oCardSet:
        return list(PhysicalCardSet.selectBy(parentID=oCardSet.id))
    return list(PhysicalCardSet.selectBy(parentID=None))


def has_children(oCardSet):
    """Return true if the card set has children"""
    if oCardSet:
        return PhysicalCardSet.selectBy(parentID=oCardSet.id).count() > 0
    return False


def format_cs_list(oParent=None, sIndent=' '):
    """Create a formatted string of all the card sets in the database that
       are children of oParent"""
    aResult = []
    for oCS in sorted(find_children(oParent), key=lambda x: x.name):
        aResult.append(sIndent + oCS.name)
        if has_children(oCS):
            aResult.append(format_cs_list(oCS, sIndent + '   '))
    return '\n'.join(aResult)
