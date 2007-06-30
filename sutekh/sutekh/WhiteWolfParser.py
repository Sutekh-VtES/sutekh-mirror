# WhiteWolfParser.py
# WhiteWolf Parser
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import HTMLParser, re
from sutekh.SutekhObjects import IAbstractCard, IClan, IRarityPair,\
                                 IDisciplinePair, IVirtue, ICreed, ICardType,\
                                 ISect, ITitle

# Card Saver

class CardDict(dict):
    oDisGaps = re.compile(r'[\\\/{}\&\s]+')
    oWhiteSp = re.compile(r'[{}\s]+')
    oDispCard = re.compile(r'\[[^\]]+\]$')

    def __init__(self):
        super(CardDict,self).__init__()

    def _makeCard(self,sName):
        sName = self.oDispCard.sub('',sName)
        sName = sName.strip()
        return IAbstractCard(sName)

    def _addExpansions(self,oCard,sExp):
        aPairs = [x.split(':') for x in sExp.strip('[]').split(',')]
        aExp = []
        for aPair in aPairs:
            if len(aPair) == 1:
                aExp.append((aPair[0].strip(),'NA'))
            else:
                aExp.append((aPair[0].strip(),aPair[1].strip()))

        for sExp, sRarSet in aExp:
            for sRar in sRarSet.split('/'):
                oP = IRarityPair((sExp,sRar))
                oCard.addRarityPair(oP)

    def _addDisciplines(self,oCard,sDis):
        sDis = self.oDisGaps.sub(' ',sDis).strip()

        if sDis == '-none-' or sDis == '': return

        for s in sDis.split():
            if s==s.lower():
               oP = IDisciplinePair((s,'inferior'))
            else:
               oP = IDisciplinePair((s,'superior'))
            oCard.addDisciplinePair(oP)

    def _addVirtues(self,oCard,sVir):
        sVir = self.oDisGaps.sub(' ',sVir).strip()

        if sVir == '-none-' or sVir == '': return

        for s in sVir.split():
            oP = IVirtue(s)
            oCard.addVirtue(oP)

    def _addCreeds(self,oCard,sCreed):
        sCreed = self.oWhiteSp.sub(' ',sCreed).strip()

        if sCreed == '-none-' or sCreed == '': return

        for s in sCreed.split('/'):
            oCard.addCreed(ICreed(s.strip()))

    def _addClans(self,oCard,sClan):
        sClan = self.oWhiteSp.sub(' ',sClan).strip()

        if sClan == '-none-' or sClan == '': return

        for s in sClan.split('/'):
            oCard.addClan(IClan(s.strip()))

    def _addCost(self,oCard,sCost):
        sCost = self.oWhiteSp.sub(' ',sCost).strip()
        sAmnt, sType = sCost.split()

        if sAmnt.lower() == 'x':
            iCost = -1
        else:
            iCost = int(sAmnt,10)

        oCard.cost = iCost
        oCard.costtype = str(sType.lower()) # make str non-unicode

    def _addLife(self,oCard,sLife):
        sLife = self.oWhiteSp.sub(' ',sLife).strip()
        aLife=sLife.split()

        try:
            oCard.life=int(aLife[0],10)
        except ValueError:
            pass

    def _getLevel(self,sLevel):
        return self.oWhiteSp.sub(' ',sLevel).strip().lower()

    def _addLevel(self,oCard,sLevel):
        oCard.level = str(self._getLevel(sLevel)) # make str non-unicode

    def _addLevelToName(self,sName,sLevel):
        return sName.strip() + " (" + self._getLevel(sLevel).capitalize() + ")"

    def _addCapacity(self,oCard,sCap):
        sCap = self.oWhiteSp.sub(' ',sCap).strip()
        aCap = sCap.split()
        try:
            oCard.capacity = int(aCap[0],10)
        except ValueError:
            pass

    def _addCardType(self,oCard,sTypes):
        for s in sTypes.split('/'):
            oCard.addCardType(ICardType(s.strip()))

    def save(self):
        if not self.has_key('name'):
            return

        if self.has_key('level'):
            self['name'] = self._addLevelToName(self['name'],self['level'])

        print self['name'].encode('ascii','xmlcharrefreplace')

        oCard = self._makeCard(self['name'])
        if self.has_key('group'):
            oCard.group = int(self.oWhiteSp.sub('',self['group']),10)

        if self.has_key('capacity'):
            self._addCapacity(oCard,self['capacity'])

        if self.has_key('cost'):
            self._addCost(oCard,self['cost'])

        if self.has_key('life'):
            self._addLife(oCard,self['life'])

        if self.has_key('level'):
            self._addLevel(oCard,self['level'])

        if self.has_key('expansion'):
            self._addExpansions(oCard,self['expansion'])

        if self.has_key('discipline'):
            self._addDisciplines(oCard,self['discipline'])

        if self.has_key('virtue'):
            self._addVirtues(oCard,self['virtue'])

        if self.has_key('clan'):
            self._addClans(oCard,self['clan'])

        if self.has_key('creed'):
            self._addCreeds(oCard,self['creed'])

        if self.has_key('cardtype'):
            self._addCardType(oCard,self['cardtype'])
        if self.has_key('text'):
            oCard.text = self['text']
            (sSect,sTitle)=parseText(oCard)
            if sSect is not None:
                oCard.addSect(ISect(sSect))
            if sTitle is not None:
                oCard.addTitle(ITitle(sTitle))

        oCard.syncUpdate()

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

class StateWithCard(State):
    def __init__(self,dInfo):
        super(StateWithCard,self).__init__()
        self._dInfo = dInfo

