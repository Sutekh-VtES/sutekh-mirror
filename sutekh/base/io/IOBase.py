# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Simon Cross <hodgestar@gmail.com>
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Base classes for sutekh.io card set parsers and writers.
   """

from xml.etree.ElementTree import parse, tostring
# pylint: disable=E0611, F0401
# For compatability with ElementTree 1.3
try:
    from xml.etree.ElementTree import ParseError
except ImportError:
    from xml.parsers.expat import ExpatError as ParseError
# pylint: enable=E0611, F0401

from sqlobject import sqlhub

from ..Utility import pretty_xml, norm_xml_quotes
from ..core.DBUtility import flush_cache


class CardSetParser(object):
    """Parent class for card set parsers.

       Card set parser classes need not subclass this class, only
       create a card set parser object when called without arguments.
       The parser object should have a .parse() method that takes a
       file-like object and a card set holder as parameters.

       Example:
           oParser = cParser()
           oParser.parse(fIn, oCardSetHolder)
       """

    def parse(self, fIn, oHolder):
        """Parse the card set in the file-like object fIn into the card
           set holder oHolder.
           """
        raise NotImplementedError("CardSetParser should be sub-classed")


class CardSetWriter(object):
    """Parent class for card set writers.

       Card set writer classes need not subclass this class, only
       create a card set writer object when called without arguments.
       The writer object should have a .write() method that takes a
       file-like object and a card set holder as parameters.

       Example:
           oWriter = cWriter()
           oWriter.write(fOut, oHolder)

       The sutekh.base.core.CardSetHolder module provides a CardSetWrapper
       implementation of the CardSetHolder class for use when writing
       out an existing card set.

       Example:
           from sutekh.base.core.CardSetHolder import CardSetWrapper
           oWriter.write(fOut, CardSetWrapper(oCS))
       """

    def write(self, fOut, oHolder):
        """Write the card set in the card set holder to the file-like
           object fOut.
           """
        raise NotImplementedError("CardSetWriter should be sub-classed")


class BaseXMLParser(object):
    """Base object for the various XML Parser classes.

       classes just implement a _convert_tree class to fill in the
       card set holder from the XML tree."""

    def __init__(self):
        self._oTree = None

    def _convert_tree(self, oHolder):
        """Convert the XML Tree into a card set holder"""
        raise NotImplementedError("BaseXMLParser should be subclassed")

    def parse(self, fIn, oHolder):
        """Read the XML tree from the file-like object fIn"""
        try:
            self._oTree = parse(fIn)
        except ParseError as oExp:
            raise IOError('Not an XML file: %s' % oExp)
        self._convert_tree(oHolder)


class BaseLineParser(CardSetParser):
    """Base class for simple line-by-line parsers.

       Subclasses override _feed to handle the individual lines
       """

    def _feed(self, sLine, oHolder):
        """Internal method to handle a single line. Overriden by the
           subclasses"""
        raise NotImplementedError("BaseLineParser should be subclassed")

    def parse(self, fIn, oHolder):
        """Parse the file line by line"""
        for sLine in fIn:
            sLine = sLine.strip()
            if not sLine:
                continue  # skip blank lines
            self._feed(sLine, oHolder)


class BaseXMLWriter(CardSetWriter):
    """Base class for XML output"""

    def _gen_tree(self, oHolder):
        """Create the XML Tree"""
        raise NotImplementedError("BaseXMLWriter should be subclassed")

    def write(self, fOut, oHolder):
        """Write the holder contents as pretty XML to the given file-like
           object fOut"""
        oRoot = self._gen_tree(oHolder)
        pretty_xml(oRoot)
        sData = tostring(oRoot)
        # Standardise quotes
        sData = norm_xml_quotes(sData)
        fOut.write(sData)


def safe_parser(oFile, oParser):
    """Wrap the logic for parsing files, to ensure we
       handle transactions and error conditions consistently.

       oFile is an object with a .open() method (e.g. EncodedFile).
       oParser is an object with a parse() method that takes an
       open file object."""
    flush_cache()
    fIn = None
    oOldConn = sqlhub.processConnection
    sqlhub.processConnection = oOldConn.transaction()
    try:
        fIn = oFile.open()
        oParser.parse(fIn)
        sqlhub.processConnection.commit(close=True)
    finally:
        # We use the fIn check so we don't swallow any exceptions raised
        # by open failing
        if fIn:
            fIn.close()
        # Always restore connection
        sqlhub.processConnection = oOldConn
