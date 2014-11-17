# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2013 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Parse expansion and date info from a CSV file."""

import csv
import datetime
from logging import Logger
from sqlobject import SQLObjectNotFound

from sutekh.base.core.BaseObjects import IExpansion


class ExpDateCSVParser(object):
    """Parse expansion and date info from a CSV file and update the
       database with the correct dates"""

    # pylint: disable=R0913
    # we may need all these arguments for some files
    def __init__(self, oLogHandler):
        self.oLogger = Logger('exp date parser')
        if oLogHandler is not None:
            self.oLogger.addHandler(oLogHandler)
        self.oLogHandler = oLogHandler

    def parse(self, fIn):
        """Process the CSV file line into the CardSetHolder"""
        oCsvFile = csv.reader(fIn)
        aRows = list(oCsvFile)
        if hasattr(self.oLogHandler, 'set_total'):
            self.oLogHandler.set_total(len(aRows))
        for sExp, sDate in aRows:
            try:
                oExp = IExpansion(sExp)
            except SQLObjectNotFound:
                # This error is non-fatal - the user may not have imported
                # the extra card lists, so we can legimately encounter
                # expansions here which aren't in the database
                self.oLogger.info('Skipped Expansion: %s', sExp)
                continue
            oDate = datetime.datetime.strptime(sDate, "%Y%m%d").date()
            oExp.releasedate = oDate
            # pylint: disable=E1101
            # E1101 - avoid SQLObject method not detected problems
            oExp.syncUpdate()
            self.oLogger.info('Added Expansion: %s', sExp)
