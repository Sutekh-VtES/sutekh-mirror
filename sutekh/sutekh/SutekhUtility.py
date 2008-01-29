# SutekhUtility.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Minor modifications copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# Misc Useful functions needed in several places. Mainly to do with database
# management. Seperated out from SutekhCli and other places, NM, 2006

from sutekh.core.SutekhObjects import VersionTable, FlushCache, \
        PhysicalCardSet, AbstractCardSet
from sutekh.core.DatabaseVersion import DatabaseVersion
from sutekh.io.WhiteWolfParser import WhiteWolfParser
from sutekh.io.RulingParser import RulingParser
from sqlobject import sqlhub, SQLObjectNotFound
import codecs, tempfile, os, sys
from logging import StreamHandler

def refreshTables(aTables, oConn, **kw):
    """Drop and recreate the given list of tables"""
    aTables.reverse()
    for cCls in aTables:
        cCls.dropTable(ifExists=True, connection=oConn)
    aTables.reverse()
    oVerHandler = DatabaseVersion(oConn)
    if not oVerHandler.setVersion(VersionTable, VersionTable.tableversion, oConn):
        return False
    for cCls in aTables:
        cCls.createTable(connection=oConn)
        if not oVerHandler.setVersion(cCls, cCls.tableversion, oConn):
            return False
    FlushCache()
    return True

def readWhiteWolfList(sWwList, oLogHandler=None):
    """Parse in  a new White Wolf CardList"""
    FlushCache()
    if oLogHandler is None:
        oLogHandler = StreamHandler(sys.stdout)
    oOldConn = sqlhub.processConnection
    sqlhub.processConnection = oOldConn.transaction()
    oParser = WhiteWolfParser(oLogHandler)
    fIn = codecs.open(sWwList, 'rU', 'cp1252')
    for sLine in fIn:
        oParser.feed(sLine)
    fIn.close()
    sqlhub.processConnection.commit()
    sqlhub.processConnection = oOldConn

def readRulings(sRulings, oLogHandler=None):
    """Parse a new White Wolf rulings file"""
    FlushCache()
    if oLogHandler is None:
        oLogHandler = StreamHandler(sys.stdout)
    oOldConn = sqlhub.processConnection
    sqlhub.processConnection = oOldConn.transaction()
    oParser = RulingParser(oLogHandler)
    fIn = codecs.open(sRulings, 'rU', 'cp1252')
    for sLine in fIn:
        oParser.feed(sLine)
    fIn.close()
    sqlhub.processConnection.commit()
    sqlhub.processConnection = oOldConn

def genTempFile(sBaseName, sDir):
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

def genTempdir():
    """Create a temporary directory using mkdtemp"""
    sTempdir = tempfile.mkdtemp('dir', 'sutekh')
    return sTempdir

def safeFilename(sFilename):
    """Replace potentially dangerous and annoying characters in the name -
       used to automatically generate sensible filenames from card set names
       """
    sSafeName = sFilename
    sSafeName = sSafeName.replace(" ", "_") # I dislike spaces in filenames
    sSafeName = sSafeName.replace("/", "_") # Prevented unexpected filesystem issues
    sSafeName = sSafeName.replace("\\", "_") # ditto for windows
    return sSafeName

def prefsDir(sApp):
    """Return a suitable directory for storing preferences and other application data.
       """
    if sys.platform.startswith("win") and "APPDATA" in os.environ:
        return os.path.join(os.environ["APPDATA"], sApp)
    else:
        return os.path.join(os.path.expanduser("~"), ".%s" % sApp.lower())

def ensureDirExists(sDir):
    """Check that a directory exists and create it if it doesn't.
       """
    if os.path.exists(sDir):
        assert os.path.isdir(sDir)
    else:
        os.makedirs(sDir)

def sqliteUri(sPath):
    """Create an SQLite db URI from the path to the db file.
       """
    sDbFile = sPath.replace(os.sep, "/")

    sDrive, sRest = os.path.splitdrive(sDbFile)
    if sDrive:
        sDbFile = "/" + sDrive.rstrip(':') + "|" + sRest
    else:
        sDbFile = sRest

    return "sqlite://" + sDbFile


def delete_physical_card_set(sSetName):
    """Unconditionally delete a PCS and its contents"""
    try:
        oCS = PhysicalCardSet.byName(sSetName)
        for oCard in oCS.cards:
            oCS.removePhysicalCard(oCard)
        PhysicalCardSet.delete(oCS.id)
        return True
    except SQLObjectNotFound:
        return False

def delete_abstract_card_set(sSetName):
    """Unconditionally delete a ACS and its contents"""
    try:
        oCS = AbstractCardSet.byName(sSetName)
        for oCard in oCS.cards:
            oCS.removeAbstractCard(oCard)
        AbstractCardSet.delete(oCS.id)
        return True
    except SQLObjectNotFound:
        return False

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
            for oElement in oElement:
                pretty_xml(oElement, iIndentLevel + 1)
            if not oElement.tail or not oElement.tail.strip():
                oElement.tail = sIndent
    else:
        if iIndentLevel and (not oElement.tail or not oElement.tail.strip()):
            oElement.tail = sIndent
