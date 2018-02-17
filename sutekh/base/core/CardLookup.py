# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Lookup AbstractCards for a list of card names.
   """

from sqlobject import SQLObjectNotFound
from .BaseAdapters import IPhysicalCard, IExpansion, IAbstractCard


class LookupFailed(Exception):
    """Raised when an AbstractCard lookup fails completed.
       """
    pass


class AbstractCardLookup(object):
    """Base class for objects which translate card names into abstract card
       objects.
       """

    def lookup(self, aNames, sInfo):
        """Return a list of AbstractCards, one for each item in aNames.

           Names for which AbstractCards could not be found will be marked with
           a None in the returned list. The method may raise LookupFailed
           if the entire list should be considered invalid (e.g. if the names
           are presented to a user who then cancels the operation).
           """
        raise NotImplementedError


class PhysicalCardLookup(object):
    """Base class for objects which translate card and expansion names
       into physical card objects
       """

    def physical_lookup(self, dCardExpansions, dNameCards, dNameExps, sInfo):
        """Returns a list of physical cards. Since physical cards can't
           be repeated, this is a list of statisfable requests.

           dCardExpansions[Name][Expansion] is the number of cards requested,
           dNameCards is a dictionary of card name to abstract card mappings
           and dNameExps is a dictionary of expansion name to expansion object
           mappings.

           Note that len(list returned) =< sum(all requests in dCardExpansions)

           The physical card list will be smaller if no matching card can be
           found in the physical card list or if dAbstactCards has elements
           that have been excluded.

           LookupFailed will be raised if the entire list should be considered
           invalid, as for AbstractCardLookup
           """
        raise NotImplementedError


class ExpansionLookup(object):
    """Base class for objects which translate expansion names into expansion
       objects
       """

    def expansion_lookup(self, aExpansionNames, sInfo, dCardExpansions):
        """Return a list of Expansions, one for each item in aExpansionNames.

           Names for which Expansions could not be found will be marked with
           a None in the returned list. The method may raise LookupFailed if
           the entire list should be considered invalid (e.g. if the names
           are presented to a user who then cancels the operation).
           """
        raise NotImplementedError


class SimpleLookup(AbstractCardLookup, PhysicalCardLookup, ExpansionLookup):
    """A really straightforward lookup of AbstractCards and PhysicalCards.

       The default when we don't have a more cunning plan.
       """

    def lookup(self, aNames, _sInfo):
        """A lookup method that excludes unknown cards."""
        aCards = []
        for sName in aNames:
            if sName:
                try:
                    oAbs = IAbstractCard(sName)
                    aCards.append(oAbs)
                except SQLObjectNotFound:
                    aCards.append(None)
            else:
                aCards.append(None)
        return aCards

    def physical_lookup(self, dCardExpansions, dNameCards, dNameExps, _sInfo):
        """Lookup cards in the physical card set, excluding unknown cards."""
        aCards = []
        for sName in dCardExpansions:
            oAbs = dNameCards[sName]
            if oAbs is not None:
                for sExpansionName in dCardExpansions[sName]:
                    try:
                        iCnt = dCardExpansions[sName][sExpansionName]
                        oExpansion = dNameExps[sExpansionName]
                        aCards.extend(
                            [IPhysicalCard((oAbs, oExpansion))] * iCnt)
                    except SQLObjectNotFound:
                        # This card is missing from the PhysicalCard list, so
                        # skipped
                        pass
        return aCards

    def expansion_lookup(self, aExpansionNames, _sInfo, _dCardExpansions):
        """Lookup for expansion names, excluding unknown expansions."""
        aExps = []
        for sExp in aExpansionNames:
            if sExp:
                try:
                    oExp = IExpansion(sExp)
                    aExps.append(oExp)
                except SQLObjectNotFound:
                    aExps.append(None)
            else:
                aExps.append(None)
        return aExps


DEFAULT_LOOKUP = SimpleLookup()
