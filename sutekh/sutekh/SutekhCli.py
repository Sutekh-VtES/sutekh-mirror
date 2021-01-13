# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com> (minor tweaks)
# GPL - see COPYING for details
"""
SutekhCli.py: command-line interface to much of Sutekh's database
management functionality
"""

from __future__ import print_function

import sys
import optparse
import os
import tempfile
from io import StringIO
from logging import StreamHandler
from sqlobject import sqlhub, connectionForURI, SQLObjectNotFound
from sutekh.base.core.BaseTables import Ruling, PHYSICAL_LIST, AbstractCard
from sutekh.base.core.BaseAdapters import IPhysicalCardSet, IAbstractCard
from sutekh.core.SutekhTables import TABLE_LIST
# pylint: disable=unused-import
# We need this import to ensure we have all the filters imported
# correctly, even though we don't use it directly
import sutekh.core.Filters
# pylint: enable=unused-import
from sutekh.SutekhUtility import (read_white_wolf_list, read_rulings,
                                  gen_temp_dir, is_crypt_card,
                                  format_text, read_exp_info_file,
                                  read_lookup_data, do_card_checks,
                                  keyword_sort_key)
from sutekh.base.core.DBUtility import refresh_tables, make_adapter_caches
from sutekh.base.Utility import (ensure_dir_exists, prefs_dir, sqlite_uri,
                                 setup_logging, fix_ssl_env)
from sutekh.core.DatabaseUpgrade import DBUpgradeManager
from sutekh.base.core.CardSetHolder import CardSetWrapper
from sutekh.base.CliUtils import (run_filter, print_card_filter_list,
                                  print_card_list, do_print_card)
from sutekh.io.XmlFileHandling import (PhysicalCardXmlFile,
                                       PhysicalCardSetXmlFile,
                                       AbstractCardSetXmlFile,
                                       write_all_pcs)
from sutekh.io.WriteArdbText import WriteArdbText
from sutekh.io.ZipFileWrapper import ZipFileWrapper
from sutekh.base.io.EncodedFile import EncodedFile
from sutekh.io.WwUrls import (WW_CARDLIST_URL, WW_RULINGS_URL,
                              EXTRA_CARD_URL, EXP_DATA_URL,
                              LOOKUP_DATA_URL)
from sutekh.SutekhInfo import SutekhInfo

