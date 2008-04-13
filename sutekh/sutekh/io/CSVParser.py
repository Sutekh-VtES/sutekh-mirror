# CSVParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""
Parse cards from a CSV file.
"""

from sutekh.core.CardSetHolder import CardSetHolder
from sutekh.core.CardLookup import DEFAULT_LOOKUP
from sqlobject import sqlhub
import csv

class CSVParser(object):
    """Parser cards from a CSV file into a CardSetHolder.

       Cards should be listed in columns and specify at least the card name and
       card count. Each row may optionally include the name of the expansion
       the card comes from.
       """

    # TODO: move this enum somewhere else
    # (possibly to CardSetHolder)
    PCL, PCS, ACS = range(3)

    def __init__(self, iCardNameColumn, iCountColumn, iExpansionColumn=None,
                 bHasHeader=True, iFileType=PCL):
        self.oCS = CardSetHolder()
        self.iCardNameColumn = iCardNameColumn
        self.iCountColumn = iCountColumn
        self.iExpansionColumn = iExpansionColumn
        self.bHasHeader = bHasHeader
        self.iFileType = iFileType
        assert (self.iFileType in [self.PCL, self.PCS, self.ACS])

    def _commit_holder(self, oCardLookup):
        """Commit contents of the card set holder to
           the database"""
        oOldConn = sqlhub.processConnection
        sqlhub.processConnection = oOldConn.transaction()

        if self.iFileType == self.PCL:
            self.oCS.create_physical_cl(oCardLookup)
        elif self.iFileType == self.PCS:
            self.oCS.create_pcs(oCardLookup)
        else:
            self.oCS.create_acs(oCardLookup)

        sqlhub.processConnection.commit()
        sqlhub.processConnection = oOldConn

    def _process_row(self, aRow):
        """Extract the relevant data from a single row in the CSV file."""
        sName = aRow[self.iCardNameColumn].strip()
        if not sName:
            return # skip rows with no name

        iCount = int(aRow[self.iCountColumn])

        if self.iExpansionColumn is not None:
            sExpansionName = aRow[self.iExpansionColumn].strip()
        else:
            sExpansionName = None

        self.oCS.add(iCount, sName, sExpansionName)

    def parse(self, fIn, sCardSetName, oCardLookup=DEFAULT_LOOKUP):
        """Process the CSV file line into the CardSetHolder"""
        oCsvFile = csv.reader(fIn)
        self.oCS.name = sCardSetName

        oIter = iter(oCsvFile)
        if self.bHasHeader:
            oIter.next()

        for aRow in oIter:
            try:
                self._process_row(aRow)
            except ValueError, oExp:
                raise ValueError("Line %d in CSV file could not be parsed"
                        " (%s)" % (oCsvFile.line_num, oExp))
