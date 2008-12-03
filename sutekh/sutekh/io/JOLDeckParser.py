# JOLDeckParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# ELDB Deck File Parser
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Parser for JOL deck format"""

# pylint: disable-msg=W0402
# string.digits is OK
import string

class JOLDeckParser(object):
    """Parser for the JOL Deck format."""

    def __init__(self, oHolder):
        self._oHolder = oHolder

    def reset(self):
        """Reset the parser state"""
        pass

    def feed(self, sLine):
        """Feed the next line to the parser and extract the cards"""
        # FIXME: This assumes that WW will not produce a card starting with
        # a numeral  - this is dangerous
        sLine = sLine.strip()
        if not sLine:
            # skip blank lines
            return
        if sLine[0] in string.digits:
            sNum, sName = sLine.split('x', 1)
            iNum = int(sNum)
        else:
            iNum = 1
            sName = sLine
        # JOL has no expansion info
        self._oHolder.add(iNum, sName, None)
