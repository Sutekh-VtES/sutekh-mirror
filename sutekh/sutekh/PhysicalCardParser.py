# PhysicalCardParser.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""
Read physical cards from an XML file which
looks like:
<cards sutekh_xml_version="1.0">
  <card id='3' name='Some Card' count='5' expansion="Some Expansion" />
  <card id='3' name='Some Card' count='2' Expansion="Some Other Expansion" />
  <card id='5' name='Some Other Card' count='2' expansion="Some Expansion" />
</cards>
"""

from sutekh.SutekhObjects import PhysicalCard, AbstractCard
from sqlobject import sqlhub
from xml.sax import parse, parseString
from xml.sax.handler import ContentHandler

class CardHandler(ContentHandler):
    aSupportedVersions=['1.0','0.0']

    def startElement(self,sTagName,oAttrs):
        if sTagName == 'cards':
            aAttributes=oAtters.getNames()
            if 'sutekh_xml_version' in aAttributes:
                sThisVersion=oAttrs.getValue('sutekh_xml_version')
            else:
                sThisVersion='0.0'
            if sThisVersion not in self.aSupportedVersions:
                raise RuntimeError("Unrecognised XML File version")
        elif sTagName == 'card':
            iId = int(oAttrs.getValue('id'),10)
            sName = oAttrs.getValue('name')
            iCount = int(oAttrs.getValue('count'),10)
            if 'expansion' in oAttrs.getNames():
                sExpansionName=oAttrs.getValue('expansion')
            else:
                sExpansionName='None Specified'
            oAbs = AbstractCard.byCanonicalName(sName.encode('utf8').lower())
            for i in range(iCount):
                if sExpansionName!='None Specified':
                    PhysicalCard(abstractCard=oAbs,Expansion=sExpansionName)
                else:
                    PhysicalCard(abstractCard=oAbs)

    def endElement(self,sName):
        pass

class PhysicalCardParser(object):
    def parse(self,fIn):
        oldConn = sqlhub.processConnection
        sqlhub.processConnection= oldConn.transaction()
        parse(fIn,CardHandler())
        sqlhub.processConnection.commit()
        sqlhub.processConnection=oldConn

    def parseString(self,sIn):
        oldConn = sqlhub.processConnection
        sqlhub.processConnection= oldConn.transaction()
        parseString(sIn, CardHandler())
        sqlhub.processConnection.commit()
        sqlhub.processConnection=oldConn
