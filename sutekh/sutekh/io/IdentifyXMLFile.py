# IdentifyXMLFile.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""
Attempts to identify a XML file as either PhysicalCard, PhysicalCardSet or
AbstractCardSet
"""

from sutekh.core.SutekhObjects import AbstractCardSet, PhysicalCardSet, \
        PhysicalCard
from sqlobject import SQLObjectNotFound
try:
    # pylint: disable-msg=E0611, F0401
    # xml.etree is a python2.5 thing
    from xml.etree.ElementTree import parse, fromstring, ElementTree
except ImportError:
    from elementtree.ElementTree import parse, fromstring, ElementTree
from xml.parsers.expat import ExpatError

class IdentifyXMLFile(object):
    """Tries to identify the XML file type.

       Parse the file into an ElementTree, and then tests the Root element
       to see which xml file it matches.
       """
    def __init__(self):
        self.oTree = None

    def identify_tree(self):
        """Process the ElementTree to identify the XML file type."""
        oRoot = self.oTree.getroot()
        sType = 'Unknown'
        sName = None
        bExists = False
        # pylint: disable-msg=E1101
        # SQLObject classes confuse pylint
        if oRoot.tag == 'abstractcardset':
            sType = 'AbstractCardSet'
            sName = oRoot.attrib['name']
            try:
                AbstractCardSet.byName(sName.encode('utf8'))
                bExists = True
            except SQLObjectNotFound:
                bExists = False
        elif oRoot.tag == 'physicalcardset':
            sType = 'PhysicalCardSet'
            sName = oRoot.attrib['name']
            try:
                PhysicalCardSet.byName(sName.encode('utf8'))
                bExists = True
            except SQLObjectNotFound:
                bExists = False
        elif oRoot.tag == 'cards':
            sType = 'PhysicalCard'
            # There is only 1 PhysicalCard List, so it exists if it's
            # not empty
            bExists = PhysicalCard.select().count() > 0
        elif oRoot.tag == 'cardmapping':
            sType = 'PhysicalCardSetMappingTable'
            sName = sType
            bExists = False # Always want to try applying the mapping table
        return (sType, sName, bExists)

    def parse(self, fIn):
        """Parse the file fIn into the ElementTree."""
        try:
            self.oTree = parse(fIn)
        except ExpatError:
            return ('Unknown', None, False) # Not an XML File
        return self.identify_tree()

    def parse_string(self, sIn):
        """Parse the string sIn into the ElementTree"""
        try:
            self.oTree = ElementTree(fromstring(sIn))
        except ExpatError:
            return ('Unknown', None, False) # Not an XML File
        return self.identify_tree()

    def id_file(self, sFileName):
        """Load the file sFileName, and try to identify it."""
        fIn = file(sFileName, 'rU')
        tResult = self.parse(fIn)
        fIn.close()
        return tResult
