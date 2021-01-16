# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Adds a frame which will display card images from ARDB in the GUI"""

import datetime
import os
import logging

from gi.repository import Gtk

from sqlobject import SQLObjectNotFound

from sutekh.base.core.BaseAdapters import IExpansion, IPrinting
from sutekh.base.gui.SutekhDialog import do_complaint_error
from sutekh.base.Utility import ensure_dir_exists, to_ascii
from sutekh.base.gui.plugins.BaseImages import (BaseImageFrame,
                                                BaseImageConfigDialog,
                                                BaseImagePlugin,
                                                check_file,
                                                CARD_IMAGE_PATH,
                                                DOWNLOAD_IMAGES,
                                                DOWNLOAD_EXPANSIONS)

from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.SutekhInfo import SutekhInfo

# Base url for downloading the images from
SUTEKH_IMAGE_SITE = 'https://sutekh.vtes.za.net'
IMAGE_DATE_FILE = "image_dates.txt"

SUTEKH_USER_AGENT = {
    'User-Agent': 'Sutekh Image Plugin'
}


class CardImageFrame(BaseImageFrame):
    # pylint: disable=too-many-public-methods, too-many-instance-attributes
    # can't not trigger these warning with pyGtk
    # we need to keep quite a lot of internal state
    """Frame which displays the image.

       Adds the VtES specific handling.
       """

    APP_NAME = SutekhInfo.NAME

    # Special cases where we don't want to use the Promo short name
    SPECIAL_EXPANSIONS = [
        "Anarchs and Alastors Storyline",
    ]

    # Cloudflare doesn't like the urllib2 default
    _dReqHeaders = SUTEKH_USER_AGENT

    def _have_expansions(self, sTestPath=''):
        """Test if directory contains expansion/image structure used by ARDB"""
        # Config, if set to download, overrides the current state
        oConfig = self._config_download_expansions()
        if oConfig is not None:
            return oConfig
        # Config isn't set for downloads, so check the current state
        if sTestPath == '':
            sTestFile = os.path.join(self._sPrefsPath, 'bh', 'acrobatics.jpg')
        else:
            sTestFile = os.path.join(sTestPath, 'bh', 'acrobatics.jpg')
        return check_file(sTestFile)

    def _check_test_file(self, sTestPath=''):
        """Test if acrobatics.jpg exists"""
        # If we're configured to download images, we assume everythings
        # kosher, since we check that the directory exists when configuring
        # things
        if self._config_download_images():
            return True
        # Downloads not set, so the state on disk matters
        if sTestPath == '':
            sTestFile = os.path.join(self._sPrefsPath, 'acrobatics.jpg')
        else:
            sTestFile = os.path.join(sTestPath, 'acrobatics.jpg')
        return check_file(sTestFile)

    def _convert_expansion(self, sExpansionName):
        """Convert the Full Expansion name into the abbreviation needed."""
        if sExpansionName == '':
            return ''
        bOK = False
        # pylint: disable=no-member
        # pylint doesn't pick up IExpansion methods correctly
        try:
            oExpansion = IExpansion(sExpansionName)
            oPrinting = None
            bOK = True
        except SQLObjectNotFound:
            if '(' in sExpansionName:
                # Maybe a Printing?
                sSplitExp, sPrintName = [x.strip() for x in
                                         sExpansionName.split('(', 1)]
                sPrintName = sPrintName.replace(')', '')
                try:
                    oExpansion = IExpansion(sSplitExp)
                    oPrinting = IPrinting((oExpansion, sPrintName))
                    bOK = True
                except SQLObjectNotFound:
                    pass
        if not bOK:
            # This can happen because we cache the expansion name and
            # a new database import may cause that to vanish.
            # We return just return a blank path segment, as the safest choice
            logging.warning('Expansion %s no longer found in the database',
                            sExpansionName)
            return ''
        # check special cases
        # Promos always get the full name, so we can find the right image
        # for cards printed in multiple different promo sets
        if oExpansion.name in self.SPECIAL_EXPANSIONS or \
                oExpansion.name.startswith('Promo'):
            sExpName = oExpansion.name.lower()
        else:
            sExpName = oExpansion.shortname.lower()
        if oPrinting:
            sExpName += '_' + oPrinting.name.lower()
        # Normalise storyline cards
        sExpName = sExpName.replace(' ', '_').replace('-', '_')
        # Strip quotes as well
        sExpName = sExpName.replace("'", '')
        return sExpName

    def _make_card_urls(self, _sFullFilename):
        """Return a url pointing to the scan of the image"""
        sFilename = self._norm_cardname(self._sCardName)[0]
        if sFilename == '':
            # Error out - we don't know where to look
            return None
        if self._bShowExpansions:
            # Only try download the current expansion
            aUrlExps = [self._convert_expansion(self._sCurExpPrint)]
        else:
            # Try all the expansions, latest to oldest
            aUrlExps = [self._convert_expansion(x) for x in self._aExpPrints]
        aUrls = []
        for sCurExpansionPath in aUrlExps:
            if sCurExpansionPath == '':
                # Error path, we don't know where to search for the image
                return None
            sUrl = '%s/cardimages/%s/%s' % (SUTEKH_IMAGE_SITE,
                                            sCurExpansionPath,
                                            sFilename)
            aUrls.append(sUrl)
        return aUrls

    def _make_date_url(self):
        """Date info file lives with the images"""
        return '%s/cardimages/%s' % (SUTEKH_IMAGE_SITE, IMAGE_DATE_FILE)

    def _parse_date_data(self, sDateData):
        """Parse date file into entries"""
        # pylint: disable=broad-except
        # We do want to catch all errors here, so we log failures
        # correctly.
        try:
            self._dDateCache = {}
            for sLine in sDateData.splitlines():
                sLine = sLine.strip()
                if not sLine:
                    continue
                # We are dealing with ls-lR type formatting
                # size YYYY-mm-DD HH:MM:SS ./<dir>/<name>
                _sSize, sDay, sTime, sName = sLine.split()
                oCacheDate = datetime.datetime.strptime(
                    "%s %s" % (sDay, sTime), "%Y-%m-%d %H:%M:%S")
                sExpansion, sCardName = sName.replace('./', '').split('/')
                sKey = os.path.join(self._sPrefsPath, sExpansion, sCardName)
                self._dDateCache[sKey] = oCacheDate
            if len(self._dDateCache) > 100:
                return True
        except Exception as oErr:
            logging.warning('Error parsing date cache file %s', oErr)
        return False

    def _norm_cardname(self, sCardName):
        """Normalise the card name"""
        # Some symbols are converted to uppercase, so fix that
        sFilename = to_ascii(sCardName).lower()
        if sFilename.startswith('the '):
            sFilename = sFilename[4:] + 'the'
        elif sFilename.startswith('an '):
            sFilename = sFilename[3:] + 'an'
        sFilename = sFilename.replace('(advanced)', 'adv')
        # Should probably do this via translate
        for sChar in (" ", ".", ",", "'", "(", ")", "-", ":", "!", '"', "/"):
            sFilename = sFilename.replace(sChar, '')
        sFilename = sFilename + '.jpg'
        return [sFilename]


