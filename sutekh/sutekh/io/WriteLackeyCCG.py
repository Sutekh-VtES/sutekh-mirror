# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
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

from sutekh.core.ELDBUtilities import type_of_card
from sutekh.SutekhUtility import is_crypt_card, strip_group_from_name
from sutekh.base.core.BaseAdapters import IAbstractCard
from sutekh.base.core.BaseTables import AbstractCard
from sutekh.base.Utility import move_articles_to_back, to_ascii


def make_unique_names():
    """Create the list of unique crypt card names"""
    aUnique = set()
    for oCard in AbstractCard.select().orderBy('canonicalName'):
        if not is_crypt_card(oCard):
            continue
        sBaseName = strip_group_from_name(oCard.name)
        if sBaseName in aUnique:
            aUnique.add(oCard.name)
        else:
            aUnique.add(sBaseName)
    return aUnique


def lackey_name(oCard, aUnique):
    """Escape the card name to Lackey CCG's requirements"""
    sName = oCard.name
    if oCard.level is not None:
        sName = sName.replace("(Advanced)", "Adv.")
    # Lackey uses (GX) postfix for the new vampires, but old
    # versions have no suffix
    if is_crypt_card(oCard):
        if sName in aUnique:
            sName = sName.replace('(Group ', '(G')
        else:
            sName = strip_group_from_name(sName)
    sName = move_articles_to_back(sName)
    # Lackey handles double-quotes a bit oddly, so we must as well
    if oCard.cardtype[0].name == 'Imbued':
        # Lackey only uses '' for Imbued
        sName = sName.replace('"', "''")
    else:
        sName = sName.replace('"', "'")
    # Bounce through ascii to strip accents, etc.
    return to_ascii(sName)


class WriteLackeyCCG:
    """Create a string in Lackey CCG format representing a card set."""

    # pylint: disable=no-self-use
    # Method for consistency
    def _gen_inv(self, oHolder):
        """Process the card set, creating the lines as needed"""
        aUnique = make_unique_names()
        dCards = {'Crypt': {}, 'Library': {}}
        sResult = ""
        for oCard in oHolder.cards:
            sType = type_of_card(IAbstractCard(oCard))
            sName = lackey_name(IAbstractCard(oCard), aUnique)
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

    # pylint: enable=no-self-use

    def write(self, fOut, oHolder):
        """Takes file object + card set to write, and writes an Lackey CCG
           deck representing the card set"""
        fOut.write(self._gen_inv(oHolder))
