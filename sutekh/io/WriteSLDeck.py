# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Writer for the Secret Library 'import a deck' web form.

   Example:

   Deck Name: My Deck
   Author: Someone

   Crypt
   ----
   1 Vampire 1
   2 Vampire 2

   Library
   ----
   1 Lib Name
   2 Lib2, The
   """

from sutekh.base.core.BaseAdapters import IAbstractCard
from sutekh.base.Utility import move_articles_to_back
from sutekh.SutekhUtility import is_crypt_card


# Variations between SL names and the official card list
SL_FIXES = {
    'Carlton Van Wyk': 'Carlton Van Wyk (Hunter)',
}


class WriteSLDeck(object):
    """Create a string in SL import format representing a card set."""

    # pylint: disable=R0201
    # method for consistency with the other methods

    def _escape(self, sName):
        """Escape the card name to SL's requirements"""
        if sName in SL_FIXES:
            sName = SL_FIXES[sName]
        sName = move_articles_to_back(sName)
        sName = sName.replace('(Advanced)', '(Adv)')
        sName = sName.replace('"', '')
        return sName

    def _gen_header(self, oHolder):
        """Add the header"""
        return ("Deck Name: %s\n"
                "Author: %s\n"
                "Description:\n%s\n" % (oHolder.name,
                                        oHolder.author,
                                        oHolder.comment))

    def _gen_card_list(self, dCards):
        """Return a list, sorted by name, with the numbers."""
        aResult = []
        for sName in sorted(dCards):
            aResult.append('%d %s\n' % (dCards[sName], sName))
        return ''.join(aResult)

    # pylint: enable=R0201
    def _gen_sl_deck(self, oHolder):
        """Process the card set, creating the lines as needed"""
        # Add the header information
        sResult = self._gen_header(oHolder)
        dCards = {'Crypt': {}, 'Library': {}}
        for oCard in oHolder.cards:
            oAbsCard = IAbstractCard(oCard)
            if is_crypt_card(oAbsCard):
                sType = 'Crypt'
            else:
                sType = 'Library'
            sName = self._escape(oAbsCard.name)
            dCards[sType].setdefault(sName, 0)
            dCards[sType][sName] += 1
        sResult += 'Crypt\n---\n'
        sResult += self._gen_card_list(dCards['Crypt'])
        sResult += '\nLibrary\n---\n'
        sResult += self._gen_card_list(dCards['Library'])
        # Assume conversion will be handled by viewers/editor/web browser?
        return sResult

    # pylint: enable=R0201

    def write(self, fOut, oHolder):
        """Takes file object + card set to write, and writes an JOL deck
           representing the deck"""
        fOut.write(self._gen_sl_deck(oHolder))
