# ZipFileWrapper.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>,
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# Class and functions to manage zip file handling for Sutekh
# Split off from SutekhUtility.py and refactored, April 2007  - NM

"""Provide a ZipFile class which wraps the functionlity from zipfile
   Sutekh needs."""

import zipfile
import datetime
from logging import Logger
from sqlobject import sqlhub, SQLObjectNotFound
from sutekh.core.SutekhObjects import PhysicalCardSet, aPhysicalSetList
from sutekh.core.CardLookup import DEFAULT_LOOKUP
from sutekh.SutekhUtility import refresh_tables
from sutekh.io.PhysicalCardParser import PhysicalCardParser
from sutekh.io.PhysicalCardSetParser import PhysicalCardSetParser
from sutekh.io.AbstractCardSetParser import AbstractCardSetParser
from sutekh.io.PhysicalCardSetWriter import PhysicalCardSetWriter
from sutekh.io.IdentifyXMLFile import IdentifyXMLFile

class ZipFileWrapper(object):
    """The zip file wrapper.

       This provides useful functions for dumping + extracting the
       database to / form a zipfile"""
    def __init__(self, sZipFileName):
        self.sZipFileName = sZipFileName
        self.oZip = None
        self._aWarnings = []

    def __open_zip_for_write(self):
        """Open zip file to be written"""
        self.oZip = zipfile.ZipFile(self.sZipFileName, 'w')

    def __open_zip_for_read(self):
        """Open zip file to be read"""
        self.oZip = zipfile.ZipFile(self.sZipFileName, 'r')

    def __close_zip(self):
        """Close the zip file and clean up"""
        self.oZip.close()
        self.oZip = None

    def write_all_pcs_to_zip(self, oLogger):
        """Add all the physical card sets to the zip file"""
        bClose = False
        tTime = datetime.datetime.now().timetuple()
        if self.oZip is None:
            self.__open_zip_for_write()
            bClose = True
        oPhysicalCardSets = PhysicalCardSet.select()
        aList = []
        for oPCSet in oPhysicalCardSets:
            sZName = oPCSet.name
            oWriter = PhysicalCardSetWriter()
            oString = oWriter.gen_xml_string(sZName)
            sZName = sZName.replace(" ", "_")
            sZName = sZName.replace("/", "_")
            sZipName = 'pcs_%s.xml' % sZName
            sZipName = sZipName.encode('ascii', 'xmlcharrefreplace')
            aList.append(sZipName)
            # ZipInfo will just use the 1st 6 fields in tTime
            oInfoObj = zipfile.ZipInfo(sZipName, tTime)
            # Set permissions on the created file - see issue 3394 on the
            # python bugtracker. Docs say this is safe on all platforms
            oInfoObj.external_attr = 0600 << 16L
            self.oZip.writestr(oInfoObj, oString)
            oLogger.info('PCS: %s written', oPCSet.name)
        if bClose:
            self.__close_zip()
        return aList

    def do_restore_from_zip(self, oCardLookup=DEFAULT_LOOKUP,
            oLogHandler=None):
        """Recover data from the zip file"""
        self._aWarnings = []
        bTablesRefreshed = False
        bOldStyle = False
        self.__open_zip_for_read()
        oLogger = Logger('Restore zip file')
        if oLogHandler is not None:
            oLogger.addHandler(oLogHandler)
            if hasattr(oLogHandler,'set_total'):
                oLogHandler.set_total(len(self.oZip.infolist()))
        # We do this so we can accomodate user created zipfiles,
        # that don't nessecarily have the ordering we want
        oIdParser = IdentifyXMLFile()
        # check that the zip file contains at least 1 PCS or the old
        # PhysicalCard list
        for oItem in self.oZip.infolist():
            oData = self.oZip.read(oItem.filename)
            oIdParser.parse_string(oData)
            if (oIdParser.type == 'PhysicalCard' or \
                    oIdParser.type == 'PhysicalCardSet') and not \
                    bTablesRefreshed:
                # We delete the Physical Card Sets
                # Since this is restoring the contents of a zip file,
                # hopefully this is safe to do
                # if we fail, the database will be in an inconsitent state,
                # but that's going to be true anyway
                refresh_tables(aPhysicalSetList, sqlhub.processConnection)
                bTablesRefreshed = True
            if oIdParser.type == 'PhysicalCard':
                bOldStyle = True
        if not bTablesRefreshed:
            raise IOError("No valid card sets found in the zip file.")
        # We try and restore the old PCS's ensuring parents exist
        dLookupCache = {}
        aToRead = self.oZip.infolist()
        while len(aToRead) > 0:
            aToRead = self.read_items(aToRead, oCardLookup, oLogger, bOldStyle,
                    dLookupCache)
        self.__close_zip()

    # pylint: disable-msg=R0913
    # we may need all these arguments
    def read_items(self, aList, oCardLookup, oLogger, bOldStyle, dLookupCache):
        """Read a list of CardSet items from the card list, reaturning
           a list of those that couldn't be read because their parents
           weren't read first"""
        aToRead = []
        oIdParser = IdentifyXMLFile()
        for oItem in aList:
            bReparent = False
            oData = self.oZip.read(oItem.filename)
            oIdParser.parse_string(oData)
            if oIdParser.type == 'PhysicalCardSet':
                # We check whether the parent has been read already
                if bOldStyle:
                    # We need to reparent this card set
                    try:
                        oParent = PhysicalCardSet.selectBy(
                                name='My Collection').getOne()
                        bReparent = True
                        oParser = PhysicalCardSetParser()
                    except SQLObjectNotFound:
                        # Card Collection not there yet, so delay
                        aToRead.append(oItem)
                        continue
                elif oIdParser.parent_exists:
                    oParser = PhysicalCardSetParser()
                else:
                    aToRead.append(oItem)
                    continue
            elif oIdParser.type == 'AbstractCardSet':
                oParser = AbstractCardSetParser()
            elif oIdParser.type == 'PhysicalCard':
                oParser = PhysicalCardParser()
            else:
                continue
            self._aWarnings.extend(oParser.parse_string(oData, oCardLookup,
                True, dLookupCache))
            oLogger.info('%s %s read', oIdParser.type, oItem.filename)
            if bReparent:
                # pylint: disable-msg=E1103
                # SQLObject confuses pylint
                oPCS = PhysicalCardSet.selectBy(name=oIdParser.name).getOne()
                oPCS.parent = oParent
                oPCS.syncUpdate()
        if len(aToRead) == len(aList):
            # We were unable to read any items this loop, so we fail
            raise IOError('Card sets with unstatisfiable parents %s' %
                    ','.join([x.filename for x in aToRead]))
        return aToRead

    # pylint: enable-msg=R0913

    def do_dump_all_to_zip(self, oLogHandler=None):
        """Dump all the database contents to the zip file"""
        self.__open_zip_for_write()
        oLogger = Logger('Restore zip file')
        if oLogHandler is not None:
            oLogger.addHandler(oLogHandler)
            if hasattr(oLogHandler,'set_total'):
                iTotal = PhysicalCardSet.select().count()
                oLogHandler.set_total(iTotal)
        aPCSList = self.write_all_pcs_to_zip(oLogger)
        self.__close_zip()
        return aPCSList

    def get_all_entries(self):
        """Return the list of card sets in the zip file"""
        self.__open_zip_for_read()
        dCardSets = {}
        oIdParser = IdentifyXMLFile()
        for oItem in self.oZip.infolist():
            oData = self.oZip.read(oItem.filename)
            oIdParser.parse_string(oData)
            if oIdParser.type == 'PhysicalCardSet':
                dCardSets[oIdParser.name] = (oItem.filename,
                        oIdParser.parent_exists, oIdParser.parent)
        self.__close_zip()
        return dCardSets

    def read_single_card_set(self, sFilename):
        """Read a single card set into a card set holder."""
        self.__open_zip_for_read()
        oIdParser = IdentifyXMLFile()
        oData = self.oZip.read(sFilename)
        oIdParser.parse_string(oData)
        oParser = None
        if oIdParser.type == 'PhysicalCardSet':
            oParser = PhysicalCardSetParser()
            oParser.string_to_holder(oData)
        self.__close_zip()
        if oParser:
            return oParser.oCS
        return None

    def get_warnings(self):
        """Get any warnings from the process"""
        return self._aWarnings
