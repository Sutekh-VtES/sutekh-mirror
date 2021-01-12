# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>,
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# Class and functions to manage zip file handling for Sutekh
# Split off from SutekhUtility.py and refactored, April 2007  - NM

"""Provide a ZipFile class which wraps the functionlity from zipfile
   Sutekh needs."""

from sutekh.base.io.BaseZipFileWrapper import BaseZipFileWrapper
from sutekh.io.PhysicalCardSetWriter import PhysicalCardSetWriter
from sutekh.io.IdentifyXMLFile import IdentifyXMLFile


class ZipFileWrapper(BaseZipFileWrapper):
    """The zip file wrapper.

       This provides useful functions for dumping + extracting the
       database to / form a zipfile"""
    def __init__(self, sZipFileName):
        super().__init__(sZipFileName)
        self._cWriter = PhysicalCardSetWriter
        self._cIdentifyFile = IdentifyXMLFile

    def _check_forced_reparent(self, oIdParser):
        """Do we need to force the parent of this to be 'My Collection'?"""
        if self._bForceReparent and oIdParser.type == 'PhysicalCardSet':
            return True
        return False

    def _should_force_reparent(self, oIdParser):
        """Check if we may need to force reparenting of card sets to
           'My Collection'"""
        if oIdParser.type == 'PhysicalCard':
            return True
        return False

    def _check_refresh(self, oIdParser):
        """Does this require we refresh the card set list?"""
        if (oIdParser.type == 'PhysicalCard' or
                oIdParser.type == 'PhysicalCardSet'):
            return True
        return False