class ImageConfigDialog(BaseImageConfigDialog):
    # pylint: disable=too-many-public-methods
    # Gtk Widget, so has many public methods
    """Dialog for configuring the Image plugin."""

    sImgDownloadSite = 'sutekh.vtes.za.net'

    dDownloadUrls = {
       'Download zipfile from sutekh.vtes.za.net (images for each expansions)':
            '%s/zipped/%s' % (SUTEKH_IMAGE_SITE, 'cardimages.zip'),
       'Download zipfile from sutekh.vtes.za.net (only 1 image per card - no expansions)':
            '%s/zipped/%s' % (SUTEKH_IMAGE_SITE, 'cardimages_single.zip'),
    }

    def __init__(self, oImagePlugin, bFirstTime=False, bDownloadUpgrade=False):
        super().__init__(oImagePlugin, bFirstTime)
        # This is a bit horrible, but we stick the download upgrade logic
        # here, rather than cluttering up the generic ConfigDialog with
        # this entirely Sutekh specific logic
        self.oChoice.set_request_headers(SUTEKH_USER_AGENT)
        if bDownloadUpgrade:
            # pylint: disable=no-member
            # pylint doesn't pick up vbox methods correctly
            # Clear the dialog vbox and start again
            self.vbox.remove(self.oDescLabel)
            self.vbox.remove(self.oChoice)
            self.vbox.remove(self.oDownload)
            self.vbox.remove(self.oDownloadExpansions)
            self.oDescLabel.set_markup('<b>Choose how to configure the '
                                       'cardimages plugin</b>\n'
                                       'The card images plugin can now '
                                       'download missing images from '
                                       'sutekh.vtes.za.net.\nDo you wish to '
                                       'enable this (you will not be prompted '
                                       'again)?')
            self.vbox.pack_start(self.oDescLabel, False, False, 0)
            self.vbox.pack_start(self.oDownload, False, False, 0)
            self.vbox.pack_start(self.oDownloadExpansions, False, False, 0)
            self.set_size_request(400, 200)
            self.show_all()


