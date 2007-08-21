# ZipFileWrapper.py
# Copyright 2007 Simon Cross <hodgestar@gmail.com>,
#                Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# Class and functions to manage zip file handling for Sutekh
# Split off from SutekhUtility.py and refactored, April 2007  - NM

import zipfile
from sqlobject import sqlhub
from sutekh.SutekhObjects import AbstractCardSet, PhysicalCardSet, PhysicalList
from sutekh.SutekhUtility import refreshTables
from sutekh.PhysicalCardParser import PhysicalCardParser
from sutekh.PhysicalCardSetParser import PhysicalCardSetParser
from sutekh.AbstractCardSetParser import AbstractCardSetParser
from sutekh.PhysicalCardWriter import PhysicalCardWriter
from sutekh.PhysicalCardSetWriter import PhysicalCardSetWriter
from sutekh.AbstractCardSetWriter import AbstractCardSetWriter
from sutekh.IdentifyXMLFile import IdentifyXMLFile

class ZipFileWrapper(object):
    def __init__(self,sZipFileName):
        self.sZipFileName = sZipFileName
        self.oZip = None

    def __openZipForWrite(self):
        self.oZip = zipfile.ZipFile(self.sZipFileName,'w')

    def __openZipForRead(self):
        self.oZip = zipfile.ZipFile(self.sZipFileName,'r')

    def __closeZip(self):
        self.oZip.close()
        self.oZip = None

    def writePhysicalCardListToZip(self):
        bClose = False
        if self.oZip is None:
            self.__openZipForWrite()
            bClose = True
        oW = PhysicalCardWriter()
        # Zipfile doesn't handle unicode unencoded - blargh
        # Documentation suggests WinZip may not like this
        oString = oW.genDoc().toprettyxml().encode('utf-8')
        self.oZip.writestr('PhysicalCardList.xml',oString)
        # If oZip isn't writeable, zipfile throws a RunTime Error
        # We just let the exception handling pass this up to the caller,
        # since we can't really do anything about this here
        if bClose:
            self.__closeZip()

    def writeAllAbstractCardSetsToZip(self):
        bClose = False
        if self.oZip is None:
            self.__openZipForWrite()
            bClose = True
        oAbstractCardSets = AbstractCardSet.select()
        aList = [];
        for acs in oAbstractCardSets:
            sZName = acs.name
            oW = AbstractCardSetWriter()
            oString = oW.genDoc(sZName).toprettyxml().encode('utf-8')
            sZName = sZName.replace(" ","_")
            sZName = sZName.replace("/","_")
            sZipName = 'acs_' + sZName.encode('ascii','xmlcharrefreplace') + '.xml'
            aList.append(sZipName)
            self.oZip.writestr(sZipName,oString)
        if bClose:
            self.__closeZip()
        return aList

    def writeAllPhysicalCardSetsToZip(self):
        bClose = False
        if self.oZip is None:
            self.__openZipForWrite()
            bClose = True
        oPhysicalCardSets = PhysicalCardSet.select()
        aList = [];
        for pcs in oPhysicalCardSets:
            sZName = pcs.name
            oW = PhysicalCardSetWriter()
            oString = oW.genDoc(sZName).toprettyxml().encode('utf-8')
            sZName = sZName.replace(" ","_")
            sZName = sZName.replace("/","_")
            sZipName = 'pcs_' + sZName.encode('ascii','xmlcharrefreplace') + '.xml'
            aList.append(sZipName)
            self.oZip.writestr(sZipName,oString)
        if bClose:
            self.__closeZip()
        return aList

    def doRestoreFromZip(self):
        bPhysicalCardsRead = False
        self.__openZipForRead()
        # We do this so we can accomodate user created zipfiles,
        # that don't nessecarily have the ordering we want
        for oItem in self.oZip.infolist():
            sFileName = oItem.filename.split('/')[-1]
            oData = self.oZip.read(oItem.filename)
            oP = IdentifyXMLFile()
            (sType,sName,bExists) = oP.parseString(oData)
            if sType == 'PhysicalCard':
                # We delete the Physical Card List
                # Since this is restoring the contents of a zip file,
                # hopefully this is safe to do
                # if we fail, the database will be in an inconsitent state,
                # but that's going to be true anyway
                refreshTables(PhysicalList,sqlhub.processConnection)
                oP = PhysicalCardParser()
                oP.parseString(oData)
                bPhysicalCardsRead = True
                break
        if not bPhysicalCardsRead:
            self.__closeZip()
            raise IOError("No PhysicalCard list found in the zip file, cannot import")
        else:
            for oItem in self.oZip.infolist():
                sFileName = oItem.filename.split('/')[-1]
                oData = self.oZip.read(oItem.filename)
                oP = IdentifyXMLFile()
                (sType,sName,bExists) = oP.parseString(oData)
                if sType == 'PhysicalCardSet':
                    oP = PhysicalCardSetParser()
                elif sType == 'AbstractCardSet':
                    oP = AbstractCardSetParser()
                else:
                    continue
                oP.parseString(oData)
        self.__closeZip()

    def doDumpAllToZip(self):
        self.__openZipForWrite()
        self.writePhysicalCardListToZip()
        aACSList = self.writeAllAbstractCardSetsToZip()
        aPCSList = self.writeAllPhysicalCardSetsToZip()
        self.__closeZip()
        return aACSList + aPCSList
