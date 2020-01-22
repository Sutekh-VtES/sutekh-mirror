# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Manage the icons from the WW site"""

from __future__ import print_function

import os
from logging import Logger
from urllib.request import urlopen
from urllib.error import HTTPError
from ..Utility import ensure_dir_exists


class BaseIconManager:
    """Manager for the card info Icons.

       Provides the basic support for managing and downloading icons.
       """

    sBaseUrl = None

    def __init__(self, sPath):
        self._sPrefsDir = sPath

    # pylint: disable=no-self-use
    # This exists to be overridden
    def _get_icon(self, sFileName, _iSize=12):
        """Return the icon.

           This is so subclasses can override it to return the
           appropriate thing rather than a filename."""
        return sFileName

    def _make_logger(self, oLogHandler=None):
        """Utility function to help handle logging setup"""
        oLogger = Logger('Download Icons')
        if oLogHandler is not None:
            oLogger.addHandler(oLogHandler)
        return oLogger

    def _download(self, sFileName, oLogger):
        """Download the icon and save it in the icons directory"""
        ensure_dir_exists(self._sPrefsDir)
        if not sFileName:
            oLogger.info('Processed non-icon')
            return
        sFullFilename = os.path.join(self._sPrefsDir, sFileName)
        sBaseDir = os.path.dirname(sFullFilename)
        sUrl = self.sBaseUrl + sFileName
        try:
            oUrl = urlopen(sUrl)
            # copy url to file
            ensure_dir_exists(sBaseDir)
            fOut = open(sFullFilename, 'wb')
            fOut.write(oUrl.read())
            fOut.close()
        except HTTPError as oErr:
            print('Unable to download %s: Error %s' % (sUrl, oErr))
        oLogger.info('Processed %s' % sFileName)

    def download_icons(self, oLogHandler=None):
        """Hook to handle downloading icons"""
        # Subclasses should implement this
        raise NotImplementedError

    def get_info(self, sText, cGrouping):
        """Hook for returning information about the icons"""
        # Subclasses should implement this
        raise NotImplementedError

    def get_icon_list(self, aValues):
        """Hook for returning icons for given list of values"""
        # Subclasses should implement this
        raise NotImplementedError

    def get_icon_total(self):
        """Hook to provide the total icon count"""
        # Subclasses should implement this
        raise NotImplementedError
