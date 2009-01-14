# test_DatabaseVersion.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test database versioning code"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.core.DatabaseVersion import DatabaseVersion
from sutekh.core.SutekhObjects import aObjectList

class DatabaseVersionTests(SutekhTest):
    """Class for the database version tests."""

    def test_version(self):
        """Handle the expected case where everything is fine"""
        oVersion = DatabaseVersion()

        aVersions = [oTable.tableversion for oTable in aObjectList]
        # Test that this works as expected
        self.assertTrue(oVersion.check_tables_and_versions(aObjectList,
            aVersions))
        # Test for failures
        oTable = aObjectList[0]
        self.assertFalse(oVersion.check_tables_and_versions([oTable],
            [oTable.tableversion - 1]))
        self.assertFalse(oVersion.check_tables_and_versions([oTable],
            [oTable.tableversion + 1]))

        for oTable in aObjectList[0:6]:
            # Test some tables
            aVersions = range(max(0, oTable.tableversion - 1),
                    oTable.tableversion + 2)
            aVersionsFail = range(oTable.tableversion + 1,
                    oTable.tableversion + 5)
            self.assertTrue(oVersion.check_table_in_versions(oTable,
                aVersions))
            self.assertFalse(oVersion.check_table_in_versions(oTable,
                aVersionsFail))

        aTables = [aObjectList[0], aObjectList[1], aObjectList[5]]
        aVersions = [aObjectList[0].tableversion + 1,
                aObjectList[1].tableversion + 3,
                aObjectList[5].tableversion - 1]

        aLowerTables, aHigherTables = \
                oVersion.get_bad_tables(aTables, aVersions)

        # aLowerTables -> Database version < requested, so these are the
        # expected results
        self.assertEqual(aLowerTables, [aObjectList[0].sqlmeta.table,
            aObjectList[1].sqlmeta.table])
        self.assertEqual(aHigherTables, [aObjectList[5].sqlmeta.table])
