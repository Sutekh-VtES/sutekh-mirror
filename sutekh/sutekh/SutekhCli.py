# SutekhCli.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Minor modifications copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import sys, optparse, os, codecs
from sqlobject import *
from SutekhObjects import *
from WhiteWolfParser import WhiteWolfParser
from RulingParser import RulingParser
from PhysicalCardParser import PhysicalCardParser
from PhysicalCardWriter import PhysicalCardWriter
from DeckParser import DeckParser
from DeckWriter import DeckWriter

def parseOptions(aArgs):
    oP = optparse.OptionParser(usage="usage: %prog [options]",version="%prog 0.1")
    oP.add_option("-d","--db",
                  type="string",dest="db",default=None,
                  help="Database URI. [./sutekh.db]")
    oP.add_option("-r","--ww-file",
                  type="string",dest="ww_file",default=None,
                  help="HTML file (probably from WW website) to read cards from.")
    oP.add_option("--ruling-file",
                  type="string",dest="ruling_file",default=None,
                  help="HTML file (probably from WW website) to read rulings from.")
    oP.add_option("-c","--refresh-tables",
                  action="store_true",dest="refresh_tables",default=False,
                  help="Drop (if possible) and recreate database tables.")
    oP.add_option("--refresh-ruling-tables",
                  action="store_true",dest="refresh_ruling_tables",default=False,
                  help="Drop (if possible) and recreate rulings tables only.")
    oP.add_option("--refresh-physical-card-tables",
                  action="store_true",dest="refresh_physical_card_tables",default=False,
                  help="Drop (if possible) and recreate physical card tables only.")
    oP.add_option("--sql-debug",
                  action="store_true",dest="sql_debug",default=False,
                  help="Print out SQL statements.")
    oP.add_option("-s","--save-physical-cards-to",
                  type="string",dest="save_physical_cards_to",default=None,
                  help="Write an XML description of the list of physical cards to the given file.")
    oP.add_option("-l","--read-physical-cards-from",
                  type="string",dest="read_physical_cards_from",default=None,
                  help="Read physical card list from the given XML file.")                   
    oP.add_option("--save-deck",
                  type="string",dest="save_deck",default=None,
                  help="Save the given deck to an XML file (by default named <deckname>.xml).")
    oP.add_option("--deck-filename",
                  type="string",dest="deck_filename",default=None,
                  help="Give an alternative filename to save the deck as")
    oP.add_option("--save-all-decks",
                  action="store_true",dest="save_all_decks",default=False,
                  help="Save all decks in the database to files - Cannot be used with --save-deck.")
    oP.add_option("--read-deck",
                  type="string",dest="read_deck",default=None,
                  help="Load a deck from the given XML file.")
    oP.add_option("--reload",action="store_true",dest="reload",default=False,
                  help="Dump physical card list and decks and reload them - \
intended to be used with -c and refreshing the abstract card list")
                  
    return oP, oP.parse_args(aArgs)

def refreshTables(aTables,**kw):
    aTables.reverse()
    for cCls in aTables:
        cCls.dropTable(ifExists=True)
    aTables.reverse()
    for cCls in aTables:
        cCls.createTable()

def readWhiteWolfList(sWwList):
    oP = WhiteWolfParser()
    fIn = codecs.open(sWwList,'rU','cp1252')
    for sLine in fIn:
        oP.feed(sLine)
    fIn.close()

def readRulings(sRulings):
    oP = RulingParser()
    fIn = codecs.open(sRulings,'rU','cp1252')
    for sLine in fIn:
        oP.feed(sLine)
    fIn.close()

def readPhysicalCards(sXmlFile):
    oP = PhysicalCardParser()
    oP.parse(file(sXmlFile,'rU'))

def writePhysicalCards(sXmlFile):
    oW = PhysicalCardWriter()
    fOut = file(sXmlFile,'w')
    oW.write(fOut)
    fOut.close()

def readDeck(sXmlFile):
    oP = DeckParser()
    oP.parse(file(sXmlFile,'rU'))

def writeDeck(sDeckName,sXmlFile):
    oW = DeckWriter()
    if sXmlFile is None:
        filename=sDeckName.replace(" ","_") # I hate spaces in filenames
        fOut=file(filename,'w')
    else:
        fOut=file(sXmlFile,'w')
    oW.write(fOut,sDeckName)
    fOut.close()

def writeAllDecks(prefix=''):
    oDecks = PhysicalCardSet.select()
    aList=[];
    for deck in oDecks:
        filename=prefix+deck.name.replace(" ","_")
        aList.append(filename)
        writeDeck(deck.name,filename)
    return aList

def main(aArgs):
    oOptParser, (oOpts, aArgs) = parseOptions(aArgs)
    
    if len(aArgs) != 1:
        oOptParser.print_help()
        return 1
        
    if oOpts.db is None:
        oOpts.db = "sqlite://" + os.path.join(os.getcwd(),"sutekh.db")

    oConn = connectionForURI(oOpts.db)
    sqlhub.processConnection = oConn
    
    if oOpts.sql_debug:
        oConn.debug = True

    if oOpts.reload:
        if not oOpts.refresh_tables:
            print "reload should be called with --refresh-tables"
            return 1
        else:
            prefix='reload_dump_'
            aDeckList=writeAllDecks(prefix)
            sCardList=prefix+'PhysCardList'
            writePhysicalCards(sCardList)
            # We dump the databases here
            # We will reload them later
    
    if oOpts.refresh_ruling_tables:
        refreshTables([Ruling])
    
    if oOpts.refresh_tables:
        refreshTables(ObjectList)
        
    if oOpts.refresh_physical_card_tables:
        refreshTables([PhysicalCard])
    
    if not oOpts.ww_file is None:
        readWhiteWolfList(oOpts.ww_file)
        
    if not oOpts.ruling_file is None:
        readRulings(oOpts.ruling_file)
        
    if not oOpts.read_physical_cards_from is None:
        readPhysicalCards(oOpts.read_physical_cards_from)

    if not oOpts.save_physical_cards_to is None:
        writePhysicalCards(oOpts.save_physical_cards_to)

    if oOpts.save_all_decks and not oOpts.save_deck is None:
        print "Can't use --save-deck and --save-all-decks Simulatenously"
        return 1

    if oOpts.save_all_decks:
        writeAllDecks()

    if not oOpts.save_deck is None:
        writeDeck(oOpts.save_deck,oOpts.deck_filename)

    if not oOpts.read_deck is None:
        readDeck(oOpts.read_deck)

    if oOpts.reload:
        readPhysicalCards(sCardList)
        for deck in aDeckList:
            readDeck(deck)


    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
