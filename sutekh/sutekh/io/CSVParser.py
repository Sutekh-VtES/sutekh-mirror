# CSVParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Parse cards from a CSV file."""

import csv


class CSVParser(object):
    """Parser cards from a CSV file into a CardSetHolder.

       Cards should be listed in columns and specify at least the card name and
       card count. Each row may optionally include the name of the expansion
       the card comes from.
       """

    # pylint: disable-msg=R0913
    # we may need all these arguments for some files
    def __init__(self, iCardNameColumn, iCountColumn, iExpansionColumn=None,
            bHasHeader=True):
        self.iCardNameColumn = iCardNameColumn
        self.oCS = None
        self.iCountColumn = iCountColumn
        self.iExpansionColumn = iExpansionColumn
        self.bHasHeader = bHasHeader

    # pylint: enable-msg=R0913

    def _process_row(self, aRow):
        """Extract the relevant data from a single row in the CSV file."""
        sName = aRow[self.iCardNameColumn].strip()
        if not sName:
            return  # skip rows with no name

        try:
            iCount = int(aRow[self.iCountColumn])
        except ValueError:
            iCount = 1
            self.oCS.add_warning("Count for '%s' could not be determined and"
                                    " was set to one." % (sName,))

        if self.iExpansionColumn is not None:
            sExpansionName = aRow[self.iExpansionColumn].strip()
        else:
            sExpansionName = None

        self.oCS.add(iCount, sName, sExpansionName)

    def parse(self, fIn, oHolder):
        """Process the CSV file line into the CardSetHolder"""
        oCsvFile = csv.reader(fIn)
        self.oCS = oHolder

        oIter = iter(oCsvFile)
        if self.bHasHeader:
            oIter.next()

        for aRow in oIter:
            try:
                self._process_row(aRow)
            except ValueError, oExp:
                raise ValueError("Line %d in CSV file could not be parsed"
                        " (%s)" % (oCsvFile.line_num, oExp))
