# ELDBInventoryParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# ELDB Inventory Parser
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Parser for ELDB inventory format"""


import re
from sutekh.core.ELDBUtilities import gen_name_lookups

class ELDBInventoryParser(object):
    """Parser for the ELDB Inventory format."""

    # Should this be based on CSVParser?
    _oCardRe = re.compile(r'\s*"(?P<name>[^"]*)"\s*,\s*(?P<cnt>[0-9]+)')

    def __init__(self, oHolder):
        self._oHolder = oHolder
        # No name info in the file - user will have to sort this out
        self._oHolder.name = ""
        self._dNameCache = gen_name_lookups()

    def feed(self, sLine):
        """Handle line by line data"""
        if sLine.strip().startswith('"ELDB - Inv'):
            # Skip header
            return
        oMatch = self._oCardRe.match(sLine)
        if oMatch:
            iCnt = int(oMatch.group('cnt'))
            sName = oMatch.group('name').strip()
            if sName in self._dNameCache:
                sName = self._dNameCache[sName]
            if iCnt:
                # ELDB will create 0 entries
                self._oHolder.add(iCnt, sName, None)
