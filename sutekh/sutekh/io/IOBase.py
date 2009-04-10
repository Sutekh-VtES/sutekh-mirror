# IOBase.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Simon Cross <hodgestar@gmail.com>
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Base classes for sutekh.io card set parsers and writers.
   """

# pylint: disable-msg=R0921
# These may be referenced elsewhere, and mainly exist as interface
# documentation, rather than genuine base classes

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

       The sutekh.core.CardSetHolder module provides a CardSetWrapper
       implementation of the CardSetHolder class for use when writing
       out an existing card set.

       Example:
           from sutekh.core.CardSetHolder import CardSetWrapper
           oWriter.write(fOut, CardSetWrapper(oCS))
       """

    def write(self, fOut, oHolder):
        """Write the card set in the card set holder to the file-like
           object fOut.
           """
        raise NotImplementedError("CardSetWriter should be sub-classed")
