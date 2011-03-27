# IconManager.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Manage the icons from the WW site"""

import gtk
import gobject
import os
from logging import Logger
from urllib2 import urlopen, HTTPError
from sutekh.SutekhUtility import prefs_dir, ensure_dir_exists
from sutekh.core.SutekhObjects import Clan, Creed, CardType, DisciplinePair, \
        Virtue, ICardType, IDisciplinePair, IVirtue, ICreed, IClan
from sutekh.gui.ProgressDialog import ProgressDialog, SutekhCountLogHandler
from sutekh.gui.SutekhDialog import do_complaint
from sutekh.core import Groupings


# Utilty functions - convert object to a filename
def _get_clan_filename(oClan):
    """Get the icon filename for the clan"""
    sClanName = oClan.name
    # Fix special cases
    if 'antitribu' in sClanName:
        sClanName = sClanName.replace('antitribu', 'anti')
    elif sClanName == 'Abomination':
        sClanName = 'abo'
    elif sClanName == 'Follower of Set':
        sClanName = 'fos'
    elif sClanName == 'Daughter of Cacophony':
        sClanName = 'daughters'
    elif sClanName == 'Harbinger of Skulls':
        sClanName = 'harbingers'
    elif sClanName == 'Blood Brother':
        sClanName = 'bloodbrothers'
    elif sClanName == 'Ahrimane':
        sClanName = 'ahrimanes'
    sClanName = sClanName.lower()
    sClanName = sClanName.replace(' ', '')
    sFileName = 'clans/iconclan%s.gif' % sClanName
    return sFileName


def _get_card_type_filename(oType):
    """Get the filename for the card type"""
    if oType.name == 'Action Modifier':
        sFileName = 'cardtype/icontypemodifier.gif'
    elif oType.name == 'Political Action':
        sFileName = 'cardtype/icontypepolitical.gif'
    elif oType.name in ('Master', 'Vampire', 'Imbued'):
        # These types have no icon
        sFileName = None
    else:
        sFileName = 'cardtype/icontype%s.gif' % oType.name.lower()
    return sFileName


def _get_creed_filename(oCreed):
    """Get the filename for the creed"""
    sFileName = 'creeds/iconcre%s.gif' % oCreed.name.lower()
    return sFileName


def _get_discipline_filename(oDiscipline):
    """Get the filename for the discipline."""
    if oDiscipline.discipline.name.lower() in ['mal', 'str', 'fli']:
        # These are misc icons
        if oDiscipline.discipline.fullname == 'Flight':
            sFileName = 'misc/iconmiscflight.gif'
        elif oDiscipline.level == 'inferior':
            sFileName = 'misc/iconmisc%s.gif' \
                    % oDiscipline.discipline.fullname.lower()
        else:
            sFileName = 'misc/iconmisc%ssup.gif' \
                    % oDiscipline.discipline.fullname.lower()
    elif oDiscipline.level == 'inferior':
        sFileName = 'disciplines/icondis%s.gif' \
                % oDiscipline.discipline.fullname.lower()
    else:
        sFileName = 'disciplines/icondis%ssup.gif' \
                % oDiscipline.discipline.fullname.lower()
    return sFileName


def _get_virtue_filename(oVirtue):
    """Get the filename for the virtue"""
    if oVirtue.name != 'jud':
        sFileName = 'virtues/iconvirtue%s.gif' % oVirtue.fullname.lower()
    else:
        # Annoying special case
        sFileName = 'virtues/iconvirtuejustice.gif'
    return sFileName


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
                iMaxX, iMinX = _check_margins(iXPos / 4, iMaxX, iMinX)
                iMaxY, iMinY = _check_margins(iYPos, iMaxY, iMinY)
        iXPos += 1
        if iXPos == iRowLength:
            # End of a line
            iYPos += 1
            iXPos = 0
    return oPixbuf.subpixbuf(iMinX + 1, iMinY + 1, iMaxX - iMinX,
            iMaxY - iMinY)


