# ZipFileWrapper.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>,
#                Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# Class and functions to manage zip file handling for Sutekh
# Split off from SutekhUtility.py and refactored, April 2007  - NM

import zipfile
from logging import Logger
from sqlobject import sqlhub
from sutekh.core.SutekhObjects import AbstractCardSet, PhysicalCardSet, \
        PhysicalList, AbstractCardSetList
from sutekh.core.CardLookup import DEFAULT_LOOKUP
from sutekh.SutekhUtility import refresh_tables
from sutekh.io.PhysicalCardParser import PhysicalCardParser
from sutekh.io.PhysicalCardSetParser import PhysicalCardSetParser
from sutekh.io.AbstractCardSetParser import AbstractCardSetParser
from sutekh.io.PhysicalCardWriter import PhysicalCardWriter
from sutekh.io.PhysicalCardSetWriter import PhysicalCardSetWriter
from sutekh.io.AbstractCardSetWriter import AbstractCardSetWriter
from sutekh.io.IdentifyXMLFile import IdentifyXMLFile

class ZipFileWrapper(object):
    def __init__(self, sZipFileName):
        self.sZipFileName = sZipFileName
        self.oZip = None

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

    def write_physical_card_list_to_zip(self, oLogger):
        """Add the contents of the physical card list to the zip file"""
        bClose = False
        if self.oZip is None:
            self.__open_zip_for_write()
            bClose = True
        oWriter = PhysicalCardWriter()
        # Zipfile doesn't handle unicode unencoded - blargh
        # Documentation suggests WinZip may not like this
        # elementtree's tostring seems to do the right thing, so we
        # trust it
        oString = oWriter.gen_xml_string()
        self.oZip.writestr('PhysicalCardList.xml', oString)
        oLogger.info('Physical Card Set written')
        # If oZip isn't writeable, zipfile throws a RunTime Error
        # We just let the exception handling pass this up to the caller,
        # since we can't really do anything about this here
        if bClose:
            self.__close_zip()

    def write_all_acs_to_zip(self, oLogger):
        """Add all the abstract card sets to the zip file"""
        bClose = False
        if self.oZip is None:
            self.__open_zip_for_write()
            bClose = True
        oAbstractCardSets = AbstractCardSet.select()
        aList = []
        for oACSet in oAbstractCardSets:
            sZName = oACSet.name
            oWriter = AbstractCardSetWriter()
            oString = oWriter.gen_xml_string(sZName)
            sZName = sZName.replace(" ", "_")
            sZName = sZName.replace("/", "_")
            sZipName = 'acs_%s.xml' % sZName
            sZipName = sZipName.encode('ascii', 'xmlcharrefreplace')
            aList.append(sZipName)
            self.oZip.writestr(sZipName, oString)
            oLogger.info('ACS: %s written', oACSet.name)
        if bClose:
            self.__close_zip()
        return aList

    def write_all_pcs_to_zip(self, oLogger):
        """Add all the physical card sets to the zip file"""
        bClose = False
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
            self.oZip.writestr(sZipName, oString)
            oLogger.info('PCS: %s written', oPCSet.name)
        if bClose:
            self.__close_zip()
        return aList

    def doRestoreFromZip(self, oCardLookup=DEFAULT_LOOKUP, oLogHandler=None):
        """Recover data from the zip file"""
        bPhysicalCardsRead = False
        self.__open_zip_for_read()
        oLogger = Logger('Restore zip file')
        if oLogHandler is not None:
            oLogger.addHandler(oLogHandler)
            if hasattr(oLogHandler,'set_total'):
                oLogHandler.set_total(len(self.oZip.infolist()))
        # We do this so we can accomodate user created zipfiles,
        # that don't nessecarily have the ordering we want
        for oItem in self.oZip.infolist():
            oData = self.oZip.read(oItem.filename)
            oParser = IdentifyXMLFile()
            (sType, sName, bExists) = oParser.parse_string(oData)
            if sType == 'PhysicalCard':
                # We delete the Physical Card List
                # Since this is restoring the contents of a zip file,
                # hopefully this is safe to do
                # if we fail, the database will be in an inconsitent state,
                # but that's going to be true anyway
                refresh_tables(PhysicalList, sqlhub.processConnection)
                refresh_tables(AbstractCardSetList, sqlhub.processConnection)
                oParser = PhysicalCardParser()
                oParser.parse_string(oData, oCardLookup)
                bPhysicalCardsRead = True
                oLogger.info('Physical Card List read')
                break
        if not bPhysicalCardsRead:
            self.__close_zip()
            raise IOError("No PhysicalCard list found in the zip file, cannot import")
        else:
            for oItem in self.oZip.infolist():
                oData = self.oZip.read(oItem.filename)
                oParser = IdentifyXMLFile()
                (sType, sName, bExists) = oParser.parse_string(oData)
                if sType == 'PhysicalCardSet':
                    oParser = PhysicalCardSetParser()
                elif sType == 'AbstractCardSet':
                    oParser = AbstractCardSetParser()
                else:
                    continue
                oParser.parse_string(oData, oCardLookup)
                oLogger.info('%s %s read', sType, oItem.filename)
        self.__close_zip()

    def doDumpAllToZip(self, oLogHandler=None):
        """Dump all the database contents to the zip file"""
        self.__open_zip_for_write()
        oLogger = Logger('Restore zip file')
        if oLogHandler is not None:
            oLogger.addHandler(oLogHandler)
            if hasattr(oLogHandler,'set_total'):
                iTotal = 1 + AbstractCardSet.select().count() + PhysicalCardSet.select().count()
                oLogHandler.set_total(iTotal)
        self.write_physical_card_list_to_zip(oLogger)
        aACSList = self.write_all_acs_to_zip(oLogger)
        aPCSList = self.write_all_pcs_to_zip(oLogger)
        self.__close_zip()
        return aACSList + aPCSList
