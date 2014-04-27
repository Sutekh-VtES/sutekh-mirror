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
import socket
import re

from sutekh.base.io.UrlOps import urlopen_with_timeout

DOC_URL = 'http://sourceforge.net/apps/trac/sutekh/wiki/' \
          'UserDocumentation?format=txt'

ZIP_URL_BASE = 'http://sourceforge.net/apps/trac/sutekh/raw-attachment'


def find_all_data_packs(sTag, sDocUrl=DOC_URL, sZipUrlBase=ZIP_URL_BASE,
        fErrorHandler=None):
    """Read a documentation page and find all the data pack URLs and hashes
    for the given tag.

    Returns empty lists if no file could be found for the given tag.

    The section looked for looks something like:

    || '''Description''' || '''Tag''' || '''Date Updated''' || '''File''' || SHA256 Checksum ||
    || Some text || starters || date || [attachment:Foo.zip:wiki:FilePage Foo.zip] || sha256sum ||
    || Other text || rulebooks || date || [attachment:Bar.zip:wiki:FilePage Bar.zip] || sha256sum ||
    || Other text || twd || date || [attachment:Bas.zip:wiki:FilePage Bas.zip] || sha256sum ||
    || Other text || twd || date || [attachment:Bas2.zip:wiki:FilePage Bas2.zip] || sha256sum ||

    dates are expected to be formated YYYY-MM-DD (strftime('%Y-%m-%d'))
    to avoid ambiguity.
    """
    oFile = urlopen_with_timeout(sDocUrl, fErrorHandler)
    if not oFile:
        return None, None, None
    oHeaderRe = re.compile(r'^\|\|.*Tag')
    oAttachmentRe = re.compile(r'\[attachment:(?P<path>[^ ]*) ')
    iTagField = None
    iAttachField = None
    aZipUrls = []
    aHashes = []
    aDates = []

    def fields(sLine):
        """Helper function to split table lines into the needed structure"""
        sLine = sLine.strip()
        return [sField.strip(" '") for sField in sLine.split('||')]

    try:
        aData = oFile.readlines()
    except urllib2.URLError, oExp:
        if fErrorHandler:
            fErrorHandler(oExp)
            aData = []
        else:
            raise
    except socket.timeout, oExp:
        if fErrorHandler:
            fErrorHandler(oExp)
            aData = []
        else:
            raise

    for sLine in aData:
        if iTagField is None:
            oMatch = oHeaderRe.match(sLine)
            if oMatch:
                aFields = fields(sLine)
                if 'Tag' not in aFields or 'File' not in aFields:
                    continue
                iTagField = aFields.index('Tag')
                iAttachField = aFields.index('File')
                iDateField = aFields.index('Date Updated')
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
                    # We need to split off the zip file name and the path
                    # bits
                    sZipName, sPath = sPath.split(':', 1)
                    sPath = sPath.replace(':', '/')
                    aZipUrls.append('/'.join((sZipUrlBase, sPath,
                        sZipName)))
                    if iShaSumField is not None:
                        aHashes.append(aFields[iShaSumField])
                    aDates.append(aFields[iDateField])

    return aZipUrls, aDates, aHashes


def find_data_pack(sTag, sDocUrl=DOC_URL, sZipUrlBase=ZIP_URL_BASE,
        fErrorHandler=None):
    """Find a single data pack for a tag. Return url and hash, if appropriate.

    Return None if no match is found.

    See find_all_data_packs for details for the wiki page format.

    If multiple datapack are found, return the last."""
    aZipUrls, _aSkip, aHashes = find_all_data_packs(sTag, sDocUrl, sZipUrlBase,
                                                    fErrorHandler)
    if not aZipUrls:
        # No match
        return None, None
    elif not aHashes:
        # No hash
        return aZipUrls[-1], None
    return aZipUrls[-1], aHashes[-1]
