# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2014 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL v2 or later - see the COPYRIGHT file for deatils

"""Functions to help maintain compatability across various pylint versions."""

# We cover all the import dancing here, so it's in a unified place

# pylint: disable=W0611
# We import this so we can ignore the differences in modules using
# this. They are unused here
try:
    # pylint: disable=E0611, F0401
    # import failures here are non-fatal
    from pylint.checkers import BaseRawChecker as Base
except ImportError:
    # pylint: disable=E0611, F0401
    # import failures here are non-fatal
    from pylint.checkers import BaseChecker as Base

try:
    # pylint: disable=E0611, F0401
    # import failures here are non-fatal
    from pylint.interfaces import IAstroidChecker
    import astroid
except ImportError:
    # pylint: disable=E0611, F0401
    # import failures here are non-fatal
    # support older pylint versions
    from pylint.interfaces import IASTNGChecker as IAstroidChecker
    from logilab import astng as astroid
# pylint: enable=W0611


def strip_symbol_from_msgs(oChecker):
    """Strip the 'symbol' entry from the msg tuple.

       Pylint versions before 0.26 don't support having a symbol entry,
       but leaving it out in later versions causes problems with duplicate
       entries, so we have this function to convert back to the older
       format."""

    dNewMsgs = {}
    for sKey, tData in oChecker.msgs.items():
        dNewMsgs[sKey] = (tData[0], tData[2])
    # Monkey patch the checker
    oChecker.msgs = dNewMsgs


def compat_register(cChecker, oLinter):
    """Handle compatibility dance for registration."""
    oChecker = cChecker(oLinter)
    try:
        oLinter.register_checker(oChecker)
    except ValueError:
        strip_symbol_from_msgs(oChecker)
        oLinter.register_checker(oChecker)
