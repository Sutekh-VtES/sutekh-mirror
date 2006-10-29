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
        self.pixbuf = None
        self.set_property("mode",gtk.CELL_RENDERER_MODE_ACTIVATABLE)

    def load_icon(self,name,widget):
        # Load the icon specified in name
        self.pixbuf=widget.render_icon(name,gtk.ICON_SIZE_SMALL_TOOLBAR)


    def on_get_size(self,widget,cell_area):
        if self.pixbuf==None:
            return 0, 0, 0, 0
        pixbuf_width  = self.pixbuf.get_width()
        pixbuf_height = self.pixbuf.get_height()
        calc_width  = self.get_property("xpad") * 2 + pixbuf_width
        calc_height = self.get_property("ypad") * 2 + pixbuf_height
        x_offset = 0
        y_offset = 0
        if cell_area and pixbuf_width > 0 and pixbuf_height > 0:
            x_offset = self.get_property("xalign") * (cell_area.width - \
                calc_width -  self.get_property("xpad"))
            y_offset = self.get_property("yalign") * (cell_area.height - \
                calc_height -  self.get_property("ypad"))
        return x_offset, y_offset, calc_width, calc_height

    def on_activate(self, event, widget, path, background_area, cell_area, flags):
        # TODO - setup drawing of clicked image
        # clicked callback should be called
        self.emit('clicked',path)
        return True

    def on_render(self,window, widget, background_area, cell_area, expose_area, flags):
       if (self.pixbuf==None):
          return None
       # Render pixbuf
       pix_rect = gtk.gdk.Rectangle()
       pix_rect.x, pix_rect.y, pix_rect.width, pix_rect.height = \
          self.on_get_size(widget, cell_area)

       pix_rect.x += cell_area.x
       pix_rect.y += cell_area.y
       pix_rect.width  -= 2 * self.get_property("xpad")
       pix_rect.height -= 2 * self.get_property("ypad")

       draw_rect = cell_area.intersect(pix_rect)
       draw_rect = expose_area.intersect(draw_rect)

       window.draw_pixbuf(widget.style.black_gc, self.pixbuf, \
          draw_rect.x-pix_rect.x, draw_rect.y-pix_rect.y, draw_rect.x, \
          draw_rect.y+2, draw_rect.width, draw_rect.height, \
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
# the callback is called as callback(self,path)
