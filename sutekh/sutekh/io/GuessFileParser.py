# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# ELDB HTML Deck Parser
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Attempt to gues the correct format from Sutekh's available parsers."""

from sutekh.base.io.BaseGuessFileParser import BaseGuessFileParser

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
from sutekh.io.SLInventoryParser import SLInventoryParser


class GuessFileParser(BaseGuessFileParser):
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
