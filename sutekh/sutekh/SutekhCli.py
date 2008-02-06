# SutekhCli.py
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Minor modifications copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import sys, optparse, os
from logging import StreamHandler
from sqlobject import sqlhub, connectionForURI
from sutekh.core.SutekhObjects import Ruling, ObjectList, PhysicalList
from sutekh.SutekhUtility import refreshTables, readWhiteWolfList, \
        readRulings, genTempdir, prefsDir, ensureDirExists, sqliteUri
from sutekh.core.DatabaseUpgrade import attempt_database_upgrade
from sutekh.io.XmlFileHandling import PhysicalCardXmlFile, \
        PhysicalCardSetXmlFile, AbstractCardSetXmlFile, \
        writeAllAbstractCardSets, writeAllPhysicalCardSets
from sutekh.io.ZipFileWrapper import ZipFileWrapper

def parseOptions(aArgs):
    oP = optparse.OptionParser(usage="usage: %prog [options]",
            version="%prog 0.1")
    oP.add_option("-d", "--db",
                  type="string", dest="db", default=None,
                  help="Database URI. [sqlite://$PREFSDIR$/sutekh.db]")
    oP.add_option("-r", "--ww-file",
                  type="string", dest="ww_file", default=None,
                  help="HTML file (probably from WW website) to read cards from.")
    oP.add_option("--ruling-file",
                  type="string", dest="ruling_file", default=None,
                  help="HTML file (probably from WW website) to read rulings from.")
    oP.add_option("-c", "--refresh-tables",
                  action="store_true", dest="refresh_tables", default=False,
                  help="Drop (if possible) and recreate database tables.")
    oP.add_option("--refresh-ruling-tables",
                  action="store_true", dest="refresh_ruling_tables",
                  default=False,
                  help="Drop (if possible) and recreate rulings tables only.")
    oP.add_option("--refresh-physical-card-tables",
                  action="store_true", dest="refresh_physical_card_tables",
                  default=False,
                  help="Drop (if possible) and recreate physical card tables only.")
    oP.add_option("--sql-debug",
                  action="store_true", dest="sql_debug", default=False,
                  help="Print out SQL statements.")
    oP.add_option("-s", "--save-physical-cards-to",
                  type="string", dest="save_physical_cards_to", default=None,
                  help="Write an XML description of the list of physical cards to the given file.")
    oP.add_option("-l", "--read-physical-cards-from",
                  type="string", dest="read_physical_cards_from", default=None,
                  help="Read physical card list from the given XML file.")
    oP.add_option("--save-pcs",
                  type="string", dest="save_pcs", default=None,
                  help="Save the given Physical Card Set to an XML file (by default named <pcsname>.xml).")
    oP.add_option("--pcs-filename",
                  type="string", dest="pcs_filename", default=None,
                  help="Give an alternative filename to save the Physical Card Set as")
    oP.add_option("--save-all-pcs",
                  action="store_true", dest="save_all_pcss", default=False,
                  help="Save all Physical Card Sets in the database to files - Cannot be used with --save-pcs.")
    oP.add_option("--read-pcs",
                  type="string", dest="read_pcs", default=None,
                  help="Load a Physical Card Set from the given XML file.")
    oP.add_option("--save-acs",
                  type="string", dest="save_acs", default=None,
                  help="Save the given Abstract Card Set to an XML file (by default named <acsname>.xml).")
    oP.add_option("--acs-filename",
                  type="string", dest="acs_filename", default=None,
                  help="Give an alternative filename to save the Abstract Card Set as")
    oP.add_option("--save-all-acs",
                  action="store_true", dest="save_all_acss", default=False,
                  help="Save all Abstract Card Sets in the database to files - Cannot be used with --save-acs.")
    oP.add_option("--read-acs",
                  type="string", dest="read_acs", default=None,
                  help="Load an Abstract Card Set from the given XML file.")
    oP.add_option("--reload", action="store_true", dest="reload",
                  default=False,
                  help="Dump the physical card list and all card sets and reload them - \
intended to be used with -c and refreshing the abstract card list")
    oP.add_option("--upgrade-db",
                  action="store_true", dest="upgrade_db", default=False,
                  help="Attempt to upgrade a database to the latest version. Cannot be used with --refresh-tables")
    oP.add_option("--dump-zip",
                  type="string", dest="dump_zip_name", default=None,
                  help="Dump the PhysicalCard list and all the CardSets to the given zipfile")
    oP.add_option("--restore-zip",
            type="string", dest="restore_zip_name", default=None,
            help="Restore everything from the given zipfile")

    return oP, oP.parse_args(aArgs)

