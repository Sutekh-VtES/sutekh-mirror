# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# WhiteWolf Parser
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2007, 2011 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Text Parser for extracting cards from the online cardlist.txt."""

import datetime
import re
from logging import Logger

from sutekh.base.io.SutekhBaseHTMLParser import LogStateWithInfo

from sutekh.base.core.DBUtility import CARDLIST_UPDATE_DATE, set_metadata_date

from sutekh.core.SutekhObjectMaker import SutekhObjectMaker
from sutekh.base.Utility import move_articles_to_front

BC_RARITIES = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6',
               'B1', 'B2', 'B3', 'B4', 'B5', 'B6']


def strip_braces(sText):
    """Helper function for searching for keywords. Strip all {} tags from the
       text"""
    # We also strip the trailing ' ()' left over from the tweaks to
    # the text of cost-reducing vampires
    return sText.replace('{', '').replace('}', '').replace(' ()', '')


# Card Saver
def _find_sect_and_title(aLines):
    """Search the first 2 lines of the card text for sect & title
       information.

       This is potentially brittle, since it had to rely on WW's
       standard text layout.
       """
    # pylint: disable=too-many-branches, too-many-statements
    # Need to consider all the cases here
    # this is thus a long function
    # Card text for vampires is either Sect attributes. or Sect.
    sSect = None
    sTitle = None
    # We access this a fair amount, hence the local cache
    sLowerLine = aLines[0].lower()
    if aLines[0].find('Camarilla') != -1:
        sSect = 'Camarilla'
        if sLowerLine.find('camarilla primogen') != -1:
            sTitle = 'Primogen'
        elif sLowerLine.find('camarilla prince of') != -1:
            sTitle = 'Prince'
        elif sLowerLine.find('justicar') != -1:
            # Since Justicar titles are of the form
            # 'Camarilla <Clan> Justicar'
            oJusticar = re.compile(r'Camarilla [A-Z][a-z]* Justicar')
            if oJusticar.search(aLines[0]) is not None:
                sTitle = 'Justicar'
        # Inner circle my be either Camariila Inner Circle or
        # Camarilla Clan Inner Circle
        # Hopefully this will go away sometime
        elif sLowerLine.find('inner circle') != -1:
            if sLowerLine.find('camarilla inner circle') != -1:
                sTitle = 'Inner Circle'
            else:
                oInnerCircle = re.compile(
                    r'Camarilla [A-Z][a-z]* Inner Circle')
                if oInnerCircle.search(aLines[0]) is not None:
                    sTitle = 'Inner Circle'
    elif aLines[0].find('Sabbat') != -1:
        sSect = 'Sabbat'
        if sLowerLine.find('sabbat archbishop of') != -1:
            sTitle = 'Archbishop'
        elif sLowerLine.find('sabbat bishop') != -1:
            sTitle = 'Bishop'
        elif sLowerLine.find('sabbat priscus') != -1:
            sTitle = 'Priscus'
        elif sLowerLine.find('sabbat cardinal') != -1:
            sTitle = 'Cardinal'
        elif sLowerLine.find('sabbat regent') != -1:
            sTitle = 'Regent'
    elif aLines[0].find('Anarch') != -1 or \
            aLines[0].find('Independent anarch') != -1:
        # We must do this before the Independent sect check, due to existence
        # of 'Independent Anarch' lines in the file.
        sSect = 'Anarch'
        # also check for Baron title
        try:
            oBaronTitle = re.compile(r'[aA]narch Baron of')
            oMatch = oBaronTitle.search(aLines[0])
            if oMatch is not None:
                sTitle = 'Baron'
        except IndexError:
            pass
    elif aLines[0].find('Independent') != -1:
        sSect = 'Independent'
        # Independent titles are on the next line. Of the form
        # 'Name has X vote(s)'
        # Templating change with the Unaligned. Now Independent. X vote(s).
        try:
            # Special cases 'The Baron' and 'Ur-Shulgi' mean we don't
            # anchor the regexp
            oIndTitle = re.compile(r'[A-Z][a-z]* has ([0-9]) vote')
            oMatch = oIndTitle.search(aLines[1])
            oIndTitle_new = re.compile(r'Independent. ([0-9]) vote')
            oMatch_new = oIndTitle_new.search(aLines[0])
            sVotes = ''
            if oMatch is not None and not aLines[1].startswith('[MERGED]'):
                oMergedTitle = re.compile(r'MERGED.*has ([0-9]) vote')
                oMergedMatch = oMergedTitle.search(aLines[1])
                if oMergedMatch is not None and oMergedMatch.groups()[0] == \
                        oMatch.groups()[0]:
                    pass
                else:
                    sVotes = oMatch.groups()[0]
            elif oMatch_new is not None:
                sVotes = oMatch_new.groups()[0]
            if sVotes:
                if sVotes == '1':
                    sTitle = 'Independent with 1 vote'
                elif sVotes == '2':
                    sTitle = 'Independent with 2 votes'
                elif sVotes == '3':
                    sTitle = 'Independent with 3 votes'
        except IndexError:
            pass
    elif aLines[0].find('Laibon') != -1:
        sSect = 'Laibon'
        if sLowerLine.find('laibon magaji') != -1:
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
        r'[:\.] ([+-]\d) (bleed|strength|stealth|intercept)(?:(?=\.)|$)')
    # We avoid running these searches on the merged text of advanced
    # vampires to avoid confusion.
    dCryptProperties = {
        'black hand': re.compile(r'[:.] Black Hand'),
        # Seraph has a special case
        'seraph': re.compile(r'\. Black Hand(\.)? Seraph'),
        'infernal': re.compile(r'[.:] Infernal\.'),
        'red list': re.compile(r'\. Red List[:.]'),
        'scarce': re.compile(r'[.:] Scarce.'),
        'sterile': re.compile(r'[.:] Sterile.'),
        # Need the } to handle some of the errata'd cards
        'blood cursed': re.compile(r'[.:\}] \(?Blood [Cc]ursed'),
        # We divide slave by clan, since that's most useful
        'tremere slave': re.compile(r'Tremere [Ss]lave[:.]'),
        'tremere antitribu slave': re.compile(
            r'Tremere antitribu [Ss]lave[:.]'),
        'malkavian antitribu slave': re.compile(
            r'Malkavian antitribu slave'),
    }

    # Searches for these keywords must include the full text, including
    # any merge text
    dCryptFullTextProperties = {
        'not for legal play': re.compile(
            r'NOT FOR LEGAL PLAY|Added to the V:EKN banned list'),
    }

    # Properites we check for all library cards
    dLibProperties = {
        'not for legal play': re.compile(
            r'NOT FOR LEGAL PLAY|Added to the V:EKN banned list'),
    }

    # Ally properties
    dAllyProperties = {
        # Red list allies are templated differently
        'red list': re.compile(r'\. Red List\.'),
        'unique': re.compile(r'Unique [A-Za-z ]+ with \d life'),
    }
    oLifeRgx = re.compile(r'(Unique )?\[?(Gargoyle creature|[A-Za-z]+)\]?'
                          r' with (\d) life\.')

    # equipment properties
    dEquipmentProperties = {
        'unique': re.compile(r'Unique (melee )?weapon|Unique equipment|'
                             r'represents a unique location|'
                             r'Unique Nod|^Unique.|'
                             r'this is a unique location|'
                             r'as equipment (while|when) '
                             r'in play. (Haven. )?Unique.'),
        'location': re.compile(r'represents a (unique )?location|'
                               r'this is a (unique )?location'),
        'melee weapon': re.compile(r'[mM]elee weapon\.'),
        'cold iron': re.compile(r'weapon\. Cold iron\.'),
        'gun': re.compile(r'[wW]eapon[:,.] [gG]un\.'),
        'weapon': re.compile(r'[wW]eapon[:,.] [gG]un\.|[mM]elee weapon\.|'
                             r'Weapon.|Unique weapon.'),
        'vehicle': re.compile(r'Vehicle\.'),
        'haven': re.compile(r'Haven\.'),
        'electronic equipment': re.compile(r'Electronic equipment.|'
                                           r'^Electronic\.'),
    }

    # master properties
    dMasterProperties = {
        # unique isn't very consistent
        'unique': re.compile(r'[Uu]nique [mM]aster|Master[:.] unique|'
                             r'Unique\.|Unique location\.|Unique contract\.'),
        'trifle': re.compile(r'[tT]rifle\.'),
        'discipline': re.compile(r'Master: Discipline\.|'
                                 r'^Discipline\.'),
        'out-of-turn': re.compile(r'Master: out-of-turn|Out-of-turn\.'),
        'location': re.compile(r'Master[:.] (unique )?[Ll]ocation|'
                               r'Unique location\.|^Location\.'),
        'boon': re.compile(r'Boon\.'),
        'frenzy': re.compile(r'Frenzy\.'),
        'hunting ground': re.compile(r'\. Hunting [Gg]round'),
        'haven': re.compile(r'Haven\.'),
        'trophy': re.compile(r'Master\. Trophy'),
        'investment': re.compile(r'Master[.:] (unique )?[Ii]nvestment'),
        'archetype': re.compile(r'Master: archetype|Archetype\.'),
        'watchtower': re.compile(r'Master: watchtower'),
        'title': re.compile(r'Title\.'),
        'contract': re.compile(r'Contract\.|Unique contract\.|'
                               r'Master: contract\.'),
    }

    # event properties
    dEventProperties = {
        'gehenna': re.compile(r'Gehenna\.'),
        'transient': re.compile(r'Transient\.'),
        'inconnu': re.compile(r'Inconnu\.'),
        'government': re.compile(r'Government\.'),
        'inquisition': re.compile(r'Inquisition\.'),
    }

    # Catch for non-specified card types
    dOtherProperties = {
        'contract': re.compile(r'Contract\.'),
        'unique': re.compile(r'Unique\.'),
        'boon': re.compile(r'Boon\.'),
        'watchtower': re.compile(r'Watchtower\.'),
        'frenzy': re.compile(r'Frenzy\.'),
        'title': re.compile(r'Title\.'),
    }

    # Special cases that aren't handled by the general code
    dAllyKeywordSpecial = {
        'Gypsies': ['1 stealth'],
        'Veneficti': ['1 stealth'],
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
        super().__init__()
        self._oLogger = oLogger
        self._oMaker = SutekhObjectMaker()

    def _find_crypt_keywords(self, oCard):
        """Extract the bleed, strength & stealth keywords from the card text"""
        dKeywords = {'bleed': 1, 'strength': 1, 'stealth': 0, 'intercept': 0}
        # Correct special cases
        if self['name'] in self.dCryptKeywordSpecial:
            for sKeyword, iVal in \
                    self.dCryptKeywordSpecial[self['name']].items():
                dKeywords[sKeyword] = iVal
        # Make sure we don't detect merged properties
        sText = strip_braces(self['text'].split('[MERGED]')[0])
        for sNum, sType in self.oCryptInfoRgx.findall(sText):
            dKeywords[sType] += int(sNum)
        for sType, iNum in dKeywords.items():
            self._add_keyword(oCard, '%d %s' % (iNum, sType))
        # Check for "Black Hand", "Infernal", "Red List", "Seraph",
        for sKeyword, oRegexp in self.dCryptProperties.items():
            oMatch = oRegexp.search(sText)
            if oMatch:
                self._add_keyword(oCard, sKeyword)
        # Add Non-Unique keyword
        if 'are not unique' in sText or 'Non-unique' in sText:
            self._add_keyword(oCard, 'non-unique')
        # Imbued are also mortals, so add the keyword
        if self['cardtype'] == 'Imbued':
            self._add_keyword(oCard, 'mortal')
        # Check for full text keywords
        for sKeyword, oRegexp in self.dCryptFullTextProperties.items():
            oMatch = oRegexp.search(self['text'])
            if oMatch:
                self._add_keyword(oCard, sKeyword)

    def _find_lib_life_and_keywords(self, oCard):
        """Extract ally and retainer life and strength & bleed keywords from
           the card text"""
        # Restrict ourselves to text before Superior disciplines
        sText = strip_braces(re.split(r'\[[A-Z]{3}\]', self['text'])[0])
        # Annoyingly not standardised
        oDetail1Rgx = re.compile(r'\. (\d strength), (\d bleed)[\.,]')
        oDetail2Rgx = re.compile(r'\. (\d bleed), (\d strength)[\.,]')
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

        for sKeyword, oRegexp in dProps.items():
            _do_match(sKeyword, oRegexp)
        for sKeyword, oRegexp in self.dLibProperties.items():
            _do_match(sKeyword, oRegexp)

    def _parse_text(self, oCard):
        """Parse the CardText for Sect and Titles"""
        # pylint: disable=too-many-branches
        # Complex set of conditions, so many branches
        sType = None
        if 'cardtype' in self:
            sTypes = self['cardtype']
            # Determine if we need to examine the card further based on type
            for sVal in sTypes.split('/'):
                if sVal in ['Vampire', 'Imbued', 'Ally', 'Retainer',
                            'Equipment', 'Master', 'Event']:
                    sType = sVal
        # Check for REFLEX card type
        if self['text'].find(' [REFLEX] ') != -1:
            if 'cardtype' in self:
                # append to card types
                self['cardtype'] += '/Reflex'
            else:
                self['cardtype'] = 'Reflex'
        if sType in ('Imbued', 'Vampire'):
            self._find_crypt_keywords(oCard)
        elif sType in ('Ally', 'Retainer'):
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
            oFlightRexegp = re.compile(r'Flight \[FLIGHT\]\.')
            oMatch = oFlightRexegp.search(aLines[-1])
            if oMatch:
                if 'discipline' in self:
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
                # pylint: disable=no-member
                # SQLObject confuses pylint
                oCard.addRarityPair(oPair)

    def _make_card(self, sName):
        """Create the abstract card in the database."""
        sName = self.oDispCard.sub('', sName)
        return self._oMaker.make_abstract_card(sName)

    def _make_aliases(self):
        """Create lookup entries from the AKA entries in the cardlist"""
        for sAlias in self['aka'].split(';'):
            oLookup = self._oMaker.make_lookup_hint(
                "CardNames", sAlias.strip(), self['name'])
            oLookup.syncUpdate()

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
            elif 'anthology' in aPair[0].lower() and \
                    'larp' not in aPair[1].lower():
                # Add the Anthology reprint cases
                aExp.append((aPair[0].strip(), aPair[1].strip()))
                aExp.append(('AnthologyI', aPair[1].strip()))
            else:
                aExp.append((aPair[0].strip(), aPair[1].strip()))

        for sThisExp, sRarSet in aExp:
            for sRar in sRarSet.split('/'):
                if sRar in BC_RARITIES:
                    # Create expansion for the Black Chantry cards
                    oPair = self._oMaker.make_rarity_pair('Black Chantry',
                                                          sRar)
                else:
                    oPair = self._oMaker.make_rarity_pair(sThisExp, sRar)
                if oPair not in oCard.rarity:
                    # pylint: disable=no-member
                    # SQLObject confuses pylint
                    oCard.addRarityPair(oPair)

    def _add_disciplines(self, oCard, sDis):
        """Add the list of disciplines to the card, creating discipline
           pairs as needed."""
        sDis = self.oDisGaps.sub(' ', sDis).strip()

        if sDis in ('-none-', ''):
            return

        for sVal in sDis.split():
            if sVal == sVal.lower():
                oPair = self._oMaker.make_discipline_pair(sVal, 'inferior')
            else:
                oPair = self._oMaker.make_discipline_pair(sVal, 'superior')
            # pylint: disable=no-member
            # SQLObject confuses pylint
            if oPair not in oCard.discipline:
                oCard.addDisciplinePair(oPair)

    def _add_virtues(self, oCard, sVir):
        """Add the list of virtues to the card."""
        sVir = self.oDisGaps.sub(' ', sVir).strip()

        if sVir in ('-none-', ''):
            return

        for sVal in sVir.split():
            # pylint: disable=no-member
            # SQLObject confuses pylint
            oVirt = self._oMaker.make_virtue(sVal)
            if oVirt not in oCard.virtue:
                oCard.addVirtue(oVirt)

    def _add_creeds(self, oCard, sCreed):
        """Add creeds to the card."""
        sCreed = self.oWhiteSp.sub(' ', sCreed).strip()

        if sCreed in ('-none-', ''):
            return

        for sVal in sCreed.split('/'):
            # pylint: disable=no-member
            # SQLObject confuses pylint
            oCreed = self._oMaker.make_creed(sVal.strip())
            if oCreed not in oCard.creed:
                oCard.addCreed(oCreed)

    def _add_clans(self, oCard, sClan):
        """Add clans to the card."""
        sClan = self.oWhiteSp.sub(' ', sClan).strip()

        if sClan in ('-none-', ''):
            return

        for sVal in sClan.split('/'):
            oClan = self._oMaker.make_clan(sVal.strip())
            if oClan not in oCard.clan:
                # pylint: disable=no-member
                # SQLObject confuses pylint
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

        if sGroup.lower() in ('*', 'any'):
            iGroup = -1
        else:
            iGroup = int(sGroup, 10)

        oCard.group = iGroup

    def _add_life(self, oCard, sLife):
        """Add the life to the card."""
        sLife = self.oWhiteSp.sub(' ', sLife).strip()
        aLife = sLife.split()
        try:
            oCard.life = int(aLife[0], 10)
        except ValueError:
            pass

    def _get_level(self, sLevel):
        """Normalised the level string."""
        return self.oWhiteSp.sub(' ', sLevel).strip().lower()

    def _add_level(self, oCard, sLevel):
        """Add the correct string for the level to the card."""
        oCard.level = self._get_level(sLevel)

    def _fix_advanced_name(self):
        """Check if this is an advanced vampire."""
        sAlias = None
        if self['name'].endswith(' (Adv)'):
            self['level'] = 'advanced'
            sAlias = self['name']
            self['name'] = self['name'].replace(' (Adv)',
                                                ' (Advanced)')
        elif 'level' in self and self._get_level(self['level']) == 'advanced':
            sAlias = self['name'] + ' (Adv)'
            self['name'] += ' (Advanced)'
        if sAlias:
            # Add lookups for the '.. (Adv)' and '.. (ADV)' variations
            for sLookup in [sAlias, sAlias.replace('(Adv)', '(ADV)')]:
                oLookup = self._oMaker.make_lookup_hint("CardNames", sLookup,
                                                        self['name'])
                oLookup.syncUpdate()

    def _add_capacity(self, oCard, sCap):
        """Add the capacity to the card."""
        sCap = self.oWhiteSp.sub(' ', sCap).strip()
        aCap = sCap.split()
        try:
            oCard.capacity = int(aCap[0], 10)
        except ValueError:
            pass

    def _add_card_type(self, oCard, sTypes):
        """Add the card type info to the card."""
        for sVal in sTypes.split('/'):
            oType = self._oMaker.make_card_type(sVal.strip())
            if oType not in oCard.cardtype:
                # pylint: disable=no-member
                # SQLObject confuses pylint
                oCard.addCardType(oType)

    def _add_title(self, oCard, sTitle):
        """Add the title to the card."""
        oTitle = self._oMaker.make_title(sTitle)
        if oTitle not in oCard.title:
            # pylint: disable=no-member
            # SQLObject confuses pylint
            oCard.addTitle(oTitle)

    def _add_sect(self, oCard, sSect):
        """Add the sect to the card."""
        oSect = self._oMaker.make_sect(sSect)
        if oSect not in oCard.sect:
            # pylint: disable=no-member
            # SQLObject confuses pylint
            oCard.addSect(oSect)

    def _add_keyword(self, oCard, sKeyword):
        """Add the keyword to the card."""
        oKeyword = self._oMaker.make_keyword(sKeyword)
        if oKeyword not in oCard.keywords:
            # pylint: disable=no-member
            # SQLObject confuses pylint
            oCard.addKeyword(oKeyword)

    def _add_artists(self, oCard, sArtists):
        """Add the artist to the card."""
        for sArtist in self.oArtistSp.split(sArtists):
            oArtist = self._oMaker.make_artist(sArtist.strip())
            if oArtist not in oCard.artists:
                # pylint: disable=no-member
                # SQLObject confuses pylint
                oCard.addArtist(oArtist)

    def _add_physical_cards(self, oCard):
        """Create a physical card for each expansion."""
        self._oMaker.make_physical_card(oCard, None)
        for oExp in {oRarity.expansion for oRarity in oCard.rarity}:
            oPrinting = self._oMaker.make_default_printing(oExp)
            self._oMaker.make_physical_card(oCard, oPrinting)

    def save(self):
        # pylint: disable=too-many-branches
        # Need to consider all cases, so many branches
        """Commit the card to the database.

           This fills in the needed fields and creates entries in the join
           tables as needed.
           """
        if 'name' not in self:
            return

        self._fix_advanced_name()

        oCard = self._make_card(self['name'])

        if 'aka' in self:
            self._make_aliases()

        self._oLogger.info('Card: %s', self['name'])

        if 'text' in self:
            self._parse_text(oCard)

        if 'group' in self:
            self._add_group(oCard, self['group'])

        if 'capacity' in self:
            self._add_capacity(oCard, self['capacity'])

        if 'cost' in self:
            self._add_cost(oCard, self['cost'])

        if 'life' in self:
            self._add_life(oCard, self['life'])

        if 'level' in self:
            self._add_level(oCard, self['level'])
            # Also add a keyword for this
            self._add_keyword(oCard, oCard.level)

        if 'expansion' in self:
            self._add_expansions(oCard, self['expansion'])

        if 'keywords' in self:
            for sKeyword in self['keywords'].split(','):
                self._add_keyword(oCard, sKeyword)

        if 'discipline' in self:
            self._add_disciplines(oCard, self['discipline'])

        if 'virtue' in self:
            self._add_virtues(oCard, self['virtue'])

        if 'clan' in self:
            self._add_clans(oCard, self['clan'])

        if 'creed' in self:
            self._add_creeds(oCard, self['creed'])

        if 'cardtype' in self:
            self._add_card_type(oCard, self['cardtype'])

        if 'burn option' in self:
            self._add_keyword(oCard, "burn option")

        if 'title' in self:
            self._add_title(oCard, self['title'])

        if 'sect' in self:
            self._add_sect(oCard, self['sect'])

        if 'artist' in self:
            self._add_artists(oCard, self['artist'])

        if 'text' in self:
            oCard.text = self['text'].replace('\r', '')
            oCard.search_text = strip_braces(oCard.text)

        self._add_blood_shadowed_court(oCard)

        self._add_physical_cards(oCard)

        oCard.syncUpdate()
        # This is a bit hack'ish, but we also need to force an update of
        # the parent here.
        # It's not clear to me if this is a bug in SQLObject or not, given
        # the logic that requires us to force the update to oCard here anyway.
        # pylint: disable=protected-access
        # Need to access _parent here
        oCard._parent.syncUpdate()
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

    # pylint: disable=arguments-differ
    # pylint doesn't like that we mark dAttr as unused here
    def transition(self, sLine, _dAttr):
        """Transition to PotentialCard if needed."""
        if sLine.startswith('Name:'):
            self.flush()
            sData = sLine.split(':', 1)[1]
            # CSV style names sometimes creep into the cardlist.txt,
            # so ensure we normalise them consistently
            self._dInfo['name'] = move_articles_to_front(sData.strip())
            return InExpansion(self._dInfo, self._oLogger)
        if sLine.strip():
            if 'name' in self._dInfo and 'text' not in self._dInfo:
                # We've it a blank line in the middle of a card, so bounce
                # back to InCard stuff
                oCard = InCard(self._dInfo, self._oLogger)
                return oCard.transition(sLine, None)
        return self

    def flush(self):
        """Save any existing card and clear out dInfo"""
        if 'name' in self._dInfo:
            # Ensure we've saved existing card
            self._dInfo.save()
        self._dInfo = CardDict(self._oLogger)


class InCard(LogStateWithInfo):
    """State when we are in a card, waiting for the card text."""

    # These look like they start a key: value pair, but actually start
    # card text

    aTextTags = [
        'anarch',
        'master',
        'camarilla',
        'sabbat',
        'laibon',
        'independent',
        'strike',
        'weapon',
    ]

    # pylint: disable=arguments-differ
    # pylint doesn't like that we mark dAttr as unused here
    def transition(self, sLine, _dAttr):
        oCardText = None
        if ':' in sLine:
            sTag = fix_clarification_markers(sLine.split(':', 1)[0].lower())
            if sTag in self.aTextTags or ' ' in sTag or '{' in sTag:
                oCardText = InCardText(self._dInfo, self._oLogger)
            else:
                sData = fix_clarification_markers(sLine.split(':', 1)[1])
                # We don't want clarification markers here
                sData = sData.replace('{', '').replace('}', '')
                self._dInfo[sTag] = sData.strip()
        elif not sLine.strip():
            # Empty line, so probably end of the card
            return WaitingForCardName(self._dInfo, self._oLogger)
        else:
            if sLine.strip().lower() == 'burn option':
                # Annoying special case
                self._dInfo['burn option'] = None
            else:
                oCardText = InCardText(self._dInfo, self._oLogger)
        if oCardText:
            # Hand over the line to the card text parser
            return oCardText.transition(sLine, None)
        return self


class InExpansion(LogStateWithInfo):
    """In the expansions section."""

    # pylint: disable=arguments-differ
    # pylint doesn't like that we mark dAttr as unused here
    def transition(self, sLine, _dAttr):
        """Transition back to InCard if needed."""
        if sLine.startswith('[') and sLine.strip().endswith(']'):
            self._dInfo['expansion'] = sLine.strip()
            return InCard(self._dInfo, self._oLogger)
        if sLine.startswith('AKA:'):
            # We force this in here, since otherwise we need to bounce back and
            # force between InExpansion and InCard in an unpleasant way
            self._dInfo['aka'] = sLine.replace('AKA:', '').strip()
            return self
        # This shouldn't happen, so we bail as the only thing to do
        raise IOError("Failed to parse expansion information")


class InCardText(LogStateWithInfo):
    """In the card text section."""

    # pylint: disable=arguments-differ
    # pylint doesn't like that we mark dAttr as unused here
    def transition(self, sLine, _dAttr):
        """Transition back to InCard if needed."""
        if sLine.startswith('Artist:') or not sLine.strip():
            self._dInfo['text'] = fix_clarification_markers(
                self._dInfo['text'].strip())
            oInCard = InCard(self._dInfo, self._oLogger)
            return oInCard.transition(sLine, None)
        if 'text' not in self._dInfo:
            self._dInfo['text'] = sLine.strip() + '\n'
            # This newline is added so there's a separation between the
            # requirements and the rest of the card text, since otherwise
            # there's no marker for that.
            # For cards with only a single line, such as Bum's rush,
            # this will be stripped when we add it to the database
        else:
            # Since we're building this up a line at a time, we add a
            # trailing space, which we strip before we exit this parser
            self._dInfo['text'] += sLine.strip() + ' '
        # Note that we do no other formatting of the card text. This
        # is handled by the format_text helper function. This makes
        # it easy to change text display without needed to update
        # the database
        return self


# Parser
class WhiteWolfTextParser:
    """Actual Parser for the WW cardlist text file(s)."""

    def __init__(self, oLogHandler):
        self._oLogger = Logger('White wolf card parser')
        if oLogHandler is not None:
            self._oLogger.addHandler(oLogHandler)
        self._oState = None
        self.reset()

    def reset(self):
        """Reset the parser"""
        self._oState = WaitingForCardName({}, self._oLogger)

    def parse(self, fIn):
        """Feed lines to the state machine"""
        for sLine in fIn:
            self.feed(sLine)
        # Ensure we flush any open card text states
        self.feed('')
        if hasattr(self._oState, 'flush'):
            self._oState.flush()
            # We reached here without errors, so we set the update date to
            # today as the most sensible default for most situations and
            # assume the caller will fix it if that's not correct.
            set_metadata_date(CARDLIST_UPDATE_DATE, datetime.datetime.today())
        else:
            raise IOError('Failed to parse card list - '
                          'unexpected state at end of file.\n'
                          'Card list probably truncated.')

    def feed(self, sLine):
        """Feed the line to the current state"""
        # Strip BOM from line start
        sLine = sLine.lstrip(u'\ufeff')
        self._oState = self._oState.transition(sLine, None)
