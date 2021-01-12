# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# WhiteWolf Rulings Parser
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""HTML Parser for extracting card rulings from the WW online rulings list."""

import re
from logging import Logger

from sqlobject import SQLObjectNotFound

from sutekh.base.io.SutekhBaseHTMLParser import (SutekhBaseHTMLParser,
                                                 HTMLStateError, LogState,
                                                 LogStateWithInfo)
from sutekh.base.core.BaseAdapters import IAbstractCard

from sutekh.core.SutekhObjectMaker import SutekhObjectMaker


# Ruling Saver
class RuleDict(dict):
    """Dictionary object which holds the extracted rulings information."""

    _aSectionKeys = ['title', 'card']
    _oMasterOut = re.compile(r'\s*-\s*Master\s*\:?\s*Out\-of\-Turn$')
    _oCommaThe = re.compile(r'\s*\,\s*The$')
    _dOddTitles = {
        'Absilmilard\'s Army': 'Absimiliard\'s Army',
        'Ankara Citadel': 'The Ankara Citadel, Turkey',
        'Carlotta': 'Carlotta Giovanni',
        'Donal O\'Connor': u'D\xf3nal O\'Connor',
        'Herald of Topeth': 'Herald of Topheth',
        'Illusions of Kindred': 'Illusions of the Kindred',
        'Khobar Towers': 'Khobar Towers, Al-Khubar',
        'Mehemet of the Ahl-i-Batin': 'Mehemet of the Ahl-i-Batin (Mage)',
        'Lazar Dobrescu': u'L\xe1z\xe1r Dobrescu',
        'Merill Molitor': 'Merrill Molitor',
        'Peace Treaty:shado': 'Peace Treaty',
        'Rotschreck': u'R\xf6tschreck',
        'Seattle Committe': 'Seattle Committee',
        'Shackles of Enkindu': 'Shackles of Enkidu',
        'Shadow Court Satyr': 'Shadow Court Satyr (Changeling)',
        'Smiling Jack the Anarch': 'Smiling Jack, The Anarch',
        'Tereza Rotas': 'Tereza Rostas',
        'The Eldest Command the Undeath': 'The Eldest Command Undeath',
        'Ur-Shulgi': 'Ur-Shulgi, The Shepherd',
    }

    def __init__(self, oLogger):
        self._oLogger = oLogger
        super().__init__()
        self._oMaker = SutekhObjectMaker()

    def _find_card(self, sTitle):
        """Find the abstract card this rules applies to."""
        sTitle = self._oMasterOut.sub('', sTitle)
        sTitle = self._oCommaThe.sub('', sTitle)

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
            if sKey in self:
                dKeep[sKey] = self[sKey]
        self.clear()
        for (sKey, sValue) in dKeep.items():
            self[sKey] = sValue

    def save(self):
        """Add the rulings to the database."""
        if not ('title' in self and 'code' in self
                and 'text' in self):
            return

        if 'card' not in self:
            self['card'] = self._find_card(self['title'])

        if self['card'] is None:
            return

        self._oLogger.info('Card: %s', self['card'].name)

        oRuling = self._oMaker.make_ruling(self['text'], self['code'])

        if 'url' in self:
            oRuling.url = self['url']
            oRuling.syncUpdate()

        self['card'].addRuling(oRuling)


# State Classes
class NoSection(LogState):
    """Not in any ruling section."""

    def transition(self, sTag, _dAttr):
        """Transition to InSection if needed."""
        if sTag == 'p':
            return InSection(RuleDict(self._oLogger), self._oLogger)
        return self


class InSection(LogStateWithInfo):
    """In a ruling section."""

    def transition(self, sTag, _dAttr):
        """Transition to SectionTitle or NoSection as needed."""
        if sTag == 'b':
            return SectionTitle(self._dInfo, self._oLogger)
        if sTag == 'p':
            # skip to next section
            return InSection(RuleDict(self._oLogger), self._oLogger)
        return NoSection(self._oLogger)


class SectionTitle(LogStateWithInfo):
    """In the title of the section."""

    def transition(self, sTag, _dAttr):
        """Transition to SectionWithTitle if needed."""
        if sTag == 'b':
            raise HTMLStateError('Unexpected tag in SectionTitle',
                                 sTag, self._sData)
        if sTag == '/b':
            self._dInfo['title'] = self._sData.strip().strip(':')
            return SectionWithTitle(self._dInfo, self._oLogger)
        return self


class SectionWithTitle(LogStateWithInfo):
    """In a section with a known title."""

    def transition(self, sTag, _dAttr):
        """Transition to SectionRule, InSection or NoSection if needed."""
        if sTag == 'ul':
            return SectionRule(self._dInfo, self._oLogger)
        if sTag == 'p':
            # skip to next section
            return InSection(RuleDict(self._oLogger), self._oLogger)
        if sTag == '/ul':
            return NoSection(self._oLogger)
        return self


class SectionRule(LogStateWithInfo):
    """In a ruling in the section."""

    def transition(self, sTag, _dAttr):
        """Transition to the appropriate InRule State."""
        if sTag == 'li':
            return InRuleText(self._dInfo, self._oLogger)
        if sTag == '/ul':
            return NoSection(self._oLogger)
        return self


class InRuleText(LogStateWithInfo):
    """In the text of a ruling."""

    oCodePattern = re.compile(r'\[[^]]*\]')

    def transition(self, sTag, dAttr):
        """Transition to SectionRule if needed."""
        if sTag == 'a':
            if 'text' not in self._dInfo:
                self._dInfo['text'] = self._sData.strip()
            self._dInfo['url'] = dAttr['href']
            return InRuleUrl(self._dInfo, self._oLogger)
        if sTag == '/li':
            if 'code' not in self._dInfo:
                # Rule without an url, so extract the last section in []'s
                # from the text
                oMatch = self.oCodePattern.search(self._sData)
                if oMatch:
                    # Add code, and remove it from text
                    self._dInfo['code'] = oMatch.group()
                    self._dInfo['text'] = \
                            self.oCodePattern.sub('', self._sData).strip()
            self._dInfo.save()
            self._dInfo.clear_rule()
            return SectionRule(self._dInfo, self._oLogger)
        return self


class InRuleUrl(LogStateWithInfo):
    """In the url associated with this ruling."""

    def transition(self, sTag, _dAttr):
        """Transition to SectionRule if needed."""
        if sTag == 'a':
            raise HTMLStateError('Unexpected tag in InRuleUrl',
                                 sTag, self._sData)
        if sTag == '/a':
            # Some rulings have multiple codes, but we only take the last one
            # since that matches the url we keep
            self._dInfo['code'] = self._sData.strip()
            return InRuleText(self._dInfo, self._oLogger)
        return self


# Parser
# pylint: disable=abstract-method
# See comments in base.io.SutekhBaseHTMLParser
class RulingParser(SutekhBaseHTMLParser):
    """Actual Parser for the WW rulings HTML files."""

    def __init__(self, oLogHandler):
        # super().__init__ calls reset, so we need this first
        self._oLogger = Logger('WW Rulings parser')
        if oLogHandler is not None:
            self._oLogger.addHandler(oLogHandler)
        super().__init__()
        # No need to touch self._oState, reset will do that for us

    def reset(self):
        """Reset the parser"""
        super().reset()
        self._oState = NoSection(self._oLogger)
