# test_ZipFileWrapper.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test the Zip File Wrapper"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.core.SutekhObjects import IAbstractCard, IPhysicalCard, \
        IPhysicalCardSet
from sutekh.io.ZipFileWrapper import ZipFileWrapper
import unittest

class ZipFileWrapperTest(SutekhTest):
    """class for the Zip File tests"""
    aAbstractCards = ['.44 magnum', 'ak-47', 'abbot', 'abebe', 'abombwe']
    aCardSetNames = ['Test Set 1', 'Test Set 2']

    def test_zip_file(self):
        """Test zip file handling"""
        # pylint: disable-msg=E1101
        # E1101: SQLObject + PyProtocols magic confuses pylint
        # FIXME: fill in details


if __name__ == "__main__":
    unittest.main()
