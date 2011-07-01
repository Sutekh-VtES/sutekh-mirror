# SutekhGui.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details
"""SutekhGui.py: start the GUI"""


import gtk
import logging
import sys
import optparse
import os
import traceback
from sqlobject import sqlhub, connectionForURI
from sutekh.core.SutekhObjects import VersionTable, TABLE_LIST
from sutekh.SutekhUtility import prefs_dir, ensure_dir_exists, sqlite_uri
from sutekh.gui.MultiPaneWindow import MultiPaneWindow
from sutekh.core.DatabaseVersion import DatabaseVersion
from sutekh.gui.ConfigFile import ConfigFile
from sutekh.gui.ConfigFileLegacy import ConfigFileLegacy
from sutekh.gui.GuiDBManagement import do_db_upgrade, initialize_db
from sutekh.gui.SutekhDialog import do_complaint_error, do_complaint_warning, \
        do_exception_complaint, do_complaint_error_details
from sutekh.SutekhInfo import SutekhInfo


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
    oOptParser.add_option("--error-log",
            type="string", dest="sErrFile", default=None,
            help="File to log messages to. Defaults to no logging")
    return oOptParser, oOptParser.parse_args(aArgs)


def exception_handler(oType, oValue, oTraceback):
    """sys.excepthook exception handler."""
    if oType == KeyboardInterrupt:
        # don't complain about KeyboardInterrupts
        return

    sMessage = "Sutekh reported an unhandled exception:\n" \
        "%s\n" % (str(oValue),)
    aTraceback = traceback.format_exception(oType, oValue, oTraceback)

    logging.error("%s:\n%s", sMessage, "".join(aTraceback))
    # Log before we show the dialog, otherwise, if there's an exception while
    # the progress bar update hack is ongoing, the error dialog won't work
    # correctly, and the exception may be lost

    do_complaint_error_details(sMessage, "".join(aTraceback))


def setup_logging(oOpts):
    """Setup the log handling for this run"""
    # Only log critical messages by default
    oRootLogger = logging.getLogger()
    oRootLogger.setLevel(level=logging.CRITICAL)
    if oOpts.verbose or oOpts.sErrFile:
        # Change logging level to debug
        oRootLogger.setLevel(logging.DEBUG)
        bSkipVerbose = False
        if oOpts.sErrFile:
            try:
                oLogHandler = logging.FileHandler(oOpts.sErrFile)
                oRootLogger.addHandler(oLogHandler)
            except IOError:
                oLogHandler = logging.StreamHandler(sys.stderr)
                oRootLogger.addHandler(oLogHandler)
                bSkipVerbose = True  # Avoid doubled logging to stderr
                logging.error('Unable to open log file, logging to stderr',
                        exc_info=1)
        if oOpts.verbose and not bSkipVerbose:
            # Add logging to stderr
            oLogHandler = logging.StreamHandler(sys.stderr)
            oRootLogger.addHandler(oLogHandler)
    else:
        # Setup fallback logger for critical messages
        oLogHandler = logging.StreamHandler(sys.stderr)
        oRootLogger.addHandler(oLogHandler)
    return oRootLogger


def main():
    # pylint: disable-msg=R0912, R0914, R0915
    # lots of different cases to consider, so long and has lots of variables
    # and if statement
    """Start the Sutekh Gui.

       Check that database exists, doesn't need to be upgraded, then
       pass control off to MultiPaneWindow.
       Save preferences on exit if needed
       """
    # Print nice complaint if not under a windowing system
    if gtk.gdk.screen_get_default() is None:
        print "Unable to find windowing system. Aborting"
        return 1
    # handle exceptions with a GUI dialog
    sys.excepthook = exception_handler

    # Disable Unity's moving of menubars to the appmenu at
    # the top of the screen since this moves the panel menus
    # into limbo.
    # TODO: we should only disable this on the panel menus
    os.environ["UBUNTU_MENUPROXY"] = "0"

    oOptParser, (oOpts, aArgs) = parse_options(sys.argv)
    sPrefsDir = prefs_dir("Sutekh")

    if len(aArgs) != 1:
        oOptParser.print_help()
        return 1

    if oOpts.sRCFile is None:
        ensure_dir_exists(sPrefsDir)
        oOpts.sRCFile = os.path.join(sPrefsDir, "sutekh.ini")
        if not os.path.isfile(oOpts.sRCFile):
            # look for old sutekhrc config file
            sLegacyConfigFile = os.path.join(sPrefsDir, "sutekhrc")
            if os.path.isfile(sLegacyConfigFile):
                oLegacyConfig = ConfigFileLegacy(sLegacyConfigFile)
                oNewConfig = oLegacyConfig.convert(oOpts.sRCFile)
                # Call check_writeable just to set the right flags.
                # If it's not writeable, the later check will complain
                # as required.
                oNewConfig.check_writeable()
                oNewConfig.write()

    oConfig = ConfigFile(oOpts.sRCFile)
    # initial config validation to set sane defaults
    # (re-validated later after plugins are loaded)
    oConfig.validate()

    if not oConfig.check_writeable():
        # Warn the user
        iRes = do_complaint_warning('Unable to write to the config file %s.\n'
                'Config changes will NOT be saved.\n'
                'Do you wish to continue?' % oOpts.sRCFile)
        if iRes == gtk.RESPONSE_CANCEL:
            return 1

    if oOpts.db is None:
        oOpts.db = oConfig.get_database_uri()

    if oOpts.db is None:
        # No commandline + no rc entry
        ensure_dir_exists(sPrefsDir)
        oOpts.db = sqlite_uri(os.path.join(sPrefsDir, "sutekh.db?cache=False"))
        oConfig.set_database_uri(oOpts.db)

    oConn = connectionForURI(oOpts.db)
    sqlhub.processConnection = oConn

    if oOpts.sql_debug:
        oConn.debug = True

    # Check we have the correct gtk version
    sMessage = gtk.check_version(2, 16, 0)
    if sMessage is not None:
        do_complaint_error('Incorrect gtk version. Sutekh requires at least'
                ' gtk 2.16.0.\nError reported %s' % sMessage)
        return 1

    # construct Window
    oMultiPaneWindow = MultiPaneWindow()

    # Test on some tables where we specify the table name
    if not oConn.tableExists('abstract_card') or \
            not oConn.tableExists('physical_map'):
        if not initialize_db(oMultiPaneWindow):
            return 1

    aTables = [VersionTable] + TABLE_LIST
    aVersions = []

    for oTable in aTables:
        aVersions.append(oTable.tableversion)

    oVer = DatabaseVersion()

    if not oVer.check_tables_and_versions(aTables, aVersions) and \
            not oOpts.ignore_db_version:
        aLowerTables, aHigherTables = oVer.get_bad_tables(aTables, aVersions)
        if not do_db_upgrade(aLowerTables, aHigherTables):
            return 1

    _oRootLogger = setup_logging(oOpts)

    oMultiPaneWindow.setup(oConfig)
    oMultiPaneWindow.run()

    # Save Config Changes
    try:
        oConfig.write()
    except IOError, oExp:
        sMesg = 'Unable to write the configuration file\n' \
                'Error was: %s' % oExp
        do_exception_complaint(sMesg)

    logging.shutdown()


if __name__ == "__main__":
    sys.exit(main())
