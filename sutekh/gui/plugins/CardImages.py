# CardImages.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Adds a frame which will display card images from ARDB in the GUI"""

import gtk
import gobject
import unicodedata
import os
import zipfile
import urllib2
import tempfile
from sqlobject import SQLObjectNotFound
from sutekh.core.SutekhObjects import PhysicalCard, PhysicalCardSet, \
        IAbstractCard, IExpansion
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.ProgressDialog import ProgressDialog
from sutekh.gui.CardListView import CardListViewListener
from sutekh.gui.BasicFrame import BasicFrame
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_buttons, \
        do_complaint_error
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.SutekhUtility import prefs_dir, ensure_dir_exists


_iFORWARD, _iBACKWARD = range(2)
_iFULL, _iVIEW_FIXED, _iFIT = range(3)
_tRATIO = (225, 300)

def _scale_dims(iImageWidth, iImageHeight, iPaneWidth, iPaneHeight):
    """Rescale the image dimension so they fit in the pane, preserving the
       aspect ratiom."""
    fImageAspectRatio = float(iImageHeight) / float(iImageWidth)
    fPaneAspectRatio = float(iPaneHeight) / float(iPaneWidth)

    if fPaneAspectRatio > fImageAspectRatio:
        # wider
        fDestWidth = iPaneWidth
        fDestHeight = iPaneWidth * fImageAspectRatio
    elif fPaneAspectRatio < fImageAspectRatio:
        fDestHeight = iPaneHeight
        fDestWidth = iPaneHeight / fImageAspectRatio
    return int(fDestWidth), int(fDestHeight)

def _check_file(sFileName):
    """Check if file exists and is readable"""
    bRes = True
    try:
        fTest = file(sFileName, 'rb')
        fTest.close()
    except IOError:
        bRes = False
    return bRes

def _unaccent(sCardName):
    """Remove unicode accents."""
    # Inspired by a post by renaud turned up by google
    # Unicode Normed decomposed form
    sNormed = unicodedata.normalize('NFD',
            unicode(sCardName.encode('utf8'), encoding='utf-8'))
    # Drop non-ascii characters
    return "".join(b for b in sNormed.encode('utf8') if ord(b) < 128)

class CardImagePopupMenu(gtk.Menu):
    # pylint: disable-msg=R0904
    # R0904 - can't not trigger these warning with pygtk
    """Popup menu for the Card Image Frame"""

    def __init__(self, oFrame, iZoomMode):
        super(CardImagePopupMenu, self).__init__()
        self.oFrame = oFrame
        self.oZoom = gtk.RadioAction('Zoom', 'Show images at original size',
                None, None, _iFULL)
        self.oZoom.set_group(None)
        self.oViewFixed = gtk.RadioAction('ViewFixed',
                'Show images at fixed size', None, None, _iVIEW_FIXED)
        self.oViewFixed.set_group(self.oZoom)
        self.oViewFit = gtk.RadioAction('ViewFit', 'Fit images to the pane',
                None, None, _iFIT)
        self.oViewFit.set_group(self.oZoom)
        self.oNext = gtk.Action('NextExp', 'Show next expansion image', None,
                None)
        self.oPrev = gtk.Action('PrevExp', 'Show previous expansion image',
                None, None)

        self.oPrev.connect('activate', self.cycle_expansion, _iBACKWARD)
        self.oNext.connect('activate', self.cycle_expansion, _iFORWARD)
        self.oViewFit.connect('activate', self.set_zoom, _iFIT)
        self.oZoom.connect('activate', self.set_zoom, _iFULL)
        self.oViewFixed.connect('activate', self.set_zoom, _iVIEW_FIXED)

        if iZoomMode == _iFULL:
            self.oZoom.set_active(True)
        elif iZoomMode == _iVIEW_FIXED:
            self.oViewFixed.set_active(True)
        elif iZoomMode == _iFIT:
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

    # pylint: disable-msg=W0613
    # oWidget needed by gtk function signature
    def cycle_expansion(self, oWidget, iDir):
        """Change the expansion as requested."""
        assert(iDir in [_iBACKWARD, _iFORWARD])
        self.oFrame.do_cycle_expansion(iDir)

    def set_zoom(self, oWidget, iScale):
        """Change the drawing mode."""
        assert(iScale in [_iFULL, _iVIEW_FIXED, _iFIT])
        self.oFrame.set_zoom_mode(iScale)

