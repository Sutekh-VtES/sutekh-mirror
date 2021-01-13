# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2016 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Print the deck using the image plugin to get images for the cards."""

import enum

from gi.repository import Gdk, GdkPixbuf, Gtk

from sutekh.base.core.BaseTables import PhysicalCardSet
from sutekh.base.core.BaseAdapters import (IAbstractCard, IPhysicalCard,
                                           IPrinting)
from sutekh.base.gui.SutekhDialog import do_complaint_error
from sutekh.base.gui.plugins.BaseImages import get_printing_info, check_file
from sutekh.gui.PluginManager import SutekhPlugin

@enum.unique
class PrintExpOption(enum.Enum):
    """The choices of which cards to use for proxy images"""
    PRINT_LATEST = 1
    PRINT_EXACT = 2

TEXT_LATEST = 'Use Latest Card Image'
TEXT_EXACT = 'Use Exact Image'

IMG_WIDTH = 720
IMG_HEIGHT = 1008


class PrintProxyPlugin(SutekhPlugin):
    """Plugin for printing a deck using proxy images"""

    dTableVersions = {PhysicalCardSet: (7,)}
    aModelsSupported = (PhysicalCardSet,)

    dOptions = {
        TEXT_LATEST: PrintExpOption.PRINT_LATEST,
        TEXT_EXACT: PrintExpOption.PRINT_EXACT,
    }

    sMenuName = "Print Card Set as Proxies"

    sHelpCategory = "card_sets:actions"

    sHelpText = """If you have downloaded the card images, this allows
                   you to print the card set using the card images for
                   use as proxies.

                   If images are available for all the expansions, you can
                   choose to either print the exact expansion specified
                   for the card, or use the latest image for the given card.
                   By default, the most recent card image will be used.

                   Cards without an expansion ("Unspecified Expansion") will
                   always be printed using the latest available image.

                   If the exact image cannot be found, another image of the
                   card from a different expansion will be used if possible.
                   The plugin will throw an error only if no suitable image
                   can be found.

                   This will only print the current filtered view of the
                   card set, which can be used to restict the card printed
                   to only those required."""

    @classmethod
    def get_help_list_text(cls):
        return """Print the card set using the images of the cards, for use \
                  as proxies."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # This is a horrible hack - we should add an API for querying other
        # plugins
        self._oSettings = None
        self._oImageFrame = None
        for oPlugin in self.parent.plugins:
            if hasattr(oPlugin, 'image_frame'):
                self._oImageFrame = oPlugin.image_frame
                break
        self._aFiles = []
        self._ePrintExpansion = PrintExpOption.PRINT_LATEST
        self._aMissing = set()

    def get_menu_item(self):
        """Register on the 'Actions' Menu"""
        if not self._oImageFrame:
            return None
        oPrint = Gtk.MenuItem(label="Print Card Set as Proxies")
        oPrint.connect("activate", self.activate)
        return ('Actions', oPrint)

    def activate(self, _oWidget):
        """Generate the PDF file"""
        oPrintOp = Gtk.PrintOperation()
        if self._oSettings:
            oPrintOp.set_print_settings(self._oSettings)

        oPrintOp.connect("begin-print", self.begin_print)
        oPrintOp.connect("end-print", self.end_print)
        oPrintOp.connect("draw-page", self.draw_page)
        oPrintOp.set_custom_tab_label('Proxy Set Print Settings')

        dCustomData = {}
        oPrintOp.connect('create-custom-widget', self._add_print_widgets,
                         dCustomData)
        oPrintOp.connect('custom-widget-apply', self._get_print_widgets,
                         dCustomData)

        oRes = oPrintOp.run(Gtk.PrintOperationAction.PRINT_DIALOG,
                            self.parent)
        if self._aMissing:
            # We aborted due to missing cards
            aErrors = ["Error printing card set.",
                       "Unable to load images for the following cards:"]
            aErrors.extend(sorted(self._aMissing))
            sErr = '\n'.join(aErrors)
            do_complaint_error(sErr)
        elif oRes == Gtk.PrintOperationResult.ERROR:
            do_complaint_error("Error printing card set:\n" +
                               oPrintOp.get_error())
        elif oRes == Gtk.PrintOperationResult.APPLY:
            self._oSettings = oPrintOp.get_print_settings()

    def begin_print(self, oPrintOp, _oContext):
        """Set up printing context.

           This includes determining pagination and the number of pages.
           """
        self._aMissing = set()
        oPrintOp.set_unit(Gtk.Units.POINTS)
        oPrintOp.set_n_pages(1)
        oIter = self.model.get_card_iterator(self.model.get_current_filter())
        aCards = sorted([IPhysicalCard(x) for x in oIter],
                        key=lambda y: IAbstractCard(y).name)

        # We lookup all the images here, so we can cancel before printing
        # if we're missing images.
        for oTheCard in aCards:
            oCard = oTheCard
            if self._ePrintExpansion == PrintExpOption.PRINT_LATEST:
                # We build a fake card with the correct expansion
                sLatestPrinting = get_printing_info(oTheCard.abstractCard)[0]
                oExp = IPrinting(sLatestPrinting)
                oCard = IPhysicalCard((oTheCard.abstractCard, oExp))

            sFilename = self._oImageFrame.lookup_filename(oCard)[0]
            if not check_file(sFilename):
                bOk = False
                for sExpName in get_printing_info(oTheCard.abstractCard):
                    oPrinting = IPrinting(sExpName)
                    oCard = IPhysicalCard((oTheCard.abstractCard, oPrinting))
                    sFilename = self._oImageFrame.lookup_filename(oCard)[0]
                    if check_file(sFilename):
                        bOk = True
                        self._aFiles.append(sFilename)
                        break
                if not bOk:
                    self._aMissing.add(oTheCard.abstractCard.name)
                    # Move onto the next card
                    continue
            else:
                self._aFiles.append(sFilename)
        if self._aMissing:
            # Abort the print operation
            oPrintOp.cancel()
            return

        # We put 9 images on a page
        iNumCards = len(aCards)
        iNumPages = iNumCards // 9
        # Add extra page if needed for the excess cards
        if iNumPages * 9 < iNumCards:
            iNumPages += 1
        oPrintOp.set_n_pages(iNumPages)

    # oPrintOp, oContext part of function signature
    def end_print(self, _oPrintOp, _oContext):
        """Clean up resources allocated in begin_print."""
        self._aFiles = []
        self._ePrintExpansion = PrintExpOption.PRINT_LATEST
        # We don't clear the missing list, so it's available for
        # reporting errors

    # oPrintOp part of function signature
    def draw_page(self, _oPrintOp, oContext, iPageNum):
        """Page drawing callback."""
        # Print this set of 9 cards
        aTheseFiles = self._aFiles[iPageNum * 9:(iPageNum + 1) * 9]
        oCairoContext = oContext.get_cairo_context()
        iOffsetX = 0
        iOffsetY = 0
        # We choose to scale the images to 720x1004
        # since that's close to 300dpi
        # Since our context is setup for the page, we need to set
        # the correct scale
        # We add bit for the cut marker lines
        fContextWidth = oContext.get_width()
        fContextHeight = oContext.get_height()
        oCairoContext.scale(fContextWidth / (3 * IMG_WIDTH + 10),
                            fContextHeight / (3 * IMG_HEIGHT + 10))
        # Draw the print marker lines
        for sFilename in aTheseFiles:
            oPixbuf = GdkPixbuf.Pixbuf.new_from_file(sFilename)
            # We probably should be cleverer with scaling here
            oPixbuf = oPixbuf.scale_simple(IMG_WIDTH, IMG_HEIGHT,
                                           GdkPixbuf.InterpType.HYPER)
            Gdk.cairo_set_source_pixbuf(oCairoContext, oPixbuf,
                                        iOffsetX, iOffsetY)
            oCairoContext.rectangle(iOffsetX, iOffsetY,
                                    IMG_WIDTH, IMG_HEIGHT)
            oCairoContext.paint()
            iOffsetX += IMG_WIDTH + 5
            if iOffsetX > 3 * IMG_WIDTH:
                iOffsetX = 0
                iOffsetY += IMG_HEIGHT + 5

    def _add_print_widgets(self, _oOp, dCustomData):
        """Add widgets to the custom options tab"""
        oVBox = Gtk.VBox(homogeneous=False, spacing=2)

        oLabel = Gtk.Label()
        oLabel.set_markup("<b>Proxy printing Options:</b>")
        oLabel.set_alignment(0.0, 0.5)
        oVBox.pack_start(oLabel, False, True, 10)
        aExpButtons = []

        oFirstBut = Gtk.RadioButton(group=None, label=TEXT_LATEST)
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

        dCustomData["aExpButtons"] = aExpButtons

        oVBox.show_all()

        return oVBox

    def _get_print_widgets(self, _oOp, _oBox, dCustomData):
        """Get the selection from the custom area"""
        for oButton in dCustomData["aExpButtons"]:
            if oButton.get_active():
                sLabel = oButton.get_label()
                self._ePrintExpansion = self.dOptions[sLabel]


plugin = PrintProxyPlugin
