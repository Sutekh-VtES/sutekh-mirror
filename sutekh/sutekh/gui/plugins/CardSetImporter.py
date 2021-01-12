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

    sMenuName = "Import ARDB, JOL or ELDB Card Set"

    sHelpCategory = "card_list:file"

    sHelpText = """This allows you to import files produced by ARDB, JOL,
                   Lackey CCG or FELDB.  While Sutekh will attempt
                   to identify the file format automatically, this
                   isn't always reliable, so you have the option of
                   specifying the format manually.

                   For some types of file, such as ARDB inventories, you
                   will also need to specify a card set name for the
                   imported file.

                   If the name of the card set clashes with an existing
                   name, you will be asked to rename the imported card
                   set or cancel the import.

                   If no cards are found in the card set, the card set
                   will not be created."""

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

    @classmethod
    def get_help_list_text(cls):
        return """Import a file saved by another deck management tool. \
                  You may specify the correct type of file as \
                  well as the file name."""


plugin = CardSetImporter
