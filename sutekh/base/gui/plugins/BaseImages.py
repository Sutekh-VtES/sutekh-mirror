# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Adds a frame which will display card images from ARDB in the GUI"""

import gtk
import gobject
import unicodedata
import os
import zipfile
import tempfile
import urllib2
from sqlobject import SQLObjectNotFound
from ...core.BaseObjects import IAbstractCard
from ...io.UrlOps import urlopen_with_timeout
from ...gui.GuiDataPack import progress_fetch_data, gui_error_handler
from ..BasePluginManager import BasePlugin
from ..ProgressDialog import ProgressDialog
from ..MessageBus import MessageBus, CARD_TEXT_MSG
from ..BasicFrame import BasicFrame
from ..SutekhDialog import SutekhDialog, do_complaint_buttons
from ..AutoScrolledWindow import AutoScrolledWindow
from ...Utility import prefs_dir, ensure_dir_exists
from ..FileOrUrlWidget import FileOrDirOrUrlWidget
from ..SutekhFileWidget import add_filter


FORWARD, BACKWARD = range(2)
FULL, VIEW_FIXED, FIT = range(3)
RATIO = (225, 300)

# Config Key Constants
DOWNLOAD_IMAGES = 'download images'
CARD_IMAGE_PATH = 'card image path'


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
        fTest = file(sFileName, 'rb')
        fTest.close()
    except IOError:
        bRes = False
    return bRes


def unaccent(sCardName):
    """Remove Unicode accents."""
    # Inspired by a post by renaud turned up by google
    # Unicode Normed decomposed form
    sNormed = unicodedata.normalize('NFD',
                                    unicode(sCardName.encode('utf8'),
                                            encoding='utf-8'))
    # Drop non-ascii characters
    return "".join(b for b in sNormed.encode('utf8') if ord(b) < 128)


def image_gui_error_handler(oExp):
    """We filter out 404 not found so we don't loop endlessly on
       card images that aren't available"""
    if isinstance(oExp, urllib2.HTTPError) and oExp.code == 404:
        return
    gui_error_handler(oExp)


class CardImagePopupMenu(gtk.Menu):
    # pylint: disable-msg=R0904
    # R0904 - can't not trigger these warning with pygtk
    """Popup menu for the Card Image Frame"""

    def __init__(self, oFrame, iZoomMode):
        super(CardImagePopupMenu, self).__init__()
        self.oFrame = oFrame
        self.oZoom = gtk.RadioAction('Zoom', 'Show images at original size',
                                     None, None, FULL)
        self.oZoom.set_group(None)
        self.oViewFixed = gtk.RadioAction('ViewFixed',
                                          'Show images at fixed size',
                                          None, None, VIEW_FIXED)
        self.oViewFixed.set_group(self.oZoom)
        self.oViewFit = gtk.RadioAction('ViewFit', 'Fit images to the pane',
                                        None, None, FIT)
        self.oViewFit.set_group(self.oZoom)
        self.oNext = gtk.Action('NextExp', 'Show next expansion image',
                                None, None)
        self.oPrev = gtk.Action('PrevExp', 'Show previous expansion image',
                                None, None)

        self.oPrev.connect('activate', self.cycle_expansion, BACKWARD)
        self.oNext.connect('activate', self.cycle_expansion, FORWARD)
        self.oViewFit.connect('activate', self.set_zoom, FIT)
        self.oZoom.connect('activate', self.set_zoom, FULL)
        self.oViewFixed.connect('activate', self.set_zoom, VIEW_FIXED)

        if iZoomMode == FULL:
            self.oZoom.set_active(True)
        elif iZoomMode == VIEW_FIXED:
            self.oViewFixed.set_active(True)
        elif iZoomMode == FIT:
            self.oViewFit.set_active(True)

        self.add(self.oViewFit.create_menu_item())
        self.add(self.oViewFixed.create_menu_item())
        self.add(self.oZoom.create_menu_item())
        self.add(self.oNext.create_menu_item())
        self.add(self.oPrev.create_menu_item())

    def set_show_expansion_state(self, bValue):
        """Grey out the expansion menus if needed"""
        self.oNext.set_sensitive(bValue)
        self.oPrev.set_sensitive(bValue)

    def cycle_expansion(self, _oWidget, iDir):
        """Change the expansion as requested."""
        assert(iDir in (BACKWARD, FORWARD))
        self.oFrame.do_cycle_expansion(iDir)

    def set_zoom(self, _oWidget, iScale):
        """Change the drawing mode."""
        assert(iScale in (FULL, VIEW_FIXED, FIT))
        self.oFrame.set_zoom_mode(iScale)


