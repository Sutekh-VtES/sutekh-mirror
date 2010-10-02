# JOLDeckParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# JOL Deck File Parser
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Parser for JOL deck format"""

import re
from sutekh.core.SutekhObjects import csv_to_canonical
from sutekh.io.IOBase import BaseLineParser


class JOLDeckParser(BaseLineParser):
    """Parser for the JOL Deck format."""

    oCardLineRegexp = re.compile('((?P<num>[0-9]+)(\s)*x(\s)*)?(?P<name>.*)$')

    def _feed(self, sLine, oHolder):
        """Read the line into the given CardSetHolder"""
        oMatch = self.oCardLineRegexp.match(sLine)
        if oMatch is not None:
            dResults = oMatch.groupdict()
            if dResults['num']:
                iNum = int(dResults['num'])
            else:
                iNum = 1
            sName = dResults['name']
        else:
            # error condition
            raise IOError('Unrecognised line for JOL format')
        # Unescape names
        if sName.endswith('(advanced)'):
            sName = sName.replace('(advanced)', '(Advanced)')
        # Avoid going down the exception path in IAbstractCard if we can
        sName = csv_to_canonical(sName)
        # JOL has no expansion info
        oHolder.add(iNum, sName, None)
