# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2011 Simon Cross <hodgestar+sutekh@gmail.com>,
# Copyright 2009, 2010, 2011 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# Class and functions to manage zip data pack handling for Sutekh
# Split off from sutekh/gui/plugins/StarterDeckInfo.py and refactored,
#    June 2011

"""Provide tools for locating and extracting data pack ZIP files."""

import urllib2
import re
from logging import Logger
# pylint: disable-msg=E0611
# E0611: hashlib is stange, and confuses pylint
from hashlib import sha256
# pyline: enable-msg=E0611


DOC_URL = 'http://sourceforge.net/apps/trac/sutekh/wiki/' \
          'UserDocumentation?format=txt'

ZIP_URL_BASE = 'http://sourceforge.net/apps/trac/sutekh/raw-attachment'


class HashError(Exception):
    """Thrown when a checksum check fails"""

    def __init__(self, sData):
        super(HashError, self).__init__("Checksum comparison failed")
        # This is a bit ugly.  We shove the data here so it's easy to
        # add ignore choices without retrying the download in the gui
        self.sData = sData


def find_data_pack(sTag, sDocUrl=DOC_URL, sZipUrlBase=ZIP_URL_BASE):
    """Read a documentation page and find a data pack URL.

    Returns None if no file could be found for the given tag.

    The section looked for looks something like:

    || '''Description''' || '''Tag''' || '''Date Updated''' || '''File''' || SHA256 Checksum ||
    || Some text || starters || date || [attachment:Foo.zip:wiki:FilePage Foo.zip] || sha256sum ||
    || Other text || rulebooks || date || [attachment:Bar.zip:wiki:FilePage Bar.zip] || sha256sum ||
    || Other text || twd || date || [attachment:Bas.zip:wiki:FilePage Bas.zip] || sha256sum ||

    dates are expected to be formated YYYY-MM-DD (strftime('%Y-%m-%d'))
    to avoid ambiguity.
    """
    oFile = urllib2.urlopen(sDocUrl)
    oHeaderRe = re.compile(r'^\|\|.*Tag')
    oAttachmentRe = re.compile(r'\[attachment:(?P<path>[^ ]*) ')
    iTagField = None
    iAttachField = None
    sZipUrl = None
    sHash = None

    def fields(sLine):
        """Helper function to split table lines into the needed structure"""
        sLine = sLine.strip()
        return [sField.strip(" '") for sField in sLine.split('||')]

    for sLine in oFile.readlines():
        if iTagField is None:
            oMatch = oHeaderRe.match(sLine)
            if oMatch:
                aFields = fields(sLine)
                if 'Tag' not in aFields or 'File' not in aFields:
                    continue
                iTagField = aFields.index('Tag')
                iAttachField = aFields.index('File')
                if 'SHA256 Checksum' in aFields:
                    iShaSumField = aFields.index('SHA256 Checksum')
                else:
                    iShaSumField = None
        else:
            aFields = fields(sLine)
            if len(aFields) > iTagField and sTag == aFields[iTagField] \
                   and len(aFields) > iAttachField:
                oMatch = oAttachmentRe.search(aFields[iAttachField])
                if oMatch:
                    sPath = oMatch.group('path')
                    # We need to split off the zip file name and the path bits
                    sZipName, sPath = sPath.split(':', 1)
                    sPath = sPath.replace(':', '/')
                    sZipUrl = '/'.join((sZipUrlBase, sPath, sZipName))
                    if iShaSumField is not None:
                        sHash = aFields[iShaSumField]

    return sZipUrl, sHash


def fetch_data(oFile, oOutFile=None, sHash=None, oLogHandler=None):
    """Fetch data from a file'ish object (WwFile, urlopen or file)"""
    if hasattr(oFile, 'info') and callable(oFile.info):
        sLength = oFile.info().getheader('Content-Length')
    else:
        sLength = None

    if sLength:
        oLogger = Logger('Sutekh data fetcher')
        if oLogHandler is not None:
            oLogger.addHandler(oLogHandler)
        aData = []
        iLength = int(sLength)
        if hasattr(oLogHandler, 'set_total'):
            # We promote to next integer, as we emit a signal
            # for any left over bits
            oLogHandler.set_total((iLength + 9999) // 10000)
        iTotal = 0
        bCont = True
        while bCont:
            sInf = oFile.read(10000)
            iTotal += len(sInf)
            if sInf:
                oLogger.info('%d downloaded', iTotal)
                if oOutFile:
                    oOutFile.write(sInf)
                else:
                    aData.append(sInf)
            else:
                bCont = False
        if oOutFile:
            sData = None
        else:
            sData = ''.join(aData)
    else:
        # Just try and download
        if oOutFile:
            oOutFile.write(oFile.read())
            sData = None
        else:
            sData = oFile.read()
    if sHash is not None:
        sDataHash = sha256(sData).hexdigest()
        if sDataHash != sHash:
            raise HashError(sData)
    return sData
