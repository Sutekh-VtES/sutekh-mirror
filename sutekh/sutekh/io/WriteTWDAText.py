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
   2x Nakhthorheb		10 OBF PRE SER                        Follower of Set:4
   2x Renenet           5 OBF PRE ser                         Follower of Set:4
   1x Neferu            9 OBF PRE SER THA dom nec   2 votes   Follower of Set:4
   1x Arcadian, The     8 DOM MYT OBT chi for                 Kiasyd:5
   ...

   Library (77 cards)
   Master (3)
     2x Barrens, The
     1x Sudden Reversal
   Action (20)
     2x Blithe Acceptance
     4x Dream World
   ...
   """

from sutekh.base.Utility import move_articles_to_back

from sutekh.core.ArdbInfo import ArdbInfo


class WriteTWDAText(ArdbInfo):
    """Create a string in ARDB's text format representing a dictionary
       of cards."""

    # pylint: disable=R0201
    # method for consistency with the other methods
    def _gen_header(self, oHolder):
        """Generate an TWDA text file header."""
        return ("Deck Name: %s\n"
                "Author: %s\n"
                "Description:\n%s\n" % (oHolder.name, oHolder.author,
                                        oHolder.comment))
    # pylint: enable=R0201

    def _crypt_sort_key(self, tItem):
        """Sort the crypt cards.

           We override the base class so we can sort by the modified name."""
        return (-tItem[1][0], self._get_cap_key(tItem[0]),
                move_articles_to_back(tItem[0].name))

    def _gen_crypt(self, dCards):
        """Generate an TWDA text file crypt description.

           dCards is mapping of (card id, card name) -> card count.
           """
        (dVamps, dCryptStats) = self._extract_crypt(dCards)
        dCombinedVamps = self._group_sets(dVamps)

        sCryptLine = "Crypt (%(size)d cards, min=%(minsum)d, " \
                     "max=%(maxsum)d, avg=%(avg).2f)" \
                     % dCryptStats
        sCrypt = sCryptLine + '\n' + '-' * len(sCryptLine) + '\n'

        aCryptLines = []
        iNameJust = 23
        iDiscJust = 0
        iTitleJust = 0
        for oCard, (iCount, _sSet) in sorted(dCombinedVamps.iteritems(),
                                             key=self._crypt_sort_key):
            dLine = self._format_crypt_line(oCard, iCount)
            if 'Imbued' in dLine['clan']:
                dLine['clan'].replace(' (Imbued)', '')
            dLine['disc'] = self._gen_disciplines(oCard)
            # Standardise missing disciplines
            if not dLine['disc']:
                dLine['disc'] = '-none-'
            # TWDA normalises crypt names to have the articles at the
            # back, but doesn't care about library cards
            dLine['name'] = move_articles_to_back(dLine['name'])
            iNameJust = max(iNameJust, len(dLine['name']))
            iDiscJust = max(iDiscJust, len(dLine['disc']))

            iTitleJust = max(iTitleJust, len(dLine['title']))
            aCryptLines.append(dLine)
            if dLine['adv'] == 'Adv':
                dLine['name'] += ' (ADV)'
        # Vincent likes tabs. Why, Vincent, why?
        # Normalise to tabstops
        iNameJust = ((iNameJust + 7) // 8) * 8 - 1
        iTitleJust = ((iTitleJust + 7) // 8) * 8 - 1
        # Need to include space for capacity (4 spaces) here
        iDiscJust = ((iDiscJust + 11) // 8) * 8

        # Pad with tabs as needed
        for dLine in aCryptLines:
            sCount = '%(count)dx ' % dLine
            iPadding = (iNameJust - len(dLine['name']) - len(sCount)) // 8
            dLine['name'] += '\t' * iPadding
            iPadding = (iTitleJust - len(dLine['title'])) // 8
            dLine['title'] = dLine['title'].lower() + '\t' * iPadding
            sDisc = '%(capacity)-3d %(disc)s' % dLine
            iPadding = (iDiscJust - len(sDisc)) // 8
            sDisc += '\t' * iPadding
            dLine['disc'] = sDisc
            sCrypt += "%(count)dx %(name)s\t%(disc)s" \
                    "\t%(title)s\t%(clan)s:%(group)d\n" % dLine
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
        if 'Master' in aSortedTypes:
            aSortedTypes.remove('Master')
            aSortedTypes.insert(0, 'Master')

        for sTypeString in aSortedTypes:
            dCards = dTypes[sTypeString]
            iTotal = sum(dCards.values())

            if sTypeString == 'Master':
                iTrifles = self._count_trifles(dLib)
                if iTrifles > 1:
                    sLib += "%s (%d, %d trifles)\n" % (sTypeString,
                                                       iTotal, iTrifles)
                elif iTrifles == 1:
                    sLib += "%s (%d, %d trifles)\n" % (sTypeString,
                                                       iTotal, iTrifles)
                else:
                    sLib += "%s (%d)\n" % (sTypeString, iTotal)
            else:
                sLib += "%s (%d)\n" % (sTypeString, iTotal)

            for oCard, iCount in sorted(
                    dCards.iteritems(),
                    key=lambda x: move_articles_to_back(x[0].name)):
                sLib += "%dx %s\n" % (iCount,
                                      move_articles_to_back(oCard.name))
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
