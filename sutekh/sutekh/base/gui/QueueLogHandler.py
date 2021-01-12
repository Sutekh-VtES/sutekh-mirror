# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details


"""LogHandler to capture logs for display in the gui.

   This is a simple finite-length queue of formatted log messages, but
   we also track the level to support filtering the recorded log messages."""

from collections import deque

from logging import Handler, Formatter, DEBUG


QUEUE_LENGTH = 500


class QueueLogHandler(Handler):
    """Simple log handler that adds messages to a queue"""
    # We explicitly inherit from object, since Handler is a classic class


    def __init__(self):
        super().__init__()
        self.aQueue = deque([], QUEUE_LENGTH)
        self.setLevel(DEBUG)
        # Set a fairly informative formatter for this
        self.formatter = Formatter(
            "%(asctime)s - %(levelname)s - "
            "%(module)s.%(funcName)s: %(message)s")
        self._oLogWidget = None

    def set_widget(self, oLogWidget):
        """Associate with the correct display widget"""
        self._oLogWidget = oLogWidget
        # Request a reload, so the window is populated
        oLogWidget.queue_reload()

    def unset_widget(self):
        """Remove the widget association"""
        self._oLogWidget = None

    # pyline: disable=arguments-differ
    # pyline gets confused here - I think because of the base classic class
    def emit(self, oRecord):
        """Add message to the queue"""
        # We record a tuple of log level (for filtering) and the
        # formatted message
        self.aQueue.append((oRecord.levelno, self.format(oRecord)))
        # Queue a reload so the widget can refresh itself with
        # the latest messages
        if self._oLogWidget:
            self._oLogWidget.queue_reload()
