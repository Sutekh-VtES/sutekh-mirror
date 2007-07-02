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

from sutekh.SutekhObjects import PhysicalCardSet, AbstractCard, PhysicalCard
from sqlobject import sqlhub, SQLObjectNotFound
from xml.sax import parse, parseString
from xml.sax.handler import ContentHandler

class PhysicalCardSetHandler(ContentHandler):
    def __init__(self):
        ContentHandler.__init__(self)
        self.pcsDB=False
        self.dUnhandled={}
        self.aUnknown=[]
        self.pcsName=None
        self.aSupportedVersions=['1.0','0.0']

    def startElement(self,sTagName,oAttrs):
        if sTagName == 'physicalcardset':
            self.pcsName = oAttrs.getValue('name')
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
                raise RuntimeError("Unrecognised XML file version")
            # Try and add pcs to PhysicalCardSet
            # Make sure
            try:
                pcs=PhysicalCardSet.byName(self.pcsName.encode('utf8'))
                pcs.author=sAuthor
                pcs.comment=sComment
                acs.annotations=sAnnotations
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
        elif sTagName == 'card':
            iId = int(oAttrs.getValue('id'),10)
            sName = oAttrs.getValue('name')
            iCount = int(oAttrs.getValue('count'),10)
            if 'expansion' in oAttrs.getNames():
                sExpansionName=oAttrs.getValue('expansion')
            else:
                sExpansionName='None Specified'

            try:
                oAbs = AbstractCard.byCanonicalName(sName.encode('utf8').lower())
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
                    if sExpansionName=='None Specified':
                        for card in possibleCards:
                            if card not in pcs.cards:
                                pcs.addPhysicalCard(card.id)
                                added=True
                                break
                    else:
                        # Only add cards if the expansion matches
                        # Do we need to do a best match if expansion
                        # doesn't match??
                        for card in possibleCards:
                            if card not in pcs.cards and \
                                    card.expansion==sExpansionName:
                                pcs.addPhysicalCard(card.id)
                                added=True
                                break
                    if not added:
                        try:
                            self.dUnhandled[(oAbs.name,sExpansionName)]+=1
                        except KeyError:
                            self.dUnhandled[(oAbs.name,sExpansionName)]=1

    def endElement(self,sName):
        pass

    def printUnHandled(self):
        if len(self.aUnknown)>0:
            print "The Following Cards are unknown"
            for sCardName in self.aUnknown:
                print sCardName.encode('utf-8')
        if len(self.dUnhandled)>0:
            print "The Following Cards where unable to be added to the database"
            for tKey, iCount in self.dUnhandled.iteritems():
                sCardName,sExpansionName=tKey
                print str(iCount)+"x "+sCardName.encode('utf-8')," from expansion ",sExpansionName

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
