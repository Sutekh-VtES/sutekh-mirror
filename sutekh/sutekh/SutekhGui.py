# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details
"""SutekhGui.py: start the GUI"""


import logging
import sys
import optparse
import os

from sqlobject import sqlhub, connectionForURI


# pylint: disable=wrong-import-position, wrong-import-order, ungrouped-imports
# We need to call fix_gui_env before we can import gi and specify versions,
# and we need to import Gtk before importing the rest of the gui stuff,
# so we need to order imports oddly.
from sutekh.base.Utility import (prefs_dir, ensure_dir_exists, sqlite_uri,
                                 setup_logging, fix_gui_env)

fix_gui_env()

# import gi and specify required versions
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')

from sutekh.base.gui.GuiUtils import prepare_gui, load_config, save_config
from sutekh.base.gui.SutekhDialog import exception_handler

from sutekh.SutekhInfo import SutekhInfo

from sutekh.gui.SutekhMainWindow import SutekhMainWindow
from sutekh.gui.ConfigFile import ConfigFile
# pylint: enable=wrong-import-position, wrong-import-order, ungrouped-imports


def parse_options(aArgs):
    """SutekhGui's option parsing"""
    oOptParser = optparse.OptionParser(
        usage="usage: %prog [options]",
        version="%%prog %s" % SutekhInfo.VERSION_STR)
    oOptParser.add_option("-d", "--db",
                          type="string", dest="db", default=None,
                          help="Database URI. [sqlite://$PREFSDIR$/sutekh.db]")
    oOptParser.add_option("--ignore-db-version",
                          action="store_true", dest="ignore_db_version",
                          default=False, help="Ignore the database version "
                                              "check. Only use this if you "
                                              "know what you're doing.")
    oOptParser.add_option("--rcfile", type="string", dest="sRCFile",
                          default=None, help="Specify Alternative resources "
                                             "file. [~/.sutekh/sutekhrc or "
                                             "$APPDATA$/Sutekh/sutekhrc]")
    oOptParser.add_option("--sql-debug", action="store_true",
                          dest="sql_debug", default=False,
                          help="Print out SQL statements.")
    oOptParser.add_option("--verbose", action="store_true", dest="verbose",
                          default=False, help="Display warning messages")
    oOptParser.add_option("--error-log", type="string", dest="sErrFile",
                          default=None, help="File to log messages to. "
                                             "Defaults to no logging")
    oOptParser.add_option("--run-plugin-checks", action="store_true",
                          dest="run_plugin_checks", default=False,
                          help="Run checks for various plugins."
                               " Used to find missing data and so forth"
                               " for plugins that support this")
    return oOptParser, oOptParser.parse_args(aArgs)


def main():
    # pylint: disable=too-many-branches, too-many-locals, too-many-statements
    # lots of different cases to consider, so long and has lots of variables
    # and if statement
    """Start the Sutekh Gui.

       Check that database exists, doesn't need to be upgraded, then
       pass control off to SutekhMainWindow
       Save preferences on exit if needed
       """
    if not prepare_gui(SutekhInfo.NAME):
        return 1

    # handle exceptions with a GUI dialog
    sys.excepthook = exception_handler

    oOptParser, (oOpts, aArgs) = parse_options(sys.argv)
    sPrefsDir = prefs_dir(SutekhInfo.NAME)

    if len(aArgs) != 1:
        oOptParser.print_help()
        return 1

    if oOpts.sRCFile is None:
        ensure_dir_exists(sPrefsDir)
        oOpts.sRCFile = os.path.join(sPrefsDir, "sutekh.ini")

    oConfig = load_config(ConfigFile, oOpts.sRCFile)
    if not oConfig:
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

    # construct Window
    oMainWindow = SutekhMainWindow()

    if not oMainWindow.do_db_checks(oConn, oConfig, oOpts.ignore_db_version):
        return 1

    _oRootLogger = setup_logging(oOpts.verbose, oOpts.sErrFile)

    oMainWindow.setup(oConfig)
    if oOpts.run_plugin_checks:
        oMainWindow.run_plugin_checks()
    oMainWindow.run()

    # Save Config Changes
    save_config(oConfig)

    logging.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
