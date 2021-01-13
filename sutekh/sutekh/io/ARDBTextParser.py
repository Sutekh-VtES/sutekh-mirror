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

from sutekh.base.core.BaseTables import AbstractCard
from sutekh.base.core.BaseFilters import MultiCardTypeFilter
from sutekh.base.io.SutekhBaseHTMLParser import HolderState

from sutekh.core.ArdbInfo import ArdbInfo


class SingleCard(ArdbInfo):
    """Class to formate a single card appropriately"""

    def format_crypt_card(self, oCard):
        """Format the crypt card to possible ARDB outputs so we can match
           lines where we can't split on whitespace reliably."""
        dFull = self._format_crypt_line(oCard, 1)
        # We don't need count
        dFull.pop('count')
        dFull['disc'] = self._gen_disciplines(oCard).strip()
        dFull['title'] = dFull['title'].strip()
        dFull['name'] = dFull['name'].strip()
        # We generate candidates for a couple of different possible formats
        dTruncated = dFull.copy()
        if dTruncated['clan'].endswith('antitribu'):
            dTruncated['clan'] = '!' + dTruncated['clan'].replace(' antitribu', '')
        elif 'Imbued' not in dTruncated['clan']:
            dTruncated['clan'] = dTruncated['clan'][:10].strip()
        dTruncated['name'] = dTruncated['name'].ljust(18)[:18].strip()

        if dFull['title'] and dFull['adv'] == 'Adv':
            sFull = "%(name)s %(adv)s %(capacity)d %(disc)s %(title)s %(clan)s:%(group)d" % dFull
            sTruncated = "%(name)s %(adv)s %(capacity)d %(disc)s %(title)s %(clan)s:%(group)d" % dTruncated
        elif dFull['adv'] == 'Adv':
            sFull = "%(name)s %(adv)s %(capacity)d %(disc)s %(clan)s:%(group)d" % dFull
            sTruncated = "%(name)s %(adv)s %(capacity)d %(disc)s %(clan)s:%(group)d" % dTruncated
        elif dFull['title']:
            sFull = "%(name)s %(capacity)d %(disc)s %(title)s %(clan)s:%(group)d" % dFull
            sTruncated = "%(name)s %(capacity)d %(disc)s %(title)s %(clan)s:%(group)d" % dTruncated
        else:
            sFull = "%(name)s %(capacity)d %(disc)s %(clan)s:%(group)d" % dFull
            sTruncated = "%(name)s %(capacity)d %(disc)s %(clan)s:%(group)d" % dTruncated
        return sFull.lower(), sTruncated.lower()


def gen_name_lookups():
    """Generate lookups for names of the form:
        2x Nakhorheb 10 OBF PRE SER Follower:4
      i.e., for cases where tabs or multiple spaces have been
      combined into single spaces, such as posts to the
      vekn forum."""
    dNameCache = {}
    oFormatter = SingleCard()
    oCryptFilter = MultiCardTypeFilter(['Vampire', 'Imbued'])
    for oCard in oCryptFilter.select(AbstractCard):
        sFull, sTrunc = oFormatter.format_crypt_card(oCard)
        dNameCache[sFull] = oCard.name
        dNameCache[sTrunc] = oCard.name
    return dNameCache


class HolderWithCacheState(HolderState):
    """State holder with a lookup cache for matching variant names, etc."""
    # pylint: disable=abstract-method
    # This is still an abstract class

    def __init__(self, oHolder, dNameCache):
        super().__init__(oHolder)
        self._dNameCache = dNameCache


# HolderWithCacheState Classes
class NameAndAuthor(HolderWithCacheState):
    """HolderWithCacheState for extracting Name and Author."""
    # pylint: disable=arguments-differ
    # pylint doesn't like that we mark dAttr as unused here
    def transition(self, sLine, _dAttr):
        """Process the line for Name and Author - trnaisiotn to Description
           if needed."""
        # Check for crypt line, as description isn't always present
        if sLine.strip().startswith('Crypt ['):
            return Cards(self._oHolder, self._dNameCache)
        if sLine.strip().startswith('Crypt: ('):
            return Cards(self._oHolder, self._dNameCache)
        if sLine.strip().startswith('Crypt ('):
            return Cards(self._oHolder, self._dNameCache)

        aParts = sLine.split(':', 1)

        if len(aParts) != 2:
            return self  # Nothing of interest seen

        sKey, sValue = aParts[0].strip(), aParts[1].strip()

        if sKey == "Deck Name":
            self._oHolder.name = sValue
        elif sKey in ("Author", "Created By", "Created by"):
            self._oHolder.author = sValue
        elif sKey == "Description":
            oDesc = Description(self._oHolder, self._dNameCache)
            if sValue:
                oDesc.data(sValue)
            return oDesc

        return self


class Description(HolderWithCacheState):
    """HolderWithCacheState for extracting description"""
    # pylint: disable=arguments-differ
    # pylint doesn't like that we mark dAttr as unused here
    def transition(self, sLine, _dAttr):
        """Process the line for the description and transition to Cards
           state if needed."""
        if sLine.strip().startswith('Crypt ['):
            self._oHolder.comment = self._sData
            return Cards(self._oHolder, self._dNameCache)
        if sLine.strip().startswith('Crypt: ('):
            self._oHolder.comment = self._sData
            return Cards(self._oHolder, self._dNameCache)
        if sLine.strip().startswith('Crypt ('):
            self._oHolder.comment = self._sData
            return Cards(self._oHolder, self._dNameCache)
        self.data(sLine)
        return self


class Cards(HolderWithCacheState):
    """HolderWithCacheState for extracting the cards"""
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
            if sName.lower() in self._dNameCache:
                sName = self._dNameCache[sName.lower()]
            # Check for the advacned string and append advanced if needed
            if self._oAdvRe.search(sLine) and 'Adv' not in sName:
                sName += ' (Advanced)'
            self._oHolder.add(iCnt, sName, None, None)
        return self


# Parser
class ARDBTextParser:
    """Parser for the ARDB Text format."""
    def __init__(self):
        """Create an ARDBTextParser.

           oHolder is a sutekh.base.core.CardSetHolder.CardSetHolder object
           (or similar).
           """
        self._oState = None

    def reset(self, oHolder):
        """Reset the parser state"""
        self._oState = NameAndAuthor(oHolder, gen_name_lookups())

    def parse(self, fIn, oHolder):
        """Parse the file"""
        self.reset(oHolder)
        for sLine in fIn:
            self._feed(sLine)

    def _feed(self, sLine):
        """Feed the next line to the current state object, and transition if
           required."""
        self._oState = self._oState.transition(sLine, {})
