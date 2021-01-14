# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>,
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# Class and functions to manage zip file handling for Sutekh
# Split off from SutekhUtility.py and refactored, April 2007  - NM

"""Provide a ZipFile class which wraps the functionlity from zipfile
   Sutekh needs."""

import zipfile
import datetime
from io import StringIO
from logging import Logger

from sqlobject import sqlhub

from ..core.BaseTables import PhysicalCardSet, PHYSICAL_SET_LIST
from ..core.BaseAdapters import IPhysicalCardSet
from ..core.CardLookup import DEFAULT_LOOKUP
from ..core.CardSetHolder import CachedCardSetHolder, CardSetWrapper
from ..core.DBUtility import refresh_tables
from ..core.CardSetUtilities import check_cs_exists


def parse_string(oParser, sIn, oHolder):
    """Utility function for reading zip files.

       Allows oParser.parse to be called on a string."""
    # We encode data to ascii when writing, so
    # this should be correct
    oFile = StringIO(sIn.decode('ascii'))
    oParser.parse(oFile, oHolder)


def write_string(oWriter, oPCSet):
    """Utility function.

       Generate a string from the Writer."""
    oHolder = CardSetWrapper(oPCSet)
    oFile = StringIO()
    oWriter.write(oFile, oHolder)
    oString = oFile.getvalue()
    oFile.close()
    return oString


class ZipEntryProxy(StringIO):
    """A proxy that provides a suitable open method so
       these can be passed to the card reading routines."""

    def open(self):
        """Reset to the start of the file."""
        self.seek(0)
        return self


