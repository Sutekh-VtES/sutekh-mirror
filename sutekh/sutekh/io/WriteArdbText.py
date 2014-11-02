# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Writer for ther ARDB text deck format.

   Example deck:

   Deck Name : Followers of Set Preconstructed Deck
   Author : L. Scott Johnson
   Description :
   Followers of Set Preconstructed Starter from Lords of the Night.

   http://www.white-wolf.com/vtes/index.php?line=Checklist_LordsOfTheNight

   Crypt [12 vampires] Capacity min: 2 max: 10 average: 5.84
   ------------------------------------------------------------
   2x Nakhthorheb			  10 OBF PRE SER           Follower :4
   ...

   Library [77 cards]
   ------------------------------------------------------------
   Action [20]
     2x Blithe Acceptance
     4x Dream World
   ...
   """

from sutekh.core.ArdbInfo import ArdbInfo


class WriteArdbText(ArdbInfo):
    """Create a string in ARDB's text format representing a dictionary
       of cards."""

    # pylint: disable=R0201
    # method for consistency with the other methods
    def _gen_header(self, oHolder):
        """Generate an ARDB text file header."""
        return ("Deck Name : %s\n"
                "Author : %s\n"
                "Description :\n%s\n" % (oHolder.name, oHolder.author,
                                         oHolder.comment))
    # pylint: enable=R0201

    def _gen_crypt(self, dCards):
        """Generaten an ARDB text file crypt description.

           dCards is mapping of (card id, card name) -> card count.
           """
        (dVamps, dCryptStats) = self._extract_crypt(dCards)
        dCombinedVamps = self._group_sets(dVamps)

        sCrypt = "Crypt [%(size)d vampires] Capacity min: %(min)d " \
                "max: %(max)d average: %(avg).2f\n" \
                "-------------------------------------------------" \
                "-----------\n" \
                % dCryptStats

        aCryptLines = []
        # ARDB's discipline & title padding are based on the longest entry
        # so we need to keep track and format later
        iDiscJust = 0
        iTitleJust = 0
        for oCard, (iCount, _sSet) in sorted(dCombinedVamps.iteritems(),
                key=lambda x: (-x[1][0], self._get_cap_key(x[0]),
                               x[0].name)):
            # We sort inversely on count, then capacity and then normally by
            # name
            dLine = {'count': iCount}
            if len(oCard.creed) > 0:
                dLine['clan'] = "%s (Imbued)" % \
                    [x.name for x in oCard.creed][0]
                dLine['capacity'] = oCard.life
            else:
                dLine['clan'] = [x.name for x in oCard.clan][0]
                if dLine['clan'].endswith('antitribu'):
                    # ARDB doesn't truncate antitribu further
                    dLine['clan'] = '!' + dLine['clan'].replace(' antitribu',
                                                                '')
                else:
                    dLine['clan'] = dLine['clan'][:10]  # truncate if needed
                dLine['capacity'] = oCard.capacity
            dLine['name'] = oCard.name
            dLine['adv'] = '   '
            if oCard.level is not None:
                dLine['name'] = dLine['name'].replace(' (Advanced)', '')
                dLine['adv'] = 'Adv'
            dLine['name'] = dLine['name'].ljust(18)[:18]  # truncate if needed
            dLine['disc'] = self._gen_disciplines(oCard)
            iDiscJust = max(iDiscJust, len(dLine['disc']))

            dLine['title'] = '   '
            if len(oCard.title):
                dLine['title'] = [oC.name for oC in oCard.title][0]
                dLine['title'] = dLine['title'].replace('Independent with ',
                                                        '')[:12]
                iTitleJust = max(iTitleJust, len(dLine['title']))
            dLine['group'] = int(oCard.group)
            aCryptLines.append(dLine)

        for dLine in aCryptLines:
            dLine['title'] = dLine['title'].ljust(iTitleJust)
            dLine['disc'] = dLine['disc'].ljust(iDiscJust)
            sCrypt += " %(count)dx %(name)s %(adv)s %(capacity)d" \
                    " %(disc)s %(title)s %(clan)s:%(group)d\n" % dLine

        return sCrypt

    def _gen_library(self, dCards):
        """Generaten an ARDB text file library description.

           dCards is mapping of (card id, card name) -> card count.
           """
        (dLib, iLibSize) = self._extract_library(dCards)
        dCombinedLib = self._group_sets(dLib)
        dTypes = self._group_types(dCombinedLib)

        sLib = "Library [%d cards]\n" \
            "------------------------------------------------------------\n" \
            % (iLibSize,)

        for sTypeString in sorted(dTypes):
            dCards = dTypes[sTypeString]
            iTotal = sum(dCards.values())

            sLib += "%s [%d]\n" % (sTypeString, iTotal)

            for oCard, iCount in sorted(dCards.iteritems(),
                                        key=lambda x: x[0].name):
                sLib += " %dx %s\n" % (iCount, oCard.name)

            sLib += "\n"

        return sLib

    def write(self, fOut, oHolder):
        """Takes filename, deck details and a dictionary of cards, of the
           form dCard[(id, name, set)] = count and writes the file."""
        # We don't encode strange characters, and just write the unicode string
        # to file. This looks to match ARDB's behaviour (tested against
        # ARDB version 2.8
        dCards = self._get_cards(oHolder.cards)
        fOut.write(self._gen_header(oHolder))
        fOut.write("\n")
        fOut.write(self._gen_crypt(dCards))
        fOut.write("\n")
        fOut.write(self._gen_library(dCards))
