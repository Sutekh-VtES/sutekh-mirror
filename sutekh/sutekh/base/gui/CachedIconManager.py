# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Icon manager which returns Gtk pixmaps for the icons and caches lookups."""

import os

from gi.repository import GdkPixbuf, GLib

from ..io.BaseIconManager import BaseIconManager
from .ProgressDialog import ProgressDialog, SutekhCountLogHandler


# Crop the transparent border from the image
def _crop_alpha(oPixbuf):
    """Crop the transparent padding from a pixbuf.

       Needed to reduce scaling issues with the clan icons.
       """
    def _check_margins(iVal, iMax, iMin):
        """Check if the margins need to be updated"""
        if iVal < iMin:
            iMin = iVal
        if iVal > iMax:
            iMax = iVal
        return iMax, iMin
    # We don't use get_pixels_array, since numeric support is optional
    # These are gif's so the transparency is either 255 - opaque or 0 -
    # transparent. We want the bounding box of the non-transparent pixels
    iRowLength = oPixbuf.get_width() * 4
    iMaxX, iMaxY = -1, -1
    iMinX, iMinY = 1000, 1000
    iXPos, iYPos = 0, 0
    for cPixel in oPixbuf.get_pixels():
        if iXPos % 4 == 3:
            # Data is ordered RGBA, so this is the alpha channel
            if cPixel == 255:
                # Is opaque, so update margins
                iMaxX, iMinX = _check_margins(iXPos // 4, iMaxX, iMinX)
                iMaxY, iMinY = _check_margins(iYPos, iMaxY, iMinY)
        iXPos += 1
        if iXPos == iRowLength:
            # End of a line
            iYPos += 1
            iXPos = 0
    if iMinX >= iMaxX or iMinY >= iMaxY:
        # No transparency found
        return oPixbuf
    return oPixbuf.new_subpixbuf(iMinX + 1, iMinY + 1, iMaxX - iMinX,
                                 iMaxY - iMinY)


class CachedIconManager(BaseIconManager):
    """Managed icons for the gui application.

       Subclass BaseIconManager to return Gtk pixbufs, not filenames.
       Also provides gui interface for downloading icons.
       """

    def __init__(self, sPath):
        self._dIconCache = {}
        super().__init__(sPath)

    def _get_icon(self, sFileName, iSize=12):
        """get the cached icon, or load it if needed."""
        if not sFileName:
            return None
        if sFileName in self._dIconCache:
            return self._dIconCache[sFileName]
        try:
            sFullFilename = os.path.join(self._sPrefsDir, sFileName)
            oPixbuf = GdkPixbuf.Pixbuf.new_from_file(sFullFilename)
            # Crop the transparent border
            oPixbuf = _crop_alpha(oPixbuf)
            # Scale, but preserve aspect ratio
            iHeight = iSize
            iWidth = iSize
            iPixHeight = oPixbuf.get_height()
            iPixWidth = oPixbuf.get_width()
            fAspect = iPixHeight / float(iPixWidth)
            if iPixWidth > iPixHeight:
                iHeight = int(fAspect * iSize)
            elif iPixHeight > iPixWidth:
                iWidth = int(iSize / fAspect)
            oPixbuf = oPixbuf.scale_simple(iWidth, iHeight,
                                           GdkPixbuf.InterpType.TILES)
        except GLib.GError:
            oPixbuf = None
        self._dIconCache[sFileName] = oPixbuf
        return oPixbuf

    def setup(self):
        """Prompt the user to download the icons if the icon directory
           doesn't exist"""
        # Subclasses will implement this
        raise NotImplementedError

    def download_with_progress(self):
        """Wrap download_icons in a progress dialog"""
        self._dIconCache = {}  # Cache is invalidated by this
        oLogHandler = SutekhCountLogHandler()
        oProgressDialog = ProgressDialog()
        oProgressDialog.set_description("Downloading icons")
        oLogHandler.set_dialog(oProgressDialog)
        oProgressDialog.show()
        oLogHandler.set_total(self.get_icon_total())
        self.download_icons(oLogHandler)
        oProgressDialog.destroy()
