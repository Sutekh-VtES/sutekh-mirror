# WriteELDBDeckFile.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Writer for the FELDB deck format.

   Example:

   "A Deck"
   "Author"
   "Description"
   2
   "Alexandra"
   "Bronwen"
   5
   "Aire of Elation"
   "Aire of Elation"
   "Social Charm"
   "Social Charm"
   "Social Charm"
   """

from sutekh.core.ELDBUtilities import norm_name

class WriteELDBDeckFile(object):
    """Create a string in ELDB deck format representing a card set."""

    # pylint: disable-msg=R0201
    # method for consistency with the other methods
    def _gen_header(self, oCardSet):
        """Generate an ELDB deck file header."""
        return '"%s"\n' \
               '"%s"\n' \
               '"%s"\n' % (oCardSet.name, oCardSet.author, oCardSet.comment)

    def _gen_inv(self, oCardSet):
        """Process the card set, creating the lines as needed"""
        aCrypt = []
        aLib = []
        for oCard in oCardSet.cards:
            oAbsCard = oCard.abstractCard
            sType = list(oAbsCard.cardtype)[0].name
            sName = norm_name(oAbsCard)
            if sType == "Vampire" or sType == "Imbued":
                aCrypt.append(sName)
            else:
                aLib.append(sName)
        aCrypt.sort()
        aLib.sort()
        sResult = "%d\n" % len(aCrypt)
        for sName in aCrypt:
            sResult += '"%s"\n' % sName
        sResult += "%d\n" % len(aLib)
        for sName in aLib:
            sResult += '"%s"\n' % sName
        return sResult

    # pylint: enable-msg=R0201

    def write(self, fOut, oCardSet):
        """Takes file object + card set to write, and writes an ELDB inventory
           representing the deck"""
        fOut.write(self._gen_header(oCardSet))
        fOut.write(self._gen_inv(oCardSet))
