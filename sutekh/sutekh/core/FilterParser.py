# FilterParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Provides filter parsing functionality.

   Use PLY to convert a string into a Abstract Syntax Tree, from which the
   final Filter Object is constructed
   """

# pylint: disable-msg=E0611
# pylint 0.18 misses ply parts
import ply.lex as lex
import ply.yacc as yacc
# pylint: enable-msg=E0611
from sutekh.core.Filters import PARSER_FILTERS, FilterNot, FilterAndBox, \
        FilterOrBox


ENTRY_FILTERS = set([x.keyword for x in PARSER_FILTERS
    if hasattr(x, 'istextentry') and x.istextentry])
WITH_FILTERS = set([x.keyword for x in PARSER_FILTERS
    if hasattr(x, 'iswithfilter') and x.iswithfilter])
FROM_FILTERS = set([x.keyword for x in PARSER_FILTERS
    if hasattr(x, 'isfromfilter') and x.isfromfilter])
LIST_FILTERS = set([x.keyword for x in PARSER_FILTERS
    if hasattr(x, 'islistfilter') and x.islistfilter])


# Misc utility functions
def get_filter_type(sKeyword):
    """Get the actual filter object from the type string"""
    # pylint: disable-msg=W0621
    return [x for x in PARSER_FILTERS if x.keyword == sKeyword][0]


def get_filters_for_type(sFilterType):
    """Get the filters associated with this filter type."""
    return [oFilterType for oFilterType in PARSER_FILTERS
            if sFilterType in oFilterType.types]


# We define an object for the lex parser
# pylint is never going to like the naming conventions here,
# which are based on ply examples
class ParseFilterDefinitions(object):
    """Provides the lexer used by PLY"""
    # pylint: disable-msg=C0103, R0201
    aKeywords = set([x.keyword for x in PARSER_FILTERS])

    tokens = (
            'NOT',
            'FILTERTYPE',
            'ID',
            'STRING',
            'OR',
            'AND',
            'COMMA',
            'IN',
            'LPAREN',
            'RPAREN',
            'VARIABLE',
            'WITH',
            'FROM',
            )

    t_AND = r'\&\&'
    t_OR = r'\|\|'
    t_STRING = r'"(\\\\|\\\'|\\"|[^"\\])*?"|\'(\\\\|\\\'|\\"|[^\'\\])*?\''
    t_COMMA = r','
    t_IN = r'='
    t_LPAREN = r'\('
    t_RPAREN = r'\)'

    # Ignore whitespace and returns
    t_ignore = ' \t\n'

    # Simplistic error handler
    def t_error(self, t):
        """Lexer error handler"""
        raise ValueError("Illegal Character '%s'" % t.value[0])

    def t_ID(self, t):
        r'[A-Za-z0-9><$_]+'
        if t.value in self.aKeywords:
            t.type = 'FILTERTYPE'
        elif t.value.lower() == 'and':
            t.type = 'AND'
        elif t.value.lower() == 'or':
            t.type = 'OR'
        elif t.value.lower() == 'in':
            t.type = 'IN'
        elif t.value.lower() == 'not':
            t.type = 'NOT'
        elif t.value[0] == '$':
            t.type = 'VARIABLE'
        elif t.value.lower() == 'with':
            t.type = 'WITH'
        elif t.value.lower() == 'from':
            t.type = 'FROM'
        else:
            t.type = 'STRING'
        return t

    # Ply docs say don't do this in __init__, so we don't
    # pylint: disable-msg=W0201, W0142
    def build(self, **kwargs):
        """Create the lexer object.

           Done outside of __init__, as PLY docs state this is required
           """
        self.oLexer = lex.lex(object=self, **kwargs)

    def apply(self, sData):
        """Apply the lexer to the string sData"""
        self.oLexer.input(sData)
        aResults = []
        while 1:
            oToken = self.oLexer.token()
            if not oToken:
                return aResults
            aResults.append(oToken)


# Define a yacc parser to produce the abstract syntax tree
class FilterYaccParser(object):
    """Provide the parser used by PLY"""
    # pylint: disable-msg=C0103, R0201
    tokens = ParseFilterDefinitions.tokens
    aUsedVariables = []

    # COMMA's have higher precedence than AND + OR
    # This shut's up most shift/reduce warnings
    precedence = (
            ('left', 'AND', 'OR'),
            ('left', 'NOT'),
            ('left', 'IN'),
            ('left', 'FROM'),
            ('left', 'COMMA'),
            ('left', 'WITH'),
    )

    def reset(self):
        """Reset the used variables history"""
        self.aUsedVariables = []

    def p_filter(self, p):
        """filter : filterpart
                  | empty"""
        p[0] = FilterNode(p[1])

    def p_filterpart_brackets(self, p):
        """filterpart : LPAREN filterpart RPAREN"""
        p[0] = p[2]

    def p_filterpart_AND(self, p):
        """filterpart : filterpart AND filterpart"""
        p[0] = BinOpNode(p[1], 'and', p[3])

    def p_filterpart_OR(self, p):
        """filterpart : filterpart OR filterpart"""
        p[0] = BinOpNode(p[1], 'or', p[3])

    def p_filterpart_NOT(self, p):
        """filterpart : NOT filterpart"""
        p[0] = NotOpNode(p[2])

    def p_filterpart_filtertype(self, p):
        """filterpart : FILTERTYPE IN expression
                      | FILTERTYPE NOT IN expression"""
        if len(p) == 4:
            p[0] = FilterPartNode(p[1], p[3], None)
        else:
            p[0] = NotOpNode(FilterPartNode(p[1], p[4], None))

    def p_filterpart_var(self, p):
        """filterpart : FILTERTYPE IN VARIABLE
                      | FILTERTYPE NOT IN VARIABLE"""
        if len(p) == 4:
            sVarName = p[3]
            oResult = FilterPartNode(p[1], None, sVarName)
        else:
            sVarName = p[4]
            oResult = NotOpNode(FilterPartNode(p[1], None, sVarName))
        if sVarName not in self.aUsedVariables and sVarName != '$':
            p[0] = oResult
            self.aUsedVariables.append(sVarName)
        elif sVarName != '$':
            raise ValueError("Duplicate variable name %s" % sVarName)
        else:
            raise ValueError("Missing variable name for %s" % sVarName)

    def p_filterpart(self, p):
        """filterpart : FILTERTYPE"""
        oNode = FilterPartNode(p[1], None, None)
        aRes = oNode.get_values()
        if aRes[1].is_None():
            # Filter that takes no type, so legal
            p[0] = FilterPartNode(p[1], None, None)
        else:
            raise ValueError("Missing values or variable for filter")

    def p_expression_comma(self, p):
        """expression : expression COMMA expression"""
        p[0] = CommaNode(p[1], p[2], p[3])

    def p_expression_string(self, p):
        """expression : STRING"""
        p[0] = StringNode(p[1])

    def p_expression_id(self, p):
        """expression : ID"""
        # Shouldn't actually trigger this rule with a legal filter string
        raise ValueError("Invalid filter element: %s" % p[1])

    def p_expression_with(self, p):
        """expression : expression WITH expression"""
        p[0] = WithNode(p[1], p[2], p[3])

    def p_expression_from(self, p):
        """expression : expression FROM expression"""
        p[0] = FromNode(p[1], p[2], p[3])

    def p_empty(self, p):
        """empty :"""
        pass

    def p_error(self, p):
        """Parsing error handler"""
        if p is None:
            raise ValueError("No valid identifier or missing variable name")
        else:
            raise ValueError("Invalid identifier: %s " % p.value)


# Wrapper objects around the parser
class FilterParser(object):
    """Entry point for filter parsing. Wraps Lexer and Parser Objects"""
    # pylint: disable-msg=R0903
    # This really does only need the 1 public method
    _oGlobalLexer = None
    _oGlobalParser = None
    _oGlobalFilterParser = None

    def __init__(self):
        """Create the global Parser and Lexer objects if needed"""
        if not self._oGlobalLexer:
            self._oGlobalLexer = ParseFilterDefinitions()
            self._oGlobalLexer.build()

        if not self._oGlobalParser:
            # yacc needs an initialised lexer
            self._oGlobalFilterParser = FilterYaccParser()
            self._oGlobalParser = yacc.yacc(module=self._oGlobalFilterParser,
                                            debug=0,
                                            write_tables=0)

    def apply(self, sFilter):
        """Apply the parser to the string sFilter"""
        self._oGlobalFilterParser.reset()
        if sFilter != '':
            oAST = self._oGlobalParser.parse(sFilter)
        else:
            # '' can cause the lexer to bomb out, so we avoid it
            oAST = self._oGlobalParser.parse(' ')
        return oAST


# Helper functions for dealing with strings
def escape(sData):
    """Escape quotes and \\'s in the string"""
    # escape \'s
    sResult = sData.replace('\\', '\\\\')
    # escape quotes
    sResult = sResult.replace("'", "\\'")
    sResult = sResult.replace('"', '\\"')
    return sResult


