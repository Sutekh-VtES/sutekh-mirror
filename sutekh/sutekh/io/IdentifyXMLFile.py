# IdentifyXMLFile.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Attempts to identify a XML file as either PhysicalCardSet, PhysicalCard
   or AbstractCardSet (the last two to support legacy backups)."""

from sutekh.core.SutekhObjects import PhysicalCardSet
from sqlobject import SQLObjectNotFound
# pylint: disable-msg=E0611, F0401
# pylint doesn't like the handling of the differences between 2.4 and 2.5
try:
    from xml.etree.ElementTree import parse
except ImportError:
    from elementtree.ElementTree import parse
# For compatability with ElementTree 1.3
try:
    from xml.etree.ElementTree import ParseError
except ImportError:
    from xml.parsers.expat import ExpatError as ParseError
# pylint: enable-msg=E0611, F0401


class IdentifyXMLFile(object):
    """Tries to identify the XML file type.

       Parse the file into an ElementTree, and then tests the Root element
       to see which xml file it matches.
       """
    def __init__(self):
        self._bSetExists = self._bParentExists = False
        self._sType = self._sName = self._sParent = None

        self._clear_id_results()

    def _clear_id_results(self):
        """Reset identifier state."""
        self._bSetExists = False
        self._bParentExists = False
        self._sType = 'Unknown'
        self._sName = None
        self._sParent = None

    # pylint: disable-msg=W0212
    # We allow access via these properties
    name = property(fget=lambda self: self._sName, doc='The name from the'
            ' XML file')
    parent_exists = property(fget=lambda self: self._bParentExists,
            doc='True if the parent card set already exists in the database')
    parent = property(fget=lambda self: self._sParent,
            doc='Name of the parent card set for this set, None if there'
            ' is no parent')
    exists = property(fget=lambda self: self._bSetExists, doc='True if the'
            ' card set already exists in the database')
    type = property(fget=lambda self: self._sType, doc='The type of the XML '
            'data')
    # pylint: enable-msg=W0212

    def identify_tree(self, oTree):
        """Process the ElementTree to identify the XML file type."""
        self._clear_id_results()
        oRoot = oTree.getroot()
        # pylint: disable-msg=E1101
        # SQLObject classes confuse pylint
        if oRoot.tag == 'abstractcardset':
            # only present in legacy backups
            self._sType = 'AbstractCardSet'
            # Same reasoning as on database upgrades
            self._sName = '(ACS) ' + oRoot.attrib['name']
            try:
                PhysicalCardSet.byName(self._sName.encode('utf8'))
                self._bSetExists = True
            except SQLObjectNotFound:
                self._bSetExists = False
            self._bParentExists = True  # Always a top level card set
        elif oRoot.tag == 'physicalcardset':
            self._sType = 'PhysicalCardSet'
            self._sName = oRoot.attrib['name']
            try:
                PhysicalCardSet.byName(self._sName.encode('utf8'))
                self._bSetExists = True
            except SQLObjectNotFound:
                self._bSetExists = False
            if oRoot.attrib.has_key('parent'):
                self._sParent = oRoot.attrib['parent']
                try:
                    PhysicalCardSet.byName(self._sParent.encode('utf8'))
                    self._bParentExists = True
                except SQLObjectNotFound:
                    self._bParentExists = False
            else:
                self._bParentExists = True  # Top level card set
        elif oRoot.tag == 'cards':
            self._sType = 'PhysicalCard'
            # Old Physical Card Collection XML file - it exists if a card
            # set called 'My Collection' exists
            self._sName = 'My Collection'
            try:
                PhysicalCardSet.byName(self._sName.encode('utf8'))
                self._bSetExists = True
            except SQLObjectNotFound:
                self._bSetExists = False
            self._bParentExists = True  # Always a top level card set
        elif oRoot.tag == 'cardmapping':
            # This is ignored now
            self._sType = 'PhysicalCardSetMappingTable'
            self._sName = self._sType
            self._bSetExists = False
            self._bParentExists = False

    def parse(self, fIn, _oDummyHolder=None):
        """Parse the file fIn into the ElementTree."""
        try:
            oTree = parse(fIn)
        except ParseError:
            self._clear_id_results()  # Not an XML file
            return
        self.identify_tree(oTree)

    def id_file(self, sFileName):
        """Load the file sFileName, and try to identify it."""
        fIn = file(sFileName, 'rU')
        try:
            self.parse(fIn, None)
        finally:
            fIn.close()
