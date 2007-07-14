# FilterGrammer.py
# Copyright Neil Muller <drnlmuller+sutekh@gmail.com>, 2007
# GPL - see COPYING for details

import ply.lex as lex
import ply.yacc as yacc
import gtk
from sutekh.gui.ScrolledList import ScrolledList
from sutekh.Filters import MultiCardTypeFilter, MultiClanFilter, \
        MultiDisciplineFilter, MultiGroupFilter, MultiCapacityFilter,\
        MultiCostFilter, MultiLifeFilter, MultiCreedFilter, MultiVirtueFilter,\
        CardTextFilter, CardNameFilter, MultiSectFilter, MultiTitleFilter,\
        FilterAndBox, FilterOrBox
from sutekh.SutekhObjects import Clan, Discipline, CardType, Title,\
                                 Creed, Virtue, Sect

# FIXME: The intention is to push this into the Individual Filter Objects,
# but this dict is currently to keep this plugin self-contained

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
            'EQUALS',
            'LPAREN',
            'RPAREN',
            )

    t_AND=r'\&\&'
    t_OR=r'\|\|'
    t_STRING=r'\".*?\"'
    t_INTEGER=r'\d+'
    t_COMMA=r','
    t_EQUALS=r'='
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
        r'[A-Za-z]+'
        if t.value in dFilterParts.keys():
            t.type='FILTERTYPE'
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

# Define a yacc parser to produce the widget sets for a filter definition

class DialogFilterYaccParser(object):
    tokens=ParseFilterDefinitions.tokens

    # COMMA's have higher precedence than AND + OR 
    # This shut's up most shift/reduce warnings
    # EQUALS has quite a high precedence, to ensure we can
    # handle FilterType = Value cases properly
    precedence=(
            ('left','AND','OR'),
            ('left','EQUALS'),
            ('left','COMMA'),
    )

    def p_filter(self,p):
        """filter : filterpart
                  | empty
        """
        p[0] = p[1]

    def p_filterpart_AND(self,p):
        """filterpart : filterpart AND filterpart"""
        p[0]=[]
        for x in p[1]:
            p[0].append(x)
        oWidget=gtk.Label()
        oWidget.set_markup('<b>AND</b>')
        p[0].append( (oWidget,'&&') )
        for x in p[3]:
            p[0].append(x)

    def p_filterpart_OR(self,p):
        """filterpart : filterpart OR filterpart"""
        p[0]=[]
        for x in p[1]:
            p[0].append(x)
        oWidget=gtk.Label()
        oWidget.set_markup('<b>AND</b>')
        p[0].append( (oWidget,'||') )
        for x in p[3]:
            p[0].append(x)

    def p_filterpart_brackets(self,p):
        """filterpart : LPAREN filterpart RPAREN"""
        oLeft=gtk.Label('(')
        oRight=gtk.Label(')')
        p[0]=[(oLeft,'(')]
        for x in p[2]:
            p[0].append(x)
        p[0].append((oRight,')'))

    def p_filterpart_filtertype_equals(self,p):
        """filterpart : FILTERTYPE EQUALS expression"""
        oFilterType=gtk.Label(p[1])
        oEqualsLabel=gtk.Label(' is ')
        p[0]=[(oFilterType,p[1]),(oEqualsLabel,'=')]
        for x in p[3]:
            p[0].append(x)

    def p_filterpart_filtertype(self,p):
        """filterpart : FILTERTYPE"""
        aVals=getValues(p[1])
        if aVals is None:
            oWidget=gtk.Entry(100)
            oWidget.set_text(p[1])
            oWidget.set_width_chars(30)
        else:
            oWidget=ScrolledList(p[1])
            oWidget.set_size_request(160,420)
            list=oWidget.get_list()
            list.clear()
            for sEntry in aVals:
                iter=list.append(None)
                list.set(iter,0,sEntry)
        p[0]=[(oWidget,p[1])]

    def p_expression_comma(self,p):
        """expression : expression COMMA expression"""
        p[0]=[]
        for x in p[1]:
            p[0].append(x)
        oWidget=gtk.Label(' or ')
        p[0].append((oWidget,','))
        for x in p[3]:
            p[0].append(x)

    def p_expression_string(self,p):
        """expression : STRING"""
        oWidget=gtk.Label()
        oWidget.set_markup('<b>'+p[1]+'</b>')
        p[0]=[(oWidget,p[1])]

    def p_expression_integer(self,p):
        """expression : INTEGER"""
        oWidget=gtk.Label()
        oWidget.set_markup('<b>'+p[1]+'</b>')
        p[0]=[(oWidget,p[1])]

    def p_expression_id(self,p):
        """expression : ID"""
        # Shouldn't actually trigger this rule with a legal filter string
        p[0]=p[1]

    def p_empty(self,p):
        """empty :"""
        p[0]=None

    def p_error(self,p):
        print "Bad Syntax found by DialogFilterParser: ",p

# Define a yacc parser to produce the final filter

class FinalFilterYaccParser(object):
    tokens=ParseFilterDefinitions.tokens

    # COMMA's have higher precedence than AND + OR 
    # This shut's up most shift/reduce warnings
    precedence=(
            ('left','AND','OR'),
            ('left','COMMA'),
    )

    def p_ffilter(self,p):
        """ffilter : ffilterpart
                  | fempty
        """
        p[0] = p[1]

    def p_ffilterpart_AND(self,p):
        """ffilterpart : ffilterpart AND ffilterpart"""
        p[0] = FilterAndBox((p[1],p[3]))

    def p_ffilterpart_OR(self,p):
        """ffilterpart : ffilterpart OR ffilterpart"""
        p[0] = FilterOrBox((p[1],p[3]))

    def p_ffilterpart_brackets(self,p):
        """ffilterpart : LPAREN ffilterpart RPAREN"""
        p[0]=p[2]

    def p_ffilterpart_filtertype(self,p):
        """ffilterpart : FILTERTYPE EQUALS fexpression"""
        if p[1] in ['CardText','CardName']:
            Filter=dFilterParts[p[1]][0](p[3][0])
        else:
            Filter=dFilterParts[p[1]][0](p[3])
        p[0]=Filter

    def p_fexpression_comma(self,p):
        """fexpression : fexpression COMMA fexpression"""
        p[0]=[]
        for x in p[1]:
            p[0].append(x)
        for x in p[3]:
            p[0].append(x)

    def p_fexpression_string(self,p):
        """fexpression : STRING"""
        # Insert into a list, so commas work
        # Strip the leading and trailing quotes
        p[0]=[p[1][1:-1]]

    def p_fexpression_integer(self,p):
        """fexpression : INTEGER"""
        p[0]=[int(p[1])]

    def p_fexpression_id(self,p):
        """fexpression : ID"""
        # Shouldn't actually trigger this rule with a legal filter string
        p[0]=p[1]

    def p_fempty(self,p):
        """fempty :"""
        p[0]=None

    def p_error(self,p):
        print "Bad Syntax found by FinalFilterParser: ",p

# Wrapper objects around the parsers 

class DialogFilterParser(object):
    def __init__(self):
        self.oLexer = ParseFilterDefinitions()
        self.oLexer.build()
        # yacc needs an initialised lexer
        self.oParser = yacc.yacc(module=DialogFilterYaccParser())

    def apply(self,str):
        return self.oParser.parse(str)

class FinalFilterParser(object):
    def __init__(self):
        self.oLexer = ParseFilterDefinitions()
        self.oLexer.build()
        # yacc needs an initialised lexer
        self.oParser = yacc.yacc(module=FinalFilterYaccParser())

    def apply(self,str):
        return self.oParser.parse(str)

