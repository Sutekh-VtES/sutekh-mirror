# CardLookup.py
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Lookup AbstractCards for a list of card names.
   """

from sqlobject import SQLObjectNotFound
from sutekh.core.SutekhObjects import AbstractCard, PhysicalCard

class LookupFailed(Exception):
    """Raised when an AbstractCard lookup fails completed.
       """
    pass

class AbstractCardLookup(object):
    """Base class for objects which translate card names into abstract card objects.
       """

    def lookup(self, aNames, sInfo):
        """Return a list of AbstractCards, one for each item in aNames.
        
           Names for which AbstractCards could not be found will be marked with
           a None in the returned list. The method may raise LookupFailed if the
           entire list should be considered invalid (e.g. if the names are
           presented to a user who then cancels the operation).
           """
        raise NotImplementedError

class PhysicalCardLookup(object):
    """Base class for objects which translate card names and expansions 
       into physical card objects
       """

    def physical_lookup(self, dCardExpansions, dNameCards, sInfo):
        """Returns a list of physical cards. Since physical cards can't
           be repeated, this is a list of statisfable requests. 

           dCardExpansions[Name][Expansion] is the number of cards requested,
           and dNameCards is a list of card name to abstract card mappings

           Note that len(list returned) =< sum(all requests in dCardExpansions)

           The physical card list will be smaller if no matching card can be
           found in the physical card list or if dAbstactCards has elements
           that have been excluded.

           LookupFailed will be raised if the entire list should be considered
           invalid, as for AbstractCardLookup
           """
        raise NotImplementedError

class SimpleLookup(AbstractCardLookup, PhysicalCardLookup):
    """A really straightforward lookup of AbstractCards and PhysicalCards.
    
       The default when we don't have a more cunning plan.
       """

    def lookup(self, aNames, sInfo):
        aCards = []
        for sName in aNames:
            try:
                oAbs = AbstractCard.byCanonicalName(sName.encode('utf8').lower())
                aCards.append(oAbs)
            except SQLObjectNotFound:
                aCards.append(None)
        return aCards

    def physical_lookup(self, dCardExpansions, dNameCards, sInfo):
        aCards = []
        for sName in dCardExpansions:
            oAbs = dNameCards[sName]
            if oAbs is not None:
                try:
                    aPhysCards = PhysicalCard.selectBy(abstractCardID=oAbs.id)
                    for oExpansion in dCardExpansions[sName]:
                        iCnt = dCardExpansions[sName][oExpansion]
                        # We treat None as specifying the same as specifying
                        # an expansion - the card (A, None) doesn't match a
                        # card in the physical card list (A, '3rd Ed')
                        # This works under the assumption that we're 
                        # importing card sets back into the same physical
                        # card list. There are numerous ways this can break,
                        # but I claim this approach best matches principles
                        # of least surprise. The gui lookup can do fancier
                        # resolutions, and that's what the user should see
                        # most often
                        for oPhys in aPhysCards:
                            if oPhys not in aCards \
                                    and oPhys.expansion == oExpansion:
                                aCards.append(oPhys)
                                iCnt -= 1
                                if iCnt == 0:
                                    break # We done with this expansion
                except SQLObjectNotFound:
                    # This card is missing from the PhysicalCard list, so skipped 
                    pass 
        return aCards

DEFAULT_LOOKUP = SimpleLookup()