def parse_options(aArgs):
    """Handle the command line options"""
    oOptParser = optparse.OptionParser(
        usage="usage: %prog [options]",
        version="%%prog %s" % SutekhInfo.VERSION_STR)
    oOptParser.add_option("-d", "--db", type="string", dest="db",
                          default=None,
                          help="Database URI. [sqlite://$PREFSDIR$/sutekh.db]")
    oOptParser.add_option("-r", "--ww-file", type="string", dest="ww_file",
                          default=None, help="Text file (probably from the"
                                             " VEKN website) to read cards"
                                             " from.")
    oOptParser.add_option("-e", "--extra-file", type="string",
                          dest="extra_file", default=None,
                          help="Text file to read extra storyline cards "
                               "from.")
    oOptParser.add_option("--ruling-file", type="string",
                          dest="ruling_file", default=None,
                          help="HTML file (probably from VEKN website) "
                               "to read rulings from.")
    oOptParser.add_option("--exp-data-file", type="string",
                          dest="exp_data_file",
                          default=None, help="JSON file to read expansion "
                                             "release date info from.")
    oOptParser.add_option("--lookup-data-file", type="string",
                          dest="lookup_file", default=None,
                          help="CSV file to read useful lookup data from.")
    oOptParser.add_option("-c", "--refresh-tables", action="store_true",
                          dest="refresh_tables", default=False,
                          help="Drop (if possible) and recreate database "
                               "tables.")
    oOptParser.add_option("--refresh-ruling-tables", action="store_true",
                          dest="refresh_ruling_tables", default=False,
                          help="Drop (if possible) and recreate rulings "
                               "tables only.")
    oOptParser.add_option("--refresh-physical-card-tables",
                          action="store_true",
                          dest="refresh_physical_card_tables", default=False,
                          help="Drop (if possible) and recreate physical "
                               "card tables only.")
    oOptParser.add_option("--sql-debug", action="store_true",
                          dest="sql_debug", default=False,
                          help="Print out SQL statements.")
    oOptParser.add_option("-l", "--read-physical-cards-from", type="string",
                          dest="read_physical_cards_from", default=None,
                          help="Read physical card list from the given "
                               "XML file.")
    oOptParser.add_option("--save-cs", type="string", dest="save_cs",
                          default=None, help="Save the given Card Set to "
                                             "an XML file (by default named "
                                             "<csname>.xml).")
    oOptParser.add_option("--cs-filename", type="string", dest="cs_filename",
                          default=None, help="Give an alternative filename "
                                             "to save the Card Set as")
    oOptParser.add_option("--save-all-cs", action="store_true",
                          dest="save_all_css", default=False,
                          help="Save all Card Sets in the database to "
                               "files - Cannot be used with --save-cs.")
    oOptParser.add_option("--read-cs", type="string", dest="read_cs",
                          default=None, help="Load a Card Set from the given "
                                             "XML file.")
    oOptParser.add_option("--read-acs", type="string", dest="read_acs",
                          default=None, help="Load an Abstract Card Set from "
                                             "the given XML file.")
    oOptParser.add_option("--reload", action="store_true", dest="reload",
                          default=False, help="Dump all card sets and reload "
                                              "them - intended to be used "
                                              "with -c and refreshing the "
                                              "abstract card list")
    oOptParser.add_option("--upgrade-db", action="store_true",
                          dest="upgrade_db", default=False,
                          help="Attempt to upgrade a database to the latest "
                               "version. Cannot be used with "
                               "--refresh-tables")
    oOptParser.add_option("--dump-zip", type="string", dest="dump_zip_name",
                          default=None, help="Dump the all the card sets to "
                                             "the given zip file")
    oOptParser.add_option("--restore-zip", type="string",
                          dest="restore_zip_name", default=None,
                          help="Restore everything from the given zipfile")
    oOptParser.add_option("--print-cs", type="string", dest="print_cs",
                          default=None, help="Print the given card set "
                                             "(ARDB Text format)")
    oOptParser.add_option("--list-cs", action="store_true", dest="list_cs",
                          default=False, help="Print a formatted list of all "
                                              "the card sets in the database")
    oOptParser.add_option("--limit-list-to", type="string", dest="limit_list",
                          default=None, help="Limit the printed list to the "
                                             "children of the given card set")
    oOptParser.add_option("--filter", type="string", dest="filter_string",
                          default=None, help="Filter to run on the database")
    oOptParser.add_option("--filter-cs", type="string", dest="filter_cs",
                          default=None,
                          help="card set to filter. If not specified, filter "
                               "the WW card list")
    oOptParser.add_option("--filter-detailed", action="store_true",
                          dest="filter_detailed", default=False,
                          help="Print card details for filter results, "
                               "rather than just card names")
    oOptParser.add_option("--print-card", type="string", dest="print_card",
                          default=None,
                          help="Print the details of the given card")
    oOptParser.add_option("--print-encoding", type="string",
                          dest="print_encoding", default='ascii',
                          help="Encoding to use when printing output")
    oOptParser.add_option("--verbose", action="store_true", dest="verbose",
                          default=False, help="Display warning messages")
    oOptParser.add_option("--fetch-files", action="store_true", dest="fetch",
                          default=False,
                          help="Fetch the rulings, WW cardlist and extra card "
                               "text files from their respective default "
                               "sites. Should be used with the -c option to "
                               "refresh the database contents")

    return oOptParser, oOptParser.parse_args(aArgs)


