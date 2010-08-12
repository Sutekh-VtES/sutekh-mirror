# FilterModelPanes.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Handle the manipulation bits for the Filter Editor
# Copyright 2010 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Handle the panes for the filter editor"""

from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.gui.ScrolledList import ScrolledList
from sutekh.gui.CardSetsListView import CardSetsListView
from sutekh.core.FilterParser import get_filters_for_type
from sutekh.core.FilterBox import FilterBoxItem, FilterBoxModel, BOXTYPE, \
        BOXTYPE_ORDER
import gobject
import gtk

DRAG_TARGETS = [ ('STRING', 0, 0), ('text/plain', 0, 0) ]
# Filters we pad values for to sort nicely
PAD_FILTERS = ['Capacity', 'CardCount: Count']

# Drag type constants
NEW_VALUE = 'NewValue: '
MOVE_VALUE = 'MoveValue: '
MOVE_FILTER = 'MoveFilter: '
NEW_FILTER = 'NewFilter: '

class FilterModelPanes(gtk.HBox):
    """Widget to hold the different panes of the Filter editor"""
    # pylint: disable-msg=R0904
    # R0904 - gtk.Widget, so many public methods

    def __init__(self, sFilterType, oDialog):
        super(FilterModelPanes, self).__init__()
        # Create the 3 panes
        self.__oBoxModel = None
        self.__sFilterType = sFilterType
        self.__oSelectBar = FilterValuesBox(oDialog, sFilterType)
        self.__oEditBox = FilterBoxModelEditBox(self.__oSelectBar)

        self.pack_start(AutoScrolledWindow(self.__oEditBox, True), expand=True)
        self.pack_start(self.__oSelectBar, expand=True)

    def replace_ast(self, oAST):
        """Replace the AST in the tree model"""
        self.__oBoxModel = FilterBoxModel(oAST, self.__sFilterType)
        self.__oEditBox.set_box_model(self.__oBoxModel)

    def get_ast_with_values(self):
        """Get the current ast for the Editor, with values filled in"""
        if not self.__oBoxModel:
            return None

        return self.__oBoxModel.get_ast_with_values()

    def get_text(self):
        """Get the current ast"""
        if self.__oBoxModel:
            return self.__oBoxModel.get_text()
        return None


