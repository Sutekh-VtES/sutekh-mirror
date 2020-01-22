# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# ELDB HTML Deck Parser
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Base class for a guessing file parser.

   Handles the logic around trying to parse the card set with multiple
   parsers.
   """

from io import StringIO
from ..core.CardSetHolder import CardSetHolder


class BaseGuessFileParser:
    """Parser which guesses the file type"""

    # Subclasses should provide this list
    PARSERS = []

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
        # We assume we've wrapped file in an EncodedFile or otherwise
        # ensured the encoding is sane
        # Is this completely safe?
        oCopy = StringIO(fIn.read())
        # Save choice, so it can be reported to the user if need be
        self.oChosenParser = self.guess_format(oCopy)
        if not self.oChosenParser:
            raise IOError('Unable to identify the file format')
        oCopy.seek(0)
        self.oChosenParser.parse(oCopy, oHolder)
