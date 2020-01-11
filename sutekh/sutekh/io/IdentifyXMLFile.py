# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Attempts to identify a XML file as either PhysicalCardSet, PhysicalCard
   or AbstractCardSet (the last two to support legacy backups)."""

from sutekh.base.core.CardSetUtilities import check_cs_exists
from sutekh.base.io.BaseIdXMLFile import BaseIdXMLFile
from sutekh.io.AbstractCardSetParser import AbstractCardSetParser
from sutekh.io.PhysicalCardParser import PhysicalCardParser
from sutekh.io.PhysicalCardSetParser import PhysicalCardSetParser


class IdentifyXMLFile(BaseIdXMLFile):
    """Tries to identify the XML file type.

       Parse the file into an ElementTree, and then tests the Root element
       to see which xml file it matches.
       """
    def _identify_tree(self, oTree):
        """Process the ElementTree to identify the XML file type."""
        self._clear_id_results()
        oRoot = oTree.getroot()
        if oRoot.tag == 'abstractcardset':
            # only present in legacy backups
            self._sType = 'AbstractCardSet'
            # Same reasoning as on database upgrades
            self._sName = '(ACS) ' + oRoot.attrib['name']
            self._bSetExists = check_cs_exists(self._sName)
            self._bParentExists = True  # Always a top level card set
        elif oRoot.tag == 'physicalcardset':
            self._sType = 'PhysicalCardSet'
            self._sName = oRoot.attrib['name']
            self._bSetExists = check_cs_exists(self._sName)
            if 'parent' in oRoot.attrib:
                self._sParent = oRoot.attrib['parent']
                self._bParentExists = check_cs_exists(self._sParent)
            else:
                self._bParentExists = True  # Top level card set
        elif oRoot.tag == 'cards':
            self._sType = 'PhysicalCard'
            # Old Physical Card Collection XML file - it exists if a card
            # set called 'My Collection' exists
            self._sName = 'My Collection'
            self._bSetExists = check_cs_exists(self._sName)
            self._bParentExists = True  # Always a top level card set
        elif oRoot.tag == 'cardmapping':
            # This is ignored now
            self._sType = 'PhysicalCardSetMappingTable'
            self._sName = self._sType
            self._bSetExists = False
            self._bParentExists = False

    def can_parse(self):
        """True if we can parse the card set."""
        if (self._sType == 'PhysicalCard' or self._sType == 'PhysicalCardSet'
                or self._sType == 'AbstractCardSet'):
            return True
        return False

    def get_parser(self):
        """Return the correct parser."""
        if self._sType == 'PhysicalCard':
            return PhysicalCardParser()
        if self._sType == 'PhysicalCardSet':
            return PhysicalCardSetParser()
        if self._sType == 'AbstractCardSet':
            return AbstractCardSetParser()
        return None
