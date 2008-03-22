# CardImages.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Adds a frame which will display card images from ARDB in the GUI"""

import gtk, gobject
import unicodedata
import os
from sutekh.core.SutekhObjects import AbstractCard, AbstractCardSet, \
                                      PhysicalCard, PhysicalCardSet, \
                                      IAbstractCard, IExpansion
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.CardListView import CardListViewListener
from sutekh.gui.BasicFrame import BasicFrame
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_buttons
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.SutekhUtility import prefs_dir

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
    """
    Remove unicode accents
    """
    # Inspired by a post by renaud turned up by google
    # Unicode Normed decomposed form
    sNormed = unicodedata.normalize('NFD',
            unicode(sCardName.encode('utf8'), encoding='utf-8'))
    # Drop non-ascii characters
    return "".join(b for b in sNormed.encode('utf8') if ord(b) < 128)

class CardImageFrame(BasicFrame, CardListViewListener):
    # pylint: disable-msg=R0901, R0904, R0902
    # R0901, R0904 - can't not trigger these warning with pygtk
    # R0902 - we need to keep quite a lot of internal state
    """
    Frame which displays the image.
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

        self._oImage.set_alignment(0.5, 0.5) # Centre image

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

    type = property(fget=lambda self: "Card Image Frame", doc="Frame Type")

    def __have_expansions(self, sTestPath=''):
        """
        Test if directory contains expansion/image structure used by ARDB
        """
        if sTestPath == '':
            sTestFile = os.path.join(self.__sPrefsPath, 'bh', 'acrobatics.jpg')
        else:
            sTestFile = os.path.join(sTestPath, 'bh', 'acrobatics.jpg')
        return check_file(sTestFile)

    def __convert_expansion(self, sExpansionName):
        "Convert the Full Expansion name into the abbrevation needed"
        if sExpansionName == '' or not self.__bShowExpansions:
            return ''
        # pylint: disable-msg=E1101
        # pylint doesn't pick up IExpansion methods correctly
        oExpansion = IExpansion(sExpansionName)
        return oExpansion.shortname.lower()

    def __set_expansion_info(self, sCardName):
        "Set the expansion info"
        # pylint: disable-msg=E1101
        # pylint doesn't pick up IAbstractCard methods correctly
        oAbsCard = IAbstractCard(sCardName)
        if len(oAbsCard.rarity) > 0:
            aExp = [oP.expansion.name for oP in oAbsCard.rarity]
            self.__aExpansions = list(set(aExp)) # remove duplicates
            self.__iExpansionPos = 0
            self.__sCurExpansion = self.__aExpansions[0]
        else:
            self.__sCurExpansion = ''
            self.__aExpansions = []
            self.__iExpansionPos = 0

    def __convert_cardname(self):
        """
        Convert sCardName to the form used by the card image list
        """
        sCurExpansionPath = self.__convert_expansion(self.__sCurExpansion)
        sFilename = unaccent(self.__sCardName.lower())
        if sFilename.find('the ') == 0:
            sFilename = sFilename[4:] + 'the'
        sFilename = sFilename.replace('(advanced)', 'adv')
        # Should probably do this via translate
        for sChar in [" ", ".", ",", "'", "(", ")", "-", ":", "!", '"', "/"]:
            sFilename = sFilename.replace(sChar, '')
        sFilename = sFilename + '.jpg'
        return os.path.join(self.__sPrefsPath, sCurExpansionPath, sFilename)

    def __load_image(self, sFullFilename):
        "Load an image into the pane, show broken image if needed"
        try:
            if self.__bShowExpansions:
                self.oExpansionLabel.set_markup('<i>Image from expansion : </i>'
                        ' %s' % self.__sCurExpansion)
                self.oExpansionLabel.show()
            else:
                self.oExpansionLabel.hide() # config chanes can cause this
            oPixbuf = gtk.gdk.pixbuf_new_from_file(sFullFilename)
            iWidth = oPixbuf.get_width()
            iHeight = oPixbuf.get_height()
            # We scale images larger than 300 wide or 410 high
            if iWidth > 300 or iHeight > 410:
                # We want to scale image to match 300x400 (because the
                # igure neater than 300/410) as closely as
                # possible without changing the aspect ratio
                fAspectRatio = float(iWidth)/float(iHeight)
                if fAspectRatio > 0.75:
                    # Wider aspect than 300x400
                    iDestWidth = 300
                    iDestHeight = int(300/fAspectRatio)
                elif fAspectRatio < 0.75:
                    iDestHeight = 400
                    iDestWidth = int(400*fAspectRatio)
                else:
                    iDestHeight = 400
                    iDestWidth = 300
                self._oImage.set_from_pixbuf(oPixbuf.scale_simple(iDestWidth,
                    iDestHeight, gtk.gdk.INTERP_HYPER))
            else:
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
        return check_file(sTestFile)

    def update_config_path(self, sNewPath):
        "Update the path we use to search for expansions"
        self.__sPrefsPath = sNewPath
        self._oConfigFile.set_plugin_key('card image path', sNewPath)
        self.__bShowExpansions = self.__have_expansions()

    def set_card_text(self, sCardName, sExpansionName=''):
        """
        Set the image in response to a set card name event
        """
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
        sFullFilename = self.__convert_cardname()
        self.__load_image(sFullFilename)


    # pylint: disable-msg=W0613
    # oWidget needed by gtk function signature
    def __cycle_expansion(self, oWidget, oEvent):
        "On a button click, move to the next expansion"
        bRedraw = False
        if len(self.__aExpansions) < 2:
            return True # nothing to scroll through
        if oEvent.type != gtk.gdk.BUTTON_PRESS:
            return True # don't jump twice on double or triple clicks
        if oEvent.button == 1:
            # left button, go forward
            self.__iExpansionPos += 1
            if self.__iExpansionPos >= len(self.__aExpansions):
                self.__iExpansionPos = 0
            bRedraw = True
        elif oEvent.button == 3:
            # Right button, go backwards
            self.__iExpansionPos -= 1
            if self.__iExpansionPos < 0:
                self.__iExpansionPos += len(self.__aExpansions)
            bRedraw = True
        if bRedraw:
            self.__sCurExpansion = self.__aExpansions[self.__iExpansionPos]
            sFullFilename = self.__convert_cardname()
            self.__load_image(sFullFilename)
        return True

# pylint: disable-msg=R0904
# R0904 - gtk Widget, so has many public methods
class ImageConfigDialog(SutekhDialog):
    """
    Dialog for configuring the Image plugin
    """
    def __init__(self, oParent):
        super(ImageConfigDialog, self).__init__('Configure Card Images Plugin',
                oParent, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL,
                    gtk.RESPONSE_CANCEL))
        oDescLabel = gtk.Label()
        oDescLabel.set_markup('<b>Choose how to configure the cardimages'
                ' plugin</b>')
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
        "Display the correct file widget when radio buttons change"
        if oRadioButton.get_active():
            for oChild in oChoiceBox.get_children():
                oChoiceBox.remove(oChild)
            if oFileWidget:
                oChoiceBox.pack_start(oFileWidget)
            self.show_all()

    def get_path(self):
        "Get the path from oDirChoiceWidget"
        return self.oDirChoiceWidget.get_filename()

    def get_file(self):
        "Get the file from oFileChoiceWidget"
        return self.oFileChoiceWidget.get_filename()

    def get_choice(self):
        "Get which of the RadioButtons was active"
        if self.oChoiceDownload.get_active():
            return 'Download'
        elif self.oChoiceLocalCopy.get_active():
            return 'Local copy'
        else:
            return 'New directory'

class CardImagePlugin(CardListPlugin):
    """
    Plugin providing access to CardImageFrame
    """
    dTableVersions = {AbstractCard : [1, 2, 3]}
    aModelsSupported = ["MainWindow"]
    aListenViews = [AbstractCardSet, PhysicalCardSet,
            PhysicalCard, AbstractCard]

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
        self._oMenuItem = None
        self._oConfigMenuItem = None

    image_frame = property(fget=lambda self: self.get_image_frame(),
            doc="The image frame")

    @classmethod
    def get_image_frame(cls):
        "Return the global ImageFrame"
        return cls.oImageFrame

    @classmethod
    def init_image_frame(cls, oCur):
        "Setup the global image frame"
        if not cls.oImageFrame:
            cls.oImageFrame = CardImageFrame(oCur.parent,
                    oCur.parent.config_file)
            cls.oImageFrame.set_title(cls._sMenuFlag)
            cls.oImageFrame.add_parts()

    def get_menu_item(self):
        """
        Overrides method from base class.
        Adds the menu item on the MainWindow if the images
        can be found.
        """
        if not self.check_versions() or not self.check_model_type():
            return None
        self._oMenuItem = gtk.MenuItem("Replace with Card Image Frame")
        self._oMenuItem.connect("activate", self.activate)
        self.parent.add_to_menu_list('Card Image Frame',
                self.add_image_frame_active)
        self._oConfigMenuItem = gtk.MenuItem("Configure Card Images Plugin")
        self._oConfigMenuItem.connect("activate", self.config_activate)
        if not self.image_frame.check_images():
            # Don't allow the menu option if we can't find the images
            self.add_image_frame_active(False)
        return self._oConfigMenuItem, self._oMenuItem

    # pylint: disable-msg=W0613
    # oMenuWidget needed by gtk function signature
    def config_activate(self, oMenuWidget):
        """
        Configure the plugin dialog
        """
        oDialog = ImageConfigDialog(self.parent)
        iResponse = oDialog.run()
        bActivateMenu = False
        if iResponse == gtk.RESPONSE_OK:
            sChoice = oDialog.get_choice()
            if sChoice == 'Download':
                sFileName = self._download_file()
                if sFileName != '' and self._unzip_file(sFileName):
                    bActivateMenu = True
                # Cleanup temporary file
            elif sChoice == 'Local copy':
                sFileName = oDialog.get_file()
                if self._unzip_file(sFileName):
                    bActivateMenu = True
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
        "Download a zip file containing the images"
        # Download and install http://feldb.extra.hu/pictures.zip
        # TODO: download the images
        return ''

    def _unzip_file(self, sFileName):
        "Unzip a file containing the images"
        if sFileName == '':
            return False # failed download
        # Check file exists
        # TODO: unzip the file
        return False

    def _accept_path(self, sTestPath):
        "Check if the path from user is OK"
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
        """
        Toggle the sensitivity of the menu item
        """
        if bValue and not self.image_frame.check_images():
            # Can only be set true if check_images returns true
            self._oMenuItem.set_sensitive(False)
        else:
            self._oMenuItem.set_sensitive(bValue)

    def get_desired_menu(self):
        'Attach to the default Plugin menu'
        return "Plugins"

    def get_frame_from_config(self, sType):
        """
        Add the frame if it's been saved in the config file
        """
        if sType == self._sMenuFlag:
            return (self.image_frame, self._sMenuFlag)
        else:
            return None

    # pylint: disable-msg=W0613
    # oWidget needed by gtk function signature
    def activate(self, oWidget):
        """
        Handle adding the frame to the main window if required
        """
        if self._sMenuFlag not in self.parent.dOpenFrames.values():
            oNewPane = self.parent.focussed_pane
            if oNewPane:
                self.parent.replace_frame(oNewPane, self.image_frame,
                        self._sMenuFlag)

# pylint: disable-msg=C0103
# shut up complaint about the name
plugin = CardImagePlugin
