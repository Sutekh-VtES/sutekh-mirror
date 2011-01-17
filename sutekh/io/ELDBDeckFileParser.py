# ELDBDeckFileParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# ELDB Deck File Parser
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Parser for ELDB deck format"""

from sutekh.core.ELDBUtilities import gen_name_lookups


# State Classes
class State(object):
    """Base class for the State Objects."""
    def __init__(self, oHolder, dNameCache):
        self._sData = ""
        self._oHolder = oHolder
        self._dNameCache = dNameCache

    def transition(self, sLine):
        """Transition to next state"""
        raise NotImplementedError

    def data(self, sData):
        """Add data to the state object."""
        self._sData += sData


class Name(State):
    """State for extracting Name."""
    def transition(self, sLine):
        """Process the line for Name - transitioning to author."""
        sValue = sLine.strip()
        if not sValue:
            return self
        sValue = sValue.strip('"')
        self._oHolder.name = sValue
        return Author(self._oHolder, self._dNameCache)


class Author(State):
    """State for extracting Author."""
    def transition(self, sLine):
        """Process the line for Author - transitioning to description."""
        sValue = sLine.strip()
        if not sValue:
            return self
        sValue = sValue.strip('"')
        if sValue:
            # ELDB may leave this blank
            self._oHolder.author = sValue
        return Description(self._oHolder, self._dNameCache)


class Description(State):
    """State for extracting description"""
    def transition(self, sLine):
        """Process the lines for the description and transition to Cards
           state if needed."""
        sValue = sLine.strip()
        if sValue.endswith('"'):
            self.data(sValue.strip('"'))
            self._oHolder.comment = self._sData
            return Cards(self._oHolder, self._dNameCache)
        else:
            self.data(sValue.strip('"') + '\n')
            return self


class Cards(State):
    """State for extracting the cards"""
    def transition(self, sLine):
        """Extract the cards from the data.

           This is the terminating state, so we always return Cards from
           this.
           """
        sCard = sLine.strip()
        if not sCard.startswith('"'):
            # Number or blank line, which we just skip
            return self
        sCard = sCard.strip('"')
        if sCard in self._dNameCache:
            sName = self._dNameCache[sCard]
        else:
            sName = sCard
        self._oHolder.add(1, sName, None)
        return self


class ELDBDeckFileParser(object):
    """Parser for the ELDB Deck format."""

    def __init__(self):
        super(ELDBDeckFileParser, self).__init__()
        self._dNameCache = gen_name_lookups()
        self._oState = None

    def _feed(self, sLine):
        """Feed the next line to the current state object, and transition if
           required."""
        self._oState = self._oState.transition(sLine)

    def parse(self, fIn, oHolder):
        """Parse the file line-by-line"""
        self._oState = Name(oHolder, self._dNameCache)
        for sLine in fIn:
            # Because of how ELDB formats comments, we don't skip blank
            # lines
            self._feed(sLine)
