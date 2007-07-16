# FilterGrammer.py
# Copyright Neil Muller <drnlmuller+sutekh@gmail.com>, 2007
# GPL - see COPYING for details

import ply.lex as lex
import ply.yacc as yacc
from sutekh.Filters import MultiCardTypeFilter, MultiClanFilter, \
        MultiDisciplineFilter, MultiGroupFilter, MultiCapacityFilter,\
        MultiCostFilter, MultiLifeFilter, MultiCreedFilter, MultiVirtueFilter,\
        CardTextFilter, CardNameFilter, MultiSectFilter, MultiTitleFilter,\
        FilterAndBox, FilterOrBox
from sutekh.SutekhObjects import Clan, Discipline, CardType, Title,\
                                 Creed, Virtue, Sect

# FIXME: The intention is to push this into the Individual Filter Objects

dFilterParts = {
        "CardType" : [MultiCardTypeFilter,"Card Type"],
        "Clan" : [MultiClanFilter,"Clan"],
        "Discipline" : [MultiDisciplineFilter,"Discipline"],
        "Group" : [MultiGroupFilter,"Group"],
        "Capacity" : [MultiCapacityFilter,"Capacity"],
        "Cost" : [MultiCostFilter,"Cost"],
        "Life" : [MultiLifeFilter,"Life"],
        "Creed" : [MultiCreedFilter,"Creed"],
        "Virtue" : [MultiVirtueFilter,"Virtue"],
        "CardText" : [CardTextFilter,"Card Text"],
        "CardName" : [CardNameFilter,"Card Name"],
        "Sect" : [MultiSectFilter,"Sect"],
        "Title" : [MultiTitleFilter,"Title"],
        }

# This should be elsewhere

def getValues(sFilterType):
    """Return a list of values to fill the selection dialog, or
       None if the input should be a text string"""
    if sFilterType == "CardText" or sFilterType == "CardName":
        return None
    elif sFilterType == "Clan":
        return [x.name for x in Clan.select().orderBy('name')]
    elif sFilterType == "Discipline":
        return [x.fullname for x in Discipline.select().orderBy('name')]
    elif sFilterType == "Group":
        return range(1,6)
    elif sFilterType == "Capacity":
        return range(1,12)
    elif sFilterType == "Cost":
        return range(0,7)+['X']
    elif sFilterType == "CostType":
        return ["blood","pool","conviction"]
    elif sFilterType == "Life":
        return range(1,8)
    elif sFilterType == "Creed":
        return [x.name for x in Creed.select().orderBy('name')]
    elif sFilterType == "Virtue":
        return [x.fullname for x in Virtue.select().orderBy('name')]
    elif sFilterType == "Sect":
        return [x.name for x in Sect.select().orderBy('name')]
    elif sFilterType == "Title":
        return [x.name for x in Title.select().orderBy('name')]
    elif sFilterType == "CardType":
        return [x.name for x in CardType.select().orderBy('name')]
    else:
        raise RuntimeError("Unknown Filter Type %s" % sFilterType)



# Grammer:
# OPS == {'&&', '||'}
# SubClause == { Filtertype [Value for this Filter instance] }
# Clause == SubClause [OP SubClause] ...
# Filter == Clause | ( Clause ) OP ( Clause )
# ()'s indicate precedence, as conventional
# AND and OR have same precedence, so 
# a AND b AND c OR d AND e is evaluted left to right:
# ( (a AND b AND c) OR d ) AND e

# We define an object for the lex parser

# This parser is used to split up the Filter Definitions
# It is also used by the grammar to create the final filter

class ParseFilterDefinitions(object):
    tokens = (
            'FILTERTYPE',
            'ID',
            'INTEGER',
            'STRING',
            'OR',
            'AND',
            'COMMA',
            'IN',
            'LPAREN',
            'RPAREN',
            'VARIABLE'
            )

    t_AND=r'\&\&'
    t_OR=r'\|\|'
    t_STRING=r'\".*?\"'
    t_INTEGER=r'\d+'
    t_COMMA=r','
    t_IN=r'='
    t_LPAREN=r'\('
    t_RPAREN=r'\)'

    # Ignore whitespace and returns
    t_ignore=' \t\n'

    # Simplistic error handler, to stop warnings
    # FIXME: Should raise Value Error - will do so when everything works 
    def t_error(self,t):
        print "Illegal Character '%s'" % t.value[0]
        t.lexer.skip(1)

    def t_ID(self,t):
        r'[A-Za-z$]+'
        if t.value in dFilterParts.keys():
            t.type='FILTERTYPE'
        elif t.value.lower() == 'and':
            t.type='AND'
        elif t.value.lower() == 'or':
            t.type='OR'
        elif t.value.lower() == 'in':
            t.type='IN'
        elif t.value[0] == '$':
            t.type='VARIABLE'
        return t

    # Ply docs say don't do this in __init__, so we don't
    def build(self,**kwargs):
        self.lexer=lex.lex(object=self,**kwargs)

    def apply(self,data):
        self.lexer.input(data)
        aResults=[]
        while 1:
            tok=self.lexer.token()
            if not tok: return aResults
            aResults.append(tok)

# Define a yacc parser to produce the abstract syntax tree

