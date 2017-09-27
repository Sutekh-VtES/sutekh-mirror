# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2013 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Parse lookup info from a CSV file.

   The csv file is formatted as: Domain, LookupKey, Value."""

import csv
import datetime
from logging import Logger

from sutekh.base.core.BaseObjects import LookupHints


class LookupHintsCSVParser(object):
    """Parse the hints information from the csv file and add it to the
       appropriate table."""

    # pylint: disable=R0913
    # we may need all these arguments for some files
    def __init__(self, oLogHandler):
        self.oLogger = Logger('lookup hints parser')
        if oLogHandler is not None:
            self.oLogger.addHandler(oLogHandler)
        self.oLogHandler = oLogHandler

    def parse(self, fIn):
        """Process the CSV file line into the database"""
        oCsvFile = csv.reader(fIn)
        aRows = list(oCsvFile)
        if hasattr(self.oLogHandler, 'set_total'):
            self.oLogHandler.set_total(len(aRows))
        for sDomain, sLookupKey, sValue in aRows:
            oLookup = LookupHint(domain=sDomain,
                                 lookup=sLookupKey,
                                 value=sValue)
            # pylint: disable=E1101
            # E1101 - avoid SQLObject method not detected problems
            oLookup.syncUpdate()
            self.oLogger.info('Added %s Hint', sDomain)
