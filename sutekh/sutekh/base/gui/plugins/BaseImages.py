# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Adds a frame which will display card images from ARDB in the GUI"""

import datetime
import enum
import logging
import os
import tempfile
from urllib.error import HTTPError
import zipfile

from gi.repository import Gdk, GdkPixbuf, GObject, Gtk

from ...core.BaseTables import PhysicalCard
from ...core.BaseAdapters import IPrintingName

from ...io.UrlOps import urlopen_with_timeout

from ...Utility import prefs_dir, ensure_dir_exists, get_printing_date

from ..BasePluginManager import BasePlugin
from ..ProgressDialog import ProgressDialog, SutekhCountLogHandler
from ..MessageBus import MessageBus
from ..GuiDataPack import progress_fetch_data, gui_error_handler
from ..BasicFrame import BasicFrame
from ..SutekhDialog import (SutekhDialog, do_complaint_buttons,
                            do_complaint_error)
from ..AutoScrolledWindow import AutoScrolledWindow
from ..FileOrUrlWidget import FileOrDirOrUrlWidget
from ..SutekhFileWidget import add_filter


@enum.unique
class Direction(enum.Enum):
    """Options to cycle through the images"""
    FORWARD = 1
    BACKWARD = 2


@enum.unique
class Size(enum.Enum):
    """Different resize options we support"""
    FULL = 1
    VIEW_FIXED = 2
    FIT = 3


RATIO = (225, 300)

# Config Key Constants
DOWNLOAD_IMAGES = 'download images'
CARD_IMAGE_PATH = 'card image path'
DOWNLOAD_EXPANSIONS = 'download expansion images'
LAST_DOWNLOADED = 'last downloaded'


def _scale_dims(iImageWidth, iImageHeight, iPaneWidth, iPaneHeight):
    """Rescale the image dimension so they fit in the pane, preserving the
       aspect ratiom."""
    fImageAspectRatio = float(iImageHeight) / float(iImageWidth)
    fPaneAspectRatio = float(iPaneHeight) / float(iPaneWidth)

    if fPaneAspectRatio > fImageAspectRatio:
        # wider
        fDestWidth = iPaneWidth
        fDestHeight = iPaneWidth * fImageAspectRatio
    else:
        fDestHeight = iPaneHeight
        fDestWidth = iPaneHeight / fImageAspectRatio
    return int(fDestWidth), int(fDestHeight)


def check_file(sFileName):
    """Check if file exists and is readable"""
    bRes = True
    try:
        fTest = open(sFileName, 'rb')
        fTest.close()
    except IOError:
        bRes = False
    return bRes


def image_gui_error_handler(oExp):
    """We filter out 404 not found so we don't loop endlessly on
       card images that aren't available"""
    if isinstance(oExp, HTTPError) and oExp.code == 404:
        return
    gui_error_handler(oExp)


def get_printing_info(oAbsCard):
    """Set the expansion info."""
    bHasInfo = len(oAbsCard.rarity) > 0
    # We opt to sort undated expansions as newer than expansions with dates
    # as likely more correct when dealing with new sets. When no expansions
    # have dates, this is the right thing
    oToday = datetime.date.today()

    def get_date(oDate):
        """Handle None values for date somewhat sanely"""
        return oDate if oDate else oToday

    if bHasInfo:
        aPrint = set()
        # We want only those printings that actually apply to this card
        for oCard in oAbsCard.physicalCards:
            oPrint = oCard.printing
            if oPrint:
                # We want the newest image, but, for identical dates,
                # we want the "Non-Printing" image if there are multiple
                # printings, so we sort by negative ordinal to get the date
                # ordering and rely on string matching to sort the printings
                # as we want to, beacause of how IPrintingName works
                aPrint.add((-get_date(get_printing_date(oPrint)).toordinal(),
                            IPrintingName(oPrint)))
        # Sort by date, newest first
        aPrintings = [x[1] for x in sorted(aPrint)]
        return aPrintings
    return []


class CardImagePopupMenu(Gtk.Menu):
    # pylint: disable=too-many-public-methods
    # can't not trigger these warning with pyGtk
    """Popup menu for the Card Image Frame"""

    def __init__(self, oFrame, iZoomMode):
        super().__init__()
        self.oFrame = oFrame
        self.oZoom = Gtk.RadioMenuItem(group=None,
                                       label='Show images at original size')
        self.oViewFixed = Gtk.RadioMenuItem(group=self.oZoom,
                                            label='Show images at fixed size')
        self.oViewFit = Gtk.RadioMenuItem(group=self.oZoom,
                                          label='Fit images to the pane')
        self.oNext = Gtk.MenuItem(label='Show next expansion image')
        self.oPrev = Gtk.MenuItem(label='Show previous expansion image')

        self.oPrev.connect('activate', self.cycle_expansion,
                           Direction.BACKWARD)
        self.oNext.connect('activate', self.cycle_expansion,
                           Direction.FORWARD)
        self.oViewFit.connect('activate', self.set_zoom, Size.FIT)
        self.oZoom.connect('activate', self.set_zoom, Size.FULL)
        self.oViewFixed.connect('activate', self.set_zoom, Size.VIEW_FIXED)

        if iZoomMode == Size.FULL:
            self.oZoom.set_active(True)
        elif iZoomMode == Size.VIEW_FIXED:
            self.oViewFixed.set_active(True)
        elif iZoomMode == Size.FIT:
            self.oViewFit.set_active(True)

        self.add(self.oViewFit)
        self.add(self.oViewFixed)
        self.add(self.oZoom)
        self.add(self.oNext)
        self.add(self.oPrev)
        self.show_all()

    def set_show_expansion_state(self, bValue):
        """Grey out the expansion menus if needed"""
        self.oNext.set_sensitive(bValue)
        self.oPrev.set_sensitive(bValue)

    def cycle_expansion(self, _oWidget, iDir):
        """Change the expansion as requested."""
        assert(iDir in Direction)
        self.oFrame.do_cycle_expansion(iDir)

    def set_zoom(self, _oWidget, iScale):
        """Change the drawing mode."""
        assert(iScale in Size)
        self.oFrame.set_zoom_mode(iScale)


