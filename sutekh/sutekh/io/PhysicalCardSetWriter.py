# PhysicalCardSetWriter.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Minor modifications copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""
Write physical cards from a PhysicalCardSet out to an XML file which
looks like:
<physicalcardset sutekh_xml_version='1.1' name='SetName' author='Author' comment='Comment'>
  <annotations> Various annotations
  More annotations
  </annotations>
  <card id='3' name='Some Card' count='5' expansion='Some Expansion' />
  <card id='3' name='Some Card' count='2' expansion='Some Other Expansion' />
  <card id='5' name='Some Other Card' count='2' expansion='Some Other Expansion' />
</physicalcardset>
"""

from sutekh.core.SutekhObjects import PhysicalCardSet
from sqlobject import SQLObjectNotFound
from sutekh.SutekhUtility import pretty_xml
try:
    from xml.etree.ElementTree import Element, SubElement, ElementTree, tostring
except ImportError:
    from elementtree.ElementTree import Element, SubElement, ElementTree, tostring

class PhysicalCardSetWriter(object):
    sMyVersion = "1.1"

    def make_tree(self, sPhysicalCardSetName):
        dPhys = {}
        try:
            oPCS = PhysicalCardSet.byName(sPhysicalCardSetName)
            bInUse = oPCS.inuse
        except SQLObjectNotFound:
            raise RuntimeError('Unable to find card set %s' % sPhysicalCardSetName)

        oRoot = Element('physicalcardset', sutekh_xml_version=self.sMyVersion,
                name=sPhysicalCardSetName, author=oPCS.author, comment=oPCS.comment)
        oAnnotationNode = SubElement(oRoot, 'annotations')
        oAnnotationNode.text = oPCS.annotations

        if bInUse:
            oRoot.attrib['inuse'] = 'Yes'

        for oCard in oPCS.cards:
            # ElementTree 1.2 doesn't support searching for attributes,
            # so this is easier than using the tree directly. For
            # elementtree 1.3, this should be reworked
            oAbs = oCard.abstractCard
            try:
                dPhys[(oAbs.id, oAbs.name, oCard.expansion)] += 1
            except KeyError:
                dPhys[(oAbs.id, oAbs.name, oCard.expansion)] = 1

        for tKey, iNum in dPhys.iteritems():
            iId, sName, oExpansion = tKey
            oCardElem = SubElement(oRoot, 'card', id=str(iId), name=sName,
                    count = str(iNum))
            if oExpansion is None:
                oCardElem.attrib['expansion'] =  'None Specified'
            else:
                oCardElem.attrib['expansion'] = oExpansion.name

        return oRoot

    def gen_xml_string(self, sPhysicalCardSetName):
        oRoot = self.make_tree(sPhysicalCardSetName)
        return tostring(oRoot)

    def write(self,fOut, sPhysicalCardSetName):
        oRoot = self.make_tree(sPhysicalCardSetName)
        pretty_xml(oRoot)
        ElementTree(oRoot).write(fOut)