def unescape(sData):
    """Unescape quotes and \\'s in the string.

       should be the inverse of escape."""
    # unescape quotes
    # We assume that this is called on a escaped sring, after any
    # surrounding quotes have been stripped off, so there are no unescaped
    # quotes to worry about
    sResult = sData.replace("\\'", "'")
    sResult = sResult.replace('\\"', '"')
    # unsecape \\
    sResult = sResult.replace('\\\\', '\\')
    return sResult


# Object used by get_values representation
# Should be made more robust
class ValueObject(object):
    """Object to represent values extracted from the AST"""

    def __init__(self, oValue, oNode):
        """Initialise ValueObject with oValue and AST node oNode"""
        self.oValue = oValue
        self.oNode = oNode

    def is_entry(self):
        """Does this represent a text entry?"""
        return isinstance(self.oValue, str) and self.oValue == ''

    def is_list(self):
        """Does this represent a list?"""
        return isinstance(self.oValue, list)

    def is_tuple(self):
        """Does this represent a tuple? (for from filters)"""
        return isinstance(self.oValue, tuple)

    def is_value(self):
        """Does this represent a assigned string value?"""
        return isinstance(self.oValue, str) and self.oValue != ''

    # pylint: disable-msg=C0103
    def is_None(self):
        """Is this node's value None?"""
        return self.oValue is None


