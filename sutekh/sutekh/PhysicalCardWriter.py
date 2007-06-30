# PhysicalCardWrite.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""
Write physical cards out to an XML file which
looks like:
<cards>
  <card id='3' name='Some Card' count='5' />
  <card id='5' name='Some Other Card' count='2' />  
</cards>
"""

from sutekh.SutekhObjects import PhysicalCard
from xml.dom.ext import PrettyPrint
from xml.dom.minidom import getDOMImplementation

class PhysicalCardWriter(object):
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
        oCardsElem.setAttribute('sutekh_xml_version','1.0')

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
        oDoc=self.genDoc()
        PrettyPrint(oDoc,fOut)
