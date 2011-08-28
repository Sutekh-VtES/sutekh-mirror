# WriteCSV.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Writer for the CSV format.

   Example:

   "Card Name", "Expansion", "Number"
   "Aabbt Kindred","Final Nights", 2
   "Inez ""Nurse216"" Villagrande", "Nights of Reckoning", 1
   "Aire of Elation", "Camarilla Edition", 3
   "Aire of Elation", "Anarchs", 3
   "Zip Line", "Twilight Rebellion", 3
   """


class WriteCSV(object):
    """Create a string in CSV format representing a card set."""

    def __init__(self, bIncludeHeader=True, bIncludeExpansion=True):
        self.bIncludeHeader = bIncludeHeader
        self.bIncludeExpansion = bIncludeExpansion

    def _expansion_name(self, oCard):
        """Utility function to return iether the name, or the appropriate
           placeholder for oExpansion is None."""
        if oCard.expansion and self.bIncludeExpansion:
            return oCard.expansion.name
        return 'Unknown Expansion'

    # pylint: disable-msg=R0201
    # method for consistency with the other methods
    def _gen_header(self):
        """Generate column headers."""
        if self.bIncludeHeader:
            if self.bIncludeExpansion:
                return '"Card Name", "Expansion", "Number"\n'
            else:
                return '"Card Name", "Number"\n'
        else:
            return ""

    def _gen_inv(self, oHolder):
        """Process the card set, creating the lines as needed"""
        dCards = {}
        sResult = ""
        for oCard in oHolder.cards:
            # We parse with doublequote=True so we double "'s in the card name
            tKey = (oCard.abstractCard.name.replace('"', '""'),
                    self._expansion_name(oCard))
            dCards.setdefault(tKey, 0)
            dCards[tKey] += 1
        # Sort the output
        for tKey, iNum in sorted(dCards.items(), key=lambda x: x[0]):
            if self.bIncludeExpansion:
                sResult += '"%s", "%s", %d\n' % (tKey[0], tKey[1], iNum)
            else:
                sResult += '"%s", %d\n' % (tKey[0], iNum)
        return sResult

    # pylint: enable-msg=R0201

    def write(self, fOut, oHolder):
        """Takes file object + card set to write, and writes an ELDB inventory
           representing the deck"""
        sHeader = self._gen_header()
        if sHeader:
            fOut.write(sHeader)
        fOut.write(self._gen_inv(oHolder))
