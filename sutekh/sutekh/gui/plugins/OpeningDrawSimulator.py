# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Dialog to display deck analysis software
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>,
# GPL - see COPYING for details
"""Simulate the opening hand draw."""

from gi.repository import Gtk

from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.base.gui.SutekhDialog import do_complaint_error
from sutekh.base.gui.plugins.BaseOpeningDraw import (BaseOpeningDraw,
                                                     fill_string,
                                                     format_dict,
                                                     draw_cards,
                                                     get_cards_filter,
                                                     hypergeometric_mean,
                                                     fill_frame,
                                                     check_cards)
from sutekh.core.Filters import CryptCardFilter, CardFunctionFilter
from sutekh.base.core.BaseFilters import (MultiCardTypeFilter,
                                          CardTypeFilter, FilterNot)


class HandDetails:
    """Convience class for holding drawn hand details"""
    # pylint: disable=too-many-arguments
    # Use all this for showing the results

    def __init__(self, dHand, dCrypt, sTypeDetails, sPropDetails,
                 dNextHand, dNextCrypt):
        self.sHand = format_dict(dHand)
        self.sCrypt = format_dict(dCrypt)
        self.sType = sTypeDetails
        self.sProp = sPropDetails
        self.dNextHand = dNextHand
        self.dNextCrypt = dNextCrypt


