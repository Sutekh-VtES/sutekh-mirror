# PhysicalCardSetWriter.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Write physical cards from a PhysicalCardSet

   Save to an XML file which looks like:
   <physicalcardset sutekh_xml_version='1.3' name='SetName' author='Author'>
     <comment>Deck Description</comment>
     <annotations> Various annotations
     More annotations
     </annotations>
     <card id='3' name='Some Card' count='5' expansion='Some Expansion' />
     <card id='3' name='Some Card' count='2'
        expansion='Some Other Expansion' />
     <card id='5' name='Some Other Card' count='2'
        expansion='Some Other Expansion' />
   </physicalcardset>
   """

from sutekh.core.SutekhObjects import PhysicalCardSet
from sqlobject import SQLObjectNotFound
from sutekh.SutekhUtility import pretty_xml
# pylint: disable-msg=E0611, F0401
# xml.etree is a python2.5 thing
try:
    from xml.etree.ElementTree import Element, SubElement, ElementTree, \
            tostring
except ImportError:
    from elementtree.ElementTree import Element, SubElement, ElementTree, \
            tostring
# pylint: enable-msg=E0611, F0401

class PhysicalCardSetWriter(object):
    """Writer for Physical Card Sets.

       We generate an ElementTree representation of the Card Set, which
       can then easily be converted to an appropriate XML representation.
       """
    sMyVersion = "1.3"

    def make_tree(self, sPhysicalCardSetName):
        """Convert the card set sPhysicalCardSetName to an ElementTree."""
        dPhys = {}
        try:
            # pylint: disable-msg=E1101
            # SQLObject confuses pylint
            oPCS = PhysicalCardSet.byName(sPhysicalCardSetName)
            bInUse = oPCS.inuse
        except SQLObjectNotFound:
            raise RuntimeError('Unable to find card set %s' %
                    sPhysicalCardSetName)

        oRoot = Element('physicalcardset', sutekh_xml_version=self.sMyVersion,
                name=sPhysicalCardSetName, author=oPCS.author)
        oCommentNode = SubElement(oRoot, 'comment')
        oCommentNode.text = oPCS.comment
        oAnnotationNode = SubElement(oRoot, 'annotations')
        oAnnotationNode.text = oPCS.annotations
        if oPCS.parent:
            oRoot.attrib['parent'] = oPCS.parent.name

        if bInUse:
            oRoot.attrib['inuse'] = 'Yes'

        for oCard in oPCS.cards:
            # ElementTree 1.2 doesn't support searching for attributes,
            # so this is easier than using the tree directly. For
            # elementtree 1.3, this should be reworked
            oAbs = oCard.abstractCard
            if oCard.expansion:
                sExpName = oCard.expansion.name
            else:
                sExpName = 'None Specified'
            tKey = (oAbs.id, oAbs.name, sExpName)
            dPhys.setdefault(tKey, 0)
            dPhys[tKey] += 1

        # we sort by card name & expansion, as makes results more predictable
        for tKey in sorted(dPhys, key=lambda x: (x[1], x[2])):
            iNum = dPhys[tKey]
            iId, sName, sExpName = tKey
            oCardElem = SubElement(oRoot, 'card', id=str(iId), name=sName,
                    count = str(iNum), expansion=sExpName)
        pretty_xml(oRoot)
        return oRoot

    def gen_xml_string(self, sPhysicalCardSetName):
        """Generate a string containing the XML output."""
        oRoot = self.make_tree(sPhysicalCardSetName)
        return tostring(oRoot)

    def write(self, fOut, sPhysicalCardSetName):
        """Generate prettier XML and write it to the file fOut."""
        oRoot = self.make_tree(sPhysicalCardSetName)
        ElementTree(oRoot).write(fOut)
