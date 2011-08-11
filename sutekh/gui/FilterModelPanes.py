# FilterModelPanes.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Handle the manipulation bits for the Filter Editor
# Copyright 2010 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Handle the panes for the filter editor"""

from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.gui.ScrolledList import ScrolledList
from sutekh.gui.CustomDragIconView import CustomDragIconView
from sutekh.gui.CardSetsListView import CardSetsListView
from sutekh.core.FilterParser import get_filters_for_type
from sutekh.core.FilterBox import FilterBoxItem, FilterBoxModel, BOXTYPE, \
        BOXTYPE_ORDER
import gobject
import gtk
import pango

DRAG_TARGETS = [('STRING', 0, 0), ('text/plain', 0, 0)]
NO_DRAG_TARGET = [("No Drag", 0, 0)]
# Filters we pad values for to sort nicely
PAD_FILTERS = set(('Capacity', 'CardCount: Count'))
LIST_TYPES = set((FilterBoxItem.LIST, FilterBoxItem.LIST_FROM))

# Drag type constants
NEW_VALUE = 'NewValue: '
MOVE_VALUE = 'MoveValue: '
MOVE_FILTER = 'MoveFilter: '
NEW_FILTER = 'NewFilter: '

# Key constants
ENTER_KEYS = set([gtk.gdk.keyval_from_name('Return'),
    gtk.gdk.keyval_from_name('KP_Enter')])
LEFT_RIGHT = set([gtk.gdk.keyval_from_name('KP_Left'),
    gtk.gdk.keyval_from_name('KP_Right'),
    gtk.gdk.keyval_from_name('Left'),
    gtk.gdk.keyval_from_name('Right')])
LEFT = set([gtk.gdk.keyval_from_name('KP_Left'),
    gtk.gdk.keyval_from_name('Left')])
RIGHT = set([gtk.gdk.keyval_from_name('KP_Right'),
    gtk.gdk.keyval_from_name('Right')])


def unescape_markup(sMarkup):
    """Untiltiy function to strip markup from a string"""
    _oAttr, sStripped, _oAccel = pango.parse_markup(sMarkup)
    return sStripped


def add_accel_to_button(oButton, sAccelKey, oAccelGroup, sToolTip=None):
    """Creates a button using an gtk.AccelLabel to display the accelerator"""
    (iKeyVal, iMod) = gtk.accelerator_parse(sAccelKey)
    if iKeyVal != 0:
        oButton.add_accelerator('clicked', oAccelGroup, iKeyVal, iMod,
                gtk.ACCEL_VISIBLE)
    if sToolTip:
        oButton.set_tooltip_markup(sToolTip)


class FilterModelPanes(gtk.HBox):
    """Widget to hold the different panes of the Filter editor"""
    # pylint: disable-msg=R0904
    # R0904 - gtk.Widget, so many public methods

    def __init__(self, sFilterType, oDialog):
        super(FilterModelPanes, self).__init__()
        # Create the 3 panes
        self._oBoxModel = None
        self._sFilterType = sFilterType
        self._oSelectBar = FilterValuesBox(oDialog, sFilterType)
        self._oEditBox = FilterBoxModelEditBox(self._oSelectBar)

        self.pack_start(AutoScrolledWindow(self._oEditBox, True), expand=True)
        self.pack_start(self._oSelectBar, expand=True)

    def replace_ast(self, oAST):
        """Replace the AST in the tree model"""
        self._oBoxModel = FilterBoxModel(oAST, self._sFilterType)
        self._oEditBox.set_box_model(self._oBoxModel)

    def get_ast_with_values(self):
        """Get the current ast for the Editor, with values filled in"""
        if not self._oBoxModel:
            return None

        return self._oBoxModel.get_ast_with_values()

    def get_text(self):
        """Get the current ast"""
        if self._oBoxModel:
            return self._oBoxModel.get_text()
        return None


