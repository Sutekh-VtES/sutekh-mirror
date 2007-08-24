# CardSetHolder.py
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Holder for card set (Abstract or Physical) data before it is committed to a database.
   """

from sutekh.core.CardLookup import DEFAULT_LOOKUP
from sutekh.core.SutekhObjects import AbstractCardSet

class CardSetHolder(object):
    def __init__(self):
        self._sName, self._sAuthor, self._sComment, self._sAnnotations = None, None, None, None
        self._dCards = {} # card name -> count

    # Manipulate Virtual Card Set

    def add(self,iCnt,sName):
        """Append cards to the virtual set.
           """
        self._dCards.setdefault(sName,0)
        self._dCards[sName] += iCnt

    def remove(self,iCnt,sName):
        """Remove cards from the virtual set.
           """
        if not sName in self._dCards or self._dCards[sName] < iCnt:
            raise RuntimeError("Not enough of card '%s' to remove '%d'." % (sName,iCnt))
        self._dCards[sName] -= iCnt

    name = property(fget = lambda self: self._sName, fset = lambda self, x: setattr(self,'_sName',x))
    author = property(fget = lambda self: self._sAuthor, fset = lambda self, x: setattr(self,'_sAuthor',x))
    comment = property(fget = lambda self: self._sComment, fset = lambda self, x: setattr(self,'_sComment',x))
    annotations = property(fget = lambda self: self._sAnnotations, fset = lambda self, x: setattr(self,'_sAnnotations',x))

    # Save Virtual Card Set to Database in Various Ways

    def createACS(self,oCardLookup=DEFAULT_LOOKUP):
        """Create an Abstract Card Set.
           """
        if self.name is None:
            raise RuntimeError("No name for the card set")

        aCardCnts = self._dCards.items()
        aAbsCards = oCardLookup.lookup([tCardCnt[0] for tCardCnt in aCardCnts])

        oACS = AbstractCardSet(name=self.name.encode('utf8'),
                               author=self.author, comment=self.comment,
                               annotations=self.annotations)
        oACS.syncUpdate()

        for oAbs, (sName, iCnt) in zip(aAbsCards,aCardCnts):
            if not oAbs:
                continue
            for i in range(iCnt):
                oACS.addAbstractCard(oAbs)