# AST object (formulation inspired by Simon Cross's example, and notes
# from the ply documentation)
class AstBaseNode(object):
    """Basic node class for the AST. Other nodes inherit from this"""

    def __init__(self, aChildren):
        """Store children"""
        self.aChildren = aChildren

    def __str__(self):
        """String representation of the AST

           Useful for debugging
           """
        sAttrs = '(' + ",".join([str(oValue) for sKey, oValue \
                in self.__dict__.items() if not sKey.startswith("_") and \
                sKey != "aChildren" and oValue not in self.aChildren]) + ")"
        sOutput = self.__class__.__name__ + sAttrs
        for oChild in self.aChildren:
            sOutput += "\n" + \
                    "\n".join(["\t" + sVal for sVal in
                        str(oChild).split("\n")])
        return sOutput

    def get_values(self):
        """Get the values associated with this node"""
        pass

    def get_filter(self):
        """Get the filter associated with the node"""
        pass

    def get_invalid_values(self):
        """Get values which are invalid for the associated filter"""
        pass

    def get_type(self):
        """Get type information of the associated filter"""
        pass


class FilterNode(AstBaseNode):
    """Represents a Filter in the AST"""

    def __init__(self, oExpression):
        """Set filter oExpression"""
        super(FilterNode, self).__init__([oExpression])
        self.oExpression = oExpression

    def get_filter_expression(self):
        """Get the actual final filter expression"""
        return self.oExpression

    def get_values(self):
        """Get filter values"""
        if self.oExpression:
            return self.oExpression.get_values()
        else:
            return None

    def get_filter(self):
        """Get filter"""
        if self.oExpression:
            return self.oExpression.get_filter()
        else:
            return None

    def get_invalid_values(self):
        """Get values that are invalid for this filter"""
        if self.oExpression:
            return self.oExpression.get_invalid_values()
        else:
            return None

    def get_type(self):
        """Get filter type"""
        if self.oExpression:
            return self.oExpression.get_type()
        else:
            return None


