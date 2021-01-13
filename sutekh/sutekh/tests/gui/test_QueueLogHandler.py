# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test the behaviour of the queued log handler"""

import logging
import unittest

import pytest

from sutekh.tests.TestCore import SutekhTest

from sutekh.base.gui.QueueLogHandler import QueueLogHandler, QUEUE_LENGTH


class DummyWidget:
    """Fake the frame widget so we can check the log handler behaviour"""

    def __init__(self):
        self.bNeedsReload = False

    def reload(self):
        """Clear reload status"""
        self.bNeedsReload = False

    def queue_reload(self):
        """Mark that we need a reload"""
        self.bNeedsReload = True


class TestQueueLogHandler(SutekhTest):
    """Class for the QueueLogHandler test cases"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    # pylint: disable=invalid-name
    # caplog is the pytest required name
    @pytest.fixture(autouse=True)
    def fix_log_level(self, caplog):
        """Set the correct log state for the tests."""
        caplog.clear()
        caplog.set_level(logging.DEBUG)
    # pylint: enable=invalid-name

    def test_basic(self):
        """Set of simple tests of the QueueLogHandler"""
        # pylint: disable=too-many-statements, too-many-locals
        # This is clearest as a single sequential test case
        oRootLogger = logging.getLogger()
        oHandler = QueueLogHandler()
        oRootLogger.addHandler(oHandler)

        oFrame = DummyWidget()

        # Check that we get log messages in the handler
        logging.info("message 1")
        logging.warning("message 2")
        logging.debug("message 3")
        logging.error("message 4")

        # Check that this hasn't touched the frame
        self.assertEqual(oFrame.bNeedsReload, False)

        # Check we have the expected (level, formatted log message) contents
        self.assertEqual(oHandler.aQueue[0][0], logging.INFO)
        self.assertTrue("INFO" in oHandler.aQueue[0][1])
        self.assertTrue(".test_basic:" in oHandler.aQueue[0][1])
        self.assertTrue("message 1" in oHandler.aQueue[0][1])

        self.assertEqual(oHandler.aQueue[1][0], logging.WARNING)
        self.assertTrue("WARNING" in oHandler.aQueue[1][1])
        self.assertTrue(".test_basic:" in oHandler.aQueue[1][1])
        self.assertTrue("message 2" in oHandler.aQueue[1][1])

        self.assertEqual(oHandler.aQueue[2][0], logging.DEBUG)
        self.assertTrue("DEBUG" in oHandler.aQueue[2][1])
        self.assertTrue("message 3" in oHandler.aQueue[2][1])

        self.assertEqual(oHandler.aQueue[3][0], logging.ERROR)
        self.assertTrue("ERROR" in oHandler.aQueue[3][1])
        self.assertTrue(".test_basic:" in oHandler.aQueue[3][1])
        self.assertTrue("message 4" in oHandler.aQueue[3][1])

        # Attach the widget
        oHandler.set_widget(oFrame)
        # Setting the widget should queue a reload to get the initial messages
        self.assertEqual(oFrame.bNeedsReload, True)
        oFrame.reload()
        self.assertEqual(oFrame.bNeedsReload, False)

        # Check various log levels trigger a reload request
        logging.info("Test message")
        self.assertEqual(oFrame.bNeedsReload, True)
        oFrame.reload()
        self.assertEqual(oFrame.bNeedsReload, False)

        logging.debug("Test message")
        self.assertEqual(oFrame.bNeedsReload, True)
        oFrame.reload()
        self.assertEqual(oFrame.bNeedsReload, False)

        logging.warning("Test message")
        self.assertEqual(oFrame.bNeedsReload, True)
        oFrame.reload()
        self.assertEqual(oFrame.bNeedsReload, False)

        logging.error("Test message")
        self.assertEqual(oFrame.bNeedsReload, True)
        oFrame.reload()
        self.assertEqual(oFrame.bNeedsReload, False)

        # Check that detaching the widget works
        oHandler.unset_widget()
        logging.error("Test message")
        self.assertEqual(oFrame.bNeedsReload, False)

        # Check queue behaviour
        # We're not aiming to test deque here, just that we're
        # using it correctly.
        for iNum in range(QUEUE_LENGTH+10):
            logging.info("queue test %d", iNum)

        self.assertEqual(len(oHandler.aQueue), QUEUE_LENGTH)
        self.assertTrue("queue test 10" in oHandler.aQueue[0][1])
        self.assertTrue("queue test 509" in oHandler.aQueue[-1][1])


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
