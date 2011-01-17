# CellRendererIcons.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Pixbuf Button CellRenderer
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Render a list VTES icons and text in a TreeView"""

import gtk
import pango
import gobject

# consts for the different display modes we need
SHOW_TEXT_ONLY, SHOW_ICONS_ONLY, SHOW_ICONS_AND_TEXT = range(3)


def _layout_text(oLayout, sText):
    """Helper function to ensure consistency in calling layout"""
    oLayout.set_markup("<i>%s </i>" % gobject.markup_escape_text(sText))
    oLayout.set_alignment(pango.ALIGN_LEFT)


# pylint: disable-msg=R0904
# gtk widget, so we must have a lot of public methods
class CellRendererIcons(gtk.GenericCellRenderer):
    """Render a list of icons and text in a cell in a TreeView.

       Used to render the VTES icons in the CardListViews
       """
    # Pad constant
    iTextPad = 4

    __gproperties__ = {
            'text': (gobject.TYPE_STRING, 'text property',
                'text to render', '', gobject.PARAM_READWRITE),
            'textlist': (gobject.TYPE_PYOBJECT, 'textlist property',
                'list of text strings to render', gobject.PARAM_READWRITE),
            'icons': (gobject.TYPE_PYOBJECT, 'icons property',
                'icons to render', gobject.PARAM_READWRITE),
            }

    def __init__(self, iIconPad=2):
        super(CellRendererIcons, self).__init__()
        self.aData = []
        self.sText = None
        self.iMode = SHOW_ICONS_AND_TEXT
        self.iIconPad = iIconPad

    def do_get_property(self, oProp):
        """Allow reading the properties"""
        if oProp.name == 'icons':
            return [x[1] for x in self.aData]
        elif oProp.name == 'textlist':
            return [x[0] for x in self.aData]
        elif oProp.name == 'text':
            return self.sText
        else:
            raise AttributeError, 'unknown property %s' % oProp.name

    def do_set_property(self, oProp, oValue):
        """Allow setting the properties"""
        # pylint: disable-msg=R0912
        # Essentially nested case statements, so many branches
        if oProp.name == 'icons':
            if oValue is None:
                # Special case
                self.aData = []
            elif isinstance(oValue, list):
                if self.aData and len(oValue) == len(self.aData):
                    self.aData = zip([x[0] for x in self.aData], oValue)
                else:
                    self.aData = [(None, x) for x in oValue]
            else:
                raise AttributeError, 'Incorrect type for icons'
        elif oProp.name == 'textlist':
            if oValue is None:
                # Special case
                self.aData = []
            elif isinstance(oValue, list):
                if self.aData and len(self.aData) == len(oValue):
                    self.aData = zip(oValue, [x[1] for x in self.aData])
                else:
                    self.aData = [(x, None) for x in oValue]
            else:
                raise AttributeError, 'Incorrect type of textlist'
        elif oProp.name == 'text':
            # Just the text string, so no icon info possible
            self.sText = oValue
        else:
            raise AttributeError, 'unknown property %s' % oProp.name

    def set_data(self, aText, aIcons, iMode=SHOW_ICONS_AND_TEXT):
        """Load the info needed to render the icon"""
        self.aData = []
        if len(aIcons) != len(aText):
            # Can't handle this case
            return False
        self.aData = zip(aText, aIcons)
        self.iMode = iMode

    def on_get_size(self, oWidget, oCellArea):
        """Handle get_size requests"""
        if not self.aData and not self.sText:
            return 0, 0, 0, 0
        iCellWidth = 0
        iCellHeight = 0
        oLayout = oWidget.create_pango_layout("")
        if self.aData:
            for sText, oIcon in self.aData:
                # Get icon dimensions
                if oIcon and self.iMode != SHOW_TEXT_ONLY:
                    iCellWidth += oIcon.get_width() + self.iIconPad
                    if oIcon.get_height() > iCellHeight:
                        iCellHeight = oIcon.get_height()
                # Get text dimensions
                if sText and (self.iMode != SHOW_ICONS_ONLY or oIcon is None):
                    # always fallback to text if oIcon is None
                    _layout_text(oLayout, sText)
                    # get layout dimensions
                    iWidth, iHeight = oLayout.get_pixel_size()
                    # add padding to width
                    if iHeight > iCellHeight:
                        iCellHeight = iHeight
                    iCellWidth += iWidth + self.iTextPad
        else:
            # Get width from sText
            _layout_text(oLayout, self.sText)
            # get layout dimensions
            iWidth, iHeight = oLayout.get_pixel_size()
            # add padding to width
            if iHeight > iCellHeight:
                iCellHeight = iHeight
                iCellWidth += iWidth + self.iTextPad
        fCalcWidth = self.get_property("xpad") * 2 + iCellWidth
        fCalcHeight = self.get_property("ypad") * 2 + iCellHeight
        iXOffset = 0
        iYOffset = 0
        if oCellArea is not None and iCellWidth > 0 and iCellHeight > 0:
            iXOffset = int(self.get_property("xalign") * (oCellArea.width - \
                fCalcWidth - self.get_property("xpad")))
            iYOffset = int(self.get_property("yalign") * (oCellArea.height - \
                fCalcHeight - self.get_property("ypad")))
        # gtk want's ints here
        return iXOffset, iYOffset, int(fCalcWidth), int(fCalcHeight)

    # pylint: disable-msg=R0913
    # R0913 - number of parameters needed by function signature
    def on_render(self, oWindow, oWidget, _oBackgroundArea,
            oCellArea, oExposeArea, _iFlags):
        """Render the icons & text for the tree view"""
        oLayout = oWidget.create_pango_layout("")
        oPixRect = gtk.gdk.Rectangle()
        oPixRect.x, oPixRect.y, oPixRect.width, oPixRect.height = \
            self.on_get_size(oWidget, oCellArea)
        # We want to always start at the left edge of the Cell, so this is
        # correct
        oPixRect.x = oCellArea.x
        oPixRect.y += oCellArea.y
        # xpad, ypad are floats, but gtk.gdk.Rectangle needs int's
        oPixRect.width -= int(2 * self.get_property("xpad"))
        oPixRect.height -= int(2 * self.get_property("ypad"))
        oDrawRect = gtk.gdk.Rectangle()
        oDrawRect.x = int(oPixRect.x)
        oDrawRect.y = int(oPixRect.y)
        oDrawRect.width = 0
        oDrawRect.height = 0
        if self.aData:
            for sText, oIcon in self.aData:
                if oIcon and self.iMode != SHOW_TEXT_ONLY:
                    # Render icon
                    oDrawRect.width = oIcon.get_width()
                    oDrawRect.height = oIcon.get_height()
                    oIconDrawRect = oCellArea.intersect(oDrawRect)
                    oIconDrawRect = oExposeArea.intersect(oIconDrawRect)
                    oWindow.draw_pixbuf(oWidget.style.black_gc, oIcon,
                            oIconDrawRect.x - oDrawRect.x,
                            oIconDrawRect.y - oDrawRect.y, oIconDrawRect.x,
                            oIconDrawRect.y, -1, oIconDrawRect.height,
                            gtk.gdk.RGB_DITHER_NONE, 0, 0)
                    oDrawRect.x += oIcon.get_width() + self.iIconPad
                if sText and (self.iMode != SHOW_ICONS_ONLY or oIcon is None):
                    # Render text
                    _layout_text(oLayout, sText)
                    oDrawRect.width, oDrawRect.height = \
                            oLayout.get_pixel_size()
                    oWindow.draw_layout(oWidget.style.black_gc, oDrawRect.x,
                            oDrawRect.y, oLayout)
                    oDrawRect.x += oDrawRect.width + self.iTextPad
        elif self.sText:
            # Render text
            _layout_text(oLayout, self.sText)
            oDrawRect.width, oDrawRect.height = oLayout.get_pixel_size()
            oWindow.draw_layout(oWidget.style.black_gc, oDrawRect.x,
                    oDrawRect.y, oLayout)
            oDrawRect.x += oDrawRect.width + self.iTextPad
        return None


gobject.type_register(CellRendererIcons)
