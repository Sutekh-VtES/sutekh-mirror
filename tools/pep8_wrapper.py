# pep8_wrapper.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2010 Neil Muller <drnlmuller+sutekh@gmail.com>
# Based on custom_raw.py from pylint, so the license is
# GPL v2 or later - see the COPYRIGHT file for details
# This is tightly tied to pep8, Copyright (C) 2006 Johann C. Rocholl
# pep8 uses the expat style license (see pep8 package for details)
# so there's no license conflict

"""Custom checker for pylint - uses pep8 to check for some of the things
   pylint misses"""

# Add this pylintrc using load-plugins
# The path to this file needs to be in PYTHONPATH as pylint must be able
# to import this

from pylint.interfaces import IRawChecker
from pylint.checkers import BaseChecker
import pep8


class DummyOptions(object):
    """Mockup object so we can use pep8 without having it stomp over pylint's
       argument passing"""

    # pylint: disable-msg=C0103, R0902
    # Need these names and attributes to monkey-patch pep8
    def __init__(self):
        self.counters = {}
        self.messages = {}
        self.select = []
        self.ignore = []
        self.verbose = 0
        self.quiet = 0
        self.repeat = True
        self.testsuite = False
        self.doctest = False
        self.show_source = False
        self.show_pep8 = False
        self.physical_checks = []
        self.logical_checks = []

    def fix_checks(self):
        """Setup the check list correctly, after monkey-patching options"""
        self.physical_checks = pep8.find_checks('physical_line')
        self.logical_checks = pep8.find_checks('logical_line')


class PEP8Checker(BaseChecker):
    """Run pep8 and report a subset of it's issues."""

    __implements__ = IRawChecker

    name = 'pep8 checker'
    # We construct msgs from this later - this allows us to maintain the
    # mapping between pep8 and pylint easily
    mapping = {
            # pylint requires that all messages start with the same first 2
            # digits, so our numbers aren't related to the pep8 numbers
            'C5701': ("Whitespace before ',',':' or ';'", ['E203']),
            'C5702': ('Extra whitespace around operator',
                ['E221', 'E222', 'E223', 'E224']),
            'C5703': ('Missing whitespace around operator', ['E225']),
            'C5704': ('Too few blank lines', ['E301', 'E302']),
            'C5705': ('Too many blank lines', ['E303']),
            'C5706': ('Blank line after decorator', ['E304']),
            'C5707': ('Too few spaces before inline comment', ['E261']),
            'C5708': ('Too many spaces after # in inline comment', ['E262']),
            'C5709': ("Missing whitespace after ',',':' or ';'", ['E231']),
            'C5710': ("Whitespace after '{', '[' or '('", ['E201']),
            'C5711': ("Whitespace before '}', ']' or ')'", ['E202']),
            'C5712': ("Blank line at end of file", ['W391']),
            'C5713': ("No newline at end of file", ['W292']),
            'C5714': ("Whitespace before '{', '[' or '('", ['E211']),
            'C5715': ("Spaces around keyword / parameter =", ['E251']),
            }
    options = ()

    def __init__(self, oLinter):
        # Constuct the pylint msgs dict from mapping
        # pylint: disable-msg=C0103
        # msgs is the pylint required name
        self.msgs = {}
        for sPylint, tData in self.mapping.iteritems():
            sMsg = 'pep8 %s: %s : (position %%d)' % (','.join(tData[1]),
                    tData[0])
            self.msgs[sPylint] = (sMsg, sMsg)
        super(PEP8Checker, self).__init__(oLinter)

    def _transform_error(self, iLineNo, iOffset, sMessage, _oCheck):
        """Monkey patch pep8's message handling.

           This allows us to get the line number as well as the error code"""
        # Split out line number and message text
        sCode = sMessage[:4]
        # Error transformation
        for sPylint, tData in self.mapping.iteritems():
            aMapping = tData[1]
            if sCode in aMapping:
                if iOffset:
                    self.add_message(sPylint, line=iLineNo, args=iOffset)
                else:
                    self.add_message(sPylint, line=iLineNo, args=1)

    def process_module(self, aStream):
        """process a module."""
        pep8.options = DummyOptions()
        pep8.options.fix_checks()
        oChecker = pep8.Checker(None)
        oChecker.lines = list(aStream)
        oChecker.report_error = self._transform_error
        oChecker.check_all()


def register(oLinter):
    """required method to auto register this checker."""
    oLinter.register_checker(PEP8Checker(oLinter))
