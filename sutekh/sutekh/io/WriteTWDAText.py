# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Writer for the text format preferred for TWDA entries.

   Example deck:

   Deck Name: Modified Followers of Set Preconstructed Deck
   Author: An Author
   Description:
   Followers of Set Preconstructed Starter from Lords of the Night.

   http://www.white-wolf.com/vtes/index.php?line=Checklist_LordsOfTheNight

   Crypt (12 cards, min=10 max=40 avg=5.84)
   ----------------------------------------
   2x Nakhthorheb	10 OBF PRE SER                        Follower of Set:4
   2x Renenet       5 OBF PRE ser                         Follower of Set:4
   1x Neferu        9 OBF PRE SER THA dom nec   2 votes   Follower of Set:4
   1x Arcadian, The 8 DOM MYT OBT chi for                 Kiasyd:5
   ...

   Library (77 cards)
   Master (4; 1 trifle)
     2x Barrens, The
     1x Sudden Reversal
     1x Wash

   Action (20)
     2x Blithe Acceptance
     4x Dream World

   Ally (1)
     1x Carlton Van Wyk

   Equipment (2)
     2x .44 Magnum

   Political Action (1)
     1x Parity Shity

   Action Modifier (3)
   ...
   """

from sutekh.base.Utility import move_articles_to_back

from sutekh.core.ArdbInfo import ArdbInfo


# the twd.htm normalises some names, but not all of them
SPECIAL_NAMES = {
    u'Pentex™ Loves You!': 'Pentex(TM) Loves You!',
    u'Pentex™ Subversion': 'Pentex(TM) Subversion',
}

# Emprically derived from the twd.htm entries
SECTION_ORDER = (
    'Master',
    'Conviction',
    'Action',
    'Ally',
    'Equipment',
    'Political Action',
    'Power',
    'Retainer',
    'Action Modifier',
    'Reaction',
    'Combat',
    'Event',
)


def format_avg(fAvg):
    """The TWDA doesn't want trailing zeros in the average, so we
       strip those here"""
    iIntPart = int(fAvg)
    fFracPart = fAvg - iIntPart
    sResult = '%d' % iIntPart
    if fFracPart > 0.001:
        sFrac = '%.2g' % fFracPart
        sResult += sFrac[1:]
    return sResult


def normalise_card_name(sName):
    """Normalise the name as needed for the TWDA"""
    sName = move_articles_to_back(sName)
    return SPECIAL_NAMES.get(sName, sName)


class WriteTWDAText(ArdbInfo):
    """Create a string in ARDB's text format representing a dictionary
       of cards."""

    # pylint: disable=no-self-use
    # method for consistency with the other methods
    def _gen_header(self, oHolder):
        """Generate an TWDA text file header."""
        return ("Deck Name: %s\n"
                "Author: %s\n"
                "Description:\n%s\n" % (oHolder.name, oHolder.author,
                                        oHolder.comment))
    # pylint: enable=no-self-use

    def _crypt_sort_key(self, tItem):
        """Sort the crypt cards.

           We override the base class so we can sort by the modified name."""
        return (-tItem[1][0], self._get_cap_key(tItem[0]),
                move_articles_to_back(tItem[0].name).lower())

    def _gen_crypt(self, dCards):
        """Generate an TWDA text file crypt description.

           dCards is mapping of (card id, card name) -> card count.
           """
        # pylint: disable=too-many-statements, too-many-branches
        # pylint: disable=too-many-locals
        # This has lots of complicated logic to try duplicate the
        # formatting done by the unpublished ARDB template used
        # in the TWDA. It's messy, largely because the TWDA uses
        # tabs, which add complicated rules.
        (dVamps, dCryptStats) = self._extract_crypt(dCards)
        dCryptStats['formatted_avg'] = format_avg(dCryptStats['avg'])
        dCombinedVamps = self._group_sets(dVamps)

        sCryptLine = "Crypt (%(size)d cards, min=%(minsum)d, " \
                     "max=%(maxsum)d, avg=%(formatted_avg)s)" \
                     % dCryptStats
        sCrypt = sCryptLine + '\n' + '-' * len(sCryptLine) + '\n'

        aCryptLines = []
        iCountSpace = 3
        iNameJust = 8
        iDiscJust = 0
        iTitleJust = 0
        for oCard, (iCount, _sSet) in sorted(dCombinedVamps.items(),
                                             key=self._crypt_sort_key):
            dLine = self._format_crypt_line(oCard, iCount)
            if 'Imbued' in dLine['clan']:
                dLine['clan'].replace(' (Imbued)', '')
            dLine['disc'] = self._gen_disciplines(oCard)
            # Standardise missing disciplines
            if not dLine['disc']:
                dLine['disc'] = '-none-'
            dLine['name'] = normalise_card_name(dLine['name'])
            iNameJust = max(iNameJust, len(dLine['name']))
            iDiscJust = max(iDiscJust, len(dLine['disc']))
            if iCount > 10:
                iCountSpace = 4
            dLine['title'] = dLine['title'].strip()
            iTitleJust = max(iTitleJust, len(dLine['title']))
            aCryptLines.append(dLine)
            if dLine['adv'] == 'Adv':
                dLine['name'] += ' (ADV)'

        # Vincent likes tabs. Why, Vincent, why?
        # Capacity position
        iCapacityPos = iCountSpace + iNameJust + 1
        if iCapacityPos < 24:
            # MAtch TWDA conventions
            iCapacityPos = 24
        # Convert to tabstop positions
        iNameJust = (iCapacityPos // 8) * 8
        # Tab stop after disciplines
        iDiscJust = ((iCapacityPos + 2 + iDiscJust) // 8) * 8
        # Tabstop after titles
        if iTitleJust:
            # Tabstop after titles
            iTitleJust = ((iDiscJust + 16) // 8) * 8
        for dLine in aCryptLines:
            if iCountSpace == 3:
                sCount = '%(count)dx ' % dLine
            else:
                sCount = '%(count)2dx ' % dLine
            iPos = iCountSpace + len(dLine['name'])
            while iPos < iNameJust:
                dLine['name'] += '\t'
                # round pos to the next tabstop
                iPos = iPos + 8 - (iPos + 8) % 8
            # Pad out with spaces to just before capacity position
            dLine['name'] += ' ' * (iCapacityPos - iPos)
            sDisc = '%(capacity)-3d %(disc)s' % dLine
            iPos = iCapacityPos + len(sDisc)
            # Round position to the tabstop before the end of the disciplines
            iTabPos = iPos - iPos % 8
            sPadd = ''
            while iTabPos <= iDiscJust:
                sPadd += '\t'
                iTabPos += 8
                iPos = iTabPos + 8
            if sPadd == '' and iTabPos > 40:
                # We add a tab in this case
                sPadd = '\t'
                iPos = iTabPos + 8
            dLine['disc'] = sDisc + sPadd
            if iTitleJust:
                iEndPos = (iTitleJust - len(dLine['title']) - iDiscJust + 7)
                iPadding = iEndPos // 8
                dLine['title'] = dLine['title'].lower() + '\t' * iPadding
            sCrypt += sCount + "%(name)s%(disc)s" \
                    "%(title)s%(clan)s:%(group)d\n" % dLine
            # Fix ANY grouping cards
            if sCrypt.endswith(':-1\n'):
                sCrypt = sCrypt.replace(':-1', ':ANY')

        return sCrypt

    def _gen_library(self, dCards):
        """Generaten an TWDA text file library description.

           dCards is mapping of (card id, card name) -> card count.
           """
        (dLib, iLibSize) = self._extract_library(dCards)
        dCombinedLib = self._group_sets(dLib)
        dTypes = self._group_types(dCombinedLib)

        sLib = "Library (%d cards)\n" \
            % (iLibSize,)

        aSortedTypes = sorted(dTypes)
        # We shuffle master to be the first section

        aProcessed = set()

        for sTypeString in SECTION_ORDER:
            dCards = {}
            for sCandidate in aSortedTypes:
                if sCandidate in aProcessed:
                    continue
                if sTypeString == sCandidate:
                    dCards = dTypes[sCandidate]
                    aProcessed.add(sCandidate)
                elif sCandidate.startswith(sTypeString+'/'):
                    dCards = dTypes[sCandidate]
                    aProcessed.add(sCandidate)
                else:
                    continue

                iTotal = sum(dCards.values())

                if sTypeString == 'Master':
                    iTrifles = self._count_trifles(dLib)
                    if iTrifles:
                        sLib += "%s (%d; %d trifle)\n" % (sTypeString,
                                                          iTotal, iTrifles)
                    else:
                        sLib += "%s (%d)\n" % (sCandidate, iTotal)
                else:
                    # Sections in the library get an extra blank line
                    sLib += '\n'
                    sLib += "%s (%d)\n" % (sCandidate, iTotal)

                # library cards are also normalised
                fKey = lambda x: move_articles_to_back(x[0].name).lower()
                for oCard, iCount in sorted(dCards.items(), key=fKey):
                    sName = normalise_card_name(oCard.name)
                    sLib += "%dx %s\n" % (iCount, sName)
        return sLib

    def write(self, fOut, oHolder):
        """Takes filename, deck details and a dictionary of cards, of the
           form dCard[(id, name, set)] = count and writes the file."""
        # We don't encode strange characters, and just write the unicode string
        # to file.
        dCards = self._get_cards(oHolder.cards)
        fOut.write(self._gen_header(oHolder))
        fOut.write("\n")
        fOut.write(self._gen_crypt(dCards))
        fOut.write("\n")
        fOut.write(self._gen_library(dCards))
