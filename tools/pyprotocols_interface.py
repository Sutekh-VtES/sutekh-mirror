# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# Based on custom.py from pylint, so the license is
# GPL v2 or later - see the COPYRIGHT file for details

"""Custom checker for pylint - Detect pyprotocols "advises" to mark interfaces
   as implemented"""

# Add this pylintrc using load-plugins
# The path to this file needs to be in PYTHONPATH as pylint must be able
# to import this

from compat_helper import Base, IAstroidChecker, astroid, compat_register


def _get_child_nodes(oNode):
    """Get the child nodes"""
    # Work around differing pylint versions
    if hasattr(oNode, 'getChildNodes'):
        return oNode.getChildNodes()
    elif hasattr(oNode, 'get_children'):
        return oNode.get_children()
    else:
        return []


# pylint: disable=F0220
# F0220: Our compat import dance confuses pylint's interface checker
class MyPyProtocolsChecker(Base):

    """Check for PyProtocols advises syntax

       This is a bit clumsy, as it does a fair amount of AST walking on
       all the classes encountered, and monkey-patches the AST pylint
       uses."""

    __implements__ = IAstroidChecker

    name = 'custom_pyprotocols_interface'
    # Since we just add addtional info to the AST, we have no messages
    options = ()
    # We're going to mess with the AST, so we need to run first
    priority = -1
    # We need to have a msgid or reportid, otherwise newer pylints don't
    # add this to the enable checker list
    msgs = {'C6789': ('PyProtocols Interface checker dummy message',
                      'pyprotocols_dummy',
                      'Dummy message to prevent pylint optimising us out')
           }

    def __init__(self, oLinter=None):
        """Constructor"""
        super(MyPyProtocolsChecker, self).__init__(oLinter)
        self._dInterfaces = {}

    def open(self):
        """initialize visit variables"""
        self._dInterfaces = {}

    def process_tokens(self, _aTokens):
        """Dummy method to make pylint happy"""
        pass

    def find_poss_advise_call(self, oNode, aClasses):
        """Check to see if we have a 'advise' function call"""
        # Ugly check here
        for oSubNode in _get_child_nodes(oNode):
            if isinstance(oSubNode, astroid.CallFunc):
                if self.check_poss_advise_call(oSubNode, aClasses):
                    return True
            elif not isinstance(oSubNode, astroid.Discard):
                continue
            for oPossAdvise in _get_child_nodes(oSubNode):
                if not isinstance(oPossAdvise, astroid.CallFunc):
                    continue
                if self.check_poss_advise_call(oPossAdvise, aClasses):
                    return True
        return False

    def check_poss_advise_call(self, oNode, aClasses):
        """Check if a promising looking call matches pyprotocols"""
        bNamedAdvise = False
        bProvides = False
        for oInfoNode in _get_child_nodes(oNode):
            if isinstance(oInfoNode, astroid.Name) and \
                    oInfoNode.name == 'advise':
                bNamedAdvise = True
            elif isinstance(oInfoNode, astroid.Keyword):
                sName = ''
                if hasattr(oInfoNode, 'name'):
                    sName = oInfoNode.name
                elif hasattr(oInfoNode, 'arg'):
                    sName = oInfoNode.arg
                if sName == 'instancesProvide':
                    bProvides = True
                    if bNamedAdvise:
                        if not self.extract_classes(oInfoNode, aClasses):
                            bProvides = False
        return bNamedAdvise and bProvides

    def extract_classes(self, oNode, aClasses):
        """Extract the inferface provided from the keyword node"""
        for oSubNode in _get_child_nodes(oNode):
            if not isinstance(oSubNode, astroid.List):
                return False
            for oName in _get_child_nodes(oSubNode):
                if oName.name in self._dInterfaces:
                    aClasses.append(self._dInterfaces[oName.name])
        return True

    def visit_class(self, oNode):
        """Check class"""
        if oNode.type == 'interface' and oNode.name != 'Interface':
            # Cache interfaces we encounter
            self._dInterfaces[oNode.name] = oNode
        aClasses = []
        for oSubNode in _get_child_nodes(oNode):
            if oSubNode.statement():
                if self.find_poss_advise_call(oSubNode, aClasses):
                    #print oNode, 'Interface implementation detected', aClasses
                    # MONKEY-PATCH alert
                    # pylint expects to read the interfaces implemented
                    # via this function. We don't construct the data
                    # the default function requires, since that involves
                    # much messing with the AST, so we just monkey patch.
                    # Given that the logilab.astng moknkey patches compiler.ast
                    # extensively, this isn't that bad an option
                    # pylint: disable=C0322
                    # C0322: pylint get's this wrong
                    oNode.interfaces = lambda herited=True, \
                            handler_func=None: aClasses
                    #print oNode.interfaces()

# Test data - uncomment to test
#
#from protocols import advise, Interface
#
#class ITest(Interface):
#    """Test Class 1"""
#    pass
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
    compat_register(MyPyProtocolsChecker, oLinter)
