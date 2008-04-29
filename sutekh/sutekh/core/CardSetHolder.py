# CardSetHolder.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Holder for card set (Abstract or Physical) data before it is committed
   to a database."""

from sutekh.core.CardLookup import DEFAULT_LOOKUP
from sutekh.core.SutekhObjects import PhysicalCardSet, PhysicalCard

class CardSetHolder(object):
    # pylint: disable-msg=R0902
    # Need to keep state of card set, so many attributes
    """Holder for Card Sets.

       This holds a list of cards and optionally expansions and may be used
       to create a PhysicalCardSet. We call on the provided CardLookup function
       to resolve unknown cards.
       """
    def __init__(self):
        self._sName, self._sAuthor, self._sComment, \
                self._sAnnotations = None, None, None, None
        self._bInUse = False
        self._dCards = {} # card name -> count
        self._dExpansions = {} # expansion name -> count
        # (card name, expansion name) -> count, used  for physical card sets
        # and the physical card list
        # The expansion name may be None to indicate an unspecified expansion
        self._dCardExpansions = {}

    # Manipulate Virtual Card Set

    def add(self, iCnt, sName, sExpansionName):
        """Append cards to the virtual set.
        
           sExpansionName may be None.
           """
        self._dCards.setdefault(sName, 0)
        self._dCards[sName] += iCnt
        self._dExpansions.setdefault(sExpansionName, 0)
        self._dExpansions[sExpansionName] += iCnt
        self._dCardExpansions.setdefault(sName, {})
        self._dCardExpansions[sName].setdefault(sExpansionName, 0)
        self._dCardExpansions[sName][sExpansionName] += iCnt

    def remove(self, iCnt, sName, sExpansionName):
        """Remove cards from the virtual set.
        
           sExpansionName may be None.
           """
        if not sName in self._dCards or self._dCards[sName] < iCnt:
            raise RuntimeError("Not enough of card '%s' to remove '%d'."
                    % (sName, iCnt))
        elif not sName in self._dCardExpansions \
                or sExpansionName not in self._dCardExpansions[sName] \
                or self._dCardExpansions[sName][sExpansionName] < iCnt:
            raise RuntimeError("Not enough of card '%s' from expansion"
                    " '%s' to remove '%d'." % (sName, sExpansionName, iCnt))
        self._dCardExpansions[sName][sExpansionName] -= iCnt
        # This should be covered by check on self._dCardExpansions
        self._dExpansions[sExpansionName] -= iCnt
        self._dCards[sName] -= iCnt

    # pylint: disable-msg=W0212
    # we delibrately allow access via these properties
    name = property(fget = lambda self: self._sName,
            fset = lambda self, x: setattr(self, '_sName', x))
    author = property(fget = lambda self: self._sAuthor,
            fset = lambda self, x: setattr(self, '_sAuthor', x))
    comment = property(fget = lambda self: self._sComment,
            fset = lambda self, x: setattr(self, '_sComment', x))
    annotations = property(fget = lambda self: self._sAnnotations,
            fset = lambda self, x: setattr(self, '_sAnnotations', x))
    inuse = property(fget = lambda self: self._bInUse,
            fset = lambda self, x: setattr(self, '_bInUse', x))
    # pylint: enable-msg=W0212

    # Save Virtual Card Set to Database

    def create_pcs(self, oCardLookup=DEFAULT_LOOKUP):
        """Create a Physical Card Set.
           """
        if self.name is None:
            raise RuntimeError("No name for the card set")

        aCardCnts = self._dCards.items()
        aAbsCards = oCardLookup.lookup([tCardCnt[0] for tCardCnt in aCardCnts],
                "Physical Card Set %s" % self.name)
        dNameCards = dict(zip(self._dCards.keys(), aAbsCards))

        aExpNames = self._dExpansions.keys()
        aExps = oCardLookup.expansion_lookup(aExpNames, "Physical Card List")
        dExpansionLookup = dict(zip(aExpNames, aExps))

        aPhysCards = oCardLookup.physical_lookup(self._dCardExpansions,
                dNameCards, dExpansionLookup, "Physical Card Set " + self.name)

        oPCS = PhysicalCardSet(name=self.name.encode('utf8'),
                               author=self.author, comment=self.comment,
                               annotations=self.annotations,
                               inuse=self.inuse)
        oPCS.syncUpdate()

        for oPhysCard in aPhysCards:
            # pylint: disable-msg=E1101
            # SQLObject confuses pylint
            if not oPhysCard:
                continue
            oPCS.addPhysicalCard(oPhysCard.id)
        oPCS.syncUpdate()

class CachedCardSetHolder(CardSetHolder):
    """CardSetHolder class which supports creating and using a
       cached dictionary of Lookup results.
       """

    def create_pcs(self, oCardLookup=DEFAULT_LOOKUP, dLookupCache={}):
        """Create a Physical Card Set.
           """
        if self.name is None:
            raise RuntimeError("No name for the card set")

        aCardCnts = self._dCards.items()
        aAbsCards = oCardLookup.lookup([dLookupCache.get(tCardCnt[0],
            tCardCnt[0]) for tCardCnt in aCardCnts],
            "Physical Card Set %s" % self.name)
        dNameCards = dict(zip(self._dCards.keys(), aAbsCards))

        aExpNames = self._dExpansions.keys()
        aExps = oCardLookup.expansion_lookup(aExpNames, "Physical Card List")
        dExpansionLookup = dict(zip(aExpNames, aExps))

        aPhysCards = oCardLookup.physical_lookup(self._dCardExpansions,
                dNameCards, dExpansionLookup, "Physical Card Set " + self.name)

        # Since we are dealing with the PhysicalCardSets, we assume that
        # dLookupCache has any answers required from the PhysicalCardList,
        # so there's now point in updating the cache here.

        oPCS = PhysicalCardSet(name=self.name.encode('utf8'),
                               author=self.author, comment=self.comment,
                               annotations=self.annotations,
                               inuse=self.inuse)
        oPCS.syncUpdate()

        for oPhysCard in aPhysCards:
            # pylint: disable-msg=E1101
            # SQLObject confuses pylint
            if not oPhysCard:
                continue
            oPCS.addPhysicalCard(oPhysCard.id)
        oPCS.syncUpdate()

