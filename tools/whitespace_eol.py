# whitespace_eol.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# Based on custom_raw.py from pylint, so the license is
# GPL v2 or later - see the COPYRIGHT file for deatils

"""Custom checker for pylint - warn about about whitespace at end of a line"""

# Add this pylintrc using load-plugins
# The path to this file needs to be in PYTHONPATH as pylint must be able
# to import this

from pylint.interfaces import IRawChecker
try:
    from pylint.checkers import BaseRawChecker as Base
except ImportError:
    from pylint.checkers import BaseChecker as Base


class WhitespaceEOLChecker(Base):
    """Check for whitespace at the end of a line."""

    __implements__ = IRawChecker

    name = 'whitespace eol'
    msgs = {'C9968': ('whitespace at the end of a line',
                      ('Line ends with whitespace, rather than immediately'
                       ' after the text')),
            }
    options = ()

    def process_module(self, aStream):
        """process a module."""
        if hasattr(aStream, 'file_stream'):
            aStream = aStream.file_stream
        for (iLineNo, sLine) in enumerate(aStream):
            sText = sLine[:-1]  # Ignore final newline
            if sText != sText.rstrip():
                # iLineNo starts at 0, so need to add 1
                self.add_message('C9968', line=(iLineNo + 1))

    def process_tokens(self, _aTokens):
        """Dummy method to make pylint happy"""
        pass


def register(oLinter):
    """required method to auto register this checker."""
    oLinter.register_checker(WhitespaceEOLChecker(oLinter))
