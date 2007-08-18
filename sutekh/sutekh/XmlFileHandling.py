# XmlFileHandling.py
# Copyright 2007 Simon Cross <hodgestar@gmail.com>,
#                Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# Routines for writing and reading from XML files - used by Gui and Cli
# Split off from SutekhUtility as being somewhat clearer, April 2007 - NM

from sutekh.SutekhObjects import AbstractCardSet, PhysicalCardSet
from sutekh.SutekhUtility import genTempFile, genTempdir, safeFilename
from sutekh.PhysicalCardParser import PhysicalCardParser
from sutekh.PhysicalCardSetParser import PhysicalCardSetParser
from sutekh.AbstractCardSetParser import AbstractCardSetParser
from sutekh.PhysicalCardWriter import PhysicalCardWriter
from sutekh.PhysicalCardSetWriter import PhysicalCardSetWriter
from sutekh.AbstractCardSetWriter import AbstractCardSetWriter
import os

class PhysicalCardXmlFile(object):
    def __init__(self,filename=None,dir=None):
        if filename is not None:
            self.sXmlFile = filename
        else:
            if dir is None:
                dir = genTempdir()
            self.sXmlFile = genTempFile('physical_cards_',dir)

    def read(self):
        if self.sXmlFile is None:
            raise RuntimeError("No Filename specified")
        oP = PhysicalCardParser()
        oP.parse(file(self.sXmlFile,'rU'))

    def write(self):
        if self.sXmlFile is None:
            raise RuntimeError("No Filename specified")
        oW = PhysicalCardWriter()
        fOut = file(self.sXmlFile,'w')
        oW.write(fOut)
        fOut.close()

    def delete(self):
        if self.sXmlFile is None:
            raise RuntimeError("No Filename specified")
        os.remove(self.sXmlFile)

class AbstractCardSetXmlFile(object):
    def __init__(self,filename=None):
        self.sXmlFile = filename

    def read(self):
        if self.sXmlFile is None:
            raise RuntimeError("No Filename specified")
        oP = AbstractCardSetParser()
        oP.parse(file(self.sXmlFile,'rU'))

    def write(self,sAbstractCardSetName):
        oW = AbstractCardSetWriter()
        if self.sXmlFile is None:
            filename = safeFilename(sAbstractCardSetName)
            fOut = file(filename,'w')
        else:
            fOut = file(self.sXmlFile,'w')
        oW.write(fOut,sAbstractCardSetName)
        fOut.close()

    def delete(self):
        if self.sXmlFile is None:
            raise RuntimeError("No Filename specified")
        os.remove(self.sXmlFile)

class PhysicalCardSetXmlFile(object):
    def __init__(self,filename=None):
        self.sXmlFile = filename

    def read(self):
        if self.sXmlFile is None:
            raise RuntimeError("No Filename specified")
        oP = PhysicalCardSetParser()
        oP.parse(file(self.sXmlFile,'rU'))

    def write(self,sPhysicalCardSetName):
        oW = PhysicalCardSetWriter()
        if self.sXmlFile is None:
            filename = safeFilename(sPhysicalCardSetName)
            fOut = file(filename,'w')
        else:
            fOut = file(self.sXmlFile,'w')
        oW.write(fOut,sPhysicalCardSetName)
        fOut.close()

    def delete(self):
        if self.sXmlFile is None:
            raise RuntimeError("No Filename specified")
        os.remove(self.sXmlFile)

def writeAllAbstractCardSets(dir=''):
    oAbstractCardSets = AbstractCardSet.select()
    aList = []
    for acs in oAbstractCardSets:
        sFName = safeFilename(acs.name)
        filename = genTempFile('acs_'+sFName+'_',dir)
        oW = AbstractCardSetXmlFile(filename)
        aList.append(oW)
        oW.write(acs.name)
    return aList

def writeAllPhysicalCardSets(dir=''):
    oPhysicalCardSets = PhysicalCardSet.select()
    aList = []
    for pcs in oPhysicalCardSets:
        sFName = safeFilename(pcs.name)
        filename = genTempFile('pcs_'+sFName+'_',dir)
        oW = PhysicalCardSetXmlFile(filename)
        aList.append(oW)
        oW.write(pcs.name)
    return aList