class OpeningHandSimulator(SutekhPlugin, BaseOpeningDraw):
    """Simulate opening hands."""

    COLUMN_WIDTH = 290  # 3 columns

    sHelpText = """This tool treats the card set as a completed deck, and
                   displays the expected distribution of cards in the opening
                   hand and crypt. It is intended to give you some idea of how
                   the deck will work in practice. In addition, you can
                   generate example opening hands and crypts by clicking the
                   _Draw sample hand_ button."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dCardTypes = {}
        self.dCardProperties = {}
        self.aLibrary = []
        self.aCrypt = []
        self.iMoreLib = 0
        self.iMoreCrypt = 0

    def _get_cards(self):
        """Extract card details from the card set."""
        oCryptFilter = CryptCardFilter()

        self.aCrypt = get_cards_filter(self.model, oCryptFilter)
        self.aLibrary = get_cards_filter(self.model, FilterNot(oCryptFilter))

        if len(self.aLibrary) < 7:
            do_complaint_error('Library needs to be at least as large as the'
                               ' opening hand')
            return False

        if len(self.aCrypt) < 4:
            do_complaint_error('Crypt needs to be at least as large as the'
                               ' opening draw')
            return False

        for sType in MultiCardTypeFilter.get_values():
            aList = get_cards_filter(self.model, CardTypeFilter(sType))
            if aList and aList[0] in self.aLibrary:
                self.dCardTypes[sType] = set([oC.name for oC in aList])

        for sFunction in CardFunctionFilter.get_values():
            aList = get_cards_filter(self.model, CardFunctionFilter(sFunction))
            if aList:
                self.dCardProperties[sFunction] = set([oC.name for oC in
                                                       aList])
        return True

    def _cleanup(self):
        """Cleanup"""
        self.dCardTypes = {}
        self.dCardProperties = {}
        self.aLibrary = []
        super()._cleanup()

    def _fill_stats(self, oDialog):
        """Fill in the stats from the draws"""
        oHBox = Gtk.HBox(True, 3)
        # setup display widgets
        # pylint: disable=no-member
        # vbox methods not detected by pylint
        oDialog.vbox.pack_start(oHBox, True, True, 0)
        dLibProbs = self._get_lib_props()
        oHBox.pack_start(self._setup_grouped_view(dLibProbs, self.dCardTypes,
                                                  'Card Types'),
                         True, True, 0)
        oHBox.pack_start(self._setup_grouped_view(dLibProbs,
                                                  self.dCardProperties,
                                                  'Card Properties'),
                         True, True, 0)
        oHBox.pack_start(self._setup_flat_view(self.aCrypt, 4, 'Crypt Cards'),
                         True, True, 0)
        oHBox.show_all()

    def _get_lib_props(self):
        """Calculate the expected number of each card in the opening hand"""
        dLibCount = {}
        for oCard in self.aLibrary:
            dLibCount.setdefault(oCard.name, 0)
            dLibCount[oCard.name] += 1
        dLibProbs = {}
        iTot = len(self.aLibrary)
        for sName, iCount in dLibCount.items():
            dLibProbs[sName] = hypergeometric_mean(iCount, 7, iTot)
        return dLibProbs

    def _do_draw_hand(self):
        """Create a new sample hand"""
        dProps = {}
        dTypes = {}
        dHand, aThisLib = draw_cards(self.aLibrary, 7, True)
        check_cards(dHand, self.dCardTypes, dTypes)
        check_cards(dHand, self.dCardProperties, dProps)
        dCrypt, aThisCrypt = draw_cards(self.aCrypt, 4, True)
        dNextHand = {}
        dNextCrypt = {}
        for iNextDraw in range(3):
            dNextHand[iNextDraw] = {}
            dNextCrypt[iNextDraw] = {}
            dNextHand[iNextDraw], _aTemp = draw_cards(aThisLib, 5, False)
            dNextCrypt[iNextDraw], _aTemp = draw_cards(aThisCrypt, 1, False)
        return HandDetails(dHand, dCrypt,
                           fill_string(dTypes, dHand, self.dCardTypes),
                           fill_string(dProps, dHand, self.dCardProperties),
                           dNextHand, dNextCrypt)

    def _fill_hand(self, oHBox):
        """Fill in details of the hand"""
        self.iMoreLib = 0
        self.iMoreCrypt = 0
        oHandLabel = Gtk.Label()
        oHandLabel.set_markup(self.aDrawnHands[self.iCurHand - 1].sHand)
        oCryptLabel = Gtk.Label()
        oCryptLabel.set_markup(self.aDrawnHands[self.iCurHand - 1].sCrypt)

        oCryptInfoBox = Gtk.VBox(homogeneous=False, spacing=0)
        oHandInfoBox = Gtk.VBox(homogeneous=False, spacing=0)
        oHandInfoBox.pack_start(oHandLabel, True, True, 0)
        oMoreCards = Gtk.Button('Next 5')
        oMoreCards.connect('clicked', self._more_lib, oHandInfoBox)
        oHandInfoBox.pack_start(oMoreCards, False, False, 0)

        oCryptInfoBox.pack_start(oCryptLabel, True, True, 0)
        oMoreCrypt = Gtk.Button('Next 1')
        oMoreCrypt.connect('clicked', self._more_crypt, oCryptInfoBox)
        oCryptInfoBox.pack_start(oMoreCrypt, False, False, 0)
        oFrame = Gtk.Frame()
        oFrame.set_label('Opening Hand')
        oFrame.add(oHandInfoBox)
        oHBox.pack_start(oFrame, True, True, 0)
        oFrame = Gtk.Frame()
        oFrame.set_label('Opening Crypt Draw')
        oFrame.add(oCryptInfoBox)
        oHBox.pack_start(oFrame, True, True, 0)

    def _more_lib(self, oButton, oBox):
        """Add the next 5 library cards"""
        if self.iMoreLib < 3:
            dNextHand = self.aDrawnHands[self.iCurHand - 1].dNextHand[
                self.iMoreLib]
            # pop out button show we can add our text
            oCardLabel = Gtk.Label()
            oCardLabel.set_markup(format_dict(dNextHand))
            oBox.remove(oButton)
            oBox.pack_start(oCardLabel, True, True, 0)
            self.iMoreLib += 1
            if self.iMoreLib < 3:
                oBox.pack_start(oButton, False, False, 0)
            oBox.show_all()

    def _more_crypt(self, oButton, oBox):
        """Add the next crypt card"""
        if self.iMoreCrypt < 3:
            dNextCrypt = self.aDrawnHands[self.iCurHand - 1].dNextCrypt[
                self.iMoreCrypt]
            # pop out button show we can add our text
            oCardLabel = Gtk.Label()
            oCardLabel.set_markup(format_dict(dNextCrypt))
            oBox.remove(oButton)
            oBox.pack_start(oCardLabel, True, True, 0)
            self.iMoreCrypt += 1
            if self.iMoreCrypt < 3:
                oBox.pack_start(oButton, False, False, 0)
            oBox.show_all()

    def _redraw_detail_box(self):
        """Fill in the details for the given hand"""
        oDetailBox = Gtk.VBox(homogeneous=False, spacing=2)
        oHBox = Gtk.HBox(False, 2)
        oHBox.pack_start(
            fill_frame(
                self.aDrawnHands[self.iCurHand - 1].sType, 'Card Types'),
            True, True, 0)
        oHBox.pack_start(
            fill_frame(
                self.aDrawnHands[self.iCurHand - 1].sProp, 'Card Properties'),
            True, True, 0)
        oDetailBox.pack_start(oHBox, False, True, 0)
        return oDetailBox


plugin = OpeningHandSimulator