class CardImageFrame(BasicFrame, CardListViewListener):
    # pylint: disable-msg=R0904, R0902
    # R0904 - can't not trigger these warning with pygtk
    # R0902 - we need to keep quite a lot of internal state
    """Frame which displays the image.

       We wrap a gtk.Image in an EventBox (for focus & DnD events)
       and a Viewport (for scrolling)
       """

    def __init__(self, oMainWindow, oConfigFile):
        super(CardImageFrame, self).__init__(oMainWindow)
        self._oConfigFile = oConfigFile
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
        aDragTargets = [ ('STRING', 0, 0),
                ('text/plain', 0, 0) ]
        oBox.drag_dest_set(gtk.DEST_DEFAULT_ALL,
                aDragTargets,
                gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
        oBox.connect('drag-data-received', self.drag_drop_handler)
        oBox.connect('drag-motion', self.drag_motion)
        oBox.connect('button-press-event', self.__cycle_expansion)

        self.__sPrefsPath = self._oConfigFile.get_plugin_key('card image path')
        if self.__sPrefsPath is None:
            self.__sPrefsPath = os.path.join(prefs_dir('Sutekh'), 'cardimages')
            self._oConfigFile.set_plugin_key('card image path',
                    self.__sPrefsPath)
        self.__bShowExpansions = self.__have_expansions()
        self.__sCurExpansion = ''
        self.__aExpansions = []
        self.__iExpansionPos = 0
        self.__sCardName = ''
        self.__iZoomMode = _iFIT
        self._tPaneSize = (0, 0)

    type = property(fget=lambda self: "Card Image Frame", doc="Frame Type")

    def __have_expansions(self, sTestPath=''):
        """Test if directory contains expansion/image structure used by ARDB"""
        if sTestPath == '':
            sTestFile = os.path.join(self.__sPrefsPath, 'bh', 'acrobatics.jpg')
        else:
            sTestFile = os.path.join(sTestPath, 'bh', 'acrobatics.jpg')
        return _check_file(sTestFile)

    def __convert_expansion(self, sExpansionName):
        """Convert the Full Expansion name into the abbrevation needed."""
        if sExpansionName == '' or not self.__bShowExpansions:
            return ''
        # pylint: disable-msg=E1101
        # pylint doesn't pick up IExpansion methods correctly
        oExpansion = IExpansion(sExpansionName)
        return oExpansion.shortname.lower()

    def __set_expansion_info(self, sCardName):
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
            self.__aExpansions = sorted(list(set(aExp))) # remove duplicates
            self.__iExpansionPos = 0
            self.__sCurExpansion = self.__aExpansions[0]
        else:
            self.__sCurExpansion = ''
            self.__aExpansions = []
            self.__iExpansionPos = 0

    def __redraw(self, bPause):
        """Redraw the current card"""
        # If further events are pending, don't try and redraw
        if bPause and gtk.gdk.events_pending():
            return
        sFullFilename = self.__convert_cardname()
        self.__load_image(sFullFilename)

    def __convert_cardname(self):
        """Convert sCardName to the form used by the card image list"""
        sCurExpansionPath = self.__convert_expansion(self.__sCurExpansion)
        sFilename = _unaccent(self.__sCardName.lower())
        if sFilename.find('the ') == 0:
            sFilename = sFilename[4:] + 'the'
        sFilename = sFilename.replace('(advanced)', 'adv')
        # Should probably do this via translate
        for sChar in [" ", ".", ",", "'", "(", ")", "-", ":", "!", '"', "/"]:
            sFilename = sFilename.replace(sChar, '')
        sFilename = sFilename + '.jpg'
        return os.path.join(self.__sPrefsPath, sCurExpansionPath, sFilename)

    def __load_image(self, sFullFilename):
        """Load an image into the pane, show broken image if needed"""
        self._oImage.set_alignment(0.5, 0.5) # Centre image
        try:
            if self.__bShowExpansions:
                self.oExpansionLabel.set_markup('<i>Image from expansion :'
                        ' </i> %s' % self.__sCurExpansion)
                self.oExpansionLabel.show()
                # pylint: disable-msg=E1101
                # pylint doesn't pick up allocation methods correctly
                iHeightOffset = self.oExpansionLabel.allocation.height + 2
            else:
                self.oExpansionLabel.hide() # config chanes can cause this
                iHeightOffset = 0
            oPixbuf = gtk.gdk.pixbuf_new_from_file(sFullFilename)
            iWidth = oPixbuf.get_width()
            iHeight = oPixbuf.get_height()
            if self.__iZoomMode == _iFIT:
                # Need to fix aspect ratios
                iPaneHeight = self._oView.get_vadjustment().page_size - \
                        iHeightOffset
                iPaneWidth = self._oView.get_hadjustment().page_size
                # don't centre image under label
                self._oImage.set_alignment(0, 0.5)
                iDestWidth, iDestHeight = _scale_dims(iWidth, iHeight,
                        iPaneWidth, iPaneHeight)
                if iDestWidth > 0 and iDestHeight > 0:
                    self._oImage.set_from_pixbuf(oPixbuf.scale_simple(
                        iDestWidth, iDestHeight, gtk.gdk.INTERP_HYPER))
                    self._tPaneSize = (self._oView.get_hadjustment().page_size,
                            self._oView.get_vadjustment().page_size)
            elif self.__iZoomMode == _iVIEW_FIXED:
                iDestWidth, iDestHeight = _scale_dims(iWidth, iHeight,
                        _tRATIO[0], _tRATIO[1])
                self._oImage.set_from_pixbuf(oPixbuf.scale_simple(iDestWidth,
                    iDestHeight, gtk.gdk.INTERP_HYPER))
            else:
                # Full size, so no scaling
                self._oImage.set_from_pixbuf(oPixbuf)

        except gobject.GError:
            self._oImage.set_from_stock(gtk.STOCK_MISSING_IMAGE,
                    gtk.ICON_SIZE_DIALOG)
        self._oImage.queue_draw()

    def check_images(self, sTestPath=''):
        """Check if dir contains images in the right structure"""
        self.__bShowExpansions = self.__have_expansions(sTestPath)
        if self.__bShowExpansions:
            return True
        if sTestPath == '':
            sTestFile = os.path.join(self.__sPrefsPath, 'acrobatics.jpg')
        else:
            sTestFile = os.path.join(sTestPath, 'acrobatics.jpg')
        return _check_file(sTestFile)

    def update_config_path(self, sNewPath):
        """Update the path we use to search for expansions."""
        self.__sPrefsPath = sNewPath
        self._oConfigFile.set_plugin_key('card image path', sNewPath)
        self.__bShowExpansions = self.__have_expansions()

    def set_card_text(self, sCardName, sExpansionName=''):
        """Set the image in response to a set card name event."""
        if sCardName != self.__sCardName:
            self.__set_expansion_info(sCardName)
            self.__sCardName = sCardName
        if len(self.__aExpansions) > 0:
            if sExpansionName in self.__aExpansions:
                # Honour expansion from set_card_text
                self.__sCurExpansion = sExpansionName
                self.__iExpansionPos = self.__aExpansions.index(sExpansionName)
            elif self.__sCurExpansion == '' or \
                    self.__sCurExpansion not in self.__aExpansions:
                # Set self.__sCurExpansion to a valid value
                self.__sCurExpansion = self.__aExpansions[0]
                self.__iExpansionPos = 0
        self.__redraw(False)

    def do_cycle_expansion(self, iDir):
        """Change the expansion image to a different one in the list."""
        if len(self.__aExpansions) < 2 or not self.__bShowExpansions:
            return # nothing to scroll through
        if iDir == _iFORWARD:
            self.__iExpansionPos += 1
            if self.__iExpansionPos >= len(self.__aExpansions):
                self.__iExpansionPos = 0
        elif iDir == _iBACKWARD:
            self.__iExpansionPos -= 1
            if self.__iExpansionPos < 0:
                self.__iExpansionPos = len(self.__aExpansions) - 1
        self.__sCurExpansion = self.__aExpansions[self.__iExpansionPos]
        self.__redraw(False)

    def set_zoom_mode(self, iScale):
        """Update the zoom mode."""
        self.__iZoomMode = iScale
        self.__redraw(False)

    # pylint: disable-msg=W0613
    # oWidget needed by gtk function signature
    def __cycle_expansion(self, oWidget, oEvent):
        """On a button click, move to the next expansion."""
        if oEvent.type != gtk.gdk.BUTTON_PRESS:
            return True # don't jump twice on double or triple clicks
        if oEvent.button == 1:
            self.do_cycle_expansion(_iFORWARD)
        elif oEvent.button == 3:
            # Do context menu
            oPopupMenu = CardImagePopupMenu(self, self.__iZoomMode)
            oPopupMenu.set_show_expansion_state(self.__bShowExpansions and
                    len(self.__aExpansions) > 1)
            oPopupMenu.popup(None, None, None, oEvent.button, oEvent.time)
        return True

    # W0613 oAdjust also required by signature
    def _pane_adjust(self, oAdjust):
        """Redraw the image if needed when the pane size changes."""
        if self.__iZoomMode == _iFIT:
            tCurSize = (self._oView.get_hadjustment().page_size,
                self._oView.get_vadjustment().page_size)
            if tCurSize[0] != self._tPaneSize[0] or \
                    tCurSize[1] != self._tPaneSize[1]:
                self.__redraw(True)

# pylint: disable-msg=R0904
# R0904 - gtk Widget, so has many public methods
class ImageConfigDialog(SutekhDialog):
    """Dialog for configuring the Image plugin."""
    def __init__(self, oParent, bFirstTime=False):
        super(ImageConfigDialog, self).__init__('Configure Card Images Plugin',
                oParent, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL,
                    gtk.RESPONSE_CANCEL))
        oDescLabel = gtk.Label()
        if not bFirstTime:
            oDescLabel.set_markup('<b>Choose how to configure the cardimages '
                    'plugin</b>')
        else:
            oDescLabel.set_markup('<b>Choose how to configure the cardimages '
                    'plugin</b>\nChoose cancel to skip configuring the '
                    'images plugin\nYou will not be prompted again')
        self.oChoiceDownload = gtk.RadioButton(
                label='Download and install cardimages from feldb.extra.hu')
        self.oChoiceLocalCopy = gtk.RadioButton(self.oChoiceDownload,
                label='Install images from a local zip file')
        self.oChoiceNewDir = gtk.RadioButton(self.oChoiceDownload,
                label='Choose a directory containing the images')
        oChoiceBox = gtk.VBox(False, 2)
        self.oDirChoiceWidget = gtk.FileChooserWidget(
                action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        self.oFileChoiceWidget = gtk.FileChooserWidget(
                action=gtk.FILE_CHOOSER_ACTION_OPEN)
        self.oChoiceDownload.connect('toggled', self._radio_toggled,
                oChoiceBox, None)
        self.oChoiceLocalCopy.connect('toggled', self._radio_toggled,
                oChoiceBox, self.oFileChoiceWidget)
        self.oChoiceNewDir.connect('toggled', self._radio_toggled, oChoiceBox,
                self.oDirChoiceWidget)

        self.oChoiceDownload.set_active(True)
        # pylint: disable-msg=E1101
        # pylint doesn't pick up vbox methods correctly
        self.vbox.pack_start(oDescLabel, False, False)
        self.vbox.pack_start(self.oChoiceDownload, False, False)
        self.vbox.pack_start(self.oChoiceLocalCopy, False, False)
        self.vbox.pack_start(self.oChoiceNewDir, False, False)
        self.vbox.pack_start(oChoiceBox)
        self.set_size_request(600, 600)

        #oDialog.vbox.pack_start(oFileWidget)
        sPrefsPath = oParent.config_file.get_plugin_key('card image path')
        if sPrefsPath is not None:
            if os.path.exists(sPrefsPath) and os.path.isdir(sPrefsPath):
                # File widget doesn't like being pointed at non-dirs
                # when in SELECT_FOLDER mode
                self.oDirChoiceWidget.set_current_folder(sPrefsPath)
        oZipFilter = gtk.FileFilter()
        oZipFilter.add_pattern('*.zip')
        oZipFilter.add_pattern('*.ZIP')
        self.oFileChoiceWidget.add_filter(oZipFilter)
        self.show_all()

    def _radio_toggled(self, oRadioButton, oChoiceBox, oFileWidget):
        """Display the correct file widget when radio buttons change"""
        if oRadioButton.get_active():
            for oChild in oChoiceBox.get_children():
                oChoiceBox.remove(oChild)
            if oFileWidget:
                oChoiceBox.pack_start(oFileWidget)
            self.show_all()

    def get_path(self):
        """Get the path from oDirChoiceWidget."""
        return self.oDirChoiceWidget.get_filename()

    def get_file(self):
        """Get the file from oFileChoiceWidget."""
        return self.oFileChoiceWidget.get_filename()

    def get_choice(self):
        """Get which of the RadioButtons was active."""
        if self.oChoiceDownload.get_active():
            return 'Download'
        elif self.oChoiceLocalCopy.get_active():
            return 'Local copy'
        else:
            return 'New directory'

class CardImagePlugin(CardListPlugin):
    """Plugin providing access to CardImageFrame."""
    dTableVersions = {PhysicalCardSet : [5]}
    aModelsSupported = ["MainWindow"]
    aListenViews = [PhysicalCardSet,
            PhysicalCard]

    oImageFrame = None

    _sMenuFlag = 'Card Image Frame'

    # pylint: disable-msg=W0142
    # ** magic OK here
    def __init__(self, *aArgs, **kwargs):
        super(CardImagePlugin, self).__init__(*aArgs, **kwargs)
        # Add listeners to the appropriate views
        if not self.image_frame:
            self.init_image_frame(self)
        if self._cModelType in self.aListenViews:
            self.view.add_listener(self.image_frame)
        self._oReplaceItem = None
        self._oAddItem = None
        self._oConfigMenuItem = None

    image_frame = property(fget=lambda self: self.get_image_frame(),
            doc="The image frame")

    @classmethod
    def get_image_frame(cls):
        """Return the global ImageFrame."""
        return cls.oImageFrame

    @classmethod
    def init_image_frame(cls, oCur):
        """Setup the global image frame."""
        if not cls.oImageFrame:
            cls.oImageFrame = CardImageFrame(oCur.parent,
                    oCur.parent.config_file)
            cls.oImageFrame.set_title(cls._sMenuFlag)
            cls.oImageFrame.add_parts()

    def get_menu_item(self):
        """Overrides method from base class.

           Adds the menu item on the MainWindow if the images can be found.
           """
        if not self.check_versions() or not self.check_model_type():
            return None
        self._oReplaceItem = gtk.MenuItem("Replace with Card Image Frame")
        self._oReplaceItem.connect("activate", self.replace_pane)

        self._oAddItem = gtk.MenuItem("Add Card Image Frame")
        self._oAddItem.connect("activate", self.add_pane)
        self.parent.add_to_menu_list('Card Image Frame',
                self.add_image_frame_active)
        self._oConfigMenuItem = gtk.MenuItem("Configure Card Images Plugin")
        self._oConfigMenuItem.connect("activate", self.config_activate)
        if not self.image_frame.check_images():
            # Don't allow the menu option if we can't find the images
            self.add_image_frame_active(False)
        return [('Plugins', self._oConfigMenuItem),
                ('Add Pane', self._oAddItem),
                ('Replace Pane', self._oReplaceItem)]

    def setup(self):
        """Prompt the user to download/setup images the first time"""
        sPrefsPath = self.parent.config_file.get_plugin_key('card image path')
        if not os.path.exists(sPrefsPath):
            # Looks like the first time
            oDialog = ImageConfigDialog(self.parent, True)
            self.handle_response(oDialog)
            # Path may have been changed, so we need to requery config file
            sPrefsPath = self.parent.config_file.get_plugin_key(
                    'card image path')
            # Don't get called next time
            ensure_dir_exists(sPrefsPath)

    # pylint: disable-msg=W0613
    # oMenuWidget needed by gtk function signature
    def config_activate(self, oMenuWidget):
        """Configure the plugin dialog."""
        oDialog = ImageConfigDialog(self.parent, False)
        self.handle_response(oDialog)

    def handle_response(self, oDialog):
        """Handle the response from the config dialog"""
        iResponse = oDialog.run()
        bActivateMenu = False
        if iResponse == gtk.RESPONSE_OK:
            sChoice = oDialog.get_choice()
            if sChoice == 'Download':
                if self._download_file():
                    bActivateMenu = True
                else:
                    do_complaint_error('Unable to successfully download'
                            ' and install zipfile')
            elif sChoice == 'Local copy':
                sFileName = oDialog.get_file()
                if self._unzip_file(sFileName):
                    bActivateMenu = True
                else:
                    do_complaint_error('Unable to successfully install '
                            ' zipfile %s' % sFileName)
            else:
                # New directory
                sTestPath = oDialog.get_path()
                if self._accept_path(sTestPath):
                    # Update preferences
                    self.image_frame.update_config_path(sTestPath)
                    bActivateMenu = True
        if bActivateMenu:
            # Update the menu display if needed
            if self._sMenuFlag not in self.parent.dOpenFrames.values():
                # Pane is not open, so try to enable menu
                self.add_image_frame_active(True)
        # get rid of the dialog
        oDialog.destroy()

    def _download_file(self):
        """Download a zip file containing the images."""
        # Download and install http://feldb.extra.hu/pictures.zip
        sUrl = 'http://feldb.extra.hu/pictures.zip'
        oFile = urllib2.urlopen(sUrl)
        sDownloadDir = prefs_dir('Sutekh')
        ensure_dir_exists(sDownloadDir)
        fTemp = tempfile.TemporaryFile()
        sLength = oFile.info().getheader('Content-Length')
        if sLength:
            iLength = int(sLength)
            oProgress = ProgressDialog()
            oProgress.set_description('Download progress')
            iTotal = 0
            bCont = True
            while bCont:
                oInf = oFile.read(10000)
                iTotal += 10000
                oProgress.update_bar(float(iTotal) / iLength)
                if oInf:
                    fTemp.write(oInf)
                else:
                    bCont = False
                    oProgress.destroy()
        else:
            # Just try and download
            fTemp.write(oFile.read())
        try:
            oZipFile = zipfile.ZipFile(fTemp, 'r')
            bRet = self._unzip_heart(oZipFile)
        except zipfile.BadZipfile:
            bRet = False
        # cleanup file
        fTemp.close()
        return bRet

    def _unzip_file(self, sFileName):
        """Unzip a file containing the images."""
        if _check_file(sFileName):
            try:
                oZipFile = zipfile.ZipFile(sFileName, 'r')
            except zipfile.BadZipfile:
                return False
            return self._unzip_heart(oZipFile)
        return False

    def _unzip_heart(self, oZipFile):
        """Heavy lifting of unzipping a file"""
        sPrefsPath = self.parent.config_file.get_plugin_key('card image path')
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
                    oItem.filename.replace('cardimages/',''))
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
        return False # No path, can't be OK

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
            return (self.image_frame, self._sMenuFlag)
        else:
            return None

    # pylint: disable-msg=W0613
    # oWidget needed by gtk function signature
    def replace_pane(self, oWidget):
        """Handle replacing a frame to the main window if required"""
        if self._sMenuFlag not in self.parent.dOpenFrames.values():
            oNewPane = self.parent.focussed_pane
            if oNewPane:
                self.parent.replace_frame(oNewPane, self.image_frame,
                        self._sMenuFlag)

    def add_pane(self, oWidget):
        """Handle adding the frame to the main window if required"""
        if self._sMenuFlag not in self.parent.dOpenFrames.values():
            oNewPane = self.parent.add_pane_end()
            self.parent.replace_frame(oNewPane, self.image_frame,
                    self._sMenuFlag)


# pylint: disable-msg=C0103
# shut up complaint about the name
plugin = CardImagePlugin
