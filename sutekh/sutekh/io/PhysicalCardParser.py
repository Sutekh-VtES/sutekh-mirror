# PhysicalCardParser.py
# Copyright 2005,2006,2007 Simon Cross <hodgestar@gmail.com>
#                     2007 Neil Muller <drnlmuller+sutekh@gmail.com>
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

from sutekh.core.CardSetHolder import CardSetHolder
from sutekh.core.CardLookup import DEFAULT_LOOKUP
from sqlobject import sqlhub
from xml.sax import parse, parseString
from xml.sax.handler import ContentHandler

class CardHandler(ContentHandler):
    aSupportedVersions = ['1.0', '0.0']

    def __init__(self):
        self.oCS = CardSetHolder()

    def startElement(self, sTagName, oAttrs):
        if sTagName == 'cards':
            aAttributes = oAttrs.getNames()
            if 'sutekh_xml_version' in aAttributes:
                sThisVersion = oAttrs.getValue('sutekh_xml_version')
            else:
                sThisVersion = '0.0'
            if sThisVersion not in self.aSupportedVersions:
                raise RuntimeError("Unrecognised XML File version")
        elif sTagName == 'card':
            sName = oAttrs.getValue('name')
            iCount = int(oAttrs.getValue('count'), 10)
            if 'expansion' in oAttrs.getNames():
                sExpansionName = oAttrs.getValue('expansion')
            else:
                sExpansionName = 'None Specified'
            if sExpansionName == 'None Specified':
                self.oCS.add(iCount, sName, None)
            else:
                self.oCS.add(iCount, sName, sExpansionName)

    def endElement(self, sName):
        pass

class PhysicalCardParser(object):
    def parse(self, fIn, oCardLookup=DEFAULT_LOOKUP):
        oMyHandler = CardHandler()
        parse(fIn, oMyHandler)
        oOldConn = sqlhub.processConnection
        sqlhub.processConnection = oOldConn.transaction()
        oMyHandler.oCS.createPhysicalCardList(oCardLookup)
        sqlhub.processConnection.commit()
        sqlhub.processConnection = oOldConn

    def parseString(self, sIn, oCardLookup=DEFAULT_LOOKUP):
        oMyHandler = CardHandler()
        parseString(sIn, oMyHandler)
        oOldConn = sqlhub.processConnection
        sqlhub.processConnection = oOldConn.transaction()
        oMyHandler.oCS.createPhysicalCardList(oCardLookup)
        sqlhub.processConnection.commit()
        sqlhub.processConnection = oOldConn
