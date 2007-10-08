# PhysicalCardSetParser.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Minor modifications copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""
Read physical cards from an XML file which
looks like:
<physicalcardset name='SetName' author='Author' comment='Comment' annotations='annotations'>
  <card id='3' name='Some Card' count='5' expansion='Some Expansion' />
  <card id='3' name='Some Card' count='2' expansion='Some Other Expansion' />
  <card id='5' name='Some Other Card' count='2' expansion='Some Other Expansion' />
</physicalcardset>
into a PhysicalCardSet
"""

from sutekh.core.CardSetHolder import CardSetHolder
from sutekh.core.CardLookup import DEFAULT_LOOKUP
from sqlobject import sqlhub
from xml.sax import parse, parseString
from xml.sax.handler import ContentHandler

class PhysicalCardSetHandler(ContentHandler):
    aSupportedVersions = ['1.0', '0.0']

    def __init__(self):
        ContentHandler.__init__(self)
        self.oCS = CardSetHolder()

    def startElement(self, sTagName, oAttrs):
        if sTagName == 'physicalcardset':
            sPCSName = oAttrs.getValue('name')
            aAttributes = oAttrs.getNames()
            sAuthor = None
            sComment = None
            sAnnotations = None
            if 'author' in aAttributes:
                sAuthor = oAttrs.getValue('author')
            if 'comment' in aAttributes:
                sComment = oAttrs.getValue('comment')
            if 'annotations' in aAttributes:
                sAnnotations = oAttrs.getValue('annotations')
            if 'sutekh_xml_version' in aAttributes:
                sThisVersion = oAttrs.getValue('sutekh_xml_version')
            else:
                sThisVersion = '0.0'
            if sThisVersion not in self.aSupportedVersions:
                raise RuntimeError("Unrecognised XML file version")
            self.oCS.name = sPCSName
            self.oCS.author = sAuthor
            self.oCS.comment = sComment
            self.oCS.annotations = sAnnotations
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

class PhysicalCardSetParser(object):
    def parse(self, fIn, oCardLookup=DEFAULT_LOOKUP):
        oMyHandler = PhysicalCardSetHandler()
        parse(fIn, oMyHandler)
        oOldConn = sqlhub.processConnection
        sqlhub.processConnection = oOldConn.transaction()
        oMyHandler.oCS.createPCS(oCardLookup)
        sqlhub.processConnection.commit()
        sqlhub.processConnection = oOldConn

    def parseString(self, sIn, oCardLookup=DEFAULT_LOOKUP):
        oMyHandler = PhysicalCardSetHandler()
        parseString(sIn, oMyHandler)
        oOldConn = sqlhub.processConnection
        sqlhub.processConnection = oOldConn.transaction()
        oMyHandler.oCS.createPCS(oCardLookup)
        sqlhub.processConnection.commit()
        sqlhub.processConnection = oOldConn
