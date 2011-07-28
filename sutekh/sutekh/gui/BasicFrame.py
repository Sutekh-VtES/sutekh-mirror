# BasicFrame.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Base class for other Frames.
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Base class for Sutekh Frames"""

import gtk
import gobject


class BasicFrame(gtk.Frame):
    # pylint: disable-msg=R0904
    # gtk.Widget, so lotes of public methods
    """The basic, blank frame for sutekh.

       Provides a default frame, and drag-n-drop handlind for
       sawpping the frames. Also provides gtkrc handling for
       setting the active hint.
       """

    aDragTargets = [('STRING', 0, 0), ('text/plain', 0, 0)]

    _cModelType = None

    def __init__(self, oMainWindow):
        super(BasicFrame, self).__init__()
        self._oMainWindow = oMainWindow
        self._aPlugins = []
        self.set_name("blank frame")
        self._iId = 0

        # Ensure new panes aren't completely hidden

        self._oTitle = gtk.EventBox()
        self._oTitleLabel = gtk.Label('Blank Frame')
        self._oTitleLabel.set_name('frame_title')
        self._oTitle.add(self._oTitleLabel)
        # Allows setting background colours for title easily
        self._oTitle.set_name('frame_title')
        self._oView = gtk.TextView()
        self._oView.set_editable(False)
        self._oView.set_cursor_visible(False)

        self._bNeedReload = False

        self._oTitle.drag_source_set(
                gtk.gdk.BUTTON1_MASK | gtk.gdk.BUTTON3_MASK, self.aDragTargets,
                gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        self._oTitle.drag_dest_set(gtk.DEST_DEFAULT_ALL,
                self.aDragTargets,
                gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        self._oTitle.connect('drag-data-received', self.drag_drop_handler)
        self._oTitle.connect('drag-data-get', self.create_drag_data)
        self._oTitle.connect('button-press-event', self.minimize_to_toolbar)
        self._oTitle.connect_after('drag_begin', self.make_drag_icon)
        self.set_drag_handler(self._oView)
        self.set_drop_handler(self._oView)

        self.set_unique_id()

    # pylint: disable-msg=W0212
    # explicitly allow access to these values via thesep properties
    title = property(fget=lambda self: self._oTitleLabel.get_text(),
            doc="Frame Title")
    name = property(fget=lambda self: self._oTitleLabel.get_text(),
            doc="Frame Name")
    type = property(fget=lambda self: "Blank Frame", doc="Frame Type")
    view = property(fget=lambda self: self._oView,
            doc="Associated View Object")
    menu = property(fget=lambda self: None, doc="Frame's menu")
    plugins = property(fget=lambda self: self._aPlugins,
            doc="Plugins enabled for this frame.")
    pane_id = property(fget=lambda self: self._iId,
            doc="ID number for this pane (should be unique)")
    config_frame_id = property(fget=lambda self: "pane%s" % (self._iId,),
            doc="Config frame id for this pane")
    # pylint: enable-msg=W0212

    def set_unique_id(self):
        """Set a unique id for this pane"""
        # the [0] is to a) ensure max is never over an empty set and
        # b) that the id is positive
        self._iId = max(self._oMainWindow.get_pane_ids() + [0]) + 1

    def init_plugins(self):
        """Loop through the plugins, and enable those appropriate for us."""
        for cPlugin in \
                self._oMainWindow.plugin_manager.get_card_list_plugins():
            self._aPlugins.append(cPlugin(self._oController.view,
                self._oController.view.get_model(), self._cModelType))

    def set_title(self, sTitle):
        """Set the title of the pane to sTitle"""
        self._oTitleLabel.set_markup(gobject.markup_escape_text(sTitle))

    def set_id(self, iNewId):
        """Set the id of the pane to the correct value"""
        self._iId = iNewId

    def set_drop_handler(self, oWidget):
        """Setup the frame drop handler on the widget"""
        oWidget.drag_dest_set(gtk.DEST_DEFAULT_ALL,
                self.aDragTargets,
                gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
        oWidget.connect('drag-data-received', self.drag_drop_handler)
        oWidget.connect('drag-motion', self.drag_motion)

    def set_drag_handler(self, oWidget):
        """Enable dragging of the frame via given widget"""
        oWidget.drag_source_set(
                gtk.gdk.BUTTON1_MASK | gtk.gdk.BUTTON3_MASK,
                self.aDragTargets,
                gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
        oWidget.connect('drag-data-get', self.create_drag_data)
        oWidget.connect_after('drag_begin', self.make_drag_icon)

    def set_focus_handler(self, oFunc):
        """Set the button press handler for the frame"""
        self.connect('button-press-event', self.call_focus, oFunc)
        # Need both, otherwise clicking on a title and the clicking on
        # the previous tree does the wrong thing
        self.view.connect('button-press-event', self.call_focus, oFunc)
        self.view.connect('focus-in-event', oFunc, self)

    def do_swap(self, aData):
        """Swap this pane with the relevant pane"""
        # We swap ourself with the other pane
        oOtherFrame = self._oMainWindow.find_pane_by_id(int(aData[1]))
        if oOtherFrame:
            self._oMainWindow.swap_frames(self, oOtherFrame)
            return True
        return False

    def do_dragged_card_set(self, aData):
        """Replace this pane with the relevant card set"""
        # We replace otherselves with the card set
        # Check that we're not the same card set already
        if self.is_card_set(aData[1]):
            return False
        # Open the card set
        self._oMainWindow.replace_with_physical_card_set(aData[1], self)
        return True

    # pylint: disable-msg=R0201
    # Methods so sub-classes can override them
    def is_card_set(self, _sSetName):
        """Returns true if we're a copy of the given card set"""
        return False

    def get_menu_name(self):
        """Return the key into the menu dictionary in the main window"""
        return None

    # pylint: enable-msg=R0201

    def cleanup(self):
        """Hook for cleanup actions when the frame is removed."""
        # do per-plugin cleanup
        for oPlugin in self._aPlugins:
            oPlugin.cleanup()
        # Don't hold references to the plugins
        self._aPlugins = []
        # Cleanup after the menu if required
        if self.menu and hasattr(self.menu, 'cleanup'):
            self.menu.cleanup()

    def reload(self):
        """Reload frame contents"""
        pass

    def do_queued_reload(self):
        """Do a deferred reload if one was set earlier"""
        self._bNeedReload = False

    def queue_reload(self):
        """Queue a reload for later - needed so reloads can happen after
           database update signals."""
        self._bNeedReload = True
        # Add timeout so reload is called in the near future
        # As we're single threaded, this won't be executred until we're
        # done with the current main_loop iteration, so it will only
        # happen after all our current processing.
        gobject.timeout_add(20, self._oMainWindow.do_all_queued_reloads)

    def update_to_new_db(self):
        """Re-associate internal data against the database.

           Needed for re-reading WW cardlists and such.
           By default, just reload.
           """
        self.reload()

    def close_frame(self):
        """Close the frame"""
        self._oMainWindow.config_file.clear_frame_profile(self.config_frame_id)
        self._oMainWindow.remove_frame(self)
        self.destroy()

    def add_parts(self):
        """Add the basic widgets (title, & placeholder) to the frame."""
        oMbox = gtk.VBox(False, 2)

        oMbox.pack_start(self._oTitle, False, False)
        # Blanks view placeholder fills everything it can
        oMbox.pack_start(self._oView, True, True)

        self.add(oMbox)
        self.show_all()

    def set_focussed_title(self):
        """Set the title to the correct style when focussed."""
        oCurStyle = self._oTitleLabel.rc_get_style()
        self._oTitleLabel.set_name('selected_title')
        # We can't have this name be a superset of the title name,
        # otherwise any style set on 'title' automatically applies
        # here, which is not what we want.

        oDefaultSutekhStyle = gtk.rc_get_style_by_paths(
                self._oTitleLabel.get_settings(), self.path() + '.',
                self.class_path(), self._oTitleLabel)
        # Bit of a hack, but get's matches to before the title specific bits
        # of the path

        oSpecificStyle = self._oTitleLabel.rc_get_style()
        if oSpecificStyle == oDefaultSutekhStyle or \
                oDefaultSutekhStyle is None:
            # No specific style which affects highlighted titles set, so create
            # one
            oMap = self._oTitleLabel.get_colormap()
            sColour = 'purple'
            if oMap.alloc_color(sColour).pixel == \
                    oCurStyle.fg[gtk.STATE_NORMAL].pixel:
                sColour = 'green'
                # Prevent collisions. If the person is using
                # purple on a green background, they deserve
                # invisible text
            sStyleInfo = """
            style "internal_sutekh_hlstyle" {
                fg[NORMAL] = "%(colour)s"
                }
            widget "%(path)s" style "internal_sutekh_hlstyle"
            """ % {'colour': sColour, 'path': self._oTitleLabel.path()}
            gtk.rc_parse_string(sStyleInfo)
            # We use gtk's style machinery to do the update.
            # This seems the only way of ensuring we will actually do
            # the right thing with themes, while still allowing flexiblity
        # Here, as this forces gtk to re-asses styles of widget and children
        self._oTitle.set_name('selected_title')

    def set_unfocussed_title(self):
        """Set the title back to the default, unfocussed style."""
        self._oTitleLabel.set_name('frame_title')
        self._oTitle.set_name('frame_title')

    def close_menu_item(self, _oMenuWidget):
        """Handle close requests from the menu."""
        self.close_frame()

    def call_focus(self, _oWidget, oEvent, oFocusFunc):
        """Call MultiPaneWindow focus handler for button events"""
        oFocusFunc(self, oEvent, self)
        return False

    # pylint: disable-msg=R0913
    # function signature requires all these arguments
    def drag_drop_handler(self, _oWindow, oDragContext, _iXPos, _iYPos,
            oSelectionData, _oInfo, oTime):
        """Handle panes being dragged onto this one.

           Allows panes to be sapped by dragging 'n dropping."""
        bDragRes = True
        if not oSelectionData and oSelectionData.format != 8:
            bDragRes = False
        else:
            aData = oSelectionData.data.splitlines()
            if aData[0] == 'Sutekh Pane:':
                if not self.do_swap(aData):
                    bDragRes = False
            elif aData[0] == 'Card Set:':
                if not self.do_dragged_card_set(aData):
                    bDragRes = False
            else:
                bDragRes = False
        oDragContext.finish(bDragRes, False, oTime)

    def create_drag_data(self, _oBtn, _oContext, oSelectionData, _oInfo,
            _oTime):
        """Fill in the needed data for drag-n-drop code"""
        sData = 'Sutekh Pane:\n%s' % self.pane_id
        oSelectionData.set(oSelectionData.target, 8, sData)

    # pylint: disable-msg=R0201
    # needs to be a method, as children can override this if needed
    def drag_motion(self, _oWidget, oDrag_context, _iXPos, _iYPos,
            _oTimestamp):
        """Show proper icon during drag-n-drop actions."""
        if 'STRING' in oDrag_context.targets:
            oDrag_context.drag_status(gtk.gdk.ACTION_COPY)
            return True
        return False

    def minimize_to_toolbar(self, _oWidget, oEvent):
        """Minimize the frame to the toolbar on double-click."""
        # pylint: disable-msg=W0212
        # We need to access _2BUTTON_PRESS
        if oEvent.type == gtk.gdk._2BUTTON_PRESS:
            self._oMainWindow.minimize_to_toolbar(self)

    def make_drag_icon(self, oWidget, _oDragContext):
        """Create an icon for dragging the pane from the titlebar"""
        oDrawable = self._oTitleLabel.get_snapshot(None)
        oWidget.drag_source_set_icon(oDrawable.get_colormap(), oDrawable)
