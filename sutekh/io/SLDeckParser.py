# SLDeckParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Secret Library Deck Parser
# Copyright 2009 Simon Cross <hodgestar+sutekh@gmail.com>
# GPL - see COPYING for details

"""Parser for Secret Library Web API deck format.

   For a description of the format see the Secret Library API at
   http://www.secretlibrary.info/api.php.

   The example deck given in the API documentation is:

   ***SL***TITLE***
   NAME OF THE DECK
   ***SL***AUTHOR***
   CREATOR OF THE DECK
   ***SL***CREATED***
   YYYY-MM-DD
   ***SL***DESCRIPTION***
   DESCRIPTION OF THE DECK
   MAY SPAN ON MULTIPLE LINES
   ***SL***CRYPT***
   2 Count Germaine
   2 Count Germaine (Adv)
   2 Fran\xc3\xa7ois Warden Loehr
   ***SL***LIBRARY***
   10 Cloak the Gathering
   2 Coven, The
   2 Carlton Van Wyk (Hunter)
   ***SL***ENDDECK***
   """

import re
from sutekh.core.SutekhObjects import csv_to_canonical
from sutekh.io.IOBase import CardSetParser


class SLDeckParser(CardSetParser):
    """Parser for the Secret Library Web API deck format."""

    oCardLineRegexp = re.compile('^(?P<num>[0-9]+)\s+(?P<name>.*)$')

    def __init__(self):
        # pylint: disable-msg=W0231
        # No need to call IOBase.__init__()
        self._dSectionParsers = {
            'title': self._title_section,
            'author': self._author_section,
            'created': self._created_section,
            'description': self._description_section,
            'crypt': self._crypt_section,
            'library': self._library_section,
            'enddeck': self._no_section,
        }

    # section parsers

    def _switch_section(self, sLine):
        """Return a new section parser based on the given heading line."""
        sSection = sLine[len('***SL***'):-len('***')].lower()
        if sSection in self._dSectionParsers:
            return self._dSectionParsers[sSection]
        else:
            raise IOError('Unknown section heading in Secret'
                ' Library Deck Format')

    # pylint: disable-msg=R0201
    # Making these functions for clarity
    def _no_section(self, _sLine, _oHolder):
        """Initial parser -- seeing a line here is an error."""
        raise IOError('Data line outside of section'
            ' for Secret Library Deck format')

    def _title_section(self, sLine, oHolder):
        """Parse a title line."""
        oHolder.name = sLine

    def _author_section(self, sLine, oHolder):
        """Parse an author line."""
        oHolder.author = sLine

    def _created_section(self, sLine, oHolder):
        """Parse a created section line."""
        sCreatedLine = "Created on %s" % (sLine,)
        if oHolder.comment:
            oHolder.comment += "\n" + sCreatedLine
        else:
            oHolder.comment = sCreatedLine

    def _description_section(self, sLine, oHolder):
        """Parse a description line. """
        if oHolder.comment:
            oHolder.comment += "\n" + sLine
        else:
            oHolder.comment = sLine

    # pylint: enable-msg=R0201

    def _crypt_section(self, sLine, oHolder):
        """Parse a crypt entry."""
        oMatch = self.oCardLineRegexp.match(sLine)
        if oMatch is None:
            raise IOError('Unrecognised crypt line for Secrety Library'
                ' deck format')
        iNum = int(oMatch.group('num'))
        sName = oMatch.group('name')

        # Fix advanced
        if sName.endswith('(Adv)'):
            sName = sName.replace('(Adv)', '(Advanced)')

        # Avoid going down the exception path in IAbstractCard if we can
        sName = csv_to_canonical(sName)

        # Secret Library has no expansion info
        oHolder.add(iNum, sName, None)

    def _library_section(self, sLine, oHolder):
        """Parse a library entry."""
        oMatch = self.oCardLineRegexp.match(sLine)
        if oMatch is None:
            raise IOError('Unrecognised library line for Secrety Library'
                ' deck format')
        iNum = int(oMatch.group('num'))
        sName = oMatch.group('name')

        # Avoid going down the exception path in IAbstractCard if we can
        sName = csv_to_canonical(sName)

        # Secret Library has no expansion info
        oHolder.add(iNum, sName, None)

    def parse(self, fIn, oHolder):
        """Parse the SL deck in fIn into oHolder."""
        fLineParser = self._no_section

        for sLine in fIn:
            sLine = sLine.strip()
            if not sLine:
                # skip blank lines
                continue

            if sLine.startswith('***'):
                fLineParser = self._switch_section(sLine)
            else:
                fLineParser(sLine, oHolder)
