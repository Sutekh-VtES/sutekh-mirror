# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Pixbuf Button CellRenderer
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Render a icon in a TreeView"""


import logging

from gi.repository import Gdk, GLib, GObject, Gtk

# This is heavily cribbed from the example in the pyGtk FAQ
# (By Nikos Kouremenos)
# limited to the use of icons only ATM
# Allows creation of a cell containing a icon pixbuf,
# and returns a "clicked" signal when activated
# To be generically useful, should be extended to abitary pixmaps,
# but that is currently not a priority


def _safe_load(oIconTheme, sName):
    """Wrap loading the icon in a try..except block to catch failures"""
    try:
        return oIconTheme.load_icon(sName, Gtk.IconSize.MENU, 0)
    except GLib.Error as oErr:
        logging.warning("Unable to load icon %s - %s", sName, oErr)
    return None


class CellRendererSutekhButton(Gtk.CellRenderer):
    """Render a icon in a cell in a TreeView.

       Used to render the arrows for incrementing and decrementing cards
       in the CardListView's
       """
    # pylint: disable=too-many-public-methods
    # Gtk widget, so we must have a lot of public methods
    # Register a showicon property - used to control wether the icon
    # is visible or not
    __gproperties__ = {
        'showicon': (GObject.TYPE_BOOLEAN, 'showicon property',
                     'whether to show the icon', 0,
                     GObject.ParamFlags.READWRITE),
    }

    def __init__(self, bShowIcon=False):
        super().__init__()
        #self.__GObject_init__()
        self.oPixbuf = None
        self.set_property("mode", Gtk.CellRendererMode.ACTIVATABLE)
        self.bShowIcon = bShowIcon
        self.bClicked = False
        self.oClickedBackgroundArea = None

    def load_icon(self, sName, _oWidget):
        """Load the icon specified in name"""
        oIconTheme = Gtk.IconTheme.get_default()
        self.oPixbuf = _safe_load(oIconTheme, sName)
        if not self.oPixbuf:
            # try fallback to symbolic version
            # This isn't always going to work, but it is available for some
            # icons, so it's worth trying
            self.oPixbuf = _safe_load(oIconTheme, sName + '-symbolic')
        if not self.oPixbuf:
            # This is supposed to always be there, so we don't wrap it in
            # safe load. If this fails, we're arguably in enough trouble
            # anyway that we should just bail out regardless
            self.oPixbuf = oIconTheme.load_icon('image-missing',
                                                Gtk.IconSize.MENU, 0)

    def do_get_property(self, oProp):
        """Allow reading the showicon property"""
        if oProp.name == 'showicon':
            return self.bShowIcon
        raise AttributeError('unknown property %s' % oProp.name)

    def do_set_property(self, oProp, oValue):
        """Allow setting the showicon property"""
        if oProp.name == 'showicon':
            self.bShowIcon = oValue
        else:
            raise AttributeError('unknown property %s' % oProp.name)

    def do_get_size(self, _oWidget, oCellArea):
        """Handle get_size requests"""
        if self.oPixbuf is None:
            return 0, 0, 0, 0
        iPixbufWidth = self.oPixbuf.get_width()
        iPixbufHeight = self.oPixbuf.get_height()
        fCalcWidth = self.get_property("xpad") * 2 + iPixbufWidth
        fCalcHeight = self.get_property("ypad") * 2 + iPixbufHeight
        iXOffset = 0
        iYOffset = 0
        if oCellArea is not None and iPixbufWidth > 0 and iPixbufHeight > 0:
            iXOffset = int(self.get_property("xalign") * (
                oCellArea.width - fCalcWidth - self.get_property("xpad")))
            iYOffset = int(self.get_property("yalign") * (
                oCellArea.height - fCalcHeight - self.get_property("ypad")))
        # Gtk want's ints here
        return iXOffset, iYOffset, int(fCalcWidth), int(fCalcHeight)

    # pylint: disable=too-many-arguments
    # number of parameters needed by function signature
    def do_activate(self, _oEvent, _oWidget, oPath, oBackgroundArea,
                    _oCellArea, _iFlags):
        """Activate signal received from the TreeView"""
        # Note that we need to offset button
        self.bClicked = True
        self.oClickedBackgroundArea = oBackgroundArea
        # clicked callback should be called
        self.emit('clicked', oPath)
        return True

    # pylint: disable=too-many-arguments
    # number of parameters needed by function signature
    def do_render(self, oCairoContext, oWidget, oBackgroundArea,
                  oCellArea, _iFlags):
        """Render the icon for the button"""
        bDrawOffset = False
        # Need to ensure that self.bClicked is unset before any early return
        if self.bClicked:
            # Offset when button is clicked
            if oBackgroundArea.x == self.oClickedBackgroundArea.x and \
                    oBackgroundArea.y == self.oClickedBackgroundArea.y:
                # Rendering the same area as was clicked, so we need to offset
                bDrawOffset = True
                # reset clicked state
                self.bClicked = False
        if self.oPixbuf is None:
            return None
        if not self.bShowIcon:
            # Draw nothing
            return None
        oPixRect = Gdk.Rectangle()
        oPixRect.x, oPixRect.y, oPixRect.width, oPixRect.height = \
            self.do_get_size(oWidget, oCellArea)

        oPixRect.x += oCellArea.x
        oPixRect.y += oCellArea.y
        # xpad, ypad are floats, but Gdk.Rectangle needs int's
        oPixRect.width -= int(2 * self.get_property("xpad"))
        oPixRect.height -= int(2 * self.get_property("ypad"))

        if bDrawOffset:
            oPixRect.x += 1
            oPixRect.y += 1
            # We add a timeout to force a redraw to unbump the button
            GObject.timeout_add(200, self.restore_offset, oWidget.get_window(),
                                oBackgroundArea)

        oDrawRect = oCellArea.intersect(oPixRect)[1]

        Gdk.cairo_set_source_pixbuf(oCairoContext,
                                    self.oPixbuf,
                                    oDrawRect.x,
                                    oDrawRect.y)
        oCairoContext.paint()
        return None

    def restore_offset(self, oWindow, oArea):
        """queue a redraw so we restore the button."""
        # Don't unbump if the user has clicked again
        if not self.bClicked:
            # queue a redraw
            oWindow.invalidate_rect(oArea, False)


# HouseKeeping work for CellRendererStukehButton
# Awkward stylistically, but I'm putting it here as it's
# associated with class creation (is global to the class)
# so doesn't belong in the per-instance constructor - NM
# Register class, needed to make clicked signal go to right class
# (otherwise it gets associated with CellRenderer, which is
# not desireable)
GObject.type_register(CellRendererSutekhButton)
# Setup clicked signal -- can also be done using the __gsignals__
# dict in the class, but I couldn't find good documentation for
# that approach.
GObject.signal_new("clicked", CellRendererSutekhButton,
                   GObject.SignalFlags.RUN_FIRST | GObject.SignalFlags.ACTION,
                   GObject.TYPE_NONE,
                   (GObject.TYPE_STRING,))
# the callback is called as callback (self, oPath)
