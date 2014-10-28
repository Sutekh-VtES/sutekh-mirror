# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# Based on custom.py from pylint, so the license is
# GPL v2 or later - see the COPYRIGHT file for deatils

"""Custom checker for pylint - warn about about 'in Dict.keys()' usage"""

# Add this pylintrc using load-plugins
# The path to this file needs to be in PYTHONPATH as pylint must be able
# to import this

from compat_helper import IAstroidChecker, Base, astroid, compat_register


# pylint: disable=R0904, F0220
# R0904: Handling three cases, so we exceed the 20 method pylint limit
# F0220: Our compat import dance confuses pylint's interface checker
class MyDictKeyChecker(Base):
    """Check for "for a in Dict.keys()" usage"""

    __implements__ = IAstroidChecker

    name = 'custom_dict_keys'
    msgs = {'W9967': ('Used x in Dict.keys()', 'x_in_dict',
                      ('Used when "x in Dict.keys()" is used rather than'
                       ' "x in Dict"')),
           }
    options = ()

    def process_tokens(self, _aTokens):
        """Dummy method to make pylint happy"""
        pass

    def open(self):
        """Dummy function."""
        pass

    def __internal_test(self, oNode):
        """Grunt work of the test"""
        if not hasattr(oNode, 'list'):
            # Later pylint is different. Bother
            oForObject = list(oNode.get_children())[1]  # part we want
            if type(oForObject) is astroid.CallFunc:
                # Check if name is keys
                oChild = list(oForObject.get_children())[0]
                if hasattr(oChild, 'attrname') and oChild.attrname == 'keys':
                    # Should check oChild to see if it's a dict?
                    self.add_message('W9967', line=oNode.lineno)
        elif hasattr(oNode.list, 'node') and \
                hasattr(oNode.list.node, 'attrname') and \
                oNode.list.node.attrname == 'keys':
            self.add_message('W9967', line=oNode.lineno)

    def visit_for(self, oNode):
        """Check for loops"""
        self.__internal_test(oNode)

    def visit_listcompfor(self, oNode):
        """Check [x for x in d] list comprehensions"""
        self.__internal_test(oNode)

    def visit_genexpfor(self, oNode):
        """Check (x for x in d) generator expressions"""
        self.__internal_test(oNode)

    def visit_listcomp(self, oNode):
        """Check [x for x in d] list comprehensions"""
        if hasattr(oNode, 'get_children'):
            oListNode = list(oNode.get_children())[1]
            self.__internal_test(oListNode)

    def visit_genexp(self, oNode):
        """Check (x for x in d) generator expressions"""
        if hasattr(oNode, 'get_children'):
            oListNode = list(oNode.get_children())[1]
            self.__internal_test(oListNode)

    # Uncomment for testing
    #def __dummy(self, dDict):
    #    """Dummy method used for testing"""
    #    for oYY in dDict.keys():
    #        print oYY
    #    print [oX for oX in self.msgs.keys()]
    #    for oYY in ['a', 'b', 'c']:
    #        print oYY


def register(oLinter):
    """required method to auto register this checker"""
    compat_register(MyDictKeyChecker, oLinter)
