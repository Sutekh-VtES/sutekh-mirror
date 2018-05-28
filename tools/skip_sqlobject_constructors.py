# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# Based on custom.py from pylint, so the license is
# GPL v2 or later - see the COPYRIGHT file for details

"""Custom checker for pylint - Skip checking parameters to SQLObject class
   constructor calls."""

# Add this pylintrc using load-plugins
# The path to this file needs to be in PYTHONPATH as pylint must be able
# to import this

from compat_helper import Base, IAstroidChecker, astroid, compat_register
from pylint.checkers.utils import safe_infer


def _get_child_nodes(oNode):
    """Get the child nodes"""
    # Work around differing pylint versions
    if hasattr(oNode, 'getChildNodes'):
        return oNode.getChildNodes()
    elif hasattr(oNode, 'get_children'):
        return oNode.get_children()
    else:
        return []


class MySQLObjectConstructorChecker(Base):

    """Check for SQLObject constructor syntax

       This is a bit clumsy, as it does a fair amount of AST walking on
       all the classes encountered, and monkey-patches the AST pylint
       uses."""

    __implements__ = IAstroidChecker

    name = 'skip_sqlobject_constructors'
    # Since we just add addtional info to the AST, we have no messages
    options = ()
    # We're going to mess with the AST, so we need to run first
    priority = 0
    # We need to have a msgid or reportid, otherwise newer pylints don't
    # add this to the enable checker list
    msgs = {'C6790': ('SQObject constructor checker dummy message',
                      'sqlobject_dummy',
                      'Dummy message to prevent pylint optimising us out')
           }

    def __init__(self, oLinter=None):
        """Constructor"""
        super(MySQLObjectConstructorChecker, self).__init__(oLinter)

    def process_tokens(self, _aTokens):
        """Dummy method to make pylint happy"""
        pass

    def visit_call(self, oNode):
        """Handle visiting function / constructor calls"""
        oCaller = safe_infer(oNode.func)
        if isinstance(oCaller, astroid.ClassDef):
            try:
                oNewCall = oCaller.local_attr('__new__')[-1]
                if not hasattr(oNewCall, 'args'):
                    return
                if oNewCall.args.args:
                    names = [x.name for x in oNewCall.args.args]
                    if ('this_bases' in names and
                        'name' in names and 'd' in names):
                        # SQLObject constructor
                        # Monkey patch this to look like something we
                        # don't know the arguments for, so we skip
                        # the incorrect check in pylint's main
                        # visit_call
                        oNewCall.args.args = None
            except astroid.exceptions.NotFoundError:
                # Not an SQLObject class, so we ignore it
                pass

# Test data - uncomment to test
#
#from sqlobject import SQLObject, IntCol
#
#class ITest(SQLObject):
#    """Test Class 1"""
#    size = IntCol
#
#class IMissed(Interface):
#    """Test Class 2 - should not be implemented"""
#    pass
#
#class TestAdapter(object):
#    """Adapter for ITest"""
#    advise(instancesProvide=[ITest], asAdapterForTypes=[basestring])
#
#    def __new__(cls, sName):
#        return sName


def register(oLinter):
    """required method to auto register this checker"""
    compat_register(MySQLObjectConstructorChecker, oLinter)
