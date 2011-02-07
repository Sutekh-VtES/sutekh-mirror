# FilterBox.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Filter Box abstraction used by the editor.
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# Split out from FilterEditor 2010 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""FilterBox model of the filters. Mainly used in filter editor"""

from sutekh.core.FilterParser import FilterNode, BinOpNode, NotOpNode, \
        FilterPartNode, escape


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
            self.append(FilterBoxItem(oAST, self.oVarNameMaker))
        elif oAST is None:
            # support for completely empty boxes
            self.sBoxType = self.AND
        else:
            raise ValueError("FilterBoxModel cannot represent AST %s of"
                    " type %s" % (oAST, type(oAST)))

        assert self.sBoxType in (self.AND, self.OR)

        if bVarMakerNeedsInit:
            self.oVarNameMaker.update(self.get_variable_names())

    def __eq__(self, oOther):
        """Non-list equality check so empty boxes aren't equal"""
        return self is oOther

    def _init_binop(self, oBinOp):
        """Create the correct box entries for a BinOpNode in the AST."""
        for oChild in (oBinOp.oLeft, oBinOp.oRight):
            if type(oChild) is BinOpNode and oChild.oOp == oBinOp.oOp:
                self._init_binop(oChild)
            elif type(oChild) is BinOpNode:
                self.append(FilterBoxModel(oChild, self.sFilterType,
                    self.oVarNameMaker))
            elif type(oChild) is NotOpNode and \
                    type(oChild.oSubExpression) is BinOpNode:
                self.append(FilterBoxModel(oChild, self.sFilterType,
                    self.oVarNameMaker))
            elif type(oChild) in (NotOpNode, FilterPartNode):
                self.append(FilterBoxItem(oChild, self.oVarNameMaker))
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

    def get_ast_with_values(self):
        """Return AST with values filled in"""
        oNewAST = self.get_ast()
        if oNewAST:
            dValues = self.get_current_values()
            aNewValues = oNewAST.get_values()
            for oValue in aNewValues:
                if oValue.is_entry() or oValue.is_list() or oValue.is_tuple():
                    oValue.oNode.set_values(dValues[oValue.oNode.get_name()])

        return oNewAST

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

    def get_current_values(self):
        """Return a dictionary of name -> value mappings for the variables
           present in the filter editing gui.
           """
        dVars = {}
        for oChild in self:
            dVars.update(oChild.get_current_values())
        return dVars

    def add_child_box(self, sChildBoxType):
        """Add a child box to this box."""
        assert sChildBoxType in (self.AND, self.OR)
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


