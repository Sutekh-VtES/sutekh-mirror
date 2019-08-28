# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2014 Neil Muller <drnlmuller+sutekh@gmail.com>
# Factored out from DatabaseUpgrade
# GPL - see COPYING for details

"""Various generic things for handling complex database operations.

   These are used when upgrading the database or reloading the underlying
   abstract card set."""


from logging import Logger

from sqlobject import sqlhub

from .CardSetHolder import make_card_set_holder
from .BaseTables import PhysicalCardSet


# Utility Exception
class UnknownVersion(Exception):
    """Exception for versions we cannot handle"""
    def __init__(self, sTableName):
        Exception.__init__(self)
        self.sTableName = sTableName

    def __str__(self):
        return "Unrecognised version for %s" % self.sTableName


def copy_to_new_abstract_card_db(oOrigConn, oNewConn, oCardLookup,
                                 oLogHandler=None):
    """Copy the card sets to a new Physical Card and Abstract Card List.

      Given an existing database, and a new database created from
      a new cardlist, copy the CardSets, going via CardSetHolders, so we
      can adapt to changed names, etc.
      """
    # pylint: disable=too-many-locals
    # we need a lot of variables here
    aPhysCardSets = []
    oOldConn = sqlhub.processConnection
    sqlhub.processConnection = oOrigConn
    # Copy Physical card sets
    oLogger = Logger('copy to new abstract card DB')
    if oLogHandler:
        oLogger.addHandler(oLogHandler)
        if hasattr(oLogHandler, 'set_total'):
            iTotal = 1 + PhysicalCardSet.select(connection=oOrigConn).count()
            oLogHandler.set_total(iTotal)
    aSets = list(PhysicalCardSet.select(connection=oOrigConn))
    bDone = False
    aDone = []
    # Ensure we only process a set after it's parent
    while not bDone:
        aToDo = []
        for oSet in aSets:
            if oSet.parent is None or oSet.parent in aDone:
                oCS = make_card_set_holder(oSet)
                aPhysCardSets.append(oCS)
                aDone.append(oSet)
            else:
                aToDo.append(oSet)
        if not aToDo:
            bDone = True
        else:
            aSets = aToDo
    oLogger.info('Memory copies made')
    # Create the cardsets from the holders
    dLookupCache = {}
    sqlhub.processConnection = oNewConn
    for oSet in aPhysCardSets:
        # create_pcs will manage transactions for us
        oSet.create_pcs(oCardLookup, dLookupCache)
        oLogger.info('Physical Card Set: %s', oSet.name)
        sqlhub.processConnection.cache.clear()
    sqlhub.processConnection = oOldConn
    return (True, [])
