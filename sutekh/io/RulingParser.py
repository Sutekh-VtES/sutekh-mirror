# RulingParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# WhiteWolf Rulings Parser
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""HTML Parser for extracting card rulings from the WW online rulings list."""

import HTMLParser, re
from logging import Logger
from sutekh.core.SutekhObjects import IAbstractCard, SutekhObjectMaker
from sqlobject import SQLObjectNotFound

# Ruling Saver

class RuleDict(dict):
    """Dictionary object which holds the extracted rulings information."""
    _aSectionKeys = ['title', 'card']
    _oMasterOut = re.compile(r'\s*-\s*Master\s*\:?\s*Out\-of\-Turn$')
    _oCommaThe = re.compile(r'\s*\,\s*The$')
    _dOddTitles = {
        'Absilmilard\'s Army' : 'Absimiliard\'s Army',
        'Carlotta' : 'Carlotta Giovanni',
        'Donal O\'Connor' : u'D\xf3nal O\'Connor',
        'Herald of Topeth' : 'Herald of Topheth',
        'Illusions of Kindred' : 'Illusions of the Kindred',
        'Khobar Towers' : 'Khobar Towers, Al-Khubar',
        'Mehemet of the Ahl-i-Batin' : 'Mehemet of the Ahl-i-Batin (Mage)',
        'Lazar Dobrescu' : u'L\xe1z\xe1r Dobrescu',
        'Merill Molitor' : 'Merrill Molitor',
        'Rotschreck' : u'R\xf6tschreck',
        'Seattle Committe' : 'Seattle Committee',
        'Shackles of Enkindu' : 'Shackles of Enkidu',
        'Shadow Court Satyr' : 'Shadow Court Satyr (Changeling)',
        'Smiling Jack the Anarch' : 'Smiling Jack, The Anarch',
        'Tereza Rotas' : 'Tereza Rostas',
        'Ur-Shulgi' : 'Ur-Shulgi, The Shepherd',
    }

    def __init__(self, oLogger):
        self.oLogger = oLogger
        super(RuleDict, self).__init__()
        self._oMaker = SutekhObjectMaker()

    def _find_card(self, sTitle):
        """Find the abstract card this rules applies to."""
        sTitle = self._oMasterOut.sub('', sTitle)
        sTitle = self._oCommaThe.sub('', sTitle)

        # pylint: disable-msg=W0704
        # Skipping SQLObject exceptions is the right thing to do here
        try:
            return IAbstractCard(sTitle)
        except SQLObjectNotFound:
            pass

        try:
            return IAbstractCard(self._dOddTitles[sTitle])
        except KeyError:
            pass
        except SQLObjectNotFound:
            pass

        try:
            return IAbstractCard(('The ' + sTitle))
        except SQLObjectNotFound:
            pass

        return None

    def clear_rule(self):
        """Remove current contents of the rule."""
        dKeep = {}
        for sKey in self._aSectionKeys:
            if self.has_key(sKey):
                dKeep[sKey] = self[sKey]
        self.clear()
        for (sKey, sValue) in dKeep.items():
            self[sKey] = sValue

    def save(self):
        """Add the rulings to the database."""
        if not (self.has_key('title') and self.has_key('code') \
                and self.has_key('text')):
            return

        if not self.has_key('card'):
            self['card'] = self._find_card(self['title'])

        if self['card'] is None:
            return

        self.oLogger.info('Card: %s', self['card'].name)

        oRuling = self._oMaker.make_ruling(self['text'], self['code'])

        if self.has_key('url'):
            oRuling.url = self['url']

        self['card'].addRuling(oRuling)

# State Base Classes

class StateError(Exception):
    """Error thrown in state transitions."""
    pass

class State(object):
    """Base class for all States"""
    def __init__(self, oLogger):
        super(State, self).__init__()
        self._sData = ""
        self.oLogger = oLogger

    def transition(self, sTag, dAttr):
        """Transition from one state to another"""
        raise NotImplementedError

    def data(self, sData):
        """Add data to the state"""
        self._sData += sData

class StateWithRule(State):
    """Base class for states which contain information of interest"""
    # pylint: disable-msg=W0223
    # transition method is still abstract here
    def __init__(self, dInfo, oLogger):
        super(StateWithRule, self).__init__(oLogger)
        self._dInfo = dInfo

# State Classes

class NoSection(State):
    """Not in any ruling section."""
    # pylint: disable-msg=W0613
    # dAttr needed by function signature
    def transition(self, sTag, dAttr):
        """Transition ot InSection if needed."""
        if sTag == 'p':
            return InSection(RuleDict(self.oLogger), self.oLogger)
        else:
            return self

class InSection(StateWithRule):
    """In a ruling section."""
    # pylint: disable-msg=W0613
    # dAttr needed by function signature
    def transition(self, sTag, dAttr):
        """Transition to SectionTitle or NoSection as needed."""
        if sTag == 'b':
            return SectionTitle(self._dInfo, self.oLogger)
        elif sTag == 'p':
            # skip to next section
            return InSection(RuleDict(self.oLogger), self.oLogger)
        else:
            return NoSection(self.oLogger)

class SectionTitle(StateWithRule):
    """In the tilte of the section."""
    # pylint: disable-msg=W0613
    # dAttr needed by function signature
    def transition(self, sTag, dAttr):
        """Transition to SectionWithTitle if needed."""
        if sTag == 'b':
            raise StateError()
        elif sTag == '/b':
            self._dInfo['title'] = self._sData.strip().strip(':')
            return SectionWithTitle(self._dInfo, self.oLogger)
        else:
            return self

class SectionWithTitle(StateWithRule):
    """In a section with a known title."""
    # pylint: disable-msg=W0613
    # dAttr needed by function signature
    def transition(self, sTag, dAttr):
        """Transition to SectionRule, InSection or NoSection if needed."""
        if sTag == 'li':
            return SectionRule(self._dInfo, self.oLogger)
        elif sTag == 'p':
            # skip to next section
            return InSection(RuleDict(self.oLogger), self.oLogger)
        elif sTag == '/p':
            return NoSection(self.oLogger)
        else:
            return self

class SectionRule(StateWithRule):
    """In a ruling in the section."""
    def transition(self, sTag, dAttr):
        """Transition to the appropriate InRule State."""
        if sTag == 'span' and dAttr.get('class') in ['ruling', 'errata',
                'clarification']:
            return InRuleText(self._dInfo, self.oLogger)
        elif sTag == 'a':
            self._dInfo['url'] = dAttr['href']
            return InRuleUrl(self._dInfo, self.oLogger)
        elif sTag == '/li':
            if not self._dInfo.has_key('code'):
                self._dInfo['code'] = self._sData.strip()
            self._dInfo.save()
            self._dInfo.clear_rule()
            return SectionWithTitle(self._dInfo, self.oLogger)
        elif sTag == 'li':
            # handles unclosed <li> inside section block
            # skip to next rule
            if not self._dInfo.has_key('code'):
                self._dInfo['code'] = self._sData.strip()
            self._dInfo.save()
            self._dInfo.clear_rule()
            return SectionRule(self._dInfo, self.oLogger)
        elif sTag == '/p':
            # handles unclosed <li> at end of section block
            # skip to next section
            if not self._dInfo.has_key('code'):
                self._dInfo['code'] = self._sData.strip()
            self._dInfo.save()
            self._dInfo.clear_rule()
            return NoSection(self.oLogger)
        return self

class InRuleText(StateWithRule):
    """In the text of a ruling."""
    # pylint: disable-msg=W0613
    # dAttr needed by function signature
    def transition(self, sTag, dAttr):
        """Transition to SectionRule if needed."""
        if sTag == 'span':
            raise StateError()
        elif sTag == '/span':
            self._dInfo['text'] = self._sData.strip()
            return SectionRule(self._dInfo, self.oLogger)
        else:
            return self

class InRuleUrl(StateWithRule):
    """In the url associated with this ruling."""
    # pylint: disable-msg=W0613
    # dAttr needed by function signature
    def transition(self, sTag, dAttr):
        """Transition to SectionRule if needed."""
        if sTag == 'a':
            raise StateError()
        elif sTag == '/a':
            self._dInfo['code'] = self._sData.strip()
            return SectionRule(self._dInfo, self.oLogger)
        else:
            return self

# Parser

class RulingParser(HTMLParser.HTMLParser, object):
    """Actual Parser for the WW rulings HTML files."""
    def __init__(self, oLogHandler):
        # super().__init__ calls reset, so we need this first
        self.oLogger = Logger('WW Rulings parser')
        if oLogHandler is not None:
            self.oLogger.addHandler(oLogHandler)
        super(RulingParser, self).__init__()
        self._oState = NoSection(self.oLogger)

    # pylint: disable-msg=C0111
    # names are as listed in HTMLParser docs, so no need for docstrings
    def reset(self):
        super(RulingParser, self).reset()
        self._oState = NoSection(self.oLogger)

    def handle_starttag(self, sTag, aAttr):
        self._oState = self._oState.transition(sTag.lower(), dict(aAttr))

    def handle_endtag(self, sTag):
        self._oState = self._oState.transition('/'+sTag.lower(), {})

    def handle_data(self, sData):
        self._oState.data(sData)

    # pylint: disable-msg=C0321
    # these don't need statements
    def handle_charref(self, sName): pass
    def handle_entityref(self, sName): pass
