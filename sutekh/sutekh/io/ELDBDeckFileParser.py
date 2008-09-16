# ELDBDeckFileParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# ELDB Deck File Parser
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Parser for ELDB deck format"""

from sutekh.core.SutekhObjects import AbstractCard
from sutekh.io.WriteELDBInventory import norm_name
from sutekh.io.ARDBTextParser import StateError, State

def gen_name_lookups():
    """Create a lookup table to map ELDB names to Sutekh names -
       reduces the number of user queries"""
    dNameCache = {}
    for oCard in AbstractCard.select():
        sSutekhName = oCard.name
        sELDBName = norm_name(oCard)
        dNameCache[sELDBName] = sSutekhName
    return dNameCache

# State Classes

class Name(State):
    """State for extracting Name."""
    def transition(self, sLine, dNameCache):
        """Process the line for Name - transioning to author."""
        sValue = sLine.strip()
        if not sValue:
            return self
        sValue = sValue.strip('"')
        self._oHolder.name = sValue
        return Author(self._oHolder)

class Author(State):
    """State for extracting Author."""
    def transition(self, sLine, dNameCache):
        """Process the line for Author - transioning to description."""
        sValue = sLine.strip()
        if not sValue:
            return self
        sValue = sValue.strip('"')
        if sValue:
            # ELDB may leave this blank
            self._oHolder.author = sValue
        return Description(self._oHolder)

class Description(State):
    """State for extracting description"""
    def transition(self, sLine, dNameCache):
        """Process the lines for the description and transition to Cards
           state if needed."""
        sValue = sLine.strip()
        if sValue.endswith('"'):
            self.data(sValue.strip('"'))
            self._oHolder.comment = self._sData
            return Cards(self._oHolder)
        else:
            self.data(sValue.strip('"') + '\n')
            return self

class Cards(State):
    """State for extracting the cards"""
    def transition(self, sLine, dNameCache):
        """Extract the cards from the data.

           This is the terminating state, so we always return Cards from
           this.
           """
        sCard = sLine.strip()
        if not sCard.startswith('"'):
            # Number or blank line, which we just skip
            return self
        sCard = sCard.strip('"')
        if sCard in dNameCache:
            sName = dNameCache[sCard]
        else:
            sName = sCard
        self._oHolder.add(1, sName, None)
        return self

class ELDBDeckFileParser(object):
    """Parser for the ELDB Deck format."""

    def __init__(self, oHolder):
        self._dNameCache = gen_name_lookups()
        self._oHolder = oHolder
        self._oState = None
        self.reset()

    def reset(self):
        """Reset the parser state"""
        self._oState = Name(self._oHolder)

    def feed(self, sLine):
        """Feed the next line to the current state object, and transition if
           required."""
        self._oState = self._oState.transition(sLine, self._dNameCache)

