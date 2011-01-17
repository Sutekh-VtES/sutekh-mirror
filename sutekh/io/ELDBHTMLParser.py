# ELDBHTMLParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# ELDB HTML Deck Parser
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

# pylint: disable-msg=C0301
# documentation, so line length ignored
"""Parser for ELDB HTML format.

   Example HTML:

   <TR><TD WIDTH=130>Deck Name:</TD><TD WIDTH=520>Osebo Preconstructed Starter Deck</TD></TR>
   <TR><TD WIDTH=130>Created By:</TD><TD WIDTH=520>L. Scott Johnson</TD></TR>
   <TR><TD WIDTH=130 VALIGN="top">Description:</TD><TD WIDTH=520>The Osebo Preconstructed Starter Deck from Legacies of Blood.</TD></TR>
   <TR><TD COLSPAN=2 WIDTH=650>&nbsp;</TD><TR>
   <TR><TD COLSPAN=2 WIDTH=650 BGCOLOR="#eeeeee">Crypt: (12 cards, Min: 12, Max: 36, Avg: 6.00)</TD></TR>
   <TR><TD COLSPAN=2 WIDTH=650>2&nbsp;&nbsp;<a href="http://www.white-wolf.com/vtes/index.php?line=Checklist_LegaciesOfBlood" class="textLink">Uzoma</a> ... </TD></TR>
   ...
   <TR><TD COLSPAN=2 WIDTH=650>2&nbsp;&nbsp;<a href="http://monger.vekn.org/showcard.html?ID=109" class="textLink">Blood Doll</a></TD></TR>
   """
# pylint: enable-msg=C0301

from sutekh.io.SutekhBaseHTMLParser import SutekhBaseHTMLParser, HolderState
import re


# State Classes
class Collecting(HolderState):
    """Default state - transitions to other states as needed"""

    def transition(self, sTag, dAttr):
        """Transition to CardItem of DeckInfoItem as needed."""
        if sTag == 'td' and dAttr.get('colspan') == '2':
            return CardItem(self._oHolder)
        elif sTag == 'td':
            return DeckInfoItem(self._oHolder)
        else:
            return self


class DeckInfoItem(HolderState):
    """States for the table rows describing the deck."""

    def transition(self, sTag, _dAttr):
        """Transition back to Collecting if needed"""
        if sTag == '/tr':
            aParts = self._sData.split(':', 1)

            if len(aParts) != 2:
                return Collecting(self._oHolder)

            sItem, sText = aParts

            if sItem == "Deck Name":
                self._oHolder.name = sText
            elif sItem == "Created By":
                self._oHolder.author = sText
            elif sItem == "Description":
                self._oHolder.comment = sText

            return Collecting(self._oHolder)
        else:
            return self


class CardItem(HolderState):
    """State for the table rows listing the cards in the deck."""
    _oCountRegex = re.compile(r'^[^0-9]*(?P<cnt>[0-9]+)[^0-9]*')

    def __init__(self, oHolder):
        super(CardItem, self).__init__(oHolder)
        self._iCnt = None

    def transition(self, sTag, _dAttr):
        """Extract card data and add it back to the CardSetHolder if possible,
           and transtion back to Collecting if needed."""
        if sTag == 'a':
            oMatch = self._oCountRegex.match(self._sData)
            if oMatch:
                self._iCnt = int(oMatch.group('cnt'))
            else:
                self._iCnt = 1
            self._sData = ""
            return self
        elif sTag == '/a':
            assert(self._iCnt is not None)
            sName = self._sData.strip()
            sName = sName.replace("`", "'")
            # No expansion info for these
            self._oHolder.add(self._iCnt, sName, None)
            self._iCnt = None
            self._sData = ""
            return Collecting(self._oHolder)
        elif sTag == '/tr':
            return Collecting(self._oHolder)
        else:
            return self


# Parser
class ELDBHTMLParser(SutekhBaseHTMLParser):
    """Actual Parser for the ELDB HTML files."""

    def __init__(self):
        """Create an ELDBHTMLParser.
           """
        # super __init__ will call rest, so need this
        self._oHolder = None  # Placeholder for later
        super(ELDBHTMLParser, self).__init__()
        # Don't need to set oState, since reset will do that

    def reset(self):
        """Reset the parser"""
        super(ELDBHTMLParser, self).reset()
        self._oState = Collecting(self._oHolder)

    def parse(self, fIn, oHolder):
        """Parse a file into the given holder"""
        self._oHolder = oHolder
        self.reset()
        for sLine in fIn:
            self.feed(sLine)
