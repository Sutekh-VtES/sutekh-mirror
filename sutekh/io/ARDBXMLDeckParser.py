# ARDBXMLDeckParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# ARDB XML File Deck Parser
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Parser for ARDB XML deck formats"""

from sutekh.io.ARDBXMLInvParser import ARDBInvXMLState, ARDBXMLInvParser


class ARDBDeckXMLState(ARDBInvXMLState):
    """Simple State tracker used by the XMLParser"""
    # tag states of interest
    ROOTTAG, NOTAG, DECKNAME, DECKAUTHOR, DECKCOMMENT, INCARD, CARDNAME, \
            CARDSET, ADVANCED = range(9)

    COUNT_KEY = 'count'

    ROOT = 'deck'

    def start(self, sTag, dAttributes):
        """Start tag encountered"""
        # Handle those different from base class
        if self._iState == self.NOTAG and sTag in ['name', 'author',
                'description']:
            if sTag == 'name':
                self._iState = self.DECKNAME
            elif sTag == 'author':
                self._iState = self.DECKAUTHOR
            elif sTag == 'description':
                self._iState = self.DECKCOMMENT
        else:
            # Fall back to base class
            super(ARDBDeckXMLState, self).start(sTag, dAttributes)

    def end(self, sTag):
        """End tag encountered"""
        # Handle cases different to base class
        if self._iState == self.DECKAUTHOR and sTag == 'author':
            self._oHolder.author = self._sData
            self._set_no_tag()
        elif self._iState == self.DECKNAME and sTag == 'name':
            self._oHolder.name = self._sData
            self._set_no_tag()
        elif self._iState == self.DECKCOMMENT and sTag == 'description':
            self._oHolder.comment = self._sData
            self._set_no_tag()
        else:
            # Fall back to base class
            super(ARDBDeckXMLState, self).end(sTag)

    def _set_no_tag(self):
        """Set state back to NOTAG state"""
        self._iState = self.NOTAG
        self._sData = ""


class ARDBXMLDeckParser(ARDBXMLInvParser):
    """Parser for the ARDB XML deck format."""

    _cState = ARDBDeckXMLState
