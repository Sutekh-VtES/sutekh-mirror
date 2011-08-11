# CardListView.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""gtk.TreeView classes for displaying the card list."""

import gtk
from sutekh.gui.FilteredView import FilteredView
from sutekh.gui.FilterDialog import FilterDialog


class CardListView(FilteredView):
    """Base class for all the card list views in Sutekh."""
    # pylint: disable-msg=R0904, R0902, R0901
    # R0904 - gtk.Widget, so many public methods
    # R0902 - We need to track a fair amount of state, so many attributes
    # R0901 - many ancestors, due to our object hierachy on top of the quite
    # deep gtk one

    def __init__(self, oController, oMainWindow, oModel, oConfig):
        super(CardListView, self).__init__(oController, oMainWindow,
                oModel, oConfig)

        self.set_select_multiple()

        self._oSelection.connect('changed', self.card_selected)

        # Only enable icons if it's available (so we don't break GuiCardLookup)
        if hasattr(oMainWindow, 'icon_manager') and \
                hasattr(oModel, 'oIconManager'):
            oModel.oIconManager = oMainWindow.icon_manager

        self._oSelection.set_select_function(self.can_select)
        tGtkVersion = gtk.gtk_version
        if tGtkVersion[0] == 2 and \
                ((tGtkVersion[1] > 6 and tGtkVersion[1] < 12) or \
                (tGtkVersion[1] == 12 and tGtkVersion[2] == 0)):
            # gtk versions from 2.8 to 2.12.0 have a bug with handling
            # cursor movements, excluded selects and multiple select mode
            # ( http://bugzilla.gnome.org/show_bug.cgi?id=483730 )
            # We kludge around it via move_cursr
            self.connect('move-cursor', self.force_cursor_move)

        # Activating rows
        self.connect('row-activated', self.card_activated)

        # special handling for select all
        self.connect('select-all', self.select_all)
        # Key combination for searching

        # Drag and Drop
        aTargets = [('STRING', 0, 0),      # second 0 means TARGET_STRING
                    ('text/plain', 0, 0)]  # and here

        self.drag_source_set(gtk.gdk.BUTTON1_MASK | gtk.gdk.BUTTON3_MASK,
                             aTargets,
                             gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        self.drag_dest_set(gtk.DEST_DEFAULT_ALL,
                           aTargets,
                           gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        self.connect('drag_data_get', self.drag_card)
        self.connect('drag_data_delete', self.drag_delete)
        self.connect('drag_data_received', self.card_drop)
        self.bSelectTop = 0

    def can_select(self, oPath):
        """disable selecting top level rows"""
        if self.bSelectTop > 0:
            # Buggy gtk version work-around
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
            return False

        # Change card text view as required
        oPhysCard = self._oModel.get_physical_card_from_path(oPath)
        self._oController.set_card_text(oPhysCard)

    def process_selection(self):
        """Create a dictionary from the selection.

           Entries are of the form sCardName : {sExpansion1 : iCount1, ... }
           for use in drag-'n drop and elsewhere.
           """
        oModel, aPathList = self._oSelection.get_selected_rows()
        dSelectedData = {}
        for oPath in aPathList:
            sCardName, sExpansion, iCount, iDepth = \
                    oModel.get_all_from_path(oPath)
            if iDepth == 0:
                # Skip top level items, since they're meaningless for the
                # selection
                continue
            # if a card is selected, then it's children (which are
            # the expansions) which are selected are ignored, since
            # We always treat this as all cards selected
            dSelectedData.setdefault(sCardName, {})
            if iDepth == 1:
                # Remove anything already assigned to this,
                # since parent overrides all
                dSelectedData[sCardName].clear()
                aChildren = oModel.get_child_entries_from_path(oPath)
                if len(aChildren) != 1:
                    # If there's more than 1 child, just go with unknown,
                    # as only sensible default
                    dSelectedData[sCardName]['None'] = iCount
                else:
                    # Otherwise, use the child, so filtering on
                    # physical expansion works as expected.
                    sExpansion, iCount = aChildren[0]
                    dSelectedData[sCardName][sExpansion] = iCount

            else:
                if 'None' in dSelectedData[sCardName]:
                    continue
                dSelectedData[sCardName][sExpansion] = iCount
        return dSelectedData

    def get_selection_as_string(self):
        """Get a string representing the current selection.

           Because of how pygtk handles drag-n-drop data, we need to
           create a string representating the card data."""
        if self._oSelection.count_selected_rows() < 1:
            return ''
        dSelectedData = self.process_selection()
        # Create selection data structure
        # Need to bung everything into a string, alas
        sSelectData = self.sDragPrefix
        for sCardName in dSelectedData:
            for sExpansion, iCount in dSelectedData[sCardName].iteritems():
                sSelectData += '\n%(count)d\n%(name)s\n%(expansion)s' % {
                        'count': iCount,
                        'name': sCardName,
                        'expansion': sExpansion,
                        }
        return sSelectData

    # Drag and Drop
    # Sub-classes should override as needed.

    def split_selection_data(self, sSelectionData):
        """Helper function to subdivide selection string into bits again"""
        # Construct list of (iCount, sCardName, sExpansion) tuples
        def true_expansion(sExpand):
            """Convert back from the 'None' placeholder in the string"""
            # The logic goes that, if the user has dragged the top level cards,
            # Then either all the cards are going to be copied, or there is
            # no expansion info, so the expansion might as well be none.
            if sExpand == 'None':
                return None
            else:
                return sExpand

        sSource, aLines = \
                super(CardListView, self).split_selection_data(sSelectionData)
        if sSource in ("None", "Sutekh Pane:", "Card Set:"):
            # Not cards that were dragged, so just return
            return sSource, aLines
        aCardInfo = zip([int(x) for x in aLines[1::3]], aLines[2::3],
                [true_expansion(x) for x in aLines[3::3]])
        return sSource, aCardInfo

    # pylint: disable-msg=R0913
    # arguments as required by the function signature

    def drag_card(self, oBtn, oContext, oSelectionData, oInfo, oTime):
        """Create string representation of the selection for drag-n-drop"""
        sSelectData = self.get_selection_as_string()
        if sSelectData == '':
            # Pass over to the frame handler
            self._oController.frame.create_drag_data(oBtn, oContext,
                    oSelectionData, oInfo, oTime)
            return
        oSelectionData.set(oSelectionData.target, 8, sSelectData)

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
            else:
                # Need to check if any of the children match
                oChildIter = self._oModel.iter_children(oIter)
                while oChildIter:
                    sChildName = self._oModel.get_name_from_iter(oChildIter)
                    sChildName = sChildName[:iLenKey].lower()
                    if self.to_ascii(sChildName).startswith(sKey) or\
                        sChildName.startswith(sKey):
                        # Expand the row
                        self.expand_to_path(oPath)
                        # Bail out, as compare will find the match for us
                        return True
                    oChildIter = self._oModel.iter_next(oChildIter)
                return True  # No matches, so bail

        sCardName = self._oModel.get_name_from_iter(oIter)[:iLenKey].lower()
        if self.to_ascii(sCardName).startswith(sKey) or \
                sCardName.startswith(sKey):
            return False

        return True

    # pylint: enable-msg=R0913

    # Activating Rows
    def card_activated(self, _oTree, oPath, _oColumn):
        """Update card text and notify listeners when a card is selected."""
        oPhysCard = self._oModel.get_physical_card_from_path(oPath)
        self._oController.set_card_text(oPhysCard)

    # Selecting

    def force_cursor_move(self, _oTreeView, _iStep, _iCount):
        """Special handling for move events for buggy gtk events.

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
        # Let gtk handle the rest of the move, since we're not doing
        # anything else funky
        return False

    # Filtering

    def _get_filter_dialog(self, sDefaultFilter):
        """Create the filter dialog for this view."""
        self._oFilterDialog = FilterDialog(self._oMainWin, self._oConfig,
                self._oController.filtertype, sDefaultFilter)
        return True

    def make_drag_icon(self, _oWidget, oDragContext):
        """Custom drag icon for dragging cards"""
        # We use STOCK_DND_MULTIPLE for multiple cards, otherwise
        # STOCK_DND for single row selected
        iNumSelected = self._oSelection.count_selected_rows()
        if iNumSelected > 1:
            self.drag_source_set_icon_stock(gtk.STOCK_DND_MULTIPLE)
        elif iNumSelected == 1:
            self.drag_source_set_icon_stock(gtk.STOCK_DND)
        else:
            # Nothing selected, so we're dragging the entire pane, so use
            # the pane icon
            self.frame.make_drag_icon(self, oDragContext)

    def select_all(self, _oWidget):
        """Expand the tree and select all the nodes"""
        self.expand_all()
        self._oSelection.select_all()
