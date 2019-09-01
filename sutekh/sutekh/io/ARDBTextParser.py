# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
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

from sutekh.base.io.SutekhBaseHTMLParser import HolderState


# HolderState Classes
class NameAndAuthor(HolderState):
    """HolderState for extracting Name and Author."""
    # pylint: disable=arguments-differ
    # pylint doesn't like that we mark dAttr as unused here
    def transition(self, sLine, _dAttr):
        """Process the line for Name and Author - trnaisiotn to Description
           if needed."""
        # Check for crypt line, as description isn't always present
        if sLine.strip().startswith('Crypt ['):
            return Cards(self._oHolder)
        elif sLine.strip().startswith('Crypt: ('):
            return Cards(self._oHolder)
        elif sLine.strip().startswith('Crypt ('):
            return Cards(self._oHolder)

        aParts = sLine.split(':', 1)

        if len(aParts) != 2:
            return self  # Nothing of interest seen

        sKey, sValue = aParts[0].strip(), aParts[1].strip()

        if sKey == "Deck Name":
            self._oHolder.name = sValue
        elif sKey == "Author" or sKey == "Created By" or sKey == "Created by":
            self._oHolder.author = sValue
        elif sKey == "Description":
            oDesc = Description(self._oHolder)
            if sValue:
                oDesc.data(sValue)
            return oDesc

        return self


class Description(HolderState):
    """HolderState for extracting description"""
    # pylint: disable=arguments-differ
    # pylint doesn't like that we mark dAttr as unused here
    def transition(self, sLine, _dAttr):
        """Process the line for the description and transition to Cards
           state if needed."""
        if sLine.strip().startswith('Crypt ['):
            self._oHolder.comment = self._sData
            return Cards(self._oHolder)
        elif sLine.strip().startswith('Crypt: ('):
            self._oHolder.comment = self._sData
            return Cards(self._oHolder)
        elif sLine.strip().startswith('Crypt ('):
            self._oHolder.comment = self._sData
            return Cards(self._oHolder)
        self.data(sLine)
        return self


class Cards(HolderState):
    """HolderState for extracting the cards"""
    _oCardRe = re.compile(
        r'\s*(?P<cnt>[0-9]+)(\s)*(x)*\s+(?P<name>[^\t\r\n]+)')
    _oAdvRe = re.compile(r'\sAdv\s')

    # pylint: disable=arguments-differ
    # pylint doesn't like that we mark dAttr as unused here
    def transition(self, sLine, _dAttr):
        """Extract the cards from the data.

           This is the terminating state, so we always return Cards from
           this.
           """
        oMatch = self._oCardRe.match(sLine)
        if oMatch:
            iCnt = int(oMatch.group('cnt'))
            sName = oMatch.group('name').split('  ')[0]
            # We see mixed spaces and tabs in the wild, so we need this
            sName = sName.strip()
            # Check for the advacned string and append advanced if needed
            if self._oAdvRe.search(sLine) and 'Adv' not in sName:
                sName += ' (Advanced)'
            self._oHolder.add(iCnt, sName, None, None)
        return self


# Parser
class ARDBTextParser(object):
    """Parser for the ARDB Text format."""
    def __init__(self):
        """Create an ARDBTextParser.

           oHolder is a sutekh.base.core.CardSetHolder.CardSetHolder object
           (or similar).
           """
        self._oState = None

    def reset(self, oHolder):
        """Reset the parser state"""
        self._oState = NameAndAuthor(oHolder)

    def parse(self, fIn, oHolder):
        """Parse the file"""
        self.reset(oHolder)
        for sLine in fIn:
            self._feed(sLine)

    def _feed(self, sLine):
        """Feed the next line to the current state object, and transition if
           required."""
        self._oState = self._oState.transition(sLine, {})
