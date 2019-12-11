# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2011 Simon Cross <hodgestar+sutekh@gmail.com>,
# Copyright 2009, 2010, 2011 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# Class and functions to manage zip data pack handling for Sutekh
# Split off from sutekh/gui/plugins/StarterDeckInfo.py and refactored,
#    June 2011

"""Provide tools for handling downloading data from urls."""

import urllib2
import socket
from logging import Logger
# pylint: disable=no-name-in-module
# hashlib is strange, and confuses pylint
from hashlib import sha256
# pylint: enable=no-name-in-module


class HashError(Exception):
    """Thrown when a checksum check fails"""

    def __init__(self, sData):
        super(HashError, self).__init__("Checksum comparison failed")
        # This is a bit ugly.  We shove the data here so it's easy to
        # add ignore choices without retrying the download in the gui
        self.sData = sData


def urlopen_with_timeout(sUrl, fErrorHandler=None, dHeaders=None, sData=None):
    """Wrap urllib2.urlopen to handle timeouts nicely"""
    # Note: The global timeout is currently set to the
    # config value at startup
    oReq = urllib2.Request(sUrl)
    if dHeaders:
        for sHeader, sValue in dHeaders.items():
            oReq.add_header(sHeader, sValue)
    if sData:
        oReq.add_data(sData)
    try:
        return urllib2.urlopen(oReq)
    except urllib2.URLError as oExp:
        if fErrorHandler:
            fErrorHandler(oExp)
        else:
            raise
    except socket.timeout as oExp:
        if fErrorHandler:
            fErrorHandler(oExp)
        else:
            raise
    return None


def fetch_data(oFile, oOutFile=None, sHash=None, oLogHandler=None,
               fErrorHandler=None):
    """Fetch data from a file'ish object (EncodedFile, urlopen or file)"""
    try:
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
    except urllib2.URLError as oExp:
        if fErrorHandler:
            fErrorHandler(oExp)
            sData = None
        else:
            raise
    except socket.timeout as oExp:
        if fErrorHandler:
            fErrorHandler(oExp)
            sData = None
        else:
            raise

    if sHash is not None:
        if sData is not None:
            # Only check has if we have data
            sDataHash = sha256(sData).hexdigest()
            if sDataHash != sHash:
                raise HashError(sData)
    return sData