def print_card_details(oCard):
    """Print the details of a given card"""
    # pylint: disable=too-many-branches
    # Several cases to consider, so many branches
    if not oCard.cardtype:
        print(u'CardType: Unknown')
    else:
        sOutput = u'CardType: %s' % u' / '.join(
            [oT.name for oT in oCard.cardtype])
        print(sOutput)
    if oCard.clan:
        sOutput = u'Clan: %s' % u' / '.join([oC.name for oC in oCard.clan])
        print(sOutput)
    if oCard.creed:
        sOutput = u'Creed: %s' % u' / '.join([oC.name for oC in oCard.creed])
        print(sOutput)
    if oCard.capacity:
        sOutput = u'Capacity: %d' % oCard.capacity
        print(sOutput)
    if oCard.life:
        sOutput = u'Life: %d' % oCard.life
        print(sOutput)
    if oCard.group:
        if oCard.group == -1:
            sOutput = u'Group: Any'
        else:
            sOutput = u'Group: %d' % oCard.group
        print(sOutput)
    if oCard.cost is not None:
        if oCard.cost == -1:
            sOutput = u'Cost: X %s' % oCard.costtype
        else:
            sOutput = u'Cost: %d %s' % (oCard.cost, oCard.costtype)
        print(sOutput)
    if oCard.keywords:
        aKeywords = [oK.keyword for oK in oCard.keywords]
        aKeywords.sort(key=keyword_sort_key)
        sOutput = u'   '.join(aKeywords)
        print(u'Keywords: %s' % sOutput)
    if oCard.discipline:
        if is_crypt_card(oCard):
            aDisciplines = []
            aDisciplines.extend(sorted([oP.discipline.name for oP in
                                        oCard.discipline if
                                        oP.level != 'superior']))
            aDisciplines.extend(sorted([oP.discipline.name.upper() for oP in
                                        oCard.discipline if
                                        oP.level == 'superior']))
            sDisciplines = u' '.join(aDisciplines)
        else:
            aDisciplines = [oP.discipline.fullname for oP in oCard.discipline]
            sDisciplines = u' / '.join(aDisciplines)
        sOutput = u'Discipline: %s' % sDisciplines
        print(sOutput)
    if oCard.virtue:
        if is_crypt_card(oCard):
            sOutput = u'Virtue: %s' % ' '.join(
                [oC.name for oC in oCard.virtue])
        else:
            sOutput = u'Virtue: %s' % ' / '.join(
                [oC.fullname for oC in oCard.virtue])
        print(sOutput)
    print(format_text(oCard.text))


