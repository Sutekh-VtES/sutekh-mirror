# AbstractCardSetParser.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Minor modifications copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""
Read cards from an XML file which
looks like:
<abstractcardset name='AbstractCardSetName' author='Author' comment='Comment' annotations='annotations'>
  <card id='3' name='Some Card' count='5' />
  <card id='5' name='Some Other Card' count='2' />
</abstractcardset>
into a AbstractCardSet
"""

from sutekh.core.CardSetHolder import CardSetHolder
from sutekh.core.CardLookup import DEFAULT_LOOKUP
from sqlobject import sqlhub
from xml.sax import parse, parseString
from xml.sax.handler import ContentHandler

class AbstractCardSetHandler(ContentHandler):
    def __init__(self):
        ContentHandler.__init__(self)
        self.acsDB = False
        self.aUnknown = []
        self.sACSName = None
        self.aSupportedVersions = ['1.0', '0.0']
        self.oCS = None

    def startElement(self, sTagName, oAttrs):
        if sTagName == 'abstractcardset':
            self.sACSName = oAttrs.getValue('name')
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
                raise RuntimeError("Unrecognised XML File Version")
            # Setup the virtual cardset
            self.oCS = CardSetHolder()
            self.oCS.name = self.sACSName
            self.oCS.author = sAuthor
            self.oCS.comment = sComment
            self.oCS.annotations = sAnnotations
        elif sTagName == 'card':
            sName = oAttrs.getValue('name')
            iCount = int(oAttrs.getValue('count'), 10)

            if self.oCS is not None:
                # Add card to virtual cardset
                self.oCS.add(iCount, sName)

    def endElement(self, sName):
        pass

class AbstractCardSetParser(object):
    def parse(self, fIn, oCardLookup=DEFAULT_LOOKUP):
        oMyHandler = AbstractCardSetHandler()
        parse(fIn, oMyHandler)
        oOldConn = sqlhub.processConnection
        sqlhub.processConnection = oOldConn.transaction()
        oMyHandler.oCS.createACS(oCardLookup)
        sqlhub.processConnection.commit()
        sqlhub.processConnection = oOldConn

    def parseString(self, sIn, oCardLookup=DEFAULT_LOOKUP):
        oMyHandler = AbstractCardSetHandler()
        parseString(sIn, oMyHandler)
        oOldConn = sqlhub.processConnection
        sqlhub.processConnection = oOldConn.transaction()
        oMyHandler.oCS.createACS(oCardLookup)
        sqlhub.processConnection.commit()
        sqlhub.processConnection = oOldConn
