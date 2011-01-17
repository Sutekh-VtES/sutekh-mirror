# ELDBInventoryParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# ELDB Inventory Parser
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Parser for ELDB inventory format"""


import re
from sutekh.core.ELDBUtilities import gen_name_lookups
from sutekh.io.IOBase import BaseLineParser


class ELDBInventoryParser(BaseLineParser):
    """Parser for the ELDB Inventory format.

       The inventory file has no name info, so the holder name isn't changed
       by the parser."""

    # Should this be based on CSVParser?
    _oCardRe = re.compile(r'\s*"(?P<name>[^"]*)"\s*,\s*(?P<cnt>[0-9]+)')

    def __init__(self):
        super(ELDBInventoryParser, self).__init__()
        self._dNameCache = gen_name_lookups()

    def _feed(self, sLine, oHolder):
        """Handle line by line data"""
        # sLine is stripped by parse
        if sLine.startswith('"ELDB - Inv'):
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
                oHolder.add(iCnt, sName, None)
