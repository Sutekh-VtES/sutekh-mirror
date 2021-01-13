# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Plugin for simple, direct printing of the card set."""

import enum

from gi.repository import Gtk, Pango, PangoCairo

from ...core.BaseTables import PhysicalCardSet
from ...core.BaseAdapters import (IAbstractCard, IPhysicalCard, IPrintingName,
                                  IExpansion)
from ..BasePluginManager import BasePlugin
from ..SutekhDialog import do_complaint_error

@enum.unique
class PrintExpOption(enum.Enum):
    """Printing Options"""
    NO_EXPANSION = 1
    LONG_INDENT = 2
    SHORT_LINE = 3


def _card_expansion_details(oCard, eMode):
    """Get the expansion for the name"""
    oPhysCard = IPhysicalCard(oCard)
    if oPhysCard.printing:
        if eMode == PrintExpOption.SHORT_LINE:
            return IExpansion(oPhysCard.printing).shortname
        return IPrintingName(oPhysCard.printing)
    return ' (Unknown)'


class BasePrint(BasePlugin):
    """Plugin for printing the card sets.

       Use Gtk's Printing support to print out a simple list of the cards
       in the card set. This has less formatting than exporting via
       HTML, for instance, but does print directly.
       """
    dTableVersions = {PhysicalCardSet: (5, 6, 7)}
    aModelsSupported = (PhysicalCardSet,)

    dOptions = {
        'No Expansion info': PrintExpOption.NO_EXPANSION,
        'Card Name\n    Expansion Name': PrintExpOption.LONG_INDENT,
        'Card Name [Short Expansion Name]': PrintExpOption.SHORT_LINE,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ePrintExpansions = PrintExpOption.NO_EXPANSION
        self._sFontName = "sans 12"
        self._oSettings = None
        # internal state for printing
        self._aPageBreaks = None
        self._oPangoLayout = None

    def get_menu_item(self):
        """Register on the 'Actions' Menu"""
        oPrint = Gtk.MenuItem(label="Print Card Set")
        oPrint.connect("activate", self.activate)
        return ('Actions', oPrint)

    def activate(self, _oWidget):
        """In response to the menu choice, do the actual print operation."""
        oPrintOp = Gtk.PrintOperation()

        if self._oSettings is not None:
            oPrintOp.set_print_settings(self._oSettings)

        oPrintOp.connect("begin-print", self.begin_print)
        oPrintOp.connect("end-print", self.end_print)
        oPrintOp.connect("draw-page", self.draw_page)

        oPrintOp.set_custom_tab_label('Card Set Print Settings')

        dCustomData = {}
        oPrintOp.connect('create-custom-widget', self._add_print_widgets,
                         dCustomData)
        oPrintOp.connect('custom-widget-apply', self._get_print_widgets,
                         dCustomData)

        oRes = oPrintOp.run(Gtk.PrintOperationAction.PRINT_DIALOG,
                            self.parent)

        if oRes == Gtk.PrintOperationResult.ERROR:
            do_complaint_error("Error printing card set:\n")
        elif oRes == Gtk.PrintOperationResult.APPLY:
            self._oSettings = oPrintOp.get_print_settings()

    def begin_print(self, oPrintOp, oContext):
        """Set up printing context.

           This includes determining pagination and the number of pages.
           """
        oPrintOp.set_use_full_page(False)
        oPrintOp.set_unit(Gtk.Units.MM)
        oPrintOp.set_n_pages(1)  # safety net in case error occur later on

        fWidth, fHeight = oContext.get_width(), oContext.get_height()

        oLayout = oContext.create_pango_layout()
        oLayout.set_font_description(
            Pango.FontDescription.from_string(self._sFontName))
        oLayout.set_width(int(fWidth * Pango.SCALE))

        oLayout.set_markup(self.cardlist_markup())

        iLineCount = oLayout.get_line_count()

        fPageHeight = 0
        aPageBreaks = []

        for iThisLine in range(iLineCount):
            oLine = oLayout.get_line(iThisLine)
            _oInkRect, oLogicalRect = oLine.get_extents()

            # line height / SCALE
            fLineHeight = float(oLogicalRect.height) / Pango.SCALE

            if fPageHeight + fLineHeight > fHeight:
                aPageBreaks.append(iThisLine)
                fPageHeight = 0

            fPageHeight += fLineHeight

        oPrintOp.set_n_pages(len(aPageBreaks) + 1)
        self._aPageBreaks = aPageBreaks
        self._oPangoLayout = oLayout

    # oPrintOp, oContext part of function signature
    def end_print(self, _oPrintOp, _oContext):
        """Clean up resources allocated in begin_print.
           """
        self._aPageBreaks = None
        self._oPangoLayout = None

    # oPrintOp part of function signature
    def draw_page(self, _oPrintOp, oContext, iPageNum):
        """Page drawing callback.
           """
        # pylint: disable=too-many-locals
        # We use lots of variables for clarity
        iStartPageLine, iEndPageLine = 0, 0
        aPageBreaks = self._aPageBreaks
        oLayout = self._oPangoLayout

        if iPageNum > 0:
            iStartPageLine = aPageBreaks[iPageNum - 1]

        if iPageNum < len(aPageBreaks):
            iEndPageLine = aPageBreaks[iPageNum]
        else:
            iEndPageLine = oLayout.get_line_count()

        oCairoContext = oContext.get_cairo_context()
        oCairoContext.set_source_rgb(0, 0, 0)
        oCairoContext.set_line_width(0.1)

        oIter = oLayout.get_iter()

        fStartPos = 0.0
        iLine = 0

        while True:
            if iLine >= iStartPageLine:
                # oIter.get_line is a bit buggy with pyGtkcompat,
                # so we side step it by querying the layout directly
                oLine = oLayout.get_line(iLine)
                _oInkRect, oLogicalRect = oLine.get_extents()

                fBaseLine = float(oIter.get_baseline()) / Pango.SCALE

                if iLine == iStartPageLine:
                    fStartPos = fBaseLine

                # line x co-ordinate / SCALE
                fXPos = float(oLogicalRect.x) / Pango.SCALE
                # baseline - start pos - line y-co-ordinate / SCALE
                fYPos = fBaseLine - fStartPos - (float(oLogicalRect.y) /
                                                 Pango.SCALE)

                oCairoContext.move_to(fXPos, fYPos)
                PangoCairo.layout_line_path(oCairoContext, oLine)
                oCairoContext.stroke_preserve()
                oCairoContext.fill()

            iLine += 1
            if not (iLine < iEndPageLine and oIter.next_line()):
                break

    def cardlist_markup(self):
        """Format the card set nicely for printing."""
        oCS = self._get_card_set()

        aMarkup = []
        aMarkup.append("<big><b><u>%s</u></b></big>" % self._escape(oCS.name))
        aMarkup.append("  <b>Author</b>: %s" % self._escape(oCS.author))
        if oCS.comment:
            aMarkup.append("  <b>Comment</b>: %s" % self._escape(oCS.comment))
            aMarkup.append("")
        if oCS.annotations:
            aMarkup.append("  <b>Annotations</b>: %s" %
                           self._escape(oCS.annotations))
            aMarkup.append("")
        # Add a line to separate the cards from the header using strikethrough
        aMarkup.append("          <s>"
                       "                                          </s>")
        aMarkup.append("")

        oCardIter = self.model.get_card_iterator(None)
        oGroupedIter = self.model.groupby(oCardIter, IAbstractCard)

        # Iterate over groups
        for sGroup, oGroupIter in sorted(oGroupedIter, key=lambda x: x[0]):
            # Check for null group
            if sGroup is None:
                sGroup = '<< None >>'

            iCnt = 0
            dCardInfo = {}
            dExpInfo = {}
            for oCard in oGroupIter:
                oAbsCard = IAbstractCard(oCard)
                dCardInfo.setdefault(oAbsCard.name, 0)
                dCardInfo[oAbsCard.name] += 1
                iCnt += 1
                if self._ePrintExpansions != PrintExpOption.NO_EXPANSION:
                    dExpInfo.setdefault(oAbsCard.name, {})
                    sExp = _card_expansion_details(oCard,
                                                   self._ePrintExpansions)
                    dExpInfo[oAbsCard.name].setdefault(sExp, 0)
                    dExpInfo[oAbsCard.name][sExp] += 1

            aMarkup.append("<u>%s:</u> (%d)" % (self._escape(sGroup), iCnt))

            # Fill in Cards
            for sCardName, iCardCnt in sorted(dCardInfo.items()):
                if self._ePrintExpansions in (PrintExpOption.NO_EXPANSION,
                                              PrintExpOption.LONG_INDENT):
                    aMarkup.append(
                        u"  %i \u00D7 %s" % (iCardCnt,
                                             self._escape(sCardName)))
                    if sCardName in dExpInfo:
                        for sExp, iCnt in sorted(dExpInfo[sCardName].items()):
                            aMarkup.append(
                                u"    %i \u00D7 %s" % (iCnt,
                                                       self._escape(sExp)))
                else:
                    for sExp, iCnt in sorted(dExpInfo[sCardName].items()):
                        aMarkup.append(
                            u"  %i \u00D7 %s [%s]" % (iCnt,
                                                      self._escape(sCardName),
                                                      self._escape(sExp)))

            aMarkup.append("")

        return "\n".join(aMarkup)

    def _add_print_widgets(self, _oOp, dCustomData):
        """Add widgets to the custom options tab"""
        oVBox = Gtk.VBox(homogeneous=False, spacing=2)

        oLabel = Gtk.Label()
        oLabel.set_markup("<b>Expansion Information:</b>")
        oLabel.set_alignment(0.0, 0.5)
        oVBox.pack_start(oLabel, False, False, 10)
        aExpButtons = []

        oFirstBut = Gtk.RadioButton(group=None, label='No Expansion info')
        oFirstBut.set_active(True)
        oVBox.pack_start(oFirstBut, False, True, 0)
        aExpButtons.append(oFirstBut)
        for sText in self.dOptions:
            if sText == oFirstBut.get_label():
                continue
            oBut = Gtk.RadioButton(group=oFirstBut, label=sText)
            oBut.set_active(False)
            oVBox.pack_start(oBut, False, True, 0)
            aExpButtons.append(oBut)

        oLabel = Gtk.Label()
        oLabel.set_markup("<b>Font:</b>")
        oLabel.set_alignment(0.0, 0.5)
        oVBox.pack_start(oLabel, False, False, 10)

        oFontSel = Gtk.FontSelection()
        oFontSel.set_font_name(self._sFontName)
        oVBox.pack_start(oFontSel, False, True, 0)

        dCustomData["aExpButtons"] = aExpButtons
        dCustomData["oFontSel"] = oFontSel

        oVBox.show_all()

        return oVBox

    def _get_print_widgets(self, _oOp, _oBox, dCustomData):
        """Get the selection from the custom area"""
        for oButton in dCustomData["aExpButtons"]:
            if oButton.get_active():
                sLabel = oButton.get_label()
                self._ePrintExpansions = self.dOptions[sLabel]

        self._sFontName = dCustomData["oFontSel"].get_font_name()
