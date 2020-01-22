# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2017, 2018 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Parse data into the lookup from a CSV file.

   The CSV file is formatted as:
   Domain,Lookup Name,Desired Name."""

import csv
from logging import Logger

from ..core.BaseTables import LookupHints


class LookupCSVParser:
    """Parse lookup info from a CSV file and add the required
       LookupHints entries to the database."""

    def __init__(self, oLogHandler):
        self.oLogger = Logger('lookup data parser')
        if oLogHandler is not None:
            self.oLogger.addHandler(oLogHandler)
        self.oLogHandler = oLogHandler

    def parse(self, fIn):
        """Process the CSV file line into the CardSetHolder"""
        oCsvFile = csv.reader(fIn)
        aRows = list(oCsvFile)
        if hasattr(self.oLogHandler, 'set_total'):
            self.oLogHandler.set_total(len(aRows))
        for sDomain, sLookup, sValue in aRows:
            oLookup = LookupHints(domain=sDomain, lookup=sLookup,
                                  value=sValue)
            oLookup.syncUpdate()
            self.oLogger.info('Added Lookup : (%s, %s)', sDomain, sLookup)
