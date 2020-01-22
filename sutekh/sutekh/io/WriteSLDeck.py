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
    u'Carlton Van Wyk': 'Carlton Van Wyk (Hunter)',
    u"Jake Washington": "Jake Washington (Hunter)",
    u'Pentex™ Loves You!': 'Pentex(TM) Loves You!',
    u'Pentex™ Subversion': 'Pentex(TM) Subversion',
    u'Nephandus': 'Nephandus (Mage)',
    u'Shadow Court Satyr': 'Shadow Court Satyr (Changeling)',
    u'Amam the Devourer': 'Amam the Devourer (Bane Mummy)',
    u'Wendell Delburton': 'Wendell Delburton (Hunter)',
    u'Dauntain Black Magician': 'Dauntain Black Magician (Changeling)',
    u"Bang Nakh — Tiger's Claws": "Bang Nakh -- Tiger's Claws",
    u"Neighborhood Watch Commander": "Neighborhood Watch Commander (Hunter)",
    u"Mylan Horseed": "Mylan Horseed (Goblin)",
    u"Sacré-Cœur Cathedral, France": "Sacre Cour Cathedral, France",
    u"Ambrosius, The Ferryman": "Ambrosius, The Ferryman (Wraith)",
    u"C\xe9leste Lamontagne": u"C\xe9l\xe8ste Lamontagne",
    u"L'\xc9puisette": "L'Epuisette",
    u"Puppeteer": "Puppeteer (Wraith)",
    u"S\xe9bastien Goulet": u"S\xe9bastian Goulet",
    u"S\xe9bastien Goulet (Adv)": u"S\xe9bastian Goulet (Adv)",
    u"Akhenaten, The Sun Pharaoh": "Akhenaten, The Sun Pharaoh (Mummy)",
    u"Tutu the Doubly Evil One": "Tutu the Doubly Evil One (Bane Mummy)",
    u"Veneficti": "Veneficti (Mage)",
    u"Brigitte Gebauer": "Brigitte Gebauer (Wraith)",
    u"\xc9tienne Fauberge": "Etienne Fauberge",
    u'Kherebutu': 'Kherebutu (Bane Mummy)',
    u'Qetu the Evil Doer': 'Qetu the Evil Doer (Bane Mummy)',
    u"Saatet-ta": u"Saatet-ta (Bane Mummy)",
    u"Mehemet of the Ahl-i-Batin": "Mehemet of the Ahl-i-Batin (Mage)",
    u"Draeven Softfoot": "Draeven Softfoot (Changeling)",
    u"Felix Fix Hessian": "Felix Fix Hessian (Wraith)",
    u"Thadius Zho": "Thadius Zho, Mage",
}


class WriteSLDeck:
    """Create a string in SL import format representing a card set."""

    # pylint: disable=no-self-use
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

    # pylint: enable=no-self-use
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

    # pylint: enable=no-self-use

    def write(self, fOut, oHolder):
        """Takes file object + card set to write, and writes an JOL deck
           representing the deck"""
        fOut.write(self._gen_sl_deck(oHolder))
