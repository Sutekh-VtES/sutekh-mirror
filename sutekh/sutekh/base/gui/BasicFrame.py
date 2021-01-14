# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Base class for other Frames.
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Base class for Sutekh Frames"""

from gi.repository import Gdk, Gtk, GLib

from .MessageBus import MessageBus

# Style the selected label to be bold
# We do this, rather than a colour, to avoid issues with
# light / dark themes, which are hard to identify programmitically
LABEL_CSS = b"""
   #selectedtitle {
      font-weight: bolder;
   }

   #frametitle {
      font-weight: normal;
   }
"""


def pack_resizable(oBox, oWidget):
    """Pack a widget into oBox so it is horizontally resizable without
       a visible scrollbar."""
    oScrollable = Gtk.ScrolledWindow()
    oScrollable.set_policy(Gtk.PolicyType.EXTERNAL, Gtk.PolicyType.NEVER)
    oScrollable.add(oWidget)
    oBox.pack_start(oScrollable, False, False, 0)
    oBox.show_all()


class BasicFrame(Gtk.Frame):
    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so many public methods
    """The basic, blank frame for sutekh.

       Provides a default frame, and drag-n-drop handlind for
       sawpping the frames.
       """

    _cModelType = None

    def __init__(self, oMainWindow):
        super().__init__()
        self._oMainWindow = oMainWindow
        self._aPlugins = []
        self.set_name("blank frame")
        self._iId = 0
        # Ensure new panes aren't completely hidden

        self._oTitle = Gtk.EventBox()
        self._oTitleLabel = Gtk.Label(label='Blank Frame')
        self._oTitleLabel.set_name('frametitle')
        self._oTitle.add(self._oTitleLabel)
        self._oView = Gtk.TextView()
        self._oView.set_editable(False)
        self._oView.set_cursor_visible(False)

        self._bNeedReload = False

        self._oTitle.drag_dest_set(Gtk.DestDefaults.ALL, [],
                                   Gdk.DragAction.COPY)
        self._oTitle.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, [],
                                     Gdk.DragAction.COPY)

        self._oTitle.drag_source_add_text_targets()
        self._oTitle.drag_dest_add_text_targets()

        self._oTitle.connect('drag-data-received', self.drag_drop_handler)
        self._oTitle.connect('drag-data-get', self.create_drag_data)
        # Create a multi-press gesture for the double click
        # This is to future proof us, since the old _2BUTTON_PRESS event,
        # while it still exists, is deprecated
        # Gtk's binding's are odd here, and we need to use new explicitly
        self._oGesture = Gtk.GestureMultiPress.new(self._oTitle)
        self._oGesture.connect('pressed', self.minimize_to_toolbar)
        self._oTitle.connect_after('drag_begin', self.make_drag_icon)
        self.set_drag_handler(self._oView)
        self.set_drop_handler(self._oView)

        oProvider = Gtk.CssProvider()
        oProvider.load_from_data(LABEL_CSS)
        oContext = self._oTitleLabel.get_style_context()
        oContext.add_provider(oProvider,
                              Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.set_unique_id()

        # subclasses will override this if required
        self._oController = None

    # pylint: disable=protected-access
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
    # pylint: enable=protected-access

    def set_unique_id(self):
        """Set a unique id for this pane"""
        # the [0] is to a) ensure max is never over an empty set and
        # b) that the id is positive
        self._iId = max(self._oMainWindow.get_pane_ids() + [0]) + 1

    def init_plugins(self):
        """Loop through the plugins, and enable those appropriate for us."""
        oPluginMgr = self._oMainWindow.plugin_manager
        for cPlugin in oPluginMgr.get_plugins_for(self._cModelType):
            self._aPlugins.append(cPlugin(self._oController.view,
                                          self._oController.view.get_model(),
                                          self._cModelType))

    def set_title(self, sTitle):
        """Set the title of the pane to sTitle"""
        self._oTitleLabel.set_markup(GLib.markup_escape_text(sTitle))

    def set_id(self, iNewId):
        """Set the id of the pane to the correct value"""
        self._iId = iNewId

    def set_drop_handler(self, oWidget):
        """Setup the frame drop handler on the widget"""
        oWidget.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        oWidget.drag_dest_add_text_targets()
        oWidget.connect('drag-data-received', self.drag_drop_handler)

    def set_drag_handler(self, oWidget):
        """Enable dragging of the frame via given widget"""
        oWidget.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, [],
                                Gdk.DragAction.COPY)
        oWidget.drag_source_add_text_targets()
        oWidget.connect('drag-data-get', self.create_drag_data)
        oWidget.connect_after('drag-begin', self.make_drag_icon)
        # oWidget.connect('drag-motion', self.drag_motion)

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

    # pylint: disable=no-self-use
    # Methods so sub-classes can override them
    def is_card_set(self, _sSetName):
        """Returns true if we're a copy of the given card set"""
        return False

    def get_menu_name(self):
        """Return the key into the menu dictionary in the main window"""
        return None

    def frame_setup(self):
        """Hook called when the frame is added to the window.

           Used for subscribing to signals and so forth."""
        MessageBus.subscribe(MessageBus.Type.DATABASE_MSG, "update_to_new_db",
                             self.update_to_new_db)

    # pylint: enable=no-self-use

    def cleanup(self, _bQuit=False):
        """Hook for cleanup actions when the frame is removed."""
        # do per-plugin cleanup
        MessageBus.unsubscribe(MessageBus.Type.DATABASE_MSG,
                               "update_to_new_db", self.update_to_new_db)
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
        self._oMainWindow.queue_reload()

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
        oMbox = Gtk.VBox(homogeneous=False, spacing=2)

        pack_resizable(oMbox, self._oTitle)
        # Blanks view placeholder fills everything it can
        oMbox.pack_start(self._oView, True, True, 0)

        self.add(oMbox)
        self.show_all()

    def set_focussed_title(self):
        """Set the title to the correct style when focussed."""
        self._oTitleLabel.set_name('selectedtitle')

    def set_unfocussed_title(self):
        """Set the title back to the default, unfocussed style."""
        self._oTitleLabel.set_name('frametitle')

    def close_menu_item(self, _oMenuWidget):
        """Handle close requests from the menu."""
        self.close_frame()

    def call_focus(self, _oWidget, oEvent, oFocusFunc):
        """Call MultiPaneWindow focus handler for button events"""
        oFocusFunc(self, oEvent, self)
        return False

    # pylint: disable=too-many-arguments
    # function signature requires all these arguments
    def drag_drop_handler(self, _oWindow, oDragContext, _iXPos, _iYPos,
                          oSelectionData, _oInfo, oTime):
        """Handle panes being dragged onto this one.

           Allows panes to be sapped by dragging 'n dropping."""
        bDragRes = True
        sData = oSelectionData.get_text()
        if not sData:
            # Not valid text
            bDragRes = False
        else:
            aData = sData.splitlines()
            if aData[0] == 'Basic Pane:':
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
        sData = 'Basic Pane:\n%s' % self.pane_id
        oSelectionData.set_text(sData, -1)

    # pylint: disable=no-self-use
    # needs to be a method, as children can override this if needed
    def drag_motion(self, _oWidget, oDrag_context, _iXPos, _iYPos,
                    _oTimestamp):
        """Show proper icon during drag-n-drop actions."""
        if 'STRING' in oDrag_context.targets:
            oDrag_context.drag_status(Gtk.DragAction.COPY)
            return True
        return False

    def minimize_to_toolbar(self, _oGesture, iNumPresses, _fX, _fY):
        """Minimize the frame to the toolbar on double-click."""
        # We're only interested in double clicks
        if iNumPresses == 2:
            self._oMainWindow.minimize_to_toolbar(self)

    def make_drag_icon(self, oWidget, _oDragContext):
        """Create an icon for dragging the pane from the titlebar"""
        iXOffset, iYOffset = self._oTitleLabel.get_layout_offsets()
        oPixbuf = Gdk.pixbuf_get_from_window(self._oTitleLabel.get_window(),
                                             iXOffset, iYOffset, 100, 20)
        oWidget.drag_source_set_icon_pixbuf(oPixbuf)
