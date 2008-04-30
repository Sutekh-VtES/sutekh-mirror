# IdentifyXMLFile.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""
Attempts to identify a XML file as either PhysicalCard, PhysicalCardSet or
AbstractCardSet (the last is to support legacy backups).
"""

from sutekh.core.SutekhObjects import PhysicalCardSet, PhysicalCard
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
        self._bSetExists = False
        self._bParentExists = False
        self._sType = ''
        self._sName = ''

    name = property(fget=lambda self: self._sName, doc='The name from the'
            ' XML file')
    parent_exists = property(fget=lambda self: self._bParentExists,
            doc='True if the parent card set already exists in the database')
    exists = property(fget=lambda self: self._bExists, doc='True if the card'
            ' set already exists in the database')
    type = property(fget=lambda self: self._sType, doc='The type of the XML '
            'data')

    def identify_tree(self):
        """Process the ElementTree to identify the XML file type."""
        oRoot = self.oTree.getroot()
        # Reset state
        self._sType = 'Unknown'
        self._sName = None
        self._sParentExists = False
        self._bExists = False
        # pylint: disable-msg=E1101
        # SQLObject classes confuse pylint
        if oRoot.tag == 'abstractcardset':
            # only present in legacy backups
            self._sType = 'AbstractCardSet'
            # Same reasoning as on database upgrades
            self._sName = '(ACS) ' + oRoot.attrib['name']
            try:
                PhysicalCardSet.byName(self._sName.encode('utf8'))
                self._bExists = True
            except SQLObjectNotFound:
                self._bExists = False
            self._bParentExists = True # Always a top level card set
        elif oRoot.tag == 'physicalcardset':
            self._sType = 'PhysicalCardSet'
            self._sName = oRoot.attrib['name']
            try:
                PhysicalCardSet.byName(self._sName.encode('utf8'))
                self._bExists = True
            except SQLObjectNotFound:
                self._bExists = False
            if oRoot.attrib.has_key('parent'):
                try:
                    sName = oRoot.attrib['parent']
                    PhysicalCardSet.byName(sName.encode('utf8'))
                    self._bParentExists = True
                except SQLObjectNotFound:
                    self._bParentExists = False
            else:
                self._bParentExists = True # Top level card set
        elif oRoot.tag == 'cards':
            self._sType = 'PhysicalCard'
            # Old Physical Card Collection XML file - it exists if a card
            # set called 'My Collection' exists
            self._sName = 'My Collection'
            try:
                PhysicalCardSet.byName(self._sName.encode('utf8'))
                self._bExists = True
            except SQLObjectNotFound:
                self._bExists = False
            self._bParentExists = True # Always a top level card set
        elif oRoot.tag == 'cardmapping':
            # This is ignored now
            self._sType = 'PhysicalCardSetMappingTable'
            self._sName = self._sType
            self._bExists = False
            self._bParentExists = False

    def parse(self, fIn):
        """Parse the file fIn into the ElementTree."""
        try:
            self.oTree = parse(fIn)
        except ExpatError:
            return ('Unknown', None, False) # Not an XML File
        self.identify_tree()

    def parse_string(self, sIn):
        """Parse the string sIn into the ElementTree"""
        try:
            self.oTree = ElementTree(fromstring(sIn))
        except ExpatError:
            return ('Unknown', None, False) # Not an XML File
        self.identify_tree()

    def id_file(self, sFileName):
        """Load the file sFileName, and try to identify it."""
        fIn = file(sFileName, 'rU')
        tResult = self.parse(fIn)
        fIn.close()
        return tResult
