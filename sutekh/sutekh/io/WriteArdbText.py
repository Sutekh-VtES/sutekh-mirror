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

class WriteArdbText(object):
    """Create a string in ARDB's text format representing a dictionary
       of cards."""

    def _extract_crypt(self, dCards):
        """Extract the crypt cards from the list."""
        iCryptSize = 0
        iMax = 0
        iMin = 75
        fAvg = 0.0
        dVamps = {}
        for tKey, iCount in dCards.iteritems():
            sName = tKey[1]
            # pylint: disable-msg=E1101
            # IAbstractCard confuses pylint
            oCard = IAbstractCard(sName)
            aTypes = [x.name for x in oCard.cardtype]
            if aTypes[0] == 'Vampire':
                dVamps[tKey] = iCount
                iCryptSize += iCount
                fAvg += oCard.capacity*iCount
                if oCard.capacity > iMax:
                    iMax = oCard.capacity
                if oCard.capacity < iMin:
                    iMin = oCard.capacity
            if aTypes[0] == 'Imbued':
                dVamps[tKey] = iCount
                iCryptSize += iCount
                fAvg += oCard.life*iCount
                if oCard.capacity > iMax:
                    iMax = oCard.life
                if oCard.capacity < iMin:
                    iMin = oCard.life
        if iCryptSize > 0:
            fAvg = round(fAvg/iCryptSize, 2)
        if iMin == 75:
            iMin = 0
        return (dVamps, iCryptSize, iMin, iMax, fAvg)

    def _extract_library(self, dCards):
        """Extract the library cards from the list."""
        iSize = 0
        dLib = {}
        for tKey, iCount in dCards.iteritems():
            iId, sName = tKey
            # pylint: disable-msg=E1101
            # IAbstractCard confuses pylint
            oCard = IAbstractCard(sName)
            aTypes = sorted([x.name for x in oCard.cardtype])
            if aTypes[0] != 'Vampire' and aTypes[0] != 'Imbued':
                # Looks like it should be the right thing, but may not
                sTypeString = "/".join(aTypes)
                # We want to be able to sort over types easily, so
                # we add them to the keys
                dLib[(iId, sName, sTypeString)] = iCount
                iSize += iCount
        return (dLib, iSize)

    def _gen_header(self, sSetName, sAuthor, sDescription):
        """Generate an ARDB text file header."""
        return "Deck Name : %s\n" \
               "Author : %s\n" \
               "Description :\n%s\n" % (sSetName, sAuthor, sDescription)

    def _gen_crypt(self, dCards):
        """Generaten an ARDB text file crypt description.

           dCards is mapping of (card id, card name) -> card count.
           """
        (dVamps, iCryptSize, iMin, iMax, fAvg) = self._extract_crypt(dCards)

        s = "Crypt [%d vampires] Capacity min: %d max: %d average: %f\n" \
            "------------------------------------------------------------\n" \
            % (iCryptSize, iMin, iMax, fAvg)

        for tKey in sorted(dVamps, key=lambda x: x[1]):
            iId, sName = tKey
            iCount = dVamps[tKey]

            oCard = IAbstractCard(sName)
            if len(oCard.creed) > 0:
                sClan = "Imbued"
            else:
                sClan = [x.name for x in oCard.clan][0]
            sDisciplines = self._gen_disciplines(oCard)

            s += "  %dx %s %d %s %s :%d\n" % \
                 (iCount, sName, oCard.capacity, sDisciplines, sClan, oCard.group)

        return s

    def _gen_disciplines(self, oCard):
        """Extract the discipline string from the card."""
        if len(oCard.discipline) > 0:
            aDisc = []
            for oDisc in oCard.discipline:
                if oDisc.level == 'superior':
                    aDisc.append(oDisc.discipline.name.upper())
                else:
                    aDisc.append(oDisc.discipline.name)
            aDisc.sort() # May not be needed
            return " ".join(aDisc)
        elif len(oCard.virtue) > 0:
            return " ".join([x.name for x in oCard.virtue])
        return ""

    def _gen_library(self, dCards):
        """Generaten an ARDB text file library description.

           dCards is mapping of (card id, card name) -> card count.
           """
        (dLib, iLibSize) = self._extract_library(dCards)

        s = "Library [%d cards]\n" \
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

            s += "%s [%d]\n" % (sTypeString, iTotal)

            for (iId, sName), iCount in dCards.iteritems():
                s += "  %dx %s\n" % (iCount, sName)

            s += "\n"

        return s

    def write(self, fOut, sSetName, sAuthor, sDescription, dCards):
        """
        Takes filename, deck details and a dictionary of cards, of the form
        dCard[(id,name)]=count
        """
        fOut.write(self._gen_header(sSetName, sAuthor, sDescription))
        fOut.write("\n")
        fOut.write(self._gen_crypt(dCards))
        fOut.write("\n")
        fOut.write(self._gen_library(dCards))
