# SutekhGui.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details
"""SutekhGui.py: start the GUI"""


import gtk
from sutekh.core.SutekhObjects import VersionTable, aObjectList
from sutekh.SutekhUtility import prefs_dir, ensure_dir_exists, sqlite_uri
from sutekh.gui.MultiPaneWindow import MultiPaneWindow
from sutekh.core.DatabaseVersion import DatabaseVersion
from sqlobject import sqlhub, connectionForURI
from sutekh.gui.ConfigFile import ConfigFile
from sutekh.gui.GuiDBManagement import do_db_upgrade, initialize_db
from sutekh.gui.SutekhDialog import do_complaint_error
from sutekh.SutekhInfo import SutekhInfo
import sys, optparse, os, traceback


# Script Launching

def parse_options(aArgs):
    """SutekhGui's option parsing"""
    oOptParser = optparse.OptionParser(usage="usage: %prog [options]",
            version="%%prog %s" % SutekhInfo.VERSION_STR)
    oOptParser.add_option("-d", "--db",
                  type="string", dest="db", default=None,
                  help="Database URI. [sqlite://$PREFSDIR$/sutekh.db]")
    oOptParser.add_option("--ignore-db-version",
                  action="store_true", dest="ignore_db_version", default=False,
                  help="Ignore the database version check. Only use this if " \
                          "you know what you're doing.")
    oOptParser.add_option("--rcfile",
                  type="string", dest="sRCFile", default=None,
                  help="Specify Alternative resources file. " \
                          "[~/.sutekh/sutekhrc or " \
                          "$APPDATA$/Sutekh/sutekhrc]")
    oOptParser.add_option("--sql-debug",
                  action="store_true", dest="sql_debug", default=False,
                  help="Print out SQL statements.")
    oOptParser.add_option("--verbose",
            action="store_true", dest="verbose", default=False,
            help="Display warning messages")
    return oOptParser, oOptParser.parse_args(aArgs)

def exception_handler(oType, oValue, oTraceback):
    """sys.excepthook exception handler."""
    if oType == KeyboardInterrupt:
        # don't complain about KeyboardInterrupts
        return

    sMessage = "Sutekh reported an unhandled exception:\n" \
        "%s\n" % (str(oValue),)

    oErrorDlg = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR,
        gtk.BUTTONS_CLOSE, sMessage)
    oErrorDlg.set_name("Sutekh.dialog")

    aTraceback = traceback.format_exception(oType, oValue, oTraceback)
    oErrorDlg.format_secondary_text("".join(aTraceback))

    # we ignore the response here
    oErrorDlg.run()
    oErrorDlg.destroy()

def main():
    """Start the Sutekh Gui.

       Check that database exists, doesn't need to be upgraded, then
       pass control off to MultiPaneWindow.
       Save preferences on exit if needed
       """
    # handle exceptions with a GUI dialog
    sys.excepthook = exception_handler

    oOptParser, (oOpts, aArgs) = parse_options(sys.argv)
    sPrefsDir = prefs_dir("Sutekh")

    if len(aArgs) != 1:
        oOptParser.print_help()
        return 1

    if oOpts.sRCFile is None:
        ensure_dir_exists(sPrefsDir)
        oOpts.sRCFile = os.path.join(sPrefsDir, "sutekhrc")

    oConfig = ConfigFile(oOpts.sRCFile)

    if oOpts.db is None:
        oOpts.db = oConfig.get_database_uri()

    if oOpts.db is None:
        # No commandline + no rc entry
        ensure_dir_exists(sPrefsDir)
        oOpts.db = sqlite_uri(os.path.join(sPrefsDir, "sutekh.db"))
        oConfig.set_database_uri(oOpts.db)

    oConn = connectionForURI(oOpts.db)
    sqlhub.processConnection = oConn

    if oOpts.sql_debug:
        oConn.debug = True

    # Check we have the correct gtk version
    sMessage = gtk.check_version(2, 10, 0)
    if sMessage is not None:
        do_complaint_error('Incorrect gtk version. Sutekh requires at least'
                ' gtk 2.10.0.\nError reported %s' % sMessage)
        return 1

    # construct Window
    oMultiPaneWindow = MultiPaneWindow()

    # Test on some tables where we specify the table name
    if not oConn.tableExists('abstract_card') or \
            not oConn.tableExists('physical_map'):
        if not initialize_db(oMultiPaneWindow):
            return 1

    aTables = [VersionTable] + aObjectList
    aVersions = []

    for oTable in aTables:
        aVersions.append(oTable.tableversion)

    oVer = DatabaseVersion()

    if not oVer.check_tables_and_versions(aTables, aVersions) and \
            not oOpts.ignore_db_version:
        aLowerTables, aHigherTables =  oVer.get_bad_tables(aTables, aVersions)
        if not do_db_upgrade(aLowerTables, aHigherTables):
            return 1

    oMultiPaneWindow.setup(oConfig, oOpts.verbose)
    oMultiPaneWindow.run()

    # Save Config Changes
    oConfig.write()

if __name__ == "__main__":
    sys.exit(main())


