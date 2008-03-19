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

class CardImageFrame(BasicFrame, CardListViewListener):
    # pylint: disable-msg=R0901, R0904
    # can't not trigger these warning with pygtk
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
        self.bShowExpansions = False

        # Enable DnD handling, same as for BasicFrame
        aDragTargets = [ ('STRING', 0, 0),
                ('text/plain', 0, 0) ]
        oBox.drag_dest_set(gtk.DEST_DEFAULT_ALL,
                aDragTargets,
                gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
        oBox.connect('drag-data-received', self.drag_drop_handler)
        oBox.connect('drag-motion', self.drag_motion)
        oBox.connect('button-press-event', self.cycle_expansion)

        self._oImage.set_alignment(0.5, 0.5) # Centre image

        self.sPrefsPath = self._oConfigFile.get_plugin_key('card image path')
        if self.sPrefsPath is None:
            self.sPrefsPath = os.path.join(prefs_dir('Sutekh'), 'cardimages')
            self._oConfigFile.set_plugin_key('card image path', self.sPrefsPath)
        self.bShowExpansions = self.have_expansions()
        self.sCurExpansion = ''
        self.aExpansions = []
        self.iExpansionPos = 0
        self.sCardName = ''

    type = property(fget=lambda self: "Card Image Frame", doc="Frame Type")

    def have_expansions(self, sTestPath=''):
        """
        Test if directory contains expansion/image structure used by ARDB
        """
        if sTestPath == '':
            sTestFile = os.path.join(self.sPrefsPath, 'bh', 'acrobatics.jpg')
        else:
            sTestFile = os.path.join(sTestPath, 'bh', 'acrobatics.jpg')
        return check_file(sTestFile)

    def check_images(self, sTestPath=''):
        """Check if dir contains images in the right structure"""
        self.bShowExpansions = self.have_expansions(sTestPath)
        if self.bShowExpansions:
            return True
        if sTestPath == '':
            sTestFile = os.path.join(self.sPrefsPath, 'acrobatics.jpg')
        else:
            sTestFile = os.path.join(sTestPath, 'acrobatics.jpg')
        return check_file(sTestFile)

    def update_config_path(self, sNewPath):
        "Update the path we use to search for expansions"
        self.sPrefsPath = sNewPath
        self._oConfigFile.set_plugin_key('card image path', sNewPath)
        self.bShowExpansions = self.have_expansions()

    def unaccent(self, sCardName):
        """
        Remove unicode accents
        """
        # Inspired by a post by renaud turned up by google
        # Unicode Normed decomposed form
        sNormed = unicodedata.normalize('NFD',
                unicode(sCardName.encode('utf8'), encoding='utf-8'))
        # Drop non-ascii characters
        return "".join(b for b in sNormed.encode('utf8') if ord(b) < 128)

    def convert_expansion(self, sExpansionName):
        "Convert the Full Expansion name into the abbrevation needed"
        if sExpansionName == '':
            return ''
        oExpansion = IExpansion(sExpansionName)
        return oExpansion.shortname.lower()

    def set_expansion_info(self, sCardName):
        "Set the expansion info"
        oAbsCard = IAbstractCard(sCardName)
        if len(oAbsCard.rarity) > 0:
            aExp = [oP.expansion.name for oP in oAbsCard.rarity]
            self.aExpansions = list(set(aExp)) # remove duplicates
            self.sCurExpansion = self.aExpansions[0] 
            self.iExpansionPos = 0
        else:
            self.sCurExpansion = ''
            self.aExpansions = []
            self.iExpansionPos = 0

    def convert_cardname(self, sCardName, sTestPath=''):
        """
        Convert sCardName to the form used by the card image list
        """
        if self.bShowExpansions:
            if sCardName != self.sCardName:
                self.set_expansion_info(sCardName)
                self.sCardName = sCardName
            if self.sCurExpansion == '' and len(self.aExpansions) > 0:
                self.sCurExpansion = self.aExpansions[0]
                self.iExpansionPos = 0
            sCurExpansionPath = self.convert_expansion(self.sCurExpansion)
        else:
            sCurExpansionPath = ''
        sFilename = self.unaccent(sCardName.lower())
        if sFilename.find('the ') == 0:
            sFilename = sFilename[4:] + 'the'
        sFilename = sFilename.replace('(advanced)', 'adv')
        # Should probably do this via translate
        for sChar in [" ", ".", ",", "'", "(", ")", "-", ":", "!", '"', "/"]:
            sFilename = sFilename.replace(sChar, '')
        sFilename = sFilename + '.jpg'
        if sTestPath == '':
            return os.path.join(self.sPrefsPath, sCurExpansionPath, sFilename)
        else:
            return os.path.join(sTestPath, sCurExpansionPath, sFilename)

    def set_card_text(self, sCardName, sExpansionName=''):
        """
        Set the image in response to a set card name event
        """
        self.sCurExpansion = sExpansionName
        sFullFilename = self.convert_cardname(sCardName)
        self.load_image(sFullFilename)

    def load_image(self, sFullFilename):
        "Load an image into the pane, show broken image if needed"
        try:
            if self.bShowExpansions:
                self.oExpansionLabel.set_markup('<i>Image from expansion : </i>'
                        ' %s' % self.sCurExpansion)
                self.oExpansionLabel.show()
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

    def cycle_expansion(self, oWidget, oEvent):
        "On a button click, move to the next expansion"
        bRedraw = False
        if len(self.aExpansions) < 2:
            return # nothing to scroll through
        if oEvent.button == 1:
            # left button
            self.iExpansionPos += 1
            if self.iExpansionPos >= len(self.aExpansions):
                self.iExpansionPos = 0
            bRedraw = True
        elif oEvent.button == 3:
            # Right button, go backwards
            self.iExpansionPos -= 1
            if self.iExpansionPos < 0:
                self.iExpansionPos += len(self.aExpansions)
            bRedraw = True
        if bRedraw:
            self.sCurExpansion = self.aExpansions[self.iExpansionPos]
            self.set_card_text(self.sCardName, self.sCurExpansion)

oImageFrame = None

class CardImagePlugin(CardListPlugin):
    """
    Plugin providing access to CardImageFrame
    """
    dTableVersions = {AbstractCard : [1, 2, 3]}
    aModelsSupported = ["MainWindow"]
    aListenViews = [AbstractCardSet, PhysicalCardSet,
            PhysicalCard, AbstractCard]

    _sMenuFlag = 'Card Image Frame'

    # pylint: disable-msg=W0142
    # ** magic OK here
    def __init__(self, *aArgs, **kwargs):
        super(CardImagePlugin, self).__init__(*aArgs, **kwargs)
        # Add listeners to the appropriate views
        global oImageFrame
        if not oImageFrame:
            oImageFrame = CardImageFrame(self.parent, self.parent.config_file)
            oImageFrame.set_title(self._sMenuFlag)
            oImageFrame.add_parts()
        if self._cModelType in self.aListenViews:
            self.view.add_listener(oImageFrame)
        self._oMenuItem = None

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
        if not oImageFrame.check_images():
            # Don't allow the menu option if we can't find the images
            self.add_image_frame_active(False)
        return self._oConfigMenuItem, self._oMenuItem

    def config_activate(self, oMenuWidget):
        """
        Configure the plugin dialog
        """
        oDialog = SutekhDialog('Configure Card Images Plugin', self.parent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL,
                    gtk.RESPONSE_CANCEL))
        oDescLabel = gtk.Label()
        oDescLabel.set_markup('<b>Choose how to configure the cardimages'
                ' plugin</b>')
        oChoiceDownload = gtk.RadioButton(
                label='Download and install cardimages from feldb.extra.hu')
        # Download and install http://feldb.extra.hu/pictures.zip
        oChoiceLocalCopy = gtk.RadioButton(oChoiceDownload,
                label='Install images from a local zip file')
        oChoiceNewDir = gtk.RadioButton(oChoiceDownload,
                label='Choose a directory containing the images')
        oChoiceBox = gtk.VBox(False, 2)
        oDirChoiceWidget = gtk.FileChooserWidget(
                action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        oFileChoiceWidget = gtk.FileChooserWidget(
                action=gtk.FILE_CHOOSER_ACTION_OPEN)
        oChoiceDownload.connect('toggled', self._radio_toggled, oDialog,
                oChoiceBox, None)
        oChoiceLocalCopy.connect('toggled', self._radio_toggled, oDialog,
                oChoiceBox, oFileChoiceWidget)
        oChoiceNewDir.connect('toggled', self._radio_toggled, oDialog,
                oChoiceBox, oDirChoiceWidget)

        oChoiceDownload.set_active(True)
        # pylint: disable-msg=E1101
        # pylint doesn't pick up vbox methods correctly
        oDialog.vbox.pack_start(oDescLabel, False, False)
        oDialog.vbox.pack_start(oChoiceDownload, False, False)
        oDialog.vbox.pack_start(oChoiceLocalCopy, False, False)
        oDialog.vbox.pack_start(oChoiceNewDir, False, False)
        oDialog.vbox.pack_start(oChoiceBox)
        oDialog.set_size_request(600, 600)

        #oDialog.vbox.pack_start(oFileWidget)
        sPrefsPath = self.parent.config_file.get_plugin_key('card image path')
        if sPrefsPath is not None:
            if os.path.exists(sPrefsPath) and os.path.isdir(sPrefsPath):
                # File widget doesn't like being pointed at non-dirs
                # when in SELECT_FOLDER mode
                oDirChoiceWidget.set_current_folder(sPrefsPath)
        oZipFilter = gtk.FileFilter()
        oZipFilter.add_pattern('*.zip')
        oZipFilter.add_pattern('*.ZIP')
        oFileChoiceWidget.add_filter(oZipFilter)
        oDialog.show_all()
        iResponse = oDialog.run()
        if iResponse == gtk.RESPONSE_OK:
            if oChoiceDownload.get_active():
                # TODO: download the images
                pass
            elif oChoiceLocalCopy.get_active():
                # TODO: unzip the file
                pass
            else: 
                sTestPath = oDirChoiceWidget.get_filename()
                if sTestPath is not None:
                    # Test if path has images
                    if not oImageFrame.check_images(sTestPath):
                        iQuery = do_complaint_buttons(
                                "Folder does not seem to contain images\n"
                                "Are you sure?", gtk.MESSAGE_QUESTION,
                                (gtk.STOCK_YES, gtk.RESPONSE_YES,
                                    gtk.STOCK_NO, gtk.RESPONSE_NO))
                        if iQuery == gtk.RESPONSE_NO:
                            # treat as canceling
                            oImageFrame.check_images() # reset bHaveExpansions
                            oDialog.destroy()
                            return
                    # Update preferences
                    oImageFrame.update_config_path(sTestPath)
                    if self._sMenuFlag not in self.parent.dOpenFrames.values():
                        # Pane is not open, so try to enable menu
                        self.add_image_frame_active(True)
        oDialog.destroy()

    def _radio_toggled(self, oRadioButton, oDialog, oChoiceBox, oFileWidget):
        "Display the correct file widget when radio buttons change"
        if oRadioButton.get_active():
            for oChild in oChoiceBox.get_children():
                oChoiceBox.remove(oChild)
            if oFileWidget:
                oChoiceBox.pack_start(oFileWidget)
            oDialog.show_all()

    def add_image_frame_active(self, bValue):
        """
        Toggle the sensitivity of the menu item
        """
        if bValue and not oImageFrame.check_images():
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
            return (oImageFrame, self._sMenuFlag)
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
                self.parent.replace_frame(oNewPane, oImageFrame,
                        self._sMenuFlag)

# pylint: disable-msg=C0103
# shut up complaint about the name
plugin = CardImagePlugin
