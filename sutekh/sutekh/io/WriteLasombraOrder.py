# WriteLasombraOrder.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Writer for the Lasombra's singles order format.

   http://www.thelasombra.com/how_to_order.htm

   X Card Name

   Library cards, sorted by expansion, rarity (rare, uncommon, common, precon),
      name

   Crypt cards, sorted by clan, name, expansion

   Example:

   Boxes
   ...

   Keepers of Tradition
   3 Ashur Tablets
   2 Ivory Bow

   Ebony Kingdom
   3 Taking the Skin: Vulture

   Crypt:
   2 Beast, The Leatherface of Detroit (BH)
   1 Christianus Lionel, The Mad Chronicler (BH)
   1 Christianus Lionel, The Mad Chronicler (SW)
   2 Mateusz Gryzbowsky (BH)
   3 Massassi

   Please quote shipping to ...
   My Paypal email address is ...
   """

from sutekh.core.SutekhObjects import IAbstractCard
from sutekh.core.ELDBUtilities import type_of_card

class WriteLasombraOrder(object):
    """Create a string representing a card set."""

    @staticmethod
    def _escape(sName):
        """Escape the card name to Lasombra's requirements"""
        sName = sName.replace('(Advanced)', '(ADV)')
        return sName

    def _split_cards(self, oHolder):
        """Seperate the cards into library, expansion, rarity, name and
           crypt, clan, name, expansion tuples."""
        # pylint: disable-msg=E1101
        # pyprotocols confuses pylint
        dCrypt = {}
        dLib = {}
        for oCard in oHolder.cards:
            if not oCard.expansion:
                raise IOError('All cards need to have an expansion specified')
            oAbsCard = IAbstractCard(oCard)
            sName = self._escape(oAbsCard.name)
            sType = type_of_card(oAbsCard)
            if sType == 'Library':
                # Need to lookup rarities for this expansion
                sExp = oCard.expansion.name
                if sExp.startswith('Promo'):
                    sExp = 'Promo'
                    sRarity = 'Promo'
                else:
                    aRarities = [oP.rarity.name for oP in oAbsCard.rarity if
                            oP.expansion == oCard.expansion]
                    if 'Rare' in aRarities:
                        sRarity = '1: Rare'
                    elif 'Uncommon' in aRarities:
                        sRarity = '2: Uncommon'
                    elif 'Common' in aRarities:
                        sRarity = '3: Common'
                    else:
                        sRarity = '4: Precon'
                dLib.setdefault(sExp, {})
                dLib[sExp].setdefault((sRarity, sName), 0)
                dLib[sExp][(sRarity, sName)] += 1
            else:
                aExpansions = set([oP.expansion.name for oP in
                    oAbsCard.rarity])
                if len(aExpansions) > 1:
                    # Only list expansions if there are multiple options
                    sExp = '(%s)' % oCard.expansion.shortname
                else:
                    sExp = ''
                sClan = [oC.name for oC in oAbsCard.clan][0]
                dCrypt.setdefault(sClan, {})
                dCrypt[sClan].setdefault((sName, sExp), 0)
                dCrypt[sClan][(sName, sExp)] += 1
        return dCrypt, dLib

    def _gen_inv(self, oHolder):
        """Process the card set"""
        dCrypt, dLib = self._split_cards(oHolder)
        sResult = 'Boxes\n\n'
        if dLib:
            for sExp in sorted(dLib):
                sResult += '%s\n' % sExp
                for (_sRarity, sName), iCnt in sorted(dLib[sExp].items()):
                    # We just use the rarity to sort on
                    sResult += '%3d %s\n' % (iCnt, sName)
                sResult += '\n'
        if dCrypt:
            sResult += 'Crypt\n'
            for sClan in sorted(dCrypt):
                for (sName, sExp), iCnt in sorted(dCrypt[sClan].items()):
                    sResult += '%3d %s %s\n' % (iCnt, sName, sExp)
        sResult += '\nPlease quote shipping to\nMy Paypal email address is\n'
        return sResult

    # pylint: enable-msg=R0201

    def write(self, fOut, oHolder):
        """Takes file object + card set to write, and writes an order"""
        fOut.write(self._gen_inv(oHolder))
