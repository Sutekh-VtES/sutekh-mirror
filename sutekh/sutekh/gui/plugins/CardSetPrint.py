# CardSetPrint.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Plugin for simple, direct printing of the card set."""

import gtk
import pango
from sutekh.core.SutekhObjects import PhysicalCardSet, IAbstractCard, \
        IPhysicalCard
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.gui.SutekhDialog import do_complaint_error

try:
    # pylint: disable-msg=W0104
    # This is an existance check, so it does do nothing
    gtk.PrintOperation
except AttributeError:
    raise ImportError("GTK version does not contain PrintOperation."
            " Try PyGTK >= 2.10.")

NO_EXPANSION, LONG_INDENT, SHORT_LINE = range(3)


def _card_expansion_details(oCard, iMode):
    """Get the expansion for the name"""
    # pylint: disable-msg=E1101
    # SQLObject & PyPrototocols confuses pylint
    oPhysCard = IPhysicalCard(oCard)
    if oPhysCard.expansion:
        if iMode == SHORT_LINE:
            return oPhysCard.expansion.shortname
        return oPhysCard.expansion.name
    return ' (Unknown)'


class CardSetPrint(SutekhPlugin):
    """Plugin for printing the card sets.

       Use gtk's Printing support to print out a simple list of the cards
       in the card set. This has less formatting than exporting via
       HTML, for instance, but does print directly.
       """
    dTableVersions = {PhysicalCardSet: (4, 5, 6)}
    aModelsSupported = (PhysicalCardSet,)

    dOptions = {
            'No Expansion info': NO_EXPANSION,
            'Card Name\n    Expansion Name': LONG_INDENT,
            'Card Name [Short Expansion Name]': SHORT_LINE,
            }

    def __init__(self, *args, **kwargs):
        super(CardSetPrint, self).__init__(*args, **kwargs)
        self._iPrintExpansions = NO_EXPANSION
        self._sFontName = "sans 12"
        self._oSettings = None
        # internal state for printing
        self._aPageBreaks = None
        self._oPangoLayout = None

    def get_menu_item(self):
        """Register on the 'Actions' Menu"""
        if not self.check_versions() or not self.check_model_type():
            return None

        oPrint = gtk.MenuItem("Print Card Set")
        oPrint.connect("activate", self.activate)
        return ('Actions', oPrint)

    def activate(self, _oWidget):
        """In response to the menu choice, do the actual print operation."""
        oPrintOp = gtk.PrintOperation()

        if not self._oSettings is None:
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

        oRes = oPrintOp.run(gtk.PRINT_OPERATION_ACTION_PRINT_DIALOG,
                self.parent)

        if oRes == gtk.PRINT_OPERATION_RESULT_ERROR:
            do_complaint_error("Error printing card set:\n")
        elif oRes == gtk.PRINT_OPERATION_RESULT_APPLY:
            self._oSettings = oPrintOp.get_print_settings()

    def begin_print(self, oPrintOp, oContext):
        """Set up printing context.

           This includes determining pagination and the number of pages.
           """
        oPrintOp.set_use_full_page(False)
        oPrintOp.set_unit(gtk.UNIT_MM)
        oPrintOp.set_n_pages(1)  # safety net in case error occur later on

        fWidth, fHeight = oContext.get_width(), oContext.get_height()

        oLayout = oContext.create_pango_layout()
        oLayout.set_font_description(pango.FontDescription(self._sFontName))
        oLayout.set_width(int(fWidth * pango.SCALE))

        oLayout.set_markup(self.cardlist_markup())

        iLineCount = oLayout.get_line_count()

        fPageHeight = 0
        aPageBreaks = []

        for iThisLine in range(iLineCount):
            oLine = oLayout.get_line(iThisLine)
            _oInkRect, oLogicalRect = oLine.get_extents()

            # line height / SCALE
            fLineHeight = float(oLogicalRect[3]) / pango.SCALE

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
        # pylint: disable-msg=R0914
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

        oContext = oContext.get_cairo_context()
        oContext.set_source_rgb(0, 0, 0)
        oContext.set_line_width(0.1)

        oIter = oLayout.get_iter()

        fStartPos = 0.0
        iLine = 0

        while True:
            if iLine >= iStartPageLine:
                oLine = oIter.get_line()
                _oInkRect, oLogicalRect = oLine.get_extents()

                fBaseLine = float(oIter.get_baseline()) / pango.SCALE

                if iLine == iStartPageLine:
                    fStartPos = fBaseLine

                # line x co-ordinate / SCALE
                fXPos = float(oLogicalRect[0]) / pango.SCALE
                # baseline - start pos - line y-co-ordinate / SCALE
                fYPos = fBaseLine - fStartPos - float(oLogicalRect[1]) / \
                        pango.SCALE

                oContext.move_to(fXPos, fYPos)
                oContext.layout_line_path(oLine)
                oContext.stroke_preserve()
                oContext.fill()

            iLine += 1
            if not (iLine < iEndPageLine and oIter.next_line()):
                break

    def cardlist_markup(self):
        """Format the card set nicely for printing."""
        oCS = self.get_card_set()

        aMarkup = []
        aMarkup.append("<u>%s</u>" % self.escape(oCS.name))
        aMarkup.append("  Author: %s" % self.escape(oCS.author))
        aMarkup.append("  Comment: %s" % self.escape(oCS.comment))
        aMarkup.append("  Annotations: %s" % self.escape(oCS.annotations))
        aMarkup.append("")

        oCardIter = self.model.get_card_iterator(None)
        oGroupedIter = self.model.groupby(oCardIter, IAbstractCard)

        # Iterate over groups
        for sGroup, oGroupIter in sorted(oGroupedIter, key=lambda x: x[0]):
            # Check for null group
            if sGroup is None:
                sGroup = '<< None >>'

            aMarkup.append("<u>%s:</u>" % (self.escape(sGroup),))

            dCardInfo = {}
            dExpInfo = {}
            for oCard in oGroupIter:
                # pylint: disable-msg=E1101
                # pyprotocols confuses pylint
                oAbsCard = IAbstractCard(oCard)
                dCardInfo.setdefault(oAbsCard.name, 0)
                dCardInfo[oAbsCard.name] += 1
                if self._iPrintExpansions != NO_EXPANSION:
                    dExpInfo.setdefault(oAbsCard.name, {})
                    sExp = _card_expansion_details(oCard,
                            self._iPrintExpansions)
                    dExpInfo[oAbsCard.name].setdefault(sExp, 0)
                    dExpInfo[oAbsCard.name][sExp] += 1

            # Fill in Cards
            for sCardName, iCnt in sorted(dCardInfo.items()):
                if self._iPrintExpansions in (NO_EXPANSION, LONG_INDENT):
                    aMarkup.append(u"  %i \u00D7 %s" %
                            (iCnt, self.escape(sCardName)))
                    if sCardName in dExpInfo:
                        for sExp, iCnt in sorted(dExpInfo[sCardName].items()):
                            aMarkup.append(u"    %i \u00D7 %s" % (iCnt,
                                self.escape(sExp)))
                else:
                    for sExp, iCnt in sorted(dExpInfo[sCardName].items()):
                        aMarkup.append(u"  %i \u00D7 %s [%s]" % (iCnt,
                            self.escape(sCardName), self.escape(sExp)))

            aMarkup.append("")

        return "\n".join(aMarkup)

    def _add_print_widgets(self, _oOp, dCustomData):
        """Add widgets to the custom options tab"""
        oVBox = gtk.VBox(False, 2)

        oLabel = gtk.Label()
        oLabel.set_markup("<b>Expansion Information:</b>")
        oLabel.set_alignment(0.0, 0.5)
        oVBox.pack_start(oLabel, expand=False, padding=10)
        aExpButtons = []

        oFirstBut = gtk.RadioButton(None, 'No Expansion info', False)
        oFirstBut.set_active(True)
        oVBox.pack_start(oFirstBut, expand=False)
        aExpButtons.append(oFirstBut)
        for sText in self.dOptions:
            if sText == oFirstBut.get_label():
                continue
            oBut = gtk.RadioButton(oFirstBut, sText, False)
            oBut.set_active(False)
            oVBox.pack_start(oBut, expand=False)
            aExpButtons.append(oBut)

        oLabel = gtk.Label()
        oLabel.set_markup("<b>Font:</b>")
        oLabel.set_alignment(0.0, 0.5)
        oVBox.pack_start(oLabel, expand=False, padding=10)

        oFontSel = gtk.FontSelection()
        oFontSel.set_font_name(self._sFontName)
        oVBox.pack_start(oFontSel, expand=False)

        dCustomData["aExpButtons"] = aExpButtons
        dCustomData["oFontSel"] = oFontSel

        oVBox.show_all()

        return oVBox

    def _get_print_widgets(self, _oOp, _oBox, dCustomData):
        """Get the selection from the custom area"""
        for oButton in dCustomData["aExpButtons"]:
            if oButton.get_active():
                sLabel = oButton.get_label()
                self._iPrintExpansions = self.dOptions[sLabel]

        self._sFontName = dCustomData["oFontSel"].get_font_name()

plugin = CardSetPrint
