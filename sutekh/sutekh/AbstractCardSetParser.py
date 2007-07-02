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

from sutekh.SutekhObjects import AbstractCardSet, AbstractCard
from sqlobject import sqlhub, SQLObjectNotFound
from xml.sax import parse, parseString
from xml.sax.handler import ContentHandler

class AbstractCardSetHandler(ContentHandler):
    def __init__(self):
        ContentHandler.__init__(self)
        self.acsDB=False
        self.aUnknown=[]
        self.acsName=None
        self.aSupportedVersions=['1.0','0.0']

    def startElement(self,sTagName,oAttrs):
        if sTagName == 'abstractcardset':
            self.acsName = oAttrs.getValue('name')
            aAttributes=oAttrs.getNames()
            sAuthor=None
            sComment=None
            sAnnotations=None
            if 'author' in aAttributes:
                sAuthor=oAttrs.getValue('author')
            if 'comment' in aAttributes:
                sComment=oAttrs.getValue('comment')
            if 'annotations' in aAttributes:
                sAnnotations=oAttrs.getValue('annotations')
            if 'sutekh_xml_version' in aAttributes:
                sThisVersion=oAttrs.getValue('sutekh_xml_version')
            else:
                sThisVersion='0.0'
            if sThisVersion not in self.aSupportedVersions:
                raise RuntimeError("Unrecognised XML File Version")
            # Try and add acs to AbstractCardSet
            # Make sure
            try:
                acs=AbstractCardSet.byName(self.acsName.encode('utf8'))
                # We overwrite acs, so we drop all cards currently
                # part of the acs
                acs.author=sAuthor
                acs.comment=sComment
                acs.annotations=sAnnotations
                acs.syncUpdate()
                ids=[]
                for card in acs.cards:
                    acs.removeAbstractCard(card.id)
                self.acsDB=True
            except SQLObjectNotFound:
                AbstractCardSet(name=self.acsName,author=sAuthor,comment=sComment)
                self.acsDB=True
        elif sTagName == 'card':
            iId = int(oAttrs.getValue('id'),10)
            sName = oAttrs.getValue('name')
            iCount = int(oAttrs.getValue('count'),10)

            try:
                oAbs = AbstractCard.byCanonicalName(sName.encode('utf8').lower())
            except SQLObjectNotFound:
                self.aUnknown.append(sName)
                oAbs=None
            if self.acsDB and oAbs is not None:
                # acs exists in databse, so we're OK
                acs=AbstractCardSet.byName(self.acsName.encode('utf8'))
                for i in range(iCount):
                    acs.addAbstractCard(oAbs.id)

    def endElement(self,sName):
        pass

    def printUnHandled(self):
        if len(self.aUnknown)>0:
            print "The Following Cards are unknown"
            for sCardName in self.aUnknown:
                print sCardName.encode('utf-8')

class AbstractCardSetParser(object):
    def parse(self,fIn):
        oldConn = sqlhub.processConnection
        sqlhub.processConnection= oldConn.transaction()
        myHandler=AbstractCardSetHandler()
        parse(fIn,myHandler)
        myHandler.printUnHandled()
        sqlhub.processConnection.commit()
        sqlhub.processConnection=oldConn

    def parseString(self,sIn):
        oldConn = sqlhub.processConnection
        sqlhub.processConnection= oldConn.transaction()
        myHandler=AbstractCardSetHandler()
        parseString(sIn,myHandler)
        myHandler.printUnHandled()
        sqlhub.processConnection.commit()
        sqlhub.processConnection=oldConn
