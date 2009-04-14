# PhysicalCardSetParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Read physical cards from an XML file which looks like:

   <physicalcardset sutekh_xml_version='1.2' name='SetName' author='Author'
      comment='Comment' parent='Parent PCS name'>
     <annotations>
     Annotations
     </annotations>
     <card id='3' name='Some Card' count='5' expansion='Some Expansion' />
     <card id='3' name='Some Card' count='2'
         expansion='Some Other Expansion' />
     <card id='5' name='Some Other Card' count='2'
         expansion='Some Other Expansion' />
   </physicalcardset>

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

class PhysicalCardSetParser(object):
    """Impement the parser.

       read the tree into an ElementTree, and walk the tree to find the
       cards.
       """
    def __init__(self):
        self.aSupportedVersions = ['1.2', '1.1', '1.0']
        self.oCS = CachedCardSetHolder()
        self.oTree = None

    def _convert_tree(self):
        """Convert the ElementTree into a CardSetHolder"""
        self.oCS = CachedCardSetHolder()
        oRoot = self.oTree.getroot()
        if oRoot.tag != 'physicalcardset':
            raise RuntimeError("Not a Physical Card Set list")
        if oRoot.attrib['sutekh_xml_version'] not in self.aSupportedVersions:
            raise RuntimeError("Unrecognised XML File version")
        self.oCS.name = oRoot.attrib['name']
        self.oCS.author = oRoot.attrib['author']
        self.oCS.comment = oRoot.attrib['comment']
        self.oCS.inuse = False
        # pylint: disable-msg=W0704
        # exception does enough for us
        try:
            if oRoot.attrib['inuse'] == 'Yes':
                self.oCS.inuse = True
        except KeyError:
            pass
        if oRoot.attrib.has_key('parent'):
            self.oCS.parent = oRoot.attrib['parent']

        # pylint: enable-msg=W0704
        for oElem in oRoot:
            if oElem.tag == 'annotations':
                self.oCS.annotations = oElem.text
            elif oElem.tag == 'card':
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

    def string_to_holder(self, sIn):
        """Parse the string into a Card Set Holder without commiting it"""
        self.oTree = ElementTree(fromstring(sIn))
        self._convert_tree()
        return self.oCS

    # pylint: disable-msg=W0102
    # W0102 - {} is the right thing here
    def parse(self, fIn, oCardLookup=DEFAULT_LOOKUP, bIgnoreWarnings=True,
            dLookupCache={}):
        """Read the file fIn into the database."""
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

