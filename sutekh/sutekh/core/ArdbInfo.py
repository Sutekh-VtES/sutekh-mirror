# ArdbInfo.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""
   Base class for the ARDB writers.
   Provide methods for extracting the relevant cards from the card set
   and such.
   """

from sutekh.core.SutekhObjects import IAbstractCard

class ArdbInfo(object):
    """Create a string in ARDB's text format representing a dictionary
       of cards."""

    # pylint: disable-msg=R0201
    # these need to be available to the descendants
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
                if oCard.life > iMax:
                    iMax = oCard.life
                if oCard.life < iMin:
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
            return " ".join(sorted([x.name for x in oCard.virtue]))
        return ""