class FilterBoxItem(object):
    """A item in the filter editor.

       This represents either a single FilterPart or a single
       NOT(FilterPart) expression in the AST.
       """
    # pylint: disable-msg=R0902
    # We track a lot of state, so several instance attributes
    NONE, ENTRY, LIST, LIST_FROM = range(4)

    def __init__(self, oAST, oVarNameMaker=None):
        if type(oAST) is NotOpNode:
            self.bNegated = True
            oAST = oAST.oSubExpression
        else:
            self.bNegated = False

        assert type(oAST) is FilterPartNode

        self.bDisabled = False

        self.sFilterName = oAST.sFilterName
        self.sFilterDesc = oAST.get_description()
        self.sVariableName = oAST.sVariableName
        if not self.sVariableName and oVarNameMaker is not None:
            self.sVariableName = oVarNameMaker.generate_name()
        elif self.sVariableName and oVarNameMaker is not None:
            if self.sVariableName in oVarNameMaker:
                self.sVariableName = oVarNameMaker.generate_name()
            else:
                oVarNameMaker.update([self.sVariableName])
        self.iValueType = None

        self.sLabel, self.aValues = None, None
        self.aCurValues = []
        # process values
        self._set_value_type(oAST)
        assert self.sLabel is not None
        assert self.iValueType is not None

        self._set_values(oAST)

    def _set_value_type(self, oAST):
        """Set the value type and label for the filter"""
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

    def _set_values(self, oAST):
        """Initialise the values of the filter item"""
        aFilterValues = oAST.aFilterValues
        if aFilterValues:
            if self.iValueType == self.LIST_FROM:
                assert len(aFilterValues.get_values()) == 2
                oLeft, oRight = aFilterValues.get_values()
                aFrom, aValues = [], []
                for oNode in oLeft:
                    if oNode.oValue != ',':
                        aValues.append(oNode.oValue)
                if '-1' in aValues:
                    aValues = None  # Sentinal case
                for oNode in oRight:
                    if oNode.oValue != ',':
                        aFrom.append(oNode.oValue)
                if "" in aFrom:
                    aFrom = None  # Sentinal case
                self.aCurValues = [aValues, aFrom]
            elif self.iValueType == self.ENTRY:
                assert len(aFilterValues.get_values()) == 1
                self.aCurValues = [aFilterValues.get_values()[0].oValue]
            else:
                # List filter
                for oNode in aFilterValues.get_values():
                    if oNode.oValue != ',':
                        self.aCurValues.append(oNode.oValue)

    def get_variable_names(self):
        """Get the variable name for this filter"""
        return set([self.sVariableName])

    def get_current_values(self):
        """Get the current values set for this filter.

           We escape the values to ensure we handle quotes and so forth
           sanely"""
        dVars = {}
        # Flag as empty by default
        dVars[self.sVariableName] = None
        if self.aCurValues:
            if self.iValueType == self.LIST:
                dVars[self.sVariableName] = ['"%s"' % escape(sValue)
                        for sValue in self.aCurValues]
            elif self.iValueType == self.LIST_FROM:
                aValues, aFrom = self.aCurValues
                if aFrom:
                    aFrom = ['"%s"' % escape(x) for x in aFrom]
                    if aValues:
                        aValues = ['"%s"' % escape(x) for x in aValues]
                        dVars[self.sVariableName] = [aValues, aFrom]
            elif self.iValueType == self.ENTRY:
                dVars[self.sVariableName] = ['"%s"' %
                        escape(self.aCurValues[0])]
        return dVars

    def get_ast(self):
        """Return an AST representation of the filter."""
        if (not self.aCurValues and self.iValueType != self.NONE) \
                or self.bDisabled:
            return None
        oAST = FilterPartNode(self.sFilterName, None,
                self.sVariableName)
        if self.bNegated:
            oAST = NotOpNode(oAST)
        return oAST

    def get_text(self):
        """Return a text representation of the filter."""
        if self.iValueType == self.NONE:
            sText = self.sFilterName
        elif self.aCurValues:
            sValues = None
            sText = "%s in %s" % (self.sFilterName, self.sVariableName)
            if self.iValueType == self.LIST:
                sValues = ",".join(['"%s"' % escape(sValue) for sValue in
                        self.aCurValues])
            elif self.iValueType == self.LIST_FROM:
                aValues, aFrom = self.aCurValues
                sFromValues = '"-1"'
                sFrom = '""'  # Sentinals
                if aValues:
                    sFromValues = ",".join(['"%s"' % escape(x)
                        for x in aValues])
                if aFrom:
                    sFrom = ",".join(['"%s"' % escape(x) for x in aFrom])
                if aFrom or aValues:
                    sValues = "%s FROM %s" % (sFromValues, sFrom)
            elif self.iValueType == self.ENTRY:
                sValues = '"%s"' % escape(self.aCurValues[0])
            if sValues:
                sText = '%s in %s' % (self.sFilterName, sValues)
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

# Useful constants for dealing with the filter boxes

BOXTYPE = {  # description -> (AND or OR, bNegate)
    'All of ...': (FilterBoxModel.AND, False),
    'Any of ...': (FilterBoxModel.OR, False),
    'Not all of ...': (FilterBoxModel.AND, True),
    'None of ...': (FilterBoxModel.OR, True),
}

BOXTYPE_ORDER = [  # order types should appear in combo
    'All of ...', 'Any of ...', 'Not all of ...', 'None of ...',
]
