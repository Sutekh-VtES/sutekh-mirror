# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Writer for pmwiki lists

   Example deck:

   (:title Example deck by Auth :)

   !! Description
   Followers of Set Preconstructed Starter from Lords of the Night.

   http://www.white-wolf.com/vtes/index.php?line=Checklist_LordsOfTheNight

   !! Notes

   (annotations)

   !! Crypt [12 vampires]
   2x Nakhthorheb
   ...

   !! Library [77 cards]

   !!! Action [20]
     2x Blithe Acceptance
     4x Dream World
   ...
   """

from sutekh.core.ArdbInfo import ArdbInfo


class WritePmwiki(ArdbInfo):
    """Create a string in pmwiki format representing a dictionary of cards."""

    # pylint: disable=no-self-use
    # method for consistency with the other methods
    def _gen_header(self, oHolder):
        """Generate an pmwiki header."""
        return ("(:title %s by %s :)\n\n"
                "!! Description\n%s\n"
                "!! Notes\n%s\n" % (oHolder.name, oHolder.author,
                                    oHolder.comment, oHolder.annotations))
    # pylint: enable=no-self-use

    def _gen_crypt(self, dCards):
        """Generate an pmwiki crypt description.

           dCards is mapping of (card id, card name) -> card count.
           """
        (dVamps, dCryptStats) = self._extract_crypt(dCards)
        dCombinedVamps = self._group_sets(dVamps)

        sCrypt = "!! Crypt [%(size)d vampires]\n" % dCryptStats

        aCryptLines = []
        for oCard, (iCount, _sSet) in sorted(dCombinedVamps.items(),
                                             key=self._crypt_sort_key):
            dLine = self._format_crypt_line(oCard, iCount)
            aCryptLines.append(dLine)

        for dLine in aCryptLines:
            sCurLine = " %(count)dx %(name)s %(adv)s" % dLine
            sCrypt += sCurLine.rstrip() + '\n'

        return sCrypt

    def _gen_library(self, dCards):
        """Generaten an pmwiki library description.

           dCards is mapping of (card id, card name) -> card count.
           """
        (dLib, iLibSize) = self._extract_library(dCards)
        dCombinedLib = self._group_sets(dLib)
        dTypes = self._group_types(dCombinedLib)

        sLib = "!! Library [%d cards]\n\n" % (iLibSize,)

        for sTypeString in sorted(dTypes):
            dCards = dTypes[sTypeString]
            iTotal = sum(dCards.values())

            sLib += "!!! %s [%d]\n" % (sTypeString, iTotal)

            for oCard, iCount in sorted(dCards.items(),
                                        key=lambda x: x[0].name):
                sLib += " %dx %s\n" % (iCount, oCard.name)

            sLib += "\n"

        return sLib

    def write(self, fOut, oHolder):
        """Takes filename, deck details and a dictionary of cards, of the
           form dCard[(id, name, set)] = count and writes the file."""
        # We don't encode strange characters, and just write the unicode string
        # to file. This looks to match ARDB's behaviour (tested against
        # ARDB version 2.8
        dCards = self._get_cards(oHolder.cards)
        fOut.write(self._gen_header(oHolder))
        fOut.write("\n")
        fOut.write(self._gen_crypt(dCards))
        fOut.write("\n")
        fOut.write(self._gen_library(dCards))
