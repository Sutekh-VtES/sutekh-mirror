# SutekhUtility.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Minor modifications copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# Misc Useful functions needed in several places. Mainly to do with database
# management. Seperated out from SutekhCli and other places, NM, 2006

from sutekh.SutekhObjects import VersionTable, AbstractCardSet, PhysicalCardSet
from sutekh.DatabaseVersion import DatabaseVersion
from sutekh.WhiteWolfParser import WhiteWolfParser
from sutekh.RulingParser import RulingParser
from sutekh.PhysicalCardParser import PhysicalCardParser
from sutekh.PhysicalCardSetParser import PhysicalCardSetParser
from sutekh.AbstractCardSetParser import AbstractCardSetParser
from sutekh.PhysicalCardWriter import PhysicalCardWriter
from sutekh.PhysicalCardSetWriter import PhysicalCardSetWriter
from sutekh.AbstractCardSetWriter import AbstractCardSetWriter
from sutekh.IdentifyXMLFile import IdentifyXMLFile
from sqlobject import sqlhub
import codecs
import tempfile
import zipfile
import os

def refreshTables(aTables,oConn,**kw):
    aTables.reverse()
    for cCls in aTables:
        cCls.dropTable(ifExists=True,connection=oConn)
    aTables.reverse()
    oVerHandler=DatabaseVersion(oConn)
    if not oVerHandler.setVersion(VersionTable,VersionTable.tableversion,oConn):
        return False
    for cCls in aTables:
        cCls.createTable(connection=oConn)
        if not oVerHandler.setVersion(cCls, cCls.tableversion,oConn):
            return False
    return True

def readWhiteWolfList(sWwList):
    oldConn=sqlhub.processConnection
    sqlhub.processConnection=oldConn.transaction()
    oP = WhiteWolfParser()
    fIn = codecs.open(sWwList,'rU','cp1252')
    for sLine in fIn:
        oP.feed(sLine)
    fIn.close()
    sqlhub.processConnection.commit()
    sqlhub.processConnection=oldConn

def readRulings(sRulings):
    oldConn=sqlhub.processConnection
    sqlhub.processConnection=oldConn.transaction()
    oP = RulingParser()
    fIn = codecs.open(sRulings,'rU','cp1252')
    for sLine in fIn:
        oP.feed(sLine)
    fIn.close()
    sqlhub.processConnection.commit()
    sqlhub.processConnection=oldConn

def readPhysicalCards(sXmlFile):
    oP = PhysicalCardParser()
    oP.parse(file(sXmlFile,'rU'))

def writePhysicalCards(sXmlFile):
    oW = PhysicalCardWriter()
    fOut = file(sXmlFile,'w')
    oW.write(fOut)
    fOut.close()

def readPhysicalCardSet(sXmlFile):
    oP = PhysicalCardSetParser()
    oP.parse(file(sXmlFile,'rU'))

def writePhysicalCardSet(sPhysicalCardSetName,sXmlFile):
    oW = PhysicalCardSetWriter()
    if sXmlFile is None:
        filename=sPhysicalCardSetName.replace(" ","_") # I hate spaces in filenames
        fOut=file(filename,'w')
    else:
        fOut=file(sXmlFile,'w')
    oW.write(fOut,sPhysicalCardSetName)
    fOut.close()

def readAbstractCardSet(sXmlFile):
    oP = AbstractCardSetParser()
    oP.parse(file(sXmlFile,'rU'))

def writeAbstractCardSet(sAbstractCardSetName,sXmlFile):
    oW = AbstractCardSetWriter()
    if sXmlFile is None:
        filename=sAbstractCardSetName.replace(" ","_") # I hate spaces in filenames
        fOut=file(filename,'w')
    else:
        fOut=file(sXmlFile,'w')
    oW.write(fOut,sAbstractCardSetName)
    fOut.close()

