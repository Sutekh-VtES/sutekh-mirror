# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
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
from sutekh.base.Utility import move_articles_to_front
from sutekh.base.io.IOBase import CardSetParser


class SLInventoryParser(CardSetParser):
    """Parser for the Secret Library web API inventory format."""

    oCardLineRegexp = re.compile(
        r'^(?P<have>[0-9]+)\s*;\s*(?P<want>[0-9]+)\s*;\s*(?P<name>.*)$')

    def __init__(self):
        # pylint: disable=super-init-not-called
        # No need to call IOBase.__init__()
        self._dSectionParsers = {
            'crypt': self._crypt_section,
            'library': self._library_section,
            'endexport': self._no_section,
        }

    # section parsers

    def _switch_section(self, sLine):
        """Return a new section parser based on the given heading line."""
        sSection = sLine[len('***SL***'):-len('***')].lower()
        if sSection in self._dSectionParsers:
            return self._dSectionParsers[sSection]
        raise IOError('Unknown section heading in Secret'
                      ' Library inventory format')

    # pylint: disable=no-self-use
    # Making these functions for clarity
    def _no_section(self, _sLine, _oHolder):
        """Initial parser -- seeing a line here is an error."""
        raise IOError('Data line outside of section'
                      ' for Secret Library inventory format')

    # pylint: enable=no-self-use

    def _crypt_section(self, sLine, oHolder):
        """Parse a crypt entry."""
        oMatch = self.oCardLineRegexp.match(sLine)
        if oMatch is None:
            raise IOError('Unrecognised crypt line for Secrety Library'
                          ' deck format')
        iNum = int(oMatch.group('have'))
        sName = oMatch.group('name')

        # Fix advanced
        if sName.endswith('(Adv)'):
            sName = sName.replace('(Adv)', '(Advanced)')

        # Avoid going down the exception path in IAbstractCard if we can
        sName = move_articles_to_front(sName)

        # Secret Library has no expansion info
        oHolder.add(iNum, sName, None, None)

    def _library_section(self, sLine, oHolder):
        """Parse a library entry."""
        oMatch = self.oCardLineRegexp.match(sLine)
        if oMatch is None:
            raise IOError('Unrecognised library line for Secrety Library'
                          ' deck format')
        iNum = int(oMatch.group('have'))
        sName = oMatch.group('name')

        # Avoid going down the exception path in IAbstractCard if we can
        sName = move_articles_to_front(sName)

        # Secret Library has no expansion info
        oHolder.add(iNum, sName, None, None)

    def parse(self, fIn, oHolder):
        """Parse the SL inventory in fIn into oHolder."""
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
