# SutekhGui.py
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

from sutekh.core.SutekhObjects import VersionTable, ObjectList
from sutekh.SutekhUtility import refreshTables, readRulings, readWhiteWolfList, \
                                 prefsDir, ensureDirExists, sqliteUri
from sutekh.gui.MainController import MainController
from sutekh.gui.DBErrorPopup import DBVerErrorPopup, NoDBErrorPopup
from sutekh.gui.DBUpgradeDialog import DBUpgradeDialog
from sutekh.gui.WWFilesDialog import WWFilesDialog
from sutekh.core.DatabaseVersion import DatabaseVersion
from sutekh.core.DatabaseUpgrade import createMemoryCopy, createFinalCopy, UnknownVersion
from sqlobject import sqlhub, connectionForURI
from sutekh.gui.ConfigFile import ConfigFile
import gtk
import sys, optparse, os

# Script Launching

def parseOptions(aArgs):
    oP = optparse.OptionParser(usage="usage: %prog [options]",
            version="%prog 0.1")
    oP.add_option("-d", "--db",
                  type="string", dest="db", default=None,
                  help="Database URI. [sqlite://$PREFSDIR$/sutekh.db]")
    oP.add_option("--ignore-db-version",
                  action="store_true", dest="ignore_db_version", default=False,
                  help="Ignore the database version check. Only use this if you know what you're doing.")
    oP.add_option("--rcfile",
                  type="string", dest="sRCFile", default=None,
                  help="Specify Alternative resources file. [~/.sutekh/sutekhrc or $APPDATA$/Sutekh/sutekhrc]")
    oP.add_option("--sql-debug",
                  action="store_true", dest="sql_debug", default=False,
                  help="Print out SQL statements.")
    return oP, oP.parse_args(aArgs)

def main(aArgs):
    oOptParser, (oOpts, aArgs) = parseOptions(aArgs)
    sPrefsDir = prefsDir("Sutekh")

    if len(aArgs) != 1:
        oOptParser.print_help()
        return 1

    if oOpts.sRCFile is None:
        ensureDirExists(sPrefsDir)
        oOpts.sRCFile = os.path.join(sPrefsDir, "sutekhrc")

    if oOpts.db is None:
        ensureDirExists(sPrefsDir)
        oOpts.db = sqliteUri(os.path.join(sPrefsDir, "sutekh.db"))

    oConfig = ConfigFile(oOpts.sRCFile)

    oConn = connectionForURI(oOpts.db)
    sqlhub.processConnection = oConn

    if oOpts.sql_debug:
        oConn.debug = True

    # Test on some tables where we specify the table name
    if not oConn.tableExists('abstract_map') or not oConn.tableExists('physical_map'):
        oDialog = NoDBErrorPopup()
        iRes = oDialog.run()
        oDialog.destroy()
        if iRes != 1:
            return 1
        else:
            oDialog = WWFilesDialog(None)
            oDialog.run()
            (sCLFilename, sRulingsFilename, bIgnore) = oDialog.getNames()
            oDialog.destroy()
            if sCLFilename is not None:
                refreshTables(ObjectList, oConn)
                readWhiteWolfList(sCLFilename)
                if sRulingsFilename is not None:
                    readRulings(sRulingsFilename)
            else:
                return 1

    aTables = [VersionTable]+ObjectList
    aVersions = []

    for oTable in aTables:
        aVersions.append(oTable.tableversion)

    oVer = DatabaseVersion()

    if not oVer.checkVersions(aTables, aVersions) and \
            not oOpts.ignore_db_version:
        aBadTables = oVer.getBadTables(aTables, aVersions)
        oDialog = DBVerErrorPopup(aBadTables)
        iRes = oDialog.run()
        oDialog.destroy()
        if iRes != 1:
            return 1
        else:
            oTempConn = connectionForURI("sqlite:///:memory:")
            try:
                (bOK, aMessages) = createMemoryCopy(oTempConn)
                if bOK:
                    oDialog = DBUpgradeDialog(aMessages)
                    iRes = oDialog.run()
                    oDialog.destroy()
                    if iRes == gtk.RESPONSE_OK:
                        (bOK, aMessages) = createFinalCopy(oTempConn)
                        if bOK:
                            oDialog = gtk.MessageDialog(None, 0, 
                                    gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, None)
                            sMesg = "Changes Commited\n"
                            if len(aMessages)>0:
                                sMesg += "Messages reported are:\n"
                                for sStr in aMessages:
                                    sMesg += sStr + "\n"
                            else:
                                sMesg += "Everything seems to have gone smoothly."
                            oDialog.set_markup(sMesg)
                            oDialog.run()
                            oDialog.destroy()
                        else:
                            sMesg = "Unable to commit updated database!\n"
                            for sStr in aMessages:
                                sMesg += sStr+"\n"
                            sMesg += "Upgrade Failed.\nYour database may be in an inconsistent state."
                            oDialog = gtk.MessageDialog(None, 0, 
                                    gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE, None)
                            oDialog.set_markup(sMesg)
                            oDialog.run()
                            oDialog.destroy()
                            return 1
                    elif iRes == 1:
                        # Try with the upgraded database
                        sqlhub.processConnection = oTempConn
                    else:
                        return 1
                else:
                    sMesg = "Unable to create memory copy!\n"
                    for sStr in aMessages:
                        sMesg += sStr + "\n"
                    sMesg += "Upgrade Failed."
                    oDialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR,
                            gtk.BUTTONS_CLOSE, None)
                    oDialog.set_markup(sMesg)
                    oDialog.run()
                    oDialog.destroy()
                    return 1
            except UnknownVersion, err:
                oDialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR,
                        gtk.BUTTONS_CLOSE, None)
                oDialog.set_markup("Upgrade Failed. " + str(err))
                oDialog.run()
                oDialog.destroy()
                return 1

    MainController(oConfig).run()

    # Save Config Changes
    oConfig.write()


if __name__ == "__main__":
    sys.exit(main(sys.argv))


