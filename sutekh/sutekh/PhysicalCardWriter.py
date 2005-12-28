"""
Write physical cards out to an XML file which
looks like:
<cards>
  <card id='3' name='Some Card' count='5' />
  <card id='5' name='Some Other Card' count='2' />  
</cards>
"""

from SutekhObjects import *
from xml.dom.ext import PrettyPrint
from xml.dom.minidom import getDOMImplementation

class PhysicalCardWriter(object):
    def write(self,fOut):
        dPhys = {}
    
        for oC in PhysicalCard.select():
            oAbs = oC.abstractCard
            try:
                dPhys[(oAbs.id, oAbs.name)] += 1
            except KeyError:
                dPhys[(oAbs.id, oAbs.name)] = 1

        oDoc = getDOMImplementation().createDocument(None,'cards',None)
        oCardsElem = oDoc.firstChild
                
        for tKey, iNum in dPhys.iteritems():
            iId, sName = tKey
            oCardElem = oDoc.createElement('card')
            oCardElem.setAttribute('id',str(iId))
            oCardElem.setAttribute('name',sName)
            oCardElem.setAttribute('count',str(iNum))
            oCardsElem.appendChild(oCardElem)
            
        PrettyPrint(oDoc,fOut)
