# WriteArdbText.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
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

    # pylint: disable-msg=R0201
    # method for consistency with the other methods
    def _gen_header(self, oHolder):
        """Generate an ARDB text file header."""
        return "Deck Name : %s\n" \
               "Author : %s\n" \
               "Description :\n%s\n" % (oHolder.name, oHolder.author,
                       oHolder.comment)
    # pylint: enable-msg=R0201

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

        for oCard,  (iCount, _sSet) in sorted(dCombinedVamps.iteritems(),
                key=lambda x: (-x[1][0], -max(x[0].capacity, x[0].life),
                    x[0].name)):
            # We sort inversely on count, then capacity and then normally by
            # name
            if len(oCard.creed) > 0:
                sClan = "Imbued"
                iCapacity = oCard.life
            else:
                sClan = [x.name for x in oCard.clan][0]
                iCapacity = oCard.capacity
            sName = oCard.name.ljust(20)
            sDisciplines = self._gen_disciplines(oCard).ljust(20)

            # FIXME: Current discrepencies from ARDB's output
            # We don't truncate fields (ARDB truncates at least name & clan)
            # We don't include titles
            # We don't use the !Clan form for antitribu clans

            sCrypt += "  %dx %s %d %s %s :%d\n" % \
                 (iCount, sName, iCapacity, sDisciplines, sClan,
                         oCard.group)

        return sCrypt

    def _gen_library(self, dCards):
        """Generaten an ARDB text file library description.

           dCards is mapping of (card id, card name) -> card count.
           """
        (dLib, iLibSize) = self._extract_library(dCards)
        dCombinedLib = self._group_sets(dLib)

        sLib = "Library [%d cards]\n" \
            "------------------------------------------------------------\n" \
            % (iLibSize,)

        dTypes = {}
        for oCard, (iCount, sTypeString, _sSet) in dCombinedLib.iteritems():
            if sTypeString not in dTypes:
                dTypes[sTypeString] = {}
            dTypes[sTypeString].setdefault(oCard, 0)
            dTypes[sTypeString][oCard] += iCount

        for sTypeString in sorted(dTypes):
            dCards = dTypes[sTypeString]
            iTotal = sum(dCards.values())

            sLib += "%s [%d]\n" % (sTypeString, iTotal)

            for oCard, iCount in sorted(dCards.iteritems(),
                    key=lambda x: x[0].name):
                sLib += "  %dx %s\n" % (iCount, oCard.name)

            sLib += "\n"

        return sLib

    # pylint: disable-msg=R0913
    # we need all these arguments
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

    # pylint: enable-msg=R0913