class BaseImageFrame(BasicFrame):
    # pylint: disable=too-many-instance-attributes, too-many-public-methods
    # we need to keep quite a lot of internal state
    # can't not trigger these warning with pyGtk
    """Frame which displays the image.

       We wrap a Gtk.Image in an EventBox (for focus & DnD events)
       and a Viewport (for scrolling)
       """

    sMenuFlag = 'Card Image Frame'

    # Subclasses should override this
    APP_NAME = 'Deck Builder'

    # If fancy header manipulation is needed, set this
    _dReqHeaders = {}

    def __init__(self, oImagePlugin):
        super().__init__(oImagePlugin.parent)
        self._oImagePlugin = oImagePlugin
        oVBox = Gtk.VBox(homogeneous=False, spacing=2)
        oBox = Gtk.EventBox()
        self.oExpPrintLabel = Gtk.Label()
        oVBox.pack_start(self.oExpPrintLabel, False, False, 0)
        oVBox.pack_start(oBox, False, False, 0)
        self._oView = AutoScrolledWindow(oVBox)
        self._oView.get_hadjustment().connect('changed', self._pane_adjust)
        self._oView.get_vadjustment().connect('changed', self._pane_adjust)
        self._oImage = Gtk.Image()
        self._oImage.set_from_icon_name("image-missing",
                                        Gtk.IconSize.DIALOG)
        oBox.add(self._oImage)

        # Enable DnD handling, same as for BasicFrame
        self.set_drag_handler(oBox)
        self.set_drop_handler(oBox)
        oBox.connect('button-press-event', self._cycle_expansion)
        oBox.connect('popup-menu', self._handle_popup_menu)

        self._sPrefsPath = self._oImagePlugin.get_config_item(
            CARD_IMAGE_PATH)
        if self._sPrefsPath is None:
            self._sPrefsPath = os.path.join(prefs_dir(self.APP_NAME),
                                            'cardimages')
            self._oImagePlugin.set_config_item(CARD_IMAGE_PATH,
                                               self._sPrefsPath)
        self._bShowExpansions = self._have_expansions()
        self._sCurExpPrint = ''
        self._aExpPrints = []
        self._iExpansionPos = 0
        self._sCardName = ''
        self._iZoomMode = Size.FIT
        self._tPaneSize = (0, 0)
        self._dFailedUrls = {}
        self._dDateCache = {}

    type = property(fget=lambda self: "Card Image Frame", doc="Frame Type")


    def _find_missing_outdated_images(self):
        """Find all the cards that are missing from the filesystem.

           Used for download helpers or missing image checks and
           so on."""
        dMissing = {}
        dOutdated = {}
        # Download date check if needed
        self._get_date_data()
        for oCard in PhysicalCard.select():
            if oCard.printing:
                # We're only interested in cards with expansion info,
                # as the "No expansion" case is a subset of those
                aNames = self.lookup_filename(oCard)
                for sName in aNames:
                    if not check_file(sName):
                        dMissing.setdefault(oCard, [])
                        dMissing[oCard].append(sName)
                    elif self._check_outdated(sName):
                        dOutdated.setdefault(oCard, [])
                        dOutdated[oCard].append(sName)
        return dMissing, dOutdated

    def check_for_all_cards(self):
        """Print details of missing card images.

           This is a helper method used to ensure that files are placed
           and named as expected. It generally shouldn't be called
           in general usage.
           """
        dMissing, dOutdated = self._find_missing_outdated_images()
        print('Card Images checks')
        print('%d missing images, %d outdated images' %
              (len(dMissing), len(dOutdated)))
        print()
        for oCard in sorted(dMissing, key=lambda x: x.abstractCard.name):
            print("Missing images for %s (%s)" % (oCard.abstractCard.name,
                                                  IPrintingName(oCard)))
            for sName in dMissing[oCard]:
                print("    %s   not found" % sName)
        print()
        for oCard in sorted(dOutdated, key=lambda x: x.abstractCard.name):
            print("Outdated images for %s (%s)" % (oCard.abstractCard.name,
                                                   IPrintingName(oCard)))
            for sName in dOutdated[oCard]:
                print("    %s   is out of date" % sName)

    def count_missing_outdated_images(self):
        """Count how many images are missing / not downloaded"""
        dMissing, dOutdated = self._find_missing_outdated_images()
        return len(dMissing), len(dOutdated)

    def _download_dict(self, dImages, oLogger):
        """Download the images in the given dict"""
        sCurName, sCurPrint = self._sCardName, self._sCurExpPrint
        for oCard, aToGrab in dImages.items():
            for sName in aToGrab:
                # make_urls may require card info, so we set it
                self._sCardName = oCard.abstractCard.canonicalName
                self._sCurExpPrint = IPrintingName(oCard)
                # This pops up another progress dialog, but that
                # is OK
                self._download_image(sName)
                # Update the image list progress bar
                oLogger.info('image download attempted')
        self._sCardName, self._sCurExpPrint = sCurName, sCurPrint

    def download_all_missing_outdated_images(self):
        """Download all images that are missing from the filesystem."""
        dMissing, dOutdated = self._find_missing_outdated_images()
        if not dMissing and not dOutdated:
            return
        oProgress = ProgressDialog()
        sCurName, sCurPrint = self._sCardName, self._sCurExpPrint
        try:
            oLogHandler = SutekhCountLogHandler()
            oLogHandler.set_dialog(oProgress)
            oLogHandler.set_total(len(dMissing) + len(dOutdated))
            oLogger = logging.Logger('Sutekh card image fetcher')
            oLogger.addHandler(oLogHandler)
            oProgress.set_description("Downloading missing or outdated images")
            self._download_dict(dMissing, oLogger)
            self._download_dict(dOutdated, oLogger)
        finally:
            self._sCardName, self._sCurExpPrint = sCurName, sCurPrint
            oProgress.destroy()

    def frame_setup(self):
        """Subscribe to the set_card_text signal"""
        # Reset to stock image to force sane state
        self._oImage.set_from_icon_name("image-missing",
                                        Gtk.IconSize.DIALOG)
        MessageBus.subscribe(MessageBus.Type.CARD_TEXT_MSG, 'set_card_text',
                             self.set_card_text)
        super().frame_setup()

    def cleanup(self, bQuit=False):
        """Remove the listener"""
        MessageBus.unsubscribe(MessageBus.Type.CARD_TEXT_MSG, 'set_card_text',
                               self.set_card_text)
        super().cleanup(bQuit)

    def _config_download_images(self):
        """Check if we are configured to download images.

           Helper function to be used in sub-classes.
           If downloads are supported, return the
           the config option, otherwise return false."""
        if self._oImagePlugin.DOWNLOAD_SUPPORTED:
            return self._oImagePlugin.get_config_item(DOWNLOAD_IMAGES)
        return False

    def _config_download_expansions(self):
        """Check if we are configured to download expansions.

           Helper function to be used in sub-classes.
           Logic is that, if downloads are supported, take
           the config option, otherwise return None, to indicate that
           downloads aren't supported."""
        if (self._oImagePlugin.DOWNLOAD_SUPPORTED and
                self._oImagePlugin.get_config_item(DOWNLOAD_IMAGES)):
            return self._oImagePlugin.get_config_item(DOWNLOAD_EXPANSIONS)
        return None

    def _have_expansions(self, sTestPath=''):
        """Test if directory contains expansion/image subdirs"""
        raise NotImplementedError("Implement _have_expansions")

    def _check_test_file(self, sTestPath=''):
        """Test if images can be found in the non-expansion case"""
        raise NotImplementedError("Implement _check_test_file")

    def _convert_expansion(self, sExpansionName):
        """Convert the Full Expansion name into the abbreviation needed."""
        raise NotImplementedError("Implement _convert_expansion")

    def _set_expansion_info(self, oAbsCard):
        """Set the expansion info."""
        self._aExpPrints = get_printing_info(oAbsCard)
        self._iExpansionPos = 0
        if self._aExpPrints:
            self._sCurExpPrint = self._aExpPrints[0]
        else:
            self._sCurExpPrint = ''

    def _redraw(self, bPause):
        """Redraw the current card"""
        # If further events are pending, don't try and redraw
        if bPause and Gdk.events_pending():
            return
        if not self._sCardName:
            # Don't go down the rest of redraw path during startup
            return
        aFullFilenames = self._convert_cardname_to_path()
        self._load_image(aFullFilenames)

    def _make_card_urls(self, _sFullFilename):
        """Return a list of possible urls pointing to a scan of the image"""
        raise NotImplementedError("implement _make_card_urls")

    def _make_date_url(self):
        """Create the url for the image date cache info."""
        raise NotImplementedError("Implement _make_date_url")

    def _parse_date_data(self, sDateData):
        """Parse the date information from the file."""
        raise NotImplementedError("Implement _parse_date_data")

    def _get_date_data(self):
        """Get the date data from the website if available"""
        sDateUrl = self._make_date_url()
        if not sDateUrl:
            # No date info, so we skip this
            return
        oLastFetched = self._dDateCache.get(
            LAST_DOWNLOADED, datetime.datetime.utcfromtimestamp(0))
        if datetime.datetime.now() - oLastFetched < datetime.timedelta(days=1):
            # Cache fresh enough
            return
        logging.info('Downloading date cache from %s', sDateUrl)
        oFile = urlopen_with_timeout(
            sDateUrl, fErrorHandler=image_gui_error_handler,
            dHeaders=self._dReqHeaders, bBinary=False)
        if oFile:
            sDateData = progress_fetch_data(oFile)
            if self._parse_date_data(sDateData):
                self._dDateCache[LAST_DOWNLOADED] = datetime.datetime.now()
        else:
            logging.info("Failed to download date cache file")
            logging.info("Delaying next download attempt for 3 hours")
            # We don't want to spam the user with repeated failues, since this
            # may be a network issues, so we delay our next download attempt.
            # XXX: Should we have a dialog informing the user in addition
            # to the log message?
            self._dDateCache[LAST_DOWNLOADED] = \
                    datetime.datetime.now() - datetime.timedelta(hours=21)

    def _check_outdated(self, sFullFilename):
        """Check if the image we're displaying has a more recent version
           available to download."""
        # Entries not in the cache are automatically older than we are, so
        # we don't try download local files
        oCacheDate = self._dDateCache.get(
            sFullFilename, datetime.datetime.utcfromtimestamp(0))
        # We assume the cache dates are utc, so we convert to that
        oCurDate = datetime.datetime.utcfromtimestamp(
            os.path.getmtime(sFullFilename))
        # We allow some fuzz to add a bit of protection against weird
        # filesystems and timezone issues - this is probably too generous
        return oCacheDate - oCurDate > datetime.timedelta(seconds=60)

    def _download_if_outdated(self, sFullFilename):
        if self._check_outdated(sFullFilename):
            logging.info("Downloading newer image for %s", sFullFilename)
            self._download_image(sFullFilename)

    def _norm_cardname(self, sCardName):
        """Normalise the card name"""
        raise NotImplementedError("Implement norm_cardname")

    def _make_paths(self, sCardName, sExpansionPath):
        """Create the joined list of paths"""
        aFilenames = self._norm_cardname(sCardName)
        aFullFilenames = []
        for sFilename in aFilenames:
            aFullFilenames.append(os.path.join(self._sPrefsPath,
                                               sExpansionPath, sFilename))
        return aFullFilenames

    def _convert_cardname_to_path(self):
        """Convert sCardName to the form used by the card image list"""
        if not self._bShowExpansions:
            sCurExpansionPath = ''
        else:
            sCurExpansionPath = self._convert_expansion(self._sCurExpPrint)
        aFullFilenames = self._make_paths(self._sCardName, sCurExpansionPath)
        return aFullFilenames

    def lookup_filename(self, oPhysCard):
        """Return the list of possible filenames for use by other plugins"""
        sExpansionPath = ''
        sCardName = oPhysCard.abstractCard.canonicalName
        if self._bShowExpansions:
            # Only lookup expansions if we have expansion images
            if oPhysCard.printing:
                sExpPrintName = IPrintingName(oPhysCard)
            else:
                # No expansion, so find the latest expansion for this card
                aExpPrints = get_printing_info(oPhysCard.abstractCard)
                sExpPrintName = aExpPrints[0]
            sExpansionPath = self._convert_expansion(sExpPrintName)
        aFullFilenames = self._make_paths(sCardName, sExpansionPath)
        return aFullFilenames

    def _download_image(self, sFullFilename):
        """Attempt to download the image."""
        aUrls = self._make_card_urls(sFullFilename)
        if not aUrls:
            return False
        for sUrl in aUrls:
            if sUrl not in self._dFailedUrls:
                logging.info('Trying %s as source for %s',
                             sUrl, sFullFilename)
                oFile = urlopen_with_timeout(
                    sUrl, fErrorHandler=image_gui_error_handler,
                    dHeaders=self._dReqHeaders, bBinary=True)
            else:
                # Skip this url, since it's already failed
                oLastChecked = self._dFailedUrls[sUrl]
                if datetime.datetime.now() - oLastChecked > datetime.timedelta(hours=2):
                    # Will retry next time
                    logging.info('Removing %s from the failed cache', sUrl)
                    del self._dFailedUrls[sUrl]
                break
            if oFile:
                # Ensure the directory exists, for expansions we
                # haven't encountered before
                sBaseDir = os.path.dirname(sFullFilename)
                ensure_dir_exists(sBaseDir)
                # Create file
                # Attempt to fetch the data
                sImgData = progress_fetch_data(oFile)
                oFile.close()
                if sImgData:
                    oOutFile = open(sFullFilename, 'wb')
                    oOutFile.write(sImgData)
                    oOutFile.close()
                    logging.info('Using image data from %s', sUrl)
                    # We remove this from the url cache
                else:
                    logging.info('Invalid image data from %s', sUrl)
                    # Got bogus data, so don't retry for a while
                    self._dFailedUrls[sUrl] = datetime.datetime.now()
                # Don't attempt to follow other urls
                break
            else:
                # Cache failure
                self._dFailedUrls[sUrl] = datetime.datetime.now()
        return True

    def _load_image(self, aFullFilenames):
        """Load an image into the pane, show broken image if needed"""
        # pylint: disable=too-many-branches, too-many-locals, too-many-statements
        # This is has to handle a number of special cases
        # and subdividing it further won't help clarity
        self._oImage.set_alignment(0.5, 0.5)  # Centre image
        # Ensure we have an up to information about the image dates
        self._get_date_data()

        for sFullFilename in aFullFilenames:
            if not check_file(sFullFilename):
                if (self._oImagePlugin.DOWNLOAD_SUPPORTED and
                        self._oImagePlugin.get_config_item(DOWNLOAD_IMAGES)):
                    # Attempt to download the image from the url
                    if not self._download_image(sFullFilename):
                        # No download, so fall back to the 'no image' case
                        self._oImage.set_from_icon_name("image-missing",
                                                        Gtk.IconSize.DIALOG)
                        self._oImage.queue_draw()
                        return
            else:
                if (self._oImagePlugin.DOWNLOAD_SUPPORTED and
                        self._oImagePlugin.get_config_item(DOWNLOAD_IMAGES) and
                        self._download_if_outdated(sFullFilename)):
                    # Try download the image
                    # We don't handle failure specially here - if it fails,
                    # we will show the existing image
                    self._download_image(sFullFilename)
        try:
            if self._bShowExpansions:
                self.oExpPrintLabel.set_markup(
                    '<i>Image from expansion : </i> %s' % self._sCurExpPrint)
                self.oExpPrintLabel.show()
                iHeightOffset = self.oExpPrintLabel.get_allocation().height + 2
            else:
                self.oExpPrintLabel.hide()  # config changes can cause this
                iHeightOffset = 0
            aPixbufs = []
            iHeight = 0
            iWidth = 0
            for sFullFilename in aFullFilenames:
                oPixbuf = GdkPixbuf.Pixbuf.new_from_file(sFullFilename)
                iWidth = max(iWidth, oPixbuf.get_width())
                iHeight = max(iHeight, oPixbuf.get_height())
                aPixbufs.append(oPixbuf)
            if len(aPixbufs) > 1:
                # Create composite pixbuf
                oPixbuf = Gdk.Pixbuf(aPixbufs[0].get_colorspace(),
                                     aPixbufs[0].get_has_alpha(),
                                     aPixbufs[0].get_bits_per_sample(),
                                     (iWidth + 4) * len(aPixbufs) - 4,
                                     iHeight)
                oPixbuf.fill(0x00000000)  # fill with transparent black
                iPos = 0
                for oThisPixbuf in aPixbufs:
                    # Scale all images to the same size
                    oThisPixbuf.scale_simple(iWidth, iHeight,
                                             GdkPixbuf.InterpType.HYPER)
                    # Add to the composite pixbuf
                    oThisPixbuf.copy_area(0, 0, iWidth, iHeight,
                                          oPixbuf, iPos, 0)
                    iPos += iWidth + 4
                # Make iWidth the total width
                iWidth = (iWidth + 4) * len(aPixbufs) - 4
            else:
                oPixbuf = aPixbufs[0]
            if self._iZoomMode == Size.FIT:
                # Need to fix aspect ratios
                iPaneHeight = (self._oView.get_vadjustment().get_page_size() -
                               iHeightOffset)
                iPaneWidth = self._oView.get_hadjustment().get_page_size()
                # don't centre image under label
                self._oImage.set_alignment(0, 0.5)
                iDestWidth, iDestHeight = _scale_dims(iWidth, iHeight,
                                                      iPaneWidth, iPaneHeight)
                if iDestWidth > 0 and iDestHeight > 0:
                    self._oImage.set_from_pixbuf(
                        oPixbuf.scale_simple(iDestWidth, iDestHeight,
                                             GdkPixbuf.InterpType.HYPER))
                    self._tPaneSize = (
                        self._oView.get_hadjustment().get_page_size(),
                        self._oView.get_vadjustment().get_page_size())
            elif self._iZoomMode == Size.VIEW_FIXED:
                iDestWidth, iDestHeight = _scale_dims(iWidth, iHeight,
                                                      RATIO[0], RATIO[1])
                self._oImage.set_from_pixbuf(
                    oPixbuf.scale_simple(iDestWidth, iDestHeight,
                                         GdkPixbuf.InterpType.HYPER))
            else:
                # Full size, so no scaling
                self._oImage.set_from_pixbuf(oPixbuf)
        except GObject.GError:
            self._oImage.set_from_icon_name("image-missing",
                                            Gtk.IconSize.DIALOG)
        self._oImage.queue_draw()

    def check_images(self, sTestPath=''):
        """Check if dir contains images in the right structure"""
        self._bShowExpansions = self._have_expansions(sTestPath)
        if self._bShowExpansions:
            return True
        return self._check_test_file(sTestPath)

    def update_config_path(self, sNewPath):
        """Update the path we use to search for expansions."""
        self._sPrefsPath = sNewPath
        self._oImagePlugin.set_config_item(CARD_IMAGE_PATH, sNewPath)
        self._bShowExpansions = self._have_expansions()

    def set_card_text(self, oPhysCard):
        """Set the image in response to a set card name event."""
        if not oPhysCard:
            return
        sCardName = oPhysCard.abstractCard.canonicalName
        sExpPrintName = ''
        if oPhysCard.printing:
            sExpPrintName = IPrintingName(oPhysCard)
        if sCardName != self._sCardName:
            self._set_expansion_info(oPhysCard.abstractCard)
            self._sCardName = sCardName
        if self._aExpPrints:
            if sExpPrintName in self._aExpPrints:
                # Honour expansion from set_card_text
                self._sCurExpPrint = sExpPrintName
                self._iExpansionPos = self._aExpPrints.index(sExpPrintName)
            else:
                # Set self._sCurExpPrint to an existing image, if possible
                self._iExpansionPos = 0
                bFound = False
                while not bFound and \
                        self._iExpansionPos < len(self._aExpPrints):
                    self._sCurExpPrint = \
                        self._aExpPrints[self._iExpansionPos]
                    aFullFilenames = self._convert_cardname_to_path()
                    for sFullFilename in aFullFilenames:
                        if check_file(sFullFilename):
                            bFound = True
                            break
                    if not bFound:
                        self._iExpansionPos += 1
                if not bFound:
                    self._sCurExpPrint = self._aExpPrints[0]
                    self._iExpansionPos = 0
        self._redraw(False)

    def do_cycle_expansion(self, iDir):
        """Change the expansion image to a different one in the list."""
        if len(self._aExpPrints) < 2 or not self._bShowExpansions:
            return  # nothing to scroll through
        if iDir == Direction.FORWARD:
            self._iExpansionPos += 1
            if self._iExpansionPos >= len(self._aExpPrints):
                self._iExpansionPos = 0
        elif iDir == Direction.BACKWARD:
            self._iExpansionPos -= 1
            if self._iExpansionPos < 0:
                self._iExpansionPos = len(self._aExpPrints) - 1
        self._sCurExpPrint = self._aExpPrints[self._iExpansionPos]
        self._redraw(False)

    def set_zoom_mode(self, iScale):
        """Update the zoom mode."""
        self._iZoomMode = iScale
        self._redraw(False)

    def _cycle_expansion(self, _oWidget, oEvent):
        """On a button click, move to the next expansion."""
        if oEvent.type != Gdk.EventType.BUTTON_PRESS:
            return True  # don't jump twice on double or triple clicks
        if oEvent.button == 1:
            self.do_cycle_expansion(Direction.FORWARD)
        elif oEvent.button == 3:
            # Do context menu
            oPopupMenu = CardImagePopupMenu(self, self._iZoomMode)
            oPopupMenu.set_show_expansion_state(self._bShowExpansions and
                                                len(self._aExpPrints) > 1)
            oPopupMenu.popup_at_pointer(None)
        return True

    def _handle_popup_menu(self, _oWidget):
        """Popup the menu on keypress"""
        oPopupMenu = CardImagePopupMenu(self, self._iZoomMode)
        oPopupMenu.set_show_expansion_state(self._bShowExpansions and
                                            len(self._aExpPrints) > 1)
        # Popup should be at the bottom center of the label, as we
        # don't know where the mouse is
        oPopupMenu.popup_at_widget(self.oExpPrintLabel,
                                   Gdk.Gravity.SOUTH,
                                   Gdk.Gravity.NORTH_WEST,
                                   None)

    def _pane_adjust(self, _oAdjust):
        """Redraw the image if needed when the pane size changes."""
        if self._iZoomMode == Size.FIT:
            tCurSize = (self._oView.get_hadjustment().get_page_size(),
                        self._oView.get_vadjustment().get_page_size())
            if tCurSize[0] != self._tPaneSize[0] or \
                    tCurSize[1] != self._tPaneSize[1]:
                self._redraw(True)

    def get_menu_name(self):
        """Return the menu key"""
        return self.sMenuFlag


