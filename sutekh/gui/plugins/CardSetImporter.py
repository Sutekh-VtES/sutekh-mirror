# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>,
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Convert a ELDB or ARDB text or html file into an Card Set."""

from sutekh.io.ELDBHTMLParser import ELDBHTMLParser
from sutekh.io.ARDBTextParser import ARDBTextParser
from sutekh.io.ARDBXMLDeckParser import ARDBXMLDeckParser
from sutekh.io.ARDBXMLInvParser import ARDBXMLInvParser
from sutekh.io.ELDBDeckFileParser import ELDBDeckFileParser
from sutekh.io.ELDBInventoryParser import ELDBInventoryParser
from sutekh.io.JOLDeckParser import JOLDeckParser
from sutekh.io.LackeyDeckParser import LackeyDeckParser
from sutekh.io.GuessFileParser import GuessFileParser
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.base.gui.plugins.BaseImport import BaseImport, GUESS_FILE_FORMAT


class CardSetImporter(SutekhPlugin, BaseImport):
    """Convert a HTML or text deck into an card set.

       Handles most of the common formats.
       """
    PARSERS = {
        'ELDB HTML File': (ELDBHTMLParser, 'HTML files', ['*.html', '*.htm']),
        'ARDB Text File': (ARDBTextParser, 'TXT files', ['*.txt']),
        'ELDB Deck (.eld)': (ELDBDeckFileParser, 'ELD files', ['*.eld']),
        'ELDB Inventory': (ELDBInventoryParser, None, None),
        'ARDB Deck XML File': (ARDBXMLDeckParser, 'XML files', ['*.xml']),
        'ARDB Inventory XML File': (ARDBXMLInvParser, 'XML files', ['*.xml']),
        'JOL Deck File': (JOLDeckParser, None, None),
        'Lackey CCG Deck File': (LackeyDeckParser, None, None),
        GUESS_FILE_FORMAT: (GuessFileParser, None, None),
        }


plugin = CardSetImporter
