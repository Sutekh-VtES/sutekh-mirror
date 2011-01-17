# DatabaseVersion.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>,
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# version management helper class

"""Versioning support for Sutekh"""

from sqlobject import sqlhub
from sutekh.core.SutekhObjects import VersionTable


def _get_connection(oConn):
    """Ensure we have a valid connection object"""
    if oConn is None:
        return sqlhub.processConnection
    else:
        return oConn


class DatabaseVersion(object):
    """Class to handle all the database manipulation aspects."""

    _dCache = {}
    _dConns = {}

    def __init__(self, oConn=None):
        oConn = _get_connection(oConn)
        # We need to make sure the version table exists, even if
        # the rest of the database doesn't, otherwise early checks are
        # problematic
        self.ensure_table_exists(oConn)
        self.populate_cache(oConn)

    @classmethod
    def get_cache(cls):
        """Get a reference to the class-global results cache"""
        return cls._dCache

    @classmethod
    def expire_cache(cls):
        """Expire the results cache - needed for database upgrade code
           paths."""
        cls._dCache = {}

    @classmethod
    def populate_cache(cls, oConn):
        """Populate the results cache if empty - reduces queries at start
           up."""
        dCache = cls.get_cache()
        if dCache:
            return
        for oVer in VersionTable.select(connection=oConn):
            if oVer.TableName in dCache:
                raise RuntimeError("Multiple version entries for %s" \
                    " found in the database." % oVer.TableName)
            else:
                dCache[oVer.TableName] = oVer.Version

    @classmethod
    def ensure_table_exists(cls, oConn):
        """Enusre the table exists, but that describe is only called
           once per connection."""
        if not cls._dConns.has_key(oConn):
            VersionTable.createTable(ifNotExists=True, connection=oConn)
            cls._dConns[oConn] = True

    @classmethod
    def expire_table_conn(cls, oConn):
        """Expire the created table for this connection.
           Needed in the database upgrade code.
           """
        if not cls._dConns.has_key(oConn):
            return  # Nothing to do
        del cls._dConns[oConn]

    def set_version(self, oTable, iTableVersion, oConn=None):
        """Set the version for oTable to iTableVersion"""
        oConn = _get_connection(oConn)
        dCache = self.get_cache()
        try:
            sTableName = oTable.sqlmeta.table
        except AttributeError:
            return False
        aVer = list(VersionTable.selectBy(TableName=sTableName,
            connection=oConn))
        iTableCount = len(aVer)
        if iTableCount == 0:
            VersionTable(TableName=sTableName,
                         Version=iTableVersion, connection=oConn)
            dCache[sTableName] = iTableVersion
        elif iTableCount == 1:
            for oVersion in aVer:
                if oVersion.Version != iTableVersion:
                    VersionTable.delete(oVersion.id, connection=oConn)
                    VersionTable(TableName=sTableName,
                                 Version=iTableVersion, connection=oConn)
                dCache[sTableName] = iTableVersion
        else:
            print "Multiple version entries for %s in the database" \
                    % sTableName
            print "Giving up. I suggest dumping and reloading everything"
            return False
        return True

    def get_table_version(self, oTable, oConn=None):
        """Get the version number for oTable.

           returns -1 if no version info exists.
           """
        oConn = _get_connection(oConn)
        dCache = self.get_cache()
        iTableVersion = -1
        try:
            sName = oTable.sqlmeta.table
        except AttributeError:
            return iTableVersion
        if dCache.has_key(sName):
            return dCache[sName]
        aVer = list(VersionTable.selectBy(TableName=sName, connection=oConn))
        iTableCount = len(aVer)
        if iTableCount < 1:
            iTableVersion = -1
        elif iTableCount == 1:
            for oVersion in aVer:
                iTableVersion = oVersion.Version
                dCache[sName] = iTableVersion
        else:
            print "Multiple version entries for %s in the database" \
                    % oTable.sqlmeta.table
            print "Giving up. I suggest dumping and reloading everything"
            # Should this be an exception?
            iTableVersion = -999
        return iTableVersion

    def check_tables_and_versions(self, aTable, aTableVersion, oConn=None):
        """Check version numbers.

           aTable is the list of tables to check
           aTableVersion is a list of version numbers to match.
           It's assumed that aTable and aTableVersions are sorted the same.
           """
        bRes = True
        for oTable, iVersion in zip(aTable, aTableVersion):
            bRes = bRes and \
                    self.get_table_version(oTable, oConn) == iVersion
        return bRes

    def check_table_in_versions(self, oTable, aTableVersions, oConn=None):
        """Check version for a single table.

           Checks whether the given table has a version in the list of
           version numbers in the list aTableVersions.
           """
        iVersion = self.get_table_version(oTable, oConn)
        return iVersion in aTableVersions

    def get_bad_tables(self, aTable, aTableVersion, oConn=None):
        """Get tables that don't match the list of version numbers

           aTable is the list of tables to check
           aTableVersion is a list of version numbers to match.
           It's assumed that aTable and aTableVersions are sorted the same.
           Returns two lists, aLowerTables and aHigherTables, where
           aLowerTables is those with a lower version number, and
           aHigherTables is those with a higher number.
           """
        oConn = _get_connection(oConn)
        aLowerTables = []
        aHigherTables = []
        for oTable, iVersion in zip(aTable, aTableVersion):
            iCurVersion = self.get_table_version(oTable, oConn)
            if iCurVersion < iVersion:
                # Current database is lower than requested
                aLowerTables.append(oTable.sqlmeta.table)
            elif iCurVersion > iVersion:
                # Current database is higher than requested
                aHigherTables.append(oTable.sqlmeta.table)
        return aLowerTables, aHigherTables
