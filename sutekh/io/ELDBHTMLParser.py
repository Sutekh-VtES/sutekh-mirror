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

import HTMLParser
import re

# State Base Classes

class StateError(Exception):
    """Error case in the state true"""
    pass

class State(object):
    """Base class for parser states"""
    def __init__(self, oHolder):
        super(State, self).__init__()
        self._sData = ""
        self._oHolder = oHolder

    def transition(self, sTag, dAttr):
        """Transition from one state to another"""
        raise NotImplementedError

    def data(self, sData):
        """Add data to the state"""
        self._sData += sData

# State Classes

class Collecting(State):
    """Default state - transitions to other states as needed"""
    def transition(self, sTag, dAttr):
        """Transition to CardItem of DeckInfoItem as needed."""
        if sTag == 'td' and dAttr.get('colspan') == '2':
            return CardItem(self._oHolder)
        elif sTag == 'td':
            return DeckInfoItem(self._oHolder)
        else:
            return self

class DeckInfoItem(State):
    """States for the table rows describing the deck."""

    # pylint: disable-msg=W0613
    # dAttr required by function signature
    def transition(self, sTag, dAttr):
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

class CardItem(State):
    """State for the table rows listing the cards in the deck."""
    _oCountRegex = re.compile(r'^[^0-9]*(?P<cnt>[0-9]+)[^0-9]*')

    def __init__(self, oHolder):
        super(CardItem, self).__init__(oHolder)
        self._iCnt = None

    # pylint: disable-msg=W0613
    # dAttr required by function signature
    def transition(self, sTag, dAttr):
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

class ELDBHTMLParser(HTMLParser.HTMLParser, object):
    """Actual Parser for the ELDB HTML files."""
    def __init__(self, oHolder):
        """Create an ELDBHTMLParser.

           oHolder is a sutekh.core.CardSetHolder.CardSetHolder object
           (or similar).
           """
        self._oHolder = oHolder
        self._oState = Collecting(self._oHolder)
        super(ELDBHTMLParser, self).__init__()

    def reset(self):
        """Reset the parser"""
        super(ELDBHTMLParser, self).reset()
        self._oState = Collecting(self._oHolder)

    # pylint: disable-msg=C0111
    # names are as listed in HTMLParser docs, so no need for docstrings
    def handle_starttag(self, sTag, aAttr):
        self._oState = self._oState.transition(sTag.lower(), dict(aAttr))

    def handle_endtag(self, sTag):
        self._oState = self._oState.transition('/' + sTag.lower(), {})

    def handle_data(self, sData):
        self._oState.data(sData)

    # pylint: disable-msg=C0321
    # these don't need statements
    def handle_charref(self, sName): pass
    def handle_entityref(self, sName): pass
