# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Gtk.TreeView classes for displaying the card list."""

from gi.repository import Gtk, Gdk

from .FilteredView import FilteredView
from .FilterDialog import FilterDialog
from ..core.BaseTables import PhysicalCard, AbstractCard
from ..core.BaseAdapters import IPhysicalCard
from ..Utility import to_ascii


class CardListView(FilteredView):
    """Base class for all the card list views in Sutekh."""
    # pylint: disable=too-many-public-methods, too-many-instance-attributes
    # Gtk.Widget, so many public methods
    # We need to track a fair amount of state, so many attributes
    # pylint: disable=too-many-ancestors
    # many ancestors, due to our object hierachy on top of the quite
    # deep Gtk one

    def __init__(self, oController, oMainWindow, oModel, oConfig):
        super().__init__(oController, oMainWindow, oModel, oConfig)

        self.set_select_multiple()

        self._oSelection.connect('changed', self.card_selected)

        # Only enable icons if it's available (so we don't break GuiCardLookup)
        if hasattr(oMainWindow, 'icon_manager') and \
                hasattr(oModel, 'oIconManager'):
            oModel.oIconManager = oMainWindow.icon_manager

        self._oSelection.set_select_function(self.can_select)

        # Activating rows
        self.connect('row-activated', self.card_activated)

        # special handling for select all
        self.connect('select-all', self.select_all)
        # Key combination for searching

        # Drag and Drop
        self.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, [],
                             Gdk.DragAction.COPY)
        self.drag_source_add_text_targets()

        self.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        self.drag_dest_add_text_targets()

        self.connect('drag-data-get', self.drag_card)
        self.connect('drag-data-delete', self.drag_delete)
        self.connect('drag-data-received', self.card_drop)
        self.bSelectTop = 0

    def can_select(self, _oSelection, _oModel, oPath, _bCurrently):
        """disable selecting top level rows"""
        if self.bSelectTop > 0:
            # Buggy Gtk version work-around
            self.bSelectTop -= 1
            return True
        # In general, we don't allow the top level nodes to be selected
        return self._oModel.iter_parent(self._oModel.get_iter(oPath)) is \
            not None

    def card_selected(self, oSelection):
        """Change the selection behaviour.

           If we have multiple rows selected, and the user selects
           a single row that is in the selection, we DON'T change
           the selection, but we do update the card text and so on.
           """
        # Check with helper function first
        oPath = self.row_selected(oSelection)
        if not oPath:
            return

        # Change card text view as required
        oPhysCard = self._oModel.get_physical_card_from_path(oPath)
        if oPhysCard:
            self._oController.set_card_text(oPhysCard)

    def process_selection(self):
        """Create a dictionary from the selection.

           Entries are of the form oAbsId : {oPhysId: iCount1, ... }
           for use in drag-'n drop and elsewhere.

           We use ids to avoid various encoding issues
           """
        oModel, aPathList = self._oSelection.get_selected_rows()
        dSelectedData = {}
        for oPath in aPathList:
            oIter = oModel.get_iter(oPath)
            iDepth = oModel.iter_depth(oIter)
            if iDepth == 0:
                # Skip top level items, since they're meaningless for the
                # selection
                continue
            oAbsCard = oModel.get_abstract_card_from_iter(oIter)
            oPhysCard = oModel.get_physical_card_from_iter(oIter)
            iCount = oModel.get_card_count_from_iter(oIter)
            # if a card is selected, then it's children (which are
            # the expansions) which are selected are ignored, since
            # We always treat this as all cards selected
            dSelectedData.setdefault(oAbsCard.id, {})
            if iDepth == 1:
                # Remove anything already assigned to this,
                # since parent overrides all
                dSelectedData[oAbsCard.id].clear()
                aChildren = oModel.get_child_entries_from_iter(oIter)
                if len(aChildren) != 1:
                    # If there's more than 1 child, just go with unknown,
                    # as only sensible default
                    dSelectedData[oAbsCard.id][-1] = iCount
                else:
                    # Otherwise, use the child, so filtering on
                    # physical expansion works as expected.
                    oChildCard, iCount = aChildren[0]
                    dSelectedData[oAbsCard.id][oChildCard.id] = iCount
            else:
                if -1 in dSelectedData[oAbsCard.id]:
                    continue
                dSelectedData[oAbsCard.id][oPhysCard.id] = iCount
        return dSelectedData

    def get_selection_as_string(self):
        """Get a string representing the current selection.

           Because of how pyGtk handles drag-n-drop data, we need to
           create a string representating the card data."""
        if self._oSelection.count_selected_rows() < 1:
            return ''
        dSelectedData = self.process_selection()
        # Create selection data structure
        # Need to bung everything into a string, alas
        sSelectData = self.sDragPrefix
        for oAbsCardID in dSelectedData:
            for oPhysCardId, iCount in dSelectedData[oAbsCardID].items():
                sSelectData += '\n%(count)d x  %(abscard)d x %(physcard)d' % {
                    'count': iCount,
                    'abscard': oAbsCardID,
                    'physcard': oPhysCardId,
                }
        return sSelectData

    # Drag and Drop
    # Sub-classes should override as needed.

    def split_selection_data(self, sSelectionData):
        """Helper function to subdivide selection string into bits again"""
        # Construct list of (iCount, oPhysCard) tuples
        def true_card(iPhysCardID, oAbsCard):
            """Convert back from the 'None' placeholder in the string"""
            # The logic goes that, if the user has dragged the top level cards,
            # Then either all the cards are going to be copied, or there is
            # no expansion info, so the expansion might as well be none.
            if iPhysCardID == -1:
                return IPhysicalCard((oAbsCard, None))
            return PhysicalCard.get(iPhysCardID)

        sSource, aLines = super().split_selection_data(sSelectionData)
        if sSource in ("None", "Basic Pane:", "Card Set:"):
            # Not cards that were dragged, so just return
            return sSource, aLines
        aCardInfo = []
        for sLine in aLines[1:]:
            iCount, iAbsID, iPhysID = [int(x) for x in sLine.split(' x ')]
            oAbsCard = AbstractCard.get(iAbsID)
            oPhysCard = true_card(iPhysID, oAbsCard)
            aCardInfo.append((iCount, oPhysCard))
        return sSource, aCardInfo

    # pylint: disable=too-many-arguments
    # arguments as required by the function signature

    def drag_card(self, oBtn, oContext, oSelectionData, oInfo, oTime):
        """Create string representation of the selection for drag-n-drop"""
        sSelectData = self.get_selection_as_string()
        if sSelectData == '':
            # Pass over to the frame handler
            self._oController.frame.create_drag_data(oBtn, oContext,
                                                     oSelectionData, oInfo,
                                                     oTime)
            return
        oSelectionData.set_text(sSelectData, -1)

    def drag_delete(self, oBtn, oContext):
        """Default drag-delete handler"""
        pass

    def card_drop(self, oWdgt, oContext, iXPos, iYPos, oData, oInfo, oTime):
        """Default drag-n-drop handler."""
        # Pass off to the Frame Handler
        self._oController.frame.drag_drop_handler(oWdgt, oContext, iXPos,
                                                  iYPos, oData, oInfo, oTime)

    def copy_selection(self):
        """Copy the current selection to the application clipboard"""
        sSelection = self.get_selection_as_string()
        self._oMainWin.set_selection_text(sSelection)

    # Card name searching

    def compare(self, oModel, _iColumn, sKey, oIter, _oData):
        """Compare the entered text to the card names."""
        if oModel.iter_depth(oIter) == 2:
            # Don't succeed for expansion items
            return True

        oPath = oModel.get_path(oIter)
        sKey = sKey.lower()
        iLenKey = len(sKey)

        if oModel.iter_depth(oIter) == 0:
            if self.row_expanded(oPath):
                # Don't succeed for expanded top level items
                return True
            # Need to check if any of the children match
            oChildIter = self._oModel.iter_children(oIter)
            while oChildIter:
                sChildName = self._oModel.get_name_from_iter(oChildIter)
                sChildName = sChildName[:iLenKey].lower()
                if (to_ascii(sChildName).startswith(sKey) or
                        sChildName.startswith(sKey)):
                    # Expand the row
                    self.expand_to_path(oPath)
                    # Bail out, as compare will find the match for us
                    return True
                oChildIter = self._oModel.iter_next(oChildIter)
            return True  # No matches, so bail

        sCardName = self._oModel.get_name_from_iter(oIter)[:iLenKey].lower()
        if (to_ascii(sCardName).startswith(sKey) or
                sCardName.startswith(sKey)):
            return False

        return True

    # pylint: enable=too-many-arguments

    # Activating Rows
    def card_activated(self, _oTree, oPath, _oColumn):
        """Update card text and notify listeners when a card is selected."""
        oPhysCard = self._oModel.get_physical_card_from_path(oPath)
        if oPhysCard:
            self._oController.set_card_text(oPhysCard)

    # Selecting

    def force_cursor_move(self, _oTreeView, _iStep, _iCount):
        """Special handling for move events for buggy Gtk events.

           We need to allow the selection of top level items when
           moving the cursor over them
           """
        oCurPath, _oColumn = self.get_cursor()
        if self._oModel.iter_parent(self._oModel.get_iter(oCurPath)) is None:
            # Root node, so need to force the move
            self.bSelectTop = 2
            # Need to succeed twice - once to select, once to unselect
            # I don't quite understand why this works this way, but it
            # does
            self._oSelection.select_path(oCurPath)
        # Let Gtk handle the rest of the move, since we're not doing
        # anything else funky
        return False

    # Filtering

    def _get_filter_dialog(self, sDefaultFilter):
        """Create the filter dialog for this view."""
        self._oFilterDialog = FilterDialog(self._oMainWin, self._oConfig,
                                           self._oController.filtertype,
                                           sDefaultFilter)
        return True

    def make_drag_icon(self, _oWidget, oDragContext):
        """Custom drag icon for dragging cards"""
        # We use STOCK_DND_MULTIPLE for multiple cards, otherwise
        # STOCK_DND for single row selected
        iNumSelected = self._oSelection.count_selected_rows()
        if iNumSelected > 1:
            self.drag_source_set_icon_stock(Gtk.STOCK_DND_MULTIPLE)
        elif iNumSelected == 1:
            self.drag_source_set_icon_stock(Gtk.STOCK_DND)
        else:
            # Nothing selected, so we're dragging the entire pane, so use
            # the pane icon
            self.frame.make_drag_icon(self, oDragContext)

    def select_all(self, _oWidget):
        """Expand the tree and select all the nodes"""
        self.expand_all()
        self._oSelection.select_all()
