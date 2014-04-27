# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""GTK gui icon manager."""

import gtk
import gobject
import os
from sutekh.base.Utility import prefs_dir, ensure_dir_exists
from sutekh.io.IconManager import IconManager
from sutekh.gui.ProgressDialog import ProgressDialog, SutekhCountLogHandler
from sutekh.gui.SutekhDialog import do_complaint


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
            if ord(cPixel) == 255:
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
    return oPixbuf.subpixbuf(iMinX + 1, iMinY + 1, iMaxX - iMinX,
                             iMaxY - iMinY)


class GuiIconManager(IconManager):
    """Gui Manager for the VTES Icons.

       Subclass IconManager to return gtk pixbufs, not filenames.
       Also provides gui interfaces for setup and downloading icons.
       """

    def __init__(self, sPath):
        if not sPath:
            sPath = os.path.join(prefs_dir('Sutekh'), 'icons')
        self._dIconCache = {}
        super(GuiIconManager, self).__init__(sPath)

    def _get_icon(self, sFileName, iSize=12):
        """get the cached icon, or load it if needed."""
        if not sFileName:
            return None
        if sFileName in self._dIconCache:
            return self._dIconCache[sFileName]
        try:
            sFullFilename = os.path.join(self._sPrefsDir, sFileName)
            oPixbuf = gtk.gdk.pixbuf_new_from_file(sFullFilename)
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
                                           gtk.gdk.INTERP_TILES)
        except gobject.GError:
            oPixbuf = None
        self._dIconCache[sFileName] = oPixbuf
        return oPixbuf

    def setup(self):
        """Prompt the user to download the icons if the icon directory
           doesn't exist"""
        if os.path.lexists(self._sPrefsDir):
            # We accept broken links as stopping the prompt
            if os.path.lexists("%s/clans" % self._sPrefsDir):
                return
            else:
                # Check if we need to upgrade to the V:EKN icons
                ensure_dir_exists("%s/clans" % self._sPrefsDir)
                if os.path.exists('%s/IconClanAbo.gif' % self._sPrefsDir):
                    iResponse = do_complaint(
                            "Sutekh has switched to using the icons from the "
                            "V:EKN site.\nIcons won't work until you "
                            "re-download them.\n\nDownload icons?",
                            gtk.MESSAGE_INFO, gtk.BUTTONS_YES_NO, False)
                else:
                    # Old icons not present, so skip
                    return
        else:
            # Create directory, so we don't prompt next time unless the user
            # intervenes
            ensure_dir_exists(self._sPrefsDir)
            ensure_dir_exists("%s/clans" % self._sPrefsDir)
            # Ask the user if he wants to download
            iResponse = do_complaint("Sutekh can download icons for the cards "
                    "from the V:EKN site\nThese icons will be stored in "
                    "%s\n\nDownload icons?" % self._sPrefsDir,
                    gtk.MESSAGE_INFO, gtk.BUTTONS_YES_NO, False)
        if iResponse == gtk.RESPONSE_YES:
            self._logged_download()
        else:
            # Let the user know about the other options
            do_complaint("Icon download skipped.\nYou can choose to download "
                    "the icons from the File menu.\nYou will not be prompted "
                    "again unless you delete %s" % self._sPrefsDir,
                    gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, False)

    def _logged_download(self):
        """Wrap download_icons in a progress dialog"""
        self._dIconCache = {}  # Cache is invalidated by this
        oLogHandler = SutekhCountLogHandler()
        oProgressDialog = ProgressDialog()
        oProgressDialog.set_description("Downloading icons")
        oLogHandler.set_dialog(oProgressDialog)
        oProgressDialog.show()
        oLogHandler.set_total(self.get_icon_total)
        self.download_icons(oLogHandler)
        oProgressDialog.destroy()
