# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2011 Simon Cross <hodgestar+sutekh@gmail.com>,
# Copyright 2009, 2010, 2011 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# Class and functions to manage zip data pack handling for Sutekh
# Split off from sutekh/gui/plugins/StarterDeckInfo.py and refactored,
#    June 2011

"""Provide tools for locating and extracting data pack ZIP files."""

import datetime
import time
import simplejson
import urllib2
import urlparse
import socket

DOC_URL = ('https://bitbucket.org/hodgestar/sutekh-datapack/raw/master/'
           'index.json')


def parse_datapack_date(sDate):
    """Parse a datapack's ISO format date entry into a datetime object."""
    sDate, _sMicro = sDate.split('.', 1)
    # work around python 2.4 shortcomings
    return datetime.datetime(*(time.strptime(sDate, "%Y-%m-%dT%H:%M:%S")[0:6]))


def find_all_data_packs(sTag, sDocUrl=DOC_URL, fErrorHandler=None):
    """Read the data pack index and return all datapacks listed for the
    given tag.

    Returns empty lists if no file could be found for the given tag.

    The index is a JSON file with the following structure:

    {
    "datapacks": [
        {
            "description": "Zip file of starter decks ...",
            "file": "Starters/Starters_SW_to_HttB_and_Others.zip",
            "sha256": "4f1867568127b12276efbe9bafa261f4ad86741ff09549a48f6...",
            "tag": "starters",
            "updated_at": "2014-07-04T18:54:31.802636"
        },
        ...
    ],
    "format": "sutekh-datapack",
    "format-version": "1.0"
    }
    """
    try:
        oFile = urllib2.urlopen(sDocUrl)
    except (urllib2.URLError, socket.timeout), oExp:
        if fErrorHandler:
            fErrorHandler(oExp)
            oFile = None
        else:
            raise

    if not oFile:
        return None, None, None
    try:
        dIndex = simplejson.load(oFile)
    except (urllib2.URLError, socket.timeout, ValueError), oExp:
        if fErrorHandler:
            fErrorHandler(oExp)
            return None, None, None
        else:
            raise
    aZipUrls = []
    aHashes = []
    aDates = []
    for dPack in dIndex["datapacks"]:
        if dPack.get("tag") != sTag:
            continue
        aZipUrls.append(urlparse.urljoin(sDocUrl, dPack["file"]))
        aHashes.append(dPack["sha256"])
        oDate = parse_datapack_date(dPack["updated_at"])
        aDates.append(oDate.strftime("%Y-%m-%d"))

    return aZipUrls, aDates, aHashes


def find_data_pack(sTag, sDocUrl=DOC_URL, fErrorHandler=None):
    """Find a single data pack for a tag. Return url and hash, if appropriate.

    Return None if no match is found.

    See find_all_data_packs for details on the sutekh datapack format.

    If multiple datapack are found, return the last."""
    aZipUrls, _aSkip, aHashes = find_all_data_packs(
        sTag, sDocUrl=sDocUrl, fErrorHandler=fErrorHandler)
    if not aZipUrls:
        # No match
        return None, None
    elif not aHashes:
        # No hash
        return aZipUrls[-1], None
    return aZipUrls[-1], aHashes[-1]
