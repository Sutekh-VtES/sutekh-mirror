# CustomDragIconView.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2010 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""gtk.TreeView class implementing a custom drag icon."""

import gtk


class CustomDragIconView(gtk.TreeView):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """Base class for tree views that fiddle with the drag icon"""

    def __init__(self, oModel):
        self._oModel = oModel
        super(CustomDragIconView, self).__init__(self._oModel)

        # Selecting rows
        self._oSelection = self.get_selection()
        self._aOldSelection = []
        self.bReentrant = False

        # We want to be at the end of the chain, so we can fiddle with the
        # icon after gtk_tree_view sets it
        self.connect_after('drag_begin', self.make_drag_icon)
        self.connect_after('drag_motion', self.drag_motion)

    def make_drag_icon(self, _oWidget, _oDragContext):
        """Drag begin signal handler to set custom icon"""
        # NB: The pygtk docs are wrong (at least for gtk 2.20), as the
        # base gtk_tree_create_row_drag_icon method isn't overridden by
        # subclasses
        # This has to be connected via connect_after as it needs to be
        # called after the stock TreeView drag begin signal so that doesn't
        # overwrite our icon

        iNumSelected = self._oSelection.count_selected_rows()
        # Logic is - if we have multiple rows selected, used the stock
        # DND_MULTIPLE icon, otherwise ensure that the icon reflects the
        # correct text as multiple selection fiddling can cause it to be
        # wrong
        if iNumSelected > 1:
            self.drag_source_set_icon_stock(gtk.STOCK_DND_MULTIPLE)
        elif iNumSelected == 1:
            _oModel, aSelectedRows = self._oSelection.get_selected_rows()
            # Create icon from correct path
            # FIXME: gtk comments suggest this may leak, although docs
            # don't mention this - something to watch for
            oDrawable = self.create_row_drag_icon(aSelectedRows[0])
            self.drag_source_set_icon(oDrawable.get_colormap(), oDrawable)
        # We don't change anything in the nothing selected case

    # pylint: disable-msg=R0201
    # needs to be a method, as children can override this if needed
    def drag_motion(self, _oWidget, oDrag_context, _iXPos, _iYPos,
            _oTimestamp):
        """Set appropriate context during drag + drop."""
        if 'STRING' in oDrag_context.targets:
            oDrag_context.drag_status(gtk.gdk.ACTION_COPY)
            return True
        return False

    # Helper method for implementing custom selection behaviour
    def row_selected(self, oSelection):
        """Change the selection behaviour.

           If we have multiple rows selected, and the user selects
           a single row that is in the selection, we DON'T change
           the selection, but we do update the card text and so on.
           """
        if self.bReentrant:
            # This is here because we alter the selection inside
            # this function (resulting in a nested call).
            # self.bReentrant is set and unset below.
            return None

        # If the selection is empty, clear everything and return
        if oSelection.count_selected_rows() <= 0:
            self._aOldSelection = []
            return None

        _oModel, aList = oSelection.get_selected_rows()
        # Implement the non default selection behaviour.
        tCursorPos = self.get_cursor()
        if len(aList) == 1 and len(self._aOldSelection) > 1 and \
            tCursorPos[0] == aList[0] and aList[0] in self._aOldSelection:
            # reset the list to it's previous state, but set
            # displayed card to this one
            try:
                self.bReentrant = True
                for oPath in self._aOldSelection:
                    oSelection.select_path(oPath)
            finally:
                self.bReentrant = False
            oPath = aList[0]
        else:
            _oModel, aList = oSelection.get_selected_rows()
            if not aList:
                self._aOldSelection = []
                return None

            if len(aList) <= len(self._aOldSelection):
                oPath = aList[-1]
            else:
                # Find the last entry in aList that's not in _aOldSelection
                oPath = [x for x in aList if x not in self._aOldSelection][-1]
            self._aOldSelection = aList
        return oPath
