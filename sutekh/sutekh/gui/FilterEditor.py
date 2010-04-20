# FilterEditor.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Editor component for generic filter ASTs.
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Widget for editing filters."""

from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.gui.CardSetsListView import CardSetsListView
from sutekh.gui.ScrolledList import ScrolledList
from sutekh.core.FilterParser import FilterNode, BinOpNode, NotOpNode, \
        FilterPartNode
from sutekh.core import FilterParser
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
        oNewAST = self.__oPanes.get_ast()
        if oNewAST is None:
            return oNewAST

        dValues = self.__oPanes.get_current_values()
        for aVals in dValues.values():
            if not aVals:
                do_complaint_error("Some filter values have not been " \
                                   "filled in so the selected filter " \
                                   "will be ignored")
                return None

        aNewValues = oNewAST.get_values()
        for oValue in aNewValues:
            if oValue.is_entry() or oValue.is_list() or oValue.is_tuple():
                oValue.oNode.set_values(dValues[oValue.oNode.get_name()])

        return oNewAST

    def get_current_text(self):
        """Get the current text of the filter for saving in the config
           file."""
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

        oHelpView = AutoScrolledWindow(FilterHelpTextView(
            self.__oPanes.get_filter_types()))
        oDlg.vbox.pack_start(oHelpView)
        oDlg.show_all()

        try:
            oDlg.run()
        finally:
            oDlg.destroy()


class FilterBoxModel(list):
    """Converts a filter AST into a simple nest box model.

       Each box either ANDs or ORs all of its contained filters.
       Each contained filter may optionally be negated.
       Values are retained for each contained filter.
       """

    AND, OR = 'and', 'or'

    # pylint: disable-msg=W0231
    # no point to calling list's __init__
    def __init__(self, oAST, sFilterType, oVarNameMaker=None):
        """Initialise a filter box from an AST filter representation."""
        if oVarNameMaker is None:
            oVarNameMaker = VariableNameGenerator()
            bVarMakerNeedsInit = True
        else:
            bVarMakerNeedsInit = False

        self.sFilterType = sFilterType
        self.bNegate = False
        self.bDisabled = False
        self.oVarNameMaker = oVarNameMaker

        if type(oAST) is FilterNode:
            oAST = oAST.oExpression

        if type(oAST) is BinOpNode:
            self.sBoxType = oAST.oOp
            self._init_binop(oAST)
        elif type(oAST) is NotOpNode and \
                type(oAST.oSubExpression) is BinOpNode:
            self.bNegate = True
            self.sBoxType = oAST.oSubExpression.oOp
            self._init_binop(oAST.oSubExpression)
        elif type(oAST) is FilterPartNode or \
                type(oAST) is NotOpNode and \
                type(oAST.oSubExpression) is FilterPartNode:
            self.sBoxType = self.AND
            self.append(FilterBoxItem(oAST))
        elif oAST is None:
            # support for completely empty boxes
            self.sBoxType = self.AND
        else:
            raise ValueError("FilterBoxModel cannot represent AST %s of"
                    " type %s" % (oAST, type(oAST)))

        assert self.sBoxType in [self.AND, self.OR]

        if bVarMakerNeedsInit:
            self.oVarNameMaker.update(self.get_variable_names())

    def _init_binop(self, oBinOp):
        """Create the correct box entries for a BinOpNode in the AST."""
        for oChild in [oBinOp.oLeft, oBinOp.oRight]:
            if type(oChild) is BinOpNode and oChild.oOp == oBinOp.oOp:
                self._init_binop(oChild)
            elif type(oChild) is BinOpNode:
                self.append(FilterBoxModel(oChild, self.sFilterType,
                    self.oVarNameMaker))
            elif type(oChild) in [NotOpNode, FilterPartNode]:
                self.append(FilterBoxItem(oChild))
            else:
                raise ValueError("FilterBoxModel encountered unsupported AST"
                        " node type %s (%s) while examing BinOpNode tree." %
                        (type(oChild), oChild))

    def set_boxtype(self, sBoxType, bNegate=False):
        """Set the type for this filter box"""
        self.sBoxType = sBoxType
        self.bNegate = bNegate

    def get_variable_names(self):
        """Get the variable names of the children in this box."""
        oNames = set()
        for oChild in self:
            oNames.update(oChild.get_variable_names())
        return oNames

    def get_ast(self):
        """Return an AST representation of the filter."""
        if self.bDisabled:
            return None

        aChildASTs = [oChild.get_ast() for oChild in self
                if not oChild.bDisabled]
        aChildASTs = [oChild for oChild in aChildASTs if oChild is not None]

        if len(aChildASTs) == 0:
            oAST = None
        elif len(aChildASTs) == 1:
            oAST = aChildASTs[0]
        else:
            oAST = BinOpNode(aChildASTs[0], self.sBoxType, aChildASTs[1])
            for oChild in aChildASTs[2:]:
                oAST = BinOpNode(oAST, self.sBoxType, oChild)

        if self.bNegate and oAST is not None:
            oAST = NotOpNode(oAST)

        return oAST

    def get_text(self):
        """Return a text representation of the filter."""
        aChildTexts = [oChild.get_text() for oChild in self]
        aChildTexts = [sChild for sChild in aChildTexts if sChild]

        if len(aChildTexts) == 0:
            sText = ''
        elif len(aChildTexts) == 1:
            sText = aChildTexts[0]
        else:
            sText = "(" + (") %s (" % self.sBoxType).join(aChildTexts) + ")"

        if self.bNegate and sText:
            sText = "NOT (%s)" % (sText,)

        return sText

    def get_filter_types(self):
        """Get the types support by this filter."""
        return [oFilterType for oFilterType in FilterParser.PARSER_FILTERS
                if self.sFilterType in oFilterType.types]

    def add_child_box(self, sChildBoxType):
        """Add a child box to this box."""
        assert sChildBoxType in [self.AND, self.OR]
        oChildBox = FilterBoxModel(None, self.sFilterType, self.oVarNameMaker)
        oChildBox.sBoxType = sChildBoxType
        self.append(oChildBox)
        return oChildBox

    def add_child_item(self, sChildTypeKeyword):
        """Add a filter item to this box."""
        sVarName = self.oVarNameMaker.generate_name()
        oAST = FilterPartNode(sChildTypeKeyword, None, sVarName)
        oChildItem = FilterBoxItem(oAST)
        self.append(oChildItem)
        return oChildItem

    def remove_child(self, oChild):
        """Remove a filter item or box from this box."""
        self.remove(oChild)

    def is_in_model(self, oChild):
        """Check if oChild is included in this box model, either directly
           or in a child box model."""
        if oChild in self:
            return True
        for oObj in self:
            if isinstance(oObj, FilterBoxModel) and oObj.is_in_model(oChild):
                return True
        return False


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

    def get_current_values(self):
        """Get the list of values from the editor"""
        return self.__oEditor.get_current_values()

    def get_filter_types(self):
        """Get a listing of all filter types"""
        return self.__oBoxModel.get_filter_types()

    def replace_ast(self, oAST):
        """Replace the AST in the tree model"""
        dVars = self.__oEditor.get_current_values()

        self.__oBoxModel = FilterBoxModel(oAST, self.__sFilterType)
        self.__oEditor.set_box_model(self.__oBoxModel)
        self.__oEditor.load()
        self.__oEditor.set_current_values(dVars)

    def get_ast(self):
        """Get the current ast"""
        if self.__oBoxModel:
            return self.__oBoxModel.get_ast()
        return None

    def get_text(self):
        """Get the current ast"""
        if self.__oBoxModel:
            return self.__oBoxModel.get_text()
        return None

    def get_values(self):
        """Get the current values"""
        if self.__oBoxModel:
            return self.__oEditor.get_values()
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
        for oFilterType in sorted(self.get_filter_types(),
                key=lambda x: x.description):
            aFilters.append((oFilterType.description, oFilterType.keyword))
        # Create buttons for each of the filters we support
        self.drag_source_set(gtk.gdk.BUTTON1_MASK | gtk.gdk.BUTTON3_MASK,
                DRAG_TARGETS, gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
        for tInfo in aFilters:
            self.__oListStore.append(tInfo)

        self.connect('drag_data_get', self.drag_filter)
        self.get_selection().set_mode(gtk.SELECTION_SINGLE)

    def get_filter_types(self):
        """Get the types support by this filter."""
        return [oFilterType for oFilterType in FilterParser.PARSER_FILTERS
                if self.__sFilterType in oFilterType.types]

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
        self._oParent = oDialog
        self.__sFilterType = sFilterType
        self._oEmptyWidget.pack_start(gtk.Label(
            'Select an active\nfilter element'), expand=False)
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
            self._oWidget.pack_start(oFilterTypes, expand=True)
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
                if oFilter.sFilterName == "PhysicalSet" or \
                        oFilter.sFilterName == "ParentCardSet":
                    # Special case to use card set list widget
                    oSetList = CardSetsListView(None, self._oParent)
                    oSetList.set_select_multiple()
                    if oFilter.aCurValues:
                        oSetList.set_all_selected_sets(oFilter.aCurValues)
                    oSetList.get_selection_object().connect('changed',
                            self.update_set_list, oFilter, oSetList)
                    self._oWidget = AutoScrolledWindow(oSetList, False)
                else:
                    # Ordinary list
                    self._oWidget = ScrolledList('Select Filter Values')
                    self._oWidget.set_select_multiple()
                    self._oWidget.fill_list(oFilter.aValues)
                    if oFilter.aCurValues:
                        self._oWidget.set_selection(oFilter.aCurValues)
                    self._oWidget.get_selection_object().connect('changed',
                            self.update_filter_list, oFilter)
            elif oFilter.iValueType == FilterBoxItem.ENTRY:
                self._oWidget = gtk.VBox()
                self._oWidget.pack_start(gtk.Label('Enter Text'), expand=False)
                oEntry = gtk.Entry()
                self._oWidget.pack_start(oEntry, expand=False)
                if oFilter.aCurValues:
                    oEntry.set_text(oFilter.aCurValues[0])
                oEntry.connect('changed', self.update_edit_box, oFilter)
            elif oFilter.iValueType == FilterBoxItem.LIST_FROM:
                self._oWidget = gtk.VBox()
                aCurCounts, aFrom = [], []
                if oFilter.aCurValues:
                    aCurCounts, aFrom = oFilter.aCurValues
                oCountList = ScrolledList('Select Counts')
                oCountList.set_select_multiple()
                oCountList.fill_list(oFilter.aValues[0])
                if aCurCounts:
                    oCountList.set_selection(aCurCounts)
                oSetList = CardSetsListView(None, self._oParent)
                oSetList.set_select_multiple()
                if aFrom:
                    oSetList.set_all_selected_sets(aFrom)
                oSetList.get_selection_object().connect('changed',
                        self.update_count_set, oFilter, oSetList)
                oCountList.get_selection_object().connect('changed',
                            self.update_count_list, oFilter, oCountList)
                self._oWidget.pack_start(oCountList, expand=True)
                oLabel = gtk.Label()
                oLabel.set_markup('<b>From</b>')
                self._oWidget.pack_start(oLabel, expand=False)
                self._oWidget.pack_start(AutoScrolledWindow(oSetList, False),
                        expand=True)
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

    def update_filter_list(self, _oSelection, oFilter):
        """Update the box model to the current selection"""
        aSelected = self._oWidget.get_selection()
        oFilter.aCurValues = aSelected
        self._oBoxModelEditor.update_list(oFilter)

    def update_count_list(self, _oSelection, oFilter, oCountList):
        """Update the box model to the current selection"""
        aSelected = oCountList.get_selection()
        if aSelected:
            oFilter.aCurValues[0] = aSelected
        else:
            oFilter.aCurValues[0] = None
        self._oBoxModelEditor.update_count_list(oFilter)

    def update_set_list(self, _oSelection, oFilter, oSetList):
        """Update the box model to the current selection"""
        aSelected = oSetList.get_all_selected_sets()
        oFilter.aCurValues = aSelected
        self._oBoxModelEditor.update_list(oFilter)

    def update_count_set(self, _oSelection, oFilter, oSetList):
        """Update the box model to the current selection"""
        aSelected = oSetList.get_all_selected_sets()
        if aSelected:
            oFilter.aCurValues[1] = aSelected
        else:
            oFilter.aCurValues[1] = None
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
            self._oBoxModelEditor.delete()

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

        self.__oTreeView.drag_source_set(
                gtk.gdk.BUTTON1_MASK | gtk.gdk.BUTTON3_MASK,
                DRAG_TARGETS, gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        self.__oTreeView.connect('drag-data-received', self.drag_drop_handler)

        self.__oTreeView.connect('drag_data_get', self.drag_filter)

        self.__oBoxModel = None
        self.oCurSelectIter = None
        oSelection = self.__oTreeView.get_selection()
        oSelection.set_mode(gtk.SELECTION_SINGLE)
        oSelection.connect('changed', self.update_values_widget, oValuesWidget)

    def load(self):
        """Load the boxmodel into the TreeView"""
        def do_add_iter(oIter, oModel, bDisabled):
            """Recursively add elements of the box model"""
            oThisIter = self.__oTreeStore.append(oIter)
            oColour = self.BLACK
            if hasattr(oModel, 'sFilterName'):
                if oModel.bNegated:
                    sText = 'NOT %s' % oModel.sFilterName
                else:
                    sText = oModel.sFilterName
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

        oCurPath, _oCol = self.__oTreeView.get_cursor()
        if not oSelectionData and oSelectionData.format != 8:
            oDragContext.finish(False, False, oTime)
        else:
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
                else:
                    # Find where dropped filter ended up and select it
                    # Since we can serious muck around with the tree layout,
                    # we can't use any previous iters or paths, so we use
                    # foreach
                    self.__oTreeStore.foreach(self._check_for_obj,
                            oMoveObj)
            else:
                oDragContext.finish(False, False, oTime)

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
                # Dragging a value moves the entire filter
                oIter = self.__oTreeStore.iter_parent(oIter)
            sSelect = 'MoveFilter: %s' % \
                    self.__oTreeStore.get_string_from_iter(oIter)
            oSelectionData.set(oSelectionData.target, 8, sSelect)

    def set_box_model(self, oBoxModel):
        """Set the box model to the correct value"""
        self.__oBoxModel = oBoxModel

    def update_values_widget(self, _oTreeSelection, oValuesWidget):
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
            oValuesWidget.set_widget(None, self)
            return
        elif oFilterObj.bDisabled:
            oValuesWidget.set_widget(None, self)
        else:
            oValuesWidget.set_widget(oFilterObj, self)
        if self.__oTreeStore.iter_depth(self.oCurSelectIter) > 0:
            oValuesWidget.enable_disable(oFilterObj)
            oValuesWidget.enable_delete()
        else:
            oValuesWidget.disable_all_buttons()

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

    def get_current_values(self):
        """Return a dictionary of name -> value mappings for the variables
           present in the filter editing gui.
           """
        dVars = {}
        self.__oTreeStore.foreach(self.get_child_values, dVars)
        return dVars

    def get_child_values(self, _oModel, _oPath, oIter, dVars):
        """Get the values out of the child value"""
        oChild = self.__oTreeStore.get_value(oIter, 1)
        if isinstance(oChild, FilterBoxItem):
            dVars.update(oChild.get_current_values())

    def set_current_values(self, dVars):
        """Set the current list values using variable names in the given
           dictionary.

           dVars is a mapping sVariableName -> [ list of string values ]
           """
        self.__oTreeStore.foreach(self.set_child_values, dVars)

    def set_child_values(self, _oModel, _oPath, oIter, dVars):
        """Get the values out of the child value"""
        oChild = self.__oTreeStore.get_value(oIter, 1)
        if isinstance(oChild, FilterBoxItem):
            oChild.set_current_values(dVars)

    def __remove_filter_part(self, oModelOrItem):
        """Remove the filter part from this box at the user's request"""
        self.__oBoxModel.remove_child(oModelOrItem)
        self.load()

    def set_negate(self, bState):
        """Set the disabled flag for a section of the filter"""
        oCurPath, _oCol = self.__oTreeView.get_cursor()
        oFilterObj = self.__oTreeStore.get_value(self.oCurSelectIter, 1)
        if oFilterObj.bNegated != bState:
            oFilterObj.bNegated = bState
            # We opt for the lazy approach and reload
            self.load()
            # Restore selection after load
            self._select_path(oCurPath)

    def set_disabled(self, bState):
        """Set the disabled flag for a section of the filter"""
        oCurPath, _oCol = self.__oTreeView.get_cursor()
        oFilterObj = self.__oTreeStore.get_value(self.oCurSelectIter, 1)
        if oFilterObj.bDisabled != bState:
            oFilterObj.bDisabled = bState
            # We opt for the lazy approach and reload
            self.load()
            # Restore selection after load
            self._select_path(oCurPath)

    def delete(self):
        """Delete an filter component from the model"""
        oFilterObj = self.__oTreeStore.get_value(self.oCurSelectIter, 1)
        oParent = self.__oTreeStore.get_value(self.__oTreeStore.iter_parent(
            self.oCurSelectIter), 1)
        oParent.remove(oFilterObj)
        self.load()