class IconManager(object):
    """Manager for the VTES Icons.

       Given the text and the tag name, look up the suitable matching icon
       for it.  Return none if no suitable icon is found.
       Also provide an option to download the icons form the v:ekn
       site.
       """

    sBaseUrl = "http://www.vekn.net/images/stories/icons/"

    def __init__(self, oConfig):
        self._sPrefsDir = oConfig.get_icon_path()
        if not self._sPrefsDir:
            self._sPrefsDir = os.path.join(prefs_dir('Sutekh'), 'icons')
        self._dIconCache = {}

    def _get_icon(self, sFileName, iSize=12):
        """get the cached icon, or load it if needed."""
        if not sFileName:
            return None
        if self._dIconCache.has_key(sFileName):
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

    def _get_clan_icons(self, aValues):
        """Get the icons for the clans"""
        dIcons = {}
        for oClan in aValues:
            sFileName = _get_clan_filename(oClan)
            dIcons[oClan.name] = self._get_icon(sFileName)
        return dIcons

    def _get_card_type_icons(self, aValues):
        """Get the icons for the card types"""
        dIcons = {}
        for oType in aValues:
            sFileName = _get_card_type_filename(oType)
            dIcons[oType.name] = self._get_icon(sFileName)
        return dIcons

    def _get_creed_icons(self, aValues):
        """Get the icons for the creeds."""
        dIcons = {}
        for oCreed in aValues:
            sFileName = _get_creed_filename(oCreed)
            dIcons[oCreed.name] = self._get_icon(sFileName)
        return dIcons

    def _get_discipline_icons(self, aValues):
        """Get the icons for the disciplines."""
        dIcons = {}
        for oDiscipline in aValues:
            sFileName = _get_discipline_filename(oDiscipline)
            if oDiscipline.level == 'superior':
                oIcon = self._get_icon(sFileName, 14)
            else:
                oIcon = self._get_icon(sFileName)
            dIcons[oDiscipline.discipline.name] = oIcon
        return dIcons

    def _get_virtue_icons(self, aValues):
        """Get the icons for the Virtues."""
        dIcons = {}
        for oVirtue in aValues:
            sFileName = _get_virtue_filename(oVirtue)
            dIcons[oVirtue.name] = self._get_icon(sFileName)
        return dIcons

    def get_icon_by_name(self, sName):
        """Lookup an icon that's a card property"""
        if sName == 'burn option':
            sFileName = 'misc/iconmiscburnoption.gif'
        elif sName == 'advanced':
            sFileName = 'misc/iconmiscadvanced.gif'
        return self._get_icon(sFileName)

    def get_info(self, sText, cGrouping):
        """Given the text and the grouping for a card list/set view,
           return the appropriate text array and icons for display."""
        if not sText:
            return [], []
        aText = []
        aIcons = []
        if cGrouping is Groupings.CardTypeGrouping:
            aText = [sText]
            dIcons = self._get_card_type_icons([ICardType(x) for x in aText])
            # Only 1 icon
            aIcons = dIcons.values()
        elif cGrouping is Groupings.MultiTypeGrouping:
            aText = sText.split(' / ')
            dIcons = self._get_card_type_icons([ICardType(x) for x in aText])
            # Do this since we need to have the same order as aText
            aIcons = [dIcons[x] for x in aText]
            aText = " /|".join(aText).split("|")
        elif cGrouping is Groupings.DisciplineGrouping:
            aText = [sText]
            try:
                oDisVirt = IDisciplinePair((sText, 'superior'))
                dIcons = self._get_discipline_icons([oDisVirt])
                # We know there's only 1 icon, so this is OK
                aIcons = dIcons.values()
            except KeyError:
                try:
                    oDisVirt = IVirtue(sText)
                    dIcons = self._get_virtue_icons([oDisVirt])
                    aIcons = dIcons.values()
                except KeyError:
                    aIcons = [None]
        elif cGrouping is Groupings.ClanGrouping:
            aText = [sText]
            try:
                oClanCreed = IClan(sText)
                dIcons = self._get_clan_icons([oClanCreed])
                # We know there's only 1 icon, so this is OK
                aIcons = dIcons.values()
            except KeyError:
                try:
                    oClanCreed = ICreed(sText)
                    dIcons = self._get_creed_icons([oClanCreed])
                    aIcons = dIcons.values()
                except KeyError:
                    aIcons = [None]
        return aText, aIcons

    def get_icon_list(self, aValues):
        """Get a list of appropriate icons for the given values"""
        if not aValues:
            return None
        aIcons = None
        if isinstance(aValues[0], CardType):
            aIcons = self._get_card_type_icons(aValues)
        elif isinstance(aValues[0], DisciplinePair):
            aIcons = self._get_discipline_icons(aValues)
        elif isinstance(aValues[0], Virtue):
            aIcons = self._get_virtue_icons(aValues)
        elif isinstance(aValues[0], Clan):
            aIcons = self._get_clan_icons(aValues)
        elif isinstance(aValues[0], Creed):
            aIcons = self._get_creed_icons(aValues)
        return aIcons

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
            self.download_icons()
        else:
            # Let the user know about the other options
            do_complaint("Icon download skipped.\nYou can choose to download "
                    "the icons from the File menu.\nYou will not be prompted "
                    "again unless you delete %s" % self._sPrefsDir,
                    gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, False)

    def download_icons(self):
        """Download the icons from the WW site"""
        def download(sFileName, oLogger):
            """Download the icon and save it in the icons directory"""
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
                fOut = file(sFullFilename, 'wb')
                fOut.write(oUrl.read())
                fOut.close()
            except HTTPError, oErr:
                print 'Unable to download %s: Error %s' % (sUrl, oErr)
            oLogger.info('Processed %s' % sFileName)
        # We use the names as from the WW site - this is not
        # ideal, but simpler than maintaining multiple names for each
        # icon.
        self._dIconCache = {}  # Cache is invalidated by this
        ensure_dir_exists(self._sPrefsDir)
        oLogHandler = SutekhCountLogHandler()
        oProgressDialog = ProgressDialog()
        oProgressDialog.set_description("Downloading icons")
        oLogHandler.set_dialog(oProgressDialog)
        oProgressDialog.show()
        oLogHandler.set_total(Creed.select().count() +
                DisciplinePair.select().count() + Clan.select().count() +
                Virtue.select().count() + CardType.select().count() + 2)
        oLogger = Logger('Download Icons')
        oLogger.addHandler(oLogHandler)
        for oCreed in Creed.select():
            download(_get_creed_filename(oCreed), oLogger)
        for oDiscipline in DisciplinePair.select():
            download(_get_discipline_filename(oDiscipline), oLogger)
        for oClan in Clan.select():
            download(_get_clan_filename(oClan), oLogger)
        for oVirtue in Virtue.select():
            download(_get_virtue_filename(oVirtue), oLogger)
        for oType in CardType.select():
            download(_get_card_type_filename(oType), oLogger)
        # download the special cases
        download('misc/iconmiscburnoption.gif', oLogger)
        download('misc/iconmiscadvanced.gif', oLogger)
        oProgressDialog.destroy()
