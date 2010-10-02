# WriteELDBInventory.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
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

from sutekh.core.SutekhObjects import AbstractCard, IAbstractCard
from sutekh.core.ELDBUtilities import norm_name, type_of_card


class WriteELDBInventory(object):
    """Create a string in ELDB inventory format representing a card set."""

    # pylint: disable-msg=R0201
    # method for consistency with the other methods
    def _gen_header(self):
        """Generate an ELDB inventory file header."""
        return '"ELDB - Inventory"'

    def _gen_inv(self, oHolder):
        """Process the card set, creating the lines as needed"""
        dCards = {}
        sResult = ""
        for oCard in AbstractCard.select():
            dCards[oCard] = 0
        for oCard in oHolder.cards:
            oAbsCard = IAbstractCard(oCard)
            dCards[oAbsCard] += 1
        for oCard, iNum in dCards.iteritems():
            sResult += '"%s",%d,0,"","%s"\n' % (norm_name(oCard), iNum,
                    type_of_card(oCard))
        return sResult

    # pylint: enable-msg=R0201

    def write(self, fOut, oHolder):
        """Takes file object + card set to write, and writes an ELDB inventory
           representing the deck"""
        fOut.write(self._gen_header())
        fOut.write("\n")
        fOut.write(self._gen_inv(oHolder))
