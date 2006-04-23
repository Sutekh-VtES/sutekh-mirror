# DeckParser.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Minor modifications copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""
Write physical cards from a PhysicalCardSet out to an XML file which
looks like:
<deck name='DeckName'>
  <card id='3' name='Some Card' count='5' />
  <card id='5' name='Some Other Card' count='2' />  
</deck>
"""

from SutekhObjects import *
from xml.dom.ext import PrettyPrint
from xml.dom.minidom import getDOMImplementation

class DeckWriter(object):
    def write(self,fOut,sDeckName):
        dPhys = {}

        try:
            oPCS = PhysicalCardSet.byName(sDeckName)
        except SQLObjectNotFound:
            return 
    
        for oC in oPCS.cards:
            oAbs = oC.abstractCard
            try:
                dPhys[(oAbs.id, oAbs.name)] += 1
            except KeyError:
                dPhys[(oAbs.id, oAbs.name)] = 1

        oDoc = getDOMImplementation().createDocument(None,'deck',None)
        
        oCardsElem = oDoc.firstChild
        oCardsElem.setAttribute('name',sDeckName)

        for tKey, iNum in dPhys.iteritems():
            iId, sName = tKey
            oCardElem = oDoc.createElement('card')
            oCardElem.setAttribute('id',str(iId))
            oCardElem.setAttribute('name',sName)
            oCardElem.setAttribute('count',str(iNum))
            oCardsElem.appendChild(oCardElem)
            
        PrettyPrint(oDoc,fOut)