def main(aArgs):
    oOptParser, (oOpts, aArgs) = parseOptions(aArgs)
    sPrefsDir = prefsDir("Sutekh")

    oLogHandler = StreamHandler(sys.stdout)

    if len(aArgs) != 1:
        oOptParser.print_help()
        return 1

    if oOpts.db is None:
        ensureDirExists(sPrefsDir)
        oOpts.db = sqliteUri(os.path.join(sPrefsDir, "sutekh.db"))

    oConn = connectionForURI(oOpts.db)
    sqlhub.processConnection = oConn

    if oOpts.sql_debug:
        oConn.debug = True

    if oOpts.reload:
        if not oOpts.refresh_tables:
            print "reload should be called with --refresh-tables"
            return 1
        else:
            sTempdir = genTempdir()
            aPhysicalCardSetList = writeAllPhysicalCardSets(sTempdir)
            aAbstractCardSetList = writeAllAbstractCardSets(sTempdir)
            oPCFile = PhysicalCardXmlFile(dir=sTempdir)
            oPCFile.write()
            # We dump the databases here
            # We will reload them later

    if oOpts.refresh_ruling_tables:
        if not refreshTables([Ruling], sqlhub.processConnection):
            print "refresh failed"
            return 1

    if oOpts.refresh_tables:
        if not refreshTables(ObjectList, sqlhub.processConnection):
            print "refresh failed"
            return 1

    if oOpts.refresh_physical_card_tables:
        if not refreshTables(PhysicalList, sqlhub.processConnection):
            print "refresh failed"
            return 1

    if not oOpts.ww_file is None:
        readWhiteWolfList(oOpts.ww_file, oLogHandler)

    if not oOpts.ruling_file is None:
        readRulings(oOpts.ruling_file, oLogHandler)

    if not oOpts.read_physical_cards_from is None:
        oFile = PhysicalCardXmlFile(oOpts.rad_physical_cards_from)
        oFile.read()

    if not oOpts.save_physical_cards_to is None:
        oPCF = PhysicalCardXmlFile(filename=oOpts.save_physical_cards_to)
        oPCF.write()

    if oOpts.save_all_acss and not oOpts.save_acs is None:
        print "Can't use --save-acs and --save-all-acs Simulatenously"
        return 1

    if oOpts.save_all_pcss and not oOpts.save_pcs is None:
        print "Can't use --save-pcs and --save-all-pcs Simulatenously"
        return 1

    if oOpts.save_all_acss:
        writeAllAbstractCardSets()

    if oOpts.save_all_pcss:
        writeAllPhysicalCardSets()

    if oOpts.dump_zip_name is not None:
        oZipFile = ZipFileWrapper(oOpts.dump_zip_name)
        oZipFile.doDumpAllToZip(oLogHandler)

    if oOpts.restore_zip_name is not None:
        oZipFile = ZipFileWrapper(oOpts.restore_zip_name)
        oZipFile.doRestoreFromZip(oLogHandler)

    if not oOpts.save_pcs is None:
        oFile = PhysicalCardSetXmlFile(oOpts.pcs_filename)
        oFile.write(oOpts.save_pcs)

    if not oOpts.save_acs is None:
        oFile = AbstractCardSetXmlFile(oOpts.acs_filename)
        oFile.write(oOpts.save_acs)

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
        for oACSet in aAbstractCardSetList:
            oACSet.read()
            oACSet.delete()
        os.rmdir(sTempdir)

    if oOpts.upgrade_db and oOpts.refresh_tables:
        print "Can't use --upgrade-db and --refresh-tables simulatenously"
        return 1

    if oOpts.upgrade_db:
        attempt_database_upgrade(oLogHandler)

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
