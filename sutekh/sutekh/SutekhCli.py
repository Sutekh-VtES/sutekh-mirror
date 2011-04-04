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

import sys
import optparse
import os
import tempfile
import StringIO
from logging import StreamHandler
from sqlobject import sqlhub, connectionForURI, SQLObjectNotFound
from sutekh.core.SutekhObjects import Ruling, TABLE_LIST, PHYSICAL_LIST, \
        IPhysicalCardSet, IAbstractCard, PhysicalCard, \
        MapPhysicalCardToPhysicalCardSet
from sutekh.core.Filters import PhysicalCardSetFilter, FilterAndBox, \
        PhysicalCardFilter
from sutekh.core.FilterParser import FilterParser
from sutekh.SutekhUtility import refresh_tables, read_white_wolf_list, \
        read_rulings, gen_temp_dir, prefs_dir, ensure_dir_exists, sqlite_uri, \
        is_crypt_card, format_text
from sutekh.core.DatabaseUpgrade import attempt_database_upgrade
from sutekh.core.CardSetHolder import CardSetWrapper
from sutekh.core.CardSetUtilities import format_cs_list
from sutekh.io.XmlFileHandling import PhysicalCardXmlFile, \
        PhysicalCardSetXmlFile, AbstractCardSetXmlFile, \
        write_all_pcs
