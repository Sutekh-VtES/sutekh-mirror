# FilterEditor.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Editor component for generic filter ASTs.
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

from sutekh.gui.MultiSelectComboBox import MultiSelectComboBox
from sutekh.core.FilterParser import FilterNode, BinOpNode, NotOpNode, FilterPartNode
from sutekh.core import FilterParser
import gtk

class FilterEditor(gtk.Frame):
    """
    GTK component for editing Sutekh filter ASTs.
    """
    def __init__(self, oAST, sFilterType):
        super(FilterEditor, self).__init__(" Filter Editor ")
        self.__sFilterType = sFilterType
        self.__oBoxModel = FilterBoxModel(oAST, sFilterType)
        self.__oBoxEditor = FilterBoxModelEditor(self.__oBoxModel)
        # TODO: add button and dialog for editing filter text directly
        self.add(self.__oBoxEditor)

    def get_filter(self):
        oAST = self.get_current_ast()
        if oAST is None:
            return None
        else:
            return oAST.get_filter()

    def get_current_ast(self):
        oNewAST = self.__oBoxModel.get_ast()
        if oNewAST is None:
            return oNewAST

        dValues = self.get_current_values()
        for sName, aVals in dValues.items():
            if not aVals:
                # TODO: warn user about missing values or disable OK button
                #       when values not filled in
                return None

        aNewValues = oNewAST.get_values()
        for oValue in aNewValues:
            if oValue.is_entry() or oValue.is_list():
                oValue.node.setValues(dValues[oValue.node.get_name()])

        return oNewAST

    def get_current_values(self):
        return self.__oBoxEditor.get_current_values()

    def set_current_values(self, dVars):
        self.__oBoxEditor.set_current_values(dVars)

    def get_current_text(self):
        return self.__oBoxModel.get_text()

class FilterBoxModel(list):
    """
    Converts a filter AST into a simple nest box model.

    Each box either ANDs or ORs all of its contained filters.
    Each contained filter may optionally be negated.
    Values are retained for each contained filter.
    """

    AND, OR = 'and', 'or'

    def __init__(self, oAST, sFilterType, oVarNameMaker=None):
        """
        Initialise a filter box from an AST filter representation.
        """
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
        elif type(oAST) is NotOpNode and type(oAST.oSubExpression) is BinOpNode:
            self.bNegate = True
            self.sBoxType = oAST.oSubExpression.oOp
            self._init_binop(oAST.oSubExpression)
        elif type(oAST) is FilterPartNode or \
             type(oAST) is NotOpNode and type(oAST.oSubExpression) is FilterPartNode:
            self.sBoxType = self.AND
            self.append(FilterBoxItem(oAST))
        elif oAST is None:
            # support for completely empty boxes
            self.sBoxType = self.AND
        else:
            raise ValueError("FilterBoxModel cannot represent AST %s of type %s" % (oAST, type(oAST)))

        assert self.sBoxType in [self.AND, self.OR]

        if bVarMakerNeedsInit:
            self.oVarNameMaker.update(self.get_variable_names())

    def _init_binop(self, oBinOp):
        for oChild in [oBinOp.oLeft, oBinOp.oRight]:
            if type(oChild) is BinOpNode and oChild.oOp == oBinOp.oOp:
                self._init_binop(oChild)
            elif type(oChild) is BinOpNode:
                self.append(FilterBoxModel(oChild, self.sFilterType, self.oVarNameMaker))
            elif type(oChild) in [NotOpNode, FilterPartNode]:
                self.append(FilterBoxItem(oChild))
            else:
                raise ValueError("FilterBoxModel encountered unsupported AST node type %s (%s) while examing BinOpNode tree." % (type(oChild), oChild))

    def set_boxtype(self, sBoxType, bNegate=False):
        self.sBoxType = sBoxType
        self.bNegate = bNegate

    def get_variable_names(self):
        oNames = set()
        for oChild in self:
            oNames.update(oChild.get_variable_names())
        return oNames

    def get_ast(self):
        """
        Return an AST representation of the filter.
        """
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
        """
        Return a text representation of the filter.
        """
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
        return [oFilterType for oFilterType in FilterParser.aFilters if self.sFilterType in oFilterType.types]

    def add_child_box(self, sChildBoxType):
        assert sChildBoxType in [self.AND, self.OR]
        oChildBox = FilterBoxModel(None, self.sFilterType, self.oVarNameMaker)
        oChildBox.sBoxType = sChildBoxType
        self.append(oChildBox)
        return oChildBox

    def add_child_item(self, sChildTypeKeyword):
        sVarName = self.oVarNameMaker.generate_name()
        oAST = FilterPartNode(sChildTypeKeyword, None, sVarName)
        oChildItem = FilterBoxItem(oAST)
        self.append(oChildItem)
        return oChildItem

    def remove_child(self, oChild):
        self.remove(oChild)

