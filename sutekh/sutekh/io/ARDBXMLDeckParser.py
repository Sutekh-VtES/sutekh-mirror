# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# ARDB XML File Deck Parser
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Parser for ARDB XML deck formats"""
import enum

from sutekh.io.ARDBXMLInvParser import ARDBInvXMLState, ARDBXMLInvParser


class ARDBDeckXMLState(ARDBInvXMLState):
    """Simple State tracker used by the XMLParser"""
    # tag states of interest
    @enum.unique
    class TagType(enum.Enum):
        """Tag types"""
        # We need to duplicate the list in ARDBInvXMLState due to
        # enum's subclassing restrictions
        ROOTTAG = 1
        NOTAG = 2
        DECKNAME = 3
        DECKAUTHOR = 4
        DECKCOMMENT = 5
        INCARD = 6
        CARDNAME = 7
        CARDSET = 8
        ADVANCED = 9

    COUNT_KEY = 'count'

    ROOT = 'deck'

    def start(self, sTag, dAttributes):
        """Start tag encountered"""
        # Handle those different from base class
        if self._eState == self.TagType.NOTAG and sTag in ['name', 'author',
                                                           'description']:
            if sTag == 'name':
                self._eState = self.TagType.DECKNAME
            elif sTag == 'author':
                self._eState = self.TagType.DECKAUTHOR
            elif sTag == 'description':
                self._eState = self.TagType.DECKCOMMENT
        else:
            # Fall back to base class
            super().start(sTag, dAttributes)

    def end(self, sTag):
        """End tag encountered"""
        # Handle cases different to base class
        if self._eState == self.TagType.DECKAUTHOR and sTag == 'author':
            self._oHolder.author = self._sData
            self._set_no_tag()
        elif self._eState == self.TagType.DECKNAME and sTag == 'name':
            self._oHolder.name = self._sData
            self._set_no_tag()
        elif self._eState == self.TagType.DECKCOMMENT and \
                sTag == 'description':
            self._oHolder.comment = self._sData
            self._set_no_tag()
        else:
            # Fall back to base class
            super().end(sTag)

    def _set_no_tag(self):
        """Set state back to NOTAG state"""
        self._eState = self.TagType.NOTAG
        self._sData = ""


class ARDBXMLDeckParser(ARDBXMLInvParser):
    """Parser for the ARDB XML deck format."""

    _cState = ARDBDeckXMLState
