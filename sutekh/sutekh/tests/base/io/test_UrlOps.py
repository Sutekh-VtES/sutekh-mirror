# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2014 Simon Cross <hodgestar+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test the UrlOps utilities"""

import unittest
from urllib.error import URLError
import socket
from sutekh.tests.TestCore import SutekhTest
from sutekh.base.tests.TestUtils import FailFile
from sutekh.base.io.UrlOps import fetch_data


class UrlOpsTest(SutekhTest):
    """Class for the URL ops tests"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    def test_error_handler(self):
        """Test triggering the error handler"""
        aErrors = []

        def error_handler(oExp):
            """Dummy error handler"""
            aErrors.append(oExp)

        oFile = FailFile(socket.timeout)
        fetch_data(oFile, fErrorHandler=error_handler)
        # pylint: disable=unbalanced-tuple-unpacking
        # by construction, this unpacking is safe
        [oExp] = aErrors
        # pylint: enable=unbalanced-tuple-unpacking
        self.assertTrue(isinstance(oExp, socket.timeout))

        del aErrors[:]

        oFile = FailFile(URLError('aaa'))
        fetch_data(oFile, fErrorHandler=error_handler)
        # pylint: disable=unbalanced-tuple-unpacking
        # by construction, this unpacking is safe
        [oExp] = aErrors
        # pylint: enable=unbalanced-tuple-unpacking
        self.assertTrue(isinstance(oExp, URLError))


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
