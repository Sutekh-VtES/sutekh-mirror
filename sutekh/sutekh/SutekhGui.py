# SutekhGui.py
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details
"SutekhGui.py: start the GUI"

from sutekh.core.SutekhObjects import VersionTable, ObjectList
from sutekh.SutekhUtility import prefs_dir, ensure_dir_exists, sqlite_uri
from sutekh.gui.MultiPaneWindow import MultiPaneWindow
from sutekh.core.DatabaseVersion import DatabaseVersion
from sqlobject import sqlhub, connectionForURI
from sutekh.gui.ConfigFile import ConfigFile
from sutekh.gui.GuiDBManagement import do_db_upgrade, initialize_db
import sys, optparse, os

# Script Launching

def parse_options(aArgs):
    "SutekhGui's option parsing"
    oOptParser = optparse.OptionParser(usage="usage: %prog [options]",
            version="%prog 0.1")
    oOptParser.add_option("-d", "--db",
                  type="string", dest="db", default=None,
                  help="Database URI. [sqlite://$PREFSDIR$/sutekh.db]")
    oOptParser.add_option("--ignore-db-version",
                  action="store_true", dest="ignore_db_version", default=False,
                  help="Ignore the database version check. Only use this if you know what you're doing.")
    oOptParser.add_option("--rcfile",
                  type="string", dest="sRCFile", default=None,
                  help="Specify Alternative resources file. [~/.sutekh/sutekhrc or $APPDATA$/Sutekh/sutekhrc]")
    oOptParser.add_option("--sql-debug",
                  action="store_true", dest="sql_debug", default=False,
                  help="Print out SQL statements.")
    return oOptParser, oOptParser.parse_args(aArgs)

def main(aArgs):
    """
    Start the Sutekh Gui.
    Check that database exists, doesn't need to be upgraded, then
    pass control off to MultiPaneWindow.
    Save preferences on exit if needed
    """
    oOptParser, (oOpts, aArgs) = parse_options(aArgs)
    sPrefsDir = prefs_dir("Sutekh")

    if len(aArgs) != 1:
        oOptParser.print_help()
        return 1

    if oOpts.sRCFile is None:
        ensure_dir_exists(sPrefsDir)
        oOpts.sRCFile = os.path.join(sPrefsDir, "sutekhrc")

    if oOpts.db is None:
        ensure_dir_exists(sPrefsDir)
        oOpts.db = sqlite_uri(os.path.join(sPrefsDir, "sutekh.db"))

    oConfig = ConfigFile(oOpts.sRCFile)

    oConn = connectionForURI(oOpts.db)
    sqlhub.processConnection = oConn

    if oOpts.sql_debug:
        oConn.debug = True

    # Test on some tables where we specify the table name
    if not oConn.tableExists('abstract_map') or \
            not oConn.tableExists('physical_map'):
        if not initialize_db():
            return 1

    aTables = [VersionTable]+ObjectList
    aVersions = []

    for oTable in aTables:
        aVersions.append(oTable.tableversion)

    oVer = DatabaseVersion()

    if not oVer.checkVersions(aTables, aVersions) and \
            not oOpts.ignore_db_version:
        aBadTables =  oVer.getBadTables(aTables, aVersions)
        if not do_db_upgrade(aBadTables):
            return 1
    MultiPaneWindow(oConfig).run()

    # Save Config Changes
    oConfig.write()

if __name__ == "__main__":
    sys.exit(main(sys.argv))