class OperatorNode(AstBaseNode):
    """Base class for nodes involving operators"""
    pass


class TermNode(AstBaseNode):
    """Node to represent values in the AST"""

    def get_type(self):
        """Return type.

           Always returns None as values nodes have no value - only
           filters have meaningful type information
           """
        return None


class StringNode(TermNode):
    """String value in the AST"""

    def __init__(self, sValue):
        """Set value"""

        super(StringNode, self).__init__([sValue])
        # Strip quotes off strings
        if sValue[0] == '"' and sValue[-1] == '"':
            self.sValue = sValue[1:-1]
        elif sValue[0] == "'" and sValue[-1] == "'":
            self.sValue = sValue[1:-1]
        else:
            self.sValue = sValue
        # Unescape quotes and \'s if needed
        self.sValue = unescape(self.sValue)

    def get_values(self):
        """Return the ValueObject holding the string"""
        return [ValueObject(self.sValue, self)]

    def get_filter(self):
        """The filter is the string, as a list"""
        return [self.sValue]


class IdNode(TermNode):
    """$foo variable identifier in the AST"""

    def __init__(self, sValue):
        """Initialise IdNode. sValue == name of variable"""
        super(IdNode, self).__init__([sValue])
        self.oValue = sValue

    def get_values(self):
        """IdNode has no values"""
        return None

    def get_filter(self):
        """IdNode has no filter"""
        return None


