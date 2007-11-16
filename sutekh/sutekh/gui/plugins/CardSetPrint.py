# CardSetExportHTML.py
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
import pango
from sutekh.core.SutekhObjects import PhysicalCardSet, AbstractCardSet, IAbstractCard, ICardType
from sutekh.gui.PluginManager import CardListPlugin

try:
    gtk.PrintOperation
except AttributeError:
    raise ImportError("GTK version does not contain PrintOperation. Try PyGTK >= 2.10.")

class CardSetPrint(CardListPlugin):
    dTableVersions = { AbstractCardSet: [2,3],
                       PhysicalCardSet: [2,3]}
    aModelsSupported = [AbstractCardSet, PhysicalCardSet]

    def get_menu_item(self):
        """
        Overrides method from base class.
        """
        if not self.check_versions() or not self.check_model_type():
            return None

        # Keep print settings
        self._oSettings = None

        iDF = gtk.MenuItem("Print Card Set")
        iDF.connect("activate", self.activate)
        return iDF

    def get_desired_menu(self):
        return "CardSet"

    def activate(self,oWidget):
        oPrintOp = gtk.PrintOperation()

        if not self._oSettings is None:
            oPrintOp.set_print_settings(self._oSettings)

        oPrintOp.connect("begin-print", self.begin_print)
        oPrintOp.connect("end-print", self.end_print)
        oPrintOp.connect("draw-page", self.draw_page)

        oRes = oPrintOp.run(gtk.PRINT_OPERATION_ACTION_PRINT_DIALOG, self.parent)


        if oRes == gtk.PRINT_OPERATION_RESULT_ERROR:
            oMsg = gtk.MessageDialog(self.parent, gtk.DIALOG_DESTROY_WITH_PARENT,
                                     gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE,
                                     "Error printing card set:\n")
            oMsg.connect("response", lambda w,id: w.destroy())
            oMsg.show()
        elif oRes == gtk.PRINT_OPERATION_RESULT_APPLY:
            self._oSettings = oPrintOp.get_print_settings()

    def begin_print(self,oPrintOp,oContext):
        """Set up printing context.
        
           This includes determining pagination and the number of pages.
           """
        oPrintOp.set_use_full_page(False)
        oPrintOp.set_unit(gtk.UNIT_MM)
        oPrintOp.set_n_pages(1) # safety net in case error occur later on

        fW, fH = oContext.get_width(), oContext.get_height()

        oL = oContext.create_pango_layout()
        oL.set_font_description(pango.FontDescription("sans 12"))
        oL.set_width(int(fW * pango.SCALE))

        # oL.set_markup("Testing Testing Testing Testing Testing Testing Testing Testing Testing Testing Testing Testing\n" * 200)
        oL.set_markup(self.cardlist_markup())

        iLineCount = oL.get_line_count()

        fPageHeight = 0
        aPageBreaks = []

        for i in range(iLineCount):
            oLine = oL.get_line(i)
            oInkRect, oLogicalRect = oLine.get_extents()

            fLineHeight = float(oLogicalRect[3]) / pango.SCALE # line height / SCALE

            if fPageHeight + fLineHeight > fH:
                aPageBreaks.append(i)
                fPageHeight = 0

            fPageHeight += fLineHeight

        oPrintOp.set_n_pages(len(aPageBreaks)+1)
        self._aPageBreaks = aPageBreaks
        self._oPangoLayout = oL

    def end_print(self,oPrintOp,oContext):
        """Clean up resources allocated in begin_print.
           """
        self._aPageBreaks = None
        self._oPangoLayout = None

    def draw_page(self,oPrintOp,oContext,iPageNum):
        """Page drawing callback.
           """
        iStartPageLine, iEndPageLine = 0, 0
        aPageBreaks = self._aPageBreaks
        oL = self._oPangoLayout

        if iPageNum > 0:
            iStartPageLine = aPageBreaks[iPageNum-1]

        if iPageNum < len(aPageBreaks):
            iEndPageLine = aPageBreaks[iPageNum]
        else:
            iEndPageLine = oL.get_line_count()

        oC = oContext.get_cairo_context()
        oC.set_source_rgb(0,0,0)
        oC.set_line_width(0.1)

        oIter = oL.get_iter()

        fStartPos = 0.0
        iLine = 0

        while True:
            if iLine >= iStartPageLine:
                oLine = oIter.get_line()
                oIntRect, oLogicalRect = oLine.get_extents()

                fBaseLine = float(oIter.get_baseline()) / pango.SCALE

                if iLine == iStartPageLine:
                    fStartPos = fBaseLine

                fX = float(oLogicalRect[0]) / pango.SCALE # line x co-ordinate / SCALE
                fY = fBaseLine - fStartPos - float(oLogicalRect[1]) / pango.SCALE # baseline - start pos - line y-co-ordinate / SCALE

                oC.move_to(fX, fY)
                oC.layout_line_path(oLine)
                oC.stroke_preserve()
                oC.fill()

            iLine += 1
            if not (iLine < iEndPageLine and oIter.next_line()):
                break

    def cardlist_markup(self):
        cSetType = self.view.cSetType
        sSetName = self.view.sSetName

        oCS = cSetType.byName(sSetName)
        aCrypt, aLibrary = self.get_cards(oCS)

        aMarkup = []
        aMarkup.append("<u>%s</u>" % oCS.name)
        aMarkup.append("  Author: %s" % oCS.author)
        aMarkup.append("  Comment: %s" % oCS.comment)
        aMarkup.append("  Annotations: %s" % oCS.annotations)
        aMarkup.append("")

        aMarkup.append("<u>Crypt:</u>")
        for oCard, iCnt in aCrypt:
            aMarkup.append("  %ix %s" % (iCnt, oCard.name))
        aMarkup.append("")

        aMarkup.append("<u>Library:</u>")
        for oCard, iCnt in aLibrary:
            aMarkup.append("  %ix %s" % (iCnt, oCard.name))

        return "\n".join(aMarkup)

    def get_cards(self,oCardSet):
        dCrypt = {}
        dLibrary = {}
        aCryptTypes = set([ICardType("Vampire"), ICardType("Imbued")])

        for oCard in oCardSet.cards:
            oACard = IAbstractCard(oCard)
            if set(oACard.cardtype).intersection(aCryptTypes):
                dCrypt.setdefault(oACard.id,[oACard,0])
                dCrypt[oACard.id][1] += 1
            else:
                dLibrary.setdefault(oACard.id,[oACard,0])
                dLibrary[oACard.id][1] += 1

        aCrypt = [(oC, iCnt) for oId, (oC, iCnt) in dCrypt.iteritems()]
        aCrypt.sort(key = lambda x: x[0].name)

        aLibrary = [(oC, iCnt) for oId, (oC, iCnt) in dLibrary.iteritems()]
        aLibrary.sort(key = lambda x: x[0].name)

        return aCrypt, aLibrary

plugin = CardSetPrint