def writeAllAbstractCardSets(dir=''):
    oAbstractCardSets = AbstractCardSet.select()
    aList=[];
    for acs in oAbstractCardSets:
        sFName=acs.name
        sFName=sFName.replace(" ","_")
        sFName=sFName.replace("/","_")
        (fd,filename)=tempfile.mkstemp('.xml','acs_'+sFName+'_',dir)
        os.close(fd)
        aList.append(filename)
        writeAbstractCardSet(acs.name,filename)
    return aList

def writeAllAbstractCardSetsToZip(oZipfile):
    oAbstractCardSets = AbstractCardSet.select()
    aList=[];
    for acs in oAbstractCardSets:
        sZName=acs.name
        oW = AbstractCardSetWriter()
        oString=oW.genDoc(sZName).toprettyxml().encode('utf-8')
        sZName=sZName.replace(" ","_")
        sZName=sZName.replace("/","_")
        sZipName='acs_'+sZName.encode('ascii','xmlcharrefreplace')+'.xml'
        aList.append(sZipName)
        oZipfile.writestr(sZipName,oString)
    return aList

def writeAllPhysicalCardSets(dir=''):
    oPhysicalCardSets = PhysicalCardSet.select()
    aList=[];
    for pcs in oPhysicalCardSets:
        sFName=pcs.name
        sFName=sFName.replace(" ","_")
        sFName=sFName.replace("/","_")
        (fd,filename)=tempfile.mkstemp('.xml','pcs_'+sFName+'_',dir)
        os.close(fd)
        aList.append(filename)
        writePhysicalCardSet(pcs.name,filename)
    return aList

def writeAllPhysicalCardSetsToZip(oZipfile):
    oPhysicalCardSets = PhysicalCardSet.select()
    aList=[];
    for pcs in oPhysicalCardSets:
        sZName=pcs.name
        oW = PhysicalCardSetWriter()
        oString=oW.genDoc(sZName).toprettyxml().encode('utf-8')
        sZName=sZName.replace(" ","_")
        sZName=sZName.replace("/","_")
        sZipName='pcs_'+sZName.encode('ascii','xmlcharrefreplace')+'.xml'
        aList.append(sZipName)
        oZipfile.writestr(sZipName,oString)
    return aList

def doDumpToZip(sZipFileName):
    oW=PhysicalCardWriter()
    # Zipfile doesn't handle unicode unencoded - blargh
    oString=oW.genDoc().toprettyxml().encode('utf-8')
    oZip=zipfile.ZipFile(sZipFileName,'w')
    oZip.writestr('PhysicalCardList.xml',oString)
    writeAllAbstractCardSetsToZip(oZip)
    writeAllPhysicalCardSetsToZip(oZip)
    oZip.close()

def doRestoreFromZip(sZipFileName):
    oZip=zipfile.ZipFile(sZipFileName,'r')
    bPhysicalCardsRead=False
    # We do this so we can accomodate user created zipfiles,
    # that don't neseecarily have the ordering we want
    for oItem in oZip.infolist():
        sFileName=oItem.filename.split('/')[-1]
        oData=oZip.read(oItem.filename)
        oP=IdentifyXMLFile()
        (sType,sName,bExists)=oP.parseString(oData)
        if sType=='PhysicalCard':
            oP = PhysicalCardParser()
            oP.parseString(oData)
            bPhysicalCardsRead=True
            break
    if not bPhysicalCardsRead:
        raise IOError("No PhysicalCard list found in the zip file, cannot import")
    else:
        for oItem in oZip.infolist():
            sFileName=oItem.filename.split('/')[-1]
            oData=oZip.read(oItem.filename)
            oP=IdentifyXMLFile()
            (sType,sName,bExists)=oP.parseString(oData)
            if sType=='PhysicalCardSet':
                oP=PhysicalCardSetParser()
            elif sType=='AbstractCardSet':
                oP=AbstractCardSetParser()
            else:
                continue
            oP.parseString(oData)