class FilterPartNode(OperatorNode):
    """A Filter = $X expression in the AST"""

    def __init__(self, sFilterName, aFilterValues, sVariableName):
        super(FilterPartNode, self).__init__([sFilterName, aFilterValues])
        self.sFilterName = sFilterName
        self.aFilterValues = aFilterValues
        self.sVariableName = sVariableName

    def get_name(self):
        """Variable name associated with the filter"""
        return self.sVariableName

    def get_description(self):
        """Get the description for the associated filter object"""
        return get_filter_type(self.sFilterName).description

    def get_values(self):
        """List of ValueObjects describing the filter and its associated
           values."""
        if self.sFilterName in ENTRY_FILTERS:
            aResults = \
                    [ValueObject(get_filter_type(self.sFilterName).description
                        + ' includes', self)]
        elif self.sFilterName in LIST_FILTERS:
            aResults = \
                    [ValueObject(get_filter_type(self.sFilterName).description
                        + ' in', self)]
        else:
            # We don't take any input for this filter, so there are no
            # values to return
            return [ValueObject(get_filter_type(self.sFilterName).description,
                self), ValueObject(None, self)]
        # Want a list within ValueObject for the GUI stuff to work
        # '' case for Entry boxes works as well
        aVals = get_filter_type(self.sFilterName).get_values()
        aResults.append(ValueObject(aVals, self))
        return aResults

    def get_invalid_values(self):
        """List of illegal values associated with this filter"""
        aRes = []
        if self.aFilterValues is None or self.sFilterName not in LIST_FILTERS:
            return None
        aCurVals = self.aFilterValues.get_values()
        oTemp = get_filter_type(self.sFilterName)([])  # Create Instance
        aValidVals = oTemp.get_values()
        if isinstance(aValidVals[0], list) and len(aCurVals) == \
                len(aValidVals):
            for aSubCurVals, aSubValidVals in zip(aCurVals, aValidVals):
                for oVal in aSubCurVals:
                    if oVal.oValue == ',':
                        continue
                    if oVal.oValue not in aSubValidVals:
                        aRes.append(oVal.oValue)
        else:
            for oVal in aCurVals:
                if oVal.oValue == ',':
                    continue
                if oVal.oValue not in aValidVals:
                    aRes.append(oVal.oValue)
        if len(aRes) > 0:
            return aRes
        else:
            return None

    def set_values(self, aVals):
        """Set values for this filter"""
        if self.aFilterValues is not None:
            raise RuntimeError("Filter values already set")
        if not aVals:
            # Skip empty values
            return
        elif self.sFilterName in FROM_FILTERS:
            sCountList = ",".join(aVals[0])
            sSetList = ",".join(aVals[1])
            sInternalFilter = self.sFilterName + '=' + sCountList + 'from' + \
                    sSetList
        else:
            sCommaList = ",".join(aVals)
            sInternalFilter = self.sFilterName + '=' + sCommaList
        oParser = FilterParser()
        oInternalAST = oParser.apply(sInternalFilter)
        # The filter we create is trivially of the FilterType = X, Y type
        # so this is safe, but potentially fragile in the future
        self.aFilterValues = oInternalAST.aChildren[0].aFilterValues
        # Update AST to reflect change
        self.aChildren[1] = self.aFilterValues

    def get_filter(self):
        """Get Filter object for this Filter"""
        if self.sFilterName in ENTRY_FILTERS or \
                self.sFilterName in LIST_FILTERS:
            if self.aFilterValues is None:
                return None
        cFilterType = get_filter_type(self.sFilterName)
        if self.aFilterValues:
            aValues = self.aFilterValues.get_filter()
            if self.sFilterName in ENTRY_FILTERS:
                # Filter takes a single string as input
                # by construction, this is aValues[0]
                oFilter = cFilterType(aValues[0])
            else:
                oFilter = cFilterType(aValues)
        else:
            # This Filter takes no argument
            oFilter = cFilterType()
        return oFilter

    def get_type(self):
        """Get allowed types for this filter"""
        return get_filter_type(self.sFilterName).types


class NotOpNode(OperatorNode):
    """AST node for NOT(X)"""
    def __init__(self, oSubExpression):
        super(NotOpNode, self).__init__([oSubExpression])
        self.oSubExpression = oSubExpression

    def get_invalid_values(self):
        """NOT(X)'s invalid values are the subfilter's invalid values"""
        return self.oSubExpression.get_invalid_values()

    def get_description(self):
        """NOT(X)'s description is the subfilter's description,
           if applicable"""
        if hasattr(self.oSubExpression, 'get_description'):
            return self.oSubExpression.get_description()
        return None

    def get_values(self):
        """NOT(X)'s values are the subfilter's values"""
        aResults = [ValueObject('NOT (', None)] + \
                 self.oSubExpression.get_values() +\
                 [ValueObject(')', None)]
        return aResults

    def get_filter(self):
        """Get the filter expression"""
        return FilterNot(self.oSubExpression.get_filter())

    def get_type(self):
        """Get the filter type (same as subfilter)"""
        return self.oSubExpression.get_type()


