# WhiteWolfParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# WhiteWolf Parser
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""HTML Parser for extracting cards from the WW online cardlist."""

import HTMLParser, re
from logging import Logger
from sutekh.core.SutekhObjects import SutekhObjectMaker

# Card Saver

def _find_sect_and_title(aLines):
    """Search the first 2 lines of the card text for sect & title
       information.

       This is potentially brittle, since it had to rely on WW's
       standard text layout.
       """
    # pylint: disable-msg=R0912, R0915
    # R0912: Need to consider all the cases here
    # R0915: This is thus a long function
    # Card text for vampires is either Sect attributes. or Sect.
    sSect = None
    sTitle = None
    if aLines[0].find('Camarilla') != -1:
        sSect = 'Camarilla'
        if aLines[0].find('Camarilla primogen') != -1:
            sTitle = 'Primogen'
        elif aLines[0].find('Camarilla Prince of') != -1:
            sTitle = 'Prince'
        elif aLines[0].find('Justicar') != -1:
            # Since Justicar titles are of the form
            # 'Camarilla <Clan> Justicar'
            oJusticar = re.compile('Camarilla [A-Z][a-z]* Justicar')
            if oJusticar.search(aLines[0]) is not None:
                sTitle = 'Justicar'
        # Inner circle my be either Camariila Inner Circle or
        # Camarilla Clan Inner Circle
        # Hopefully this will go away sometime
        elif aLines[0].find('Inner Circle') != -1:
            if aLines[0].find('Camarilla Inner Circle') != -1:
                sTitle = 'Inner Circle'
            else:
                oInnerCircle = re.compile('Camarilla [A-Z][a-z]* Inner Circle')
                if oInnerCircle.search(aLines[0]) is not None:
                    sTitle = 'Inner Circle'
    elif aLines[0].find('Sabbat') != -1:
        sSect = 'Sabbat'
        if aLines[0].find('Sabbat Archbishop of') != -1:
            sTitle = 'Archbishop'
        elif aLines[0].find('Sabbat bishop') != -1:
            sTitle = 'Bishop'
        elif aLines[0].find('Sabbat priscus') != -1:
            sTitle = 'Priscus'
        elif aLines[0].find('Sabbat cardinal') != -1:
            sTitle = 'Cardinal'
        elif aLines[0].find('Sabbat regent') != -1:
            sTitle = 'Regent'
    elif aLines[0].find('Independent') != -1:
        sSect = 'Independent'
        # Independent titles are on the next line. Of the form
        # 'Name has X vote(s)'
        # pylint: disable-msg=W0704
        # error isn't fatal, so ignoring it is fine
        try:
            # Special cases 'The Baron' and 'Ur-Shulgi' mean we don't
            # anchor the regexp
            oIndTitle = re.compile('[A-Z][a-z]* has ([0-9]) vote')
            oMatch = oIndTitle.search(aLines[1])
            if oMatch is not None and not aLines[1].startswith('[MERGED]'):
                oMergedTitle = re.compile('MERGED.*has ([0-9]) vote')
                oMergedMatch = oMergedTitle.search(aLines[1])
                if oMergedMatch is not None and oMergedMatch.groups()[0] == \
                        oMatch.groups()[0]:
                    pass
                elif oMatch.groups()[0] == '1':
                    sTitle = 'Independent with 1 vote'
                elif oMatch.groups()[0] == '2':
                    sTitle = 'Independent with 2 votes'
                elif oMatch.groups()[0] == '3':
                    sTitle = 'Independent with 3 votes'
        except IndexError:
            pass
    elif aLines[0].find('Laibon') != -1:
        sSect = 'Laibon'
        if aLines[0].find('Laibon magaji') != -1:
            sTitle = 'Magaji'
    return sSect, sTitle

class CardDict(dict):
    """Dictionary object which holds the extracted card info."""
    oDisGaps = re.compile(r'[\\\/{}\&\s]+')
    oWhiteSp = re.compile(r'[{}\s]+')
    oDispCard = re.compile(r'\[[^\]]+\]$')

    def __init__(self, oLogger):
        super(CardDict, self).__init__()
        self.oLogger = oLogger
        self._oMaker = SutekhObjectMaker()

    def _parse_text(self):
        """Parse the CardText for Sect and Titles"""
        sType = None
        if self.has_key('cardtype'):
            sTypes = self['cardtype']
            # Determine if vampire is one of the card types
            for sVal in sTypes.split('/'):
                if sVal == 'Vampire':
                    sType = sVal
        # Check for REFLEX card type
        if self['text'].find(' [REFLEX] ') != -1:
            if self.has_key('cardtype'):
                # append to card types
                self['cardtype'] += '/Reflex'
            else:
                self['cardtype'] = 'Reflex'
        if sType == 'Vampire':
            # Sect attributes: more text. Title is in the attributes
            aLines = self['text'].split(':')
            sSect, sTitle = _find_sect_and_title(aLines)
            # check if the vampire has flight (text ends has Flight [FLIGHT].)
            oFlightRexegp = re.compile('Flight \[FLIGHT\]\.')
            oMatch = oFlightRexegp.search(aLines[-1])
            if oMatch:
                if self.has_key('discipline'):
                    self['discipline'] += ' FLI'
                else:
                    self['discipline'] = 'FLI'
            if sSect is not None:
                self['sect'] = sSect
            if sTitle is not None:
                self['title'] = sTitle

    def _add_blood_shadowed_court(self, oCard):
        """Add Blood Shadowed Court to the expansion list if appropriate."""
        oCamVampPair = self._oMaker.make_rarity_pair('CE', 'Vampire')
        if oCamVampPair in oCard.rarity:
            oPair = self._oMaker.make_rarity_pair('BSC', 'BSC')
            if oPair not in oCard.rarity:
                # Don't duplicate entries
                oCard.addRarityPair(oPair)

    def _make_card(self, sName):
        """Create the abstract card in the database."""
        sName = self.oDispCard.sub('', sName)
        return self._oMaker.make_abstract_card(sName)

    def _add_expansions(self, oCard, sExp):
        """Add expansion information to the card, creating expansion pairs
           as needed."""
        aPairs = [x.split(':') for x in sExp.strip('[]').split(',')]
        aExp = []
        for aPair in aPairs:
            if len(aPair) == 1:
                aExp.append((aPair[0].strip(), 'NA'))
            elif aPair[1].strip().startswith('Promo-'):
                # Handle the TR:Promo special case
                aExp.append((aPair[1].strip(), 'NA'))
            else:
                aExp.append((aPair[0].strip(), aPair[1].strip()))

        for sExp, sRarSet in aExp:
            for sRar in sRarSet.split('/'):
                oPair = self._oMaker.make_rarity_pair(sExp, sRar)
                if oPair not in oCard.rarity:
                    oCard.addRarityPair(oPair)

    def _add_disciplines(self, oCard, sDis):
        """Add the list of disciplines to the card, creating discipline
           pairs as needed."""
        sDis = self.oDisGaps.sub(' ', sDis).strip()

        if sDis == '-none-' or sDis == '':
            return

        for sVal in sDis.split():
            if  sVal == sVal.lower():
                oPair = self._oMaker.make_discipline_pair(sVal, 'inferior')
            else:
                oPair = self._oMaker.make_discipline_pair(sVal, 'superior')
            if oPair not in oCard.discipline:
                oCard.addDisciplinePair(oPair)

    def _add_virtues(self, oCard, sVir):
        """Add the list of virtues to the card."""
        sVir = self.oDisGaps.sub(' ', sVir).strip()

        if sVir == '-none-' or sVir == '':
            return

        for sVal in sVir.split():
            oVirt = self._oMaker.make_virtue(sVal)
            if oVirt not in oCard.virtue:
                oCard.addVirtue(oVirt)

    def _add_creeds(self, oCard, sCreed):
        """Add creeds to the card."""
        sCreed = self.oWhiteSp.sub(' ', sCreed).strip()

        if sCreed == '-none-' or sCreed == '':
            return

        for sVal in sCreed.split('/'):
            oCreed = self._oMaker.make_creed(sVal.strip())
            if oCreed not in oCard.creed:
                oCard.addCreed(oCreed)

    def _add_clans(self, oCard, sClan):
        """Add clans to the card."""
        sClan = self.oWhiteSp.sub(' ', sClan).strip()

        if sClan == '-none-' or sClan == '':
            return

        for sVal in sClan.split('/'):
            oClan = self._oMaker.make_clan(sVal.strip())
            if oClan not in oCard.clan:
                oCard.addClan(oClan)

    def _add_cost(self, oCard, sCost):
        """Add the cost to the card, replace 'X' with -1."""
        sCost = self.oWhiteSp.sub(' ', sCost).strip()
        sAmnt, sType = sCost.split()

        if sAmnt.lower() == 'x':
            iCost = -1
        else:
            iCost = int(sAmnt, 10)

        oCard.cost = iCost
        oCard.costtype = str(sType.lower()) # make str non-unicode

    def _add_group(self, oCard, sGroup):
        """Add the group to the card. Replace '*' with -1."""
        sGroup = self.oWhiteSp.sub(' ', sGroup).strip()

        if sGroup == '*':
            iGroup = -1
        else:
            iGroup = int(sGroup, 10)

        oCard.group = iGroup

    def _add_life(self, oCard, sLife):
        """Add the life to the card."""
        sLife = self.oWhiteSp.sub(' ', sLife).strip()
        aLife = sLife.split()
        # pylint: disable-msg=W0704
        # ignoring the error is the right thing here
        try:
            oCard.life = int(aLife[0], 10)
        except ValueError:
            pass

    def _get_level(self, sLevel):
        """Normalised the level string."""
        return self.oWhiteSp.sub(' ', sLevel).strip().lower()

    def _add_level(self, oCard, sLevel):
        """Add the correct string for the level to the card."""
        oCard.level = str(self._get_level(sLevel)) # make str non-unicode

    def _add_level_to_name(self, sName, sLevel):
        """Add level info to the vampire name."""
        return sName.strip() + " (%s)" % self._get_level(sLevel).capitalize()

    def _add_capacity(self, oCard, sCap):
        """Add the capacity to the card."""
        sCap = self.oWhiteSp.sub(' ', sCap).strip()
        aCap = sCap.split()
        # pylint: disable-msg=W0704
        # ignoring the error is the right thing here
        try:
            oCard.capacity = int(aCap[0], 10)
        except ValueError:
            pass

    def _add_card_type(self, oCard, sTypes):
        """Add the card type info to the card."""
        for sVal in sTypes.split('/'):
            oType = self._oMaker.make_card_type(sVal.strip())
            if oType not in oCard.cardtype:
                oCard.addCardType(oType)

    def _add_title(self, oCard, sTitle):
        """Add the title to the card."""
        oTitle = self._oMaker.make_title(sTitle)
        if oTitle not in oCard.title:
            oCard.addTitle(oTitle)

    def _add_sect(self, oCard, sSect):
        """Add the sect to the card."""
        oSect = self._oMaker.make_sect(sSect)
        if oSect not in oCard.sect:
            oCard.addSect(oSect)

    def _add_physical_cards(self, oCard):
        """Create a physical card for each expansion."""
        self._oMaker.make_physical_card(oCard, None)
        for oExp in set([oRarity.expansion for oRarity in oCard.rarity]):
            self._oMaker.make_physical_card(oCard, oExp)

    def save(self):
        # pylint: disable-msg=R0912
        # Need to consider all cases, so many branches
        """Commit the card to the database.

           This fills in the needed fields and creates entries in the join
           tables as needed.
           """
        if not self.has_key('name'):
            return

        if self.has_key('text'):
            self._parse_text()

        if self.has_key('level'):
            self['name'] = self._add_level_to_name(self['name'], self['level'])

        self.oLogger.info('Card: %s', self['name'])

        oCard = self._make_card(self['name'])
        if self.has_key('group'):
            self._add_group(oCard, self['group'])

        if self.has_key('capacity'):
            self._add_capacity(oCard, self['capacity'])

        if self.has_key('cost'):
            self._add_cost(oCard, self['cost'])

        if self.has_key('life'):
            self._add_life(oCard, self['life'])

        if self.has_key('level'):
            self._add_level(oCard, self['level'])

        if self.has_key('expansion'):
            self._add_expansions(oCard, self['expansion'])

        if self.has_key('discipline'):
            self._add_disciplines(oCard, self['discipline'])

        if self.has_key('virtue'):
            self._add_virtues(oCard, self['virtue'])

        if self.has_key('clan'):
            self._add_clans(oCard, self['clan'])

        if self.has_key('creed'):
            self._add_creeds(oCard, self['creed'])

        if self.has_key('cardtype'):
            self._add_card_type(oCard, self['cardtype'])

        if self.has_key('burn option'):
            oCard.burnoption = True

        if self.has_key('title'):
            self._add_title(oCard, self['title'])

        if self.has_key('sect'):
            self._add_sect(oCard, self['sect'])

        if self.has_key('text'):
            oCard.text = self['text'].replace('\r', '')

        self._add_blood_shadowed_court(oCard)

        self._add_physical_cards(oCard)

        oCard.syncUpdate()

# State Base Classes

class StateError(Exception):
    """Error case in the state true"""
    pass

class State(object):
    """Base class for the State transitions."""
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

class StateWithCard(State):
    """Base class for state transitions when already in a card."""
    # pylint: disable-msg=W0223
    # descendants will override transition, so still abstract here.
    def __init__(self, dInfo, oLogger):
        super(StateWithCard, self).__init__(oLogger)
        self._dInfo = dInfo

# State Classes

class NoCard(State):
    """State when we are not in a card."""
    # pylint: disable-msg=W0613
    # dAttr required by function signature
    def transition(self, sTag, dAttr):
        """Transition to PotentialCard if needed."""
        if sTag == 'p':
            return PotentialCard(self.oLogger)
        else:
            return self

class PotentialCard(State):
    """State for a section that may be a card"""
    def transition(self, sTag, dAttr):
        """Transition to InCard or NoCard if needed."""
        if sTag == 'a' and dAttr.has_key('name'):
            return InCard(CardDict(self.oLogger), self.oLogger)
        else:
            return NoCard(self.oLogger)

class InCard(StateWithCard):
    """State for in a card description in the WW card list."""
    # pylint: disable-msg=W0613
    # dAttr required by function signature
    def transition(self, sTag, dAttr):
        """Transistion to the appropriate section state if needed."""
        if sTag == 'p':
            raise StateError()
        elif sTag == '/p':
            self._dInfo.save()
            return NoCard(self.oLogger)
        elif sTag == 'span' and dAttr.get('class') == 'cardname':
            return InCardName(self._dInfo, self.oLogger)
        elif sTag == 'span' and dAttr.get('class') == 'exp':
            return InExpansion(self._dInfo, self.oLogger)
        elif sTag == 'span' and dAttr.get('class') == 'key':
            return InKeyValue(self._dInfo, self.oLogger)
        elif sTag == 'td' and dAttr.get('colspan') == '2':
            return InCardText(self._dInfo, self.oLogger)
        else:
            return self

class InCardName(StateWithCard):
    """In the card name section."""
    # pylint: disable-msg=W0613
    # dAttr required by function signature
    def transition(self, sTag, dAttr):
        """Transistion back to InCard if needed."""
        if sTag == '/span':
            self._dInfo['name'] = self._sData.strip()
            return InCard(self._dInfo, self.oLogger)
        elif sTag == 'span':
            raise StateError()
        else:
            return self

class InExpansion(StateWithCard):
    """In the expansions section."""
    # pylint: disable-msg=W0613
    # dAttr required by function signature
    def transition(self, sTag, dAttr):
        """Transistion back to InCard if needed."""
        if sTag == '/span':
            self._dInfo['expansion'] = self._sData.strip()
            return InCard(self._dInfo, self.oLogger)
        elif sTag == 'span':
            raise StateError()
        else:
            return self

class InCardText(StateWithCard):
    """In the card text section."""
    # pylint: disable-msg=W0613
    # dAttr required by function signature
    def transition(self, sTag, dAttr):
        """Transistion back to InCard if needed."""
        if sTag == '/td' or sTag == 'tr' or sTag == '/tr' or sTag == '/table':
            self._dInfo['text'] = self._sData.strip()
            return InCard(self._dInfo, self.oLogger)
        elif sTag == 'td':
            raise StateError()
        else:
            return self

class InKeyValue(StateWithCard):
    """Extract a dictionary key from the table holding the card info."""
    # pylint: disable-msg=W0613
    # dAttr required by function signature
    def transition(self, sTag, dAttr):
        """Transition to WaitingForValue if needed."""
        if sTag == '/span':
            sKey = self._sData.strip().strip(':').lower()
            return WaitingForValue(sKey, self._dInfo, self.oLogger)
        elif sTag == 'span':
            raise StateError()
        else:
            return self

class WaitingForValue(StateWithCard):
    """Extract a value from the table holding the card info."""
    def __init__(self, sKey, dInfo, oLogHandler):
        super(WaitingForValue, self).__init__(dInfo, oLogHandler)
        self._sKey = sKey
        self._bGotTd = False

    # pylint: disable-msg=W0613
    # dAttr required by function signature
    def transition(self, sTag, dAttr):
        """Transition back to InCard if needed."""
        if sTag == 'td':
            self._sData = ""
            self._bGotTd = True
            return self
        elif sTag == '/td' and self._bGotTd:
            self._dInfo[self._sKey] = self._sData.strip()
            return InCard(self._dInfo, self.oLogger)
        elif sTag == '/tr':
            self._dInfo[self._sKey] = None
            return InCard(self._dInfo, self.oLogger)
        elif sTag == 'tr':
            raise StateError()
        else:
            return self

# Parser

class WhiteWolfParser(HTMLParser.HTMLParser, object):
    """Actual Parser for the WW cardlist HTML file(s)."""
    def __init__(self, oLogHandler):
        # super().__init__ calls reset, so we need this first
        self.oLogger = Logger('White wolf card parser')
        if oLogHandler is not None:
            self.oLogger.addHandler(oLogHandler)
        super(WhiteWolfParser, self).__init__()
        self._oState = NoCard(self.oLogger)

    # pylint: disable-msg=C0111
    # names are as listed in HTMLParser docs, so no need for docstrings
    def reset(self):
        super(WhiteWolfParser, self).reset()
        self._oState = NoCard(self.oLogger)

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


