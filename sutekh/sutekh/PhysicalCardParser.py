# PhysicalCardParser.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""
Read physical cards from an XML file which
looks like:
<cards>
  <card id='3' name='Some Card' count='5' />
  <card id='5' name='Some Other Card' count='2' />  
</cards>
"""

from SutekhObjects import *
from xml.sax import parse
from xml.sax.handler import ContentHandler

class CardHandler(ContentHandler):
    def startElement(self,sTagName,oAttrs):
        if sTagName == 'card':
            iId = int(oAttrs.getValue('id'),10)
            sName = oAttrs.getValue('name')
            iCount = int(oAttrs.getValue('count'),10)

            oAbs = AbstractCard.byName(sName.encode('utf8'))
            for i in range(iCount):
                PhysicalCard(abstractCard=oAbs)

    def endElement(self,sName):
        pass

class PhysicalCardParser(object):
    def parse(self,fIn):
        parse(fIn,CardHandler())
