# CardSetUtilities.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Utilitity functions for dealing with managing the CardSet Objects"""

from sqlobject import SQLObjectNotFound
from sutekh.core.SutekhObjects import PhysicalCardSet

def get_loop_names(oCardSet):
    """Return a list names of the card sets in the loop."""
    aLoop = [oCardSet.name]
    oParent = oCardSet.parent
    while oParent != oCardSet and oParent:
        aLoop.append(oParent.name)
        oParent = oParent.parent
    if not oParent:
        # Safet check case
        return []
    aLoop.reverse()
    return aLoop

def delete_physical_card_set(sSetName):
    """Unconditionally delete a PCS and its contents"""
    # pylint: disable-msg=E1101
    # SQLObject confuse pylint
    try:
        oCS = PhysicalCardSet.byName(sSetName)
        aChildren = find_children(oCS)
        for oChildCS in aChildren:
            oChildCS.parent = oCS.parent
            oChildCS.syncUpdate()
        for oCard in oCS.cards:
            oCS.removePhysicalCard(oCard)
        PhysicalCardSet.delete(oCS.id)
        return True
    except SQLObjectNotFound:
        return False

def detect_loop(oCardSet):
    """Checks whether the given card set is part of a loop"""
    oParent = oCardSet.parent
    while oParent:
        if oParent == oCardSet:
            return True # we have a loop
        oParent = oParent.parent
    return False # we've hit none, so no loop

def find_children(oCardSet):
    """Find all the children of the given card set"""
    # pylint: disable-msg=E1101
    # SQLObject confuses pylint
    return list(PhysicalCardSet.selectBy(parentID=oCardSet.id))
