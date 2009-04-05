# PhysicalCardParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2007, 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Read physical cards from an XML file which looks like:

   <cards sutekh_xml_version="1.0">
     <card id='3' name='Some Card' count='5' expansion="Some Expansion" />
     <card id='3' name='Some Card' count='2'
        Expansion="Some Other Expansion" />
     <card id='5' name='Some Other Card' count='2'
       expansion="Some Expansion" />
   </cards>
   into the default PhysicalCardSet 'My Collection'.
   """

from sutekh.core.CardSetHolder import CachedCardSetHolder
from sutekh.core.CardLookup import DEFAULT_LOOKUP
from sqlobject import sqlhub
# pylint: disable-msg=E0611, F0401
# xml.etree is a python2.5 thing
try:
    from xml.etree.ElementTree import parse, fromstring, ElementTree
except ImportError:
    from elementtree.ElementTree import parse, fromstring, ElementTree
# pylint: enable-msg=E0611, F0401

class PhysicalCardParser(object):
    """Implement the PhysicalCard Parser.

       We read the xml file into a ElementTree, then walk the tree to
       extract the cards.
       """
    aSupportedVersions = ['1.0', '0.0']

    def __init__(self):
        self.oCS = None
        self.oTree = None

    def _convert_tree(self):
        """parse the elementtree into a card set holder"""
        self.oCS = CachedCardSetHolder()
        self.oCS.name = "My Collection"
        oRoot = self.oTree.getroot()
        if oRoot.tag != 'cards':
            raise RuntimeError("Not a Physical card list")
        if oRoot.attrib['sutekh_xml_version'] not in self.aSupportedVersions:
            raise RuntimeError("Unrecognised XML File version")
        for oElem in oRoot:
            if oElem.tag == 'card':
                iCount = int(oElem.attrib['count'], 10)
                sName = oElem.attrib['name']
                try:
                    sExpansionName = oElem.attrib['expansion']
                    if sExpansionName == "None Specified":
                        sExpansionName = None
                except KeyError:
                    sExpansionName = None
                self.oCS.add(iCount, sName, sExpansionName)

    def _commit_tree(self, oCardLookup, dLookupCache):
        """Commit the tree to the database.

           We use the card set holder, so it calls the appropriate card lookup
           function for unknown cards
           """
        oOldConn = sqlhub.processConnection
        sqlhub.processConnection = oOldConn.transaction()
        self.oCS.create_pcs(oCardLookup, dLookupCache)
        sqlhub.processConnection.commit(close=True)
        sqlhub.processConnection = oOldConn
        self.oCS = None

    # pylint: disable-msg=W0102
    # W0102 - {} is the right thing here
    def parse(self, fIn, oCardLookup=DEFAULT_LOOKUP, bIgnoreWarnings=True,
            dLookupCache={}):
        """Read the file object fIn into the database."""
        self.oTree = parse(fIn)
        self._convert_tree()
        self._commit_tree(oCardLookup, dLookupCache)
        if not bIgnoreWarnings:
            return self.oCS.get_warnings()
        else:
            return []

    def parse_string(self, sIn, oCardLookup=DEFAULT_LOOKUP,
            bIgnoreWarnings=True, dLookupCache={}):
        """Read the string sIn into the database."""
        self.oTree = ElementTree(fromstring(sIn))
        self._convert_tree()
        self._commit_tree(oCardLookup, dLookupCache)
        if not bIgnoreWarnings:
            return self.oCS.get_warnings()
        else:
            return []
