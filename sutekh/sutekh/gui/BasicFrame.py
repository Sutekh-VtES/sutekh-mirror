# CardListFrame.py
# Base class for other Frames.
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details


import gtk

class BasicFrame(gtk.Frame, object):
    def __init__(self, oMainWindow):
        super(BasicFrame, self).__init__()
        self._oMainWindow = oMainWindow

        # Ensure new panes aren't completely hidden

        self._oTitle = gtk.EventBox()
        self._oTitleLabel = gtk.Label('Blank Frame')
        self._oTitle.add(self._oTitleLabel)
        oBuf = gtk.TextBuffer()
        self._oView = gtk.TextView()
        self._oView.set_editable(False)
        self._oView.set_cursor_visible(False)

        aDragTargets = [ ('STRING', 0, 0),
                         ('text/plain', 0, 0) ]

        self._oTitle.drag_source_set(gtk.gdk.BUTTON1_MASK | gtk.gdk.BUTTON3_MASK, 
                aDragTargets,
                gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        self._oTitle.drag_dest_set(gtk.DEST_DEFAULT_ALL,
                aDragTargets,
                gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        self._oTitle.connect('drag-data-received', self.drag_drop_handler)
        self._oTitle.connect('drag-data-get', self.create_drag_data)

        self._oView.drag_dest_set(gtk.DEST_DEFAULT_ALL,
                aDragTargets,
                gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        self._oView.connect('drag-data-received', self.drag_drop_handler)
        self._oView.connect('drag-motion', self.drag_motion)

        self._oBaseStyle = self._oTitle.get_style().copy()
        self._oFocStyle = self._oTitle.get_style().copy()
        oMap = self._oTitle.get_colormap()
        oHighlighted = oMap.alloc_color("purple")
        self._oFocStyle.fg[gtk.STATE_NORMAL] = oHighlighted

    title = property(fget=lambda self: self._oTitleLabel.get_text(), doc="Frame Title")
    name = property(fget=lambda self: self._oTitleLabel.get_text(), doc="Frame Name")
    type = property(fget=lambda self: "Blank Frame", doc="Frame Type")
    view = property(fget=lambda self: self._oView, doc="Associated View Object")

    def set_title(self, sTitle):
        self._oTitleLabel.set_text(sTitle)

    def drag_drop_handler(self, oWindow, oDragContext, x, y, oSelectionData, oInfo, oTime):
        if not oSelectionData and oSelectionData.format != 8:
            oDragContext.finish(False, False, oTime)
        else:
            aData =  oSelectionData.data.splitlines()
            if aData[0] != 'Sutekh Pane:':
                oDragContext.finish(False, False, oTime)
            else:
                if self.do_swap(aData):
                    oDragContext.finish(True, False, oTime)
                else:
                    oDragContext.finish(False, False, oTime)

    def do_swap(self, aData):
        if aData[1] != 'Card Set Pane:':
            # We swap ourself with the other pane
            oOtherFrame = self._oMainWindow.find_pane_by_name(aData[1])
            if oOtherFrame is not None:
                 self._oMainWindow.swap_frames(self, oOtherFrame)
                 return True
        else:
            # We replace otherselves with the card set
            if aData[2] == 'PCS:':
                self._oMainWindow.replace_with_physical_card_set(aData[3], self)
                return True
            elif aData[2] == 'ACS:':
                self._oMainWindow.replace_with_abstract_card_set(aData[3], self)
                return True
        return False

    def cleanup(self):
        pass

    def reload(self):
        """Reload frame contents"""
        pass

    def close_frame(self):
        self._oMainWindow.remove_frame(self)
        self.destroy()

    def close_menu_item(self, oMenuWidget):
        self.close_frame()

    def add_parts(self):
        wMbox = gtk.VBox(False, 2)

        wMbox.pack_start(self._oTitle, False, False)
        # Blanks view placeholder fills everything it can
        wMbox.pack_start(self._oView, True, True)

        self.add(wMbox)
        self.show_all()

    def set_focussed_title(self):
        self._oTitleLabel.set_style(self._oFocStyle)

    def set_unfocussed_title(self):
        self._oTitleLabel.set_style(self._oBaseStyle)

    def create_drag_data(self, oBtn, oContext, oSelectionData, oInfo, oTime):
        """
        Fill in the needed data for drag-n-drop code
        """
        sData = 'Sutekh Pane:\n' + self.title
        oSelectionData.set(oSelectionData.target, 8, sData)

    def drag_motion(self, widget, drag_context, x, y, timestamp):
        if 'STRING' in drag_context.targets:
            drag_context.drag_status(gtk.gdk.ACTION_COPY)
            return True
        return False