# State Classes

class NoCardard(State):
    def transition(self,sTag,dAttr):
        if sTag == 'p':
            return PotentialCard()
        else:
            return self

class PotentialCard(State):
    def transition(self,sTag,dAttr):
        if sTag == 'a' and dAttr.has_key('name'):
            return InCard(CardDict())
        else:
            return NoCardard()

class InCard(StateWithCard):
    def transition(self,sTag,dAttr):
        if sTag == 'p':
            raise StateError()
        elif sTag == '/p':
            self._dInfo.save()
            return NoCardard()
        elif sTag == 'span' and dAttr.get('class') == 'cardname':
            return InCardName(self._dInfo)
        elif sTag == 'span' and dAttr.get('class') == 'exp':
            return InExpansion(self._dInfo)
        elif sTag == 'span' and dAttr.get('class') == 'key':
            return InKeyValue(self._dInfo)
        elif sTag == 'td' and dAttr.get('colspan') == '2':
            return InCardText(self._dInfo)
        else:
            return self

class InCardName(StateWithCard):
    def transition(self,sTag,dAttr):
        if sTag == '/span':
            self._dInfo['name'] = self._sData.strip()
            return InCard(self._dInfo)
        elif sTag == 'span':
            raise StateError()
        else:
            return self

class InExpansion(StateWithCard):
    def transition(self,sTag,dAttr):
        if sTag == '/span':
            self._dInfo['expansion'] = self._sData.strip()
            return InCard(self._dInfo)
        elif sTag == 'span':
            raise StateError()
        else:
            return self

class InCardText(StateWithCard):
    def transition(self,sTag,dAttr):
        if sTag == '/td' or sTag == 'tr' or sTag == '/tr' or sTag == '/table':
            self._dInfo['text'] = self._sData.strip()
            return InCard(self._dInfo)
        elif sTag == 'td':
            raise StateError()
        else:
            return self

class InKeyValue(StateWithCard):
    def transition(self,sTag,dAttr):
        if sTag == '/span':
            sKey = self._sData.strip().strip(':').lower()
            return WaitingForValue(sKey,self._dInfo)
        elif sTag == 'span':
            raise StateError()
        else:
            return self

class WaitingForValue(StateWithCard):
    def __init__(self,sKey,dInfo):
        super(WaitingForValue,self).__init__(dInfo)
        self._sKey = sKey
        self._bGotTd = False

    def transition(self,sTag,dAttr):
        if sTag == 'td':
            self._sData = ""
            self._bGotTd = True
            return self
        elif sTag == '/td' and self._bGotTd:
            self._dInfo[self._sKey] = self._sData.strip()
            return InCard(self._dInfo)
        elif sTag == '/tr':
            self._dInfo[self._sKey] = None
            return InCard(self._dInfo)
        elif sTag == 'tr':
            raise StateError()
        else:
            return self

# Parser

class WhiteWolfParser(HTMLParser.HTMLParser,object):
    def reset(self):
        super(WhiteWolfParser,self).reset()
        self._state = NoCardard()

    def handle_starttag(self,sTag,aAttr):
        self._state = self._state.transition(sTag.lower(),dict(aAttr))

    def handle_endtag(self,sTag):
        self._state = self._state.transition('/'+sTag.lower(),{})

    def handle_data(self,sData):
        self._state.data(sData)

    def handle_charref(self,sName): pass
    def handle_entityref(self,sName): pass

# We define this as a seperate function, so it can also be used by
# the database upgrade stuff
# Can't define it in SutkehUtility because of the circular dependancy
# on WhiteWolfParser that arise
# Prepares I need a global functions file as well

def parseText(oCard):
    """Parse the CardText for Sect and Titles"""
    oType=oCard.cardtype
    sTitle=None
    sSect=None
    if oType[0].name != 'Vampire':
        return (None,None)
    aLines=oCard.text.splitlines()
    if aLines[0].find('Camarilla')!=-1:
        sSect='Camarilla'
        if aLines[0].find('primogen')!=-1:
            sTitle='Primogen'
        elif aLines[0].find('Prince of')!=-1:
            sTitle='Prince'
        elif aLines[0].find('Justicar')!=-1:
            sTitle='Justicar'
        elif aLines[0].find('Inner Circle')!=-1:
            sTitle='Inner Circle'
    elif aLines[0].find('Sabbat')!=-1:
        sSect='Sabbat'
        if aLines[0].find('bishop')!=-1:
            sTitle='Bishop'
        elif aLines[0].find('Archbishop of')!=-1:
            sTitle='Archbishop'
        elif aLines[0].find('priscus')!=-1:
            sTitle='Priscus'
        elif aLines[0].find('cardinal')!=-1:
            sTitle='Cardinal'
        elif aLines[0].find('regent')!=-1:
            sTitle='Regent'
    elif aLines[0].find('Independent')!=-1:
        sSect='Independent'
        # Independent titles are on the next line. Of the form
        # Name has X vote(s)
        try:
            if aLines[1].find('has 1 vote')!=-1:
                sTitle='Independent with 1 vote'
            elif aLines[1].find('has 2 votes')!=-1:
                sTitle='Independent with 2 votes'
            elif aLines[1].find('has 3 votes')!=-1:
                sTitle='Independent with 3 votes'
        except IndexError:
            pass
    elif aLines[0].find('Laibon')!=-1:
        sSect='Laibon'
        if aLines[0].find('magaji')!=-1:
            sTitle='Magaji'
    return (sSect,sTitle)
