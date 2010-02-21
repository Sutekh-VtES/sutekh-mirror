# SutekhCli.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com> (minor tweaks)
# GPL - see COPYING for details
"""
SutekhCli.py: command-line interface to much of Sutekh's database
management functionality
"""

import sys, optparse, os
from logging import StreamHandler
from sqlobject import sqlhub, connectionForURI
from sutekh.core.SutekhObjects import Ruling, aObjectList, aPhysicalList
from sutekh.SutekhUtility import refresh_tables, read_white_wolf_list, \
        read_rulings, gen_temp_dir, prefs_dir, ensure_dir_exists, sqlite_uri
from sutekh.core.DatabaseUpgrade import attempt_database_upgrade
from sutekh.io.XmlFileHandling import PhysicalCardXmlFile, \
        PhysicalCardSetXmlFile, AbstractCardSetXmlFile, \
        write_all_pcs
from sutekh.io.ZipFileWrapper import ZipFileWrapper
from sutekh.io.WwFile import WwFile
from sutekh.SutekhInfo import SutekhInfo

def parse_options(aArgs):
    """Handle the command line options"""
    oOptParser = optparse.OptionParser(usage="usage: %prog [options]",
            version="%%prog %s" % SutekhInfo.VERSION_STR)
    oOptParser.add_option("-d", "--db",
                  type="string", dest="db", default=None,
                  help="Database URI. [sqlite://$PREFSDIR$/sutekh.db]")
    oOptParser.add_option("-r", "--ww-file",
                  type="string", dest="ww_file", default=None,
                  help="HTML file (probably from WW website) to read " \
                          "cards from.")
    oOptParser.add_option("--ruling-file",
                  type="string", dest="ruling_file", default=None,
                  help="HTML file (probably from WW website) to read " \
                          "rulings from.")
    oOptParser.add_option("-c", "--refresh-tables",
                  action="store_true", dest="refresh_tables", default=False,
                  help="Drop (if possible) and recreate database tables.")
    oOptParser.add_option("--refresh-ruling-tables",
                  action="store_true", dest="refresh_ruling_tables",
                  default=False,
                  help="Drop (if possible) and recreate rulings tables only.")
    oOptParser.add_option("--refresh-physical-card-tables",
                  action="store_true", dest="refresh_physical_card_tables",
                  default=False,
                  help="Drop (if possible) and recreate physical card " \
                          "tables only.")
    oOptParser.add_option("--sql-debug",
                  action="store_true", dest="sql_debug", default=False,
                  help="Print out SQL statements.")
    oOptParser.add_option("-l", "--read-physical-cards-from",
                  type="string", dest="read_physical_cards_from", default=None,
                  help="Read physical card list from the given XML file.")
    oOptParser.add_option("--save-pcs",
                  type="string", dest="save_pcs", default=None,
                  help="Save the given Physical Card Set to an XML file " \
                          "(by default named <pcsname>.xml).")
    oOptParser.add_option("--pcs-filename",
                  type="string", dest="pcs_filename", default=None,
                  help="Give an alternative filename to save the Physical " \
                          "Card Set as")
    oOptParser.add_option("--save-all-pcs",
                  action="store_true", dest="save_all_pcss", default=False,
                  help="Save all Physical Card Sets in the database to files" \
                          " - Cannot be used with --save-pcs.")
    oOptParser.add_option("--read-pcs",
                  type="string", dest="read_pcs", default=None,
                  help="Load a Physical Card Set from the given XML file.")
    oOptParser.add_option("--read-acs",
                  type="string", dest="read_acs", default=None,
                  help="Load an Abstract Card Set from the given XML file.")
    oOptParser.add_option("--reload", action="store_true", dest="reload",
                  default=False,
                  help="Dump all card sets and reload them - intended to be" \
                          " used with -c and refreshing the abstract card" \
                          " list")
    oOptParser.add_option("--upgrade-db",
                  action="store_true", dest="upgrade_db", default=False,
                  help="Attempt to upgrade a database to the latest version." \
                          " Cannot be used with --refresh-tables")
    oOptParser.add_option("--dump-zip",
                  type="string", dest="dump_zip_name", default=None,
                  help="Dump the all the card sets to the given zip file")
    oOptParser.add_option("--restore-zip",
            type="string", dest="restore_zip_name", default=None,
            help="Restore everything from the given zipfile")

    return oOptParser, oOptParser.parse_args(aArgs)

