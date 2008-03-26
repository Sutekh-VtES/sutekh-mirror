# PhysicalCardSetParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""
Read physical cards from an XML file which
looks like:
<physicalcardset sutekh_xml_version='1.1' name='SetName' author='Author' comment='Comment'>
  <annotations>
  Annotations
  </annotations>
  <card id='3' name='Some Card' count='5' expansion='Some Expansion' />
  <card id='3' name='Some Card' count='2' expansion='Some Other Expansion' />
  <card id='5' name='Some Other Card' count='2' expansion='Some Other Expansion' />
</physicalcardset>
into a PhysicalCardSet
"""

from sutekh.core.CardSetHolder import CardSetHolder
from sutekh.core.CardLookup import DEFAULT_LOOKUP
from sqlobject import sqlhub
try:
    from xml.etree.ElementTree import parse, fromstring, ElementTree
except ImportError:
    from elementtree.ElementTree import parse, fromstring, ElementTree

class PhysicalCardSetParser(object):
    def __init__(self):
        self.aSupportedVersions = ['1.1', '1.0']
        self.oCS = CardSetHolder()
        self.oTree = None

    def _convert_tree(self):
        """Convert the ElementTree into a CardSetHolder"""
        oRoot = self.oTree.getroot()
        if oRoot.tag != 'physicalcardset':
            raise RuntimeError("Not a Physical Card Set list")
        if oRoot.attrib['sutekh_xml_version'] not in self.aSupportedVersions:
            raise RuntimeError("Unrecognised XML File version")
        self.oCS.name = oRoot.attrib['name']
        self.oCS.author = oRoot.attrib['author']
        self.oCS.comment = oRoot.attrib['comment']
        self.oCS.inuse = False
        try:
            if oRoot.attrib['inuse'] == 'Yes':
                self.oCS.inuse = True
        except KeyError:
            pass
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

    def _commit_tree(self, oCardLookup):
        oOldConn = sqlhub.processConnection
        sqlhub.processConnection = oOldConn.transaction()
        self.oCS.createPCS(oCardLookup)
        sqlhub.processConnection.commit()
        sqlhub.processConnection = oOldConn

    def parse(self, fIn, oCardLookup=DEFAULT_LOOKUP):
        self.oTree = parse(fIn)
        self._convert_tree()
        self._commit_tree(oCardLookup)

    def parse_string(self, sIn, oCardLookup=DEFAULT_LOOKUP):
        self.oTree = ElementTree(fromstring(sIn))
        self._convert_tree()
        self._commit_tree(oCardLookup)
