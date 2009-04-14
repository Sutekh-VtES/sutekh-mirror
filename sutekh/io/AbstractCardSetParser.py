# AbstractCardSetParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Read cards from an XML file which looks like:

   <abstractcardset sutekh_xml_version='1.0' name='AbstractCardSetName'
      author='Author' comment='Comment'>
     <annotations>
     Annotations
     </annotations>
     <card id='3' name='Some Card' count='5' />
     <card id='5' name='Some Other Card' count='2' />
   </abstractcardset>
   into a PhysicalCardSet.
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

class AbstractCardSetParser(object):
    """Impement the parser.

       read the tree into an ElementTree, and walk the tree to find the
       cards.
       """
    def __init__(self):
        self.aSupportedVersions = ['1.1', '1.0']
        self.oCS = CachedCardSetHolder()
        self.oTree = None

    def _convert_tree(self):
        """Convert the ElementTree into a CachedCardSetHolder"""
        self.oCS = CachedCardSetHolder()
        oRoot = self.oTree.getroot()
        if oRoot.tag != 'abstractcardset':
            raise RuntimeError("Not a Abstract Card Set list")
        if oRoot.attrib['sutekh_xml_version'] not in self.aSupportedVersions:
            raise RuntimeError("Unrecognised XML File version")
        # same reasoning as for database upgrades
        # Ensure name fits into column
        self.oCS.name = '(ACS) %s' % oRoot.attrib['name']
        self.oCS.name = self.oCS.name[:50]
        self.oCS.author = oRoot.attrib['author']
        self.oCS.comment = oRoot.attrib['comment']
        self.oCS.inuse = False
        for oElem in oRoot:
            if oElem.tag == 'annotations':
                self.oCS.annotations = oElem.text
            elif oElem.tag == 'card':
                iCount = int(oElem.attrib['count'], 10)
                sName = oElem.attrib['name']
                # Add card to virtual cardset
                self.oCS.add(iCount, sName, None)

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

    # pylint: disable-msg=W0102
    # W0102 - {} is the right thing here
    def parse(self, fIn, oCardLookup=DEFAULT_LOOKUP, bIgnoreWarnings=True,
            dLookupCache={}):
        """Parse the file fIn into the database."""
        self.oTree = parse(fIn)
        self._convert_tree()
        self._commit_tree(oCardLookup, dLookupCache)
        if not bIgnoreWarnings:
            return self.oCS.get_warnings()
        else:
            return []

    def parse_string(self, sIn, oCardLookup=DEFAULT_LOOKUP,
            bIgnoreWarnings=True, dLookupCache={}):
        """Parse the string sIn into the database."""
        self.oTree = ElementTree(fromstring(sIn))
        self._convert_tree()
        self._commit_tree(oCardLookup, dLookupCache)
        if not bIgnoreWarnings:
            return self.oCS.get_warnings()
        else:
            return []
