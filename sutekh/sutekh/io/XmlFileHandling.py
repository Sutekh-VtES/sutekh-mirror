# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>,
# Copyright 2007, 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# Routines for writing and reading from XML files - used by Gui and Cli
# Split off from SutekhUtility as being somewhat clearer, April 2007 - NM


"""Routines for manipulating XML Files"""

import os

from sqlobject import SQLObjectNotFound

from sutekh.base.Utility import gen_temp_file, safe_filename
from sutekh.base.core.BaseTables import PhysicalCardSet
from sutekh.base.core.BaseAdapters import IPhysicalCardSet
from sutekh.base.core.CardSetHolder import CardSetHolder, CardSetWrapper
from sutekh.base.core.CardLookup import DEFAULT_LOOKUP

from sutekh.io.PhysicalCardParser import PhysicalCardParser
from sutekh.io.PhysicalCardSetParser import PhysicalCardSetParser
from sutekh.io.AbstractCardSetParser import AbstractCardSetParser
from sutekh.io.PhysicalCardSetWriter import PhysicalCardSetWriter


def _do_read(oParser, sFileName, oLookup, bIgnoreWarnings):
    """Helper function to read from a parser"""
    oHolder = CardSetHolder()
    oParser.parse(open(sFileName, 'r'), oHolder)
    oHolder.create_pcs(oLookup)
    if not bIgnoreWarnings:
        return oHolder.get_warnings()
    return None


class PhysicalCardXmlFile:
    """Class for handling PhysicalCard XML Files"""
    def __init__(self, sFileName=None, oLookup=DEFAULT_LOOKUP):
        self.oCardLookup = oLookup
        self.sXmlFile = sFileName

    def read(self, bIgnoreWarnings=True):
        """Read the card collection from the file"""
        if self.sXmlFile is None:
            raise IOError("No Filename specified")
        oParser = PhysicalCardParser()
        return _do_read(oParser, self.sXmlFile, self.oCardLookup,
                        bIgnoreWarnings)

    # pylint: disable=no-self-use
    # method for backwards compatibility
    def write(self):
        """Write the card collection to the file (DEPRECATED)."""
        raise RuntimeError("Writing out of physical card lists to XML files"
                           " is no longer supported.")

    def delete(self):
        """Delete the file"""
        if self.sXmlFile is None:
            raise IOError("No Filename specified")
        os.remove(self.sXmlFile)


class AbstractCardSetXmlFile:
    """Class for handling Abstract Card Set XML files"""
    def __init__(self, sFileName=None, oLookup=DEFAULT_LOOKUP):
        self.oCardLookup = oLookup
        self.sXmlFile = sFileName

    def read(self, bIgnoreWarnings=True):
        """Read the card set from the file."""
        if self.sXmlFile is None:
            raise IOError("No Filename specified")
        oParser = AbstractCardSetParser()
        return _do_read(oParser, self.sXmlFile, self.oCardLookup,
                        bIgnoreWarnings)

    # pylint: disable=no-self-use
    # method for backwards compatibility
    def write(self, _sAbstractCardSetName):
        """Write the given card set to the file (DEPRECATED)."""
        raise RuntimeError("Writing out of abstract card sets to XML files"
                           " is no longer supported.")

    def delete(self):
        """Delete the file"""
        if self.sXmlFile is None:
            raise IOError("No Filename specified")
        os.remove(self.sXmlFile)


class PhysicalCardSetXmlFile:
    """Class for handling Physical Card Set XML files"""
    def __init__(self, sFileName=None, oLookup=DEFAULT_LOOKUP):
        self.oCardLookup = oLookup
        self.sXmlFile = sFileName

    def read(self, bIgnoreWarnings=True):
        """Read the card set from the file."""
        if self.sXmlFile is None:
            raise IOError("No Filename specified")
        oParser = PhysicalCardSetParser()
        return _do_read(oParser, self.sXmlFile, self.oCardLookup,
                        bIgnoreWarnings)

    def write(self, sPCSName):
        """Write the given card set to the file"""
        oWriter = PhysicalCardSetWriter()
        if self.sXmlFile is None:
            sFileName = safe_filename(sPCSName) + '.xml'
        else:
            sFileName = self.sXmlFile
        fOut = open(sFileName, 'w')
        try:
            oPCS = IPhysicalCardSet(sPCSName)
        except SQLObjectNotFound as oExp:
            raise IOError(f'No card set named {sPCSName}') from oExp
        oHolder = CardSetWrapper(oPCS)
        oWriter.write(fOut, oHolder)
        fOut.close()
        return sFileName

    def delete(self):
        """Delete the file"""
        if self.sXmlFile is None:
            raise IOError("No Filename specified")
        os.remove(self.sXmlFile)


def write_all_pcs(sDir=''):
    """Write all the Physical Card Sets into files in the given directory"""
    oPhysicalCardSets = PhysicalCardSet.select()
    aList = []
    for oPCS in oPhysicalCardSets:
        sFName = safe_filename(oPCS.name)
        sFileName = gen_temp_file('pcs_' + sFName + '_', sDir)
        oWriter = PhysicalCardSetXmlFile(sFileName)
        aList.append(oWriter)
        oWriter.write(oPCS.name)
    return aList
