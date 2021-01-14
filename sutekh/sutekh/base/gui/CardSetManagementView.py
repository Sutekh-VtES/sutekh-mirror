# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Gtk.TreeView class for the card set list."""

from gi.repository import Gtk, Gdk

from sqlobject import SQLObjectNotFound

from ..core.BaseAdapters import IPhysicalCardSet
from .GuiCardSetFunctions import reparent_card_set
from .CardSetsListView import CardSetsListView
from .FilterDialog import FilterDialog


class CardSetManagementView(CardSetsListView):
    """Tree View for the management of card set list."""
    # pylint: disable=too-many-public-methods, too-many-instance-attributes
    # Gtk.Widget, so many public methods
    # We need to track a fair amount of state, so many attributes
    # pylint: disable=too-many-ancestors
    # many ancestors, due to our object hierachy on top of the quite
    # deep Gtk one

    def __init__(self, oController, oMainWindow):
        super().__init__(oController, oMainWindow)

        # Selecting rows
        self.set_select_single()

        # Need this so we can drag the pane in the same way as the card list
        self.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, [],
                             Gdk.DragAction.COPY)
        self.drag_source_add_text_targets()

        self.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        self.drag_dest_add_text_targets()

        self.connect('drag-data-get', self.drag_card_set)
        self.connect('row-activated', self.row_clicked)
        self.connect('drag-data-received', self.card_set_drop)

        self.set_name('card set management view')

    def make_drag_icon(self, oWidget, oDragContext):
        """Drag begin signal handler to set custom icon"""
        sSetName = self.get_selected_card_set()
        if sSetName:
            # defer to CustomDragIcon
            super().make_drag_icon(oWidget, oDragContext)
        else:
            # use pane icon
            self.frame.make_drag_icon(self, oDragContext)

    # pylint: disable=too-many-arguments
    # arguments as required by the function signature
    def drag_card_set(self, oBtn, oDragContext, oSelectionData, oInfo, oTime):
        """Allow card sets to be dragged to a frame."""
        sSetName = self.get_selected_card_set()
        if not sSetName:
            # Pass over to the frame handler
            self._oController.frame.create_drag_data(oBtn, oDragContext,
                                                     oSelectionData, oInfo,
                                                     oTime)
            return
        sData = "\n".join(['Card Set:', sSetName])
        oSelectionData.set_text(sData, -1)

    def card_set_drop(self, oWidget, oContext, iXPos, iYPos, oData, oInfo,
                      oTime):
        """Default drag-n-drop handler."""
        # Pass off to the Frame Handler
        sData = oData.get_text()
        if not sData:
            # Abort
            oContext.finish(False, False, oTime)
            return
        sSource, aData = self.split_selection_data(sData)
        bDragRes = False
        if sSource == "Basic Pane:":
            self._oController.frame.drag_drop_handler(oWidget, oContext,
                                                      iXPos, iYPos, oData,
                                                      oInfo, oTime)
            return
        if sSource == "Card Set:":
            # Find the card set at iXPos, iYPos
            # Need to do this to avoid headers and such confusing us
            oPath = self.get_path_at_pointer(oContext.get_device())
            if oPath:
                sThisName = aData[1]
                try:
                    oDraggedCS = IPhysicalCardSet(sThisName)
                    oParentCS = IPhysicalCardSet(
                        self._oModel.get_name_from_path(oPath))
                    if reparent_card_set(oDraggedCS, oParentCS):
                        # Use frame reload to keep scroll position
                        self.frame.reload()
                        oPath = self._oModel.get_path_from_name(sThisName)
                        # Make newly dragged set visible
                        if oPath:
                            self.expand_to_path(oPath)
                        bDragRes = True  # drop succeeded
                except SQLObjectNotFound:
                    pass
        oContext.finish(bDragRes, False, oTime)

    def row_clicked(self, _oTreeView, oPath, _oColumn):
        """Handle row clicked events.

           allow double clicks to open a card set.
           """
        sName = self._oModel.get_name_from_path(oPath)
        self._oMainWin.add_new_physical_card_set(sName)

    # pylint: enable=too-many-arguments

    def get_path_at_pointer(self, oDevice):
        """Get the path at the current pointer position"""
        _oWin, iXPos, iYPos, _oMask = \
            self.get_bin_window().get_device_position(oDevice)
        tRes = self.get_path_at_pos(iXPos, iYPos)
        if tRes:
            return tRes[0]
        return None

    # Filtering

    def _get_filter_dialog(self, sDefaultFilter):
        """Create the filter dialog for this view."""
        self._oFilterDialog = FilterDialog(self._oMainWin, self._oConfig,
                                           self._oController.filtertype,
                                           sDefaultFilter)
        return True
