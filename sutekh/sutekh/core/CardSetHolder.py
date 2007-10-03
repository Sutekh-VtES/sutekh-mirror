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
        self._dCards = {} # card name -> count
        # (card name, expansion) -> count, used  for physical card sets 
        # and the physical card list
        self._dCardExpansions = {} 

    # Manipulate Virtual Card Set

    def add(self, iCnt, sName, sExpansion=None):
        """Append cards to the virtual set.
           """
        self._dCards.setdefault(sName, 0)
        self._dCards[sName] += iCnt
        self._dCardExpansions.setdefault(sName,{})
        self._dCardExpansions[sName].setdefault(sExpansion, 0)
        self._dCardExpansions[sName][sExpansion] += iCnt

    def remove(self, iCnt, sName, sExpansion=None):
        """Remove cards from the virtual set.
           """
        if not sName in self._dCards or self._dCards[sName] < iCnt:
            raise RuntimeError("Not enough of card '%s' to remove '%d'." % (sName,iCnt))
        elif not sName in self._dCardExpansions \
                or sExpansion not in self._dCardExpansions[sName] \
                or self._dCardExpansions[sName][sExpansion] < iCnt:
            raise RuntimeError("Not enough of card '%s' from expansion '%s' to remove '%d'." % (sName,sExpansion,iCnt))
        self._dCardExpansions[sName][sExpansion] -= iCnt
        self._dCards[sName] -= iCnt

    name = property(fget = lambda self: self._sName, fset = lambda self, x: setattr(self,'_sName',x))
    author = property(fget = lambda self: self._sAuthor, fset = lambda self, x: setattr(self,'_sAuthor',x))
    comment = property(fget = lambda self: self._sComment, fset = lambda self, x: setattr(self,'_sComment',x))
    annotations = property(fget = lambda self: self._sAnnotations, fset = lambda self, x: setattr(self,'_sAnnotations',x))

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

    def createPhysicalCardList(self, oCardLookup=DEFAULT_LOOKUP):
        """Create the Physical Card List from this Card Set.
           Intended for updating WW card lists when WW rename cards, etc.
        """

        aCardCnts = self._dCards.items()
        aAbsCards = oCardLookup.lookup([tCardCnt[0] for tCardCnt in aCardCnts], "Physical Card List")

        for oAbs, (sName, iCnt) in zip(aAbsCards,aCardCnts):
            if not oAbs:
                continue
            for sExpansion, iExtCnt in self._dCardExpansions[sName].iteritems():
                for i in range(iExtCnt):
                    PhysicalCard(abstractCard=oAbs,expansion=sExpansion)

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
                               annotations=self.annotations)
        oPCS.syncUpdate()

        for oPhysCard in aPhysCards:
            if not oPhysCard:
                continue
            oPCS.addPhysicalCard(oPhysCard.id)
