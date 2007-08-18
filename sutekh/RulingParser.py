# RulingsParser.py
# WhiteWolf Rulings Parser
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import HTMLParser, re
from sutekh.SutekhObjects import AbstractCard, IRuling
from sqlobject import SQLObjectNotFound

# Ruling Saver

class RuleDict(dict):
    _aSectionKeys = ['title','card']
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

    def __init__(self):
        super(RuleDict,self).__init__()

    def _findCard(self,sTitle):
        sTitle = self._oMasterOut.sub('',sTitle)
        sTitle = self._oCommaThe.sub('',sTitle)

        try:
            return AbstractCard.byCanonicalName(sTitle.encode('utf8').lower())
        except SQLObjectNotFound:
            pass

        try:
            return AbstractCard.byCanonicalName(self._dOddTitles[sTitle].encode('utf8').lower())
        except KeyError:
            pass
        except SQLObjectNotFound:
            pass

        try:
            return AbstractCard.byCanonicalName(('The ' + sTitle).encode('utf8').lower())
        except SQLObjectNotFound:
            pass

        return None

    def clearRule(self):
        dKeep = {}
        for s in self._aSectionKeys:
            if self.has_key(s):
                dKeep[s] = self[s]
        self.clear()
        for (k,v) in dKeep.items():
            self[k] = v

    def save(self):
        if not (self.has_key('title') and self.has_key('code') \
                and self.has_key('text')):
            return

        if not self.has_key('card'):
            self['card'] = self._findCard(self['title'])

        if self['card'] is None:
            return

        print self['card'].name.encode('ascii','replace')

        oR = IRuling((self['text'],self['code']))

        if self.has_key('url'):
            oR.url = self['url']

        self['card'].addRuling(oR)

# State Base Classes

class StateError(Exception):
    pass

class State(object):
    def __init__(self):
        super(State,self).__init__()
        self._sData = ""

    def transition(self,sTag,dAttr):
        raise NotImplementedError

    def data(self,sData):
        self._sData += sData

class StateWithRule(State):
    def __init__(self,dInfo):
        super(StateWithRule,self).__init__()
        self._dInfo = dInfo

# State Classes

class NoSection(State):
    def transition(self,sTag,dAttr):
        if sTag == 'p':
            return InSection(RuleDict())
        else:
            return self

class InSection(StateWithRule):
    def transition(self,sTag,dAttr):
        if sTag == 'b':
            return SectionTitle(self._dInfo)
        elif sTag == 'p':
            # skip to next section
            return InSection(RuleDict())
        else:
            return NoSection()

class SectionTitle(StateWithRule):
    def transition(self,sTag,dAttr):
        if sTag == 'b':
            raise StateError()
        elif sTag == '/b':
            self._dInfo['title'] = self._sData.strip().strip(':')
            return SectionWithTitle(self._dInfo)
        else:
            return self

class SectionWithTitle(StateWithRule):
    def transition(self,sTag,dAttr):
        if sTag == 'li':
            return SectionRule(self._dInfo)
        elif sTag == 'p':
            # skip to next section
            return InSection(RuleDict())
        elif sTag == '/p':
            return NoSection()
        else:
            return self

class SectionRule(StateWithRule):
    def transition(self,sTag,dAttr):
        if sTag == 'span' and dAttr.get('class') in ['ruling','errata','clarification']:
            return InRuleText(self._dInfo)
        elif sTag == 'a':
            self._dInfo['url'] = dAttr['href']
            return InRuleUrl(self._dInfo)
        elif sTag == '/li':
            if not self._dInfo.has_key('code'):
                self._dInfo['code'] = self._sData.strip()
            self._dInfo.save()
            self._dInfo.clearRule()
            return SectionWithTitle(self._dInfo)
        elif sTag == 'li':
            # handles unclosed <li> inside section block
            # skip to next rule
            if not self._dInfo.has_key('code'):
                self._dInfo['code'] = self._sData.strip()
            self._dInfo.save()
            self._dInfo.clearRule()
            return SectionRule(self._dInfo)
        elif sTag == '/p':
            # handles unclosed <li> at end of section block
            # skip to next section
            if not self._dInfo.has_key('code'):
                self._dInfo['code'] = self._sData.strip()
            self._dInfo.save()
            self._dInfo.clearRule()
            return NoSection()
        return self

class InRuleText(StateWithRule):
    def transition(self,sTag,dAttr):
        if sTag == 'span':
            raise StateError()
        elif sTag == '/span':
            self._dInfo['text'] = self._sData.strip()
            return SectionRule(self._dInfo)
        else:
            return self

class InRuleUrl(StateWithRule):
    def transition(self,sTag,dAttr):
        if sTag == 'a':
            raise StateError()
        elif sTag == '/a':
            self._dInfo['code'] = self._sData.strip()
            return SectionRule(self._dInfo)
        else:
            return self

# Parser

class RulingParser(HTMLParser.HTMLParser,object):
    def reset(self):
        super(RulingParser,self).reset()
        self._state = NoSection()

    def handle_starttag(self,sTag,aAttr):
        self._state = self._state.transition(sTag.lower(),dict(aAttr))

    def handle_endtag(self,sTag):
        self._state = self._state.transition('/'+sTag.lower(),{})

    def handle_data(self,sData):
        self._state.data(sData)

    def handle_charref(self,sName): pass
    def handle_entityref(self,sName): pass