class BaseImageConfigDialog(SutekhDialog):
    # pylint: disable=too-many-public-methods
    # Gtk Widget, so has many public methods
    """Base Dialog for configuring the Image plugin."""

    sImgDownloadSite = ''

    # The list of download urls to present to the user
    # {'User visible text': url }
    dDownloadUrls = {}

    def __init__(self, oImagePlugin, bFirstTime=False):
        super().__init__(
            'Configure Card Images Plugin',
            oImagePlugin.parent,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            ("_OK", Gtk.ResponseType.OK,
             "_Cancel", Gtk.ResponseType.CANCEL))
        self.oDescLabel = Gtk.Label()
        if not bFirstTime:
            self.oDescLabel.set_markup('<b>Choose how to configure the'
                                       ' cardimages plugin</b>')
        else:
            self.oDescLabel.set_markup('<b>Choose how to configure the '
                                       'cardimages plugin</b>\n'
                                       'Choose cancel to skip '
                                       'configuring the images plugin\n'
                                       'You will not be prompted again')
        sDefaultDir = oImagePlugin.get_config_item(CARD_IMAGE_PATH)
        self.oChoice = FileOrDirOrUrlWidget(
            oImagePlugin.parent,
            "Choose location for images file", "Choose image directory",
            sDefaultDir, self.dDownloadUrls)
        add_filter(self.oChoice, 'Zip Files', ['*.zip', '*.ZIP'])
        self.vbox.pack_start(self.oDescLabel, False, False, 0)
        if not bFirstTime:
            # Set to the null choice
            self.oChoice.select_by_name('Select directory ...')
        self.vbox.pack_start(self.oChoice, False, False, 0)
        if oImagePlugin.DOWNLOAD_SUPPORTED:
            self.oDownload = Gtk.CheckButton(
                'Download missing images from %s?' % self.sImgDownloadSite)
            bCurrentDownload = oImagePlugin.get_config_item(DOWNLOAD_IMAGES)
            self.oDownloadExpansions = Gtk.CheckButton(
                'Download images for each expansion?')
            bDownloadExpansions = oImagePlugin.get_config_item(
                DOWNLOAD_EXPANSIONS)
            if bCurrentDownload is None:
                # Handle 'not in the config file' issues
                bCurrentDownload = False
                bDownloadExpansions = False
            self.oDownload.set_active(bCurrentDownload)
            self.oDownload.connect('toggled', self._enable_exp)
            self.oDownloadExpansions.set_active(bDownloadExpansions)
            if not bCurrentDownload:
                self.oDownloadExpansions.set_sensitive(False)
            self.vbox.pack_start(self.oDownload, False, False, 0)
            self.vbox.pack_start(self.oDownloadExpansions, False, False, 0)
        else:
            self.oDownload = None
        self.set_size_request(400, 200)

        self.show_all()

    def get_data(self):
        """Get the results of the users choice."""
        sFile, _bUrl, bDir = self.oChoice.get_file_or_dir_or_url()
        if self.oDownload:
            bDownload = self.oDownload.get_active()
            bDownloadExpansions = self.oDownloadExpansions.get_active()
        else:
            bDownload = False
            bDownloadExpansions = False
        if bDir:
            # Just return the name the user chose
            return sFile, True, bDownload, bDownloadExpansions
        if sFile:
            oOutFile = tempfile.TemporaryFile()
            self.oChoice.get_binary_data(oOutFile)
            return oOutFile, False, bDownload, bDownloadExpansions
        return None, False, bDownload, bDownloadExpansions

    def _enable_exp(self, oButton):
        """Enable or disable the 'Expansion images' button as required."""
        self.oDownloadExpansions.set_sensitive(oButton.get_active())


