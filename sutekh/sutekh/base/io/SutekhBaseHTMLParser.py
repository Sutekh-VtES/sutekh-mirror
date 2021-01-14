# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# BAse classes for the HTML Parsers in Sutekh
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Common base classes for the different HTML Parsers"""

from html.parser import HTMLParser
from logging import Logger


# State Base Classes
class StateError(Exception):
    """Error case in the state"""
    pass


class HTMLStateError(StateError):
    """Exception with more info for HTML State transition errors"""
    def __init__(self, sInfo, sData, sTag):
        super().__init__()
        self._sInfo = sInfo
        self._sData = sData
        self._sTag = sTag

    def __str__(self):
        return "HTML Parser State Error : %s\nsData : %s\nTag : %s" % (
            self._sInfo, self._sData, self._sTag)


class BaseState:
    """Base class for parser states"""

    def __init__(self):
        super().__init__()
        self._sData = ""

    def transition(self, sTag, dAttr):
        """Transition from one state to another"""
        raise NotImplementedError  # pragma: no cover

    def data(self, sData):
        """Add data to the state"""
        self._sData += sData


class LogState(BaseState):
    """Base class for the State transitions with a log handler"""

    # pylint: disable=abstract-method
    # descendants will override transition, so still abstract here.
    def __init__(self, oLogger):
        super().__init__()
        self._oLogger = oLogger


class LogStateWithInfo(LogState):
    """Base class for states which contain information of interest"""

    # pylint: disable=abstract-method
    # transition method is still abstract here
    def __init__(self, dInfo, oLogger):
        super().__init__(oLogger)
        self._dInfo = dInfo


class HolderState(BaseState):
    """Base class for parser states"""

    # pylint: disable=abstract-method
    # transition method is still abstract here
    def __init__(self, oHolder):
        super().__init__()
        self._oHolder = oHolder


# Base Parser
# pylint: disable=abstract-method
# pylint complains about error not being overridden, but HTMLParser
# does provide it - the class inheritence structure involved just
# confuses pylint
class SutekhBaseHTMLParser(HTMLParser):
    """Base Parser for the Sutekh HTML parsers"""

    def __init__(self):
        """Create an SutekhBaseHTMLParser."""
        self._oState = BaseState()
        super().__init__()

    def reset(self):
        """Reset the parser"""
        super().reset()
        self._oState = BaseState()

    # pylint: disable=missing-docstring, arguments-differ
    # names are as listed in HTMLParser docs, so no need for docstrings
    # We change the naming convention to match ours, so the argument names
    # will differ
    def handle_starttag(self, sTag, aAttr):
        self._oState = self._oState.transition(sTag.lower(), dict(aAttr))

    def handle_endtag(self, sTag):
        self._oState = self._oState.transition('/' + sTag.lower(), {})

    def handle_data(self, sData):
        self._oState.data(sData)

    def handle_charref(self, sName):
        pass  # pragma: no cover

    def handle_entityref(self, sName):
        pass  # pragma: no cover

    # pylint: enable=missing-docstring, arguments-differ

    def parse(self, fOpenFile):
        """Wrapper around feed to provide a consistent interface with
           other parsers."""
        for sLine in fOpenFile:
            self.feed(sLine)


# Parser with loggin
class LoggingHTMLParser(SutekhBaseHTMLParser):
    """HTML Parser that sets up appropriate logging logic."""

    sLogName = 'Base html parser'

    def __init__(self, oLogHandler):
        self._oLogger = Logger(self.sLogName)
        if oLogHandler is not None:
            self._oLogger.addHandler(oLogHandler)
        super().__init__()
