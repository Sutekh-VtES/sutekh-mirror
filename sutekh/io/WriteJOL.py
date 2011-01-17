# WriteJOL.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Writer for the JOL format.

   We use the "Num"x"Name" format for created decks, as being shorter

   Example:

   4xVampire 1
   Vampire 2
   2xVampire 3

   2xLib Name

   """

from sutekh.core.SutekhObjects import IAbstractCard
from sutekh.core.ELDBUtilities import type_of_card


class WriteJOL(object):
    """Create a string in JOL format representing a card set."""

    # pylint: disable-msg=R0201
    # method for consistency with the other methods

    def _escape(self, sName):
        """Escape the card name to JOL's requirements"""
        sName = sName.replace('(Advanced)', '(advanced)')
        return sName

    # pylint: enable-msg=R0201
    def _gen_inv(self, oHolder):
        """Process the card set, creating the lines as needed"""
        # pylint: disable-msg=E1101
        # pyprotocols confuses pylint
        dCards = {'Crypt': {}, 'Library': {}}
        sResult = ""
        for oCard in oHolder.cards:
            oAbsCard = IAbstractCard(oCard)
            sType = type_of_card(oAbsCard)
            sName = self._escape(oAbsCard.name)
            dCards[sType].setdefault(sName, 0)
            dCards[sType][sName] += 1
        # Sort the output
        for sType in dCards:
            for sName, iNum in sorted(dCards[sType].items()):
                if iNum > 1:
                    sResult += '%dx%s\n' % (iNum, sName)
                else:
                    sResult += '%s\n' % sName
            if sType == 'Crypt':
                sResult += '\n'
        # Assume conversion will be handled by viewers/editor/web browser?
        return sResult

    # pylint: enable-msg=R0201

    def write(self, fOut, oHolder):
        """Takes file object + card set to write, and writes an JOL deck
           representing the deck"""
        fOut.write(self._gen_inv(oHolder))
