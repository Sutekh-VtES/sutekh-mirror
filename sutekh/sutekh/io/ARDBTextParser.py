# ARDBTextParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# ARDB Text File Deck Parser
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Parser for ARDB text deck format.

   Example deck:

   Deck Name : Followers of Set Preconstructed Deck
   Author : L. Scott Johnson
   Description :
   Followers of Set Preconstructed Starter from Lords of the Night.

   http://www.white-wolf.com/vtes/index.php?line=Checklist_LordsOfTheNight

   Crypt [12 vampires] Capacity min: 2 max: 10 average: 5.84
   ------------------------------------------------------------
   2x Nakhthorheb			  10 OBF PRE SER           Follower :4
   ...

   Library [77 cards]
   ------------------------------------------------------------
   Action [20]
     2x Blithe Acceptance
     4x Dream World
   ...
   """

import re

# State Base Classes

class StateError(Exception):
    pass

class State(object):
    def __init__(self,oHolder):
        self._sData = ""
        self._oHolder = oHolder

    def transition(self,sLine):
        raise NotImplementedError

    def data(self,sData):
        self._sData += sData

# State Classes

class NameAndAuthor(State):
    def transition(self,sLine):
        aParts = sLine.split(':')
        if len(aParts) != 2:
            return self

        sKey, sValue = aParts[0].strip(), aParts[1].strip()

        if sKey == "Deck Name":
            self._oHolder.name = sValue
        elif sKey == "Author":
            self._oHolder.author = sValue
        elif sKey == "Description":
            return Description(self._oHolder)

        return self

class Description(State):
    def transition(self,sLine):
        if sLine.strip().startswith('Crypt ['):
            self._oHolder.comment = self._sData
            return Cards(self._oHolder)
        else:
            self.data(sLine)
            return self

class Cards(State):
    _oCardRe = re.compile(r'\s*(?P<cnt>[0-9]+)x\s+(?P<name>[^\t\r\n]+)')

    def transition(self,sLine):
        oM = self._oCardRe.match(sLine)
        if oM:
            iCnt = int(oM.group('cnt'))
            self._oHolder.add(iCnt,oM.group('name'))
        return self

# Parser

class ARDBTextParser(object):
    def __init__(self,oHolder):
        """Create an ARDBTextParser.
        
           oHolder is a sutekh.core.CardSetHolder.CardSetHolder object (or similar).
           """
        self._oHolder = oHolder
        self.reset()

    def reset(self):
        self._state = NameAndAuthor(self._oHolder)

    def feed(self,sLine):
        self._state = self._state.transition(sLine)