class BaseImageFrame(BasicFrame):
    # pylint: disable-msg=R0904, R0902
    # R0904 - can't not trigger these warning with pygtk
    # R0902 - we need to keep quite a lot of internal state
    """Frame which displays the image.

       We wrap a gtk.Image in an EventBox (for focus & DnD events)
       and a Viewport (for scrolling)
       """

    sMenuFlag = 'Card Image Frame'

    # Subclasses should override this
    APP_NAME = 'Deck Builder'

    def __init__(self, oImagePlugin):
        super(BaseImageFrame, self).__init__(oImagePlugin.parent)
        self._oImagePlugin = oImagePlugin
        oVBox = gtk.VBox(False, 2)
        oBox = gtk.EventBox()
        self.oExpansionLabel = gtk.Label()
        oVBox.pack_start(self.oExpansionLabel, False, False)
        oVBox.pack_start(oBox)
        self._oView = AutoScrolledWindow(oVBox, True)
        self._oView.get_hadjustment().connect('changed', self._pane_adjust)
        self._oView.get_vadjustment().connect('changed', self._pane_adjust)
        self._oImage = gtk.Image()
        self._oImage.set_from_stock(gtk.STOCK_MISSING_IMAGE,
                                    gtk.ICON_SIZE_DIALOG)
        oBox.add(self._oImage)

        # Enable DnD handling, same as for BasicFrame
        self.set_drag_handler(oBox)
        self.set_drop_handler(oBox)
        oBox.connect('button-press-event', self._cycle_expansion)

        self._sPrefsPath = self._oImagePlugin.get_config_item(
            CARD_IMAGE_PATH)
        if self._sPrefsPath is None:
            self._sPrefsPath = os.path.join(prefs_dir(self.APP_NAME),
                                            'cardimages')
            self._oImagePlugin.set_config_item(CARD_IMAGE_PATH,
                                               self._sPrefsPath)
        self._bShowExpansions = self._have_expansions()
        self._sCurExpansion = ''
        self._aExpansions = []
        self._iExpansionPos = 0
        self._sCardName = ''
        self._iZoomMode = FIT
        self._tPaneSize = (0, 0)
        self._dUrlCache = {}

    type = property(fget=lambda self: "Card Image Frame", doc="Frame Type")

    def frame_setup(self):
        """Subscribe to the set_card_text signal"""
        # Reset to stock image to force sane state
        self._oImage.set_from_stock(gtk.STOCK_MISSING_IMAGE,
                                    gtk.ICON_SIZE_DIALOG)
        MessageBus.subscribe(CARD_TEXT_MSG, 'set_card_text',
                             self.set_card_text)
        super(BaseImageFrame, self).frame_setup()

    def cleanup(self, bQuit=False):
        """Remove the listener"""
        MessageBus.unsubscribe(CARD_TEXT_MSG, 'set_card_text',
                               self.set_card_text)
        super(BaseImageFrame, self).cleanup(bQuit)

    def _have_expansions(self, sTestPath=''):
        """Test if directory contains expansion/image subdirs"""
        raise NotImplementedError("Implement _have_expansions")

    def _check_test_file(self, sTestPath=''):
        """Test if images can be found in the non-expansion case"""
        raise NotImplementedError("Implement _check_test_file")

    def _convert_expansion(self, sExpansionName):
        """Convert the Full Expansion name into the abbreviation needed."""
        raise NotImplementedError("Implement _convert_expansions")

    def _set_expansion_info(self, sCardName):
        """Set the expansion info."""
        # pylint: disable-msg=E1101
        # pylint doesn't pick up IAbstractCard methods correctly
        try:
            oAbsCard = IAbstractCard(sCardName)
            bHasInfo = len(oAbsCard.rarity) > 0
        except SQLObjectNotFound:
            bHasInfo = False
        if bHasInfo:
            aExp = [oP.expansion.name for oP in oAbsCard.rarity]
            self._aExpansions = sorted(list(set(aExp)))  # remove duplicates
            self._iExpansionPos = 0
            self._sCurExpansion = self._aExpansions[0]
        else:
            self._sCurExpansion = ''
            self._aExpansions = []
            self._iExpansionPos = 0

    def _redraw(self, bPause):
        """Redraw the current card"""
        # If further events are pending, don't try and redraw
        if bPause and gtk.gdk.events_pending():
            return
        if not self._sCardName:
            # Don't go down the rest of redraw path during startup
            return
        sFullFilename = self._convert_cardname_to_path()
        self._load_image(sFullFilename)

    def _make_card_url(self):
        """Return a url pointing to a scan of the image"""
        raise NotImplementedError("implement _make_card_url")

    def _norm_cardname(self):
        """Normalise the card name"""
        raise NotImplementedError("Implement norm_cardname")

    def _convert_cardname_to_path(self):
        """Convert sCardName to the form used by the card image list"""
        sCurExpansionPath = self._convert_expansion(self._sCurExpansion)
        sFilename = self._norm_cardname()
        return os.path.join(self._sPrefsPath, sCurExpansionPath, sFilename)

    def _load_image(self, sFullFilename):
        """Load an image into the pane, show broken image if needed"""
        self._oImage.set_alignment(0.5, 0.5)  # Centre image

        if not check_file(sFullFilename):
            if (self._oImagePlugin.DOWNLOAD_SUPPORTED and
                    self._oImagePlugin.get_config_item(DOWNLOAD_IMAGES)):
                # Attempt to download the image from the url
                sUrl = self._make_card_url()
                if sUrl:
                    if sUrl not in self._dUrlCache:
                        oFile = urlopen_with_timeout(
                            sUrl, fErrorHandler=image_gui_error_handler)
                    else:
                        oFile = self._dUrlCache[sUrl]
                else:
                    # No url, so fall back to the 'no image' case
                    self._oImage.set_from_stock(gtk.STOCK_MISSING_IMAGE,
                                                gtk.ICON_SIZE_DIALOG)
                    self._oImage.queue_draw()
                    return
                self._dUrlCache[sUrl] = oFile
                if oFile:
                    oOutFile = file(sFullFilename, 'wb')
                    # Attempt to fetch the data
                    progress_fetch_data(oFile, oOutFile)
                    oOutFile.close()
                    oFile.close()
        try:
            if self._bShowExpansions:
                self.oExpansionLabel.set_markup(
                    '<i>Image from expansion : </i> %s' % self._sCurExpansion)
                self.oExpansionLabel.show()
                # pylint: disable-msg=E1101
                # pylint doesn't pick up allocation methods correctly
                iHeightOffset = self.oExpansionLabel.allocation.height + 2
            else:
                self.oExpansionLabel.hide()  # config changes can cause this
                iHeightOffset = 0
            oPixbuf = gtk.gdk.pixbuf_new_from_file(sFullFilename)
            iWidth = oPixbuf.get_width()
            iHeight = oPixbuf.get_height()
            if self._iZoomMode == FIT:
                # Need to fix aspect ratios
                iPaneHeight = (self._oView.get_vadjustment().page_size -
                               iHeightOffset)
                iPaneWidth = self._oView.get_hadjustment().page_size
                # don't centre image under label
                self._oImage.set_alignment(0, 0.5)
                iDestWidth, iDestHeight = _scale_dims(iWidth, iHeight,
                                                      iPaneWidth, iPaneHeight)
                if iDestWidth > 0 and iDestHeight > 0:
                    self._oImage.set_from_pixbuf(
                        oPixbuf.scale_simple(iDestWidth, iDestHeight,
                                             gtk.gdk.INTERP_HYPER))
                    self._tPaneSize = (self._oView.get_hadjustment().page_size,
                                       self._oView.get_vadjustment().page_size)
            elif self._iZoomMode == VIEW_FIXED:
                iDestWidth, iDestHeight = _scale_dims(iWidth, iHeight,
                                                      RATIO[0], RATIO[1])
                self._oImage.set_from_pixbuf(
                    oPixbuf.scale_simple(iDestWidth, iDestHeight,
                                         gtk.gdk.INTERP_HYPER))
            else:
                # Full size, so no scaling
                self._oImage.set_from_pixbuf(oPixbuf)
        except gobject.GError:
            self._oImage.set_from_stock(gtk.STOCK_MISSING_IMAGE,
                                        gtk.ICON_SIZE_DIALOG)
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
        sExpansionName = ''
        if oPhysCard.expansion:
            sExpansionName = oPhysCard.expansion.name
        if sCardName != self._sCardName:
            self._set_expansion_info(sCardName)
            self._sCardName = sCardName
        if len(self._aExpansions) > 0:
            if sExpansionName in self._aExpansions:
                # Honour expansion from set_card_text
                self._sCurExpansion = sExpansionName
                self._iExpansionPos = self._aExpansions.index(sExpansionName)
            else:
                # Set self._sCurExpansion to an existing image, if possible
                self._iExpansionPos = 0
                bFound = False
                while not bFound and \
                        self._iExpansionPos < len(self._aExpansions):
                    self._sCurExpansion = \
                        self._aExpansions[self._iExpansionPos]
                    sFullFilename = self._convert_cardname_to_path()
                    if check_file(sFullFilename):
                        bFound = True
                    else:
                        self._iExpansionPos += 1
                if not bFound:
                    self._sCurExpansion = self._aExpansions[0]
                    self._iExpansionPos = 0
        self._redraw(False)

    def do_cycle_expansion(self, iDir):
        """Change the expansion image to a different one in the list."""
        if len(self._aExpansions) < 2 or not self._bShowExpansions:
            return  # nothing to scroll through
        if iDir == FORWARD:
            self._iExpansionPos += 1
            if self._iExpansionPos >= len(self._aExpansions):
                self._iExpansionPos = 0
        elif iDir == BACKWARD:
            self._iExpansionPos -= 1
            if self._iExpansionPos < 0:
                self._iExpansionPos = len(self._aExpansions) - 1
        self._sCurExpansion = self._aExpansions[self._iExpansionPos]
        self._redraw(False)

    def set_zoom_mode(self, iScale):
        """Update the zoom mode."""
        self._iZoomMode = iScale
        self._redraw(False)

    def _cycle_expansion(self, _oWidget, oEvent):
        """On a button click, move to the next expansion."""
        if oEvent.type != gtk.gdk.BUTTON_PRESS:
            return True  # don't jump twice on double or triple clicks
        if oEvent.button == 1:
            self.do_cycle_expansion(FORWARD)
        elif oEvent.button == 3:
            # Do context menu
            oPopupMenu = CardImagePopupMenu(self, self._iZoomMode)
            oPopupMenu.set_show_expansion_state(self._bShowExpansions and
                                                len(self._aExpansions) > 1)
            oPopupMenu.popup(None, None, None, oEvent.button, oEvent.time)
        return True

    def _pane_adjust(self, _oAdjust):
        """Redraw the image if needed when the pane size changes."""
        if self._iZoomMode == FIT:
            tCurSize = (self._oView.get_hadjustment().page_size,
                        self._oView.get_vadjustment().page_size)
            if tCurSize[0] != self._tPaneSize[0] or \
                    tCurSize[1] != self._tPaneSize[1]:
                self._redraw(True)

    def get_menu_name(self):
        """Return the menu key"""
        return self.sMenuFlag