class FilterBoxModelEditor(gtk.VBox):
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

    def __init__(self, oBoxModel):
        super(FilterBoxModelEditor, self).__init__(spacing=5)
        self.__oBoxModel = oBoxModel
        self.__aChildren = []
        self.__fRemoveBox = None # set by parent (if any)

        self.__oBoxTypeSelector = gtk.combo_box_new_text()
        self.pack_start(self.__oBoxTypeSelector, expand=False)

        for i, sDesc in enumerate(self.BOXTYPE_ORDER):
            self.__oBoxTypeSelector.append_text(sDesc)
            sBoxType, bNegate = self.BOXTYPE[sDesc]
            if self.__oBoxModel.sBoxType == sBoxType \
               and self.__oBoxModel.bNegate == bNegate:
                self.__oBoxTypeSelector.set_active(i)

        self.__oBoxTypeSelector.connect('changed', self.__change_boxtype)

        oChildHBox = gtk.HBox(spacing=10)
        oChildHBox.pack_start(gtk.VSeparator(), expand=False)
        self.__oChildArea = gtk.VBox(spacing=5)
        oChildHBox.pack_start(self.__oChildArea)
        self.pack_start(oChildHBox, expand=False)

        for oChild in self.__oBoxModel:
            if type(oChild) is FilterBoxModel:
                oModelEditor = FilterBoxModelEditor(oChild)
                oModelEditor.register_remove_box(self.__remove_model)
                self.__aChildren.append(oModelEditor)
                self.__oChildArea.pack_start(oModelEditor, expand=False)
            else:
                oItemEditor = FilterBoxItemEditor(oChild)
                oItemEditor.connect_remove_button(self.__remove_filter_part)
                self.__aChildren.append(oItemEditor)
                self.__oChildArea.pack_start(oItemEditor, expand=False)

        self.pack_start(gtk.HSeparator(), expand=False)

        oHBox = gtk.HBox()
        self.pack_start(oHBox, expand=False)

        oAddButton = gtk.Button("+")
        oHBox.pack_start(oAddButton, expand=False)

        oTypeSelector = gtk.combo_box_new_text()
        oHBox.pack_start(oTypeSelector, expand=False)

        oAddButton.connect('clicked', self.__add_filter_part, oTypeSelector)

        for oFilterType in self.__oBoxModel.get_filter_types():
            oTypeSelector.append_text(oFilterType.keyword)
            # TODO: display FilterType.helptext somewhere

        oTypeSelector.append_text("Sub-Filter")

    def get_title(self):
        if self.__oBoxModel.sBoxType == FilterBoxModel.AND:
            return "All of ..."
        else:
            return "One of ..."

    def get_current_values(self):
        """Return a dictionary of name -> value mappings for the variables present
           in the filter editing gui.
           """
        dVars = {}
        for oChild in self.__aChildren:
            dVars.update(oChild.get_current_values())
        return dVars

    def set_current_values(self, dVars):
        """
        Set the current list values using variable names in the given dictionary.

        dVars is a mapping sVariableName -> [ list of string values ]
        """
        for oChild in self.__aChildren:
            oChild.set_current_values(dVars)

    def register_remove_box(self, fRemoveBox):
        """
        Register a function for removing this box from it's parent editor.

        fRemoveBox(oBoxEditor, oBoxModel)
        """
        self.__fRemoveBox = fRemoveBox
        self.__oBoxTypeSelector.append_text("Remove Sub-Filter")
        self.__oBoxTypeSelector.show_all()

    def __change_boxtype(self, oBoxTypeSelector):
        sType = oBoxTypeSelector.get_active_text()
        if sType == "Remove Sub-Filter":
            self.__fRemoveBox(self, self.__oBoxModel)
        else:
            sBoxType, bNegate = self.BOXTYPE[sType]
            self.__oBoxModel.set_boxtype(sBoxType, bNegate)

    def __add_filter_part(self, oAddButton, oTypeSelector):
        sType = oTypeSelector.get_active_text()
        if not sType:
            # ignore add button clicks when a type isn't selected
            return
        if sType == "Sub-Filter":
            oChildBoxModel = self.__oBoxModel.add_child_box(FilterBoxModel.AND)
            oChildEditor = FilterBoxModelEditor(oChildBoxModel)
            oChildEditor.register_remove_box(self.__remove_model)
        else:
            oChildItem = self.__oBoxModel.add_child_item(sType)
            oChildEditor = FilterBoxItemEditor(oChildItem)
            oChildEditor.connect_remove_button(self.__remove_filter_part)
        self.__aChildren.append(oChildEditor)
        self.__oChildArea.pack_start(oChildEditor, expand=False)
        self.show_all()

    def __remove_filter_part(self, oRemoveButton, oEditor, oModelOrItem):
        self.__oBoxModel.remove_child(oModelOrItem)
        self.__aChildren.remove(oEditor)
        self.__oChildArea.remove(oEditor)

    def __remove_model(self, oEditor, oModel):
        self.__remove_filter_part(None, oEditor, oModel)

