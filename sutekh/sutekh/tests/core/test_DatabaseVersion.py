# test_DatabaseVersion.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test database versioning code"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.core.DatabaseVersion import DatabaseVersion
from sutekh.core.SutekhObjects import TABLE_LIST


class DatabaseVersionTests(SutekhTest):
    """Class for the database version tests."""

    def test_version(self):
        """Handle the expected case where everything is fine"""
        oVersion = DatabaseVersion()

        aVersions = [oTable.tableversion for oTable in TABLE_LIST]
        # Test that this works as expected
        self.assertTrue(oVersion.check_tables_and_versions(TABLE_LIST,
            aVersions))
        # Test for failures
        oTable = TABLE_LIST[0]
        self.assertFalse(oVersion.check_tables_and_versions([oTable],
            [oTable.tableversion - 1]))
        self.assertFalse(oVersion.check_tables_and_versions([oTable],
            [oTable.tableversion + 1]))

        for oTable in TABLE_LIST[0:6]:
            # Test some tables
            aVersions = range(max(0, oTable.tableversion - 1),
                    oTable.tableversion + 2)
            aVersionsFail = range(oTable.tableversion + 1,
                    oTable.tableversion + 5)
            # Check with cache expired
            DatabaseVersion.expire_cache()
            self.assertTrue(oVersion.check_table_in_versions(oTable,
                aVersions))
            self.assertFalse(oVersion.check_table_in_versions(oTable,
                aVersionsFail))
            # Test with the cache filled
            self.assertTrue(oVersion.check_table_in_versions(oTable,
                aVersions))
            self.assertFalse(oVersion.check_table_in_versions(oTable,
                aVersionsFail))

        aTables = [TABLE_LIST[0], TABLE_LIST[1], TABLE_LIST[5]]
        aVersions = [TABLE_LIST[0].tableversion + 1,
                TABLE_LIST[1].tableversion + 3,
                TABLE_LIST[5].tableversion - 1]

        aLowerTables, aHigherTables = \
                oVersion.get_bad_tables(aTables, aVersions)

        # aLowerTables -> Database version < requested, so these are the
        # expected results
        self.assertEqual(aLowerTables, [TABLE_LIST[0].sqlmeta.table,
            TABLE_LIST[1].sqlmeta.table])
        self.assertEqual(aHigherTables, [TABLE_LIST[5].sqlmeta.table])
