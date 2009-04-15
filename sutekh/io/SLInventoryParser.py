# SLInventoryParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Secret Library Inventory Parser
# Copyright 2009 Simon Cross <hodgestar+sutekh@gmail.com>
# GPL - see COPYING for details

"""Parser for Secret Library Web API inventory format

   For a description of the format see the Secret Library API at
   http://www.secretlibrary.info/api.php.

   The example inventory given in the API documentation is:

   ***SL***CRYPT***
   2;2;Abebe
   2;2;Alan Sovereign (Adv)
   4;3;Fran\xc3\xa7ois Warden Loehr
   ***SL***LIBRARY***
   1;1;Absimiliard's Army
   5;5;Ahriman's Demesne
   4;4;Atonement
   1;1;Textbook Damnation, The
   8;8;Watch Commander
   ***SL***ENDEXPORT***
   """

import re
from sutekh.core.SutekhObjects import csv_to_canonical

class SLInventoryParser(object):
    """Parser for the Secret Libary web API inventory format."""

    oCardLineRegexp = re.compile('^(?P<have>[0-9]+)\s*;\s*(?P<want>[0-9]+)\s*;\s*(?P<name>.*)$')

    def __init__(self, oHolder):
        self._oHolder = oHolder
        self._dSectionParsers = {
            'crypt': self._crypt_section,
            'library': self._library_section,
            'endexport': self._no_section
        }
        self._fLineParser = self._no_section

    def reset(self):
        """Reset the parser state"""
        pass

    # section parsers

    def _switch_section(self, sLine):
        """Switch to a new section parser based on the given heading line."""
        sSection = sLine[len('***SL***'):-len('***')].lower()
        if sSection in self._dSectionParsers:
            self._fLineParser = self._dSectionParsers[sSection]
        else:
            raise RuntimeError('Unknown section heading in Secret'
                ' Library inventory format')

    def _no_section(self, sLine):
        """Initial parser -- seeing a line here is an error."""
        raise RuntimeError('Data line outside of section'
            ' for Secret Library inventory format')

    def _crypt_section(self, sLine):
        """Parse a crypt entry."""
        oMatch = self.oCardLineRegexp.match(sLine)
        if oMatch is None:
            raise RuntimeError('Unrecognised crypt line for Secrety Library'
                ' deck format')
        iNum = int(oMatch.group('have'))
        sName = oMatch.group('name')

        # Fix advanced
        if sName.endswith('(Adv)'):
            sName = sName.replace('(Adv)', '(Advanced)')

        # Avoid going down the exception path in IAbstractCard if we can
        sName = csv_to_canonical(sName)

        # Secret Library has no expansion info
        self._oHolder.add(iNum, sName, None)

    def _library_section(self, sLine):
        """Parse a library entry."""
        oMatch = self.oCardLineRegexp.match(sLine)
        if oMatch is None:
            raise RuntimeError('Unrecognised library line for Secrety Library'
                ' deck format')
        iNum = int(oMatch.group('have'))
        sName = oMatch.group('name')

        # Avoid going down the exception path in IAbstractCard if we can
        sName = csv_to_canonical(sName)

        # Secret Library has no expansion info
        self._oHolder.add(iNum, sName, None)

    def feed(self, sLine):
        """Feed the next line to the parser and extract the cards"""
        sLine = sLine.strip()
        if not sLine:
            # skip blank lines
            return

        if sLine.startswith('***'):
            self._switch_section(sLine)
        else:
            self._fLineParser(sLine)
