# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2017 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Splits a VEKN pdf file into pieces and adds them to the card images
   as a set of expansion images"""

import os

# gi will return a ValueError if we can't require the correct
# poppler version, so we convert this into a ImportError for
# the plugin manager
try:
    import gi
    gi.require_version('Poppler', '0.18')
except ValueError as oErr:
    raise ImportError("Failed to require Poppler: %s" % oErr)
from gi.repository import GLib, Gtk, Poppler, Gdk
import cairo

from sqlobject import SQLObjectNotFound

from sutekh.base.core.BaseTables import PhysicalCardSet, Expansion
from sutekh.base.core.BaseAdapters import IPhysicalCard, IExpansion
from sutekh.base.core.BaseFilters import MultiExpansionFilter
from sutekh.base.gui.plugins.BaseImages import check_file
from sutekh.base.gui.SutekhDialog import (SutekhDialog,
                                          do_complaint_buttons,
                                          do_complaint_error)
from sutekh.base.gui.SutekhFileWidget import SutekhFileWidget
from sutekh.base.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.base.gui.GuiCardLookup import ACLLookupView
from sutekh.base.gui.CellRendererSutekhButton import CellRendererSutekhButton
from sutekh.base.Utility import ensure_dir_exists

from sutekh.gui.PluginManager import SutekhPlugin


START = (36, 50)
CARD_DIM = (180, 252)

SCALES = {
    '360 x 504': 2,
    '540 x 756': 3,
    '720 x 1008': 4,
    '900 x 1260': 5,
    }


def _get_cards_iter(oModel, oIter):
    """Get a list of cards with a printing and the associated path"""
    aList = []
    oChildIter = oModel.iter_children(oIter)
    while oChildIter:
        oCard = oModel.get_physical_card_from_iter(oChildIter)
        if oCard:
            aList.append((oCard, oChildIter))
        if oModel.iter_n_children(oChildIter) > 0:
            aList.extend(_get_cards_iter(oModel, oChildIter))
        oChildIter = oModel.iter_next(oChildIter)
    return aList


def lookup_card(oAbsCard, aExp, oImageFrame):
    sFileName = None
    oPhysCard = None
    for oExp in aExp:
        try:
            oPhysCard = IPhysicalCard((oAbsCard, oExp))
        except SQLObjectNotFound:
            continue
        sFileName = oImageFrame.lookup_filename(oPhysCard)[0]
    return sFileName


class ImportView(ACLLookupView):
    """View to display the page from the PDF"""

    def __init__(self, oParent, oConfig, aExp):
        super().__init__(oParent, oConfig)

        oUsedCell = CellRendererSutekhButton()
        oUsedCell.load_icon("starred", self)
        oExistingCell = CellRendererSutekhButton()
        oExistingCell.load_icon("non-starred", self)
        # We override the IncCard & DecCell columns for the 'used' and
        # We override the IncCard & DecCell columns for the 'used' and
        # 'existsing' flags, which is a bit icky, but we aren't using them
        # for their intended purpose anyway.
        oUsedColumn = Gtk.TreeViewColumn("Used", oUsedCell, showicon=3)
        oUsedColumn.set_fixed_width(50)
        oUsedColumn.set_sizing(Gtk.TreeViewColumnSizing.FIXED)

        oExistingColumn = Gtk.TreeViewColumn("Image Exists",
                                             oExistingCell, showicon=4)
        oExistingColumn.set_fixed_width(50)
        oExistingColumn.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        # We insert the column before the name, so it's more visible.
        self.insert_column(oUsedColumn, 0)
        self.insert_column(oExistingColumn, 1)

        self._oModel.selectfilter = MultiExpansionFilter(aExp)
        self._aExp = aExp
        self._oModel.applyfilter = True

    def set_selected_used(self):
        """Set the selected card to used."""
        _oModel, aSelection = self.get_selection().get_selected_rows()
        for oPath in aSelection:
            oIter = self._oModel.get_iter(oPath)
            self._oModel.set(oIter, 3, True)

    def set_existing(self, oImageFrame):
        """Set the given card to existing"""
        aAllCards = _get_cards_iter(self._oModel, None)
        for oCard, oIter in aAllCards:
            sName = lookup_card(oCard.abstractCard, self._aExp, oImageFrame)
            if not sName:
                continue
            if not check_file(sName):
                continue
            # Flag as existing
            self._oModel.set(oIter, 4, True)


class ImportPDFImagesPlugin(SutekhPlugin):
    """Plugin to split a VEKN card set PDF into images for use
       with the CardImages plugin."""
    # pylint: disable=attribute-defined-outside-init
    # We define a bunch of attributes outside of __init__, since there's
    # no benefit to defining them earlier, and the plugin entry point ensures
    # it will be safe.

    dTableVersions = {PhysicalCardSet: (7, )}
    aModelsSupported = ("MainWindow",)

    sMenuName = "Import VEKN pdf file as card images"

    sHelpCategory = "card_list:downloads"

    sHelpText = """This plugin allows you to import a PDF release from the
                   V:EKN as images. This is especially useful for ensuring
                   there are high resolution images available for printing
                   the card set.

                   The initial dialog allows you to choose a PDF file,
                   specify which expansion the PDF file corresponds
                   to and also specify the resolution to use for the
                   images.

                   The cards will then be extracted from the PDF file, and
                   then you will be presented with a dialog listing
                   the cards in the expansion on the left, and showing
                   the extracted image on the right.

                   You can move between the extracted images using
                   the *Prev Image* and *Next Image* image buttons.
                   For each image, you can select a card from the
                   list and choose *Set image for selected card*
                   to save the displayed image as the extracted
                   image for the card. Cards which have already
                   been choses will be marked with a tick-mark
                   next to their names."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._oImageFrame = None

    def get_menu_item(self):
        """Add the menu item to the Data Downloads menu.
           """
        oImport = Gtk.MenuItem(label=self.sMenuName)
        oImport.connect('activate', self.run_import_dialog)
        return [('Data Downloads', oImport)]

    def run_import_dialog(self, _oMenuWidget):
        """Ask the user for a PDF image and an expansion, and then
           step through the sections of the image, asking the user
           to map them to cards."""

        # We do the plugin lookup here, to get around the current lack
        # of plugin dependancy ordering
        for oPlugin in self.parent.plugins:
            if hasattr(oPlugin, 'image_frame'):
                self._oImageFrame = oPlugin.image_frame
                break
        # Can't operate without the Card Image Plugin
        if self._oImageFrame is None:
            return

        self.oDlg = SutekhDialog("Choose PDF File and Expansion", None,
                                 Gtk.DialogFlags.MODAL |
                                 Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                 ("_OK", Gtk.ResponseType.OK,
                                  "_Cancel", Gtk.ResponseType.CANCEL))
        # pylint: disable=no-member
        # vbox confuses pylint
        self.oDlg.vbox.pack_start(Gtk.Label(label="PDF File"), False, True, 0)
        self.oFileChooser = SutekhFileWidget(self.parent,
                                             Gtk.FileChooserAction.OPEN)
        self.oFileChooser.add_filter_with_pattern('PDF Files', ['*.pdf'])
        # self.oFileChooser.default_filter()
        self.oDlg.vbox.pack_start(self.oFileChooser, True, True, 0)

        # Choose the expansion for the card set

        self.oDlg.vbox.pack_start(Gtk.Label(label="Expansion"), False, True, 0)

        aExpansions = [x.name for x in Expansion.select()
                       if x.name[:5] != 'Promo'] + ['Promo']
        self._oFirstBut = None
        self._oFirstScaleBut = None
        aExpansions.sort()
        oTable = Gtk.Table(len(aExpansions) // 4, 4)
        self.oDlg.vbox.pack_start(oTable, False, True, 0)
        iXPos, iYPos = 0, 0
        for sName in aExpansions:
            if self._oFirstBut:
                oBut = Gtk.RadioButton(group=self._oFirstBut, label=sName)
            else:
                # No first button
                self._oFirstBut = Gtk.RadioButton(group=None, label=sName)
                self._oFirstBut.set_sensitive(True)
                oBut = self._oFirstBut
            oTable.attach(oBut, iXPos, iXPos + 1, iYPos, iYPos + 1)
            iXPos += 1
            if iXPos > 3:
                iXPos = 0
                iYPos += 1

        self.oDlg.vbox.pack_start(Gtk.Label(label="Image Size to Use"),
                                  False, True, 0)
        oTable = Gtk.Table(len(SCALES) // 2, 2)
        self.oDlg.vbox.pack_start(oTable, False, True, 0)
        iXPos, iYPos = 0, 0
        for sScale in sorted(SCALES):
            if self._oFirstScaleBut:
                oBut = Gtk.RadioButton(group=self._oFirstScaleBut,
                                       label=sScale)
            else:
                self._oFirstScaleBut = Gtk.RadioButton(group=None,
                                                       label=sScale)
                self._oFirstScaleBut.set_sensitive(True)
                oBut = self._oFirstScaleBut
            oTable.attach(oBut, iXPos, iXPos + 1, iYPos, iYPos + 1)
            iXPos += 1
            if iXPos > 1:
                iXPos = 0
                iYPos += 1

        self.oDlg.connect("response", self.handle_response)
        self.oDlg.set_size_request(1000, 600)
        self.oDlg.show_all()

        self.oDlg.run()

    def handle_response(self, _oWidget, oResponse):
        """Handle the user's clicking on OK or CANCEL in the dialog."""
        aExp = []
        if oResponse == Gtk.ResponseType.OK:
            for oBut in self._oFirstBut.get_group():
                if oBut.get_active():
                    sName = oBut.get_label()
                    if sName != 'Promo':
                        aExp = [IExpansion(sName)]
                    else:
                        aExp = [x for x in Expansion.select()
                                if x.name[:5] == 'Promo']
            for oBut in self._oFirstScaleBut.get_group():
                if oBut.get_active():
                    sScale = oBut.get_label()
                    self._iScale = SCALES[sScale]
            sFile = self.oFileChooser.get_filename()
            if not sFile:
                do_complaint_error("No PDF file selected")
            else:
                self.oDlg.hide()
                self.do_import(sFile, aExp)

        self.oDlg.destroy()

    def do_import(self, sFile, aExp):
        """Do the actual import of the PDF file"""
        # pylint: disable=no-member
        # Poppler & GLib confuse pylint
        try:
            self._oDocument = Poppler.Document.new_from_file(
                "file://" + sFile, None)
        except GLib.GError:
            do_complaint_error("Unable to parse the PDF file: %s" % sFile)
            return
        oImportDialog = SutekhDialog("Match cards and images", None,
                                     Gtk.DialogFlags.MODAL |
                                     Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                     ("_Close", Gtk.ResponseType.CLOSE))
        self._iNumPages = self._oDocument.get_n_pages()
        self._iCurPageNo = 0
        self._iXPos, self._iYPos = 0, 0
        self._oPageImg = None

        self._iXOffset, self._iYOffset = 0, 0
        self._iXSize, self._iYSize = CARD_DIM

        self._load_page()

        oHBox = Gtk.HBox()
        oImportDialog.vbox.pack_start(oHBox, True, True, 0)

        oAbsCardView = ImportView(oImportDialog, self.config, aExp)
        oAbsCardView.load()
        oViewWin = AutoScrolledWindow(oAbsCardView)
        oViewWin.set_size_request(350, 650)
        oHBox.pack_start(oViewWin, False, False, 0)

        oVBox = Gtk.VBox()
        oHBox.pack_start(oVBox, True, True, 0)
        oDrawArea = Gtk.DrawingArea()
        oDrawArea.set_size_request(self._iScale * CARD_DIM[0],
                                   self._iScale * CARD_DIM[1])

        oDrawArea.connect('draw', self._draw_pdf_section)

        # Import manipulation button area
        oOffsetBox = Gtk.HBox()

        oXOffAdj = Gtk.Adjustment(lower=-CARD_DIM[0] // 2,
                                  upper=CARD_DIM[0] // 2,
                                  step_incr=1, value=0)
        oYOffAdj = Gtk.Adjustment(lower=-CARD_DIM[1] // 2,
                                  upper=CARD_DIM[1] // 2,
                                  step_incr=1, value=0)

        self._oXOffset = Gtk.SpinButton()
        self._oXOffset.set_adjustment(oXOffAdj)
        self._oXOffset.set_value(0)
        self._oYOffset = Gtk.SpinButton()
        self._oYOffset.set_adjustment(oYOffAdj)
        self._oYOffset.set_value(0)

        oOffsetBox.pack_start(Gtk.Label(label="Horizontal Offset : "),
                              False, False, 0)
        oOffsetBox.pack_start(self._oXOffset, False, False, 0)
        oOffsetBox.pack_start(Gtk.Label(label="Vertical Offset : "),
                              False, False, 0)
        oOffsetBox.pack_start(self._oYOffset, False, False, 0)

        oScaleBox = Gtk.HBox()

        oXScaleAdj = Gtk.Adjustment(lower=10,
                                    upper=CARD_DIM[0] + 100,
                                    step_incr=1, value=CARD_DIM[0])
        oYScaleAdj = Gtk.Adjustment(lower=10, upper=CARD_DIM[1] + 100,
                                    step_incr=1, value=CARD_DIM[1])
        self._oXScale = Gtk.SpinButton()
        self._oXScale.set_adjustment(oXScaleAdj)
        self._oXScale.set_value(CARD_DIM[0])
        self._oYScale = Gtk.SpinButton()
        self._oYScale.set_adjustment(oYScaleAdj)
        self._oYScale.set_value(CARD_DIM[1])

        oScaleBox.pack_start(Gtk.Label(label="Horizontal Size : "),
                             False, False, 0)
        oScaleBox.pack_start(self._oXScale, False, False, 0)
        oScaleBox.pack_start(Gtk.Label(label="Vertical Size : "),
                             False, False, 0)
        oScaleBox.pack_start(self._oYScale, False, False, 0)

        oApplyButton = Gtk.Button('Apply offsets')
        oApplyButton.connect('pressed', self._update_offsets, oDrawArea)
        oVBox.pack_start(oOffsetBox, False, False, 0)
        oVBox.pack_start(oScaleBox, False, False, 0)
        oVBox.pack_start(oApplyButton, False, False, 0)
        oVBox.pack_start(AutoScrolledWindow(oDrawArea), True, True, 0)

        self._oNextButton = Gtk.Button('Next Image')
        self._oNextButton.connect('pressed', self.chg_img, oDrawArea, +1)
        self._oPrevButton = Gtk.Button('Prev Image')
        self._oPrevButton.connect('pressed', self.chg_img, oDrawArea, -1)
        oButtonBox = Gtk.HBox()
        oButtonBox.pack_start(self._oPrevButton, False, False, 0)
        oButtonBox.pack_end(self._oNextButton, False, False, 0)
        self._oPrevButton.set_sensitive(False)
        oSaveButton = Gtk.Button('Set image for selected card')
        oSaveButton.connect('pressed', self.save_img, oDrawArea, oAbsCardView,
                            aExp)
        oButtonBox.pack_start(oSaveButton, False, False, 0)
        oVBox.pack_start(oButtonBox, False, False, 0)

        oImportDialog.set_size_request(350 + self._iScale * CARD_DIM[0], 650)

        oImportDialog.show_all()
        oAbsCardView.set_existing(self._oImageFrame)
        oImportDialog.run()
        oImportDialog.destroy()

    def _draw_pdf_section(self, oDrawArea, _oEvent):
        oContext = oDrawArea.get_window().cairo_create()
        _iX, _iY, iWidth, iHeight = oDrawArea.get_window().get_geometry()
        self._render_pdf(oContext, iWidth, iHeight)

    def _render_pdf(self, oContext, iWidth, iHeight):
        """Render the card on the given cairo context"""
        oContext.set_source_rgb(0, 0, 0)
        oContext.rectangle(0, 0, iWidth, iHeight)
        oContext.fill()
        if self._oPageImg:
            iPageX = START[0] + self._iXOffset + self._iXPos * CARD_DIM[0]
            iPageX = iPageX * self._iScale
            iPageY = START[1] + self._iYOffset + self._iYPos * CARD_DIM[1]
            iPageY = iPageY * self._iScale
            oContext.set_source_surface(self._oPageImg, -iPageX, -iPageY)
            oContext.rectangle(0, 0, self._iScale * CARD_DIM[0],
                               self._iScale * CARD_DIM[1])
            oContext.fill()

    def _update_offsets(self, _oBut, oDrawArea):
        """Update the offsets and reload the pdf image."""
        self._iXOffset = self._oXOffset.get_value()
        self._iYOffset = self._oYOffset.get_value()
        self._iXSize = self._oXScale.get_value()
        self._iYSize = self._oYScale.get_value()
        self._load_page()
        self._draw_pdf_section(oDrawArea, None)

    def _load_page(self):
        """Load the page to a cairo surface"""
        # pylint: disable=no-member
        # cairo confuses pylint
        oCurPage = self._oDocument.get_page(self._iCurPageNo)
        fWidth, fHeight = oCurPage.get_size()
        iWidth = self._iScale * int(fWidth)
        iHeight = self._iScale * int(fHeight)
        self._oPageImg = cairo.ImageSurface(cairo.FORMAT_ARGB32,
                                            iWidth, iHeight)
        oPageContext = cairo.Context(self._oPageImg)
        # We scale the input pdf so that (self._iXSize, self._iYSize) sections
        # are scaled to requested output size
        fXScale = self._iScale * float(CARD_DIM[0]) / self._iXSize
        fYScale = self._iScale * float(CARD_DIM[1]) / self._iYSize
        oPageContext.scale(fXScale, fYScale)
        # Fill background with white
        oPageContext.set_source_rgb(1, 1, 1)
        oPageContext.rectangle(0, 0, iWidth, iHeight)
        oPageContext.fill()
        # Paint in the pdf page
        oCurPage.render(oPageContext)

    def save_img(self, _oBut, oDrawArea, oAbsView, aExp):
        """Save the image we extracted from the PDF."""
        # Get the card from the model, to avoid encoding issues
        oAbsCard = oAbsView.get_selected_abstract_card()
        if oAbsCard is None:
            do_complaint_error("No Card selected")
            return
        sFileName = lookup_card(oAbsCard, aExp, self._oImageFrame)
        if not sFileName:
            return
        if check_file(sFileName):
            iRes = do_complaint_buttons(
                "File %s exists. Do You want to replace it?" % sFileName,
                Gtk.MessageType.QUESTION,
                ("Yes", Gtk.ResponseType.YES,
                 "No", Gtk.ResponseType.NO))
            if iRes == Gtk.ResponseType.NO:
                return
        # Actually save the image
        ensure_dir_exists(os.path.dirname(sFileName))
        oPixbuf = Gdk.pixbuf_get_from_window(oDrawArea.get_window(), 0, 0,
                                             self._iScale * CARD_DIM[0],
                                             self._iScale * CARD_DIM[1])
        oPixbuf.savev(sFileName, "jpeg", ("quality",), ("98",))
        # Mark the card as used
        oAbsView.set_selected_used()
        # Advance to the next image
        self.chg_img(None, oDrawArea, +1)

    def chg_img(self, _oBut, oDrawArea, iChg):
        """Change to the next / prev image in the PDF."""
        iOldPage = iNewPage = self._iCurPageNo
        iYPos = self._iYPos
        iXPos = self._iXPos + iChg
        if iXPos >= 3:
            iYPos += 1
            iXPos = 0
        elif iXPos < 0:
            iYPos -= 1
            iXPos = 2
        if iYPos >= 3:
            iNewPage += 1
            iXPos = 0
            iYPos = 0
        elif iYPos < 0:
            iNewPage -= 1
            iXPos = 2
            iYPos = 2
        if iNewPage < 0 or iNewPage >= self._iNumPages:
            # Exceed the document limits, so bail with doing anything
            return
        self._iCurPageNo = iNewPage
        self._iXPos = iXPos
        self._iYPos = iYPos
        if iNewPage != iOldPage:
            # Changed page
            self._load_page()
        # Force redraw
        if (self._iCurPageNo == self._iNumPages - 1 and
                self._iXPos == 2 and self._iYPos == 2):
            self._oNextButton.set_sensitive(False)
        else:
            self._oNextButton.set_sensitive(True)
        if (self._iCurPageNo == 0 and
                self._iXPos == 0 and self._iYPos == 0):
            self._oPrevButton.set_sensitive(False)
        else:
            self._oPrevButton.set_sensitive(True)
        self._draw_pdf_section(oDrawArea, None)


plugin = ImportPDFImagesPlugin
