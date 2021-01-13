# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Handle the multi pane UI for Sutkeh
# Copyright 2007, 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - See COPYING for details

"""Multi-pane window."""

from itertools import chain

from gi.repository import Gtk, Gdk, GLib

from .MainToolbar import MainToolbar
from .BasicFrame import BasicFrame
# pylint: enable=wrong-import-position


class MultiPaneWindow(Gtk.Window):
    """Window that has a configurable number of panes."""
    # pylint: disable=too-many-instance-attributes, too-many-public-methods
    # we need to keep a lot of state, so many instance attributes
    # Gtk.Widget, so many public methods
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_border_width(2)

        # This always increments when panes are added, so the number is unique
        # for each new frame
        self._iCount = 0

        # Need to keep track of open card sets globally
        self.aClosedFrames = []
        self.aOpenFrames = []

        self._oToolbar = None
        self._oMenu = None
        self._oVBox = None
        self._bQueue = False

        self._aHPanes = []

        self._oFocussed = None

        self._oBusyCursor = Gdk.Cursor.new_for_display(
            Gdk.Display.get_default(), Gdk.CursorType.WATCH)

        # Flag to block calling reloads during a refresh process
        self._bBlockReload = False

    def _setup_vbox(self):
        """Setup the intial vbox and connect the key_press event"""
        self._oToolbar = MainToolbar(self)

        self._oVBox = Gtk.VBox(homogeneous=False, spacing=1)
        if self._oMenu:
            self._oVBox.pack_start(self._oMenu, False, False, 0)
        self._oVBox.pack_start(self._oToolbar, False, False, 0)
        self._oVBox.show()
        self.add(self._oVBox)

        self.show_all()
        self.connect('key-press-event', self.key_press)

    # pylint: disable=protected-access
    # We allow access via these properties
    # Needed for Backup plugin
    focussed_pane = property(fget=lambda self: self._oFocussed,
                             doc="The currently focussed pane.")
    mainwindow = property(fget=lambda self: self,
                          doc="Return reference to the main window")

    # pylint: enable=protected-access

    def _clear_frames(self):
        """Clear out all existing frames (loop over copies of the list)"""
        for oFrame in chain(self.aOpenFrames[:], self.aClosedFrames[:]):
            self.remove_frame(oFrame, True)

    def reload_all(self):
        """Reload all frames. Useful for major DB changes"""
        for oPane in chain(self.aOpenFrames, self.aClosedFrames):
            oPane.reload()

    def _block_reload(self):
        """Prevent queued reloads triggering do to scheduling wierdness"""
        self._bBlockReload = True

    def _unblock_reload(self):
        """Re-enable reload behaviour"""
        self._bBlockReload = False

    def queue_reload(self):
        """Queue a reload if we don't already have one queued"""
        if not self._bQueue:
            self._bQueue = True
            # Add timeout so reload is called in the near future
            # As we're single threaded, this won't be executed until we're
            # done with the current main_loop iteration.
            # In most situations, this is will be enough, and we have
            # additional protections for the complex cases.
            GLib.timeout_add(30, self.do_all_queued_reloads)

    def do_all_queued_reloads(self):
        """Do any deferred reloads from the database signal handlers."""
        if self._bBlockReload:
            # We can't reload right now, so punt this down the road a bit
            # We schedule a bit further in the future than the BasicFrame
            # initial queue, since we know we're already busy with stuff.
            #
            # This workaround avoids triggering "database locked" errors
            # when updating sqlite DBs on some systems, but it's a good
            # idea to avoid reloading during a update on any system.
            GLib.timeout_add(100, self.do_all_queued_reloads)
            return
        self._bQueue = False
        for oPane in chain(self.aOpenFrames, self.aClosedFrames):
            oPane.do_queued_reload()

    # Pane manipulation functions

    def top_level_panes(self):
        """Return a list of top-level panes.

           This is just the contents of the MainWindow vbox minus
           the toolbar and menu.
           """
        return [x for x in self._oVBox.get_children() if
                x not in (self._oMenu, self._oToolbar)]

    def find_pane_by_id(self, iId):
        """Return the Gtk widget corresponding to the given pane name"""
        for oPane in chain(self.aOpenFrames, self.aClosedFrames):
            if oPane.pane_id == iId:
                return oPane
        return None

    def get_pane_ids(self):
        """Return a list of all relevant pane ids"""
        aIds = []
        aIds.extend([x.pane_id for x in self.aOpenFrames])
        aIds.extend([x.pane_id for x in self.aClosedFrames])
        return aIds

    def reset_menu(self):
        """Children will override this"""

    def win_focus(self, _oWidget, _oEvent, oFrame):
        """Respond to focus change events.

           Keep track of focussed pane, update menus and handle highlighting.
           """
        if self._oFocussed is not None:
            self._oFocussed.set_unfocussed_title()
        self._oFocussed = oFrame
        if oFrame:
            # oFrame can be None when win_focus is called directly
            self._oFocussed.set_focussed_title()
            self._oFocussed.view.grab_focus()
        self.reset_menu()

    def key_press(self, _oWidget, oEvent):
        """Move to the next frame on Tab"""
        oKeyVal = oEvent.get_keyval()[1]
        if oKeyVal == Gdk.keyval_from_name('Tab') or \
                oKeyVal == Gdk.keyval_from_name('KP_Tab'):
            self.move_to_frame(+1)
            return True
        if oKeyVal == Gdk.keyval_from_name('ISO_Left_Tab'):
            # Shift & tab should always be this, AFAICT
            self.move_to_frame(-1)
            return True
        return False  # propogate event

    # _oWidget needed so this can be also be called from the menu
    def add_pane_end(self, _oWidget=None):
        """Add a pane to the right edge of the window.

           Used for the add pane menu items and double clicking on card set
           names.
           """
        if not self.aOpenFrames:
            oPane = None
        else:
            # Descend the right child of the panes, until we get a
            # non-paned item
            oPane = self.top_level_panes()[0]
            while isinstance(oPane, (Gtk.HPaned, Gtk.VPaned)):
                oPane = oPane.get_child2()
        oOldFocus = self._oFocussed
        self.win_focus(None, None, oPane)
        oNewPane = self.add_pane()
        self.win_focus(None, None, oOldFocus)
        return oNewPane

    # frame management functions

    def move_to_frame(self, iDir):
        """Move the focus to the previous frame"""
        if iDir > 0:
            oNewFrame = self._find_next_frame(self._oFocussed)
        else:
            oNewFrame = self._find_prev_frame(self._oFocussed)
        if oNewFrame:
            self.win_focus(None, None, oNewFrame)

    def _find_prev_frame(self, oFrame):
        """Move the focus to the next frame in the window"""
        if not oFrame:
            if not self.aOpenFrames:
                # No frame, so nothing to focus
                return None
            # get first child, and descent that
            oChild = self.top_level_panes()[0]
            oParent = self._oVBox
        else:
            oParent = oFrame.get_parent()
            if isinstance(oParent, Gtk.VPaned):
                if oParent.get_child2() == oFrame:
                    # Need to go to the top frame
                    return oParent.get_child1()
                oChild = oParent
            else:
                oChild = oFrame
            # Need to move to the 'neighbouring' HPane
            oParent = oChild.get_parent()
            while (isinstance(oParent, Gtk.HPaned) and
                   oChild == oParent.get_child1()):
                # As long as we're the left-most branch, we ascend
                oChild = oParent
                oParent = oChild.get_parent()
        # prepare to descend to the correct frame
        if isinstance(oParent, Gtk.HPaned) and oChild == oParent.get_child2():
            # We need to start going down the left-hand tree
            oChild = oParent.get_child1()
        while isinstance(oChild, Gtk.HPaned):
            # we descend down the right branch until we reach a frame
            oChild = oChild.get_child2()
        if isinstance(oChild, Gtk.VPaned):
            # go to the bottom frame in this case
            oChild = oChild.get_child2()
        return oChild

    def _find_next_frame(self, oFrame):
        """Move the focus to the next frame in the window"""
        if not oFrame:
            if not self.aOpenFrames:
                # No frame, so nothing to focus
                return None
            # get first child, and descent that
            oChild = self.top_level_panes()[0]
            oParent = self._oVBox
        else:
            oParent = oFrame.get_parent()
            if isinstance(oParent, Gtk.VPaned):
                if oParent.get_child1() == oFrame:
                    # Need to go to the bottom frame
                    return oParent.get_child2()
                oChild = oParent
            else:
                oChild = oFrame
            # Need to move to the 'neighbouring' HPane
            oParent = oChild.get_parent()
            while (isinstance(oParent, Gtk.HPaned) and
                   oChild == oParent.get_child2()):
                # As long as we're the right-most branch, we ascend
                oChild = oParent
                oParent = oChild.get_parent()
        # prepare to descend to the correct frame
        if isinstance(oParent, Gtk.HPaned) and oChild == oParent.get_child1():
            # We need to start going down the right-hand tree
            oChild = oParent.get_child2()
        while isinstance(oChild, Gtk.HPaned):
            # we descend down the left branch until we reach a frame
            oChild = oChild.get_child1()
        if isinstance(oChild, Gtk.VPaned):
            # go to the top frame in this case
            oChild = oChild.get_child1()
        return oChild

    def _get_open_pane_pos(self):
        """Return a list of open panes with their positions"""

        def walk_children(oPane, bVert, iPos, aPanes):
            """Walk the tree of HPanes + VPanes, and get their info."""
            # oPane.get_position() gives us the position relative to the paned
            # we're contained in. However, when we recreate the layout, we
            # don't split panes in the same order, hence the fancy
            # score-keeping work to convert the obtained positions to those
            # needed for restoring
            if isinstance(oPane, Gtk.HPaned):
                oChild1 = oPane.get_child1()
                oChild2 = oPane.get_child2()
                iChildPos = walk_children(oChild1, False, iPos, aPanes)
                iMyPos = oPane.get_position()
                if isinstance(oChild1, Gtk.HPaned):
                    iMyPos = iMyPos - iChildPos
                    iChildPos = oPane.get_position()
                else:
                    iChildPos = iMyPos
                if iMyPos < 1:
                    # Setting pos to < 1 doesn't do what we want
                    iMyPos = 1
                iChild2Pos = walk_children(oChild2, False, iMyPos, aPanes)
                if isinstance(oChild2, Gtk.HPaned):
                    iChildPos += iChild2Pos
            elif isinstance(oPane, Gtk.VPaned):
                oChild1 = oPane.get_child1()
                oChild2 = oPane.get_child2()
                iMyPos = oPane.get_position()
                walk_children(oChild1, False, iPos, aPanes)
                walk_children(oChild2, True, iMyPos, aPanes)
                iChildPos = iPos
            else:
                aPanes.append((oPane, bVert, iPos))
                iChildPos = iPos
            return iChildPos

        aPanes = []
        aTopLevelPanes = self.top_level_panes()
        if aTopLevelPanes:
            walk_children(aTopLevelPanes[0], False, -1, aPanes)
        return aPanes

    def replace_frame(self, oOldFrame, oNewFrame):
        """Replace oOldFrame with oNewFrame + update menus"""
        oNewFrame.show()
        oNewFrame.set_focus_handler(self.win_focus)
        oParent = oOldFrame.get_parent()
        oParent.remove(oOldFrame)
        oParent.add(oNewFrame)
        self.aOpenFrames.remove(oOldFrame)
        self.aOpenFrames.append(oNewFrame)
        if oNewFrame in self.aClosedFrames:
            self.aClosedFrames.remove(oNewFrame)
        else:
            # Newly added frame, so call frame_setup
            oNewFrame.frame_setup()
        if self._oFocussed == oOldFrame:
            self.win_focus(None, None, None)
        # kill any listeners, etc.
        oOldFrame.cleanup()
        self.reset_menu()

    def swap_frames(self, oFrame1, oFrame2):
        """swap two frames - used by drag-n-drop code"""
        if oFrame1 != oFrame2:
            oParent1 = oFrame1.get_parent()
            oParent2 = oFrame2.get_parent()
            if oParent1 == oParent2:
                # Special logic to ensure that we get them swapped
                if oFrame1 == oParent1.get_child1():
                    oParent1.remove(oFrame1)
                    oParent1.remove(oFrame2)
                    oParent1.add1(oFrame2)
                    oParent1.add2(oFrame1)
                else:
                    oParent1.remove(oFrame1)
                    oParent1.remove(oFrame2)
                    oParent1.add1(oFrame1)
                    oParent1.add2(oFrame2)
            else:
                oParent2.remove(oFrame2)
                oParent1.remove(oFrame1)
                oParent2.add(oFrame1)
                oParent1.add(oFrame2)
            oParent1.show()
            oParent2.show()
            self.reset_menu()

    def get_current_pane(self):
        """Get the parent HPane of the focussed pane.

           If there's no Focussed Pane, return the last added pane,
           which does the right thing for restore_from_config.
           """
        if self._oFocussed:
            oParent = self._oFocussed.get_parent()
            if isinstance(oParent, Gtk.VPaned):
                # Get the HPane this belongs to
                oParent = oParent.get_parent()
            return oParent
        # Return the last added pane, for automatic adds
        return self._aHPanes[-1]

    # Utility functions for add_pane
    def _get_pane_to_replace(self):
        """Get the pane to be replaced in add_pane

           Return the pane and the part to replace"""
        oParent = self.get_current_pane()
        # Must be a hpane, by construction
        if self._oFocussed:
            oPart1 = self._oFocussed
            if isinstance(oPart1.get_parent(), Gtk.VPaned):
                # Veritical pane, so we need to use the pane, not
                # the Frame
                oPart1 = oPart1.get_parent()
        else:
            # Replace right child of last added pane when no
            # obvious option
            oPart1 = oParent.get_child2()
        return oPart1, oParent

    def _do_replace_pane(self, oParent, oPart1, oNewPane, iConfigPos):
        """Handle the nitty gritty of replacing a pane in the window"""
        if oPart1 == oParent.get_child1():
            oParent.remove(oPart1)
            oParent.add1(oNewPane)
            # Going to the left of the current pane,
            iPos = oParent.get_position() // 2
        else:
            oParent.remove(oPart1)
            oParent.add2(oNewPane)
            oCur = oParent.get_allocation()
            if oCur.width == 1 and oParent.get_position() > 1 and \
                    iConfigPos == -1:
                # we are in early startup, so we can move the
                # Parent as well
                # We want to split ourselves into equally sized
                # sections
                oCur = self._oVBox.get_allocation()
                iPos = oCur.width // (len(self._aHPanes) + 2)
                self.set_pos_for_all_hpanes(iPos)
            else:
                iPos = (oCur.width - oParent.get_position()) // 2
        return iPos

    def add_pane(self, bVertical=False, iConfigPos=-1):
        """Add a blank frame to the window.

           bVertical -> set True to split the current pane vertically
           iConfigPos -> Layout parameter for restoring positions.
           if iConfigPos == -1, the currently focussed frame is
           halved in size.
           """
        # this is a complex function (arguably too complex). Simplifying
        # it is non trivial
        oWidget = BasicFrame(self)
        oWidget.add_parts()
        oWidget.frame_setup()
        oWidget.set_focus_handler(self.win_focus)
        self._iCount += 1
        sKey = 'Blank Pane:' + str(self._iCount)
        oWidget.set_title(sKey)
        self.aOpenFrames.append(oWidget)
        if len(self.aOpenFrames) == 1:
            # We have a blank space to fill, so just plonk in the widget
            self._oVBox.pack_start(oWidget, True, True, 0)
        else:
            # We already have a widget, so we add a pane
            if bVertical:
                oNewPane = Gtk.VPaned()
                oCurAlloc = self._oVBox.get_allocation()
                oMenuAlloc = self._oMenu.get_allocation()
                iPos = (oCurAlloc.height - oMenuAlloc.height) // 2
            else:
                oNewPane = Gtk.HPaned()
            if self._aHPanes:
                # We pop out the current frame, and plonk it in
                # the new pane - we add the new widget to the other
                # part
                oPart1, oParent = self._get_pane_to_replace()
                iTPos = self._do_replace_pane(oParent, oPart1, oNewPane,
                                              iConfigPos)
                if not bVertical:
                    iPos = iTPos
            else:
                # This is the first HPane, or the 1st VPane we add, so
                # vbox has 2 children
                # The menu, and the one we want
                oPart1 = self.top_level_panes()[0]
                oParent = self._oVBox
                # Just split the window
                oCur = oParent.get_allocation()
                if not bVertical:
                    iPos = oCur.width // 2
                oParent.remove(oPart1)
                oParent.pack_start(oNewPane, True, True, 0)
            oNewPane.add1(oPart1)
            oNewPane.add2(oWidget)
            oPart1.show()
            oNewPane.show()
            oParent.show()
            if not bVertical:
                self._aHPanes.append(oNewPane)
            if iConfigPos == -1:
                oNewPane.set_position(iPos)
            else:
                oNewPane.set_position(iConfigPos)
        self._oVBox.show()
        self.reset_menu()
        # Reset frame focussed state
        if self._oFocussed:
            self.win_focus(None, None, self._oFocussed)
        return oWidget

    def remove_frame(self, oFrame, bForceZero=False, bClose=False):
        """Remove the Frame oFrame from the window.

           bForceZero is used to force the removal of the last widget in
           the window.

           bClose is used to add the frame to the list of closed frames
           rather than destroying it and cleaning it up.
           """
        if oFrame is not None and oFrame in self.aOpenFrames:
            oNeighbour = self._find_prev_frame(oFrame)
            if len(self.aOpenFrames) == 1:
                if not bForceZero:
                    # Break out, as we do nothing
                    return
                # Removing last widget, so just clear the vbox
                oWidget = self.top_level_panes()[0]
                self._oVBox.remove(oWidget)
            elif isinstance(oFrame.get_parent(), Gtk.VPaned):
                # Removing a vertical frame, keep the correct child
                oParent = oFrame.get_parent()
                oKept = [x for x in oParent.get_children() if x != oFrame][0]
                oHPane = oParent.get_parent()
                oHPane.remove(oParent)
                oParent.remove(oFrame)
                oParent.remove(oKept)
                oHPane.add(oKept)
            elif len(self._aHPanes) == 1:
                # Removing from the only pane, so keep the other pane
                oThisPane = self._aHPanes[0]  # Only pane
                self._aHPanes.remove(oThisPane)
                oKept = [x for x in oThisPane.get_children() if x != oFrame][0]
                # clear out pane
                oThisPane.remove(oFrame)
                oThisPane.remove(oKept)
                self._oVBox.remove(oThisPane)
                self._oVBox.pack_start(oKept, True, True, 0)
            else:
                oFocussedPane = [x for x in self._aHPanes if oFrame in
                                 x.get_children()][0]
                oKept = [x for x in oFocussedPane.get_children() if
                         x != oFrame][0]
                oParent = oFocussedPane.get_parent()
                oParent.remove(oFocussedPane)
                oFocussedPane.remove(oKept)
                oParent.add(oKept)
                # Housekeeping
                oFocussedPane.remove(oFrame)
                self._aHPanes.remove(oFocussedPane)
            self._oVBox.show()
            # Remove from list of open panes
            self.aOpenFrames.remove(oFrame)
            # Any cleanup events we need?
            if bClose:
                self.aClosedFrames.append(oFrame)
            else:
                oFrame.cleanup()
            if oFrame == self._oFocussed:
                if oNeighbour != oFrame:
                    # Removing the focussed frame, so we move
                    self.win_focus(None, None, oNeighbour)
                else:
                    # Can't do better than this, really
                    self.win_focus(None, None, None)
            self.reset_menu()
        elif oFrame in self.aClosedFrames and not bClose:
            self.aClosedFrames.remove(oFrame)
            # Need to remove button from the toolbar
            self._oToolbar.remove_frame_button(oFrame.title)
            oFrame.cleanup()

    def set_all_panes_equal(self):
        """Evenly distribute the space between all the frames."""
        oCurAlloc = self._oVBox.get_allocation()
        iNewPos = oCurAlloc.width // (len(self._aHPanes) + 1)
        self.set_pos_for_all_hpanes(iNewPos)

    def set_pos_for_all_hpanes(self, iNewPos):
        """Set all the panes to the same Position value"""
        oCurAlloc = self._oVBox.get_allocation()
        oMenuAlloc = self._oMenu.get_allocation()
        iVertPos = (oCurAlloc.height - oMenuAlloc.height) // 2

        def set_pos_children(oPane, iPos, iVertPos):
            """Walk the tree in display order, setting positions accordingly"""
            oChild1 = oPane.get_child1()
            oChild2 = oPane.get_child2()
            if isinstance(oChild1, Gtk.HPaned):
                iMyPos = iPos + set_pos_children(oChild1, iPos, iVertPos)
            else:
                if isinstance(oChild1, Gtk.VPaned):
                    oChild1.set_position(iVertPos)
                iMyPos = iPos
            oPane.set_position(iMyPos)
            if isinstance(oChild2, Gtk.HPaned):
                iMyPos += set_pos_children(oChild2, iPos, iVertPos)
            elif isinstance(oChild2, Gtk.VPaned):
                oChild2.set_position(iVertPos)
            return iMyPos

        aTopLevelPanes = self.top_level_panes()
        for oPane in aTopLevelPanes:
            # Should only be 1 here
            if isinstance(oPane, Gtk.HPaned):
                set_pos_children(oPane, iNewPos, iVertPos)
            elif isinstance(oPane, Gtk.VPaned):
                # Do something sensible for single VPane case
                oPane.set_position(iVertPos)

    def set_busy_cursor(self):
        """Set the window cursor to indicate busy status"""
        # This needs to be on the top level widget, so has to be here
        # Safe-guard for if we're called while shutting down
        oWin = self.get_window()
        if oWin:
            oWin.set_cursor(self._oBusyCursor)
            # Since we're about to do a bunch of CPU grinding, tell Gtk
            # to redraw now
            Gdk.flush()

    def restore_cursor(self):
        """Restore the ordinary cursor"""
        # Safe-guard for if we're called while shutting down
        oWin = self.get_window()
        if oWin:
            oWin.set_cursor(None)

    def minimize_to_toolbar(self, oFrame):
        """Minimize the given frame to the main menu"""
        # don't allow last frame to be minimized
        if len(self.aOpenFrames) == 1:
            return
        self._oToolbar.frame_to_toolbar(oFrame, oFrame.title)
        self.remove_frame(oFrame, bClose=True)

    def restore_from_toolbar(self, oFrame):
        """Restore the given frame from the toolbar"""
        oNewPane = self.add_pane_end()
        self.replace_frame(oNewPane, oFrame)
        self.win_focus(None, None, oFrame)
