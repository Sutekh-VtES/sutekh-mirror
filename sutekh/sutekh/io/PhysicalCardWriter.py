# PhysicalCardWriter.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""
Write physical cards out to an XML file which
looks like:
<cards sutekh_xml_version="1.0">
  <card id='3' name='Some Card' count='5' Expansion="Some Expansion" />
  <card id='3' name='Some Card' count='2' Expansion="Some Other Expansion" />
  <card id='5' name='Some Other Card' count='2' Expansion="Some Other Expansion" />
</cards>
"""

from sutekh.core.SutekhObjects import PhysicalCard
from sutekh.SutekhUtility import pretty_xml
try:
    from xml.etree.ElementTree import Element, SubElement, ElementTree, tostring
except ImportError:
    from elementtree.ElementTree import Element, SubElement, ElementTree, tostring

class PhysicalCardWriter(object):
    sMyVersion = '1.0'

    def make_tree(self):
        dPhys = {}

        for oC in PhysicalCard.select():
            oAbs = oC.abstractCard
            try:
                dPhys[(oAbs.id, oAbs.name, oC.expansion)] += 1
            except KeyError:
                dPhys[(oAbs.id, oAbs.name, oC.expansion)] = 1

        oRoot = Element('cards', sutekh_xml_version=self.sMyVersion)

        for tKey, iNum in dPhys.iteritems():
            iId, sName, oExpansion = tKey
            oCardElem = SubElement(oRoot,'card', id=str(iId))
            oCardElem.attrib['name'] = sName
            if oExpansion is None:
                oCardElem.attrib['expansion'] = 'None Specified'
            else:
                oCardElem.attrib['expansion']= oExpansion.name
            oCardElem.attrib['count'] = str(iNum)

        return oRoot

    def gen_xml_string(self):
        oRoot = self.make_tree()
        # For zip files, we don't bother with prettifying output
        if oRoot:
            return tostring(oRoot)
        else:
            return ''

    def write(self,fOut):
        oRoot = self.make_tree()
        pretty_xml(oRoot)
        ElementTree(oRoot).write(fOut)
