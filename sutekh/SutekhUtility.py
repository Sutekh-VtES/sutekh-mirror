# SutekhUtility.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# Misc Useful functions needed in several places. Mainly to do with database
# management. Seperated out from SutekhCli and other places, NM, 2006

"""Misc functions needed in various places in Sutekh."""

from sutekh.core.SutekhObjects import VersionTable, flush_cache
from sutekh.core.DatabaseVersion import DatabaseVersion
from sutekh.io.WhiteWolfParser import WhiteWolfParser
from sutekh.io.RulingParser import RulingParser
from sqlobject import sqlhub
import tempfile, os, sys

def refresh_tables(aTables, oConn):
    """Drop and recreate the given list of tables"""
    aTables.reverse()
    for cCls in aTables:
        cCls.dropTable(ifExists=True, connection=oConn)
    aTables.reverse()
    oVerHandler = DatabaseVersion(oConn)
    # Make sure we recreate the database version table
    oVerHandler.expire_table_conn(oConn)
    oVerHandler.ensure_table_exists(oConn)
    if not oVerHandler.set_version(VersionTable, VersionTable.tableversion,
            oConn):
        return False
    for cCls in aTables:
        cCls.createTable(connection=oConn)
        if not oVerHandler.set_version(cCls, cCls.tableversion, oConn):
            return False
    flush_cache()
    return True

def read_white_wolf_list(aWwFiles, oLogHandler=None):
    """Parse in a new White Wolf cardlist

       aWwList is a list of objects with a .open() method (e.g.
       sutekh.io.WwFile.WwFile's)
       """
    flush_cache()
    oOldConn = sqlhub.processConnection
    sqlhub.processConnection = oOldConn.transaction()
    oParser = WhiteWolfParser(oLogHandler)
    for oFile in aWwFiles:
        fIn = oFile.open()
        for sLine in fIn:
            oParser.feed(sLine)
        fIn.close()
    sqlhub.processConnection.commit()
    sqlhub.processConnection = oOldConn

def read_rulings(oRulings, oLogHandler=None):
    """Parse a new White Wolf rulings file

       oRulings is an object with a .open() method (e.g. a sutekh.io.WwFile.WwFile)
       """
    flush_cache()
    oOldConn = sqlhub.processConnection
    sqlhub.processConnection = oOldConn.transaction()
    oParser = RulingParser(oLogHandler)
    fIn = oRulings.open()
    for sLine in fIn:
        oParser.feed(sLine)
    fIn.close()
    sqlhub.processConnection.commit()
    sqlhub.processConnection = oOldConn

def gen_temp_file(sBaseName, sDir):
    """Simple wrapper around tempfile creation - generates the name and closes
       the file
       """
    (fTemp, sFilename) = tempfile.mkstemp('.xml', sBaseName, sDir)
    # This may not be nessecary, but the available documentation
    # suggests that, on Windows NT anyway, leaving the file open will
    # cause problems when writePhysicalCards tries to reopen it
    os.close(fTemp)
    # There is a race condition here, but since Sutekh should not be running
    # with elevated priveleges, this should never be a security issues
    # The the race requires something to delete and replace the tempfile,
    # I don't see it being triggered accidently
    return sFilename

def gen_temp_dir():
    """Create a temporary directory using mkdtemp"""
    sTempdir = tempfile.mkdtemp('dir', 'sutekh')
    return sTempdir

def safe_filename(sFilename):
    """Replace potentially dangerous and annoying characters in the name -
       used to automatically generate sensible filenames from card set names
       """
    sSafeName = sFilename
    sSafeName = sSafeName.replace(" ", "_") # I dislike spaces in filenames
    # Prevented unexpected filesystem issues
    sSafeName = sSafeName.replace("/", "_")
    sSafeName = sSafeName.replace("\\", "_") # ditto for windows
    return sSafeName

def prefs_dir(sApp):
    """Return a suitable directory for storing preferences and other
       application data."""
    if sys.platform.startswith("win") and "APPDATA" in os.environ:
        return os.path.join(os.environ["APPDATA"], sApp)
    else:
        return os.path.join(os.path.expanduser("~"), ".%s" % sApp.lower())

def ensure_dir_exists(sDir):
    """Check that a directory exists and create it if it doesn't.
       """
    if os.path.exists(sDir):
        assert os.path.isdir(sDir)
    else:
        os.makedirs(sDir)

def sqlite_uri(sPath):
    """Create an SQLite db URI from the path to the db file.
       """
    sDbFile = sPath.replace(os.sep, "/")

    sDrive, sRest = os.path.splitdrive(sDbFile)
    if sDrive:
        sDbFile = "/" + sDrive.rstrip(':') + "|" + sRest
    else:
        sDbFile = sRest

    return "sqlite://" + sDbFile

def pretty_xml(oElement, iIndentLevel=0):
    """
    Helper function to add whitespace text attributes to a ElementTree.
    Makes for 'pretty' indented XML output.
    Based on the example indent function at http://effbot.org/zone/element-lib.htm [22/01/2008]
    """
    sIndent = "\n" + iIndentLevel * "  "
    if len(oElement):
        if not oElement.text or not oElement.text.strip():
            oElement.text = sIndent + "  "
            for oSubElement in oElement:
                pretty_xml(oSubElement, iIndentLevel + 1)
            # Reset indentation level for last child element
            # pylint: disable-msg=W0631
            # We know SubElement will exist because of the len check above
            if not oSubElement.tail or not oSubElement.tail.strip():
                oSubElement.tail = sIndent
    else:
        if iIndentLevel and (not oElement.tail or not oElement.tail.strip()):
            oElement.tail = sIndent


