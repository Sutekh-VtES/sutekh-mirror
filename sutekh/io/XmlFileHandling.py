# XmlFileHandling.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>,
# Copyright 2007, 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# Routines for writing and reading from XML files - used by Gui and Cli
# Split off from SutekhUtility as being somewhat clearer, April 2007 - NM


"""Routines for manipulating XML Files"""

from sutekh.core.SutekhObjects import PhysicalCardSet, IPhysicalCardSet
from sutekh.core.CardSetHolder import CardSetHolder, CardSetWrapper
from sutekh.core.CardLookup import DEFAULT_LOOKUP
from sutekh.SutekhUtility import gen_temp_file, gen_temp_dir, safe_filename
from sutekh.io.PhysicalCardParser import PhysicalCardParser
from sutekh.io.PhysicalCardSetParser import PhysicalCardSetParser
from sutekh.io.AbstractCardSetParser import AbstractCardSetParser
from sutekh.io.PhysicalCardSetWriter import PhysicalCardSetWriter
from sqlobject import SQLObjectNotFound
import os


def _do_read(oParser, sFileName, oLookup, bIgnoreWarnings):
    """Helper function to read from a parser"""
    oHolder = CardSetHolder()
    oParser.parse(file(sFileName, 'rU'), oHolder)
    oHolder.create_pcs(oLookup)
    if not bIgnoreWarnings:
        return oHolder.get_warnings()
    return None


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

    def read(self, bIgnoreWarnings=True):
        """Read the card collection from the file"""
        if self.sXmlFile is None:
            raise IOError("No Filename specified")
        oParser = PhysicalCardParser()
        return _do_read(oParser, self.sXmlFile, self.oCardLookup,
                bIgnoreWarnings)

    # pylint: disable-msg=R0201
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


class AbstractCardSetXmlFile(object):
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

    # pylint: disable-msg=R0201
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


class PhysicalCardSetXmlFile(object):
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

    def write(self, sPhysicalCardSetName):
        """Write the given card set to the file"""
        oWriter = PhysicalCardSetWriter()
        if self.sXmlFile is None:
            sFileName = safe_filename(sPhysicalCardSetName)
            fOut = file(sFileName, 'w')
        else:
            fOut = file(self.sXmlFile, 'w')
        try:
            oPCS = IPhysicalCardSet(sPhysicalCardSetName)
        except SQLObjectNotFound:
            raise IOError('No card set named %s ' % sPhysicalCardSetName)
        oHolder = CardSetWrapper(oPCS)
        oWriter.write(fOut, oHolder)
        fOut.close()

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