class BaseImageConfigDialog(SutekhDialog):
    # pylint: disable-msg=R0904
    # R0904 - gtk Widget, so has many public methods
    """Base Dialog for configuring the Image plugin."""

    sDefURLId = ''
    sDefaultUrl = ''
    sImgDownloadSite = ''

    def __init__(self, oImagePlugin, bFirstTime=False):
        super(BaseImageConfigDialog, self).__init__(
            'Configure Card Images Plugin',
            oImagePlugin.parent,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_OK, gtk.RESPONSE_OK,
             gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.oDescLabel = gtk.Label()
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
        if self.sDefaultUrl:
            dUrls = {self.sDefURLId: self.sDefaultUrl}
        else:
            # Just allow the user to choose an url themselves
            dUrls = None
        self.oChoice = FileOrDirOrUrlWidget(
            oImagePlugin.parent,
            "Choose location for images file", "Choose image directory",
            sDefaultDir, dUrls)
        add_filter(self.oChoice, 'Zip Files', ['*.zip', '*.ZIP'])
        # pylint: disable-msg=E1101
        # pylint doesn't pick up vbox methods correctly
        self.vbox.pack_start(self.oDescLabel, False, False)
        if not bFirstTime:
            # Set to the null choice
            self.oChoice.select_by_name('Select directory ...')
            self.vbox.pack_start(self.oChoice, False, False)
        if oImagePlugin.DOWNLOAD_SUPPORTED:
            self.oDownload = gtk.CheckButton(
                'Download missing images from %s?' % self.sImgDownloadSite)
            bCurrentDownload = oImagePlugin.get_config_item(DOWNLOAD_IMAGES)
            if bCurrentDownload is None:
                # Handle 'not in the config file' issues
                bCurrentDownload = False
            self.oDownload.set_active(bCurrentDownload)
            self.vbox.pack_start(self.oDownload, False, False)
        else:
            self.oDownload = None
        self.set_size_request(400, 200)

        self.show_all()

    def get_data(self):
        """Get the results of the users choice."""
        sFile, _bUrl, bDir = self.oChoice.get_file_or_dir_or_url()
        if self.oDownload:
            bDownload = self.oDownload.get_active()
        else:
            bDownload = False
        if bDir:
            # Just return the name the user chose
            return sFile, True, bDownload
        if sFile:
            oOutFile = tempfile.TemporaryFile()
            self.oChoice.get_binary_data(oOutFile)
            return oOutFile, False, bDownload
        return None, None, bDownload


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

    # pylint: disable-msg=W0142
    # ** magic OK here
    def __init__(self, *args, **kwargs):
        super(BaseImagePlugin, self).__init__(*args, **kwargs)
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
            cls.dGlobalConfig[DOWNLOAD_IMAGES] = 'boolean(default=None)'

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
        super(BaseImagePlugin, self).cleanup()

    def get_menu_item(self):
        """Overrides method from base class.

           Adds the menu item on the MainWindow if the images can be found.
           """
        if not self.check_versions() or not self.check_model_type():
            return None
        self.init_image_frame()
        # Add listener
        self._oReplaceItem = gtk.MenuItem("Replace with Card Image Frame")
        self._oReplaceItem.connect("activate", self.replace_pane)

        self._oAddItem = gtk.MenuItem("Add Card Image Frame")
        self._oAddItem.connect("activate", self.add_pane)
        self.parent.add_to_menu_list('Card Image Frame',
                                     self.add_image_frame_active)
        self._oConfigMenuItem = gtk.MenuItem(
            "Download or Configure Card Images")
        self._oConfigMenuItem.connect("activate", self.config_activate)
        if not self.image_frame.check_images():
            # Don't allow the menu option if we can't find the images
            self.add_image_frame_active(False)
        return [('Data Downloads', self._oConfigMenuItem),
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
            oOutputFile = file(sFileName, 'wb')
            oOutputFile.write(oData)
            oOutputFile.close()
        oProgressDialog.destroy()
        if self.image_frame.check_images(sPrefsPath):
            return True
        return False

    def _accept_path(self, sTestPath):
        """Check if the path from user is OK."""
        if sTestPath is not None:
            # Test if path has images
            if not self.image_frame.check_images(sTestPath):
                iQuery = do_complaint_buttons(
                    "Folder does not seem to contain images\n"
                    "Are you sure?", gtk.MESSAGE_QUESTION,
                    (gtk.STOCK_YES, gtk.RESPONSE_YES,
                     gtk.STOCK_NO, gtk.RESPONSE_NO))
                if iQuery == gtk.RESPONSE_NO:
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
        else:
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
