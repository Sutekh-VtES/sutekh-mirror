# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Writer for the FELDB inventory format.

   Example:

   "ELDB - Inventory"
   "Aabbt Kindred",1,0,"","Crypt"
   "Aaron Duggan, Cameron`s Toady",0,0,"","Crypt"
   ...
   "Zip Line",0,0,"","Library"
   """

from sutekh.base.core.BaseTables import AbstractCard
from sutekh.base.core.BaseAdapters import IAbstractCard
from sutekh.SutekhUtility import is_crypt_card
from sutekh.core.ELDBUtilities import norm_name, type_of_card


class WriteELDBInventory:
    """Create a string in ELDB inventory format representing a card set."""

    # pylint: disable=no-self-use
    # method for consistency with the other methods
    def _gen_header(self):
        """Generate an ELDB inventory file header."""
        return '"ELDB - Inventory"'

    def _gen_inv(self, oHolder):
        """Process the card set, creating the lines as needed"""
        dCards = {}
        aSeen = set()
        sResult = ""
        for oCard in AbstractCard.select():
            dCards[oCard] = 0
        for oCard in oHolder.cards:
            oAbsCard = IAbstractCard(oCard)
            dCards[oAbsCard] += 1
        # We sort to ensure we process multi-group cards in the right order
        for oCard in sorted(dCards, key=lambda x: x.name):
            iNum = dCards[oCard]
            sName = norm_name(oCard)
            # FIXME: It's not clear if ELDB is still being developed enough
            # to support the multi-group vampires, but we try this anyway
            if sName in aSeen and is_crypt_card(oCard):
                sName = f'{sName} (Group {oCard.group})'
            aSeen.add(sName)
            sResult += '"%s",%d,0,"","%s"\n' % (sName, iNum,
                                                type_of_card(oCard))
        return sResult

    # pylint: enable=no-self-use

    def write(self, fOut, oHolder):
        """Takes file object + card set to write, and writes an ELDB inventory
           representing the deck"""
        fOut.write(self._gen_header())
        fOut.write("\n")
        fOut.write(self._gen_inv(oHolder))
