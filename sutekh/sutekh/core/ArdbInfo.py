# ArdbInfo.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Base class for the ARDB writers.

   Provide methods for extracting the relevant cards from the card set
   and such.
   """

from sutekh.core.SutekhObjects import IAbstractCard, IPhysicalCard

class ArdbInfo(object):
    """Create a string in ARDB's text format representing a dictionary
       of cards."""

    # pylint: disable-msg=R0201
    # these need to be available to the descendants
    def _extract_crypt(self, dCards):
        """Extract the crypt cards from the list."""
        dCryptStats = {
                'size' : 0,
                'min' : 75,
                'max' : 0,
                'avg' : 0.0
                }
        dVamps = {}
        for tKey, iCount in dCards.iteritems():
            sName = tKey[1]
            # pylint: disable-msg=E1101
            # IAbstractCard confuses pylint
            oCard = IAbstractCard(sName)
            aTypes = [x.name for x in oCard.cardtype]
            if aTypes[0] == 'Vampire':
                dVamps[tKey] = iCount
                dCryptStats['size'] += iCount
                dCryptStats['avg'] += oCard.capacity*iCount
                if oCard.capacity > dCryptStats['max']:
                    dCryptStats['max'] = oCard.capacity
                if oCard.capacity < dCryptStats['min']:
                    dCryptStats['min'] = oCard.capacity
            if aTypes[0] == 'Imbued':
                dVamps[tKey] = iCount
                dCryptStats['size'] += iCount
                dCryptStats['avg'] += oCard.life*iCount
                if oCard.life > dCryptStats['max']:
                    dCryptStats['max'] = oCard.life
                if oCard.life < dCryptStats['min']:
                    dCryptStats['min'] = oCard.life
        if dCryptStats['size'] > 0:
            dCryptStats['avg'] = round(dCryptStats['avg'] /
                    dCryptStats['size'], 2)
        if dCryptStats['min'] == 75:
            dCryptStats['min'] = 0
        return dVamps, dCryptStats

    def _extract_library(self, dCards):
        """Extract the library cards from the list."""
        iSize = 0
        dLib = {}
        for tKey, iCount in dCards.iteritems():
            iId, sName, sSet = tKey
            # pylint: disable-msg=E1101
            # IAbstractCard confuses pylint
            oCard = IAbstractCard(sName)
            aTypes = sorted([x.name for x in oCard.cardtype])
            if aTypes[0] != 'Vampire' and aTypes[0] != 'Imbued':
                # Looks like it should be the right thing, but may not
                sTypeString = "/".join(aTypes)
                # We want to be able to sort over types easily, so
                # we add them to the keys
                dLib[(iId, sName, sTypeString, sSet)] = iCount
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

    def _get_cards(self, oCardIter):
        """Create the dictionary of cards given the list of cards"""
        # pylint: disable-msg=E1101
        # SQLObject methods confuse pylint
        dDict = {}
        for oCard in oCardIter:
            oPhysCard = IPhysicalCard(oCard)
            oAbsCard = IAbstractCard(oCard)
            if oPhysCard.expansion:
                sSet = self._get_ardb_exp_name(oPhysCard.expansion)
            else:
                # ARDB doesn't have a concept of 'No expansion', so we
                # need to fake it. We use the first legitimate expansion
                oRarityPair = list(oAbsCard.rarity)[0]
                sSet = self._get_ardb_exp_name(oRarityPair.expansion)
            dDict.setdefault((oAbsCard.id, oAbsCard.name, sSet), 0)
            dDict[(oAbsCard.id, oAbsCard.name, sSet)] += 1
        return dDict

    def _get_ardb_exp_name(self, oExpansion):
        """Extract the correct ARDB name for the expansion"""
        sSet = oExpansion.shortname
        if sSet == 'Promo':
            sSet = oExpansion.name
            sSet.replace('-', '')
        elif sSet == 'BSC':
            # ARDB doesn't support BSC.
            sSet = 'CE'
        return sSet

