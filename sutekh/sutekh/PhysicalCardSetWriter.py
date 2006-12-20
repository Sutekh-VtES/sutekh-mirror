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

from SutekhObjects import *
from xml.dom.ext import PrettyPrint
from xml.dom.minidom import getDOMImplementation

class PhysicalCardSetWriter(object):
    def write(self,fOut,sPhysicalCardSetName):
        dPhys = {}

        try:
            oPCS = PhysicalCardSet.byName(sPhysicalCardSetName)
            sAuthor=oPCS.author
            sComment=oPCS.comment
        except SQLObjectNotFound:
            return

        for oC in oPCS.cards:
            oAbs = oC.abstractCard
            try:
                dPhys[(oAbs.id, oAbs.name)] += 1
            except KeyError:
                dPhys[(oAbs.id, oAbs.name)] = 1

        oDoc = getDOMImplementation().createDocument(None,'physicalcardset',None)

        oCardsElem = oDoc.firstChild
        oCardsElem.setAttribute('name',sPhysicalCardSetName)
        oCardsElem.setAttribute('author',sAuthor)
        oCardsElem.setAttribute('comment',sComment)

        for tKey, iNum in dPhys.iteritems():
            iId, sName = tKey
            oCardElem = oDoc.createElement('card')
            oCardElem.setAttribute('id',str(iId))
            oCardElem.setAttribute('name',sName)
            oCardElem.setAttribute('count',str(iNum))
            oCardsElem.appendChild(oCardElem)

        PrettyPrint(oDoc,fOut)