class CardImagePlugin(SutekhPlugin, BaseImagePlugin):
    """Plugin providing access to CardImageFrame."""

    DOWNLOAD_SUPPORTED = True

    _cImageFrame = CardImageFrame

    @classmethod
    def update_config(cls):
        super().update_config()
        # We default to download expansions is true, since that matches
        # the zip file we provide from sutekh.vtes.za.net
        cls.dGlobalConfig[DOWNLOAD_EXPANSIONS] = 'boolean(default=True)'

    def setup(self):
        """Prompt the user to download/setup images the first time"""
        sPrefsPath = self.get_config_item(CARD_IMAGE_PATH)
        if not os.path.exists(sPrefsPath):
            # Looks like the first time
            oDialog = ImageConfigDialog(self, True, False)
            self.handle_response(oDialog)
            # Path may have been changed, so we need to requery config file
            sPrefsPath = self.get_config_item(CARD_IMAGE_PATH)
            # Don't get called next time
            ensure_dir_exists(sPrefsPath)
        else:
            oDownloadImages = self.get_config_item(DOWNLOAD_IMAGES)
            if oDownloadImages is None:
                # Doesn't look like we've asked this question
                oDialog = ImageConfigDialog(self, False, True)
                # Default to false
                self.set_config_item(DOWNLOAD_IMAGES, False)
                self.handle_response(oDialog)

    def config_activate(self, _oMenuWidget):
        """Configure the plugin dialog."""
        oDialog = ImageConfigDialog(self, False, False)
        self.handle_response(oDialog)

    def handle_response(self, oDialog):
        """Handle the response from the config dialog"""
        iResponse = oDialog.run()
        if iResponse == Gtk.ResponseType.OK:
            oFile, bDir, bDownload, bDownloadExpansions = oDialog.get_data()
            if bDir:
                # New directory
                if self._accept_path(oFile):
                    # Update preferences
                    self.image_frame.update_config_path(oFile)
                    self._activate_menu()
            elif oFile:
                if self._unzip_file(oFile):
                    self._activate_menu()
                else:
                    do_complaint_error('Unable to successfully unzip data')
                oFile.close()  # clean up temp file
            else:
                # Unable to get data
                do_complaint_error('Unable to configure card images plugin')
            # Update download option
            self.set_config_item(DOWNLOAD_IMAGES, bDownload)
            self.set_config_item(DOWNLOAD_EXPANSIONS, bDownloadExpansions)
            # Reset expansions settings if needed
            self.image_frame.check_images()
        # get rid of the dialog
        oDialog.destroy()


plugin = CardImagePlugin
