# CardImages.py
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Adds a frame which will display card images from ARDB in the GUI"""

import gtk, gobject
import unicodedata
import os
from sutekh.core.SutekhObjects import AbstractCard, AbstractCardSet, \
                                      PhysicalCard, PhysicalCardSet
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error
from sutekh.gui.CardListView import CardListViewListener
from sutekh.gui.BasicFrame import BasicFrame
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.SutekhUtility import prefs_dir

class CardImageFrame(BasicFrame, CardListViewListener):

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


        aDragTargets = [ ('STRING', 0, 0),
                ('text/plain', 0, 0) ]

        oBox.drag_dest_set(gtk.DEST_DEFAULT_ALL,
                aDragTargets,
                gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        oBox.connect('drag-data-received', self.drag_drop_handler)
        oBox.connect('drag-motion', self.drag_motion)
        self._oImage.set_alignment(0.5, 0.5) # Centre Image

    type = property(fget=lambda self: "Card Image Frame", doc="Frame Type")

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

    def convert_cardname(self, sCardName):
        """ 
        Convert sCardName to the form used by the card image list
        """
        sFilename = self.unaccent(sCardName.lower())
        if sFilename.find('the ') == 0:
            sFilename = sFilename[4:] + 'the'
        sFilename = sFilename.replace('(advanced)','adv')
        # Should probably do this via translate
        for sChar in [" ", ".", ",", "'", "(", ")", "-", ":", "!", '"', "/"]:
            sFilename = sFilename.replace(sChar, '')
        sFilename = sFilename + '.jpg'
        return os.path.join(prefs_dir('Sutekh'), 'cardimages', sFilename)

    def check_cardname(self, sCardName):
        """
        Check if the file associated with sCardName can be found
        """
        sFullFilename = self.convert_cardname(sCardName)
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
            self._oImage.set_from_pixbuf(oPixbuf)
        except gobject.GError:
            print "Unable to load image", sFullFilename
            self._oImage.set_from_stock(gtk.STOCK_MISSING_IMAGE,
                    gtk.ICON_SIZE_DIALOG)
        self._oImage.queue_draw()

oImageFrame = None

class CardImagePlugin(CardListPlugin):
    dTableVersions = {AbstractCard : [1,2,3]}
    aModelsSupported = ["MainWindow"]
    aListenViews = [AbstractCardSet, PhysicalCardSet,
            PhysicalCard, AbstractCard]

    _sMenuFlag = 'Card Image Frame'

    def __init__(self,*args,**kws):
        super(CardImagePlugin, self).__init__(*args,**kws)
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
        """
        if not self.check_versions() or not self.check_model_type():
            return None
        if not oImageFrame.check_cardname('Acrobatics'):
            # Don't allow the menu option if we can't find the images
            return None
        self._oMenuItem = gtk.MenuItem("Replace with Card Image Frame")
        self._oMenuItem.connect("activate", self.activate)
        self.parent.add_to_menu_list('Card Image Frame',
                self.add_image_frame_active)
        return self._oMenuItem

    def add_image_frame_active(self, bValue):
        self._oMenuItem.set_sensitive(bValue)

    def get_desired_menu(self):
        return "Plugins"

    def get_frame_from_config(self, sType):
        if sType == self._sMenuFlag:
            return (oImageFrame, self._sMenuFlag)
        else:
            return None

    def activate(self, oWidget):
        if self._sMenuFlag not in self.parent.dOpenFrames.values():
            oNewPane = self.parent.focussed_pane
            if oNewPane:
                self.parent.replace_frame(oNewPane, oImageFrame, self._sMenuFlag)

plugin = CardImagePlugin
