# PhysicalCardWrite.py
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
from xml.dom.minidom import getDOMImplementation

class PhysicalCardWriter(object):
    sMyVersion = '1.0'

    def genDoc(self):
        dPhys = {}

        for oC in PhysicalCard.select():
            oAbs = oC.abstractCard
            try:
                dPhys[(oAbs.id, oAbs.name, oC.expansion)] += 1
            except KeyError:
                dPhys[(oAbs.id, oAbs.name, oC.expansion)] = 1

        oDoc = getDOMImplementation().createDocument(None,'cards',None)
        oCardsElem = oDoc.firstChild
        oCardsElem.setAttribute('sutekh_xml_version',self.sMyVersion)

        for tKey, iNum in dPhys.iteritems():
            iId, sName, sExpansion = tKey
            oCardElem = oDoc.createElement('card')
            oCardElem.setAttribute('id',str(iId))
            oCardElem.setAttribute('name',sName)
            if sExpansion is None:
                oCardElem.setAttribute('expansion','None Specified')
            else:
                oCardElem.setAttribute('expansion',sExpansion)
            oCardElem.setAttribute('count',str(iNum))
            oCardsElem.appendChild(oCardElem)

        return oDoc

    def write(self,fOut):
        oDoc = self.genDoc()
        fOut.write(oDoc.toprettyxml())
