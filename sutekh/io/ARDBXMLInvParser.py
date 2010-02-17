# ARDBXMLInvParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# ARDB XML Inventory File Parser
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Parser for ARDB XML inventory format."""

# pylint: disable-msg=E0611, F0401
# pylint doesn't like the handling of the differences between 2.4 and 2.5
try:
    from xml.etree.ElementTree import XMLParser
except ImportError:
    from elementtree.ElementTree import XMLTreeBuilder as XMLParser
# pylint: enable-msg=E0611, F0401
from sutekh.core.ArdbInfo import unescape_ardb_name, \
        unescape_ardb_expansion_name

class XMLState(object):
    """Simple State tracker used by the XMLParser"""
    # tag states of interest
    # We try and honour set info, although current ARDB seems a bit odd in
    # how it sets this
    NOTAG, INCARD, CARDNAME, CARDSET, ADVANCED = range(5)

    def __init__(self, oHolder):
        self._sData = ""
        self._sCardName = None
        self._sCardSet = None
        self._sAdvanced = ''
        self._iCount = 0
        self._iState = self.NOTAG
        self._oHolder = oHolder

    def reset(self):
        """Reset internal state"""
        self._sData = ""
        self._sCardName = None
        self._sCardSet = None
        self._iCount = 0
        self._iState = self.NOTAG
        self._sAdvanced = ''

    def start(self, sTag, dAttributes):
        """Start tag encountered"""
        if self._iState == self.INCARD:
            if sTag == 'name':
                self._iState = self.CARDNAME
            elif sTag == 'set':
                self._iState = self.CARDSET
            elif sTag == 'adv':
                self._iState = self.ADVANCED
        elif self._iState == self.NOTAG:
            if sTag == 'vampire' or sTag == 'card':
                self._iState = self.INCARD
                self._iCount = int(dAttributes['have'])

    def end(self, sTag):
        """End tage encountered"""
        if self._iState == self.INCARD:
            if sTag == 'vampire' or sTag == 'card':
                if not self._sCardSet:
                    # convert empty string to None
                    self._sCardSet = None
                else:
                    self._sCardSet = unescape_ardb_expansion_name(
                            self._sCardSet)
                if self._sAdvanced == '(Advanced)':
                    self._sCardName = self._sCardName + ' (Advanced)'
                self._sCardName = unescape_ardb_name(self._sCardName)
                self._oHolder.add(self._iCount, self._sCardName,
                        self._sCardSet)
                self._sCardName = None
                self._sCardSet = None
                self._iState = self.NOTAG
                self._sAdvanced = ''
        elif self._iState == self.CARDNAME and sTag == 'name':
            self._iState = self.INCARD
            self._sCardName = self._sData
            self._sData = ""
        elif self._iState == self.CARDSET and sTag == 'set':
            self._iState = self.INCARD
            self._sCardSet = self._sData
            self._sData = ""
        elif self._iState == self.ADVANCED and sTag == 'adv':
            self._iState = self.INCARD
            self._sAdvanced = self._sData
            self._sData = ""

    def data(self, sText):
        """Text data for current tag"""
        if self._iState not in [self.INCARD, self.NOTAG]:
            if self._sData:
                self._sData += sText
            else:
                self._sData = sText


class ARDBXMLInvParser(XMLParser, object):
    """Parser for the ARDB Inventory XML format."""
    def __init__(self, oHolder):
        self._oHolder = oHolder
        self._oState = XMLState(self._oHolder)
        super(ARDBXMLInvParser, self).__init__(target=self._oState)
        self.reset()

    def reset(self):
        """Reset parser state"""
        self._oState.reset()

