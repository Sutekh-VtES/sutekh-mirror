# FilterEditor.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Editor component for generic filter ASTs.
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# Copyright 2010 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Widget for editing filters."""

from sutekh.gui.SutekhDialog import SutekhDialog
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.gui.CardSetsListView import CardSetsListView
from sutekh.gui.ScrolledList import ScrolledList
from sutekh.core.FilterParser import get_filters_for_type
from sutekh.core.FilterBox import FilterBoxItem, FilterBoxModel
import gtk
import pango
import gobject

DRAG_TARGETS = [ ('STRING', 0, 0), ('text/plain', 0, 0) ]

class FilterEditor(gtk.Alignment):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """GTK component for editing Sutekh filter ASTs.

       Provides a graphical representation of the filter as nested boxes,
       which the user can extend or remove from.
       """
    def __init__(self, oAST, sFilterType, oParser, oFilterDialog):
        # Child widget absorbs all free space
        super(FilterEditor, self).__init__(xscale=1.0, yscale=1.0)
        self.__oParser = oParser
        self.__oFilterDialog = oFilterDialog # Dialog we're a child of

        self.__oPanes = FilterModelPanes(sFilterType, oFilterDialog)

        self.__sFilterType = sFilterType

        oNameLabel = gtk.Label("Filter name:")
        self.__oNameEntry = gtk.Entry()
        self.__oNameEntry.set_width_chars(30)

        oHelpButton = gtk.Button("Help")
        oHelpButton.connect("clicked", self.__show_help_dialog)

        oHBox = gtk.HBox(spacing=5)
        oHBox.pack_start(oNameLabel, expand=False)
        oHBox.pack_start(self.__oNameEntry, expand=False)
        oHBox.pack_end(oHelpButton, expand=False)

        self.__oVBox = gtk.VBox(spacing=5)
        self.__oVBox.pack_end(oHBox, expand=False)
        self.__oVBox.pack_end(gtk.HSeparator(), expand=False)
        self.__oVBox.pack_start(self.__oPanes, expand=True)

        self.add(self.__oVBox)

        self.replace_ast(oAST)

    def get_filter(self):
        """Get the actual filter for the current AST."""
        oAST = self.get_current_ast()
        if oAST is None:
            return None
        else:
            return oAST.get_filter()

    def get_current_ast(self):
        """Get the current AST represented by the editor."""
        return self.__oPanes.get_ast_with_values()

    def get_current_text(self):
        """Get the current text of the filter for saving in the config
           file.

           We include any current set values for the filter when saving."""
        return self.__oPanes.get_text()

    def replace_ast(self, oAST):
        """Replace the current AST with a new one and update the GUI,
           preserving variable values if possible.

           Also used to setup the filter initially.
           """
        self.__oPanes.replace_ast(oAST)

    def set_name(self, sName):
        """Set the filter name."""
        self.__oNameEntry.set_text(sName)

    def get_name(self):
        """Get the filter name."""
        return self.__oNameEntry.get_text().strip()

    def connect_name_changed(self, fCallback):
        """Connect a callback to the name entry change signal."""
        self.__oNameEntry.connect('changed', fCallback)

    def __show_help_dialog(self, _oHelpButton):
        """Show a dialog window with the helptext from the filters."""
        oDlg = SutekhDialog("Help on Filters", self.__oFilterDialog,
                gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))

        oDlg.set_default_size(600, 500)
        # pylint: disable-msg=E1101
        # vbox confuse pylint

        # Ensure we sort this in the same order as the toolbar
        oHelpView = AutoScrolledWindow(FilterHelpTextView(
            sorted(get_filters_for_type(self.__sFilterType),
                key=lambda x: x.description)))
        oDlg.vbox.pack_start(oHelpView)
        oDlg.show_all()

        try:
            oDlg.run()
        finally:
            oDlg.destroy()


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
        self.__oEditor = FilterBoxModelEditor(self.__oSelectBar)

        self.pack_start(AutoScrolledWindow(self.__oEditor, True), expand=True)
        self.pack_start(self.__oSelectBar, expand=True)

    def replace_ast(self, oAST):
        """Replace the AST in the tree model"""
        self.__oBoxModel = FilterBoxModel(oAST, self.__sFilterType)
        self.__oEditor.set_box_model(self.__oBoxModel)
        self.__oEditor.load()

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
        # Create buttons for each of the filters we support
        self.drag_source_set(gtk.gdk.BUTTON1_MASK | gtk.gdk.BUTTON3_MASK,
                DRAG_TARGETS, gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
        for tInfo in aFilters:
            self.__oListStore.append(tInfo)

        self.connect('drag_data_get', self.drag_filter)
        self.get_selection().set_mode(gtk.SELECTION_SINGLE)

    def drag_filter(self, _oBtn, _oContext, oSelectionData, _oInfo, _oTime):
        """Create a drag info for this filter"""
        _oModel, oIter = self.get_selection().get_selected()
        if oIter:
            sSelect = 'NewFilter: %s' % self.__oListStore.get_value(oIter, 1)
            oSelectionData.set(oSelectionData.target, 8, sSelect)

class FilterValuesBox(gtk.VBox):
    """Holder for the value setting objects"""
    # pylint: disable-msg=R0904
    # R0904 - gtk.Widget, so many public methods

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
        oCheckBox = gtk.HBox()
        self.__oDisable = gtk.CheckButton('Disable')
        self.__oNegate = gtk.CheckButton('Negate')
        self.__oDelete = gtk.Button('Delete')

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

    def _get_view_widget(self, oWidget):
        """Helper function to get view from widget if needed"""
        oSetWidget = oWidget
        if hasattr(oWidget, 'view'):
            oSetWidget = oWidget.view
        return oSetWidget

    def _set_drop_for_widget(self, oWidget):
        """Set the correct drop dest behaviour for the given widget"""
        oViewWidget = self._get_view_widget(oWidget)
        oViewWidget.drag_dest_set(gtk.DEST_DEFAULT_ALL, DRAG_TARGETS,
                gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
        oViewWidget.connect('drag_data_received', self.drag_drop_handler)

    def _set_drag_for_widget(self, oWidget, fCallback, oFilter):
        """Set the correct drag source behaviour for the widget"""
        oViewWidget = self._get_view_widget(oWidget)
        oViewWidget.drag_source_set(
                gtk.gdk.BUTTON1_MASK | gtk.gdk.BUTTON3_MASK, DRAG_TARGETS,
                gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
        oViewWidget.connect('drag_data_get', fCallback, oFilter, oWidget)

    def set_widget(self, oFilter, oBoxModelEditor):
        """Replace the current widget with the correct widget for the
           new filter"""
        self._oBoxModelEditor = oBoxModelEditor
        if self._oWidget:
            self.remove(self._oWidget)
            self._oWidget = None
        if isinstance(oFilter, FilterBoxModel):
            # Select between box options
            self.__oDisable.set_active(oFilter.bDisabled)
            self.__oNegate.set_inconsistent(True)
            self.__oNegate.set_sensitive(False)
            self._oWidget = gtk.VBox()
            oFilterTypes = ScrolledList('Filter Group Type')
            oFilterTypes.set_select_single()
            oFilterTypes.fill_list(oBoxModelEditor.BOXTYPE_ORDER)
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
                    oSetList = CardSetsListView(None, self._oParent)
                    oSetList.set_select_multiple()
                    self._oWidget = AutoScrolledWindow(oSetList, False)
                    self._set_drag_for_widget(oSetList, self.update_set_list,
                            oFilter)
                    self._set_drop_for_widget(oSetList)
                else:
                    # Ordinary list
                    self._oWidget = ScrolledList('Select Filter Values')
                    self._oWidget.set_select_multiple()
                    self._oWidget.fill_list(oFilter.aValues)
                    self._set_drag_for_widget(self._oWidget,
                            self.update_filter_list, oFilter)
                    self._set_drop_for_widget(self._oWidget)
            elif oFilter.iValueType == FilterBoxItem.ENTRY:
                self._oWidget = gtk.VBox()
                self._set_drop_for_widget(self._oWidget)
                self._oWidget.pack_start(gtk.Label('Enter Text'), expand=False)
                oEntry = gtk.Entry()
                self._oWidget.pack_start(oEntry, expand=False)
                if oFilter.aCurValues:
                    oEntry.set_text(oFilter.aCurValues[0])
                oEntry.connect('changed', self.update_edit_box, oFilter)
            elif oFilter.iValueType == FilterBoxItem.LIST_FROM:
                self._oWidget = gtk.VBox()
                oCountList = ScrolledList('Select Counts')
                oCountList.set_select_multiple()
                oCountList.fill_list(oFilter.aValues[0])
                oSetList = CardSetsListView(None, self._oParent)
                oSetList.set_select_multiple()
                self._set_drag_for_widget(oSetList, self.update_count_set,
                        oFilter)
                self._set_drop_for_widget(oSetList)
                self._set_drag_for_widget(oCountList,
                        self.update_count_list, oFilter)
                self._set_drop_for_widget(oCountList)
                self._oWidget.pack_start(oCountList, expand=True)
                oLabel = gtk.Label()
                oLabel.set_markup('<b>From</b>')
                self._oWidget.pack_start(oLabel, expand=False)
                self._oWidget.pack_start(AutoScrolledWindow(oSetList, False),
                        expand=True)
            elif oFilter.iValueType == FilterBoxItem.NONE:
                # None filter, so no selection widget, but we have buttons
                self._oWidget = self._oNoneWidget
        else:
            # No selected widget, so clear everything
            self._oWidget = self._oEmptyWidget
            self.disable_all_buttons()
        self.pack_start(self._oWidget, expand=True)
        self.show_all()

    def set_box_model_value(self, oBoxModel, oWidget):
        """Set the correct selection for this box model"""
        for sDesc, tInfo in self._oBoxModelEditor.BOXTYPE.iteritems():
            sBoxType, bNegate = tInfo
            if oBoxModel.sBoxType == sBoxType and oBoxModel.bNegate == bNegate:
                oWidget.set_selected(sDesc)

    def update_box_model(self, _oSelection, oBoxModel, oList):
        """Update the box model to the current selection"""
        aSelected = oList.get_selection()
        if not aSelected:
            return # We don't do anything special if nothing's selected
        for sDesc, tInfo in self._oBoxModelEditor.BOXTYPE.iteritems():
            if sDesc == aSelected[0]:
                oBoxModel.sBoxType, oBoxModel.bNegate = tInfo
        self._oBoxModelEditor.update(oBoxModel)


    def drag_drop_handler(self, _oWindow, oDragContext, _iXPos, _iYPos,
            oSelectionData, _oInfo, oTime):
        """Handle drops from the filter toolbar"""
        if not oSelectionData and oSelectionData.format != 8:
            oDragContext.finish(False, False, oTime)
        else:
            sData =  oSelectionData.data
            oStore = self._oBoxModelEditor.get_tree_store()
            if sData.startswith('MoveValue: '):
                # Removing a value from the list
                _sSource, sValue = [x.strip() for x in sData.split(':', 1)]
                oValIter = oStore.get_iter_from_string(sValue)
                oFilter = oStore.get_value(oStore.iter_parent(oValIter), 1)
                sVal = oStore.get_value(oValIter, 0)
                if oFilter.iValueType == FilterBoxItem.LIST \
                        and sVal in oFilter.aCurValues:
                    oFilter.aCurValues.remove(sVal)
                    self._oBoxModelEditor.update_list(oFilter)
                elif oFilter.iValueType == FilterBoxItem.LIST_FROM:
                    if oFilter.aCurValues[0] and sVal in oFilter.aCurValues[0]:
                        oFilter.aCurValues[0].remove(sVal)
                    elif oFilter.aCurValues[1] and \
                            sVal in oFilter.aCurValues[1]:
                        oFilter.aCurValues[1].remove(sVal)
                    self._oBoxModelEditor.update_count_list(oFilter)
            elif sData.startswith('MoveFilter: '):
                # Removing a filter
                _sSource, sFilter = [x.strip() for x in sData.split(':', 1)]
                oMoveIter = oStore.get_iter_from_string(sFilter)
                oMoveObj = oStore.get_value(oMoveIter, 1)
                oParent  = oStore.get_value(oStore.iter_parent(oMoveIter), 1)
                oParent.remove(oMoveObj)
                self._oBoxModelEditor.load() # May break stuff
            else:
                oDragContext.finish(False, False, oTime)


    def update_filter_list(self, _oBtn, _oContext, _oSelectionData,
            _oInfo, _oTime, oFilter, _oWidget):
        """Update the box model with the new values"""
        aSelected = self._oWidget.get_selection()
        for sSet in aSelected:
            if sSet not in oFilter.aCurValues:
                oFilter.aCurValues.append(sSet)
        oFilter.aCurValues.sort()
        self._oBoxModelEditor.update_list(oFilter)

    def update_count_list(self, _oBtn, _oContext, _oSelectionData,
            _oInfo, _oTime, oFilter, oCountList):
        """Update the box model with the new values"""
        aSelected = oCountList.get_selection()
        for sCount in aSelected:
            if not oFilter.aCurValues[0]:
                oFilter.aCurValues[0] = [sCount]
            elif sCount not in oFilter.aCurValues[0]:
                oFilter.aCurValues[0].append(sCount)
        oFilter.aCurValues[0].sort()
        self._oBoxModelEditor.update_count_list(oFilter)

    def update_set_list(self, _oBtn, _oContext, _oSelectionData,
            _oInfo, _oTime, oFilter, oSetList):
        """Update the box model to the current selection"""
        aSelected = oSetList.get_all_selected_sets()
        for sSet in aSelected:
            if sSet not in oFilter.aCurValues:
                oFilter.aCurValues.append(sSet)
        oFilter.aCurValues.sort()
        self._oBoxModelEditor.update_list(oFilter)

    def update_count_set(self, _oBtn, _oContext, _oSelectionData,
            _oInfo, _oTime, oFilter, oSetList):
        """Update the box model to the current selection"""
        aSelected = oSetList.get_all_selected_sets()
        for sSet in aSelected:
            if not oFilter.aCurValues[1]:
                oFilter.aCurValues[1] = [sSet]
            elif sSet not in oFilter.aCurValues[1]:
                oFilter.aCurValues[1].append(sSet)
        oFilter.aCurValues[1].sort()
        self._oBoxModelEditor.update_count_list(oFilter)

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

class FilterBoxModelEditor(gtk.VBox):
    """Widget for editing a FilterBoxModel."""
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    BOXTYPE = { # description -> (AND or OR, bNegate)
        'All of ...': (FilterBoxModel.AND, False),
        'Any of ...': (FilterBoxModel.OR, False),
        'Not all of ...': (FilterBoxModel.AND, True),
        'None of ...': (FilterBoxModel.OR, True),
    }

    BOXTYPE_ORDER = [ # order types should appear in combo
        'All of ...', 'Any of ...', 'Not all of ...',
        'None of ...',
    ]

    BLACK =  gtk.gdk.color_parse('black')
    GREY =  gtk.gdk.color_parse('grey')
    NO_VALUE = '<i>No Values Set</i>'
    NONE_VALUE = '<b>No Values for this filter</b>'

    def __init__(self, oValuesWidget):
        super(FilterBoxModelEditor, self).__init__()
        self.__oTreeStore = gtk.TreeStore(gobject.TYPE_STRING,
                gobject.TYPE_PYOBJECT, gtk.gdk.Color)
        self.__oTreeView = gtk.TreeView(self.__oTreeStore)
        self.pack_start(self.__oTreeView, expand=True)
        oTextCell = gtk.CellRendererText()
        oColumn = gtk.TreeViewColumn("Filter", oTextCell, markup=0,
                foreground_gdk=2)
        self.__oTreeView.append_column(oColumn)

        self.__oTreeView.drag_dest_set(gtk.DEST_DEFAULT_ALL, DRAG_TARGETS,
                gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        self._oValuesWidget = oValuesWidget

        self.__oTreeView.drag_source_set(
                gtk.gdk.BUTTON1_MASK | gtk.gdk.BUTTON3_MASK,
                DRAG_TARGETS, gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        self.__oTreeView.connect('drag_data_received', self.drag_drop_handler)

        self.__oTreeView.connect('drag_data_get', self.drag_filter)

        self.__oBoxModel = None
        self.oCurSelectIter = None
        oSelection = self.__oTreeView.get_selection()
        oSelection.set_mode(gtk.SELECTION_SINGLE)
        oSelection.connect('changed', self.update_values_widget)
        self.__oTreeView.connect('button_press_event', self.press_button)

    def load(self):
        """Load the boxmodel into the TreeView"""
        def do_add_iter(oIter, oModel, bDisabled):
            """Recursively add elements of the box model"""
            oThisIter = self.__oTreeStore.append(oIter)
            oColour = self.BLACK
            if hasattr(oModel, 'sFilterDesc'):
                if oModel.bNegated:
                    sText = 'NOT %s' % oModel.sFilterDesc
                else:
                    sText = oModel.sFilterDesc
                if oModel.bDisabled or bDisabled:
                    oColour = self.GREY
                self.__oTreeStore.set(oThisIter, 0, sText, 1, oModel,
                        2, oColour)
                if oModel.iValueType == oModel.LIST_FROM:
                    # Load LIST_FROM
                    aValues, aFrom = oModel.aCurValues
                    if aValues:
                        for sValue in aValues:
                            oChild = self.__oTreeStore.append(oThisIter)
                            self.__oTreeStore.set(oChild, 0, sValue, 1, None,
                                    2, oColour)
                    else:
                        oChild = self.__oTreeStore.append(oThisIter)
                        self.__oTreeStore.set(oChild, 0, self.NO_VALUE,
                                1, None, 2, oColour)
                    oChild = self.__oTreeStore.append(oThisIter)
                    self.__oTreeStore.set(oChild, 0, '<b>From</b>', 1, None,
                            2, oColour)
                    if aFrom:
                        for sValue in aFrom:
                            oChild = self.__oTreeStore.append(oThisIter)
                            self.__oTreeStore.set(oChild, 0, sValue, 1, None,
                                    2, oColour)
                    else:
                        oChild = self.__oTreeStore.append(oThisIter)
                        self.__oTreeStore.set(oChild, 0, self.NO_VALUE,
                                1, None, 2, oColour)
                elif oModel.aCurValues and oModel.aValues:
                    for sValue in oModel.aCurValues:
                        oChild = self.__oTreeStore.append(oThisIter)
                        self.__oTreeStore.set(oChild, 0, sValue, 1, None,
                                2, oColour)
                elif oModel.aCurValues:
                    oChild = self.__oTreeStore.append(oThisIter)
                    self.__oTreeStore.set(oChild, 0, oModel.aCurValues[0],
                            1, None, 2, oColour)
                elif oModel.iValueType == oModel.NONE:
                    oChild = self.__oTreeStore.append(oThisIter)
                    self.__oTreeStore.set(oChild, 0, self.NONE_VALUE, 1, None,
                            2, oColour)
                else:
                    oChild = self.__oTreeStore.append(oThisIter)
                    self.__oTreeStore.set(oChild, 0, self.NO_VALUE, 1, None,
                            2, oColour)
            elif hasattr(oModel, 'sBoxType'):
                # Box Model, so lookup correct string
                if oModel.bDisabled or bDisabled:
                    oColour = self.GREY
                    bDisabled = True
                for sDesc, tInfo in self.BOXTYPE.iteritems():
                    sBoxType, bNegate = tInfo
                    if oModel.sBoxType == sBoxType \
                            and oModel.bNegate == bNegate:
                        self.__oTreeStore.set(oThisIter, 0, sDesc, 1, oModel,
                                2, oColour)
                # iterate over children
                for oSubModel in oModel:
                    do_add_iter(oThisIter, oSubModel, bDisabled)
            else:
                # Something else
                pass

        self.__oTreeStore.clear()
        if self.__oBoxModel is None:
            return
        # Walk the box model, creating items as we need them
        do_add_iter(None, self.__oBoxModel, False)
        self.__oTreeView.expand_all()
        # Select the root of the model by default.
        self._select_path(
                self.__oTreeStore.get_path(self.__oTreeStore.get_iter_root()))

    def drag_drop_handler(self, _oWindow, oDragContext, iXPos, iYPos,
            oSelectionData, _oInfo, oTime):
        """Handle drops from the filter toolbar"""
        if not oSelectionData and oSelectionData.format != 8:
            oDragContext.finish(False, False, oTime)
        else:
            oCurPath, _oCol = self.__oTreeView.get_cursor()
            sData =  oSelectionData.data
            if sData.startswith('NewFilter: ') or \
                    sData.startswith('MoveFilter: '):
                sSource, sFilter = [x.strip() for x in sData.split(':', 1)]
                # Check we have an acceptable drop position
                tInfo = self.__oTreeView.get_dest_row_at_pos(iXPos, iYPos)
                iIndex = 0
                if not tInfo:
                    oIter = self.__oTreeStore.get_iter_root()
                    iIndex = -1
                else:
                    oPath, iDropPos = tInfo
                    oIter = self.__oTreeStore.get_iter(oPath)
                    if self.__oTreeStore.iter_depth(oIter) > 0 and \
                            iDropPos == gtk.TREE_VIEW_DROP_BEFORE:
                        # Find the iter immediately before this one, since
                        # that's our actual target
                        oParIter = self.__oTreeStore.iter_parent(oIter)
                        oPrevIter = oParIter
                        oNextIter = self.__oTreeStore.iter_children(oParIter)
                        while self.__oTreeStore.get_path(oNextIter) != oPath:
                            oPrevIter = oNextIter
                            oNextIter = self.__oTreeStore.iter_next(oPrevIter)
                        oIter = oPrevIter
                # oIter now points to the right point to insert
                oFilterObj = self.__oTreeStore.get_value(oIter, 1)
                if not hasattr(oFilterObj, 'sBoxType'):
                    # Need to insert into parent box model
                    oTempIter = oIter
                    oInsertObj = oFilterObj
                    while not hasattr(oInsertObj, 'sBoxType'):
                        oTempIter = self.__oTreeStore.iter_parent(oTempIter)
                        oInsertObj = self.__oTreeStore.get_value(oTempIter, 1)
                        if oFilterObj is None:
                            # Bounce this up a level as well
                            oFilterObj = oInsertObj
                    # We insert after this filter
                    iIndex = oInsertObj.index(oFilterObj) + 1
                else:
                    oInsertObj = oFilterObj
                if sSource == 'NewFilter':
                    tInfo = self._oValuesWidget.get_current_pos_and_sel()
                    if sFilter == 'Filter Group':
                        oInsertObj.add_child_box(oInsertObj.AND)
                    else:
                        oInsertObj.add_child_item(sFilter)
                else:
                    # Find the dragged filter and remove it from it's current
                    # position
                    oMoveIter = self.__oTreeStore.get_iter_from_string(sFilter)
                    oMoveObj = self.__oTreeStore.get_value(oMoveIter, 1)
                    oParent  = self.__oTreeStore.get_value(
                            self.__oTreeStore.iter_parent(oMoveIter), 1)
                    # Check move is legal
                    bDoInsert = False
                    if oInsertObj != oMoveObj:
                        if not isinstance(oMoveObj, FilterBoxModel) or \
                                not oMoveObj.is_in_model(oInsertObj):
                            bDoInsert = True
                    if bDoInsert:
                        oParent.remove(oMoveObj)
                        oInsertObj.append(oMoveObj)
                    else:
                        oDragContext.finish(False, False, oTime)
                        return
                # Move to the correct place
                if iIndex >= 0:
                    oAddedFilter = oInsertObj.pop()
                    oInsertObj.insert(iIndex, oAddedFilter)
                self.load()
                if sSource == 'NewFilter':
                    # Restore selection after load
                    self._select_path(oCurPath)
                    # Restore values widget selection
                    self._oValuesWidget.restore_pos_and_selection(tInfo)
                else:
                    # Find where dropped filter ended up and select it
                    # Since we can serious muck around with the tree layout,
                    # we can't use any previous iters or paths, so we use
                    # foreach
                    self.__oTreeStore.foreach(self._check_for_obj,
                            oMoveObj)
            else:
                oDragContext.finish(False, False, oTime)

    def get_view(self):
        """Get the view object"""
        return self.__oTreeView

    def get_tree_store(self):
        """Get the tree store"""
        return self.__oTreeStore

    def _select_path(self, oPath):
        """Helper function to manage setting the selected path"""
        self.__oTreeView.set_cursor(oPath)
        self.__oTreeView.grab_focus()
        self.__oTreeView.scroll_to_cell(oPath, None, True, 0.5, 0.0)

    def _check_for_obj(self, _oModel, oPath, oIter, oFilterObj):
        """Helper function for selecting and object in the tree.
          Meant to be called via the foreach method."""
        oCurObj = self.__oTreeStore.get_value(oIter, 1)
        if oCurObj is oFilterObj:
            self._select_path(oPath)

    def drag_filter(self, _oBtn, _oContext, oSelectionData, _oInfo, _oTime):
        """Create a drag info for this filter"""
        _oModel, oIter = self.__oTreeView.get_selection().get_selected()
        if oIter and self.__oTreeStore.iter_depth(oIter) > 0:
            # We don't allow the root node to be dragged
            oFilter = self.__oTreeStore.get_value(oIter, 1)
            if oFilter is None:
                # Dragging a value
                sSelect = 'MoveValue: %s' % \
                        self.__oTreeStore.get_string_from_iter(oIter)
            else:
                # Dragging a filter
                sSelect = 'MoveFilter: %s' % \
                        self.__oTreeStore.get_string_from_iter(oIter)
            oSelectionData.set(oSelectionData.target, 8, sSelect)

    def set_box_model(self, oBoxModel):
        """Set the box model to the correct value"""
        self.__oBoxModel = oBoxModel

    def update_values_widget(self, _oTreeSelection):
        """Update the values widget to the new selection"""
        # Get the current selected row
        _oModel, oIter = self.__oTreeView.get_selection().get_selected()
        oFilterObj = None
        if oIter:
            oFilterObj = self.__oTreeStore.get_value(oIter, 1)
            while oFilterObj is None:
                oIter = self.__oTreeStore.iter_parent(oIter)
                if oIter:
                    oFilterObj = self.__oTreeStore.get_value(oIter, 1)
        self.oCurSelectIter = oIter
        if oFilterObj is None:
            self._oValuesWidget.set_widget(None, self)
            return
        elif oFilterObj.bDisabled:
            self._oValuesWidget.set_widget(None, self)
        else:
            self._oValuesWidget.set_widget(oFilterObj, self)
        if self.__oTreeStore.iter_depth(self.oCurSelectIter) > 0:
            self._oValuesWidget.enable_disable(oFilterObj)
            self._oValuesWidget.enable_delete()
        else:
            self._oValuesWidget.disable_all_buttons()

    def update(self, oBoxModel):
        """Update the listing for the given box model"""
        for sDesc, tInfo in self.BOXTYPE.iteritems():
            sBoxType, bNegate = tInfo
            if oBoxModel.sBoxType == sBoxType and oBoxModel.bNegate == bNegate:
                self.__oTreeStore.set(self.oCurSelectIter, 0, sDesc)

    def update_entry(self, oFilterItem):
        """Update the filter with the current text"""
        oChild = self.__oTreeStore.iter_children(self.oCurSelectIter)
        if not oChild:
            # No children, so oCurSelectIter is the one we want
            oChild = self.oCurSelectIter
        sText = oFilterItem.aCurValues[0]
        if not sText:
            sText = self.NO_VALUE
        self.__oTreeStore.set(oChild, 0, sText, 1, None)
        self.__oTreeView.expand_to_path(self.__oTreeStore.get_path(oChild))
        self.__oTreeView.expand_row(self.__oTreeStore.get_path(oChild), True)


    def _update_cur_iter_with_list(self, aValues):
        """Fill in the list values"""
        oChild = self.__oTreeStore.iter_children(self.oCurSelectIter)
        oCurPath, _oCol = self.__oTreeView.get_cursor()
        oCurIter = self.__oTreeStore.get_iter(oCurPath)
        iPos = 0
        iIndex = -1
        while oChild:
            oNext = self.__oTreeStore.iter_next(oChild)
            if not self.__oTreeStore.get_path(oChild) == \
                    self.__oTreeStore.get_path(oCurIter):
                self.__oTreeStore.remove(oChild)
            else:
                iIndex = iPos
            oChild = oNext
            iPos += 1
        if iIndex < 0:
            # We deleted everything, so add 1 child
            oCurIter = self.__oTreeStore.append(self.oCurSelectIter)
            iIndex = 0
        if aValues:
            iIndex = min(len(aValues) - 1, iIndex)
            iPos = 0
            for sValue in aValues:
                if iPos == iIndex:
                    oChild = oCurIter
                elif iPos < iIndex:
                    oChild = self.__oTreeStore.insert_before(
                            self.oCurSelectIter, oCurIter)
                else:
                    oChild = self.__oTreeStore.append(self.oCurSelectIter)
                if sValue is not None:
                    self.__oTreeStore.set(oChild, 0, sValue, 1, None, 2,
                            self.BLACK)
                else:
                    self.__oTreeStore.set(oChild, 0, self.NO_VALUE, 1, None,
                            2, self.BLACK)
                iPos += 1
        else:
            self.__oTreeStore.set(oCurIter, 0, self.NO_VALUE, 1, None, 2,
                    self.BLACK)
        self.__oTreeView.expand_to_path(self.__oTreeStore.get_path(oCurIter))
        self.__oTreeView.expand_row(self.__oTreeStore.get_path(oCurIter), True)

    def update_list(self, oFilterItem):
        """Update the list to show the current values"""
        self._update_cur_iter_with_list(oFilterItem.aCurValues)

    def update_count_list(self, oFilterItem):
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
        self._update_cur_iter_with_list(aValues)

    def __remove_filter_part(self, oModelOrItem):
        """Remove the filter part from this box at the user's request"""
        self.__oBoxModel.remove_child(oModelOrItem)
        self.load()

    def _get_cur_filter(self):
        """Get the currently selected filter path"""
        oCurPath, _oCol = self.__oTreeView.get_cursor()
        if oCurPath:
            return self.__oTreeStore.get_value(self.oCurSelectIter, 1), \
                    oCurPath
        return None, None

    def toggle_negate(self, _oWidget):
        """Toggle the disabled flag for a section of the filter"""
        oFilterObj, oCurPath = self._get_cur_filter()
        if oFilterObj:
            oFilterObj.bNegated = not oFilterObj.bNegated
            # We opt for the lazy approach and reload
            self.load()
            # Restore selection after load
            self._select_path(oCurPath)


    def set_negate(self, bState):
        """Set the disabled flag for a section of the filter"""
        oFilterObj, oCurPath = self._get_cur_filter()
        if oFilterObj and oFilterObj.bNegated != bState:
            oFilterObj.bNegated = bState
            # We opt for the lazy approach and reload
            self.load()
            # Restore selection after load
            self._select_path(oCurPath)

    def toggle_disabled(self, _oWidget):
        """Toggle the disabled flag for a section of the filter"""
        oFilterObj, oCurPath = self._get_cur_filter()
        if oFilterObj:
            oFilterObj.bDisabled = not oFilterObj.bDisabled
            self.load()
            self._select_path(oCurPath)

    def set_disabled(self, bState):
        """Set the disabled flag for a section of the filter"""
        oFilterObj, oCurPath = self._get_cur_filter()
        if oFilterObj and oFilterObj.bDisabled != bState:
            oFilterObj.bDisabled = bState
            # We opt for the lazy approach and reload
            self.load()
            # Restore selection after load
            self._select_path(oCurPath)

    def delete(self, _oIgnore):
        """Delete an filter component from the model

           _oIgnore is so this can be called from the popup menu"""
        oFilterObj, _oCurPath = self._get_cur_filter()
        if oFilterObj:
            oParent = self.__oTreeStore.get_value(
                    self.__oTreeStore.iter_parent(self.oCurSelectIter), 1)
            oParent.remove(oFilterObj)
            self.load()

    def press_button(self, _oWidget, oEvent):
        """Display the popup menu"""
        if oEvent.button == 3:
            iXPos = int(oEvent.x)
            iYPos = int(oEvent.y)
            oTime = oEvent.time
            oPathInfo = self.__oTreeView.get_path_at_pos(iXPos, iYPos)
            if oPathInfo is not None:
                oPath, oCol, _iCellX, _iCellY = oPathInfo
                self.__oTreeView.grab_focus()
                self.__oTreeView.set_cursor(oPath, oCol, False)
                oPopupMenu = BoxModelPopupMenu(self)
                # Show before popup, otherwise menu items aren't drawn properly
                oPopupMenu.show_all()
                oPopupMenu.popup(None, None, None, oEvent.button, oTime)
                return True # Don't propogate to buttons
        return False


class FilterHelpBuffer(gtk.TextBuffer):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """TextBuffer object used to display the help about the filters."""
    def __init__(self):
        super(FilterHelpBuffer, self).__init__(None)

        # See http://www.pygtk.org/pygtk2reference/class-gtktexttag.html
        # for some possible properties

        self.create_tag("description", weight=pango.WEIGHT_BOLD)
        self.create_tag("keyword", style=pango.STYLE_ITALIC)
        self.create_tag("helptext", left_margin=10)
        self._oIter = self.get_iter_at_offset(0)

    # pylint: disable-msg=W0142
    # ** magic OK here
    def tag_text(self, *aArgs, **kwargs):
        """Insert text into the buffer with tags."""
        self.insert_with_tags_by_name(self._oIter, *aArgs, **kwargs)

    # pylint: enable-msg=W0142

    def add_help_text(self, sDescription, sHelpText):
        """Add the given help text to the text buffer."""
        self.tag_text(sDescription, "description")
        self.tag_text(" :\n")
        self.tag_text(sHelpText, "helptext")
        self.tag_text("\n")

    def reset_iter(self):
        """reset the iterator to the start of the buffer."""
        self._oIter = self.get_iter_at_offset(0)

class FilterHelpTextView(gtk.TextView):
    """TextView widget for displaying the help text."""
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    def __init__(self, aFilterTypes):
        super(FilterHelpTextView, self).__init__()
        oBuf = FilterHelpBuffer()

        self.set_buffer(oBuf)
        self.set_editable(False)
        self.set_cursor_visible(False)
        self.set_wrap_mode(gtk.WRAP_WORD)
        self.set_border_width(5)
        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))

        oBuf.reset_iter()

        oBuf.tag_text(
            "Filter elements and values for the filters can be dragged "
            "from the right hand pane to the filter to add them to "
            "the filter, and dragged from the filter to the right hand "
            "pane to remove them from the filter. Disabled filter elements "
            "or filter elements with no values set are ignored.\n"
            "The available filtering options are listed below. "
            "The first line of each item shows the description "
            "you'll see in the filter editor in bold. "
            "The rest of the description describes the arguments "
            "the filter takes and the results it produces."
            "\n\n"
        )

        # Add test for filter group
        oBuf.add_help_text('Filter Group', "Filter element with holds "
                "other filter elements. The result of is the combination "
                "of all the filter elements as specified by the Filter "
                "Group type (All of, Any of and so on).")

        for oFilt in aFilterTypes:
            oBuf.add_help_text(oFilt.description,
                    oFilt.helptext)

        oBuf.tag_text(
            "\n"
            "Note: Using filters which require information about "
            "cards in a card set will temporarily turn off displaying "
            "cards with zero counts (for modes where this is possible) "
            "in the card list since there are no "
            "associated cards on which to base the query. "
            "Filters affected by this are: Physical Expansion, "
            "Card Sets and In Card Sets in Use."
        )
