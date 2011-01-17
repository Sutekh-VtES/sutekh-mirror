# CardSetManagementView.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""gtk.TreeView class for the card set list."""

import gtk
from sqlobject import SQLObjectNotFound
from sutekh.core.SutekhObjects import IPhysicalCardSet
from sutekh.gui.GuiCardSetFunctions import reparent_card_set
from sutekh.gui.CardSetsListView import CardSetsListView
from sutekh.gui.FilterDialog import FilterDialog


class CardSetManagementView(CardSetsListView):
    """Tree View for the management of card set list."""
    # pylint: disable-msg=R0904, R0902, R0901
    # R0904 - gtk.Widget, so many public methods
    # R0902 - We need to track a fair amount of state, so many attributes
    # R0901 - many ancestors, due to our object hierachy on top of the quite
    # deep gtk one

    def __init__(self, oController, oMainWindow):
        super(CardSetManagementView, self).__init__(oController,
                oMainWindow)

        # Selecting rows
        self.set_select_single()

        # Drag and Drop
        aTargets = [('STRING', 0, 0),       # second 0 means TARGET_STRING
                     ('text/plain', 0, 0)]  # and here

        # Need this so we can drag the pane in the same way as the card list
        self.drag_source_set(gtk.gdk.BUTTON1_MASK | gtk.gdk.BUTTON3_MASK,
                             aTargets,
                             gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        self.enable_model_drag_dest(aTargets,
                gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        self.connect('drag_data_get', self.drag_card_set)
        self.connect('row_activated', self.row_clicked)
        self.connect('drag_data_received', self.card_set_drop)

        self.set_name('card set management view')

    def make_drag_icon(self, oWidget, oDragContext):
        """Drag begin signal handler to set custom icon"""
        sSetName = self.get_selected_card_set()
        if sSetName:
            # defer to CustomDragIcon
            super(CardSetManagementView, self).make_drag_icon(oWidget,
                    oDragContext)
        else:
            # use pane icon
            self.frame.make_drag_icon(self, oDragContext)

    # pylint: disable-msg=R0913
    # arguments as required by the function signature
    def drag_card_set(self, oBtn, oDragContext, oSelectionData, oInfo, oTime):
        """Allow card sets to be dragged to a frame."""
        sSetName = self.get_selected_card_set()
        if not sSetName:
            # Pass over to the frame handler
            self._oController.frame.create_drag_data(oBtn, oDragContext,
                    oSelectionData, oInfo, oTime)
            return
        sData = "\n".join(['Card Set:', sSetName])
        oSelectionData.set(oSelectionData.target, 8, sData)

    def card_set_drop(self, oWidget, oContext, iXPos, iYPos, oData, oInfo,
            oTime):
        """Default drag-n-drop handler."""
        # Pass off to the Frame Handler
        sSource, aData = self.split_selection_data(oData.data)
        bDragRes = False
        if sSource == "Sutekh Pane:":
            self._oController.frame.drag_drop_handler(oWidget, oContext,
                    iXPos, iYPos, oData, oInfo, oTime)
            return
        elif sSource == "Card Set:":
            # Find the card set at iXPos, iYPos
            # Need to do this to avoid headers and such confusing us
            oPath = self.get_path_at_pointer()
            if oPath:
                sThisName = aData[1]
                # pylint: disable-msg=W0704
                # doing nothing on SQLObjectNotFound seems the best choice
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

    # pylint: enable-msg=R0913

    def get_path_at_pointer(self):
        """Get the path at the current pointer position"""
        iXPos, iYPos, _oIgnore = self.get_bin_window().get_pointer()
        tRes = self.get_path_at_pos(iXPos, iYPos)
        if tRes:
            return tRes[0]
        return None

    # Filtering

    def _get_filter_dialog(self, sDefaultFilter):
        """Create the filter dialog for this view."""
        self._oFilterDialog = FilterDialog(self._oMainWin, self._oConfig,
                self._oController.filtertype, sDefaultFilter)
        return True