class FilterEditorToolbar(CustomDragIconView):
    """Toolbar listing the possible filter elements"""
    # pylint: disable-msg=R0904
    # R0904 - gtk.Widget, so many public methods

    def __init__(self, sFilterType):
        self._oListStore = gtk.ListStore(gobject.TYPE_STRING,
                gobject.TYPE_STRING)
        super(FilterEditorToolbar, self).__init__(self._oListStore)
        oTextCell = gtk.CellRendererText()
        oColumn = gtk.TreeViewColumn("Filter Element", oTextCell, text=0)
        oColumn.set_spacing(2)
        self.append_column(oColumn)
        self._sFilterType = sFilterType
        # Get supported filters
        aFilters = [('Filter Group ..', 'Filter Group')]
        for oFilterType in sorted(get_filters_for_type(self._sFilterType),
                key=lambda x: x.description):
            aFilters.append((oFilterType.description, oFilterType.keyword))
        self.drag_source_set(
                gtk.gdk.BUTTON1_MASK | gtk.gdk.BUTTON3_MASK,
                DRAG_TARGETS, gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
        # Create entries for each of the filters we support
        for tInfo in aFilters:
            self._oListStore.append(tInfo)

        self.connect('drag_data_get', self.drag_filter)
        self.get_selection().set_mode(gtk.SELECTION_SINGLE)

    def drag_filter(self, _oBtn, _oContext, oSelectionData, _oInfo, _oTime):
        """Create a drag info for this filter"""
        sSelect = self.get_paste_filter()
        if sSelect:
            oSelectionData.set(oSelectionData.target, 8, sSelect)

    def get_paste_filter(self):
        """Get the currently selected filter"""
        _oModel, oIter = self.get_selection().get_selected()
        if oIter:
            sSelect = '%s%s' % (NEW_FILTER,
                    self._oListStore.get_value(oIter, 1))
            return sSelect
        return None


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
        self._sFilterType = sFilterType
        self._oEmptyWidget.pack_start(gtk.Label(
            'Select an active\nfilter element'), expand=False)
        self._oNoneWidget.pack_start(gtk.Label(
            'No values for this filter'), expand=False)
        # Handle removing none file elements
        self._set_drop_for_widget(self._oNoneWidget)
        self._oFilter = None
        self._oBoxModelEditor = None
        self._aLastSelection = []
        self._oLastFilter = None
        oCheckBox = gtk.HBox()

        self._oDisable = gtk.CheckButton('Disable (Ctrl-space)')
        self._oNegate = gtk.CheckButton('Negate (Alt-space)')
        self._oDelete = gtk.Button('Delete Filter or Value (del)')

        add_accel_to_button(self._oDisable, "<Ctl>space", oDialog.accel_group)
        add_accel_to_button(self._oNegate, "<Alt>space", oDialog.accel_group)
        add_accel_to_button(self._oDelete, "Delete", oDialog.accel_group)

        self._oDisable.set_sensitive(False)
        self._oDelete.set_sensitive(False)
        self._oNegate.set_sensitive(False)

        oCheckBox.pack_start(self._oDisable, expand=True)
        oCheckBox.pack_start(self._oNegate, expand=True)
        self.pack_start(oCheckBox, expand=False)
        self.pack_start(self._oDelete, expand=False)
        self._oDisable.connect('toggled', self.toggle_disabled)
        self._oDelete.connect('clicked', self.delete)
        self._oNegate.connect('toggled', self.toggle_negate)

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
        oFilterTypes.view.connect('key-press-event', self.key_press, oFilter,
                'Filter Type')
        self._oWidget.pack_start(oFilterTypes, expand=False)
        self._oWidget.pack_start(gtk.Label('Or Drag Filter Element'),
                expand=False)
        oSubFilterList = FilterEditorToolbar(self._sFilterType)
        oSubFilterList.connect('key-press-event', self.key_press, oFilter,
                'Filter')
        self._oWidget.pack_start(AutoScrolledWindow(oSubFilterList),
                    expand=True)

    def _make_list_from(self, oFilter):
        """Create the widget for the 'X form Y' filters"""
        self._oWidget = gtk.VBox()
        oCountList = ScrolledList('Select Counts', bSpecialSelect=True)
        oCountList.set_select_multiple()
        oCountList.fill_list(oFilter.aValues[0])
        oCountList.connect('key-press-event', self.key_press, oFilter, 'Count')
        oSetList = CardSetsListView(None, self._oParent, bSpecialSelect=True)
        oSetList.set_select_multiple()
        oSetList.connect('key-press-event', self.key_press, oFilter, 'Set')
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
        oSetList = CardSetsListView(None, self._oParent, bSpecialSelect=True)
        oSetList.set_select_multiple()
        self._oWidget = AutoScrolledWindow(oSetList, False)
        oSetList.connect('key-press-event', self.key_press, oFilter, 'CardSet')
        self._set_drag_for_widget(oSetList, self.update_set_list, oFilter)
        self._set_drop_for_widget(oSetList)

    def _make_filter_values_list(self, oFilter):
        """Create a filter values list widget"""
        self._oWidget = ScrolledList('Select Filter Values',
                bSpecialSelect=True)
        self._oWidget.set_select_multiple()
        self._oWidget.fill_list(oFilter.aValues)
        self._oWidget.view.connect('key-press-event', self.key_press, oFilter,
                'Value')
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
        oEntry.connect('key-press-event', self.key_press, oFilter, 'Entry')

    def set_widget(self, oFilter, oBoxModelEditor):
        """Replace the current widget with the correct widget for the
           new filter"""
        self._oBoxModelEditor = oBoxModelEditor
        self._aLastSelection = []
        if self._oWidget:
            if self._oLastFilter == oFilter:
                return  # We're still the same filter, so do nothing
            self.remove(self._oWidget)
            self._oWidget = None
        if isinstance(oFilter, FilterBoxModel):
            # Select between box options
            self._oDisable.set_active(oFilter.bDisabled)
            self._oNegate.set_inconsistent(True)
            self._oNegate.set_sensitive(False)
            self._make_filter_group_list(oFilter)
        elif isinstance(oFilter, FilterBoxItem):
            self._oDisable.set_active(oFilter.bDisabled)
            self._oNegate.set_inconsistent(False)
            self._oNegate.set_active(oFilter.bNegated)
            self._oNegate.set_sensitive(True)
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
                self._oWidget.connect('key-press-event', self.key_press, None,
                        'None')
        else:
            # No selected widget, so clear everything
            self._oWidget = self._oEmptyWidget
            self.disable_all_buttons()
        self.pack_start(self._oWidget, expand=True)
        self._oLastFilter = oFilter
        self.show_all()

    # pylint: disable-msg=R0201
    # Methods for consistency
    def set_box_model_value(self, oBoxModel, oWidget):
        """Set the correct selection for this box model"""
        for sDesc, tInfo in BOXTYPE.iteritems():
            sBoxType, bNegate = tInfo
            if oBoxModel.sBoxType == sBoxType and oBoxModel.bNegate == bNegate:
                oWidget.set_selected_entry(sDesc)

    # pylint: enable-msg=R0201

    def update_box_model(self, _oSelection, oBoxModel, oList):
        """Update the box model to the current selection"""
        aSelected = oList.get_selection()
        if not aSelected:
            return  # We don't do anything special if nothing's selected
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
            sData = oSelectionData.data
            if not sData:
                bDragRes = False
            elif sData.startswith(MOVE_VALUE):
                # Removing a value from the list
                sIter = sData.split(':', 1)[1].strip()
                oIter = self._oBoxModelEditor.get_iter_from_string(sIter)
                self._oBoxModelEditor.remove_value_at_iter(oIter)
            elif sData.startswith(MOVE_FILTER):
                # Removing a filter
                sIter = sData.split(':', 1)[1].strip()
                oIter = self._oBoxModelEditor.get_iter_from_string(sIter)
                self._oBoxModelEditor.remove_filter_at_iter(oIter)
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

    def switch_focus(self, oEvent, sSource):
        """Handle switching focus between the different filter bits"""
        if sSource in set(['Value', 'Entry', 'None', 'CardSet']):
            # Only one entry in the filter pane
            self._oBoxModelEditor.grab_focus()
        elif sSource == 'Editor':
            if isinstance(self._oLastFilter, FilterBoxItem):
                if self._oLastFilter.iValueType == FilterBoxItem.LIST:
                    # Only one entry in the filter pane
                    self._oWidget.view.grab_focus()
                elif self._oLastFilter.iValueType == FilterBoxItem.ENTRY:
                    # entry is the second child of the VBox
                    self._oWidget.get_children()[1].grab_focus()
            if isinstance(self._oLastFilter, FilterBoxModel) or \
                    (isinstance(self._oLastFilter, FilterBoxItem) and
                            self._oLastFilter.iValueType ==
                            FilterBoxItem.LIST_FROM):
                if oEvent.keyval in LEFT:
                    # bottom child needs the focus
                    oAutoScrolled = self._oWidget.get_children()[2]
                    oAutoScrolled.get_child().grab_focus()
                else:
                    # top child needs the focus
                    self._oWidget.get_children()[0].view.grab_focus()
        elif sSource in set(['Count', 'Set', 'Filter Type', 'Filter']):
            if oEvent.keyval in RIGHT and \
                    sSource in set(['Count', 'Filter Type']):
                # Top child selected, so pass to bottom
                oAutoScrolled = self._oWidget.get_children()[2]
                oAutoScrolled.get_child().grab_focus()
            elif oEvent.keyval in LEFT and \
                    sSource in set(['Filter', 'Set']):
                # Bottom child selected, so pass to top
                self._oWidget.get_children()[0].view.grab_focus()
            else:
                # Passing focus to Model Editor
                self._oBoxModelEditor.grab_focus()

    def key_press(self, oWidget, oEvent, oFilter, sSource):
        """Handle key press events to do allow keyboard pasting"""
        # Alt-direction moves focus around
        if oEvent.keyval in LEFT_RIGHT and \
                (oEvent.get_state() & gtk.gdk.MOD1_MASK):
            self.switch_focus(oEvent, sSource)
        # We flag on ctrl-enter
        if oEvent.keyval not in ENTER_KEYS or not \
                (oEvent.get_state() & gtk.gdk.CONTROL_MASK):
            return
        if sSource == 'Filter':
            # Paste current filter into the current filter box
            sSelect = oWidget.get_paste_filter()
            if sSelect:
                self._oBoxModelEditor.paste_filter(oFilter, sSelect, -1)
        elif sSource == 'Count':
            sSelect = '%s%s: Count' % (NEW_VALUE, oFilter.sFilterName)
            self._format_selection(sSelect, oWidget.get_selection())
            self._oBoxModelEditor.paste_value(sSelect)
        elif sSource == 'Set':
            sSelect = '%s%s: Set' % (NEW_VALUE, oFilter.sFilterName)
            self._format_selection(sSelect, oWidget.get_all_selected_sets())
            self._oBoxModelEditor.paste_value(sSelect)
        elif sSource == 'CardSet':
            sSelect = '%s%s' % (NEW_VALUE, oFilter.sFilterName)
            self._format_selection(sSelect, oWidget.get_all_selected_sets())
            self._oBoxModelEditor.paste_value(sSelect)
        elif sSource == 'Value':
            sSelect = '%s%s' % (NEW_VALUE, oFilter.sFilterName)
            self._format_selection(sSelect, self._oWidget.get_selection())
            self._oBoxModelEditor.paste_value(sSelect)

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
        self._oDisable.set_sensitive(False)
        self._oDelete.set_sensitive(False)
        self._oNegate.set_sensitive(False)

    def enable_delete(self):
        """Enable the delete button"""
        self._oDelete.set_sensitive(True)

    def enable_disable(self, oFilterObj):
        """Enable the delete button"""
        self._oDisable.set_sensitive(True)
        self._oDisable.set_active(oFilterObj.bDisabled)

    def get_current_pos_and_sel(self):
        """Get the current scroll position and selection path in the
           sub-filter list to restore later"""

        def _get_values(oAdj):
            """Get important values out of a gtk.Adjustment"""
            return oAdj.value, oAdj.page_size

        # We must always be calling this with a filter box model shown
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

        # FIXME: fix selection behaviour so we select the correct
        # filter box model in this case, rather than the newly added
        # filter.
        if len(self._oWidget.get_children()) != 3:
            # Selected widget is not a box model (can happen if we insert
            # something before the box model, so no sensible default selection
            return
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
        self._oDel = gtk.MenuItem("Delete filter or value")

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

    BLACK = gtk.gdk.color_parse('black')
    GREY = gtk.gdk.color_parse('grey')
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
                    self.append(oFilterIter,
                            (gobject.markup_escape_text(sValue), None,
                                oColour))
            else:
                self.append(oFilterIter, (self.NO_VALUE, None, oColour))
            self.append(oFilterIter, ('<b>From</b>', None, oColour))
            if aFrom:
                for sValue in aFrom:
                    self.append(oFilterIter,
                            (gobject.markup_escape_text(sValue), None,
                                oColour))
            else:
                self.append(oFilterIter, (self.NO_VALUE, None, oColour))
        elif oModel.aCurValues and oModel.aValues:
            for sValue in oModel.aCurValues:
                self.append(oFilterIter,
                        (gobject.markup_escape_text(sValue), None, oColour))
        elif oModel.aCurValues:
            self.append(oFilterIter,
                    (gobject.markup_escape_text(oModel.aCurValues[0]), None,
                        oColour))
        elif oModel.iValueType == oModel.NONE:
            self.append(oFilterIter, (self.NONE_VALUE, None, oColour))
        else:
            self.append(oFilterIter, (self.NO_VALUE, None, oColour))

    def fix_filter_name(self, oIter, oModel):
        """Fix the name for the given filter to reflect it negated state"""
        if oModel.bNegated:
            sText = 'NOT %s' % oModel.sFilterDesc
        else:
            sText = oModel.sFilterDesc
        self.set(oIter, 0, sText)

    def _do_add_iter(self, oIter, oModel, bDisabled):
        """Recursively add elements of the box model"""
        oThisIter = self.append(oIter)
        oColour = self.BLACK
        if hasattr(oModel, 'sFilterDesc'):
            if oModel.bDisabled or bDisabled:
                oColour = self.GREY
            self.set(oThisIter, 1, oModel, 2, oColour)
            self.fix_filter_name(oThisIter, oModel)
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

    def _clear_iter(self, oSelectIter, oPath):
        """Clear the current iter, saving curently selected element"""
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
        return iIndex, oCurIter

    def _add_list_iter(self, iPos, iIndex, oSelectIter, oCurIter):
        """Set the iter correctly for the list update"""
        if iPos == iIndex:
            oChild = oCurIter
        elif iPos < iIndex:
            oChild = self.insert_before(oSelectIter, oCurIter)
        else:
            oChild = self.append(oSelectIter)
        return oChild

    def update_iter_with_values(self, aValues, oSelectIter, oPath):
        """Update the given iter with the changed values"""
        iIndex, oCurIter = self._clear_iter(oSelectIter, oPath)
        if aValues:
            iIndex = min(len(aValues) - 1, iIndex)
            iPos = 0
            for sValue in aValues:
                oChild = self._add_list_iter(iPos, iIndex, oSelectIter,
                        oCurIter)
                if sValue is not None:
                    self.set(oChild, 0, gobject.markup_escape_text(sValue),
                            1, None, 2, self.BLACK)
                else:
                    self.set(oChild, 0, self.NO_VALUE, 1, None, 2, self.BLACK)
                iPos += 1
        else:
            self.set(oCurIter, 0, self.NO_VALUE, 1, None, 2, self.BLACK)
        return self.get_path(oCurIter)

    def update_iter_with_from_list(self, aCounts, aNames, oSelectIter, oPath):
        """Update the given iter with the changed values"""
        iIndex, oCurIter = self._clear_iter(oSelectIter, oPath)
        iIndex = min(len(aCounts) + len(aNames), iIndex)
        iPos = 0
        for sValue in aCounts:
            oChild = self._add_list_iter(iPos, iIndex, oSelectIter, oCurIter)
            if sValue is not None:
                self.set(oChild, 0, gobject.markup_escape_text(sValue),
                        1, None, 2, self.BLACK)
            else:
                self.set(oChild, 0, self.NO_VALUE, 1, None, 2, self.BLACK)
            iPos += 1
        oChild = self._add_list_iter(iPos, iIndex, oSelectIter, oCurIter)
        iPos += 1
        self.set(oChild, 0, '<b>From</b>', 1, None, 2, self.BLACK)
        for sValue in aNames:
            oChild = self._add_list_iter(iPos, iIndex, oSelectIter, oCurIter)
            if sValue is not None:
                self.set(oChild, 0, gobject.markup_escape_text(sValue),
                        1, None, 2, self.BLACK)
            else:
                self.set(oChild, 0, self.NO_VALUE, 1, None, 2, self.BLACK)
            iPos += 1
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
        else:
            sText = gobject.markup_escape_text(sText)
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


class FilterBoxModelEditView(CustomDragIconView):
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

        self.drag_dest_set(gtk.DEST_DEFAULT_ALL, DRAG_TARGETS,
                gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
        self.drag_source_set(
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
        self.connect('key_press_event', self.key_press)

    def key_press(self, _oWidget, oEvent):
        """Handle key-press events for the filter box model"""
        if oEvent.keyval in LEFT_RIGHT and \
                (oEvent.get_state() & gtk.gdk.MOD1_MASK):
            # Pass focus to the value widget
            self._oValuesWidget.switch_focus(oEvent, 'Editor')

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

    def get_iter_from_string(self, sIter):
        """Lookup the iter given the string. Used used dragging stuff out
           of the pane."""
        return self._oStore.get_iter_from_string(sIter)

    def remove_value_at_iter(self, oIter):
        """Remove the filter value at the given point in the tree"""
        oFilter = self._oStore.get_value(self._oStore.iter_parent(oIter), 1)
        sValue = unescape_markup(self._oStore.get_value(oIter, 0))
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

    def remove_filter_at_iter(self, oIter):
        """Remove the filter element at the given point in the tree"""
        oMoveObj = self._oStore.get_value(oIter, 1)
        oParent = self._oStore.get_value(self._oStore.iter_parent(oIter), 1)
        oParent.remove(oMoveObj)
        self.load()  # May break stuff

    def update_list(self, oIter, oFilterItem):
        """Update the list to show the current values"""
        self._update_iter_with_list(oIter, oFilterItem.aCurValues)

    def update_count_list(self, oIter, oFilterItem):
        """Update the list to show the current values"""
        aCounts = []
        aNames = []
        if oFilterItem.aCurValues[0]:
            aCounts.extend(oFilterItem.aCurValues[0])
        else:
            aCounts.append(None)
        if oFilterItem.aCurValues[1]:
            aNames.extend(oFilterItem.aCurValues[1])
        else:
            aNames.append(None)
        self._update_iter_with_from_list(oIter, aCounts, aNames)

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

    def _update_iter_with_from_list(self, oIter, aCounts, aNames):
        """Fill in with a from list"""
        oPath, _oCol = self.get_cursor()
        oCurPath = self._oStore.update_iter_with_from_list(aCounts,
                aNames, oIter, oPath)
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
        sCurValue = unescape_markup(self._oStore.get_value(oIter, 0))
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
            sData = oSelectionData.data
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

    def paste_value(self, sData):
        """Paste data from the widgets"""
        if sData.startswith(NEW_VALUE):
            oFilterObj, _oPath = self._get_cur_filter()
            self._update_values(oFilterObj, self.oCurSelectIter, sData)

    def _check_drag_value(self, oIter, oFilter, tCurTarget, oAction,
            oDragContext):
        """Check if the current target is an acceptable drop location
           for a filter value"""
        if not tCurTarget:
            oDragContext.drag_status(0)
            return False
        if oFilter is None:
            oFilter = self._oStore.get_value(
                    self._oStore.iter_parent(oIter), 1)
        # Check that destination is valid for this value
        oDropObj, _oIter = self._oStore.get_drop_filter(tCurTarget)
        if hasattr(oDropObj, 'sFilterName') and \
               oDropObj.sFilterName == oFilter.sFilterName:
            oDragContext.drag_status(oAction)
            return True
        else:
            oDragContext.drag_status(0)
            return False

    def _fix_highlight(self, tCurTarget):
        """Fix the highlighted row to match the actual drop target for
           filters"""
        _iIndex, oIter = self._oStore.get_drop_iter(tCurTarget)
        oDropObj = self._oStore.get_value(oIter, 1)
        if oDropObj is None:
            # Target is a filter value, so set highlight to the
            # parent filter
            oDropPath = self._oStore.get_path(self._oStore.iter_parent(oIter))
            self.set_drag_dest_row(oDropPath, gtk.TREE_VIEW_DROP_AFTER)

    def drag_motion(self, _oWidget, oDragContext, iXPos, iYPos, _oTime):
        """Ensure we have correct row highlighted for the drag"""
        # We lift the idea of changing the drag target from
        # Walter Anger's post to the pygtk mailling list
        # http://www.daa.com.au/pipermail/pygtk/2003-November/006431.html
        oCurPath, _oCol = self.get_cursor()
        oIter = self._oStore.get_iter(oCurPath)
        oFilter = self._oStore.get_value(oIter, 1)
        tCurTarget = self.get_dest_row_at_pos(iXPos, iYPos)
        # Flags to fix row highlghting - we use this method rather then gtk's
        # internal code to workaround
        # https://bugzilla.gnome.org/show_bug.cgi?id=641924 on Windows
        # The logic is: Always set the highlighted row if we're dragging a
        # filter element, but only highlight rows if we can drop there
        # when dragging values
        bSetRow = False
        bFixHighlight = False
        if oDragContext.get_source_widget() is self:
            # We're dragging within the view
            if oFilter is None:
                # Dragging a value
                if self._check_drag_value(oIter, oFilter, tCurTarget,
                        gtk.gdk.ACTION_MOVE, oDragContext):
                    self._fix_highlight(tCurTarget)
                    bSetRow = True
                    bFixHighlight = True
            else:
                # dragging a filter around
                oDragContext.drag_status(gtk.gdk.ACTION_MOVE)
                bSetRow = True
        else:
            # Dragging from outside the view, so different rules
            if oFilter is None or not hasattr(oFilter, 'sBoxType'):
                # Dragging values into the filter (since filter is selected)
                if self._check_drag_value(oIter, oFilter, tCurTarget,
                        gtk.gdk.ACTION_COPY, oDragContext):
                    bSetRow = True
                    bFixHighlight = True
            else:
                # Dragging in a filter element
                oDragContext.drag_status(gtk.gdk.ACTION_COPY)
                bSetRow = True
        if bSetRow:
            if tCurTarget:
                self.set_drag_dest_row(tCurTarget[0], tCurTarget[1])
            else:
                # Set highlight on the root of the tree
                oIter = self._oStore.get_iter_root()
                oDropPath = self._oStore.get_path(oIter)
                self.set_drag_dest_row(oDropPath, gtk.TREE_VIEW_DROP_AFTER)
            if bFixHighlight:
                self._fix_highlight(tCurTarget)
        # Ensure we don't propogate this signal further
        return True

    # pylint: enable-msg=R0913

    def _do_drop_value(self, sData, tRowInfo):
        """Handled dropping in new values"""
        def target_ok(oDropFilter, sFilterName):
            """Check that we have a valid target"""
            if not hasattr(oDropFilter, 'sFilterName'):
                # Can't drop values onto a box filter
                return False
            elif oDropFilter.iValueType not in LIST_TYPES:
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
        self._update_values(oFilterObj, oDropIter, sData)

    def _update_values(self, oFilterObj, oIter, sData):
        """Update the values with the given info from the filter"""
        aSelection = self._oValuesWidget.get_selected_values()
        if oFilterObj.iValueType == FilterBoxItem.LIST:
            # Get values from the list
            for sValue in aSelection:
                if sValue not in oFilterObj.aCurValues:
                    oFilterObj.aCurValues.append(sValue)
            oFilterObj.aCurValues.sort()
            self.update_list(oIter, oFilterObj)
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
            self.update_count_list(oIter, oFilterObj)
        return True

    def _do_move_value(self, sData, tRowInfo):
        """Handle moving filter values"""
        def target_ok(oDropFilter, oSourceFilter):
            """Check that we have a valid target"""
            if not hasattr(oDropFilter, 'sFilterName'):
                # Can't drop values onto a box filter
                return False
            elif oDropFilter.iValueType not in LIST_TYPES:
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
        sValue = unescape_markup(self._oStore.get_value(oIter, 0))
        if not target_ok(oFilterObj, oSourceFilter):
            return False
        aTarget = []
        if oFilterObj.iValueType == FilterBoxItem.LIST:
            aTarget = oFilterObj.aCurValues
        elif oFilterObj.iValueType == FilterBoxItem.LIST_FROM:
            for iIndex in (0, 1):
                # We do this loop because we may need to explicitly set
                # the destination filter to an empty list
                if oSourceFilter.aCurValues[iIndex] and \
                        sValue in oSourceFilter.aCurValues[iIndex]:
                    if not oFilterObj.aCurValues[iIndex]:
                        oFilterObj.aCurValues[iIndex] = []
                    aTarget = oFilterObj.aCurValues[iIndex]
                    break
        if sValue in aTarget:
            # Don't allow duplicate values
            return False
        aTarget.append(sValue)
        aTarget.sort()
        self.remove_value_at_iter(oIter)
        self.load()
        self._oStore.foreach(self._check_for_value, (oFilterObj, sValue))
        return True

    def paste_filter(self, oInsertObj, sData, iIndex):
        """Add a filter to the given filter object"""
        oCurPath, _oCol = self.get_cursor()
        sFilter = [x.strip() for x in sData.split(':', 1)][1]
        tSelInfo = self._oValuesWidget.get_current_pos_and_sel()
        if sFilter == 'Filter Group':
            oInsertObj.add_child_box(oInsertObj.AND)
        else:
            oInsertObj.add_child_item(sFilter)
        # Move to the correct place
        if iIndex >= 0:
            oFilterObj = oInsertObj.pop()
            oInsertObj.insert(iIndex, oFilterObj)
        self.load()
        # Restore selection after load
        self.select_path(oCurPath)
        # Restore values widget selection
        self._oValuesWidget.restore_pos_and_selection(tSelInfo)

    def _do_drop_filter(self, sData, tRowInfo):
        """Handle the moving/dropping of a filter onto the view"""
        # Check we have an acceptable drop position
        oInsertObj, iIndex = self._oStore.get_insert_box(tRowInfo)
        if sData.startswith('NewFilter'):
            self.paste_filter(oInsertObj, sData, iIndex)
        else:
            sIter = [x.strip() for x in sData.split(':', 1)][1]
            # Find the dragged filter and remove it from it's current
            # position
            oSourceIter = self._oStore.get_iter_from_string(sIter)
            oFilterObj = self._oStore.get_value(oSourceIter, 1)
            oParent = self._oStore.get_value(
                    self._oStore.iter_parent(oSourceIter), 1)
            # Check move is legal
            bDoInsert = False
            if oInsertObj is not oFilterObj:
                if not isinstance(oFilterObj, FilterBoxModel) or \
                        not oFilterObj.is_in_model(oInsertObj):
                    bDoInsert = True
            if bDoInsert:
                oParent.remove(oFilterObj)
                oInsertObj.append(oFilterObj)
            else:
                return False
            # Move to the correct place
            if iIndex >= 0:
                oFilterObj = oInsertObj.pop()
                oInsertObj.insert(iIndex, oFilterObj)
            self.load()
            self._oStore.foreach(self._check_for_obj, oFilterObj)
        return True

    def _get_cur_filter(self):
        """Get the currently selected filter path"""
        oCurPath, _oCol = self.get_cursor()
        if oCurPath:
            return self._oStore.get_value(self.oCurSelectIter, 1), oCurPath
        return None, None

    def toggle_negate(self, _oWidget):
        """Toggle the disabled flag for a section of the filter"""
        oFilterObj, _oCurPath = self._get_cur_filter()
        if oFilterObj:
            # This is a a bit inefficient, but allows us to handle updating
            # the value in only one place
            self.set_negate(not oFilterObj.bNegated)

    def set_negate(self, bState):
        """Set the disabled flag for a section of the filter"""
        oFilterObj, _oCurPath = self._get_cur_filter()
        if oFilterObj and oFilterObj.bNegated != bState:
            oFilterObj.bNegated = bState
            self._oStore.fix_filter_name(self.oCurSelectIter, oFilterObj)

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
        oFilterObj, oCurPath = self._get_cur_filter()
        oCurIter = self._oStore.get_iter(oCurPath)
        oCurValue = self._oStore.get_value(oCurIter, 1)
        if oCurValue is oFilterObj:
            # At the filter level
            self.remove_filter_at_iter(self.oCurSelectIter)
        elif oFilterObj.iValueType == FilterBoxItem.NONE:
            # None filter, so delete always removes
            self.remove_filter_at_iter(self.oCurSelectIter)
        elif (oFilterObj.iValueType == FilterBoxItem.LIST or
                oFilterObj.iValueType == FilterBoxItem.ENTRY) \
                        and not oFilterObj.aCurValues:
            # Emptu filter
            self.remove_filter_at_iter(self.oCurSelectIter)
        elif oFilterObj.iValueType == FilterBoxItem.LIST_FROM and \
                not oFilterObj.aCurValues[0] and not oFilterObj.aCurValues[1]:
            # empty list from filter, so remove
            self.remove_filter_at_iter(self.oCurSelectIter)
        else:
            # Deleting a value
            self.remove_value_at_iter(oCurIter)

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
                return True  # Don't propogate to buttons
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
        self._oTreeView = FilterBoxModelEditView(oTreeStore, oValuesWidget,
                None)
        self.pack_start(self._oTreeView, expand=True)

    def set_box_model(self, oBoxModel):
        """Set the box model to the correct value"""
        self._oTreeView.set_box_model(oBoxModel)
