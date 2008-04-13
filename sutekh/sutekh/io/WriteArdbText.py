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

from sutekh.core.SutekhObjects import IAbstractCard
from sutekh.core.ArdbInfo import ArdbInfo

class WriteArdbText(ArdbInfo):
    """Create a string in ARDB's text format representing a dictionary
       of cards."""

    # pylint: disable-msg=R0201
    # method for consistency with the other methods
    def _gen_header(self, sSetName, sAuthor, sDescription):
        """Generate an ARDB text file header."""
        return "Deck Name : %s\n" \
               "Author : %s\n" \
               "Description :\n%s\n" % (sSetName, sAuthor, sDescription)
    # pylint: enable-msg=R0201

    def _gen_crypt(self, dCards):
        """Generaten an ARDB text file crypt description.

           dCards is mapping of (card id, card name) -> card count.
           """
        (dVamps, iCryptSize, iMin, iMax, fAvg) = self._extract_crypt(dCards)

        sCrypt = "Crypt [%d vampires] Capacity min: %d max: %d average: %f\n" \
            "------------------------------------------------------------\n" \
            % (iCryptSize, iMin, iMax, fAvg)

        for tKey in sorted(dVamps, key=lambda x: x[1]):
            sName = tKey[1]
            iCount = dVamps[tKey]

            # pylint: disable-msg=E1101
            # IAbstractCard confuses pylint
            oCard = IAbstractCard(sName)
            if len(oCard.creed) > 0:
                sClan = "Imbued"
            else:
                sClan = [x.name for x in oCard.clan][0]
            sDisciplines = self._gen_disciplines(oCard)

            sCrypt += "  %dx %s %d %s %s :%d\n" % \
                 (iCount, sName, oCard.capacity, sDisciplines, sClan,
                         oCard.group)

        return sCrypt

    def _gen_library(self, dCards):
        """Generaten an ARDB text file library description.

           dCards is mapping of (card id, card name) -> card count.
           """
        (dLib, iLibSize) = self._extract_library(dCards)

        sLib = "Library [%d cards]\n" \
            "------------------------------------------------------------\n" \
            % (iLibSize,)

        dTypes = {}
        for iId, sName, sTypeString in dLib:
            if sTypeString not in dTypes:
                dTypes[sTypeString] = {}
            dTypes[sTypeString][(iId, sName)] = dLib[(iId, sName, sTypeString)]

        for sTypeString in sorted(dTypes):
            dCards = dTypes[sTypeString]
            iTotal = sum(dCards.values())

            sLib += "%s [%d]\n" % (sTypeString, iTotal)

            for (iId, sName), iCount in dCards.iteritems():
                sLib += "  %dx %s\n" % (iCount, sName)

            sLib += "\n"

        return sLib

    # pylint: disable-msg=R0913
    # we need all these arguments
    def write(self, fOut, sSetName, sAuthor, sDescription, dCards):
        """
        Takes filename, deck details and a dictionary of cards, of the form
        dCard[(id, name)]=count
        """
        fOut.write(self._gen_header(sSetName, sAuthor, sDescription))
        fOut.write("\n")
        fOut.write(self._gen_crypt(dCards))
        fOut.write("\n")
        fOut.write(self._gen_library(dCards))

    # pylint: enable-msg=R0913
