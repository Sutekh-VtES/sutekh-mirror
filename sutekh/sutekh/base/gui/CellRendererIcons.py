# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Pixbuf Button CellRenderer
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Render a list of icons and text in a TreeView"""

import enum

from gi.repository import Gdk, GLib, GObject, Gtk, Pango, PangoCairo


# consts for the different display modes we need
@enum.unique
class DisplayOption(enum.Enum):
    """Possible modes for the icon renderer"""
    SHOW_TEXT_ONLY = 1
    SHOW_ICONS_ONLY = 2
    SHOW_ICONS_AND_TEXT = 3


def _layout_text(oLayout, sText):
    """Helper function to ensure consistency in calling layout"""
    oLayout.set_markup("<i>%s </i>" % GLib.markup_escape_text(sText))
    oLayout.set_alignment(Pango.Alignment.LEFT)


class CellRendererIcons(Gtk.CellRenderer):
    """Render a list of icons and text in a cell in a TreeView.

       Used to render the icons in the CardListViews
       """
    # pylint: disable=too-many-public-methods
    # Gtk widget, so we must have a lot of public methods
    # Pad constant
    iTextPad = 4

    __gproperties__ = {
        'text': (GObject.TYPE_STRING, 'text property',
                 'text to render', '', GObject.ParamFlags.READWRITE),
        'textlist': (GObject.TYPE_PYOBJECT, 'textlist property',
                     'list of text strings to render',
                     GObject.ParamFlags.READWRITE),
        'icons': (GObject.TYPE_PYOBJECT, 'icons property',
                  'icons to render', GObject.ParamFlags.READWRITE),
    }

    def __init__(self, iIconPad=2):
        super().__init__()
        self.aData = []
        self.sText = None
        self.eMode = DisplayOption.SHOW_ICONS_AND_TEXT
        self.iIconPad = iIconPad

    def do_get_property(self, oProp):
        """Allow reading the properties"""
        if oProp.name == 'icons':
            return [x[1] for x in self.aData]
        if oProp.name == 'textlist':
            return [x[0] for x in self.aData]
        if oProp.name == 'text':
            return self.sText
        raise AttributeError('unknown property %s' % oProp.name)

    def do_set_property(self, oProp, oValue):
        """Allow setting the properties"""
        # pylint: disable=too-many-branches
        # Essentially nested case statements, so many branches
        if oProp.name == 'icons':
            if oValue is None:
                # Special case
                self.aData = []
            elif isinstance(oValue, list):
                if self.aData and len(oValue) == len(self.aData):
                    self.aData = list(zip([x[0] for x in self.aData], oValue))
                else:
                    self.aData = [(None, x) for x in oValue]
            else:
                raise AttributeError(
                    'Incorrect type for icons: %s' % type(oValue))
        elif oProp.name == 'textlist':
            if oValue is None:
                # Special case
                self.aData = []
            elif isinstance(oValue, list):
                if self.aData and len(self.aData) == len(oValue):
                    self.aData = list(zip(oValue, [x[1] for x in self.aData]))
                else:
                    self.aData = [(x, None) for x in oValue]
            else:
                raise AttributeError(
                    'Incorrect type of textlist: %s' % type(oValue))
        elif oProp.name == 'text':
            # Just the text string, so no icon info possible
            self.sText = oValue
        else:
            raise AttributeError('unknown property %s' % oProp.name)

    def set_data(self, aText, aIcons, eMode=DisplayOption.SHOW_ICONS_AND_TEXT):
        """Load the info needed to render the icon"""
        self.aData = []
        if len(aIcons) != len(aText):
            # Can't handle this case
            return
        self.aData = list(zip(aText, aIcons))
        self.eMode = eMode

    def do_get_size(self, oWidget, oCellArea):
        """Handle get_size requests"""
        if not self.aData and not self.sText:
            return 0, 0, 0, 0
        iCellWidth = 0
        iCellHeight = 0
        oLayout = oWidget.create_pango_layout("")
        if self.aData:
            for sText, oIcon in self.aData:
                # Get icon dimensions
                if oIcon and self.eMode != DisplayOption.SHOW_TEXT_ONLY:
                    iCellWidth += oIcon.get_width() + self.iIconPad
                    if oIcon.get_height() > iCellHeight:
                        iCellHeight = oIcon.get_height()
                # Get text dimensions
                if sText and (self.eMode != DisplayOption.SHOW_ICONS_ONLY or oIcon is None):
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
            iXOffset = int(self.get_property("xalign") * (
                oCellArea.width - fCalcWidth - self.get_property("xpad")))
            iYOffset = int(self.get_property("yalign") * (
                oCellArea.height - fCalcHeight - self.get_property("ypad")))
        # Gtk want's ints here
        return iXOffset, iYOffset, int(fCalcWidth), int(fCalcHeight)

    # pylint: disable=too-many-arguments
    # number of parameters needed by function signature
    def do_render(self, oCairoContext, oWidget, _oBackgroundArea,
                  oCellArea, _iFlags):
        """Render the icons & text for the tree view"""
        oLayout = oWidget.create_pango_layout("")
        oPixRect = Gdk.Rectangle()
        oPixRect.x, oPixRect.y, oPixRect.width, oPixRect.height = \
            self.do_get_size(oWidget, oCellArea)
        # We want to always start at the left edge of the Cell, so this is
        # correct
        oPixRect.x = oCellArea.x
        oPixRect.y += oCellArea.y
        # xpad, ypad are floats, but Gdk.Rectangle needs int's
        oPixRect.width -= int(2 * self.get_property("xpad"))
        oPixRect.height -= int(2 * self.get_property("ypad"))
        oDrawRect = Gdk.Rectangle()
        oDrawRect.x = int(oPixRect.x)
        oDrawRect.y = int(oPixRect.y)
        oDrawRect.width = 0
        oDrawRect.height = 0
        if self.aData:
            for sText, oIcon in self.aData:
                if oIcon and self.eMode != DisplayOption.SHOW_TEXT_ONLY:
                    # Render icon
                    Gdk.cairo_set_source_pixbuf(oCairoContext,
                                                oIcon,
                                                oDrawRect.x,
                                                oDrawRect.y)
                    oCairoContext.paint()
                    oDrawRect.x += oIcon.get_width() + self.iIconPad
                if sText and (self.eMode != DisplayOption.SHOW_ICONS_ONLY or oIcon is None):
                    # Render text
                    _layout_text(oLayout, sText)
                    oDrawRect.width, oDrawRect.height = \
                        oLayout.get_pixel_size()
                    oStyleContext = oWidget.get_style_context()
                    oState = oWidget.get_state_flags()
                    oColour = oStyleContext.get_color(oState)
                    oCairoContext.set_source_rgba(oColour.red, oColour.green,
                                                  oColour.blue, oColour.alpha)
                    oCairoContext.move_to(oDrawRect.x, oDrawRect.y)
                    PangoCairo.show_layout(oCairoContext, oLayout)
                    oDrawRect.x += oDrawRect.width + self.iTextPad
        elif self.sText:
            # Render text
            _layout_text(oLayout, self.sText)
            oDrawRect.width, oDrawRect.height = oLayout.get_pixel_size()
            oStyleContext = oWidget.get_style_context()
            oState = oWidget.get_state_flags()
            oColour = oStyleContext.get_color(oState)
            oCairoContext.set_source_rgba(oColour.red, oColour.green,
                                          oColour.blue, oColour.alpha)
            oCairoContext.move_to(oDrawRect.x, oDrawRect.y)
            PangoCairo.show_layout(oCairoContext, oLayout)
            oDrawRect.x += oDrawRect.width + self.iTextPad
        return None


GObject.type_register(CellRendererIcons)
