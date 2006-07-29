# SutekhGui.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import sys, optparse, os
from sqlobject import *
from SutekhObjects import *
from gui.MainController import MainController
        
# Script Launching    

def parseOptions(aArgs):
    oP = optparse.OptionParser(usage="usage: %prog [options]",version="%prog 0.1")
    oP.add_option("-d","--db",
                  type="string",dest="db",default=None,
                  help="Database URI. [sqlite://$PWD/sutekh.db]")
    return oP, oP.parse_args(aArgs)

def main(aArgs):
    oOptParser, (oOpts, aArgs) = parseOptions(aArgs)
    
    if len(aArgs) != 1:
        oOptParser.print_help()
        return 1
        
    if oOpts.db is None:
        oOpts.db = "sqlite://" + os.path.join(os.getcwd(),"sutekh.db")

    oConn = connectionForURI(oOpts.db)
    sqlhub.processConnection = oConn

    aTables=[VersionTable]+ObjectList
    aVersions=[]

    for oTable in aTables:
        aVersions.append(oTable.tableversion)

    oVer=DatabaseVersion()

    if not oVer.checkVersions(aTables,aVersions):
        print "Unsupported database Version."
        return 1

    MainController().run()


if __name__ == "__main__":
    sys.exit(main(sys.argv))


