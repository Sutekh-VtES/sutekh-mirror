# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Lackey Deck File Parser
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Parser for Lackey CCG deck format"""

# pylint: disable=deprecated-module
# string.digits is OK
import string
# pylint: enable=deprecated-module
from sutekh.base.core.BaseTables import AbstractCard
from sutekh.io.WriteLackeyCCG import lackey_name
from sutekh.base.io.IOBase import BaseLineParser


def gen_name_lookups():
    """Create a lookup table to map Lackey CCG names to Sutekh names -
       reduces the number of user queries"""
    dNameCache = {}
    for oCard in AbstractCard.select():
        sSutekhName = oCard.name
        sLackeyName = lackey_name(oCard)
        if sLackeyName != sSutekhName:
            # Since we will need to check wether a card is in the dictionary
            # anyway (missed cases, etc), there's no point in having the
            # identity entries
            dNameCache[sLackeyName] = sSutekhName
    return dNameCache


class LackeyDeckParser(BaseLineParser):
    """Parser for the Lackey Deck format."""

    def __init__(self):
        super().__init__()
        self._dNameCache = gen_name_lookups()

    def _feed(self, sLine, oHolder):
        """Read the line into the given CardSetHolder"""
        if sLine[0] in string.digits:
            # Split on any whitespace
            sNum, sName = sLine.split(None, 1)
            try:
                iNum = int(sNum)
            except ValueError:
                # pylint: disable=raise-missing-from
                # We don't need the ValueError details here.
                raise IOError("Illegal number %s for Lackey CCG deck" % sNum)
            if sName in self._dNameCache:
                sName = self._dNameCache[sName]
        elif sLine != 'Crypt:':
            raise IOError("Illegal string %s for Lackey CCG deck" % sLine)
        else:
            # Skip the 'Crypt:' line
            return
        # Lackey has no expansion info
        oHolder.add(iNum, sName, None, None)
