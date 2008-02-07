# XmlFileHandling.py
# Copyright 2007 Simon Cross <hodgestar@gmail.com>,
#                Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# Routines for writing and reading from XML files - used by Gui and Cli
# Split off from SutekhUtility as being somewhat clearer, April 2007 - NM

from sutekh.core.SutekhObjects import AbstractCardSet, PhysicalCardSet
from sutekh.core.CardLookup import DEFAULT_LOOKUP
from sutekh.SutekhUtility import gen_temp_file, gen_temp_dir, safe_filename
from sutekh.io.PhysicalCardParser import PhysicalCardParser
from sutekh.io.PhysicalCardSetParser import PhysicalCardSetParser
from sutekh.io.AbstractCardSetParser import AbstractCardSetParser
from sutekh.io.PhysicalCardWriter import PhysicalCardWriter
from sutekh.io.PhysicalCardSetWriter import PhysicalCardSetWriter
from sutekh.io.AbstractCardSetWriter import AbstractCardSetWriter
import os

class PhysicalCardXmlFile(object):
    def __init__(self, filename=None, dir=None, lookup=DEFAULT_LOOKUP):
        self.oCardLookup = lookup
        if filename is not None:
            self.sXmlFile = filename
        else:
            if dir is None:
                dir = gen_temp_dir()
            self.sXmlFile = gen_temp_file('physical_cards_', dir)

    def read(self):
        if self.sXmlFile is None:
            raise RuntimeError("No Filename specified")
        oP = PhysicalCardParser()
        oP.parse(file(self.sXmlFile,'rU'), self.oCardLookup)

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
    def __init__(self, filename=None, oCardLookup=None, lookup=DEFAULT_LOOKUP):
        self.oCardLookup = lookup
        self.sXmlFile = filename

    def read(self):
        if self.sXmlFile is None:
            raise RuntimeError("No Filename specified")
        oP = AbstractCardSetParser()
        oP.parse(file(self.sXmlFile,'rU'), self.oCardLookup)

    def write(self, sAbstractCardSetName):
        oW = AbstractCardSetWriter()
        if self.sXmlFile is None:
            filename = safe_filename(sAbstractCardSetName)
            fOut = file(filename,'w')
        else:
            fOut = file(self.sXmlFile,'w')
        oW.write(fOut, sAbstractCardSetName)
        fOut.close()

    def delete(self):
        if self.sXmlFile is None:
            raise RuntimeError("No Filename specified")
        os.remove(self.sXmlFile)

class PhysicalCardSetXmlFile(object):
    def __init__(self, filename=None, lookup=DEFAULT_LOOKUP):
        self.oCardLookup = lookup
        self.sXmlFile = filename

    def read(self):
        if self.sXmlFile is None:
            raise RuntimeError("No Filename specified")
        oP = PhysicalCardSetParser()
        oP.parse(file(self.sXmlFile,'rU'), self.oCardLookup)

    def write(self, sPhysicalCardSetName):
        oW = PhysicalCardSetWriter()
        if self.sXmlFile is None:
            filename = safe_filename(sPhysicalCardSetName)
            fOut = file(filename,'w')
        else:
            fOut = file(self.sXmlFile,'w')
        oW.write(fOut, sPhysicalCardSetName)
        fOut.close()

    def delete(self):
        if self.sXmlFile is None:
            raise RuntimeError("No Filename specified")
        os.remove(self.sXmlFile)

def writeAllAbstractCardSets(dir=''):
    oAbstractCardSets = AbstractCardSet.select()
    aList = []
    for acs in oAbstractCardSets:
        sFName = safe_filename(acs.name)
        filename = gen_temp_file('acs_'+sFName+'_', dir)
        oW = AbstractCardSetXmlFile(filename)
        aList.append(oW)
        oW.write(acs.name)
    return aList

def writeAllPhysicalCardSets(dir=''):
    oPhysicalCardSets = PhysicalCardSet.select()
    aList = []
    for pcs in oPhysicalCardSets:
        sFName = safe_filename(pcs.name)
        filename = gen_temp_file('pcs_'+sFName+'_', dir)
        oW = PhysicalCardSetXmlFile(filename)
        aList.append(oW)
        oW.write(pcs.name)
    return aList
