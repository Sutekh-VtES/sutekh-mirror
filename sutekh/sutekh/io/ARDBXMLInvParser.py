# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# ARDB XML Inventory File Parser
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Parser for ARDB XML inventory format."""

import enum

from xml.etree.ElementTree import XMLParser
# pylint: disable=no-name-in-module, import-error
# For compatability with ElementTree 1.3
try:
    from xml.etree.ElementTree import ParseError
except ImportError:
    from xml.parsers.expat import ExpatError as ParseError
# pylint: enable=no-name-in-module, import-error
from sutekh.base.Utility import move_articles_to_front
from sutekh.core.ArdbInfo import unescape_ardb_expansion_name


class ARDBInvXMLState:
    """Simple State tracker used by the XMLParser"""
    # tag states of interest
    # We try and honour set info, although current ARDB seems a bit odd in
    # how it sets this
    @enum.unique
    class TagType(enum.Enum):
        """Tag types we care about"""
        ROOTTAG = 1
        NOTAG = 2
        INCARD = 3
        CARDNAME = 4
        CARDSET = 5
        ADVANCED = 6

    COUNT_KEY = 'have'

    ROOT = 'inventory'

    def __init__(self, oHolder):
        self._sData = ""
        self._sCardName = None
        self._sCardSet = None
        self._iCount = 0
        self._eState = self.TagType.ROOTTAG
        self._oHolder = oHolder
        self._sAdvanced = ''

    def reset(self):
        """Reset internal state"""
        self._sData = ""
        self._sCardName = None
        self._sCardSet = None
        self._iCount = 0
        self._eState = self.TagType.ROOTTAG
        self._sAdvanced = ''

    def start(self, sTag, dAttributes):
        """Start tag encountered"""
        if self._eState == self.TagType.ROOTTAG:
            if sTag == self.ROOT:
                self._eState = self.TagType.NOTAG
            else:
                raise IOError('Not a ARDB %s XML file type' % self.ROOT)
        elif self._eState == self.TagType.INCARD:
            if sTag == 'name':
                self._eState = self.TagType.CARDNAME
            elif sTag == 'set':
                self._eState = self.TagType.CARDSET
            elif sTag == 'adv':
                self._eState = self.TagType.ADVANCED
        elif self._eState == self.TagType.NOTAG:
            if sTag in ('vampire', 'card'):
                self._eState = self.TagType.INCARD
                self._iCount = int(dAttributes[self.COUNT_KEY])

    def end(self, sTag):
        """End tag encountered"""
        if self._eState == self.TagType.INCARD:
            if sTag in ('vampire', 'card'):
                if not self._sCardSet:
                    # convert empty string to None
                    self._sCardSet = None
                else:
                    self._sCardSet = unescape_ardb_expansion_name(
                        self._sCardSet)
                if self._sAdvanced == '(Advanced)':
                    self._sCardName = self._sCardName + ' (Advanced)'
                self._sCardName = move_articles_to_front(self._sCardName)
                self._oHolder.add(self._iCount, self._sCardName,
                                  self._sCardSet, None)
                self._sCardName = None
                self._sCardSet = None
                self._eState = self.TagType.NOTAG
                self._sAdvanced = ''
        elif self._eState == self.TagType.CARDNAME and sTag == 'name':
            self._eState = self.TagType.INCARD
            self._sCardName = self._sData
            self._sData = ""
        elif self._eState == self.TagType.CARDSET and sTag == 'set':
            self._eState = self.TagType.INCARD
            self._sCardSet = self._sData
            self._sData = ""
        elif self._eState == self.TagType.ADVANCED and sTag == 'adv':
            self._eState = self.TagType.INCARD
            self._sAdvanced = self._sData
            self._sData = ""

    def data(self, sText):
        """Text data for current tag"""
        if self._eState not in [self.TagType.INCARD, self.TagType.NOTAG]:
            if self._sData:
                self._sData += sText
            else:
                self._sData = sText


class ARDBXMLInvParser:
    """Parser for the ARDB Inventory XML format."""
    _cState = ARDBInvXMLState

    def parse(self, fIn, oHolder):
        """Parse XML file into the card set holder"""
        oParser = XMLParser(target=self._cState(oHolder))
        try:
            for sLine in fIn:
                oParser.feed(sLine)
        except ParseError as oExp:
            raise IOError('Not an valid XML file') from oExp
