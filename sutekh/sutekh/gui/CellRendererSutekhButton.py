# CellRendererSutekhButton.py
# Pixbuf Button CellRenderer
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk, gobject

# This is heavily cribbed from the example in the pygtk FAQ
# (By Nikos Kouremenos)
# limited to the use of icons only ATM
# Allows creation of a cell containing a icon pixbuf,
# and returns a "clicked" signal when activated
# To be generically useful, should be extended to abitary pixmaps,
# but that is currently not a priority

class CellRendererSutekhButton(gtk.GenericCellRenderer):
    def __init__(self):
        self.__gobject_init__()
        self.oPixbuf = None
        self.set_property("mode", gtk.CELL_RENDERER_MODE_ACTIVATABLE)

    def load_icon(self, sName, oWidget):
        # Load the icon specified in name
        self.oPixbuf = oWidget.render_icon(sName, gtk.ICON_SIZE_SMALL_TOOLBAR)


    def on_get_size(self, oWidget, oCellArea):
        if self.oPixbuf is None:
            return 0, 0, 0, 0
        iPixbufWidth  = self.oPixbuf.get_width()
        iPixbufHeight = self.oPixbuf.get_height()
        iCalcWidth  = self.get_property("xpad") * 2 + iPixbufWidth
        iCalcHeight = self.get_property("ypad") * 2 + iPixbufHeight
        iXOffset = 0
        iYOffset = 0
        if oCellArea is not None and iPixbufWidth > 0 and iPixbufHeight > 0:
            iXOffset = self.get_property("xalign") * (oCellArea.width - \
                iCalcWidth -  self.get_property("xpad"))
            iYOffset = self.get_property("yalign") * (oCellArea.height - \
                iCalcHeight -  self.get_property("ypad"))
        return iXOffset, iYOffset, iCalcWidth, iCalcHeight

    def on_activate(self, oEvent, oWidget, oPath, oBackgroundArea,
            oCellArea, iFlags):
        # TODO - setup drawing of clicked image
        # clicked callback should be called
        self.emit('clicked', oPath)
        return True

    def on_render(self, oWindow, oWidget, oBackgroundArea,
            oCellArea, oExposeArea, iFlags):
        if self.oPixbuf is None:
            return None
        # Render pixbuf
        oPixRect = gtk.gdk.Rectangle()
        oPixRect.x, oPixRect.y, oPixRect.width, oPixRect.height = \
            self.on_get_size(oWidget, oCellArea)

        oPixRect.x += oCellArea.x
        oPixRect.y += oCellArea.y
        oPixRect.width  -= 2 * self.get_property("xpad")
        oPixRect.height -= 2 * self.get_property("ypad")

        oDrawRect = oCellArea.intersect(oPixRect)
        oDrawRect = oExposeArea.intersect(oDrawRect)

        oWindow.draw_pixbuf(oWidget.style.black_gc, self.oPixbuf,
            oDrawRect.x - oPixRect.x, oDrawRect.y - oPixRect.y, oDrawRect.x,
            oDrawRect.y + 2, oDrawRect.width, oDrawRect.height,
            gtk.gdk.RGB_DITHER_NONE, 0, 0)
        return None

# HouseKeeping work for CellRendererStukehButton
# Awkward stylistically, but I'm putting it here as it's
# associated with class creation (is global to the class)
# so doesn't belong in the per-instance constructor - NM
# Register class, needed to make clicked signal go to right class
# (otherwise it gets associated with GenericCellRenderer, which is
# not desireable)
gobject.type_register(CellRendererSutekhButton)
# Setup clicked signal -- can also be done using the __gsignals__
# dict in the class, but I couldn't find good documentation for
# that approach.
gobject.signal_new("clicked", CellRendererSutekhButton,
    gobject.SIGNAL_RUN_FIRST|gobject.SIGNAL_ACTION,
    gobject.TYPE_NONE,
    (gobject.TYPE_STRING,))
# the callback is called as callback (self, oPath)