class FilterBoxItem(object):
    """A item in the filter editor.

       This represents either a single FilterPart or a single
       NOT(FilterPart) expression in the AST.
       """
    NONE, ENTRY, LIST, LIST_FROM = range(4)

    def __init__(self, oAST):
        if type(oAST) is NotOpNode:
            self.bNegated = True
            oAST = oAST.oSubExpression
        else:
            self.bNegated = False

        assert type(oAST) is FilterPartNode

        self.bDisabled = False

        self.sFilterName = oAST.sFilterName
        self.sVariableName = oAST.sVariableName
        self.aFilterValues = oAST.aFilterValues
        self.iValueType = None

        # process values
        self.sLabel, self.aValues = None, None
        self.aCurValues = []
        for oValue in oAST.get_values():
            if oValue.is_value():
                assert self.sLabel is None
                self.sLabel = oValue.oValue
            elif oValue.is_list():
                assert self.iValueType is None
                self.aValues = oValue.oValue
                self.iValueType = self.LIST
            elif oValue.is_tuple():
                assert self.iValueType is None
                self.aValues = oValue.oValue
                self.iValueType = self.LIST_FROM
                self.aCurValues = [None, None]
            elif oValue.is_entry():
                assert self.iValueType is None
                self.iValueType = self.ENTRY
            elif oValue.is_None():
                assert self.iValueType is None
                self.iValueType = self.NONE

        assert self.sLabel is not None
        assert self.iValueType is not None

    def get_variable_names(self):
        """Get the variable name for this filter"""
        return set([self.sVariableName])

    def get_current_values(self):
        """Get the current values set for this filter."""
        dVars = {}
        # Flag as empty by default
        dVars[self.sVariableName] = None
        if self.aCurValues:
            if self.iValueType == self.LIST:
                dVars[self.sVariableName] = ['"%s"' % sValue for sValue in
                        self.aCurValues]
            elif self.iValueType == self.LIST_FROM:
                aValues, aFrom = self.aCurValues
                if aFrom:
                    aFrom = ['"%s"' % x for x in aFrom]
                    if aValues:
                        aValues = ['"%s"' % x for x in aValues]
                        dVars[self.sVariableName] = [aValues, aFrom]
            elif self.iValueType == self.ENTRY:
                dVars[self.sVariableName] = ['"%s"' % self.aCurValues[0]]
        return dVars

    def set_current_values(self, dVars):
        """Set the current values for the entry widget for this filter
           item."""
        sName = self.sVariableName
        if not sName in dVars:
            return
        if self.aValues:
            if self.iValueType == FilterBoxItem.LIST:
                aVals = [sVal.strip('"') for sVal in dVars[sName]]
                self.aCurValues = aVals
            elif self.iValueType == FilterBoxItem.LIST_FROM:
                if len(dVars[sName]) != 2:
                    return
                aVals = [sVal.strip('"') for sVal in dVars[sName][0]]
                aFrom = [sVal.strip('"') for sVal in dVars[sName][1]]
                self.aCurValues = [aVals, aFrom]
        elif len(dVars[sName]) > 0:
            self.aCurValues = [dVars[sName][0].strip('"')]
        else:
            self.aCurValues = []

    def get_ast(self):
        """Return an AST representation of the filter."""
        oAST = FilterPartNode(self.sFilterName, self.aFilterValues,
                self.sVariableName)
        if self.bNegated:
            oAST = NotOpNode(oAST)
        return oAST

    def get_text(self):
        """Return a text representation of the filter."""
        if self.iValueType == self.NONE:
            sText = self.sFilterName
        else:
            sText = "%s in %s" % (self.sFilterName, self.sVariableName)
        if self.bNegated:
            return "NOT (%s)" % sText
        return sText

class VariableNameGenerator(set):
    """Generate a unique name for a variable in a filter."""
    KEYFORM = "$var%s"

    def __init__(self):
        super(VariableNameGenerator, self).__init__()
        self.__iNum = 0

    def generate_name(self):
        """Generate the next variable in the list."""
        sName = self.KEYFORM % self.__iNum
        while sName in self:
            self.__iNum += 1
            sName = self.KEYFORM % self.__iNum
        self.add(sName)
        return sName

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

    def add_help_text(self, sDescription, sKeyword, sHelpText):
        """Add the given help text to the text buffer."""
        self.tag_text(sDescription, "description")
        self.tag_text(" (")
        self.tag_text(sKeyword, "keyword")
        self.tag_text(") :\n")
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
            "The available filtering options are listed below. "
            "The first line of each item shows the description "
            "you'll see in the filter editor in bold with the "
            "keyword to use in query strings in italics afterwards. "
            "The rest of the description describes the arguments "
            "the filter takes and the results it produces."
            "\n\n"
        )

        for oFilt in aFilterTypes:
            oBuf.add_help_text(oFilt.description, oFilt.keyword,
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
