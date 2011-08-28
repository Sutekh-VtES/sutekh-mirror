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
     <card name='Some Card' count='5' expansion='Some Expansion' />
     <card name='Some Card' count='2'
        expansion='Some Other Expansion' />
     <card name='Some Other Card' count='2'
        expansion='Some Other Expansion' />
   </physicalcardset>
   """

from sutekh.io.IOBase import BaseXMLWriter
# pylint: disable-msg=E0611, F0401
# xml.etree is a python2.5 thing
try:
    from xml.etree.ElementTree import Element, SubElement
except ImportError:
    from elementtree.ElementTree import Element, SubElement
# pylint: enable-msg=E0611, F0401


class PhysicalCardSetWriter(BaseXMLWriter):
    """Writer for Physical Card Sets.

       We generate an ElementTree representation of the Card Set, which
       can then easily be converted to an appropriate XML representation.
       """
    sMyVersion = "1.3"

    def _gen_tree(self, oHolder):
        """Convert the card set wrapped in oHolder to an ElementTree."""
        dPhys = {}
        bInUse = oHolder.inuse

        oRoot = Element('physicalcardset', sutekh_xml_version=self.sMyVersion,
                name=oHolder.name)
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
            # elementtree 1.3, this should be reworked
            oAbs = oCard.abstractCard
            if oCard.expansion:
                sExpName = oCard.expansion.name
            else:
                sExpName = 'None Specified'
            tKey = (oAbs.name, sExpName)
            dPhys.setdefault(tKey, 0)
            dPhys[tKey] += 1

        # we sort by card name & expansion, as makes results more predictable
        for tKey in sorted(dPhys):
            iNum = dPhys[tKey]
            sName, sExpName = tKey
            SubElement(oRoot, 'card', name=sName, count=str(iNum),
                    expansion=sExpName)
        return oRoot
