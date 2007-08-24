# CardLookup.py
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Lookup AbstractCards for a list of card names.
   """

from sqlobject import SQLObjectNotFound
from sutekh.core.SutekhObjects import AbstractCard

class LookupFailed(Exception):
    """Raised when an AbstractCard lookup fails completed.
       """
    pass

class AbstractCardLookup(object):
    """Base class for objects which translate card names into abstract card objects.
       """

    def lookup(self,aNames):
        """Return a list of AbstractCards, one for each item in aNames.
        
           Names for which AbstractCards could not be found will be marked with
           a None in the returned list. The method may raise LookupFailed if the
           entire list should be considered invalid (e.g. if the names are
           presented to a user who then cancels the operation).
           """
        raise NotImplementedError

class SimpleLookup(AbstractCardLookup):
    """A really straightforward lookup of AbstractCards.
    
       The default when we don't have a more cunning plan.
       """

    def lookup(self,aNames):
        aCards = []
        for sName in aNames:
            try:
                oAbs = AbstractCard.byCanonicalName(sName.encode('utf8').lower())
                aCards.append(oAbs)
            except SQLObjectNotFound:
                aCards.append(None)
        return aCards

DEFAULT_LOOKUP = SimpleLookup()