class FilterEditorToolbar(gtk.TreeView):
    """Toolbar listing the possible filter elements"""
    # pylint: disable-msg=R0904
    # R0904 - gtk.Widget, so many public methods

    def __init__(self, sFilterType):
        self.__oListStore = gtk.ListStore(gobject.TYPE_STRING,
                gobject.TYPE_STRING)
        super(FilterEditorToolbar, self).__init__(self.__oListStore)
        oTextCell = gtk.CellRendererText()
        oColumn = gtk.TreeViewColumn("Filter Element", oTextCell, text=0)
        oColumn.set_spacing(2)
        self.append_column(oColumn)
        self.__sFilterType = sFilterType
        # Get supported filters
        aFilters = [('Filter Group ..', 'Filter Group')]
        for oFilterType in sorted(get_filters_for_type(self.__sFilterType),
                key=lambda x: x.description):
            aFilters.append((oFilterType.description, oFilterType.keyword))
        self.enable_model_drag_source(
                gtk.gdk.BUTTON1_MASK | gtk.gdk.BUTTON3_MASK,
                DRAG_TARGETS, gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
        # Create entries for each of the filters we support
        for tInfo in aFilters:
            self.__oListStore.append(tInfo)

        self.connect('drag_data_get', self.drag_filter)
        self.get_selection().set_mode(gtk.SELECTION_SINGLE)

    def drag_filter(self, _oBtn, _oContext, oSelectionData, _oInfo, _oTime):
        """Create a drag info for this filter"""
        _oModel, oIter = self.get_selection().get_selected()
        if oIter:
            sSelect = '%s%s' % (NEW_FILTER,
                    self.__oListStore.get_value(oIter, 1))
            oSelectionData.set(oSelectionData.target, 8, sSelect)

class FilterValuesBox(gtk.VBox):
    """Holder for the value setting objects"""
    # pylint: disable-msg=R0904, R0902
    # R0904 - gtk.Widget, so many public methods
    # R0902: We need to keep a lot of state to handle all the cases

    def __init__(self, oDialog, sFilterType):
        super(FilterValuesBox, self).__init__()
        self._oEmptyWidget = gtk.VBox()
        self._oNoneWidget = gtk.VBox()
        self._oParent = oDialog
        self.__sFilterType = sFilterType
        self._oEmptyWidget.pack_start(gtk.Label(
            'Select an active\nfilter element'), expand=False)
        self._oNoneWidget.pack_start(gtk.Label(
            'No values for this filter'), expand=False)
        # Handle removing none file elements
        self._set_drop_for_widget(self._oNoneWidget)
        self._oFilter = None
        self._oBoxModelEditor = None
        self._aLastSelection = []
        oCheckBox = gtk.HBox()
        self.__oDisable = gtk.CheckButton('Disable')
        self.__oNegate = gtk.CheckButton('Negate')
        self.__oDelete = gtk.Button('Delete Filter')

        self.__oDisable.set_sensitive(False)
        self.__oDelete.set_sensitive(False)
        self.__oNegate.set_sensitive(False)

        oCheckBox.pack_start(self.__oDisable, expand=True)
        oCheckBox.pack_start(self.__oNegate, expand=True)
        self.pack_start(oCheckBox, expand=False)
        self.pack_start(self.__oDelete, expand=False)
        self.__oDisable.connect('toggled', self.toggle_disabled)
        self.__oDelete.connect('clicked', self.delete)
        self.__oNegate.connect('toggled', self.toggle_negate)

        self._oWidget = self._oEmptyWidget
        self.pack_start(self._oWidget, expand=True)
        self.show_all()

    def _set_drop_for_widget(self, oWidget):
        """Set the correct drop dest behaviour for the given widget"""
        oViewWidget = self._get_view_widget(oWidget)
        oViewWidget.drag_dest_set(gtk.DEST_DEFAULT_ALL, DRAG_TARGETS,
                gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
        oViewWidget.connect('drag_data_received', self.drag_drop_handler)

    # pylint: disable-msg=R0201
    # Methods for consistency

    def _set_drag_for_widget(self, oWidget, fCallback, oFilter):
        """Set the correct drag source behaviour for the widget"""
        oViewWidget = self._get_view_widget(oWidget)
        oViewWidget.drag_source_set(
                gtk.gdk.BUTTON1_MASK | gtk.gdk.BUTTON3_MASK, DRAG_TARGETS,
                gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
        oViewWidget.connect('drag_data_get', fCallback, oFilter, oWidget)

    def _get_view_widget(self, oWidget):
        """Helper function to get view from widget if needed"""
        oSetWidget = oWidget
        if hasattr(oWidget, 'view'):
            oSetWidget = oWidget.view
        return oSetWidget

    # pylint: enable-msg=R0201

    def _make_filter_group_list(self, oFilter):
        """Create the toolbar for the filter group"""
        self._oWidget = gtk.VBox()
        oFilterTypes = ScrolledList('Filter Group Type')
        oFilterTypes.set_select_single()
        oFilterTypes.fill_list(BOXTYPE_ORDER)
        self.set_box_model_value(oFilter, oFilterTypes)
        oFilterTypes.get_selection_object().connect('changed',
                self.update_box_model, oFilter, oFilterTypes)
        oFilterTypes.set_size_request(100, 150)
        self._oWidget.pack_start(oFilterTypes, expand=False)
        self._oWidget.pack_start(gtk.Label('Or Drag Filter element'),
                expand=False)
        oSubFilterList = FilterEditorToolbar(self.__sFilterType)
        self._oWidget.pack_start(AutoScrolledWindow(oSubFilterList),
                    expand=True)

    def _make_list_from(self, oFilter):
        """Create the widget for the 'X form Y' filters"""
        self._oWidget = gtk.VBox()
        oCountList = ScrolledList('Select Counts')
        oCountList.set_select_multiple()
        oCountList.fill_list(oFilter.aValues[0])
        oSetList = CardSetsListView(None, self._oParent)
        oSetList.set_select_multiple()
        self._set_drag_for_widget(oSetList, self.update_count_set, oFilter)
        self._set_drop_for_widget(oSetList)
        self._set_drag_for_widget(oCountList, self.update_count_list, oFilter)
        self._set_drop_for_widget(oCountList)
        self._oWidget.pack_start(oCountList, expand=True)
        oLabel = gtk.Label()
        oLabel.set_markup('<b>From</b>')
        self._oWidget.pack_start(oLabel, expand=False)
        self._oWidget.pack_start(AutoScrolledWindow(oSetList, False),
                expand=True)

    def _make_card_set_list(self, oFilter):
        """Create a card set list widget"""
        oSetList = CardSetsListView(None, self._oParent)
        oSetList.set_select_multiple()
        self._oWidget = AutoScrolledWindow(oSetList, False)
        self._set_drag_for_widget(oSetList, self.update_set_list, oFilter)
        self._set_drop_for_widget(oSetList)

    def _make_filter_values_list(self, oFilter):
        """Create a filter values list widget"""
        self._oWidget = ScrolledList('Select Filter Values')
        self._oWidget.set_select_multiple()
        self._oWidget.fill_list(oFilter.aValues)
        self._set_drag_for_widget(self._oWidget, self.update_filter_list,
                oFilter)
        self._set_drop_for_widget(self._oWidget)

    def _make_filter_entry(self, oFilter):
        """Create a text entry widget"""
        self._oWidget = gtk.VBox()
        self._set_drop_for_widget(self._oWidget)
        self._oWidget.pack_start(gtk.Label('Enter Text'), expand=False)
        oEntry = gtk.Entry()
        self._oWidget.pack_start(oEntry, expand=False)
        if oFilter.aCurValues:
            oEntry.set_text(oFilter.aCurValues[0])
        oEntry.connect('changed', self.update_edit_box, oFilter)

    def set_widget(self, oFilter, oBoxModelEditor):
        """Replace the current widget with the correct widget for the
           new filter"""
        self._oBoxModelEditor = oBoxModelEditor
        self._aLastSelection = []
        if self._oWidget:
            self.remove(self._oWidget)
            self._oWidget = None
        if isinstance(oFilter, FilterBoxModel):
            # Select between box options
            self.__oDisable.set_active(oFilter.bDisabled)
            self.__oNegate.set_inconsistent(True)
            self.__oNegate.set_sensitive(False)
            self._make_filter_group_list(oFilter)
        elif isinstance(oFilter, FilterBoxItem):
            self.__oDisable.set_active(oFilter.bDisabled)
            self.__oNegate.set_inconsistent(False)
            self.__oNegate.set_active(oFilter.bNegated)
            self.__oNegate.set_sensitive(True)
            if oFilter.iValueType == FilterBoxItem.LIST:
                # Select appropriate list widget for this filter
                if oFilter.sFilterName == "Card_Sets" or \
                        oFilter.sFilterName == "ParentCardSet":
                    # Special case to use card set list widget
                    self._make_card_set_list(oFilter)
                else:
                    # Ordinary list
                    self._make_filter_values_list(oFilter)
            elif oFilter.iValueType == FilterBoxItem.ENTRY:
                self._make_filter_entry(oFilter)
            elif oFilter.iValueType == FilterBoxItem.LIST_FROM:
                self._make_list_from(oFilter)
            elif oFilter.iValueType == FilterBoxItem.NONE:
                # None filter, so no selection widget, but we have buttons
                self._oWidget = self._oNoneWidget
        else:
            # No selected widget, so clear everything
            self._oWidget = self._oEmptyWidget
            self.disable_all_buttons()
        self.pack_start(self._oWidget, expand=True)
        self.show_all()

    # pylint: disable-msg=R0201
    # Methods for consistency
    def set_box_model_value(self, oBoxModel, oWidget):
        """Set the correct selection for this box model"""
        for sDesc, tInfo in BOXTYPE.iteritems():
            sBoxType, bNegate = tInfo
            if oBoxModel.sBoxType == sBoxType and oBoxModel.bNegate == bNegate:
                oWidget.set_selected(sDesc)

    # pylint: enable-msg=R0201

    def update_box_model(self, _oSelection, oBoxModel, oList):
        """Update the box model to the current selection"""
        aSelected = oList.get_selection()
        if not aSelected:
            return # We don't do anything special if nothing's selected
        for sDesc, tInfo in BOXTYPE.iteritems():
            if sDesc == aSelected[0]:
                oBoxModel.sBoxType, oBoxModel.bNegate = tInfo
        self._oBoxModelEditor.update_box_text(oBoxModel)

    # pylint: disable-msg=R0913
    # function signature requires all these arguments

    def drag_drop_handler(self, _oWindow, oDragContext, _iXPos, _iYPos,
            oSelectionData, _oInfo, oTime):
        """Handle drops from the filter toolbar"""
        bDragRes = True
        if not oSelectionData and oSelectionData.format != 8:
            bDragRes = False
        else:
            sData =  oSelectionData.data
            if not sData:
                bDragRes = False
            elif sData.startswith(MOVE_VALUE):
                # Removing a value from the list
                sIter = sData.split(':', 1)[1].strip()
                self._oBoxModelEditor.remove_value_at_iter(sIter)
            elif sData.startswith(MOVE_FILTER):
                # Removing a filter
                sIter = sData.split(':', 1)[1].strip()
                self._oBoxModelEditor.remove_filter_at_iter(sIter)
            else:
                # Not relevant
                bDragRes = False
        oDragContext.finish(bDragRes, False, oTime)

    # pylint: enable-msg=R0913

    def get_selected_values(self):
        """Get the most recent selection - used by the drop values code"""
        return self._aLastSelection

    def _format_selection(self, sSelect, aSelection):
        """Set the current selection, properly formatted for sorting"""
        sName = sSelect.replace(NEW_VALUE, '')
        if sName in PAD_FILTERS:
            # Is this the best approach?
            self._aLastSelection = ['%2s' % x for x in aSelection]
        else:
            self._aLastSelection = aSelection

    def update_filter_list(self, _oBtn, _oContext, oSelectionData,
            _oInfo, _oTime, oFilter, _oWidget):
        """Update the box model with the new values"""
        sSelect = '%s%s' % (NEW_VALUE, oFilter.sFilterName)
        self._format_selection(sSelect, self._oWidget.get_selection())
        oSelectionData.set(oSelectionData.target, 8, sSelect)

    def update_count_list(self, _oBtn, _oContext, oSelectionData,
            _oInfo, _oTime, oFilter, oCountList):
        """Update the box model with the new values"""
        sSelect = '%s%s: Count' % (NEW_VALUE, oFilter.sFilterName)
        self._format_selection(sSelect, oCountList.get_selection())
        oSelectionData.set(oSelectionData.target, 8, sSelect)

    def update_set_list(self, _oBtn, _oContext, oSelectionData,
            _oInfo, _oTime, oFilter, oSetList):
        """Update the box model to the current selection"""
        sSelect = '%s%s' % (NEW_VALUE, oFilter.sFilterName)
        self._format_selection(sSelect, oSetList.get_all_selected_sets())
        oSelectionData.set(oSelectionData.target, 8, sSelect)

    def update_count_set(self, _oBtn, _oContext, oSelectionData,
            _oInfo, _oTime, oFilter, oSetList):
        """Update the box model to the current selection"""
        sSelect = '%s%s: Set' % (NEW_VALUE, oFilter.sFilterName)
        self._format_selection(sSelect, oSetList.get_all_selected_sets())
        oSelectionData.set(oSelectionData.target, 8, sSelect)

    def update_edit_box(self, oEntry, oFilter):
        """Update the box model with the current text"""
        oFilter.aCurValues = [oEntry.get_text()]
        self._oBoxModelEditor.update_entry(oFilter)

    def toggle_negate(self, oButton):
        """Toggle the disabled flag for a section of the filter"""
        if self._oBoxModelEditor:
            self._oBoxModelEditor.set_negate(oButton.get_active())

    def toggle_disabled(self, oButton):
        """Toggle the disabled flag for a section of the filter"""
        if self._oBoxModelEditor:
            self._oBoxModelEditor.set_disabled(oButton.get_active())

    def delete(self, _oButton):
        """Delete a filter element"""
        if self._oBoxModelEditor:
            self._oBoxModelEditor.delete(None)

    def disable_all_buttons(self):
        """Disable all the buttons"""
        self.__oDisable.set_sensitive(False)
        self.__oDelete.set_sensitive(False)
        self.__oNegate.set_sensitive(False)

    def enable_delete(self):
        """Enable the delete button"""
        self.__oDelete.set_sensitive(True)

    def enable_disable(self, oFilterObj):
        """Enable the delete button"""
        self.__oDisable.set_sensitive(True)
        self.__oDisable.set_active(oFilterObj.bDisabled)

    def get_current_pos_and_sel(self):
        """Get the current scroll position and selection path in the
           sub-filter list to restore later"""

        def _get_values(oAdj):
            """Get important values out of a gtk.Adjustment"""
            return oAdj.value, oAdj.page_size

        assert len(self._oWidget.get_children()) == 3
        oScrolledWindow = self._oWidget.get_children()[2]
        oSubFilterWidget = oScrolledWindow.get_children()[0]
        _oModel, aPaths = oSubFilterWidget.get_selection().get_selected_rows()
        # We use the values, rather than the actual adjustments, to avoid a
        # race condition where gtk deletes the actual adjustment out from
        # under us
        tHorizVals = _get_values(oScrolledWindow.get_hadjustment())
        tVertVals = _get_values(oScrolledWindow.get_vadjustment())
        return tHorizVals, tVertVals, aPaths

    def restore_pos_and_selection(self, tScrollAdj):
        """Restore the selection and scrollbar position in the sub-filter
           list"""
        def _set_values(oAdj, tInfo):
            """Set the values on an adjustment"""
            oAdj.value = tInfo[0]
            oAdj.page_size = tInfo[1]
            # Send required signals
            oAdj.changed()
            oAdj.value_changed()

        assert len(self._oWidget.get_children()) == 3
        oScrolledWindow = self._oWidget.get_children()[2]
        oSubFilterWidget = oScrolledWindow.get_children()[0]
        oSelection = oSubFilterWidget.get_selection()
        # selection will be a list with 1 path
        oSelection.select_path(tScrollAdj[2][0])
        _set_values(oScrolledWindow.get_hadjustment(), tScrollAdj[0])
        _set_values(oScrolledWindow.get_vadjustment(), tScrollAdj[1])

class BoxModelPopupMenu(gtk.Menu):
    """Popup context menu for disable/ negate & delete"""
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods

    def __init__(self, oBoxModelEditor):
        super(BoxModelPopupMenu, self).__init__()
        self._oDis = gtk.MenuItem("Disable / Enable Filter")
        self._oNeg = gtk.MenuItem("Negate Filter Element")
        self._oDel = gtk.MenuItem("Delete filter")

        self._oDis.connect("activate", oBoxModelEditor.toggle_disabled)
        self._oNeg.connect("activate", oBoxModelEditor.toggle_negate)
        self._oDel.connect("activate", oBoxModelEditor.delete)
        self.append(self._oDis)
        self.append(self._oNeg)
        self.append(gtk.SeparatorMenuItem())
        self.append(self._oDel)


class FilterBoxModelStore(gtk.TreeStore):
    """TreeStore for the FilterBoxModelEditor"""
    # pylint: disable-msg=R0904
    # R0904 - gtk.Widget, so many public methods

    BLACK =  gtk.gdk.color_parse('black')
    GREY =  gtk.gdk.color_parse('grey')
    NO_VALUE = '<i>No Values Set</i>'
    NONE_VALUE = '<b>No Values for this filter</b>'

    def __init__(self):
        super(FilterBoxModelStore, self).__init__(gobject.TYPE_STRING,
                gobject.TYPE_PYOBJECT, gtk.gdk.Color)

    def _fill_values(self, oFilterIter, oModel, oColour):
        """Fill in the values for this filter"""
        if oModel.iValueType == oModel.LIST_FROM:
            # Load LIST_FROM
            aValues, aFrom = oModel.aCurValues
            if aValues:
                for sValue in aValues:
                    self.append(oFilterIter, (sValue, None, oColour))
            else:
                self.append(oFilterIter, (self.NO_VALUE, None, oColour))
            self.append(oFilterIter, ('<b>From</b>', None, oColour))
            if aFrom:
                for sValue in aFrom:
                    self.append(oFilterIter, (sValue, None, oColour))
            else:
                self.append(oFilterIter, (self.NO_VALUE, None, oColour))
        elif oModel.aCurValues and oModel.aValues:
            for sValue in oModel.aCurValues:
                self.append(oFilterIter, (sValue, None, oColour))
        elif oModel.aCurValues:
            self.append(oFilterIter, (oModel.aCurValues[0], None, oColour))
        elif oModel.iValueType == oModel.NONE:
            self.append(oFilterIter, (self.NONE_VALUE, None, oColour))
        else:
            self.append(oFilterIter, (self.NO_VALUE, None, oColour))

    def _do_add_iter(self, oIter, oModel, bDisabled):
        """Recursively add elements of the box model"""
        oThisIter = self.append(oIter)
        oColour = self.BLACK
        if hasattr(oModel, 'sFilterDesc'):
            if oModel.bNegated:
                sText = 'NOT %s' % oModel.sFilterDesc
            else:
                sText = oModel.sFilterDesc
            if oModel.bDisabled or bDisabled:
                oColour = self.GREY
            self.set(oThisIter, 0, sText, 1, oModel, 2, oColour)
            self._fill_values(oThisIter, oModel, oColour)
        elif hasattr(oModel, 'sBoxType'):
            # Box Model, so lookup correct string
            if oModel.bDisabled or bDisabled:
                oColour = self.GREY
                bDisabled = True
            for sDesc, tInfo in BOXTYPE.iteritems():
                sBoxType, bNegate = tInfo
                if oModel.sBoxType == sBoxType \
                        and oModel.bNegate == bNegate:
                    self.set(oThisIter, 0, sDesc, 1, oModel, 2, oColour)
            # iterate over children
            for oSubModel in oModel:
                self._do_add_iter(oThisIter, oSubModel, bDisabled)

    def load(self, oBoxModel):
        """Load the box model into the store"""

        self.clear()
        if oBoxModel is None:
            return
        # Walk the box model, creating items as we need them
        self._do_add_iter(None, oBoxModel, False)
        return self.get_path(self.get_iter_root())

    def update_iter_with_values(self, aValues, oSelectIter, oPath):
        """Update the given iter with the changed values"""
        oChild = self.iter_children(oSelectIter)
        oCurIter = self.get_iter(oPath)
        iPos = 0
        iIndex = -1
        while oChild:
            oNext = self.iter_next(oChild)
            if not self.get_path(oChild) == self.get_path(oCurIter):
                self.remove(oChild)
            else:
                iIndex = iPos
            oChild = oNext
            iPos += 1
        if iIndex < 0:
            # We deleted everything, so add 1 child
            oCurIter = self.append(oSelectIter)
            iIndex = 0
        if aValues:
            iIndex = min(len(aValues) - 1, iIndex)
            iPos = 0
            for sValue in aValues:
                if iPos == iIndex:
                    oChild = oCurIter
                elif iPos < iIndex:
                    oChild = self.insert_before(oSelectIter, oCurIter)
                else:
                    oChild = self.append(oSelectIter)
                if sValue is not None:
                    self.set(oChild, 0, sValue, 1, None, 2, self.BLACK)
                else:
                    self.set(oChild, 0, self.NO_VALUE, 1, None, 2, self.BLACK)
                iPos += 1
        else:
            self.set(oCurIter, 0, self.NO_VALUE, 1, None, 2, self.BLACK)
        return self.get_path(oCurIter)

    def update_entry(self, oFilterItem, oSelectIter):
        """Update the store with the current text"""
        oChild = self.iter_children(oSelectIter)
        if not oChild:
            # No children, so oSelectIter is the one we want
            oChild = oSelectIter
        sText = oFilterItem.aCurValues[0]
        if not sText:
            sText = self.NO_VALUE
        self.set(oChild, 0, sText, 1, None)
        return self.get_path(oChild)

    def get_drop_iter(self, tRowInfo):
        """Get the correct iter from the drop info"""
        iIndex = 0
        if not tRowInfo:
            oIter = self.get_iter_root()
            iIndex = -1
        else:
            oPath, iDropPos = tRowInfo
            oIter = self.get_iter(oPath)
            if self.iter_depth(oIter) > 0 and \
                    iDropPos == gtk.TREE_VIEW_DROP_BEFORE:
                # Find the iter immediately before this one, since
                # that's our actual target
                oParIter = self.iter_parent(oIter)
                oPrevIter = oParIter
                oNextIter = self.iter_children(oParIter)
                while self.get_path(oNextIter) != oPath:
                    oPrevIter = oNextIter
                    oNextIter = self.iter_next(oPrevIter)
                oIter = oPrevIter
        # oIter now points to the right point to insert
        return iIndex, oIter

    def get_drop_filter(self, tRowInfo):
        """Get the filter associated with the given drop point"""
        _iIndex, oIter = self.get_drop_iter(tRowInfo)
        oFilterObj = self.get_value(oIter, 1)
        while oFilterObj is None:
            oIter = self.iter_parent(oIter)
            oFilterObj = self.get_value(oIter, 1)
        return oFilterObj, oIter

    def get_insert_box(self, tRowInfo):
        """Get the filter box model to insert into."""
        iIndex, oIter = self.get_drop_iter(tRowInfo)
        oFilterObj = self.get_value(oIter, 1)
        if not hasattr(oFilterObj, 'sBoxType'):
            # Need to insert into parent box model
            oTempIter = oIter
            oInsertObj = oFilterObj
            while not hasattr(oInsertObj, 'sBoxType'):
                oTempIter = self.iter_parent(oTempIter)
                oInsertObj = self.get_value(oTempIter, 1)
                if oFilterObj is None:
                    # Bounce this up a level as well
                    oFilterObj = oInsertObj
            # We insert after this filter
            iIndex = oInsertObj.index(oFilterObj) + 1
        else:
            oInsertObj = oFilterObj
        return oInsertObj, iIndex


class FilterBoxModelEditView(gtk.TreeView):
    """TreeView for the FilterBoxModelEditor"""
    # pylint: disable-msg=R0904
    # R0904 - gtk.Widget, so many public methods

    def __init__(self, oStore, oValuesWidget, oBoxModel):
        super(FilterBoxModelEditView, self).__init__(oStore)
        self._oStore = oStore
        self._oBoxModel = oBoxModel
        oTextCell = gtk.CellRendererText()
        oColumn = gtk.TreeViewColumn("Filter", oTextCell, markup=0,
                foreground_gdk=2)
        self.append_column(oColumn)

        self.enable_model_drag_dest(DRAG_TARGETS,
                gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
        self.enable_model_drag_source(
                gtk.gdk.BUTTON1_MASK | gtk.gdk.BUTTON3_MASK,
                DRAG_TARGETS, gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        oSelection = self.get_selection()
        oSelection.set_mode(gtk.SELECTION_SINGLE)
        self._oValuesWidget = oValuesWidget
        self.oCurSelectIter = None
        oSelection.connect('changed', self.update_values_widget)

        self.connect('drag_data_received', self.drag_drop_handler)
        self.connect('drag_data_get', self.drag_element)
        self.connect('button_press_event', self.press_button)

    def update_values_widget(self, _oTreeSelection):
        """Update the values widget to the new selection"""
        # Get the current selected row
        _oModel, oIter = self.get_selection().get_selected()
        oFilterObj = None
        if oIter:
            oFilterObj = self._oStore.get_value(oIter, 1)
            while oFilterObj is None:
                oIter = self._oStore.iter_parent(oIter)
                if oIter:
                    oFilterObj = self._oStore.get_value(oIter, 1)
        self.oCurSelectIter = oIter
        if oFilterObj is None:
            self._oValuesWidget.set_widget(None, self)
            return
        elif oFilterObj.bDisabled:
            self._oValuesWidget.set_widget(None, self)
        else:
            self._oValuesWidget.set_widget(oFilterObj, self)
        if self._oStore.iter_depth(self.oCurSelectIter) > 0:
            self._oValuesWidget.enable_disable(oFilterObj)
            self._oValuesWidget.enable_delete()
        else:
            self._oValuesWidget.disable_all_buttons()

    def select_path(self, oPath):
        """Helper function to manage setting the selected path"""
        self.set_cursor(oPath)
        self.grab_focus()
        self.scroll_to_cell(oPath, None, True, 0.5, 0.0)

    def set_box_model(self, oBoxModel):
        """Set the box model to the correct value"""
        self._oBoxModel = oBoxModel
        self.load()

    def load(self, oPath=None):
        """Load the boxmodel into the TreeView"""
        oRootPath = self._oStore.load(self._oBoxModel)
        self.expand_all()
        if oPath:
            self.select_path(oPath)
        else:
            # Select the root of the model by default.
            self.select_path(oRootPath)

    def remove_value_at_iter(self, sIter):
        """Remove the filter value at the given point in the tree"""
        oIter = self._oStore.get_iter_from_string(sIter)
        oFilter = self._oStore.get_value(self._oStore.iter_parent(oIter), 1)
        sValue = self._oStore.get_value(oIter, 0)
        if oFilter.iValueType == FilterBoxItem.LIST \
                and sValue in oFilter.aCurValues:
            oFilter.aCurValues.remove(sValue)
            self.update_list(self.oCurSelectIter, oFilter)
        elif oFilter.iValueType == FilterBoxItem.LIST_FROM:
            if oFilter.aCurValues[0] and \
                    sValue in oFilter.aCurValues[0]:
                oFilter.aCurValues[0].remove(sValue)
            elif oFilter.aCurValues[1] and \
                    sValue in oFilter.aCurValues[1]:
                oFilter.aCurValues[1].remove(sValue)
            self.update_count_list(self.oCurSelectIter, oFilter)

    def remove_filter_at_iter(self, sIter):
        """Remove the filter element at the given point in the tree"""
        oIter = self._oStore.get_iter_from_string(sIter)
        oMoveObj = self._oStore.get_value(oIter, 1)
        oParent  = self._oStore.get_value(self._oStore.iter_parent(oIter), 1)
        oParent.remove(oMoveObj)
        self.load() # May break stuff

    def update_list(self, oIter, oFilterItem):
        """Update the list to show the current values"""
        self._update_iter_with_list(oIter, oFilterItem.aCurValues)

    def update_count_list(self, oIter, oFilterItem):
        """Update the list to show the current values"""
        aValues = []
        if oFilterItem.aCurValues[0]:
            aValues.extend(oFilterItem.aCurValues[0])
        else:
            aValues.append(None)
        aValues.append('<b>From</b>')
        if oFilterItem.aCurValues[1]:
            aValues.extend(oFilterItem.aCurValues[1])
        else:
            aValues.append(None)
        self._update_iter_with_list(oIter, aValues)

    def update_box_text(self, oBoxModel):
        """Update the listing for the given box model"""
        for sDesc, tInfo in BOXTYPE.iteritems():
            sBoxType, bNegate = tInfo
            if oBoxModel.sBoxType == sBoxType and oBoxModel.bNegate == bNegate:
                self._oStore.set(self.oCurSelectIter, 0, sDesc)

    def update_entry(self, oFilterItem):
        """Update the filter with the current text"""
        oChildPath = self._oStore.update_entry(oFilterItem,
                self.oCurSelectIter)
        self.expand_to_path(oChildPath)
        self.expand_row(oChildPath, True)

    def _update_iter_with_list(self, oIter, aValues):
        """Fill in the list values"""
        oPath, _oCol = self.get_cursor()
        oCurPath = self._oStore.update_iter_with_values(aValues,
                oIter, oPath)
        self.expand_to_path(oCurPath)
        self.expand_row(oCurPath, True)

    def _check_for_obj(self, _oModel, oPath, oIter, oFilterObj):
        """Helper function for selecting an object in the tree.
          Meant to be called via the foreach method."""
        oCurObj = self._oStore.get_value(oIter, 1)
        if oCurObj is oFilterObj:
            self.select_path(oPath)

    def _check_for_value(self, _oModel, oPath, oIter, tValueInfo):
        """Helper function for selecting a value in a filter in the tree.
          Meant to be called via the foreach method."""
        oFilterObj, sValue = tValueInfo
        sCurValue = self._oStore.get_value(oIter, 0)
        if sCurValue == sValue:
            # Check parent
            oParIter = self._oStore.iter_parent(oIter)
            oCurFilter = self._oStore.get_value(oParIter, 1)
            if oCurFilter is oFilterObj:
                self.select_path(oPath)

    # pylint: disable-msg=R0913
    # function signature requires all these arguments

    def drag_drop_handler(self, _oWindow, oDragContext, iXPos, iYPos,
            oSelectionData, _oInfo, oTime):
        """Handle drops from the filter toolbar"""
        bDragRes = True
        if not oSelectionData and oSelectionData.format != 8:
            bDragRes = False
        else:
            sData =  oSelectionData.data
            tRowInfo = self.get_dest_row_at_pos(iXPos, iYPos)
            if not sData:
                bDragRes = False
            elif sData.startswith(NEW_FILTER) or \
                    sData.startswith(MOVE_FILTER):
                if not self._do_drop_filter(sData, tRowInfo):
                    bDragRes = False
            elif sData.startswith(MOVE_VALUE):
                if not self._do_move_value(sData, tRowInfo):
                    bDragRes = False
            elif sData.startswith(NEW_VALUE):
                if not self._do_drop_value(sData, tRowInfo):
                    bDragRes = False
            else:
                bDragRes = False
        oDragContext.finish(bDragRes, False, oTime)

    # pylint: enable-msg=R0913

    def _do_drop_value(self, sData, tRowInfo):
        """Handled dropping in new values"""
        def target_ok(oDropFilter, sFilterName):
            """Check that we have a valid target"""
            if not hasattr(oDropFilter, 'sFilterName'):
                # Can't drop values onto a box filter
                return False
            elif oDropFilter.iValueType not in [FilterBoxItem.LIST,
                    FilterBoxItem.LIST_FROM]:
                # Not sensible to drop onto entry or null filters
                return False
            elif sFilterName != oDropFilter.sFilterName:
                # Only drag between the same filter types
                return False
            return True

        # values are created as 'NewValue: FilterName[: Section]'
        # We then call back into oValuesWidget to get the actual
        # values, to avoid awkward escaping issues
        oFilterObj, oDropIter = self._oStore.get_drop_filter(tRowInfo)
        sFilterName = sData.split(':', 2)[1].strip()
        if not target_ok(oFilterObj, sFilterName):
            return False
        aSelection = self._oValuesWidget.get_selected_values()
        if oFilterObj.iValueType == FilterBoxItem.LIST:
            # Get values from the list
            for sValue in aSelection:
                if sValue not in oFilterObj.aCurValues:
                    oFilterObj.aCurValues.append(sValue)
            oFilterObj.aCurValues.sort()
            self.update_list(oDropIter, oFilterObj)
        else:
            # List from filter - we need to distinguish between the
            # different parts
            sSection = sData.split(':', 2)[2].strip()
            for sValue in aSelection:
                if sSection == 'Count':
                    if not oFilterObj.aCurValues[0]:
                        oFilterObj.aCurValues[0] = [sValue]
                    elif sValue not in oFilterObj.aCurValues[0]:
                        oFilterObj.aCurValues[0].append(sValue)
                else:
                    if not oFilterObj.aCurValues[1]:
                        oFilterObj.aCurValues[1] = [sValue]
                    elif sValue not in oFilterObj.aCurValues[1]:
                        oFilterObj.aCurValues[1].append(sValue)
            if sSection == 'Count':
                oFilterObj.aCurValues[0].sort()
            else:
                oFilterObj.aCurValues[1].sort()
            self.update_count_list(oDropIter, oFilterObj)
        return True

    def _do_move_value(self, sData, tRowInfo):
        """Handle moving filter values"""
        def target_ok(oDropFilter, oSourceFilter):
            """Check that we have a valid target"""
            if not hasattr(oDropFilter, 'sFilterName'):
                # Can't drop values onto a box filter
                return False
            elif oDropFilter.iValueType not in [FilterBoxItem.LIST,
                    FilterBoxItem.LIST_FROM]:
                # Not sensible to drop onto entry or null filters
                return False
            elif oSourceFilter.sFilterName != oDropFilter.sFilterName:
                # Only drag between the same filter types
                return False
            elif oSourceFilter is oDropFilter:
                # Don't drag onto ourselves
                return False
            return True

        sIter = sData.split(':', 1)[1].strip()
        # Check if target point is suitable
        oFilterObj, _oDropIter = self._oStore.get_drop_filter(tRowInfo)
        oIter = self._oStore.get_iter_from_string(sIter)
        oSourceFilter = self._oStore.get_value(
                self._oStore.iter_parent(oIter), 1)
        sValue = self._oStore.get_value(oIter, 0)
        if not target_ok(oFilterObj, oSourceFilter):
            return False
        aTarget = []
        if oFilterObj.iValueType == FilterBoxItem.LIST:
            aTarget = oFilterObj.aCurValues
        elif oFilterObj.iValueType == FilterBoxItem.LIST_FROM:
            if oSourceFilter.aCurValues[0] and \
                    sValue in oSourceFilter.aCurValues[0]:
                # Dragging the 1st element
                if not oFilterObj.aCurValues[0]:
                    oFilterObj.aCurValues[0] = []
                aTarget = oFilterObj.aCurValues[0]
            elif oSourceFilter.aCurValues[1] and \
                    sValue in oSourceFilter.aCurValues[1]:
                if not oFilterObj.aCurValues[0]:
                    oFilterObj.aCurValues[1] = []
                aTarget = oFilterObj.aCurValues[1]
        if sValue in aTarget:
            # Don't allow duplicate values
            return False
        aTarget.append(sValue)
        aTarget.sort()
        self.remove_value_at_iter(sIter)
        self.load()
        self._oStore.foreach(self._check_for_value, (oFilterObj, sValue))
        return True

    def _do_drop_filter(self, sData, tRowInfo):
        """Handle the moving/dropping of a filter onto the view"""
        oCurPath, _oCol = self.get_cursor()
        sSource, sFilter = [x.strip() for x in sData.split(':', 1)]
        # Check we have an acceptable drop position
        oInsertObj, iIndex = self._oStore.get_insert_box(tRowInfo)
        if sSource == 'NewFilter':
            tSelInfo = self._oValuesWidget.get_current_pos_and_sel()
            if sFilter == 'Filter Group':
                oInsertObj.add_child_box(oInsertObj.AND)
            else:
                oInsertObj.add_child_item(sFilter)
        else:
            # Find the dragged filter and remove it from it's current
            # position
            oMoveIter = self._oStore.get_iter_from_string(sFilter)
            oMoveObj = self._oStore.get_value(oMoveIter, 1)
            oParent  = self._oStore.get_value(
                    self._oStore.iter_parent(oMoveIter), 1)
            # Check move is legal
            bDoInsert = False
            if oInsertObj is not oMoveObj:
                if not isinstance(oMoveObj, FilterBoxModel) or \
                        not oMoveObj.is_in_model(oInsertObj):
                    bDoInsert = True
            if bDoInsert:
                oParent.remove(oMoveObj)
                oInsertObj.append(oMoveObj)
            else:
                return False
        # Move to the correct place
        if iIndex >= 0:
            oAddedFilter = oInsertObj.pop()
            oInsertObj.insert(iIndex, oAddedFilter)
        self.load()
        if sSource == 'NewFilter':
            # Restore selection after load
            self.select_path(oCurPath)
            # Restore values widget selection
            self._oValuesWidget.restore_pos_and_selection(tSelInfo)
        else:
            # Find where dropped filter ended up and select it
            # Since we can seriously muck around with the tree layout,
            # we can't use any previous iters or paths, so we use
            # foreach
            self._oStore.foreach(self._check_for_obj, oMoveObj)
        return True

    def _get_cur_filter(self):
        """Get the currently selected filter path"""
        oCurPath, _oCol = self.get_cursor()
        if oCurPath:
            return self._oStore.get_value(self.oCurSelectIter, 1), oCurPath
        return None, None

    def toggle_negate(self, _oWidget):
        """Toggle the disabled flag for a section of the filter"""
        oFilterObj, oCurPath = self._get_cur_filter()
        if oFilterObj:
            oFilterObj.bNegated = not oFilterObj.bNegated
            # We opt for the lazy approach and reload
            self.load(oCurPath)

    def set_negate(self, bState):
        """Set the disabled flag for a section of the filter"""
        oFilterObj, oCurPath = self._get_cur_filter()
        if oFilterObj and oFilterObj.bNegated != bState:
            oFilterObj.bNegated = bState
            # We opt for the lazy approach and reload
            self.load(oCurPath)

    def toggle_disabled(self, _oWidget):
        """Toggle the disabled flag for a section of the filter"""
        oFilterObj, oCurPath = self._get_cur_filter()
        if oFilterObj:
            oFilterObj.bDisabled = not oFilterObj.bDisabled
            self.load(oCurPath)

    def set_disabled(self, bState):
        """Set the disabled flag for a section of the filter"""
        oFilterObj, oCurPath = self._get_cur_filter()
        if oFilterObj and oFilterObj.bDisabled != bState:
            oFilterObj.bDisabled = bState
            # We opt for the lazy approach and reload
            self.load(oCurPath)

    def delete(self, _oIgnore):
        """Delete an filter component from the model

           _oIgnore is so this can be called from the popup menu"""
        oFilterObj, _oCurPath = self._get_cur_filter()
        if oFilterObj is not None:
            oParent = self._oStore.get_value(
                    self._oStore.iter_parent(self.oCurSelectIter), 1)
            oParent.remove(oFilterObj)
            self.load()

    def press_button(self, _oWidget, oEvent):
        """Display the popup menu"""
        if oEvent.button == 3:
            iXPos = int(oEvent.x)
            iYPos = int(oEvent.y)
            oTime = oEvent.time
            oPathInfo = self.get_path_at_pos(iXPos, iYPos)
            if oPathInfo is not None:
                oPath, oCol, _iCellX, _iCellY = oPathInfo
                self.grab_focus()
                self.set_cursor(oPath, oCol, False)
                oPopupMenu = BoxModelPopupMenu(self)
                # Show before popup, otherwise menu items aren't drawn properly
                oPopupMenu.show_all()
                oPopupMenu.popup(None, None, None, oEvent.button, oTime)
                return True # Don't propogate to buttons
        return False

    def drag_element(self, _oBtn, _oContext, oSelectionData, _oInfo, _oTime):
        """Create a drag info for this filter"""
        _oModel, oIter = self.get_selection().get_selected()
        if oIter and self._oStore.iter_depth(oIter) > 0:
            # We don't allow the root node to be dragged
            oFilter = self._oStore.get_value(oIter, 1)
            if oFilter is None:
                # Dragging a value
                sSelect = '%s%s' % (MOVE_VALUE,
                        self._oStore.get_string_from_iter(oIter))
            else:
                # Dragging a filter
                sSelect = '%s%s' % (MOVE_FILTER,
                        self._oStore.get_string_from_iter(oIter))
            oSelectionData.set(oSelectionData.target, 8, sSelect)


class FilterBoxModelEditBox(gtk.VBox):
    """Box to hold the BoxModel view."""
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods

    def __init__(self, oValuesWidget):
        super(FilterBoxModelEditBox, self).__init__()
        self._oValuesWidget = oValuesWidget
        oTreeStore = FilterBoxModelStore()
        self.__oTreeView = FilterBoxModelEditView(oTreeStore, oValuesWidget,
                None)
        self.pack_start(self.__oTreeView, expand=True)

    def set_box_model(self, oBoxModel):
        """Set the box model to the correct value"""
        self.__oTreeView.set_box_model(oBoxModel)
