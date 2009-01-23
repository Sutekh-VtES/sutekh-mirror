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

class WriteJOL(object):
    """Create a string in JOL format representing a card set."""

    # pylint: disable-msg=R0201
    # method for consistency with the other methods

    def _escape(self, sName):
        """Escape the card name to JOL's requirements"""
        sName = sName.replace('(Advanced)', '(advanced)')
        return sName

    def _crypt_or_library(self, oCard):
        """Return 'crypt' or 'library' as required"""
        sType = list(oCard.abstractCard.cardtype)[0].name
        if sType == "Vampire" or sType == "Imbued":
            return "crypt"
        else:
            return "library"

    # pylint: enable-msg=R0201
    def _gen_inv(self, oCardSet):
        """Process the card set, creating the lines as needed"""
        dCards = {'crypt' : {}, 'library' : {}}
        sResult = ""
        for oCard in oCardSet.cards:
            sType = self._crypt_or_library(oCard)
            sName = self._escape(oCard.abstractCard.name)
            dCards[sType].setdefault(sName, 0)
            dCards[sType][sName] += 1
        # Sort the output
        for sType in dCards:
            for sName, iNum in sorted(dCards[sType].items()):
                if iNum > 1:
                    sResult += '%dx%s\n' % (iNum, sName)
                else:
                    sResult += '%s\n' % sName
            if sType == 'crypt':
                sResult += '\n'
        # Assume conversion will be handled by viewers/editor/web browser?
        return sResult

    # pylint: enable-msg=R0201

    def write(self, fOut, oCardSet):
        """Takes file object + card set to write, and writes an JOL deck
           representing the deck"""
        fOut.write(self._gen_inv(oCardSet))