class BaseImagePlugin(BasePlugin):
    """Plugin providing access to the Image Frame."""
    dTableVersions = {}
    aModelsSupported = ("MainWindow",)

    DOWNLOAD_SUPPORTED = False

    dGlobalConfig = {
        CARD_IMAGE_PATH: 'string(default=None)',
    }

    _sMenuFlag = BaseImageFrame.sMenuFlag
    _cImageFrame = BaseImageFrame

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.oImageFrame = None
        self._oReplaceItem = None
        self._oAddItem = None
        self._oConfigMenuItem = None

    image_frame = property(fget=lambda self: self.oImageFrame,
                           doc="The image frame")

    @classmethod
    def update_config(cls):
        """Add a download option if the plugin supports it."""
        if cls.DOWNLOAD_SUPPORTED:
            # We flag download images with None so we can do first time
            # config off that
            cls.dGlobalConfig[DOWNLOAD_IMAGES] = 'boolean(default=None)'
            cls.dGlobalConfig[DOWNLOAD_EXPANSIONS] = 'boolean(default=False)'

    def init_image_frame(self):
        """Setup the image frame."""
        if not self.oImageFrame:
            self.oImageFrame = self._cImageFrame(self)
            self.oImageFrame.set_title(self._sMenuFlag)
            self.oImageFrame.add_parts()

    def cleanup(self):
        """Cleanup listeners if required"""
        if self.oImageFrame:
            self.oImageFrame.cleanup()
        super().cleanup()

    def get_menu_item(self):
        """Overrides method from base class.

           Adds the menu item on the MainWindow if the images can be found.
           """
        self.init_image_frame()
        # Add listener
        self._oReplaceItem = Gtk.MenuItem(
            label="Replace with Card Image Frame")
        self._oReplaceItem.connect("activate", self.replace_pane)

        self._oAddItem = Gtk.MenuItem(label="Add Card Image Frame")
        self._oAddItem.connect("activate", self.add_pane)
        self.parent.add_to_menu_list('Card Image Frame',
                                     self.add_image_frame_active)
        self._oConfigMenuItem = Gtk.MenuItem(
            label="Configure Card Images")
        self._oConfigMenuItem.connect("activate", self.config_activate)
        self._oDownloadMenuItem = Gtk.MenuItem(
            label="Download all missing card images")
        self._oDownloadMenuItem.connect("activate", self.download_all_activate)
        if not self.image_frame.check_images():
            # Don't allow the menu option if we can't find the images
            self.add_image_frame_active(False)
            self._oDownloadMenuItem.set_sensitive(False)
        return [('Data Downloads', self._oConfigMenuItem),
                ('Data Downloads', self._oDownloadMenuItem),
                ('Add Pane', self._oAddItem),
                ('Replace Pane', self._oReplaceItem)]

    def setup(self):
        """Prompt the user to download/setup images the first time"""
        raise NotImplementedError('Implement setup')

    def config_activate(self, _oMenuWidget):
        """Configure the plugin dialog."""
        raise NotImplementedError('Implement config_activate')

    def _activate_menu(self):
        """Update the menu item"""
        if not self.parent.is_open_by_menu_name(self._sMenuFlag):
            # Pane is not open, so try to enable menu
            self.add_image_frame_active(True)
        self._oDownloadMenuItem.set_sensitive(True)

    def download_all_activate(self, _oMenuWidget):
        """Download all the missing images"""
        iMissing, iOutdated = self.image_frame.count_missing_outdated_images()
        if not iMissing and not iOutdated:
            _iMesg = do_complaint_buttons(
                "All images already downloaded.", Gtk.MessageType.INFO,
                ("_OK", Gtk.ResponseType.OK))
            return
        iQuery = do_complaint_buttons(
            f"Download {iMissing} missing and {iOutdated} outdated"
            " images now?", Gtk.MessageType.QUESTION,
            ("Yes", Gtk.ResponseType.YES, "No", Gtk.ResponseType.NO))
        if iQuery != Gtk.ResponseType.YES:
            return
        self.image_frame.download_all_missing_outdated_images()

    def _unzip_file(self, oFile):
        """Unzip a file containing the images."""
        try:
            oZipFile = zipfile.ZipFile(oFile)
        except zipfile.BadZipfile:
            return False
        return self._unzip_heart(oZipFile)

    def _unzip_heart(self, oZipFile):
        """Heavy lifting of unzipping a file"""
        sPrefsPath = self.get_config_item(CARD_IMAGE_PATH)
        ensure_dir_exists(sPrefsPath)
        iNumber = len(oZipFile.infolist())
        if iNumber < 300:
            # zipfile too short, so don't bother
            return False
        oProgressDialog = ProgressDialog()
        oProgressDialog.set_description('Unzipping')
        iCur = 0
        for oItem in oZipFile.infolist():
            iCur += 1
            oProgressDialog.update_bar(float(iCur) / iNumber)
            oData = oZipFile.read(oItem.filename)
            # Empty data represents a folder
            # (or at any rate a file to be skipped)
            if not oData:
                continue
            # Should I also test for cardimages\ ?
            sFileName = os.path.join(sPrefsPath,
                                     oItem.filename.replace('cardimages/',
                                                            ''))
            sFileName = sFileName.replace('/', os.path.sep)
            sDir = os.path.dirname(sFileName)
            ensure_dir_exists(sDir)
            oOutputFile = open(sFileName, 'wb')
            oOutputFile.write(oData)
            oOutputFile.close()
        oProgressDialog.destroy()
        if self.image_frame.check_images(sPrefsPath):
            return True
        return False

    def _accept_path(self, sTestPath):
        """Check if the path from user is OK."""
        if sTestPath is not None:
            # Test if path exists
            if not os.path.exists(sTestPath):
                iQuery = do_complaint_buttons(
                    "Folder does not exist. Really use it?\n"
                    "(Answering yes will create the folder)",
                    Gtk.MessageType.QUESTION,
                    ("Yes", Gtk.ResponseType.YES,
                     "No", Gtk.ResponseType.NO))
                if iQuery == Gtk.ResponseType.NO:
                    # Treat as cancelling
                    return False
                ensure_dir_exists(sTestPath)
                # We know it doesn't have images, but as we've been
                # told to create it by the user, we assume they know
                # what they're doing and they intend to download images
                # into it
                return True
            if not os.path.isdir(sTestPath):
                # Exists, but not a directory, so this is a fatal
                # error
                # This in general shouldn't happen, because we usually
                # check the path from the file widget, but we don't want
                # to assume that's the case for all users of this helper
                do_complaint_error(
                    "%s is not a folder. Please choose a path for"
                    " the images" % sTestPath)
                return False
            # Test if path has images
            if not self.image_frame.check_images(sTestPath):
                iQuery = do_complaint_buttons(
                    "Folder does not seem to contain images\n"
                    "Are you sure?", Gtk.MessageType.QUESTION,
                    ("Yes", Gtk.ResponseType.YES,
                     "No", Gtk.ResponseType.NO))
                if iQuery == Gtk.ResponseType.NO:
                    # Treat as cancelling
                    return False
            return True
        return False  # No path, can't be OK

    def add_image_frame_active(self, bValue):
        """Toggle the sensitivity of the menu item."""
        if bValue and not self.image_frame.check_images():
            # Can only be set true if check_images returns true
            self._oReplaceItem.set_sensitive(False)
            self._oAddItem.set_sensitive(False)
        else:
            self._oReplaceItem.set_sensitive(bValue)
            self._oAddItem.set_sensitive(bValue)

    def get_frame_from_config(self, sType):
        """Add the frame if it's been saved in the config file."""
        if sType == self._sMenuFlag:
            return self.image_frame
        return None

    def replace_pane(self, _oWidget):
        """Handle replacing a frame to the main window if required"""
        if not self.parent.is_open_by_menu_name(self._sMenuFlag):
            oNewPane = self.parent.focussed_pane
            if oNewPane:
                self.image_frame.set_unique_id()
                self.parent.replace_frame(oNewPane, self.image_frame)

    def add_pane(self, _oWidget):
        """Handle adding the frame to the main window if required"""
        if not self.parent.is_open_by_menu_name(self._sMenuFlag):
            oNewPane = self.parent.add_pane_end()
            self.image_frame.set_unique_id()
            self.parent.replace_frame(oNewPane, self.image_frame)

    def run_checks(self):
        """Find and list any missing images."""
        self.image_frame.check_for_all_cards()