class FilterYaccParser(object):
    tokens=ParseFilterDefinitions.tokens

    # COMMA's have higher precedence than AND + OR 
    # This shut's up most shift/reduce warnings
    precedence=(
            ('left','AND','OR'),
            ('left','IN'),
            ('left','COMMA'),
    )

    def p_filter(self,p):
        """filter : filterpart
                  | fempty
        """
        p[0] = FilterNode(p[1])

    def p_filterpart_brackets(self,p):
        """filterpart : LPAREN filterpart RPAREN"""
        p[0]=p[2]

    def p_filterpart_AND(self,p):
        """filterpart : filterpart AND filterpart"""
        p[0] = BinOpNode(p[1],'and',p[3])

    def p_filterpart_OR(self,p):
        """filterpart : filterpart OR filterpart"""
        p[0] = BinOpNode(p[1],'or',p[3])

    def p_filterpart_filtertype(self,p):
        """filterpart : FILTERTYPE IN expression"""
        p[0]=FilterPartNode(p[1],p[3])

    def p_filterpart_var(self,p):
        """filterpart : FILTERTYPE IN VARIABLE"""
        p[0]=FilterPartNode(p[1],None)

    def p_expression_comma(self,p):
        """expression : expression COMMA expression"""
        p[0]=CommaNode(p[1],p[2],p[3])

    def p_expression_string(self,p):
        """expression : STRING"""
        # Insert into a list, so commas work
        p[0]=StringNode(p[1])

    def p_expression_integer(self,p):
        """expression : INTEGER"""
        p[0]=IntegerNode(int(p[1]))

    def p_expression_id(self,p):
        """expression : ID"""
        # Shouldn't actually trigger this rule with a legal filter string
        p[0]=IdNode(p[1])

    def p_fempty(self,p):
        """fempty :"""
        p[0]=None

    def p_error(self,p):
        print "Bad Syntax found by FinalFilterParser: ",p

# Wrapper objects around the parser

class FilterParser(object):
    def __init__(self):
        self.oLexer = ParseFilterDefinitions()
        self.oLexer.build()
        # yacc needs an initialised lexer
        self.oParser = yacc.yacc(module=FilterYaccParser())

    def apply(self,str):
        oAST=self.oParser.parse(str)
        return oAST

# AST object (formulation inspired by Simon Cross's example, and notes 
# from the ply documentation)

class AstBaseNode(object):
    def __init__(self,children):
        self.children = children

    def __str__(self):
        sAttrs = '('+",".join([ str(value) for key,value \
                in self.__dict__.items() if not key.startswith("_") and \
                key != "children" and value not in self.children])+")"
        s=self.__class__.__name__ + sAttrs
        for child in self.children:
            s+="\n" + "\n".join(["\t" + x for x in str(child).split("\n")])
        return s

    def getValues(self):
        pass

    def getFilter(self):
        pass

class FilterNode(AstBaseNode):
    def __init__(self,expression):
        super(FilterNode,self).__init__([expression])
        self.expression = expression

    def getValues(self):
        return self.expression.getValues()

    def getFilter(self):
        return self.expression.getFilter()

class OperatorNode(AstBaseNode):
    pass

class TermNode(AstBaseNode):
    pass

class StringNode(TermNode):
    def __init__(self,value):
        super(StringNode,self).__init__([value])
        self.value=value

    def getValues(self):
        return [self.value]

    def getFilter(self):
        # Strip quotes off strings for the filter
        return [self.value[1:-1]]

class IntegerNode(TermNode):
    def __init__(self,value):
        super(IntegerNode,self).__init__([value])
        self.value=value

    def getValues(self):
        return [self.value]

    def getFilter(self):
        return [self.value]

class IdNode(TermNode):
    def __init__(self,value):
        super(IdNode,self).__init__([value])
        self.value=value

    def getValues(self):
        return None

    def getFilter(self):
        return None

class FilterPartNode(OperatorNode):
    def __init__(self,filtertype,filtervalues):
        super(FilterPartNode,self).__init__([filtertype,filtervalues])
        self.filtertype=filtertype
        self.filtervalues=filtervalues

    def getValues(self):
        aRes=[self.filtertype+' = ']
        if self.filtervalues is None:
            aVals=getValues(self.filtertype)
            # Want a list within the list for the GUI stuff to work
            # None case for Entry boxes works as well
            aRes.append(aVals)
        else:
            aRes.extend(self.filtervalues.getValues())
        return aRes

    def getFilter(self):
        if self.filtervalues is None:
            return None
        aValues=self.filtervalues.getFilter()
        FilterType=dFilterParts[self.filtertype][0]
        if self.filtertype in ['CardText','CardName']:
            # FIXME: Don't quite like special casing this here - MultiCardText?
            # aValues[0] is a fragile assumption - join?
            oFilter=FilterType(aValues[0])
        else:
            oFilter=FilterType(aValues)
        return oFilter

class BinOpNode(OperatorNode):
    def __init__(self,left,op,right):
        super(BinOpNode,self).__init__([left,right])
        self.op=op
        self.left=left
        self.right=right

    def getValues(self):
        # Add the extra brackets so the processing in the dialog
        # doesn't change precedence
        aRes=['(']
        aRes.extend(self.left.getValues())
        aRes.append(self.op)
        aRes.extend(self.right.getValues())
        aRes.append(')')
        return aRes

    def getFilter(self):
        oLeftFilter=self.left.getFilter()
        oRightFilter=self.right.getFilter()
        if oLeftFilter is None:
            return oRightFilter
        elif oRightFilter is None:
            return oLeftFilter
        if self.op == 'and':
            oFilter=FilterAndBox([oLeftFilter,oRightFilter])
        elif self.op == 'or':
            oFilter=FilterOrBox([oLeftFilter,oRightFilter])
        else:
            raise RuntimeError('Unknown operator in AST')
        return oFilter

class CommaNode(OperatorNode):
    def __init__(self,left,op,right):
        super(CommaNode,self).__init__([left,right])
        self.op=op
        self.left=left
        self.right=right

    def getValues(self):
        aRes=self.left.getValues()
        aRes.append(',')
        aRes.extend(self.right.getValues())
        return aRes

    def getFilter(self):
        aRes=self.left.getFilter()
        aRes.extend(self.right.getFilter())
        return aRes
