# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2014 Neil Muller <drnlmuller+sutekh@gmail.com>
# Based on custom_raw.py from pylint, so the license is
# GPL v2 or later - see the COPYRIGHT file for details

"""Dummy message provider to stop older pylint versions complaining
   about disabling / re-enabling codes for newer versions."""

# Add this pylintrc using load-plugins
# The path to this file needs to be in PYTHONPATH as pylint must be able
# to import this

from pylint.interfaces import IRawChecker
from pylint.exceptions import InvalidMessageError
from compat_helper import Base, compat_register

# This is a hack, but we want to be able to disable messages that are not
# defined in older pylint versions without polluting the output with
# 'bad-option' errors everywhere, and we don't want to disable bad-option,
# since that could silence legimate errors. Thus we stuff dummy versions of the
# relevant newer options into pylint's message dictionary so they're treated as
# existing without doing anything.


MESSAGES = {
    # tuple unpacking checks added in pylint 1.1.0
    'W0632': ('Possible unbalanced tuple unpacking',
              'unbalanced-tuple-unpacking',
              'Dummy message to silence W0632 disabling errors'),
    'W0640': ('Cell variable defined in loop',
              'cell-var-from-loop',
              'Dummy message to silence W0604 disabling errors'),
}


class DummyMessageHolder(Base):
    """Check for whitespace at the end of a line."""

    __implements__ = IRawChecker

    name = 'whitespace eol'
    msgs = {}
    options = ()

    def process_module(self, aStream):
        """Dummy method."""
        pass

    def process_tokens(self, _aTokens):
        """Dummy method."""
        pass


def register(oLinter):
    """required method to auto register this checker."""
    for sMsgID, tData in MESSAGES.items():
        try:
            # We try add each message to the pylint message dictionary,
            # ignoring those that fail
            DummyMessageHolder.msgs = {sMsgID: tData}
            compat_register(DummyMessageHolder, oLinter)
        except (AssertionError, InvalidMessageError):
            # This message is already defined, so ignore it
            pass
