# AbstractCardSetParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Minor modifications copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""
Read cards from an XML file which
looks like:
<abstractcardset sutekh_xml_version='1.0' name='AbstractCardSetName' author='Author' comment='Comment'>
  <annotations>
  Annotations
  </annotations>
  <card id='3' name='Some Card' count='5' />
  <card id='5' name='Some Other Card' count='2' />
</abstractcardset>
into a AbstractCardSet
"""

from sutekh.core.CardSetHolder import CardSetHolder
from sutekh.core.CardLookup import DEFAULT_LOOKUP
from sqlobject import sqlhub
try:
    from xml.etree.ElementTree import parse, fromstring, ElementTree
except ImportError:
    from elementtree.ElementTree import parse, fromstring, ElementTree

class AbstractCardSetParser(object):
    def __init__(self):
        self.aSupportedVersions = ['1.1', '1.0']
        self.oCS = CardSetHolder()
        self.oTree = None

    def _convert_tree(self):
        """Convert the ElementTree into a CardSetHolder"""
        oRoot = self.oTree.getroot()
        if oRoot.tag != 'abstractcardset':
            raise RuntimeError("Not a Abstract Card Set list")
        if oRoot.attrib['sutekh_xml_version'] not in self.aSupportedVersions:
            raise RuntimeError("Unrecognised XML File version")
        self.oCS.name = oRoot.attrib['name']
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
                self.oCS.add(iCount, sName)

    def _commit_tree(self, oCardLookup):
        oOldConn = sqlhub.processConnection
        sqlhub.processConnection = oOldConn.transaction()
        self.oCS.createACS(oCardLookup)
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
