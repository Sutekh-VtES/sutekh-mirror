# GuessFileParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# ELDB HTML Deck Parser
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Attempt to guess the file format from the first few lines, and then
   chain to the correct Parser"""

import StringIO
from sutekh.core.CardSetHolder import CardSetHolder

from sutekh.io.AbstractCardSetParser import AbstractCardSetParser
from sutekh.io.PhysicalCardSetParser import PhysicalCardSetParser
from sutekh.io.PhysicalCardParser import PhysicalCardParser
from sutekh.io.ARDBXMLDeckParser import ARDBXMLDeckParser
from sutekh.io.ARDBXMLInvParser import ARDBXMLInvParser
from sutekh.io.ARDBTextParser import ARDBTextParser
from sutekh.io.JOLDeckParser import JOLDeckParser
from sutekh.io.ELDBInventoryParser import ELDBInventoryParser
from sutekh.io.ELDBDeckFileParser import ELDBDeckFileParser
from sutekh.io.ELDBHTMLParser import ELDBHTMLParser
from sutekh.io.LackeyDeckParser import LackeyDeckParser
from sutekh.io.SLDeckParser import SLDeckParser
from sutekh.io. SLInventoryParser import  SLInventoryParser


class GuessFileParser(object):
    """Parser which guesses the file type"""

    PARSERS = [
            PhysicalCardSetParser,
            AbstractCardSetParser,
            PhysicalCardParser,
            ARDBXMLDeckParser,
            ARDBXMLInvParser,
            ARDBTextParser,
            ELDBInventoryParser,
            ELDBDeckFileParser,
            ELDBHTMLParser,
            SLDeckParser,
            SLInventoryParser,
            LackeyDeckParser,
            # JOL is the most permissive, so must be last
            JOLDeckParser,
            ]

    def __init__(self):
        self.oChosenParser = None

    def guess_format(self, oFile):
        """Handle the guessing"""
        for cParser in self.PARSERS:
            oHolder = CardSetHolder()
            oFile.seek(0)
            oParser = cParser()
            try:
                oParser.parse(oFile, oHolder)
            except IOError:
                # error from the parser, so probably not right
                continue
            if oHolder.num_entries == 0:
                # No cards, so we don't trust this result
                continue
            return oParser
        return None

    def parse(self, fIn, oHolder):
        """attempt arse a file into the given holder"""
        # Cache file, (for network cases, etc.)
        # Is this completely safe?
        oCopy = StringIO.StringIO(fIn.read())
        # Save choice, so it can be reported to the user if need be
        self.oChosenParser = self.guess_format(oCopy)
        if not self.oChosenParser:
            raise IOError('Unable to identify the file format')
        oCopy.seek(0)
        self.oChosenParser.parse(oCopy, oHolder)
