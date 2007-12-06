# CardSetHolder.py
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Holder for card set (Abstract or Physical) data before it is committed to a database.
   """

from sutekh.core.CardLookup import DEFAULT_LOOKUP
from sutekh.core.SutekhObjects import AbstractCardSet, PhysicalCardSet, PhysicalCard

class CardSetHolder(object):
    def __init__(self):
        self._sName, self._sAuthor, self._sComment, self._sAnnotations = None, None, None, None
        self._bInUse = False
        self._dCards = {} # card name -> count
        # (card name, expansion) -> count, used  for physical card sets 
        # and the physical card list
        self._dCardExpansions = {} 

    # Manipulate Virtual Card Set

    def add(self, iCnt, sName, oExpansion=None):
        """Append cards to the virtual set.
           """
        self._dCards.setdefault(sName, 0)
        self._dCards[sName] += iCnt
        self._dCardExpansions.setdefault(sName,{})
        self._dCardExpansions[sName].setdefault(oExpansion, 0)
        self._dCardExpansions[sName][oExpansion] += iCnt

    def remove(self, iCnt, sName, oExpansion=None):
        """Remove cards from the virtual set.
           """
        if oExpansion is None:
            sExpName = 'No Expansion'
        else:
            sExpName = oExpansion.name
        if not sName in self._dCards or self._dCards[sName] < iCnt:
            raise RuntimeError("Not enough of card '%s' to remove '%d'." % (sName,iCnt))
        elif not sName in self._dCardExpansions \
                or oExpansion not in self._dCardExpansions[sName] \
                or self._dCardExpansions[sName][oExpansion] < iCnt:
            raise RuntimeError("Not enough of card '%s' from expansion '%s' to remove '%d'." % (sName, sExpName, iCnt))
        self._dCardExpansions[sName][oExpansion] -= iCnt
        self._dCards[sName] -= iCnt

    name = property(fget = lambda self: self._sName, fset = lambda self, x: setattr(self,'_sName',x))
    author = property(fget = lambda self: self._sAuthor, fset = lambda self, x: setattr(self,'_sAuthor',x))
    comment = property(fget = lambda self: self._sComment, fset = lambda self, x: setattr(self,'_sComment',x))
    annotations = property(fget = lambda self: self._sAnnotations, fset = lambda self, x: setattr(self,'_sAnnotations',x))
    inuse = property(fget = lambda self: self._bInUse, fset = lambda self, x: setattr(self,'_bInUse',x))

    # Save Virtual Card Set to Database in Various Ways

    def createACS(self, oCardLookup=DEFAULT_LOOKUP):
        """Create an Abstract Card Set.
           """
        if self.name is None:
            raise RuntimeError("No name for the card set")

        aCardCnts = self._dCards.items()
        aAbsCards = oCardLookup.lookup([tCardCnt[0] for tCardCnt in aCardCnts], "Abstract Card Set " + self.name)

        oACS = AbstractCardSet(name=self.name.encode('utf8'),
                               author=self.author, comment=self.comment,
                               annotations=self.annotations)
        oACS.syncUpdate()

        for oAbs, (sName, iCnt) in zip(aAbsCards,aCardCnts):
            if not oAbs:
                continue
            for i in range(iCnt):
                oACS.addAbstractCard(oAbs)
        oACS.syncUpdate()

    def createPhysicalCardList(self, oCardLookup=DEFAULT_LOOKUP):
        """Create the Physical Card List from this Card Set.
           Intended for updating WW card lists when WW rename cards, etc.
        """

        aCardCnts = self._dCards.items()
        aAbsCards = oCardLookup.lookup([tCardCnt[0] for tCardCnt in aCardCnts], "Physical Card List")

        for oAbs, (sName, iCnt) in zip(aAbsCards,aCardCnts):
            if not oAbs:
                continue
            for oExpansion, iExtCnt in self._dCardExpansions[sName].iteritems():
                for i in range(iExtCnt):
                    PhysicalCard(abstractCard=oAbs, expansion=oExpansion)

    def createPCS(self, oCardLookup=DEFAULT_LOOKUP):
        """Create a Physical Card Set.
           """
        if self.name is None:
            raise RuntimeError("No name for the card set")

        aCardCnts = self._dCards.items()
        aAbsCards = oCardLookup.lookup([tCardCnt[0] for tCardCnt in aCardCnts], "Physical Card Set " +  self.name)
        dNameCards = dict(zip(self._dCards.keys(), aAbsCards))
        aPhysCards = oCardLookup.physical_lookup(self._dCardExpansions,
                dNameCards, "Physical Card Set " + self.name)

        oPCS = PhysicalCardSet(name=self.name.encode('utf8'),
                               author=self.author, comment=self.comment,
                               annotations=self.annotations,
                               inuse=self.inuse)
        oPCS.syncUpdate()

        for oPhysCard in aPhysCards:
            if not oPhysCard:
                continue
            oPCS.addPhysicalCard(oPhysCard.id)
        oPCS.syncUpdate()

class CachedCardSetHolder(CardSetHolder):
    """
    CardSetHolder class which supports creating and using a cached
    dctionary of Lookup results.
    """

    def createACS(self, oCardLookup=DEFAULT_LOOKUP, dLookupCache={}):
        """Create an Abstract Card Set.
           """
        if self.name is None:
            raise RuntimeError("No name for the card set")

        aCardCnts = self._dCards.items()
        aAbsCards = oCardLookup.lookup([dLookupCache.get(tCardCnt[0], tCardCnt[0]) for tCardCnt in aCardCnts], "Abstract Card Set " + self.name)

        oACS = AbstractCardSet(name=self.name.encode('utf8'),
                               author=self.author, comment=self.comment,
                               annotations=self.annotations)
        oACS.syncUpdate()

        for oAbs, (sName, iCnt) in zip(aAbsCards,aCardCnts):
            if not oAbs:
                dLookupCache[sName] = None
                continue
            if oAbs.canonicalName != sName and sName not in dLookupCache.keys():
                # Update the cache
                # Should we cache None responses, so to avoid prompting on those
                # again?
                dLookupCache[sName] = oAbs.canonicalName
            for i in range(iCnt):
                oACS.addAbstractCard(oAbs)
        oACS.syncUpdate()
        return dLookupCache

    def createPhysicalCardList(self, oCardLookup=DEFAULT_LOOKUP, dLookupCache={}):
        """Create the Physical Card List from this Card Set.
           Intended for updating WW card lists when WW rename cards, etc.
        """

        aCardCnts = self._dCards.items()
        aAbsCards = oCardLookup.lookup([dLookupCache.get(tCardCnt[0], tCardCnt[0]) for tCardCnt in aCardCnts], "Physical Card List")

        for oAbs, (sName, iCnt) in zip(aAbsCards,aCardCnts):
            if not oAbs:
                dLookupCache[sName] = None
                continue
            if oAbs.canonicalName != sName and sName not in dLookupCache.keys():
                dLookupCache[sName] = oAbs.canonicalName
                # Update the cache
            for oExpansion, iExtCnt in self._dCardExpansions[sName].iteritems():
                for i in range(iExtCnt):
                    PhysicalCard(abstractCard=oAbs, expansion=oExpansion)
        return dLookupCache

    def createPCS(self, oCardLookup=DEFAULT_LOOKUP, dLookupCache={}):
        """Create a Physical Card Set.
           """
        if self.name is None:
            raise RuntimeError("No name for the card set")

        aCardCnts = self._dCards.items()
        aAbsCards = oCardLookup.lookup([dLookupCache.get(tCardCnt[0], tCardCnt[0]) for tCardCnt in aCardCnts], "Physical Card Set " + self.name)
        dNameCards = dict(zip(self._dCards.keys(), aAbsCards))
        aPhysCards = oCardLookup.physical_lookup(self._dCardExpansions,
                dNameCards, "Physical Card Set " + self.name)

        # Since we are dealing with the PhysicalCardSets, we assume that
        # dLookupCache has any answers required from the PhysicalCardList,
        # so there's now point in updating the cache here.

        oPCS = PhysicalCardSet(name=self.name.encode('utf8'),
                               author=self.author, comment=self.comment,
                               annotations=self.annotations)
        oPCS.syncUpdate()

        for oPhysCard in aPhysCards:
            if not oPhysCard:
                continue
            oPCS.addPhysicalCard(oPhysCard.id)
        oPCS.syncUpdate()