def main():
    """
    Main function: Loop through the options and process the database
    accordingly.
    """
    # Turn off some pylint refactoring warnings
    # pylint: disable-msg=R0915, R0912, R0911
    oOptParser, (oOpts, aArgs) = parse_options(sys.argv)
    sPrefsDir = prefs_dir("Sutekh")

    oLogHandler = StreamHandler(sys.stdout)

    if len(aArgs) != 1:
        oOptParser.print_help()
        return 1

    if oOpts.db is None:
        ensure_dir_exists(sPrefsDir)
        oOpts.db = sqlite_uri(os.path.join(sPrefsDir, "sutekh.db"))

    oConn = connectionForURI(oOpts.db)
    sqlhub.processConnection = oConn

    if oOpts.sql_debug:
        oConn.debug = True

    if oOpts.reload:
        if not oOpts.refresh_tables:
            print "reload should be called with --refresh-tables"
            return 1
        else:
            sTempdir = gen_temp_dir()
            aPhysicalCardSetList = write_all_pcs(sTempdir)
            oPCFile = PhysicalCardXmlFile(dir=sTempdir)
            oPCFile.write()
            # We dump the databases here
            # We will reload them later

    if oOpts.refresh_ruling_tables:
        if not refresh_tables([Ruling], sqlhub.processConnection):
            print "refresh failed"
            return 1

    if oOpts.refresh_tables:
        if not refresh_tables(aObjectList, sqlhub.processConnection):
            print "refresh failed"
            return 1

    if oOpts.refresh_physical_card_tables:
        if not refresh_tables(aPhysicalList, sqlhub.processConnection):
            print "refresh failed"
            return 1

    if not oOpts.ww_file is None:
        read_white_wolf_list([WwFile(oOpts.ww_file)], oLogHandler)

    if not oOpts.ruling_file is None:
        read_rulings(WwFile(oOpts.ruling_file), oLogHandler)

    if not oOpts.read_physical_cards_from is None:
        oFile = PhysicalCardXmlFile(oOpts.read_physical_cards_from)
        oFile.read()

    if oOpts.save_all_pcss and not oOpts.save_pcs is None:
        print "Can't use --save-pcs and --save-all-pcs Simulatenously"
        return 1

    if oOpts.save_all_pcss:
        write_all_pcs()

    if oOpts.dump_zip_name is not None:
        oZipFile = ZipFileWrapper(oOpts.dump_zip_name)
        oZipFile.do_dump_all_to_zip(oLogHandler)

    if oOpts.restore_zip_name is not None:
        oZipFile = ZipFileWrapper(oOpts.restore_zip_name)
        oZipFile.do_restore_from_zip(oLogHandler=oLogHandler)

    if not oOpts.save_pcs is None:
        oFile = PhysicalCardSetXmlFile(oOpts.pcs_filename)
        oFile.write(oOpts.save_pcs)

    if not oOpts.read_pcs is None:
        oFile = PhysicalCardSetXmlFile(oOpts.read_pcs)
        oFile.read()

    if not oOpts.read_acs is None:
        oFile = AbstractCardSetXmlFile(oOpts.read_acs)
        oFile.read()

    if oOpts.reload:
        oPCFile.read()
        oPCFile.delete()
        for oPCSet in aPhysicalCardSetList:
            oPCSet.read()
            oPCSet.delete()
        os.rmdir(sTempdir)

    if oOpts.upgrade_db and oOpts.refresh_tables:
        print "Can't use --upgrade-db and --refresh-tables simulatenously"
        return 1

    if oOpts.upgrade_db:
        attempt_database_upgrade(oLogHandler)

    return 0

if __name__ == "__main__":
    sys.exit(main())
