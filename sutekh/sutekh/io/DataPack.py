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
import json
from urllib.error import URLError
from urllib.parse import urljoin
import socket

from sutekh.base.io.UrlOps import urlopen_with_timeout

DOC_URL = ('https://bitbucket.org/hodgestar/sutekh-datapack/raw/master/'
           'index.json')


def parse_datapack_date(sDate):
    """Parse a datapack's ISO format date entry into a datetime object."""
    return datetime.datetime.strptime(sDate, "%Y-%m-%dT%H:%M:%S.%f")


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
    oFile = urlopen_with_timeout(sDocUrl, fErrorHandler)
    if not oFile:
        return None, None, None
    try:
        dIndex = json.load(oFile)
    except (URLError, socket.timeout, ValueError) as oExp:
        if fErrorHandler:
            fErrorHandler(oExp)
            return None, None, None
        raise
    finally:
        # This is a basically a no-op for remote urls, but needed
        # for when we're dealing with a local file
        oFile.close()
    aZipUrls = []
    aHashes = []
    aDates = []
    for dPack in dIndex["datapacks"]:
        if dPack.get("tag") != sTag:
            continue
        aZipUrls.append(urljoin(sDocUrl, dPack["file"]))
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
    if not aHashes:
        # No hash
        return aZipUrls[-1], None
    return aZipUrls[-1], aHashes[-1]
