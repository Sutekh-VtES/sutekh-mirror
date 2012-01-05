# WhiteWolfTextParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# WhiteWolf Parser
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2007, 2011 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Text Parser for extracting cards from the online cardlist.txt."""

import re
import codecs
from sutekh.io.SutekhBaseHTMLParser import LogStateWithInfo
from logging import Logger
from sutekh.core.SutekhObjects import SutekhObjectMaker


def strip_braces(sText):
    """Helper function for searching for keywords. Strip all {} tags from the
       text"""
    return sText.replace('{', '').replace('}', '')


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

    # Usefule regex's
    oDisGaps = re.compile(r'[\\\/{}\&\s]+')
    oWhiteSp = re.compile(r'[{}\s]+')
    oDispCard = re.compile(r'\[[^\]]+\]$')
    oArtistSp = re.compile(r'[&;]')
    # Use regexp lookahead for the last '.', so it can anchor the next match
    # Use non-grouping parentheses so we ca can catch either . or the end of
    # the text
    # Defaults
    oCryptInfoRgx = re.compile(
            '[:\.] ([+-]\d) (bleed|strength|stealth|intercept)(?:(?=\.)|$)')
    dCryptProperties = {
            'black hand': re.compile('Sabbat\. Black Hand'),
            # Seraph has a special case
            'seraph': re.compile('Sabbat\. Black Hand(\.)? Seraph'),
            'infernal': re.compile('[.:] Infernal\.'),
            'red list': re.compile('\. Red List:'),
            'anarch': re.compile('\. Anarch:'),
            'scarce': re.compile('[.:] Scarce.'),
            'sterile': re.compile('[.:] Sterile.'),
            # Need the } to handle some of the errata'd cards
            'blood cursed': re.compile('[.:\}] \(?Blood [Cc]ursed'),
            'not for legal play': re.compile(
                'NOT FOR LEGAL PLAY|Added to the V:EKN banned list'),
            }

    # Properites we check for all library cards
    dLibProperties = {
            'not for legal play': re.compile(
                'NOT FOR LEGAL PLAY|Added to the V:EKN banned list'),
            }

    # Ally properties
    dAllyProperties = {
            # Red list allies are templated differently
            'red list': re.compile('\. Red List\.'),
            }
    oLifeRgx = re.compile('(Unique )?\[?(Gargoyle creature|[A-Za-z]+)\]?'
            ' with (\d) life\.')

    # equipment properties
    dEquipmentProperties = {
            'unique': re.compile('Unique (melee )?weapon|Unique equipment|'
                'represents a unique location'),
            'location': re.compile('represents a (unique )?location'),
            'melee weapon': re.compile('[mM]elee weapon\.'),
            'cold iron': re.compile('weapon\. Cold iron\.'),
            'gun': re.compile('[wW]eapon[:,.] [gG]un\.'),
            'weapon': re.compile('[wW]eapon[:,.] [gG]un\.|[mM]elee weapon\.|'
                'Weapon.|Unique weapon.'),
            'vehicle': re.compile('Vehicle\.'),
            'haven': re.compile('Haven\.'),
            'electronic equipment': re.compile('Electronic equipment.'),
            }

    # master properties
    dMasterProperties = {
            # unique isn't very consistent
            'unique': re.compile('[Uu]nique [mM]aster|Master[:.] unique|'
                'Unique\.'),
            'trifle': re.compile('[mM]aster[:.] .*[tT]rifle'),
            'discipline': re.compile('Master: Discipline\.'),
            'out-of-turn': re.compile('Master: out-of-turn'),
            'location': re.compile('Master[:.] (unique )?[Ll]ocation'),
            'boon': re.compile('Boon\.'),
            'frenzy': re.compile('Frenzy\.'),
            'hunting ground': re.compile('\. Hunting [Gg]round'),
            'haven': re.compile('Haven\.'),
            'trophy': re.compile('Master\. Trophy'),
            'investment': re.compile('Master[.:] (unique )?[Ii]nvestment'),
            'archetype': re.compile('Master: archetype'),
            'watchtower': re.compile('Master: watchtower'),
            'title': re.compile('Title\.'),
            }

    # event properties
    dEventProperties = {
            'gehenna': re.compile('Gehenna\.'),
            'transient': re.compile('Transient\.'),
            'inconnu': re.compile('Inconnu\.'),
            'government': re.compile('Government\.'),
            'inquisition': re.compile('Inquisition\.'),
            }

    # Catch for non-specified card types
    dOtherProperties = {
            'unique': re.compile('Unique\.'),
            'boon': re.compile('Boon\.'),
            'watchtower': re.compile('Watchtower\.'),
            'frenzy': re.compile('Frenzy\.'),
            'title': re.compile('Title\.'),
            }

    # Special cases that aren't handled by the general code
    dAllyKeywordSpecial = {
            'Gypsies': ['1 stealth'],
            'Veneficti (Mage)': ['1 stealth'],
            'High Top': ['1 intercept'],
            'Ghoul Retainer': ['1 strength'],
            }
    # These vampires aren't templated as normal
    dCryptKeywordSpecial = {
            'Spider-Killer': {'stealth': 1},
            'Muaziz, Archon of Ulugh Beg': {'stealth': 1},
            'Rebekka, Chantry Elder of Munich': {'stealth': 1},
            }

    def __init__(self, oLogger):
        super(CardDict, self).__init__()
        self.oLogger = oLogger
        self._oMaker = SutekhObjectMaker()

    def _find_crypt_keywords(self, oCard):
        """Extract the bleed, strength & stealth keywords from the card text"""
        dKeywords = {'bleed': 1, 'strength': 1, 'stealth': 0, 'intercept': 0}
        # Correct special cases
        if self['name'] in self.dCryptKeywordSpecial:
            for sKeyword, iVal in \
                    self.dCryptKeywordSpecial[self['name']].iteritems():
                dKeywords[sKeyword] = iVal
        # Make sure we don't detect merged properties
        sText = strip_braces(self['text'].split('[MERGED]')[0])
        for sNum, sType in self.oCryptInfoRgx.findall(sText):
            dKeywords[sType] += int(sNum)
        for sType, iNum in dKeywords.iteritems():
            self._add_keyword(oCard, '%d %s' % (iNum, sType))
        # Check for "Black Hand", "Infernal", "Red List", "Seraph",
        for sKeyword, oRegexp in self.dCryptProperties.iteritems():
            oMatch = oRegexp.search(sText)
            if oMatch:
                self._add_keyword(oCard, sKeyword)
        # Add Non-Unique keyword
        if 'are not unique' in sText or 'Non-unique' in sText:
            self._add_keyword(oCard, 'non-unique')
        # Imbued are also mortals, so add the keyword
        if self['cardtype'] == 'Imbued':
            self._add_keyword(oCard, 'mortal')

    def _find_lib_life_and_keywords(self, oCard):
        """Extract ally and retainer life and strength & bleed keywords from
           the card text"""
        # Restrict ourselves to text before Superior disciplines
        sText = strip_braces(re.split('\[[A-Z]{3}\]', self['text'])[0])
        # Annoyingly not standardised
        oDetail1Rgx = re.compile('\. (\d strength), (\d bleed)[\.,]')
        oDetail2Rgx = re.compile('\. (\d bleed), (\d strength)[\.,]')
        oMatch = self.oLifeRgx.search(sText)
        if oMatch:
            # Normalise type
            if oMatch.group(1):
                self._add_keyword(oCard, 'unique')
            sType = oMatch.group(2).lower().replace(']', '')
            self._add_keyword(oCard, sType)
            self['life'] = oMatch.group(3)
            oDetail = oDetail1Rgx.search(sText)
            if not oDetail:
                oDetail = oDetail2Rgx.search(sText)
            if oDetail:
                self._add_keyword(oCard, oDetail.group(1))
                self._add_keyword(oCard, oDetail.group(2))
        self._find_card_keywords(oCard, self.dAllyProperties)
        if self['name'] in self.dAllyKeywordSpecial:
            for sKeyword in self.dAllyKeywordSpecial[self['name']]:
                self._add_keyword(oCard, sKeyword)

    def _find_card_keywords(self, oCard, dProps):
        """Find keywords for library cards"""
        sText = strip_braces(self['text'])

        def _do_match(sKeyword, oRegexp):
            """Helper to do the match"""
            oMatch = oRegexp.search(sText)
            if oMatch:
                self._add_keyword(oCard, sKeyword)

        for sKeyword, oRegexp in dProps.iteritems():
            _do_match(sKeyword, oRegexp)
        for sKeyword, oRegexp in self.dLibProperties.iteritems():
            _do_match(sKeyword, oRegexp)

    def _parse_text(self, oCard):
        """Parse the CardText for Sect and Titles"""
        # pylint: disable-msg=R0912
        # Complex set of conditions, so many branches
        sType = None
        if self.has_key('cardtype'):
            sTypes = self['cardtype']
            # Determine if we need to examine the card further based on type
            for sVal in sTypes.split('/'):
                if sVal in ['Vampire', 'Imbued', 'Ally', 'Retainer',
                        'Equipment', 'Master', 'Event']:
                    sType = sVal
        # Check for REFLEX card type
        if self['text'].find(' [REFLEX] ') != -1:
            if self.has_key('cardtype'):
                # append to card types
                self['cardtype'] += '/Reflex'
            else:
                self['cardtype'] = 'Reflex'
        if sType == 'Imbued' or sType == 'Vampire':
            self._find_crypt_keywords(oCard)
        elif sType == 'Ally' or sType == 'Retainer':
            self._find_lib_life_and_keywords(oCard)
        elif sType == 'Equipment':
            self._find_card_keywords(oCard, self.dEquipmentProperties)
        elif sType == 'Master':
            self._find_card_keywords(oCard, self.dMasterProperties)
        elif sType == 'Event':
            self._find_card_keywords(oCard, self.dEventProperties)
        else:
            self._find_card_keywords(oCard, self.dOtherProperties)
        if sType == 'Vampire':
            # Sect attributes: more text. Title is in the attributes
            aLines = strip_braces(self['text']).split(':')
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
        aPairs = [x.split(':') for x in sExp.strip('[]').split(',') if x]
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
        oCard.costtype = str(sType.lower())  # make str non-unicode

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
        oCard.level = str(self._get_level(sLevel))  # make str non-unicode

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

    def _add_keyword(self, oCard, sKeyword):
        """Add the keyword to the card."""
        oKeyword = self._oMaker.make_keyword(sKeyword)
        if oKeyword not in oCard.keywords:
            oCard.addKeyword(oKeyword)

    def _add_artists(self, oCard, sArtists):
        """Add the artist to the card."""
        for sArtist in self.oArtistSp.split(sArtists):
            oArtist = self._oMaker.make_artist(sArtist.strip())
            if oArtist not in oCard.artists:
                oCard.addArtist(oArtist)

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

        if self.has_key('level'):
            self['name'] = self._add_level_to_name(self['name'], self['level'])

        oCard = self._make_card(self['name'])

        self.oLogger.info('Card: %s', self['name'])

        if self.has_key('text'):
            self._parse_text(oCard)

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
            # Also add a keyword for this
            self._add_keyword(oCard, oCard.level)

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
            self._add_keyword(oCard, "burn option")

        if self.has_key('title'):
            self._add_title(oCard, self['title'])

        if self.has_key('sect'):
            self._add_sect(oCard, self['sect'])

        if self.has_key('artist'):
            self._add_artists(oCard, self['artist'])

        if self.has_key('text'):
            oCard.text = self['text'].replace('\r', '')

        self._add_blood_shadowed_court(oCard)

        self._add_physical_cards(oCard)

        oCard.syncUpdate()
        # FIXME: Pass back any error confitions? Missing text, etc.


# Parsing helper functions
def fix_clarification_markers(sLine):
    """Standardise the clarification markers from the text"""
    for sMarker in ['={', '-{']:
        sLine = sLine.replace(sMarker, '{')
    for sMarker in ['}=', '}-']:
        sLine = sLine.replace(sMarker, '}')
    return sLine


# State Classes
class WaitingForCardName(LogStateWithInfo):
    """State when we are not in a card."""

    def transition(self, sLine, _dAttr):
        """Transition to PotentialCard if needed."""
        if sLine.startswith('Name:'):
            self.flush()
            sData = sLine.split(':', 1)[1]
            self._dInfo['name'] = sData.strip()
            return InExpansion(self._dInfo, self.oLogger)
        elif sLine.strip():
            if self._dInfo.has_key('name') and not self._dInfo.has_key('text'):
                # We've it a blank line in the middle of a card, so bounce
                # back to InCard stuff
                oCard = InCard(self._dInfo, self.oLogger)
                return oCard.transition(sLine, None)
        return self

    def flush(self):
        """Save any existing card and clear out dInfo"""
        if self._dInfo.has_key('name'):
            # Ensure we've saved existing card
            self._dInfo.save()
        self._dInfo = CardDict(self.oLogger)


class InCard(LogStateWithInfo):
    """State when we are in a card, waiting for the card text."""

    # These look like they start a key: value pair, but actually start
    # card text

    aTextTags = [
            'master',
            'camarilla',
            'sabbat',
            'laibon',
            'independent',
            'strike',
            'weapon',
            ]

    def transition(self, sLine, _dAttr):
        oCardText = None
        if ':' in sLine:
            sTag = fix_clarification_markers(sLine.split(':', 1)[0].lower())
            if sTag in self.aTextTags or ' ' in sTag or '{' in sTag:
                oCardText = InCardText(self._dInfo, self.oLogger)
            else:
                sData = fix_clarification_markers(sLine.split(':', 1)[1])
                # We don't want clarification markers here
                sData = sData.replace('{', '').replace('}', '')
                self._dInfo[sTag] = sData.strip()
        elif not sLine.strip():
            # Empty line, so probably end of the card
            return WaitingForCardName(self._dInfo, self.oLogger)
        else:
            if sLine.strip().lower() == 'burn option':
                # Annoying special case
                self._dInfo['burn option'] = None
            else:
                oCardText = InCardText(self._dInfo, self.oLogger)
        if oCardText:
            # Hand over the line to the card text parser
            return oCardText.transition(sLine, None)
        else:
            return self


class InExpansion(LogStateWithInfo):
    """In the expansions section."""

    def transition(self, sLine, _dAttr):
        """Transition back to InCard if needed."""
        if sLine.startswith('[') and sLine.strip().endswith(']'):
            self._dInfo['expansion'] = sLine.strip()
            return InCard(self._dInfo, self.oLogger)
        else:
            return self


class InCardText(LogStateWithInfo):
    """In the card text section."""

    def transition(self, sLine, _dAttr):
        """Transition back to InCard if needed."""
        if sLine.startswith('Artist:') or not sLine.strip():
            self._dInfo['text'] = fix_clarification_markers(
                    self._dInfo['text'].strip())
            oInCard = InCard(self._dInfo, self.oLogger)
            return oInCard.transition(sLine, None)
        else:
            if not self._dInfo.has_key('text'):
                self._dInfo['text'] = sLine.strip() + '\n'
            else:
                # Since we're building this up a line at a time, we add a
                # trailing space, which we strip before we exit this parser
                self._dInfo['text'] += sLine.strip() + ' '
            return self


# Parser
class WhiteWolfTextParser(object):
    """Actual Parser for the WW cardlist text file(s)."""

    def __init__(self, oLogHandler):
        self.oLogger = Logger('White wolf card parser')
        if oLogHandler is not None:
            self.oLogger.addHandler(oLogHandler)
        self._oState = None
        self.reset()

    def reset(self):
        """Reset the parser"""
        self._oState = WaitingForCardName({}, self.oLogger)

    def parse(self, fIn):
        """Feed lines to the state machine"""
        for sLine in fIn:
            self.feed(sLine)
        # Ensure we flush any open card text states
        self.feed('')
        if hasattr(self._oState, 'flush'):
            self._oState.flush()
        else:
            raise IOError('Failed to parse card list - '
                    'unexpected state at end of file.\n'
                    'Card list probably truncated.')

    def feed(self, sLine):
        """Feed the line to the current state"""
        # Strip BOM from line start
        sLine = sLine.decode('utf8').lstrip(u'\ufeff')
        self._oState = self._oState.transition(sLine, None)
