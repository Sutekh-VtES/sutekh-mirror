# SutekhGui.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

from sutekh.SutekhObjects import *
from sutekh.SutekhUtility import *
from sutekh.SutekhCli import *
from sutekh.gui.MainController import MainController
from sutekh.gui.DBErrorPopup import DBVerErrorPopup, NoDBErrorPopup
from sutekh.gui.DBUpgradeDialog import DBUpgradeDialog
from sutekh.gui.WWFilesDialog import WWFilesDialog
from sutekh.DatabaseVersion import DatabaseVersion
from sutekh.DatabaseUpgrade import *
from sqlobject import *
import gtk
import sys, optparse, os

# Script Launching

def parseOptions(aArgs):
    oP = optparse.OptionParser(usage="usage: %prog [options]",version="%prog 0.1")
    oP.add_option("-d","--db",
                  type="string",dest="db",default=None,
                  help="Database URI. [sqlite://$PWD/sutekh.db]")
    oP.add_option("--ignore-db-version",action="store_true",
            dest="ignore_db_version",default=False,
            help="Ignore the database version check. Only use this if you know what you're doing")
    return oP, oP.parse_args(aArgs)

def main(aArgs):
    oOptParser, (oOpts, aArgs) = parseOptions(aArgs)

    if len(aArgs) != 1:
        oOptParser.print_help()
        return 1

    if oOpts.db is None:
        oOpts.db = "sqlite://" + "/".join([os.getcwd().replace(os.sep,"/"),"sutekh.db"])

    oConn = connectionForURI(oOpts.db)
    sqlhub.processConnection = oConn

    # Test on some tables where we specify the table name
    if not oConn.tableExists('abstract_map') or not oConn.tableExists('physical_map'):
        diag=NoDBErrorPopup()
        res=diag.run()
        diag.destroy()
        if res!=1:
            return 1
        else:
            Dlg=WWFilesDialog(None)
            Dlg.run()
            (sCLFilename,sRulingsFilename)=Dlg.getNames()
            Dlg.destroy()
            if sCLFilename is not None:
                refreshTables(ObjectList,oConn)
                readWhiteWolfList(sCLFilename)
                if sRulingsFilename is not None:
                    readRulings(sRulingsFilename)
            else:
                return 1

    aTables=[VersionTable]+ObjectList
    aVersions=[]

    for oTable in aTables:
        aVersions.append(oTable.tableversion)

    oVer=DatabaseVersion()

    if not oVer.checkVersions(aTables,aVersions) and not oOpts.ignore_db_version:
        aBadTables=oVer.getBadTables(aTables,aVersions)
        diag=DBVerErrorPopup(aBadTables)
        res=diag.run()
        diag.destroy()
        if res!=1:
            return 1
        else:
            tempConn=connectionForURI("sqlite:///:memory:")
            try:
                if createMemoryCopy(tempConn):
                    diag=DBUpgradeDialog()
                    res=diag.run()
                    diag.destroy()
                    if res==gtk.RESPONSE_OK:
                        createFinalCopy(tempConn)
                        print "Changes Committed"
                    elif res==1:
                        # Try with the upgraded database
                        sqlhub.processConnection=tempConn
                    else:
                        return 1
                else:
                    diag=gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,\
                            gtk.BUTTONS_CLOSE,None)
                    diag.set_markup("Unable to create memory copy. Upgrade Failed")
                    diag.run()
                    return 1
            except unknownVersion, err:
                diag=gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,\
                        gtk.BUTTONS_CLOSE,None)
                diag.set_markup("Upgrade Failed. "+str(err))
                diag.run()
                return 1

    MainController().run()


if __name__ == "__main__":
    sys.exit(main(sys.argv))


