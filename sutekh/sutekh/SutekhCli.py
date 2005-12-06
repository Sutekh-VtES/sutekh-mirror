import sys, optparse, os, codecs
from sqlobject import *
from SutekhObjects import *
from WhiteWolfParser import WhiteWolfParser
from RulingParser import RulingParser

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
    oP.add_option("--sql-debug",
                  action="store_true",dest="sql_debug",default=False,
                  help="Print out SQL statements.")
    return oP, oP.parse_args(aArgs)

def refreshTables(aTables,**kw):
    for cCls in aTables:
        cCls.dropTable(ifExists=True)
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
    
    if oOpts.refresh_ruling_tables:
        refreshTables([Ruling])
    
    if oOpts.refresh_tables:
        refreshTables(ObjectList)        
    
    if not oOpts.ww_file is None:
        readWhiteWolfList(oOpts.ww_file)
        
    if not oOpts.ruling_file is None:
        readRulings(oOpts.ruling_file)

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
