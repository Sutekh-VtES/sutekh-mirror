# SutekhBaseHTMLParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# BAse classes for the HTML Parsers in Sutekh
# Copyright 2009 Neil Muller <drnlmuller+gmail@gmail.com>
# GPL - see COPYING for details

"""Common base classes for the different HTML Parsers"""

import HTMLParser


# State Base Classes
class StateError(Exception):
    """Error case in the state true"""
    pass


class BaseState(object):
    """Base class for parser states"""

    def __init__(self):
        super(BaseState, self).__init__()
        self._sData = ""

    def transition(self, sTag, dAttr):
        """Transition from one state to another"""
        raise NotImplementedError

    def data(self, sData):
        """Add data to the state"""
        self._sData += sData


class LogState(BaseState):
    """Base class for the State transitions with a log handler"""

    # pylint: disable-msg=W0223
    # descendants will override transition, so still abstract here.
    def __init__(self, oLogger):
        super(LogState, self).__init__()
        self.oLogger = oLogger


class LogStateWithInfo(LogState):
    """Base class for states which contain information of interest"""

    # pylint: disable-msg=W0223
    # transition method is still abstract here
    def __init__(self, dInfo, oLogger):
        super(LogStateWithInfo, self).__init__(oLogger)
        self._dInfo = dInfo


class HolderState(BaseState):
    """Base class for parser states"""

    # pylint: disable-msg=W0223
    # transition method is still abstract here
    def __init__(self, oHolder):
        super(HolderState, self).__init__()
        self._oHolder = oHolder


# Base Parser
class SutekhBaseHTMLParser(HTMLParser.HTMLParser, object):
    """Base Parser for the Sutekh HTML parsers"""

    # We explicitly inherit from object, since HTMLParser is a classic class
    def __init__(self):
        """Create an SutekhBaseHTMLParser.

           oHolder is a sutekh.core.CardSetHolder.CardSetHolder object
           (or similar).
           """
        self._oState = BaseState()
        super(SutekhBaseHTMLParser, self).__init__()

    def reset(self):
        """Reset the parser"""
        super(SutekhBaseHTMLParser, self).reset()
        self._oState = BaseState()

    # pylint: disable-msg=C0111
    # names are as listed in HTMLParser docs, so no need for docstrings
    def handle_starttag(self, sTag, aAttr):
        self._oState = self._oState.transition(sTag.lower(), dict(aAttr))

    def handle_endtag(self, sTag):
        self._oState = self._oState.transition('/' + sTag.lower(), {})

    def handle_data(self, sData):
        self._oState.data(sData)

    # pylint: disable-msg=C0321
    # these don't need statements
    def handle_charref(self, sName): pass
    def handle_entityref(self, sName): pass
