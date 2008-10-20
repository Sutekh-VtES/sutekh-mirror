# FilterEditor.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Editor component for generic filter ASTs.
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Widget for ediging filters."""

from sutekh.gui.MultiSelectComboBox import MultiSelectComboBox
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.core.FilterParser import FilterNode, BinOpNode, NotOpNode, \
        FilterPartNode
from sutekh.core import FilterParser
import gtk
import pango
import gobject

class FilterEditor(gtk.Frame):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """GTK component for editing Sutekh filter ASTs.

       Provides a graphical representation of the filter as nested boxes,
       which the user can extend or remove from.
       """
    def __init__(self, oAST, sFilterType, oParser, oFilterDialog):
        super(FilterEditor, self).__init__(" Filter Editor ")
        self.__sFilterType = sFilterType
        self.__oParser = oParser
        self.__oFilterDialog = oFilterDialog # Dialog we're a child of

        self.__oBoxModel = None
        self.__oBoxEditor = None

        oNameLabel = gtk.Label("Filter name:")
        self.__oNameEntry = gtk.Entry()
        self.__oNameEntry.set_width_chars(30)

        oTextEditorButton = gtk.Button("Edit Query Text")
        oTextEditorButton.connect("clicked", self.__show_text_editor)
        oHelpButton = gtk.Button("Help")
        oHelpButton.connect("clicked", self.__show_help_dialog)

        oHBox = gtk.HBox(spacing=5)
        oHBox.pack_start(oNameLabel, expand=False)
        oHBox.pack_start(self.__oNameEntry, expand=False)
        oHBox.pack_end(oHelpButton, expand=False)
        oHBox.pack_end(oTextEditorButton, expand=False)

        self.__oVBox = gtk.VBox(spacing=5)
        self.__oVBox.pack_end(oHBox, expand=False)
        self.__oVBox.pack_end(gtk.HSeparator(), expand=False)

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
        oNewAST = self.__oBoxModel.get_ast()
        if oNewAST is None:
            return oNewAST

        dValues = self.get_current_values()
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

    def replace_ast(self, oAST):
        """Replace the current AST with a new one and update the GUI,
           preserving variable values if possible.

           Also used to setup the filter initially.
           """
        if self.__oBoxEditor is None:
            dVars = {}
        else:
            dVars = self.get_current_values()
            self.__oVBox.remove(self.__oBoxEditor)

        self.__oBoxModel = FilterBoxModel(oAST, self.__sFilterType)
        self.__oBoxEditor = FilterBoxModelEditor(self.__oBoxModel,
                self.__oFilterDialog)
        self.__oVBox.pack_start(self.__oBoxEditor)
        self.show_all()

        self.set_current_values(dVars)

    def get_current_values(self):
        """Get the current values in the editor."""
        return self.__oBoxEditor.get_current_values()

    def set_current_values(self, dVars):
        """Set the values in the editor to those in dVars."""
        self.__oBoxEditor.set_current_values(dVars)

    def get_current_text(self):
        """Get the current text in the editor."""
        return self.__oBoxModel.get_text()

    def set_name(self, sName):
        """Set the filter name."""
        self.__oNameEntry.set_text(sName)

    def get_name(self):
        """Get the filter name."""
        return self.__oNameEntry.get_text().strip()

    def connect_name_changed(self, fCallback):
        """Connect a callback to the name entry change signal."""
        self.__oNameEntry.connect('changed', fCallback)

    # pylint: disable-msg=W0613
    # oTextEditorButton required by function signature
    def __show_text_editor(self, oTextEditorButton):
        """Show a gtk.Entry widget so filters can be directly typed by the
           user."""
        oDlg = SutekhDialog("Query Editor", self.__oFilterDialog,
                gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                 gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        oDlg.set_default_size(600, -1)

        oEntry = gtk.Entry()
        oEntry.set_text(self.get_current_text())
        # pylint: disable-msg=E1101
        # vbox confuse pylint
        oDlg.vbox.pack_start(oEntry)
        oDlg.show_all()

        try:
            iResponse = oDlg.run()
            if iResponse == gtk.RESPONSE_OK:
                sNewFilter = oEntry.get_text()
                try:
                    oAST = self.__oParser.apply(sNewFilter)
                except ValueError, oExcep:
                    do_complaint_error("Invalid Filter: %s\n Error: %s"
                            % (sNewFilter, str(oExcep)))
                else:
                    self.replace_ast(oAST)
        finally:
            oDlg.destroy()

    # oHelpButton required by function signature
    def __show_help_dialog(self, oHelpButton):
        """Show a dialog window with the helptext from the filters."""
        oDlg = SutekhDialog("Help on Filters", self.__oFilterDialog,
                gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))

        oDlg.set_default_size(600, 500)
        # pylint: disable-msg=E1101
        # vbox confuse pylint

        oHelpView = AutoScrolledWindow(FilterHelpTextView(
            self.__oBoxModel.get_filter_types()))
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
        aChildASTs = [oChild.get_ast() for oChild in self]
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
        return [oFilterType for oFilterType in FilterParser.aParserFilters
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

    def __init__(self, oBoxModel, oParentWin):
        super(FilterBoxModelEditor, self).__init__(spacing=5)
        self.__oBoxModel = oBoxModel
        self.__aChildren = []
        self.__fRemoveBox = None # set by parent (if any)
        self.__oParentWin = oParentWin

        self.__oBoxTypeSelector = gtk.combo_box_new_text()
        self.pack_start(self.__oBoxTypeSelector, expand=False)

        for iLoop, sDesc in enumerate(self.BOXTYPE_ORDER):
            self.__oBoxTypeSelector.append_text(sDesc)
            sBoxType, bNegate = self.BOXTYPE[sDesc]
            if self.__oBoxModel.sBoxType == sBoxType \
               and self.__oBoxModel.bNegate == bNegate:
                self.__oBoxTypeSelector.set_active(iLoop)

        self.__oBoxTypeSelector.connect('changed', self.__change_boxtype)

        oChildHBox = gtk.HBox(spacing=10)
        oChildHBox.pack_start(gtk.VSeparator(), expand=False)
        self.__oChildArea = gtk.VBox(spacing=5)
        oChildHBox.pack_start(self.__oChildArea)
        self.pack_start(oChildHBox, expand=False)

        for oChild in self.__oBoxModel:
            if type(oChild) is FilterBoxModel:
                oModelEditor = FilterBoxModelEditor(oChild, self.__oParentWin)
                oModelEditor.register_remove_box(self.__remove_model)
                self.__aChildren.append(oModelEditor)
                self.__oChildArea.pack_start(oModelEditor, expand=False)
            else:
                oItemEditor = FilterBoxItemEditor(oChild, self.__oParentWin)
                oItemEditor.connect_remove_button(self.__remove_filter_part)
                self.__aChildren.append(oItemEditor)
                self.__oChildArea.pack_start(oItemEditor, expand=False)

        self.pack_start(gtk.HSeparator(), expand=False)

        oHBox = gtk.HBox()
        self.pack_start(oHBox, expand=False)

        oAddButton = gtk.Button("+")
        oHBox.pack_start(oAddButton, expand=False)

        oTypeSelector = self._make_type_list()
        oHBox.pack_start(oTypeSelector, expand=False)

        oAddButton.connect('clicked', self.__add_filter_part, oTypeSelector)

    def _make_type_list(self):
        """Create a combo box to select the filter type."""
        oTypeStore = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING,)
        oTypeSelector = gtk.ComboBox(oTypeStore)
        oCell = gtk.CellRendererText()
        oTypeSelector.pack_start(oCell, True)
        oTypeSelector.add_attribute(oCell, 'text', 0)

        for oFilterType in self.__oBoxModel.get_filter_types():
            oIter = oTypeStore.append(None)
            oTypeStore.set(oIter, 0, oFilterType.description,
                                  1, oFilterType.keyword)
        oIter = oTypeStore.append(None)
        oTypeStore.set(oIter, 0, "Sub-Filter",
                              1, None)

        return oTypeSelector

    def get_title(self):
        """Get the correct title for this box"""
        if self.__oBoxModel.sBoxType == FilterBoxModel.AND:
            return "All of ..."
        else:
            return "One of ..."

    def get_current_values(self):
        """Return a dictionary of name -> value mappings for the variables
           present in the filter editing gui.
           """
        dVars = {}
        for oChild in self.__aChildren:
            dVars.update(oChild.get_current_values())
        return dVars

    def set_current_values(self, dVars):
        """Set the current list values using variable names in the given
           dictionary.

           dVars is a mapping sVariableName -> [ list of string values ]
           """
        for oChild in self.__aChildren:
            oChild.set_current_values(dVars)

    def register_remove_box(self, fRemoveBox):
        """Register a function for removing this box from it's parent editor.

           The function signature is fRemoveBox(oBoxEditor, oBoxModel)
           """
        self.__fRemoveBox = fRemoveBox
        self.__oBoxTypeSelector.append_text("Remove Sub-Filter")
        self.__oBoxTypeSelector.show_all()

    def __change_boxtype(self, oBoxTypeSelector):
        """Change the type of this box to that chosen by the user."""
        sType = oBoxTypeSelector.get_active_text()
        if sType == "Remove Sub-Filter":
            self.__fRemoveBox(self, self.__oBoxModel)
        else:
            sBoxType, bNegate = self.BOXTYPE[sType]
            self.__oBoxModel.set_boxtype(sBoxType, bNegate)

    # pylint: disable-msg=W0613
    # oAddButton needed by function signature
    def __add_filter_part(self, oAddButton, oTypeSelector):
        """Add a filter part or filter box to this box."""
        oIter = oTypeSelector.get_active_iter()
        oModel = oTypeSelector.get_model()

        if not oIter:
            # ignore add button clicks when a type isn't selected
            return

        sDescription = oModel.get_value(oIter, 0)
        sKeyword = oModel.get_value(oIter, 1)

        if sDescription == "Sub-Filter":
            oChildBoxModel = self.__oBoxModel.add_child_box(FilterBoxModel.AND)
            oChildEditor = FilterBoxModelEditor(oChildBoxModel,
                    self.__oParentWin)
            oChildEditor.register_remove_box(self.__remove_model)
        else:
            oChildItem = self.__oBoxModel.add_child_item(sKeyword)
            oChildEditor = FilterBoxItemEditor(oChildItem, self.__oParentWin)
            oChildEditor.connect_remove_button(self.__remove_filter_part)

        self.__aChildren.append(oChildEditor)
        self.__oChildArea.pack_start(oChildEditor, expand=False)
        self.show_all()

    # oRemoveButton needed by function signature
    def __remove_filter_part(self, oRemoveButton, oEditor, oModelOrItem):
        """Remove the filter part from this box at the user's request"""
        self.__oBoxModel.remove_child(oModelOrItem)
        self.__aChildren.remove(oEditor)
        self.__oChildArea.remove(oEditor)

    def __remove_model(self, oEditor, oModel):
        """Remove the filter model from this box"""
        self.__remove_filter_part(None, oEditor, oModel)

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

        self.sFilterName = oAST.sFilterName
        self.sVariableName = oAST.sVariableName
        self.aFilterValues = oAST.aFilterValues
        self.iValueType = None

        # process values
        self.sLabel, self.aValues = None, None
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

    def get_ast(self):
        """Return an AST respresentation of the filter."""
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
        return sText