class BinOpNode(OperatorNode):
    """AST node for binary operations (AND, OR)"""
    def __init__(self, oLeft, oOp, oRight):
        super(BinOpNode, self).__init__([oLeft, oRight])
        self.oOp = oOp
        self.oLeft = oLeft
        self.oRight = oRight

    def get_invalid_values(self):
        """Get invalid values from both children"""
        aLeft = self.oLeft.get_invalid_values()
        aRight = self.oRight.get_invalid_values()
        if aLeft is None:
            return aRight
        elif aRight is None:
            return aLeft
        else:
            return aLeft + aRight

    def get_values(self):
        """Get values from both children"""
        aLeft = self.oLeft.get_values()
        aRight = self.oRight.get_values()
        if aLeft is None:
            return aRight
        elif aRight is None:
            return aLeft
        else:
            # Add the extra brackets so the display in the dialog
            # reflects the correct precedence
            aResults = [ValueObject('(', None)] + aLeft +\
                    [ValueObject(') ' + self.oOp + ' (', self)] +\
                    aRight + [ValueObject(')', None)]
            return aResults

    def get_filter(self):
        """Get the filter expression. Handle None children"""
        oLeftFilter = self.oLeft.get_filter()
        oRightFilter = self.oRight.get_filter()
        if oLeftFilter is None:
            return oRightFilter
        elif oRightFilter is None:
            return oLeftFilter
        if self.oOp == 'and':
            oFilter = FilterAndBox([oLeftFilter, oRightFilter])
        elif self.oOp == 'or':
            oFilter = FilterOrBox([oLeftFilter, oRightFilter])
        else:
            raise RuntimeError('Unknown operator in AST')
        return oFilter

    def get_type(self):
        """Get the type of the filter - intersection of the children's types"""
        aLeftTypes = self.oLeft.get_type()
        aRightTypes = self.oRight.get_type()
        if aRightTypes is None:
            return aLeftTypes
        if aLeftTypes is None:
            return aRightTypes
        aRes = []
        # Type must be the intersection of sub-filter types
        for sType in aLeftTypes:
            if sType in aRightTypes:
                aRes.append(sType)
        return aRes


class CommaNode(OperatorNode):
    """AST node for comma separator (Val1, Val2)"""
    def __init__(self, oLeft, oOp, oRight):
        super(CommaNode, self).__init__([oLeft, oRight])
        self.oOp = oOp
        self.oLeft = oLeft
        self.oRight = oRight

    def get_values(self):
        """Get values - union of children's values"""
        aResults = self.oLeft.get_values()
        aResults.append(ValueObject(',', self))
        aResults.extend(self.oRight.get_values())
        return aResults

    def get_filter(self):
        """Get filter expression"""
        aResults = self.oLeft.get_filter()
        aResults.extend(self.oRight.get_filter())
        return aResults

    def get_type(self):
        """Get type - children are values, so always None"""
        # Syntax ensures , only in value lists, which have no type
        return None


class WithNode(OperatorNode):
    """AST node for values of the form 'X with Y'"""
    def __init__(self, oLeft, oOp, oRight):
        super(WithNode, self).__init__([oLeft, oRight])
        self.oOp = oOp
        self.oLeft = oLeft
        self.oRight = oRight

    def get_values(self):
        """Get values"""
        return [ValueObject(self.oLeft.get_filter()[0] + ' ' + self.oOp +
            ' ' + self.oRight.get_filter()[0], self)]

    def get_filter(self):
        """Get filter expression"""
        return [(self.oLeft.get_filter()[0], self.oRight.get_filter()[0])]

    def get_type(self):
        """Get filter type - these are values, so always None"""
        # Syntax ensures with only in value lists, which have no type
        return None


class FromNode(OperatorNode):
    """AST node for values of the form 'X, Y from W, Z'"""
    def __init__(self, oLeft, oOp, oRight):
        super(FromNode, self).__init__([oLeft, oRight])
        self.oOp = oOp
        self.oLeft = oLeft
        self.oRight = oRight

    def get_values(self):
        """Get values"""
        return [self.oLeft.get_values(),
            self.oRight.get_values()]

    def get_filter(self):
        """Get filter expression"""
        return [self.oLeft.get_filter(), self.oRight.get_filter()]

    def get_type(self):
        """Get filter type - these are values, so always None"""
        # Syntax ensures with only in value lists, which have no type
        return None
