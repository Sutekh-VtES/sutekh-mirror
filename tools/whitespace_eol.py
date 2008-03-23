
"""Custom checker for pylint - warn about about whitespace at end of a line"""

# Copyright Neil Muller, 2008 <drnlmuller+sutekh@gmail.com>
# Based on custom_raw.py from pylint, so the license is
# GPL v2 or later (see COPYRIGHT file for sutekh)

# Add this pylintrc using load-plugins
# The path to this file needs to be in PYTHONPATH as pylint must be able
# to import this

from pylint.interfaces import IRawChecker
from pylint.checkers import BaseChecker

class WhitespaceEOLChecker(BaseChecker):
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
        for (iLineNo, sLine) in enumerate(aStream):
            sText = sLine[:-1] # Ignore final newline
            if sText != sText.rstrip():
                # iLineNo starts at 0, so need to add 1
                self.add_message('C9968', line=(iLineNo + 1))


def register(oLinter):
    """required method to auto register this checker."""
    oLinter.register_checker(WhitespaceEOLChecker(oLinter))

