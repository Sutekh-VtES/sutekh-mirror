# PhysicalCardSetParser.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Minor modifications copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""
Read physical cards from an XML file which
looks like:
<physicalcardset name='PhysicalCardSetName'>
  <card id='3' name='Some Card' count='5' />
  <card id='5' name='Some Other Card' count='2' />
</physicalcardset>
into a PhysicalCardSet
"""

from SutekhObjects import *
from sqlobject import *
from xml.sax import parse, parseString
from xml.sax.handler import ContentHandler

class PhysicalCardSetHandler(ContentHandler):
    def __init__(self):
        ContentHandler.__init__(self)
        self.pcsDB=False
        self.dUnhandled={}
        self.aUnknown=[]
        self.pcsName=None

    def startElement(self,sTagName,oAttrs):
        if sTagName == 'physicalcardset':
            self.pcsName = oAttrs.getValue('name')
            sAuthor=oAttrs.getValue('author')
            sComment=oAttrs.getValue('comment')
            # Try and add pcs to PhysicalCardSet
            # Make sure
            try:
                pcs=PhysicalCardSet.byName(self.pcsName.encode('utf8'))
                pcs.author=sAuthor
                pcs.comment=sComment
                pcs.syncUpdate()
                # We overwrite pcs, so we drop all cards currently
                # part of the PhysicalCardSet
                ids=[]
                for card in pcs.cards:
                    pcs.removePhysicalCard(card.id)
                self.pcsDB=True
            except SQLObjectNotFound:
                PhysicalCardSet(name=self.pcsName,author=sAuthor,comment=sComment)
                self.pcsDB=True
        if sTagName == 'card':
            iId = int(oAttrs.getValue('id'),10)
            sName = oAttrs.getValue('name')
            iCount = int(oAttrs.getValue('count'),10)

            try:
                oAbs = AbstractCard.byName(sName.encode('utf8'))
            except SQLObjectNotFound:
                oAbs=None
                self.aUnknown.append(sName)
            if self.pcsDB and oAbs is not None:
                # pcs exists in databse, so we're OK
                pcs=PhysicalCardSet.byName(self.pcsName.encode('utf8'))
                for i in range(iCount):
                    # We see if we can add the card, otherwise we add it to the
                    # dictionary of unhandlable cards
                    # Get all physical IDs that match this card
                    possibleCards=PhysicalCard.selectBy(abstractCardID=oAbs.id)
                    added=False
                    for card in possibleCards:
                        if card not in pcs.cards:
                            pcs.addPhysicalCard(card.id)
                            added=True
                            break
                    if not added:
                        try:
                            self.dUnhandled[oAbs.name]+=1
                        except KeyError:
                            self.dUnhandled[oAbs.name]=1

    def endElement(self,sName):
        pass

    def printUnHandled(self):
        if len(self.aUnknown)>0:
            print "The Following Cards are unknown"
            for sCardName in self.aUnknown:
                print sCardName.encode('utf-8')
        if len(self.dUnhandled)>0:
            print "The Following Cards where unable to be added to the database"
            for sCardName, iCount in self.dUnhandled.iteritems():
                print str(iCount)+"x "+sCardName.encode('utf-8')

class PhysicalCardSetParser(object):
    def parse(self,fIn):
        oldConn = sqlhub.processConnection
        sqlhub.processConnection= oldConn.transaction()
        myHandler=PhysicalCardSetHandler()
        parse(fIn,myHandler)
        myHandler.printUnHandled()
        sqlhub.processConnection.commit()
        sqlhub.processConnection=oldConn

    def parseString(self,sIn):
        oldConn = sqlhub.processConnection
        sqlhub.processConnection= oldConn.transaction()
        myHandler=PhysicalCardSetHandler()
        parseString(sIn,myHandler)
        myHandler.printUnHandled()
        sqlhub.processConnection.commit()
        sqlhub.processConnection=oldConn