class FilterBoxItemEditor(gtk.HBox):
    """Widget for editing the entries for the filter associated with a
       FilterBoxItem."""
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    def __init__(self, oBoxItem, oParent):
        super(FilterBoxItemEditor, self).__init__(spacing=5)
        self.__oBoxItem = oBoxItem

        self.__oRemoveButton = gtk.Button("-")
        self.pack_start(self.__oRemoveButton, expand=False)

        self.__oNegateButton = gtk.CheckButton("NOT")
        self.__oNegateButton.set_active(self.__oBoxItem.bNegated)
        self.__oNegateButton.connect('toggled', self.__toggle_negated)
        self.pack_start(self.__oNegateButton, expand=False)

        self.pack_start(gtk.Label(self.__oBoxItem.sLabel), expand=False)

        if self.__oBoxItem.iValueType == FilterBoxItem.LIST:
            oWidget = MultiSelectComboBox(oParent)
            oWidget.fill_list(self.__oBoxItem.aValues)
            oWidget.set_list_size(200, 400)
        elif self.__oBoxItem.iValueType == FilterBoxItem.LIST_FROM:
            # Create an additional widget for the from side
            oWidget = MultiSelectComboBox(oParent)
            oWidget.fill_list(self.__oBoxItem.aValues[0])
            oWidget.set_list_size(200, 400)
            oFromStore = gtk.ListStore(str)
            self.__oFromWidget = gtk.ComboBox(oFromStore)
            oCell = gtk.CellRendererText()
            self.__oFromWidget.pack_start(oCell, True)
            self.__oFromWidget.add_attribute(oCell, 'text', 0)
            for sCardSet in self.__oBoxItem.aValues[1]:
                oIter = oFromStore.append(None)
                oFromStore.set(oIter, 0, sCardSet)
            self.pack_end(self.__oFromWidget, False, False)
            self.pack_end(gtk.Label(' from '), False, False)
        elif self.__oBoxItem.iValueType == FilterBoxItem.NONE:
            oWidget = gtk.Label('  < No user data required > ')
        elif self.__oBoxItem.iValueType == FilterBoxItem.ENTRY:
            oWidget = gtk.Entry(100)
            oWidget.set_width_chars(30)
        else:
            raise RuntimeError("Unknown FilterBoxItem ValueType %s" %
                    (self.__oBoxItem.iValueType,))

        self.__oEntryWidget = oWidget
        self.pack_start(oWidget)

    def connect_remove_button(self, fHandler):
        """Add a handler for the 'remove filter' button"""
        if self.__oRemoveButton is not None:
            self.__oRemoveButton.connect('clicked', fHandler, self,
                    self.__oBoxItem)

    def get_current_values(self):
        """Get the current values set for this filter."""
        dVars = {}
        sName = self.__oBoxItem.sVariableName
        if self.__oBoxItem.aValues:
            aSelection = self.__oEntryWidget.get_selection()
            if self.__oBoxItem.sFilterName in FilterParser.aWithFilters:
                aSplit = [sItem.split(" with ") for sItem in aSelection]
                aVals = ['"%s with %s"' % (sPart1, sPart2) for sPart1,
                        sPart2 in aSplit]
            elif self.__oBoxItem.sFilterName in FilterParser.aFromFilters:
                # Need to sort out how to handle this case
                oIter = self.__oFromWidget.get_active_iter()
                oModel = self.__oFromWidget.get_model()
                if not oIter:
                    sFrom = None
                else:
                    sFrom = '"%s"' % oModel.get_value(oIter, 0)
                aVals = [['"%s"' % (sItem,) for sItem in aSelection], sFrom]
            else:
                aVals = ['"%s"' % (sItem,) for sItem in aSelection]
            dVars[sName] = aVals
        else:
            sText = self.__oEntryWidget.get_text()
            if sText != '':
                dVars[sName] = ['"' + sText + '"']
        return dVars

    def set_current_values(self, dVars):
        """Set the current values for the entry widget for this filter
           item."""
        sName = self.__oBoxItem.sVariableName
        if not sName in dVars:
            return
        if self.__oBoxItem.aValues:
            if self.__oBoxItem.iValueType == FilterBoxItem.LIST:
                aVals = [sVal.strip('"') for sVal in dVars[sName]]
                self.__oEntryWidget.set_selection(aVals)
            elif self.__oBoxItem.iValueType == FilterBoxItem.LIST_FROM:
                if len(dVars[sName]) != 2:
                    return
                aVals = [sVal.strip('"') for sVal in dVars[sName][0]]
                self.__oEntryWidget.set_selection(aVals)
                sFrom = dVars[sName][1]
                if sFrom:
                    sFrom = sFrom.strip('"')
                    oModel = self.__oFromWidget.get_model()
                    oIter = oModel.get_iter_first()
                    while oIter:
                        sEntry = oModel.get(oIter, 0)[0]
                        if sEntry == sFrom:
                            self.__oFromWidget.set_active_iter(oIter)
                            break
                        oIter = oModel.iter_next(oIter)
        elif len(dVars[sName]) > 0:
            self.__oEntryWidget.set_text(dVars[sName][0].strip('"'))
        else:
            self.__oEntryWidget.set_text("")

    # pylint: disable-msg=W0613
    # oWidget is needed by function signature
    def __toggle_negated(self, oWidget):
        """Response to the use setting/unsetting the not status of this
           filter item"""
        self.__oBoxItem.bNegated = self.__oNegateButton.get_active()

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

class FilterHelpBuffer(gtk.TextBuffer, object):
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

class FilterHelpTextView(gtk.TextView, object):
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
