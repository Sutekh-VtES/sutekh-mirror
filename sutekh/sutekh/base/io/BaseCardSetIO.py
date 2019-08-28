# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2014 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Base classes for the app specific XML card set parsers and writers.
   """

from xml.etree.ElementTree import Element, SubElement

from .IOBase import BaseXMLParser, BaseXMLWriter
from ..core.BaseTables import MAX_ID_LENGTH


class BaseCardXMLParser(BaseXMLParser):
    # pylint: disable=abstract-method
    # Doesn't matter that we don't override _convert_tree - subclasses will
    # do that for us
    """Base class for cardset XML files.

       Adds version checking helper functions and such"""

    # Sub-classes override these
    aSupportedVersions = []
    sTypeTag = "none"
    sTypeName = "cardset XML"
    sVersionTag = "none"

    def _check_tree(self):
        """Check if the tree is valid"""
        oRoot = self._oTree.getroot()
        if oRoot.tag != self.sTypeTag:
            raise IOError("Not a %s XML File" % self.sTypeName)
        if oRoot.attrib[self.sVersionTag] not in self.aSupportedVersions:
            raise IOError("Unrecognised %s File version" % self.sTypeName)

    # pylint: disable=no-self-use
    # method so subclasses can use it if needed

    def _parse_card(self, oElem, oHolder):
        """Extract the expansion information from a card node"""
        iCount = int(oElem.attrib['count'], 10)
        sName = oElem.attrib['name']
        try:
            sExpansionName = oElem.attrib['expansion']
            if sExpansionName == "None Specified":
                sExpansionName = None
        except KeyError:
            sExpansionName = None
        try:
            sPrinting = oElem.attrib['printing']
            if sPrinting == "No Printing":
                sPrinting = None
        except KeyError:
            sPrinting = None
        oHolder.add(iCount, sName, sExpansionName, sPrinting)


class BaseCardSetParser(BaseCardXMLParser):
    # pylint: disable=abstract-method
    # Doesn't matter that we don't override _convert_tree - subclasses will
    # do that for us
    """Base class for physical cardset XML files.

       Adds generic _convert_tree method"""

    def _convert_tree(self, oHolder):
        """Convert the ElementTree into a CardSetHolder"""
        self._check_tree()
        oRoot = self._oTree.getroot()
        oHolder.name = oRoot.attrib['name'][:MAX_ID_LENGTH]
        oHolder.inuse = False
        try:
            oHolder.author = oRoot.attrib['author']
        except KeyError:
            pass
        try:
            oHolder.comment = oRoot.attrib['comment']
        except KeyError:
            # Default value for comment is the right thing here
            pass
        try:
            if oRoot.attrib['inuse'] == 'Yes':
                oHolder.inuse = True
        except KeyError:
            pass

        if 'parent' in oRoot.attrib:
            oHolder.parent = oRoot.attrib['parent']

        for oElem in oRoot:
            if oElem.tag == 'comment':
                if oHolder.comment:
                    # We already encontered a comment, so error out
                    raise IOError("Format error. Multiple"
                                  " comment values encountered.")
                oHolder.comment = oElem.text
            if oElem.tag == 'annotations':
                if oHolder.annotations:
                    raise IOError("Format error. Multiple"
                                  " annotation values encountered.")
                oHolder.annotations = oElem.text
            elif oElem.tag == 'card':
                self._parse_card(oElem, oHolder)


class BaseCardXMLWriter(BaseXMLWriter):
    """Base class for cardset XML files.

       Handles all the expansion dancing needed."""

    # base classes will overwrite these
    sMyVersion = "1.0"
    sTypeTag = "none"
    sVersionTag = "none"

    def _gen_tree(self, oHolder):
        """Convert the card set wrapped in oHolder to an ElementTree."""
        dPhys = {}
        bInUse = oHolder.inuse

        oRoot = Element(self.sTypeTag,
                        name=oHolder.name)
        oRoot.attrib[self.sVersionTag] = self.sMyVersion
        if oHolder.author:
            oRoot.attrib['author'] = oHolder.author
        else:
            oRoot.attrib['author'] = ''
        oCommentNode = SubElement(oRoot, 'comment')
        oCommentNode.text = oHolder.comment
        oAnnotationNode = SubElement(oRoot, 'annotations')
        oAnnotationNode.text = oHolder.annotations
        if oHolder.parent:
            oRoot.attrib['parent'] = oHolder.parent

        if bInUse:
            oRoot.attrib['inuse'] = 'Yes'

        for oCard in oHolder.cards:
            # ElementTree 1.2 doesn't support searching for attributes,
            # so this is easier than using the tree directly. For
            # ElementTree 1.3, this should be reworked
            oAbs = oCard.abstractCard
            if oCard.printing:
                sExpName = oCard.printing.expansion.name
                sPrinting = oCard.printing.name
                if sPrinting is None:
                    sPrinting = 'No Printing'
            else:
                sExpName = 'None Specified'
                sPrinting = 'No Printing'
            tKey = (oAbs.name, sExpName, sPrinting)
            dPhys.setdefault(tKey, 0)
            dPhys[tKey] += 1

        # we sort by card name & expansion, as makes results more predictable
        for tKey in sorted(dPhys):
            iNum = dPhys[tKey]
            sName, sExpName, sPrinting = tKey
            SubElement(oRoot, 'card', name=sName, count=str(iNum),
                       expansion=sExpName, printing=sPrinting)
        return oRoot