class FilterBoxItem(object):
    def __init__(self, oAST):
        if type(oAST) is NotOpNode:
            self.bNegated = True
            oAST = oAST.oSubExpression
        else:
            self.bNegated = False

        assert type(oAST) is FilterPartNode

        self.sFilterType = oAST.filtertype
        self.sVariableName = oAST.sVariableName
        self.aFilterValues = oAST.filtervalues
        self.bNoneFilter = False

        # process values
        self.sLabel, self.aValues = None, None
        for oValue in oAST.get_values():
            if oValue.is_value():
                assert self.sLabel is None
                self.sLabel = oValue.value
            elif oValue.is_list():
                assert self.aValues is None
                self.aValues = oValue.value
            elif oValue.is_entry():
                pass
            elif oValue.is_None():
                self.bNoneFilter = True
                pass

        assert self.sLabel is not None

    def get_variable_names(self):
        return set([self.sVariableName])

    def get_ast(self):
        """
        Return an AST respresentation of the filter.
        """
        oAST = FilterPartNode(self.sFilterType, self.aFilterValues, self.sVariableName)
        if self.bNegated:
            oAST = NotOpNode(oAST)
        return oAST

    def get_text(self):
        """
        Return a text representation of the filter.
        """
        if self.bNoneFilter:
            sText = self.sFilterType
        else:
            sText = "%s in %s" % (self.sFilterType, self.sVariableName)
        return sText

class FilterBoxItemEditor(gtk.HBox):
    def __init__(self, oBoxItem):
        super(FilterBoxItemEditor, self).__init__(spacing=5)
        self.__oBoxItem = oBoxItem

        self.__oRemoveButton = gtk.Button("-")
        self.pack_start(self.__oRemoveButton, expand=False)

        self.__oNegateButton = gtk.CheckButton("NOT")
        self.__oNegateButton.set_active(self.__oBoxItem.bNegated)
        self.__oNegateButton.connect('toggled', self.__toggle_negated)
        self.pack_start(self.__oNegateButton, expand=False)

        self.pack_start(gtk.Label(self.__oBoxItem.sLabel), expand=False)

        if self.__oBoxItem.aValues:
            oWidget = MultiSelectComboBox()
            oWidget.fill_list(self.__oBoxItem.aValues)
            oWidget.set_list_size(200, 400)
        elif self.__oBoxItem.bNoneFilter:
            oWidget = gtk.Label('  < No user data required > ')
        else:
            oWidget = gtk.Entry(100)
            oWidget.set_width_chars(30)

        self.__oEntryWidget = oWidget
        self.pack_start(oWidget)

    def connect_remove_button(self, fHandler):
        if self.__oRemoveButton is not None:
            self.__oRemoveButton.connect('clicked', fHandler, self, self.__oBoxItem)

    def get_current_values(self):
        dVars = {}
        sName = self.__oBoxItem.sVariableName
        if self.__oBoxItem.aValues:
            aSelection = self.__oEntryWidget.get_selection()
            if self.__oBoxItem.sFilterType in FilterParser.aWithFilters:
                aSplit = [sItem.split(" with ") for sItem in aSelection]
                aVals = ['"%s with %s"' % (sPart1, sPart2) for sPart1, sPart2 in aSplit]
            else:
                aVals = ['"%s"' % (sItem,) for sItem in aSelection]
            dVars[sName] = aVals
        else:
            sText = self.__oEntryWidget.get_text()
            if sText != '':
                dVars[sName] = ['"' + sText + '"']
        return dVars

    def set_current_values(self, dVars):
        sName = self.__oBoxItem.sVariableName
        if not sName in dVars:
            return
        if self.__oBoxItem.aValues:
            aVals = [sVal.strip('"') for sVal in dVars[sName]]
            self.__oEntryWidget.set_selection(aVals)
        else:
            self.__oEntryWidget.set_text(dVars[sName][0].strip('"'))

    def __toggle_negated(self, oWidget):
        self.__oBoxItem.bNegated = self.__oNegateButton.get_active()

class VariableNameGenerator(set):
    KEYFORM = "$var%s"

    def __init__(self):
        super(VariableNameGenerator, self).__init__()
        self.__iNum = 0

    def generate_name(self):
        sName = self.KEYFORM % self.__iNum
        while sName in self:
            self.__iNum += 1
            sName = self.KEYFORM % self.__iNum
        self.add(sName)
        return sName