class BaseZipFileWrapper:
    """The zip file wrapper.

       This provides useful functions for dumping + extracting the
       database to / form a zipfile"""
    def __init__(self, sZipFileName):
        self.sZipFileName = sZipFileName
        self.oZip = None
        self._aWarnings = []
        self._bForceReparent = False
        self._cWriter = None
        self._cIdentifyFile = None

    def _open_zip_for_write(self):
        """Open zip file to be written"""
        self.oZip = zipfile.ZipFile(self.sZipFileName, 'w')

    def _open_zip_for_read(self):
        """Open zip file to be read"""
        self.oZip = zipfile.ZipFile(self.sZipFileName, 'r')

    def _close_zip(self):
        """Close the zip file and clean up"""
        self.oZip.close()
        self.oZip = None

    def _write_pcs_list_to_zip(self, aPCSList, oLogger):
        """Write the given list of card sets to the zip file"""
        bClose = False
        tTime = datetime.datetime.now().timetuple()
        if self.oZip is None:
            self._open_zip_for_write()
            bClose = True
        aList = []
        for oPCSet in aPCSList:
            sZName = oPCSet.name
            # pylint: disable=not-callable
            # subclasses will provide a callable cWriter
            oWriter = self._cWriter()
            # pylint: enable=not-callable
            oString = write_string(oWriter, oPCSet)
            sZName = sZName.replace(" ", "_")
            sZName = sZName.replace("/", "_")
            sZipName = '%s.xml' % sZName
            sZipName = sZipName.encode('ascii',
                                       'xmlcharrefreplace').decode('ascii')
            aList.append(sZipName)
            # ZipInfo will just use the 1st 6 fields in tTime
            oInfoObj = zipfile.ZipInfo(sZipName, tTime)
            # Set permissions on the created file - see issue 3394 on the
            # python bugtracker. Docs say this is safe on all platforms
            oInfoObj.external_attr = 0o600 << 16
            oInfoObj.compress_type = zipfile.ZIP_DEFLATED
            self.oZip.writestr(oInfoObj, oString)
            oLogger.info('PCS: %s written', oPCSet.name)
        if bClose:
            self._close_zip()
        return aList

    def do_restore_from_zip(self, oCardLookup=DEFAULT_LOOKUP,
                            oLogHandler=None):
        """Recover data from the zip file"""
        self._aWarnings = []
        bTablesRefreshed = False
        self._bForceReparent = False
        self._open_zip_for_read()
        oLogger = Logger('Restore zip file')
        if oLogHandler is not None:
            oLogger.addHandler(oLogHandler)
            if hasattr(oLogHandler, 'set_total'):
                oLogHandler.set_total(len(self.oZip.infolist()))
        # We do this so we can accomodate user created zipfiles,
        # that don't nessecarily have the ordering we want
        # pylint: disable=not-callable
        # subclasses will provide a callable cIdentifyFile
        oIdParser = self._cIdentifyFile()
        # pylint: enable=not-callable
        # check that the zip file contains at least 1 Physical Card Set
        for oItem in self.oZip.infolist():
            oData = self.oZip.read(oItem.filename)
            oIdParser.parse_string(oData)
            if not bTablesRefreshed and self._check_refresh(oIdParser):
                # We delete the Physical Card Sets
                # Since this is restoring the contents of a zip file,
                # hopefully this is safe to do
                # if we fail, the database will be in an inconsitent state,
                # but that's going to be true anyway
                refresh_tables(PHYSICAL_SET_LIST, sqlhub.processConnection)
                bTablesRefreshed = True
            if self._should_force_reparent(oIdParser):
                self._bForceReparent = True
        if not bTablesRefreshed:
            raise IOError("No valid card sets found in the zip file.")
        # We try and restore the card sets ensuring parents exist
        dLookupCache = {}
        aToRead = self.oZip.infolist()
        while aToRead:
            aToRead = self.read_items(aToRead, oCardLookup, oLogger,
                                      dLookupCache)
        self._close_zip()

    def read_items(self, aList, oCardLookup, oLogger, dLookupCache):
        """Read a list of CardSet items from the card list, reaturning
           a list of those that couldn't be read because their parents
           weren't read first"""
        aToRead = []
        # pylint: disable=not-callable
        # subclasses will provide a callable cIdentifyFile
        oIdParser = self._cIdentifyFile()
        # pylint: enable=not-callable
        oOldConn = sqlhub.processConnection
        oTrans = oOldConn.transaction()
        sqlhub.processConnection = oTrans
        for oItem in aList:
            bReparent = False
            oData = self.oZip.read(oItem.filename)
            oIdParser.parse_string(oData)
            if not oIdParser.can_parse():
                # Unreadable item, so skip it
                continue
            # We check whether the parent has been read already
            if not oIdParser.parent_exists:
                aToRead.append(oItem)
                continue
            if self._check_forced_reparent(oIdParser):
                # We need to reparent this card set
                if check_cs_exists('My Collection'):
                    bReparent = True
                else:
                    # Card Collection not there yet, so delay
                    aToRead.append(oItem)
                    continue
            oParser = oIdParser.get_parser()
            oHolder = CachedCardSetHolder()
            parse_string(oParser, oData, oHolder)
            if bReparent:
                oHolder.parent = 'My Collection'
            oHolder.create_pcs(oCardLookup, dLookupCache)
            self._aWarnings.extend(oHolder.get_warnings())
            oLogger.info('%s %s read', oIdParser.type, oItem.filename)
        oTrans.commit(close=True)
        sqlhub.processConnection = oOldConn
        if len(aToRead) == len(aList):
            # We were unable to read any items this loop, so we fail
            raise IOError('Card sets with unstatisfiable parents %s' %
                          ','.join([x.filename for x in aToRead]))
        return aToRead

    # Helper methods for influencing how the zip files are handled
    # subclasses should override these

    def _check_forced_reparent(self, oIdParser):
        """Do we need to force the parent of this to be 'My Collection'?"""
        raise NotImplementedError(
            "implement _check_forced_reparent")  # pragma: no cover

    def _should_force_reparent(self, oIdParser):
        """Check if we may need to force reparenting of card sets to
           'My Collection'"""
        raise NotImplementedError(
            "implement _should_force_reparent")  # pragma: no cover

    def _check_refresh(self, oIdParser):
        """Does this require we refresh the card set list?"""
        raise NotImplementedError(
            "implement _check_refresh")  # pragma: no cover

    def do_dump_all_to_zip(self, oLogHandler=None):
        """Dump all the database contents to the zip file"""
        aPhysicalCardSets = PhysicalCardSet.select()
        return self.do_dump_list_to_zip(aPhysicalCardSets, oLogHandler)

    def do_dump_list_to_zip(self, aCSList, oLogHandler=None):
        """Handle dumping a list of cards to the zip file with log fiddling"""
        self._open_zip_for_write()
        oLogger = Logger('Write zip file')
        if oLogHandler is not None:
            oLogger.addHandler(oLogHandler)
            if hasattr(oLogHandler, 'set_total'):
                if hasattr(aCSList, 'count'):
                    # Handle case we have a select result list
                    iTotal = aCSList.count()
                    oLogHandler.set_total(iTotal)
                else:
                    oLogHandler.set_total(len(aCSList))
        aPCSList = self._write_pcs_list_to_zip(aCSList, oLogger)
        self._close_zip()
        return aPCSList

    def dump_cs_names_to_zip(self, aCSNames, oLogHandler=None):
        """Utility function to dump a list of CS names to a zip"""
        aCSList = []
        for sName in aCSNames:
            aCSList.append(IPhysicalCardSet(sName))
        return self.do_dump_list_to_zip(aCSList, oLogHandler)

    def get_all_entries(self):
        """Return the list of card sets in the zip file"""
        self._open_zip_for_read()
        dCardSets = {}
        # pylint: disable=not-callable
        # subclasses will provide a callable cIdentifyFile
        oIdParser = self._cIdentifyFile()
        # pylint: enable=not-callable
        for oItem in self.oZip.infolist():
            oData = self.oZip.read(oItem.filename)
            oIdParser.parse_string(oData)
            if oIdParser.can_parse():
                dCardSets[oIdParser.name] = (oItem.filename,
                                             oIdParser.parent_exists,
                                             oIdParser.parent)
        self._close_zip()
        return dCardSets

    def read_single_card_set(self, sFilename):
        """Read a single card set into a card set holder."""
        self._open_zip_for_read()
        # pylint: disable=not-callable
        # subclasses will provide a callable cIdentifyFile
        oIdParser = self._cIdentifyFile()
        # pylint: enable=not-callable
        oData = self.oZip.read(sFilename)
        oIdParser.parse_string(oData)
        oHolder = None
        if oIdParser.can_parse():
            oHolder = CachedCardSetHolder()
            oParser = oIdParser.get_parser()
            parse_string(oParser, oData, oHolder)
        self._close_zip()
        return oHolder

    def get_info_file(self, sFileName):
        """Try to find a non-deck file in the zipfile.

           Return None if it's not present, otherwise return
           the contents."""
        self._open_zip_for_read()
        sData = None
        for oItem in self.oZip.infolist():
            if oItem.filename == sFileName:
                # First match found wins
                sData = self.oZip.read(oItem.filename)
                break
        self._close_zip()
        return sData

    def get_warnings(self):
        """Get any warnings from the process"""
        return self._aWarnings
