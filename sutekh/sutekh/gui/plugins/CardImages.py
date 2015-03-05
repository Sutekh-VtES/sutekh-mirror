# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Adds a frame which will display card images from ARDB in the GUI"""

import gtk
import os
import logging
from sqlobject import SQLObjectNotFound
from sutekh.base.core.BaseObjects import IExpansion
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.SutekhInfo import SutekhInfo
from sutekh.base.gui.SutekhDialog import do_complaint_error
from sutekh.base.Utility import ensure_dir_exists
from sutekh.base.gui.plugins.BaseImages import (BaseImageFrame,
                                                BaseImageConfigDialog,
                                                BaseImagePlugin,
                                                check_file, unaccent,
                                                CARD_IMAGE_PATH,
                                                DOWNLOAD_IMAGES)


# We try lackeyccg for images from these sets
LACKEY_IMAGES = ('dm', 'vekn_2014_the_returned', 'tu')


class CardImageFrame(BaseImageFrame):
    # pylint: disable=R0904, R0902
    # R0904 - can't not trigger these warning with pygtk
    # R0902 - we need to keep quite a lot of internal state
    """Frame which displays the image.

       Adds the VtES specific handling.
       """

    APP_NAME = SutekhInfo.NAME

    def _have_expansions(self, sTestPath=''):
        """Test if directory contains expansion/image structure used by ARDB"""
        if sTestPath == '':
            sTestFile = os.path.join(self._sPrefsPath, 'bh', 'acrobatics.jpg')
        else:
            sTestFile = os.path.join(sTestPath, 'bh', 'acrobatics.jpg')
        return check_file(sTestFile)

    def _check_test_file(self, sTestPath=''):
        """Test if acrobatics.jpg exists"""
        if sTestPath == '':
            sTestFile = os.path.join(self._sPrefsPath, 'acrobatics.jpg')
        else:
            sTestFile = os.path.join(sTestPath, 'acrobatics.jpg')
        return check_file(sTestFile)

    def _convert_expansion(self, sExpansionName):
        """Convert the Full Expansion name into the abbreviation needed."""
        if sExpansionName == '' or not self._bShowExpansions:
            return ''
        # pylint: disable=E1101
        # pylint doesn't pick up IExpansion methods correctly
        try:
            oExpansion = IExpansion(sExpansionName)
        except SQLObjectNotFound:
            # This can happen because we cache the expansion name and
            # a new database import may cause that to vanish.
            # We return just return a blank path segment, as the safest choice
            logging.warn('Expansion %s no longer found in the database',
                         sExpansionName)
            return ''
        # special case Anarchs and alastors due to promo hack shortname
        if oExpansion.name == 'Anarchs and Alastors Storyline':
            sExpName = oExpansion.name.lower()
        else:
            sExpName = oExpansion.shortname.lower()
        # Normalise for storyline cards
        sExpName = sExpName.replace(' ', '_').replace("'", '')
        return sExpName

    def _make_card_urls(self):
        """Return a url pointing to the vtes.pl scan of the image"""
        sCurExpansionPath = self._convert_expansion(self._sCurExpansion)
        sFilename = self._norm_cardname()
        if sCurExpansionPath == '' or sFilename == '':
            # Error path, we don't know where to search for the image
            return ''
        # Remap paths to point to the vtes.pl equivilents
        if sCurExpansionPath == 'nergal_storyline':
            sCurExpansionPath = 'isl'
        elif sCurExpansionPath == 'anarchs_and_alastors_storyline':
            sCurExpansionPath = 'aa'
        elif sCurExpansionPath == 'edens_legacy_storyline':
            sCurExpansionPath = 'el'
        elif sCurExpansionPath == 'cultist_storyline':
            sCurExpansionPath = 'csl'
        elif sCurExpansionPath == 'white_wolf_2003_demo':
            sCurExpansionPath = 'dd'
        elif sCurExpansionPath == 'third':
            sCurExpansionPath = '3e'
        sUrl = 'http://nekhomanta.h2.pl/pics/games/vtes/%s/%s' % (
            sCurExpansionPath, sFilename)
        if sCurExpansionPath in LACKEY_IMAGES:
            # Try get the card from lackey first
            # Strip the "(Mythic storyline)" prefix from the returned cards
            if sCurExpansionPath == 'vekn_2014_the_returned':
                # Lackey uses 'montaro2' and so forth for the duplicate names
                # between the 2015 storyline rewards expansion and the actual
                # storyline cards, but this only applies to some of the card
                # names, so we need to try all possibilities in the right
                # order
                sFilename = sFilename.replace('mythicstoryline', '')
                sFilename2 = sFilename.replace('.jpg', '2.jpg')
            sLackeyUrl = 'http://www.lackeyccg.com/vtes/high/cards/%s' % (
                sFilename)
            sLackeyUrl2 = 'http://www.lackeyccg.com/vtes/high/cards/%s' % (
                sFilename2)
            return (sLackeyUrl2, sLackeyUrl, sUrl)
        return (sUrl, )

    def _norm_cardname(self):
        """Normalise the card name"""
        sFilename = unaccent(self._sCardName)
        if sFilename.startswith('the '):
            sFilename = sFilename[4:] + 'the'
        elif sFilename.startswith('an '):
            sFilename = sFilename[3:] + 'an'
        sFilename = sFilename.replace('(advanced)', 'adv')
        # Should probably do this via translate
        for sChar in (" ", ".", ",", "'", "(", ")", "-", ":", "!", '"', "/"):
            sFilename = sFilename.replace(sChar, '')
        sFilename = sFilename + '.jpg'
        return sFilename


class ImageConfigDialog(BaseImageConfigDialog):
    # pylint: disable=R0904
    # R0904 - gtk Widget, so has many public methods
    """Dialog for configuring the Image plugin."""

    sDefURLId = 'csillagbolcselet.hu'
    sDefaultUrl = 'http://csillagmag.hu/upload/pictures.zip'
    sImgDownloadSite = 'vtes.pl'

    def __init__(self, oImagePlugin, bFirstTime=False, bDownloadUpgrade=False):
        super(ImageConfigDialog, self).__init__(oImagePlugin, bFirstTime)
        # This is a bit horrible, but we stick the download upgrade logic
        # here, rather than cluttering up the generic ConfigDialog with
        # this entirely Sutekh specific logic
        if bDownloadUpgrade:
            # pylint: disable=E1101
            # pylint doesn't pick up vbox methods correctly
            # Clear the dialog vbox and start again
            self.vbox.remove(self.oDescLabel)
            self.vbox.remove(self.oChoice)
            self.vbox.remove(self.oDownload)
            self.oDescLabel.set_markup('<b>Choose how to configure the '
                                       'cardimages plugin</b>\n'
                                       'The card images plugin can now '
                                       'download missing images from '
                                       'vtes.pl.\nDo you wish to enable '
                                       'this (you will not be prompted '
                                       'again)?')
            self.vbox.pack_start(self.oDescLabel, False, False)
            self.vbox.pack_start(self.oDownload, False, False)
            self.set_size_request(400, 200)
            self.show_all()


class CardImagePlugin(SutekhPlugin, BaseImagePlugin):
    """Plugin providing access to CardImageFrame."""

    DOWNLOAD_SUPPORTED = True

    _cImageFrame = CardImageFrame

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
        if iResponse == gtk.RESPONSE_OK:
            oFile, bDir, bDownload = oDialog.get_data()
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
        # get rid of the dialog
        oDialog.destroy()


plugin = CardImagePlugin
