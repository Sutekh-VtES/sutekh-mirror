# DataPack.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2011 Simon Cross <hodgestar+sutekh@gmail.com>,
# Copyright 2009,2010,2011 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# Class and functions to manage zip data pack handling for Sutekh
# Split off from sutekh/gui/plugins/StarterDeckInfo.py and refactored,
#    June 2011

"""Provide tools for locating and extracting data pack ZIP files."""

import urllib2
import re


DOC_URL = 'http://sourceforge.net/apps/trac/sutekh/wiki/' \
          'UserDocumentation?format=txt'

ZIP_URL_BASE = 'http://sourceforge.net/apps/trac/sutekh/raw-attachment'


def find_data_pack(sTag, sDocUrl=DOC_URL, sZipUrlBase=ZIP_URL_BASE):
    """Read a documentation page and find a data pack URL.

    Returns None if no file could be found for the given tag.

    The section looked for looks something like:

    || '''Description''' || '''Tag''' || '''Date Updated''' || '''File'''
    || Some text || starters || date || [attachment:Foo.zip:wiki:FilePage Foo.zip] ||
    || Other text || rulebooks || date || [attachment:Bar.zip:wiki:FilePage Bar.zip] ||
    || Other text || twd || date || [attachment:Bas.zip:wiki:FilePage Bas.zip] ||

    dates are expected to be formated YYYY-MM-DD (strftime('%Y-%m-%d'))
    to avoid ambiguity.
    """
    oFile = urllib2.urlopen(sDocUrl)
    oHeaderRe = re.compile(r'^\|\|.*Tag')
    oAttachmentRe = re.compile(r'\[attachment:(?P<path>[^ ]*) ')
    iTagField = None
    iAttachField = None
    sZipUrl = None

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

    return sZipUrl
