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
from sutekh.SutekhInfo import SutekhInfo
from sutekh.SutekhUtility import is_crypt_card


def escape_ardb_expansion_name(oExpansion):
    """Rework the expansion name to match ARDB"""
    sExpName = oExpansion.shortname
    if sExpName == 'Promo':
        sExpName = oExpansion.name
        sExpName = sExpName.replace('-', '')
    elif sExpName == 'BSC':
        # ARDB doesn't support BSC.
        sExpName = 'CE'
    return sExpName


def unescape_ardb_expansion_name(sExpName):
    """Rework ARBD Promo to Sutekh Promo-"""
    if sExpName.startswith('Promo') and not sExpName.startswith('Promo-'):
        sExpName = sExpName.replace('Promo', 'Promo-')
    return sExpName


class ArdbInfo(object):
    """Create a string in ARDB's text format representing a dictionary
       of cards."""

    # Should this be an attribute of VersionTable?
    sDatabaseVersion = 'Sutekh-20090410'

    sVersionString = SutekhInfo.VERSION_STR
    # pylint: disable-msg=W0511
    # this is not a actual TODO item
    # Claim same version as recent ARDB
    sFormatVersion = '-TODO-1.0'
    # pyline: enable-msg=W0511

    def _get_cards(self, oCardIter):
        """Create the dictionary of cards given the list of cards"""
        # pylint: disable-msg=E1101
        # SQLObject methods confuse pylint
        dDict = {}
        for oCard in oCardIter:
            oPhysCard = IPhysicalCard(oCard)
            oAbsCard = IAbstractCard(oCard)
            sSet = self._get_ardb_exp_name(oPhysCard)
            dDict.setdefault((oAbsCard, sSet), 0)
            dDict[(oAbsCard, sSet)] += 1
        return dDict

    # pylint: disable-msg=R0201
    # these need to be available to the descendants
    def _group_sets(self, dCards):
        """Group the cards together regardless of set.

           ARDB inventory doesn't seperate cards by set, although it's included
           in the XML file, so we need to combine things so there's only 1
           entry per card."""
        dCombinedCards = {}
        for tKey, iNum in sorted(dCards.iteritems(),
                key=lambda x: (x[0][0].name, x[0][-1])):
            oCard = tKey[0]
            dCombinedCards.setdefault(oCard, [0] + list(tKey[1:]))
            dCombinedCards[oCard][0] += iNum
        return dCombinedCards

    def _extract_crypt(self, dCards):
        """Extract the crypt cards from the list."""
        dCryptStats = {
                'size': 0,
                'min': 75,
                'max': 0,
                'avg': 0.0,
                }
        dVamps = {}
        for tKey, iCount in dCards.iteritems():
            oCard = tKey[0]
            if is_crypt_card(oCard):
                dVamps[tKey] = iCount
                dCryptStats['size'] += iCount
                if oCard.cardtype[0].name == "Vampire":
                    iCap = oCard.capacity
                elif oCard.cardtype[0].name == "Imbued":
                    iCap = oCard.life
                dCryptStats['avg'] += iCap * iCount
                if iCap > dCryptStats['max']:
                    dCryptStats['max'] = iCap
                if iCap < dCryptStats['min']:
                    dCryptStats['min'] = iCap
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
            oCard, sSet = tKey
            if not is_crypt_card(oCard):
                aTypes = sorted([x.name for x in oCard.cardtype])
                # Looks like it should be the right thing, but may not
                sTypeString = "/".join(aTypes)
                # We want to be able to sort over types easily, so
                # we add them to the keys
                dLib[(oCard, sTypeString, sSet)] = iCount
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
            aDisc.sort()  # May not be needed
            return " ".join(aDisc)
        elif len(oCard.virtue) > 0:
            return " ".join(sorted([x.name for x in oCard.virtue]))
        return ""

    def _get_ardb_exp_name(self, oPhysCard):
        """Extract the correct ARDB name for the expansion"""
        # pylint: disable-msg=E1101
        # IAbstractCard confuses pylint
        if oPhysCard.expansion:
            oExpansion = oPhysCard.expansion
        else:
            oAbsCard = IAbstractCard(oPhysCard)
            # ARDB doesn't have a concept of 'No expansion', so we
            # need to fake it. We use the first legitimate expansion
            # We sort the list to ensure stable results across databases, etc.
            aExp = sorted([oP.expansion for oP in oAbsCard.rarity],
                    key=lambda x: x.shortname)
            oExpansion = aExp[0]
        sSet = escape_ardb_expansion_name(oExpansion)
        return sSet