from sutekh.io.WriteArdbText import WriteArdbText
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
                  help="Text file (probably from the VEKN website) to read " \
                          "cards from.")
    oOptParser.add_option("-e", "--extra-file",
                  type="string", dest="extra_file", default=None,
                  help="Text file to read extra storyline" \
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
    oOptParser.add_option("--save-cs",
                  type="string", dest="save_cs", default=None,
                  help="Save the given Card Set to an XML file " \
                          "(by default named <csname>.xml).")
    oOptParser.add_option("--cs-filename",
                  type="string", dest="cs_filename", default=None,
                  help="Give an alternative filename to save the " \
                          "Card Set as")
    oOptParser.add_option("--save-all-cs",
                  action="store_true", dest="save_all_css", default=False,
                  help="Save all Card Sets in the database to files" \
                          " - Cannot be used with --save-cs.")
    oOptParser.add_option("--read-cs",
                  type="string", dest="read_cs", default=None,
                  help="Load a Card Set from the given XML file.")
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
    oOptParser.add_option("--print-cs",
            type="string", dest="print_cs", default=None,
            help="Print the given card set (ARDB Text format)")
    oOptParser.add_option("--list-cs",
            action="store_true", dest="list_cs", default=False,
            help="Print a formatted list of all the card sets in the database")
    oOptParser.add_option("--limit-list-to",
            type="string", dest="limit_list", default=None,
            help="Limit the printed list to the children of the "
                    "given card set")
    oOptParser.add_option("--filter",
            type="string", dest="filter_string", default=None,
            help="Filter to run on the database")
    oOptParser.add_option("--filter-cs",
            type="string", dest="filter_cs", default=None,
            help="card set to filter. If not specified, filter the WW" \
                    " card list")
    oOptParser.add_option("--filter-detailed",
            action="store_true", dest="filter_detailed", default=False,
            help="Print card details for filter results, rather than just" \
                    " card names")
    oOptParser.add_option("--print-card",
            type="string", dest="print_card", default=None,
            help="Print the details of the given card")
    oOptParser.add_option("--print-encoding",
            type="string", dest="print_encoding", default='ascii',
            help="Encoding to use when printing output")

    return oOptParser, oOptParser.parse_args(aArgs)


def print_card_details(oCard, sEncoding):
    """Print the details of a given card"""
    # pylint: disable-msg=E1101, R0912
    # E1101: SQLObject can confuse pylint
    # R0912: Several cases to consider, so many branches
    if len(oCard.cardtype) == 0:
        print 'CardType: Unknown'
    else:
        print 'CardType: %s' % ' / '.join([oT.name for oT in oCard.cardtype])
    if len(oCard.clan) > 0:
        print 'Clan: %s' % ' / '.join([oC.name for oC in oCard.clan])
    if len(oCard.creed) > 0:
        print 'Creed: %s' % ' / '.join([oC.name for oC in oCard.creed])
    if oCard.capacity:
        print 'Capacity: %d' % oCard.capacity
    if oCard.life:
        print 'Life: %d' % oCard.life
    if oCard.group:
        if oCard.group == -1:
            print 'Group: Any'
        else:
            print 'Group: %d' % oCard.group
    if not oCard.cost is None:
        if oCard.cost == -1:
            print 'Cost: X %s' % oCard.costtype
        else:
            print 'Cost: %d %s' % (oCard.cost, oCard.costtype)
    if len(oCard.discipline) > 0:
        if is_crypt_card(oCard):
            aDisciplines = []
            aDisciplines.extend(sorted([oP.discipline.name for oP in
                oCard.discipline if oP.level != 'superior']))
            aDisciplines.extend(sorted([oP.discipline.name.upper() for oP in
                oCard.discipline if oP.level == 'superior']))
            sDisciplines = ' '.join(aDisciplines)
        else:
            aDisciplines = [oP.discipline.fullname for oP in oCard.discipline]
            sDisciplines = ' / '.join(aDisciplines)
        print 'Discipline: %s' % sDisciplines
    if len(oCard.virtue) > 0:
        if is_crypt_card(oCard):
            print 'Virtue: %s' % ' '.join([oC.name for oC in oCard.virtue])
        else:
            print 'Virtue: %s' % ' / '.join([oC.fullname for oC in
                oCard.virtue])
    print format_text(oCard.text.encode(sEncoding, 'xmlcharrefreplace'))


def run_filter(oFilter, oCardSet, bDetailed, sEncoding):
    """Run the given filter, printing the results as required"""
    if oCardSet:
        # Filter the given card set
        oBaseFilter = PhysicalCardSetFilter(oCardSet.name)
        oJointFilter = FilterAndBox([oBaseFilter, oFilter])
        aResults = oJointFilter.select(MapPhysicalCardToPhysicalCardSet)
        dResults = {}
        for oCard in aResults:
            oAbsCard = IAbstractCard(oCard)
            dResults.setdefault(oAbsCard, 0)
            dResults[oAbsCard] += 1
    else:
        # Filter WW cardlist
        oBaseFilter = PhysicalCardFilter()
        oJointFilter = FilterAndBox([oBaseFilter, oFilter])
        aResults = oJointFilter.select(PhysicalCard)
        dResults = {}
        for oCard in aResults:
            oAbsCard = IAbstractCard(oCard)
            dResults.setdefault(oAbsCard, 1)

    for oCard in sorted(dResults, key=lambda x: x.name):
        if oCardSet:
            iCnt = dResults[oCard]
            print '%3d x %s' % (iCnt,
                    oCard.name.encode(sEncoding, 'xmlcharrefreplace'))
        else:
            print oCard.name.encode(sEncoding, 'xmlcharrefreplace')
        if bDetailed:
            print_card_details(oCard, sEncoding)


def main_with_args(aTheArgs):
    """
    Main function: Loop through the options and process the database
    accordingly.
    """
    # Turn off some pylint refactoring warnings
    # pylint: disable-msg=R0915, R0912, R0911, R0914
    oOptParser, (oOpts, aArgs) = parse_options(aTheArgs)
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
            (fTemp, sReloadZipName) = \
                    tempfile.mkstemp('.zip', 'sutekh', sTempdir)
            os.close(fTemp)
            oZipFile = ZipFileWrapper(sReloadZipName)
            oZipFile.do_dump_all_to_zip(oLogHandler)
            # We dump the databases here
            # We will reload them later

    if oOpts.refresh_ruling_tables:
        if not refresh_tables([Ruling], sqlhub.processConnection):
            print "refresh failed"
            return 1

    if oOpts.refresh_tables:
        if not refresh_tables(TABLE_LIST, sqlhub.processConnection):
            print "refresh failed"
            return 1

    if oOpts.refresh_physical_card_tables:
        if not refresh_tables(PHYSICAL_LIST, sqlhub.processConnection):
            print "refresh failed"
            return 1

    if not oOpts.ww_file is None:
        read_white_wolf_list([WwFile(oOpts.ww_file)], oLogHandler)

    if not oOpts.extra_file is None:
        read_white_wolf_list([WwFile(oOpts.extra_file)], oLogHandler)

    if not oOpts.ruling_file is None:
        read_rulings([WwFile(oOpts.ruling_file)], oLogHandler)

    if not oOpts.read_physical_cards_from is None:
        oFile = PhysicalCardXmlFile(oOpts.read_physical_cards_from)
        oFile.read()

    if oOpts.save_all_css and not oOpts.save_cs is None:
        print "Can't use --save-cs and --save-all-cs Simulatenously"
        return 1

    if oOpts.save_all_css:
        write_all_pcs()

    if oOpts.dump_zip_name is not None:
        oZipFile = ZipFileWrapper(oOpts.dump_zip_name)
        oZipFile.do_dump_all_to_zip(oLogHandler)

    if oOpts.restore_zip_name is not None:
        oZipFile = ZipFileWrapper(oOpts.restore_zip_name)
        oZipFile.do_restore_from_zip(oLogHandler=oLogHandler)

    if not oOpts.save_cs is None:
        oFile = PhysicalCardSetXmlFile(oOpts.cs_filename)
        oFile.write(oOpts.save_cs)

    if not oOpts.print_cs is None:
        try:
            oCS = IPhysicalCardSet(oOpts.print_cs)
            fPrint = StringIO.StringIO()
            oPrinter = WriteArdbText()
            oPrinter.write(fPrint, CardSetWrapper(oCS))
            print fPrint.getvalue().encode(oOpts.print_encoding,
                        'xmlcharrefreplace')
        except SQLObjectNotFound:
            print 'Unable to load card set', oOpts.print_cs
            return 1

    if oOpts.list_cs:
        if oOpts.limit_list is not None:
            try:
               # pylint: disable-msg=E1101
               # SQLObject confuse pylint
                oCS = IPhysicalCardSet(oOpts.limit_list)
                print ' %s' % oCS.name.encode(oOpts.print_encoding,
                        'xmlcharrefreplace')
                print format_cs_list(oCS, '    ').encode(oOpts.print_encoding,
                        'xmlcharrefreplace')
            except SQLObjectNotFound:
                print 'Unable to load card set', oOpts.limit_list
                return 1
        else:
            print format_cs_list().encode(oOpts.print_encoding,
                    'xmlcharrefreplace')
    elif oOpts.limit_list is not None:
        print "Can't use limit-list-to without list-cs"
        return 1

    if not oOpts.filter_string is None:
        oParser = FilterParser()
        oFilter = oParser.apply(oOpts.filter_string).get_filter()
        oCS = None
        if oOpts.filter_cs:
            oCS = IPhysicalCardSet(oOpts.filter_cs)
        run_filter(oFilter, oCS, oOpts.filter_detailed, oOpts.print_encoding)

    if not oOpts.print_card is None:
        try:
            try:
                oCard = IAbstractCard(oOpts.print_card)
            except UnicodeDecodeError, oErr:
                if oOpts.print_encoding != 'ascii':
                    # Are there better choices than --print-encoding?
                    oCard = IAbstractCard(
                            oOpts.print_card.decode(oOpts.print_encoding))
                else:
                    print 'Unable to interpret card name:'
                    print oErr
                    print 'Please specify a suitable --print-encoding'
                    return 1
            # pylint: disable-msg=E1101, E1103
            # SQLObject confuse pylint
            print oCard.name.encode(oOpts.print_encoding, 'xmlcharrefreplace')
            print_card_details(oCard, oOpts.print_encoding)
        except SQLObjectNotFound:
            print 'Unable to find card %s' % oOpts.print_card
            return 1

    if not oOpts.read_cs is None:
        oFile = PhysicalCardSetXmlFile(oOpts.read_cs)
        oFile.read()

    if not oOpts.read_acs is None:
        oFile = AbstractCardSetXmlFile(oOpts.read_acs)
        oFile.read()

    if oOpts.reload:
        oZipFile = ZipFileWrapper(sReloadZipName)
        oZipFile.do_restore_from_zip(oLogHandler=oLogHandler)
        os.remove(sReloadZipName)
        os.rmdir(sTempdir)

    if oOpts.upgrade_db and oOpts.refresh_tables:
        print "Can't use --upgrade-db and --refresh-tables simulatenously"
        return 1

    if oOpts.upgrade_db:
        attempt_database_upgrade(oLogHandler)

    return 0


def main():
    """
    Entry_point for setuptools scripts. Passes sys.argv to main_with_args
    """
    return main_with_args(sys.argv)

if __name__ == "__main__":
    sys.exit(main())