def main_with_args(aTheArgs):
    """
    Main function: Loop through the options and process the database
    accordingly.
    """
    # Turn off some pylint refactoring warnings
    # pylint: disable=too-many-statements, too-many-branches
    # pylint: disable=too-many-return-statements, too-many-locals
    oOptParser, (oOpts, aArgs) = parse_options(aTheArgs)
    sPrefsDir = prefs_dir(SutekhInfo.NAME)

    oLogHandler = StreamHandler(sys.stdout)

    if len(aArgs) != 1:
        oOptParser.print_help()
        return 1

    if oOpts.db is None:
        ensure_dir_exists(sPrefsDir)
        oOpts.db = sqlite_uri(os.path.join(sPrefsDir, "sutekh.db"))

    bDoCardListChecks = False

    oConn = connectionForURI(oOpts.db)
    sqlhub.processConnection = oConn

    if oOpts.sql_debug:
        oConn.debug = True

    if not oConn.tableExists('abstract_card'):
        if not oOpts.refresh_tables:
            print("Database has not been created.")
            return 1
    else:
        try:
            _oCard = IAbstractCard('Ossian')
        except SQLObjectNotFound:
            if not oOpts.fetch and oOpts.ww_file is None:
                print("Database is missing cards - please import the cardlist")
                return 1

    # Only log critical messages by default
    setup_logging(oOpts.verbose)

    if oOpts.reload:
        if not oOpts.refresh_tables:
            print("reload should be called with --refresh-tables")
            return 1
        sTempdir = gen_temp_dir()
        (fTemp, sReloadZipName) = \
            tempfile.mkstemp('.zip', 'sutekh', sTempdir)
        os.close(fTemp)
        oZipFile = ZipFileWrapper(sReloadZipName)
        oZipFile.do_dump_all_to_zip(oLogHandler)
        # We dump the databases here
        # We will reload them later

    if oOpts.refresh_ruling_tables:
        if not refresh_tables([Ruling], sqlhub.processConnection):
            print("refresh failed")
            return 1

    if oOpts.refresh_tables:
        if not refresh_tables(TABLE_LIST, sqlhub.processConnection):
            print("refresh failed")
            return 1

    if oOpts.refresh_physical_card_tables:
        if not refresh_tables(PHYSICAL_LIST, sqlhub.processConnection):
            print("refresh failed")
            return 1

    if oOpts.lookup_file is not None:
        read_lookup_data(EncodedFile(oOpts.lookup_file), oLogHandler)

    if oOpts.ww_file is not None:
        read_white_wolf_list(EncodedFile(oOpts.ww_file), oLogHandler)
        bDoCardListChecks = True

    if oOpts.extra_file is not None:
        read_white_wolf_list(EncodedFile(oOpts.extra_file), oLogHandler)
        bDoCardListChecks = True

    if oOpts.exp_data_file is not None:
        read_exp_info_file(EncodedFile(oOpts.exp_data_file), oLogHandler)

    if oOpts.ruling_file is not None:
        read_rulings(EncodedFile(oOpts.ruling_file), oLogHandler)

    if oOpts.fetch:
        read_lookup_data(EncodedFile(LOOKUP_DATA_URL, True), oLogHandler)
        read_white_wolf_list(EncodedFile(WW_CARDLIST_URL, True), oLogHandler)
        read_rulings(EncodedFile(WW_RULINGS_URL, True), oLogHandler)
        read_white_wolf_list(EncodedFile(EXTRA_CARD_URL, True), oLogHandler)
        read_exp_info_file(EncodedFile(EXP_DATA_URL, True), oLogHandler)
        bDoCardListChecks = True

    if bDoCardListChecks:
        # Run the consistency checks on the database
        for oAbsCard in AbstractCard.select():
            aMessages = do_card_checks(oAbsCard)
            if aMessages:
                print('\n'.join(aMessages))

    if oOpts.upgrade_db:
        oDBUpgrade = DBUpgradeManager()
        oDBUpgrade.attempt_database_upgrade(oLogHandler)

    if oOpts.save_all_css and oOpts.save_cs is not None:
        print("Can't use --save-cs and --save-all-cs Simulatenously")
        return 1

    # initialise the caches, so adapters, etc work for reading / writing
    # card sets
    make_adapter_caches()

    if oOpts.read_physical_cards_from is not None:
        oFile = PhysicalCardXmlFile(oOpts.read_physical_cards_from)
        oFile.read()

    if oOpts.save_all_css:
        write_all_pcs()

    if oOpts.dump_zip_name is not None:
        oZipFile = ZipFileWrapper(oOpts.dump_zip_name)
        oZipFile.do_dump_all_to_zip(oLogHandler)

    if oOpts.restore_zip_name is not None:
        oZipFile = ZipFileWrapper(oOpts.restore_zip_name)
        oZipFile.do_restore_from_zip(oLogHandler=oLogHandler)

    if oOpts.save_cs is not None:
        oFile = PhysicalCardSetXmlFile(oOpts.cs_filename)
        oFile.write(oOpts.save_cs)

    if oOpts.print_cs is not None:
        try:
            oCS = IPhysicalCardSet(oOpts.print_cs)
            fPrint = StringIO()
            oPrinter = WriteArdbText()
            oPrinter.write(fPrint, CardSetWrapper(oCS))
            print(fPrint.getvalue())
        except SQLObjectNotFound:
            print('Unable to load card set', oOpts.print_cs)
            return 1

    if oOpts.list_cs:
        if not print_card_list(oOpts.limit_list):
            return 1
    elif oOpts.limit_list is not None:
        print("Can't use limit-list-to without list-cs")
        return 1

    if oOpts.filter_string is not None:
        dResults = run_filter(oOpts.filter_string, oOpts.filter_cs)
        print_card_filter_list(dResults, print_card_details,
                               oOpts.filter_detailed)

    if oOpts.print_card is not None:
        if not do_print_card(oOpts.print_card, print_card_details):
            return 1

    if oOpts.read_cs is not None:
        oFile = PhysicalCardSetXmlFile(oOpts.read_cs)
        oFile.read()

    if oOpts.read_acs is not None:
        oFile = AbstractCardSetXmlFile(oOpts.read_acs)
        oFile.read()

    if oOpts.reload:
        oZipFile = ZipFileWrapper(sReloadZipName)
        oZipFile.do_restore_from_zip(oLogHandler=oLogHandler)
        os.remove(sReloadZipName)
        os.rmdir(sTempdir)

    if oOpts.upgrade_db and oOpts.refresh_tables:
        print("Can't use --upgrade-db and --refresh-tables simulatenously")
        return 1

    return 0


def main():
    """
    Entry_point for setuptools scripts. Passes sys.argv to main_with_args
    """
    fix_ssl_env()
    return main_with_args(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
