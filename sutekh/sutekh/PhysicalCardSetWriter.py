# PhysicalCardSetWriter.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Minor modifications copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""
Write physical cards from a PhysicalCardSet out to an XML file which
looks like:
<physicalcardset name='SetName'>
  <card id='3' name='Some Card' count='5' />
  <card id='5' name='Some Other Card' count='2' />
</physicalcardset>
"""

from sutekh.SutekhObjects import PhysicalCardSet
from sqlobject import SQLObjectNotFound
from xml.dom.ext import PrettyPrint
from xml.dom.minidom import getDOMImplementation

class PhysicalCardSetWriter(object):
    sMyVersion="1.0"

    def genDoc(self,sPhysicalCardSetName):
        dPhys = {}

        try:
            oPCS = PhysicalCardSet.byName(sPhysicalCardSetName)
            sAuthor=oPCS.author
            sComment=oPCS.comment
            sAnnotations=oPCS.annotations
        except SQLObjectNotFound:
            return

        for oC in oPCS.cards:
            oAbs = oC.abstractCard
            try:
                dPhys[(oAbs.id, oAbs.name, oC.expansion)] += 1
            except KeyError:
                dPhys[(oAbs.id, oAbs.name, oC.expansion)] = 1

        oDoc = getDOMImplementation().createDocument(None,'physicalcardset',None)

        oCardsElem = oDoc.firstChild
        oCardsElem.setAttribute('sutekh_xml_version',self.sMyVersion)
        oCardsElem.setAttribute('name',sPhysicalCardSetName)
        oCardsElem.setAttribute('author',sAuthor)
        oCardsElem.setAttribute('comment',sComment)
        oCardsElem.setAttribute('annotations',sAnnotations)

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

    def write(self,fOut,sPhysicalCardSetName):
        oDoc=self.genDoc(sPhysicalCardSetName)
        PrettyPrint(oDoc,fOut)
