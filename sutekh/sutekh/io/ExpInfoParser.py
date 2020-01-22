# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2013 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Parse expansion and printing info from a json file."""

import json
from logging import Logger

from sutekh.base.core.BaseAdapters import (IExpansion, IPrinting,
                                           IAbstractCard)

from sutekh.core.SutekhObjectMaker import SutekhObjectMaker


class ExpInfoParser:
    """Parse expansion and printing info from a JSON file and update the
       database with the correct information."""

    # pylint: disable=too-many-arguments
    # we may need all these arguments for some files
    def __init__(self, oLogHandler):
        self.oLogger = Logger('exp info parser')
        if oLogHandler is not None:
            self.oLogger.addHandler(oLogHandler)
        self.oLogHandler = oLogHandler
        self._oMaker = SutekhObjectMaker()

    def _update_printing(self, oPrinting, dPrintInfo):
        """Update the specific printing with the required info"""
        # Clear any existing properties (to ensure we reflect
        # updates correctly)
        for oProp in oPrinting.properties:
            oPrinting.removePrintingProperty(oProp)
        # Add properties for the variant
        sDate = dPrintInfo.pop('date')
        sBack = dPrintInfo.pop('back')
        oDateProp = self._oMaker.make_printing_property(
            "Release Date: %s" % sDate)
        oBackProp = self._oMaker.make_printing_property(
            "Back Type: %s" % sBack)

        # pylint: disable=no-member
        # SQLObject confuses pylint
        oPrinting.addPrintingProperty(oDateProp)
        oPrinting.addPrintingProperty(oBackProp)
        # pylint: enable=no-member

        aCards = dPrintInfo.pop('cards', [])
        # Create Physical cards for the variant cards if needed
        for sCardName in aCards:
            oAbsCard = IAbstractCard(sCardName)
            _oCard = self._oMaker.make_physical_card(oAbsCard, oPrinting)
        # Any other items in the dict get added 'as-is'
        for sKey, sValue in dPrintInfo.items():
            oProp = self._oMaker.make_printing_property(
                "%s: %s" % (sKey, sValue))
            oPrinting.addProperty(oProp)

    def _handle_expansion(self, sExp, dExpInfo):
        """Handle updating the specific expansion."""
        oExp = IExpansion(sExp)
        for sVariant in dExpInfo:
            if sVariant == "None":
                oPrinting = IPrinting((oExp, None))
            else:
                oPrinting = self._oMaker.make_printing(oExp, sVariant)
            self._update_printing(oPrinting, dExpInfo[sVariant])
            oPrinting.syncUpdate()

    def parse(self, fIn):
        """Process the JSON file line into the database"""
        dExpInfo = json.load(fIn)
        if hasattr(self.oLogHandler, 'set_total'):
            self.oLogHandler.set_total(len(dExpInfo))
        for sExp in dExpInfo:
            self._handle_expansion(sExp, dExpInfo[sExp])
            self.oLogger.info('Added Expansion info: %s', sExp)
