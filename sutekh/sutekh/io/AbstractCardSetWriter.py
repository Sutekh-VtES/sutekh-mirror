# AbstractCardSetWriter.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Minor modifications copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""
Write cards from a AbstractCardSet out to an XML file which
looks like:
<abstractcardset sutekh_xml_version='1.1' name='AbstractCardSetName' author='Author' comment='Comment' >
  <annotations> Various annotations
  More annotations
  </annotations>
  <card id='3' name='Some Card' count='5' />
  <card id='5' name='Some Other Card' count='2' />
</abstractcardset>
"""

from sutekh.core.SutekhObjects import AbstractCardSet
from sqlobject import SQLObjectNotFound
from sutekh.SutekhUtility import pretty_xml
try:
    from xml.etree.ElementTree import Element, SubElement, ElementTree, tostring
except ImportError:
    from elementtree.ElementTree import Element, SubElement, ElementTree, tostring

class AbstractCardSetWriter(object):
    sMyVersion = "1.1"

    def make_tree(self, sAbstractCardSetName):
        dCards = {}
        try:
            oACS = AbstractCardSet.byName(sAbstractCardSetName)
        except SQLObjectNotFound:
            raise RuntimeError('Unable to find card set %s' % sAbstractCardSetName)

        for oAbs in oACS.cards:
            try:
                dCards[(oAbs.id, oAbs.name)] += 1
            except KeyError:
                dCards[(oAbs.id, oAbs.name)] = 1

        oRoot = Element('abstractcardset', sutekh_xml_version=self.sMyVersion,
                author = oACS.author, name=sAbstractCardSetName, 
                comment = oACS.comment)

        oAnnotationNode = SubElement(oRoot, 'annotations')
        oAnnotationNode.text = oACS.annotations

        for tKey, iNum in dCards.iteritems():
            iId, sName = tKey
            oCardElem = SubElement(oRoot, 'card', id=str(iId), name=sName, 
                    count=str(iNum))

        return oRoot

    def gen_xml_string(self, sAbstractCardSetName):
        oRoot = self.make_tree(sAbstractCardSetName)
        return tostring(oRoot)

    def write(self, fOut, sAbstractCardSetName):
        oRoot = self.make_tree(sAbstractCardSetName)
        pretty_xml(oRoot)
        ElementTree(oRoot).write(fOut)
