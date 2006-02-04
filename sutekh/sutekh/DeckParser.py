"""
Read physical cards from an XML file which
looks like:
<deck name='DeckName'>
  <card id='3' name='Some Card' count='5' />
  <card id='5' name='Some Other Card' count='2' />  
</deck>
"""

from SutekhObjects import *
from xml.sax import parse
from xml.sax.handler import ContentHandler

class DeckHandler(ContentHandler):
    def __init__(self):
        ContentHandler.__init__(self)
        self.deckDB=False
        self.unHandled={}
        self.deckName=None
        
    def startElement(self,sTagName,oAttrs):
        if sTagName == 'deck':
            self.deckName = oAttrs.getValue('name')
            # Try and add deck to PhysicalCardSet
            # Make sure 
            try:
                deck=PhysicalCardSet.byName(self.deckName)
                # We overwrite deck, so we drop all cards currently 
                # part of the deck
                ids=[]
                for card in deck.cards:
                    deck.removePhysicalCard(card.id)
                self.deckDB=True
            except SQLObjectNotFound:
                PhysicalCardSet(name=self.deckName)
                self.deckDB=True
        if sTagName == 'card':
            iId = int(oAttrs.getValue('id'),10)
            sName = oAttrs.getValue('name')
            iCount = int(oAttrs.getValue('count'),10)
            
            oAbs = AbstractCard.byName(sName)
            if self.deckDB:
                # deck exists in databse, so we're OK
                deck=PhysicalCardSet.byName(self.deckName)
                for i in range(iCount):
                    # We see if we can add the card, otherwise we add it to the
                    # dictionary of unhandlable cards 
                    # Get all physical IDs that match this card
                    possibleCards=PhysicalCard.selectBy(abstractCardID=oAbs.id)
                    added=False
                    for card in possibleCards:
                        if card not in deck.cards:
                            deck.addPhysicalCard(card.id)
                            added=True
                            break
                    if not added:
                        try:
                            self.unHandled[oAbs.name]+=1
                        except KeyError:
                            self.unHandled[oAbs.name]=1
        
    def endElement(self,sName):
        pass

    def printUnHandled(self):
        if len(self.unHandled)>0:
            print "The Following Cards where unable to be added to the database"
            for CardName, Count in self.unHandled.iteritems():
                print str(Count)+"x "+CardName.encode('utf-8')

class DeckParser(object):
    def parse(self,fIn):
        myHandler=DeckHandler()
        parse(fIn,myHandler)
        myHandler.printUnHandled()
