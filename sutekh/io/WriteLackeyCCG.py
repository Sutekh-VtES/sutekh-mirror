# WriteLackeyCCG.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Writer for the Lackey CCG file format.
     (AFAICT, the tabs aren't required, but Lackey uses them, so I'm playing
      safe)

   Example:

   2\tCard 1
   3\tCard 2
   1\tCard 3
   Crypt:
   1\tVampire 1
   2\tVampire 2


   """

import unicodedata
from sutekh.core.ELDBUtilities import type_of_card
from sutekh.core.SutekhObjects import canonical_to_csv, IAbstractCard


def lackey_name(oCard):
    """Escape the card name to Lackey CCG's requirements"""
    sName = oCard.name
    if oCard.level is not None:
        sName = sName.replace("(Advanced)", "Adv.")
    sName = canonical_to_csv(sName)
    # Lackey handles double-quotes a bit oddly, so we must as well
    if oCard.cardtype[0].name == 'Imbued':
        # Lackey only uses '' for Imbued
        sName = sName.replace('"', "''")
    else:
        sName = sName.replace('"', "'")
    sName = unicodedata.normalize('NFKD', sName).encode('ascii', 'ignore')
    return sName


class WriteLackeyCCG(object):
    """Create a string in Lackey CCG format representing a card set."""

    # pylint: disable-msg=R0201
    # Method for consistency
    def _gen_inv(self, oHolder):
        """Process the card set, creating the lines as needed"""
        dCards = {'Crypt': {}, 'Library': {}}
        sResult = ""
        for oCard in oHolder.cards:
            sType = type_of_card(IAbstractCard(oCard))
            sName = lackey_name(IAbstractCard(oCard))
            dCards[sType].setdefault(sName, 0)
            dCards[sType][sName] += 1
        # Sort the output
        # Need to be in this order
        for sType in ['Library', 'Crypt']:
            for sName, iNum in sorted(dCards[sType].items()):
                sResult += '%d\t%s\n' % (iNum, sName)
            if sType == 'Library':
                sResult += 'Crypt:\n'
        return sResult

    # pylint: enable-msg=R0201

    def write(self, fOut, oHolder):
        """Takes file object + card set to write, and writes an Lackey CCG
           deck representing the card set"""
        fOut.write(self._gen_inv(oHolder))
