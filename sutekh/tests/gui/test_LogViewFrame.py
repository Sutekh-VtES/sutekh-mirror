# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test the behaviour of the log text view"""

import logging
import unittest

from io import BytesIO

from sutekh.tests.GuiSutekhTest import GuiSutekhTest

from sutekh.base.core.BaseTables import PhysicalCardSet


class TestLogViewFrame(GuiSutekhTest):
    """Class for the LogViewFrame test cases"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    INFO_MSG = 'Info message 1'
    DEBUG_MSG = 'Debug message 2'
    ERROR_MSG = 'Error message 3'
    WARN_MSG = 'Warn message 4'

    def test_basic(self):
        """Set of simple tests of the LogViewFrame"""
        # Add the log view frame
        oOutput = BytesIO()
        # 'My Collection' is needed for default config
        _oMyCollection = PhysicalCardSet(name='My Collection')
        self.oWin.setup(self.oConfig)
        oNewFrame = self.oWin.add_new_log_view_frame(None)
        # Clear the log history of any existing entries
        self.oWin.gui_log_handler.aQueue.clear()
        oNewFrame.reload()
        # Check that the frame is properly cleared
        oNewFrame.view.export_buffer(oOutput)
        self.assertEqual(oOutput.getvalue(), b'')
        # log several messages
        logging.info(self.INFO_MSG)
        logging.debug(self.DEBUG_MSG)
        logging.error(self.ERROR_MSG)
        logging.warn(self.WARN_MSG)
        # Assert that they're all present
        oNewFrame.reload()
        oNewFrame.view.export_buffer(oOutput)
        sResult = oOutput.getvalue()
        self.assertTrue('ERROR' in sResult)
        self.assertTrue('WARN' in sResult)
        self.assertTrue('INFO' in sResult)
        self.assertTrue('DEBUG' in sResult)

        self.assertTrue(self.ERROR_MSG in sResult)
        self.assertTrue(self.WARN_MSG in sResult)
        self.assertTrue(self.INFO_MSG in sResult)
        self.assertTrue(self.DEBUG_MSG in sResult)
        # Test filtering
        oOutput.truncate(0)
        oOutput.seek(0)

        oNewFrame.set_filter_level(logging.WARN)
        oNewFrame.view.export_buffer(oOutput)
        sResult = oOutput.getvalue()
        self.assertTrue('ERROR' in sResult)
        self.assertTrue('WARN' in sResult)
        self.assertTrue(self.ERROR_MSG in sResult)
        self.assertTrue(self.WARN_MSG in sResult)

        self.assertTrue('INFO' not in sResult)
        self.assertTrue('DEBUG' not in sResult)
        self.assertTrue(self.INFO_MSG not in sResult)
        self.assertTrue(self.DEBUG_MSG not in sResult)


if __name__ == "__main__":
    unittest.main()
