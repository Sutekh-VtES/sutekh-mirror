# XmlFileHandling.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>,
# Copyright 2007, 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# Routines for writing and reading from XML files - used by Gui and Cli
# Split off from SutekhUtility as being somewhat clearer, April 2007 - NM


"""Routines for manipulating XML Files"""

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
    """Class for handling PhysicalCard XML Files"""
    def __init__(self, sFileName=None, sDir=None, oLookup=DEFAULT_LOOKUP):
        self.oCardLookup = oLookup
        if sFileName is not None:
            self.sXmlFile = sFileName
        else:
            if sDir is None:
                sDir = gen_temp_dir()
            self.sXmlFile = gen_temp_file('physical_cards_', sDir)

    def read(self):
        """Read the card collection from the file"""
        if self.sXmlFile is None:
            raise RuntimeError("No Filename specified")
        oParser = PhysicalCardParser()
        oParser.parse(file(self.sXmlFile,'rU'), self.oCardLookup)

    def write(self):
        """Write the card collection to the file"""
        if self.sXmlFile is None:
            raise RuntimeError("No Filename specified")
        oWriter = PhysicalCardWriter()
        fOut = file(self.sXmlFile,'w')
        oWriter.write(fOut)
        fOut.close()

    def delete(self):
        """Delete the file"""
        if self.sXmlFile is None:
            raise RuntimeError("No Filename specified")
        os.remove(self.sXmlFile)

class AbstractCardSetXmlFile(object):
    """Class for handling Abstract Card Set XML files"""
    def __init__(self, sFileName=None, oLookup=DEFAULT_LOOKUP):
        self.oCardLookup = oLookup
        self.sXmlFile = sFileName

    def read(self):
        """Read the card set from the file."""
        if self.sXmlFile is None:
            raise RuntimeError("No Filename specified")
        oParser = AbstractCardSetParser()
        oParser.parse(file(self.sXmlFile,'rU'), self.oCardLookup)

    def write(self, sAbstractCardSetName):
        """Write the given card set to the file"""
        oWriter = AbstractCardSetWriter()
        if self.sXmlFile is None:
            sFileName = safe_filename(sAbstractCardSetName)
            fOut = file(sFileName,'w')
        else:
            fOut = file(self.sXmlFile,'w')
        oWriter.write(fOut, sAbstractCardSetName)
        fOut.close()

    def delete(self):
        """Delete the file"""
        if self.sXmlFile is None:
            raise RuntimeError("No Filename specified")
        os.remove(self.sXmlFile)

class PhysicalCardSetXmlFile(object):
    """Class for handling Physical Card Set XML files"""
    def __init__(self, sFileName=None, oLookup=DEFAULT_LOOKUP):
        self.oCardLookup = oLookup
        self.sXmlFile = sFileName

    def read(self):
        """Read the card set from the file."""
        if self.sXmlFile is None:
            raise RuntimeError("No Filename specified")
        oParser = PhysicalCardSetParser()
        oParser.parse(file(self.sXmlFile,'rU'), self.oCardLookup)

    def write(self, sPhysicalCardSetName):
        """Write the given card set to the file"""
        oWriter = PhysicalCardSetWriter()
        if self.sXmlFile is None:
            sFileName = safe_filename(sPhysicalCardSetName)
            fOut = file(sFileName,'w')
        else:
            fOut = file(self.sXmlFile,'w')
        oWriter.write(fOut, sPhysicalCardSetName)
        fOut.close()

    def delete(self):
        """Delete the file"""
        if self.sXmlFile is None:
            raise RuntimeError("No Filename specified")
        os.remove(self.sXmlFile)

def write_all_acs(sDir=''):
    """Write all the Abstract Card Sets into files in the given directory"""
    oAbstractCardSets = AbstractCardSet.select()
    aList = []
    for oACS in oAbstractCardSets:
        sFName = safe_filename(oACS.name)
        sFileName = gen_temp_file('acs_'+sFName+'_', sDir)
        oWriter = AbstractCardSetXmlFile(sFileName)
        aList.append(oWriter)
        oWriter.write(oACS.name)
    return aList

def write_all_pcs(sDir=''):
    """Write all the Physical Card Sets into files in the given directory"""
    oPhysicalCardSets = PhysicalCardSet.select()
    aList = []
    for oPCS in oPhysicalCardSets:
        sFName = safe_filename(oPCS.name)
        sFileName = gen_temp_file('pcs_'+sFName+'_', sDir)
        oWriter = PhysicalCardSetXmlFile(sFileName)
        aList.append(oWriter)
        oWriter.write(oPCS.name)
    return aList
