# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# Misc Useful functions needed in several places. Mainly to do with database
# management. Seperated out from SutekhCli and other places, NM, 2006

"""Misc generic functions needed in various places."""

import tempfile
import os
import re
import sys
import logging
from sqlobject import sqlhub
import urlparse


def gen_temp_file(sBaseName, sDir):
    """Simple wrapper around tempfile creation - generates the name and closes
       the file
       """
    (fTemp, sFilename) = tempfile.mkstemp('.xml', sBaseName, sDir)
    # This may not be nessecary, but the available documentation
    # suggests that, on Windows NT anyway, leaving the file open will
    # cause problems if we try to reopen it
    os.close(fTemp)
    # There is a race condition here, but since Sutekh should not be running
    # with elevated priveleges, this should never be a security issues
    # The race requires something to delete and replace the tempfile,
    # I don't see it being triggered accidently
    return sFilename


def gen_app_temp_dir(sApp):
    """Create a temporary directory using mkdtemp"""
    sTempdir = tempfile.mkdtemp('dir', sApp)
    return sTempdir


def safe_filename(sFilename):
    """Replace potentially dangerous and annoying characters in the name -
       used to automatically generate sensible filenames from card set names
       """
    sSafeName = sFilename
    sSafeName = sSafeName.replace(" ", "_")  # I dislike spaces in filenames
    # Prevented unexpected filesystem issues
    sSafeName = sSafeName.replace("/", "_")
    sSafeName = sSafeName.replace("\\", "_")  # ditto for windows
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
    Based on the example indent function at
    http://effbot.org/zone/element-lib.htm [22/01/2008]
    """
    sIndent = "\n" + iIndentLevel * "  "
    if len(oElement):
        if not oElement.text or not oElement.text.strip():
            oElement.text = sIndent + "  "
            for oSubElement in oElement:
                pretty_xml(oSubElement, iIndentLevel + 1)
            # Reset indentation level for last child element
            # pylint: disable=W0631
            # We know SubElement will exist because of the len check above
            if not oSubElement.tail or not oSubElement.tail.strip():
                oSubElement.tail = sIndent
    else:
        if iIndentLevel and (not oElement.tail or not oElement.tail.strip()):
            oElement.tail = sIndent


def norm_xml_quotes(sData):
    """Normalise quote escaping from ElementTree, to hide version
       differences"""
    # Because of how ElementTree adds quotes internally, this should always
    # be safe
    return sData.replace('&apos;', "'")


def get_database_url():
    """Return the database url, with the password stripped out if
       needed"""
    sDBuri = sqlhub.processConnection.uri()
    # pylint: disable=E1103
    # pylint doesn't like the SpiltResult named tuple
    tParsed = urlparse.urlsplit(sDBuri)
    if tParsed.password:
        tCombined = (tParsed.scheme,
                     tParsed.netloc.replace(tParsed.password, '****'),
                     tParsed.path, tParsed.query, tParsed.fragment)
        sUrl = urlparse.urlunsplit(tCombined)
    else:
        sUrl = sDBuri
    return sUrl


# helper conversion functions
def move_articles_to_back(sName):
    """Moves articles to the end of the name.

       Reverse of move_articles_to_front.
       Used when exporting to various formats and when selected
       as a display option."""
    if sName.startswith('The '):
        sName = sName[4:] + ", The"
    elif sName.startswith('An '):
        sName = sName[3:] + ", An"
    elif sName.startswith('A '):
        sName = sName[2:] + ", A"
    return sName


def move_articles_to_front(sName):
    """Moves articles from the end back to the start as is expected
       in the database.

       Reverses move_articles_to_back.
       Used when importing from various formats."""
    # handle case variations as well
    if sName.lower().endswith(', the'):
        sName = "The " + sName[:-5]
    elif sName.lower().endswith(', an'):
        sName = "An " + sName[:-4]
    elif sName.lower().endswith(', a'):
        sName = "A " + sName[:-3]
    # The result might be mixed case, but, as we will feed this into
    # IAbstractCard in most cases, that won't matter
    return sName


def normalise_whitespace(sText):
    """Return a copy of sText with all whitespace normalised to single
       spaces."""
    return re.sub('\s+', ' ', sText, flags=re.MULTILINE).strip()


def find_subclasses(cClass):
    """Utility method to find the subclasses of a specific class.

       Used for introspection magic to lookup various stuff without importing
       it directly from the main application.

       Because we expect liberal use of overloading, this only returns
       classes which have no subclasses themselves, so overloading a base
       Filter to tweak behaviour will only return the overloaded filter,
       rather than both.

       To avoid issues with diamond inheritance, we return an unordered set
       of the subclasses."""
    aSubClasses = set()
    for oChild in cClass.__subclasses__():
        aSubClasses.update(find_subclasses(oChild))
    if not cClass.__subclasses__():
        # No children, so append
        aSubClasses.add(cClass)
    return aSubClasses


def setup_logging(bVerbose, sErrFile=None):
    """Setup the log handling for this run"""
    # Only log critical messages by default
    oRootLogger = logging.getLogger()
    oRootLogger.setLevel(level=logging.CRITICAL)
    if bVerbose or sErrFile:
        # Change logging level to debug
        oRootLogger.setLevel(logging.DEBUG)
        bSkipVerbose = False
        if sErrFile:
            try:
                oLogHandler = logging.FileHandler(sErrFile)
                oRootLogger.addHandler(oLogHandler)
            except IOError:
                oLogHandler = logging.StreamHandler(sys.stderr)
                oRootLogger.addHandler(oLogHandler)
                bSkipVerbose = True  # Avoid doubled logging to stderr
                logging.error('Unable to open log file, logging to stderr',
                              exc_info=1)
        if bVerbose and not bSkipVerbose:
            # Add logging to stderr
            oLogHandler = logging.StreamHandler(sys.stderr)
            oRootLogger.addHandler(oLogHandler)
    else:
        # Setup fallback logger for critical messages
        oLogHandler = logging.StreamHandler(sys.stderr)
        oRootLogger.addHandler(oLogHandler)
    return oRootLogger
