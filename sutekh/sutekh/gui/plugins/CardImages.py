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
                                      PhysicalCard, PhysicalCardSet
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.CardListView import CardListViewListener
from sutekh.gui.BasicFrame import BasicFrame
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_buttons
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.SutekhUtility import prefs_dir

class CardImageFrame(BasicFrame, CardListViewListener):
    # pylint: disable-msg=R0901,R0904
    # can't not trigger these warning with pygtk
    """
    Frame which displays the image.
    We wrap a gtk.Image in an EventBox (for focus & DnD events)
    and a Viewport (for scrolling)
    """

    def __init__(self, oMainWindow, oConfigFile):
        super(CardImageFrame, self).__init__(oMainWindow)
        self._oConfigFile = oConfigFile
        oBox = gtk.EventBox()
        oViewport = gtk.Viewport()
        oViewport.add(oBox)
        self._oView = AutoScrolledWindow(oViewport)
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

        self._oImage.set_alignment(0.5, 0.5) # Centre image

        self.sPrefsPath = self._oConfigFile.get_plugin_key('card image path')
        if self.sPrefsPath is None:
            self.sPrefsPath = os.path.join(prefs_dir('Sutekh'), 'cardimages')
            self._oConfigFile.set_plugin_key('card image path', self.sPrefsPath)

    type = property(fget=lambda self: "Card Image Frame", doc="Frame Type")

    def update_config_path(self, sNewPath):
        self.sPrefsPath = sNewPath
        self._oConfigFile.set_plugin_key('card image path', sNewPath)

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

    def convert_cardname(self, sCardName, sTestPath=''):
        """ 
        Convert sCardName to the form used by the card image list
        """
        sFilename = self.unaccent(sCardName.lower())
        if sFilename.find('the ') == 0:
            sFilename = sFilename[4:] + 'the'
        sFilename = sFilename.replace('(advanced)', 'adv')
        # Should probably do this via translate
        for sChar in [" ", ".", ",", "'", "(", ")", "-", ":", "!", '"', "/"]:
            sFilename = sFilename.replace(sChar, '')
        sFilename = sFilename + '.jpg'
        if sTestPath == '':
            return os.path.join(self.sPrefsPath, sFilename)
        else:
            return os.path.join(sTestPath, sFilename)

    def check_cardname(self, sCardName, sTestPath=''):
        """
        Check if the file associated with sCardName can be found
        """
        sFullFilename = self.convert_cardname(sCardName, sTestPath)
        bRes = True
        try:
            fTest = file(sFullFilename, 'rb')
            fTest.close()
        except IOError:
            bRes = False
        return bRes

    def set_card_text(self, sCardName):
        """
        Set the image in response to a set card name event
        """
        sFullFilename = self.convert_cardname(sCardName)
        try:
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
            print "Unable to load image", sFullFilename
            self._oImage.set_from_stock(gtk.STOCK_MISSING_IMAGE,
                    gtk.ICON_SIZE_DIALOG)
        self._oImage.queue_draw()

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
        if not oImageFrame.check_cardname('Acrobatics'):
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
        oDesc = gtk.Label('Choose directory containing the card images')
        oDialog.vbox.pack_start(oDesc)
        oFileWidget = gtk.FileChooserWidget(
                action=gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER)
        oDialog.vbox.pack_start(oFileWidget)
        sPrefsPath = self.parent.config_file.get_plugin_key('card image path')
        if sPrefsPath is not None:
            oFileWidget.set_current_name(sPrefsPath)
            oFileWidget.set_current_folder(sPrefsPath)
        oDialog.show_all()
        iResponse = oDialog.run()
        if iResponse == gtk.RESPONSE_OK:
            sTestPath = oFileWidget.get_filename()
            if sTestPath is not None:
                # Test if path is OK
                if not os.path.exists(sTestPath):
                    iQuery = do_complaint_buttons(
                            "Folder does not exist\n"
                            "Create it?", gtk.MESSAGE_QUESTION,
                            (gtk.STOCK_YES, gtk.RESPONSE_YES,
                                gtk.STOCK_NO, gtk.RESPONSE_NO))
                    if iQuery == gtk.RESPONSE_NO:
                        # treat as canceling
                        oDialog.destroy()
                        return
                    else:
                        os.makedirs(sTestPath)
                elif not oImageFrame.check_cardname('Acrobatics', sTestPath):
                    iQuery = do_complaint_buttons(
                            "Folder does not seem to contain images\n"
                            "Are you sure?", gtk.MESSAGE_QUESTION,
                            (gtk.STOCK_YES, gtk.RESPONSE_YES,
                                gtk.STOCK_NO, gtk.RESPONSE_NO))
                    if iQuery == gtk.RESPONSE_NO:
                        # treat as canceling
                        oDialog.destroy()
                        return
                # Update preferences
                oImageFrame.update_config_path(sTestPath)
                if self._sMenuFlag not in self.parent.dOpenFrames.values():
                    # Pane is not open, so try to enable menu
                    self.add_image_frame_active(True)
        oDialog.destroy()

    def add_image_frame_active(self, bValue):
        """
        Toggle the sensitivity of the menu item
        """
        if bValue and not oImageFrame.check_cardname('Acrobatics'):
            # Can only be set true if check_cardname returns true
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
