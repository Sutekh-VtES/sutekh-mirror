# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Dialog to display deck analysis software
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>,
# GPL - see COPYING for details
"""Calculate probabilities for drawing the current selection."""

from copy import copy

from gi.repository import Gtk

from ...core.BaseTables import PhysicalCardSet
from ..BasePluginManager import BasePlugin
from ..SutekhDialog import (SutekhDialog, do_complaint_error,
                            do_complaint_warning)
from ..AutoScrolledWindow import AutoScrolledWindow


def _choose(iChoices, iTotal):
    """Returns number of unordered combinations of iChoices objects from
       iTotal (iTotal)(iTotal-1)...(iTotal-iChoices+1)/iChoices!"""
    if iChoices > 0:
        iDenom = iChoices
    else:
        return 1  # 0!/0! = 1, since 0! = 1
    iNumerator = iTotal
    for iNum in range(1, iChoices):
        iNumerator *= (iTotal - iNum)
        iDenom *= iNum
    return iNumerator // iDenom


def _gen_choice_list(dSelectedCounts):
    """Recursively generate all possible choices"""
    aList = []
    aSelectOrder = sorted(dSelectedCounts.items(), key=lambda x: (x[1], x[0]),
                          reverse=True)
    sThisItem = aSelectOrder[0][0]
    if len(dSelectedCounts) > 1:
        dNew = copy(dSelectedCounts)
        del dNew[sThisItem]
        aSubLists = _gen_choice_list(dNew)
        for iChoice in range(dSelectedCounts[sThisItem] + 1):
            for aChoices in aSubLists:
                aThisList = [iChoice]
                aThisList.extend(aChoices)
                aList.append(aThisList)
    else:
        aList = [[x] for x in range(dSelectedCounts[sThisItem] + 1)]
    aList.sort(key=lambda x: [sum(x)] + x)
    return aList


def _multi_hyper_prob(aFound, iDraws, aObjects, iTotal):
    """Multivariate hypergeometric probability:

       Given a list of draw numbers: aFound = [iFound1, iFound2 ... iFoundN]
       form aObjects = [iObjects1, iObjects2 ... iObjectsN]
       return the probably of seeing exactly aFound from iDraws
       """
    # Complain about impossible cases
    if len(aFound) != len(aObjects):
        raise RuntimeError('Invalid input: aFound : %s, aObjects: %s' % (
            ','.join([str(x) for x in aFound]),
            ','.join([str(x) for x in aObjects])))
    # pylint: disable=too-many-boolean-expressions
    # We do want to check all of these
    if sum(aFound) < 0 or min(aFound) < 0 or sum(aObjects) < 0 or \
            iTotal <= 0 or iDraws <= 0 or min(aObjects) < 0 or \
            sum(aObjects) > iTotal or iDraws > iTotal:
        raise RuntimeError('Invalid values for multivariate hypergeomtric'
                           ' probability calculation: aFound: %s iDraws: %d'
                           ' aObjects: %s iTotal: %d' % (
                               ','.join([str(x) for x in
                                         aFound]),
                               iDraws, ','.join([str(x) for x in aObjects]),
                               iTotal))
    # pylint: enable=too-many-boolean-expressions
    # Eliminate trivial cases
    if sum(aFound) > iDraws:
        return 0.0
    for iFound, iObjects in zip(aFound, aObjects):
        if iFound > iObjects:
            return 0.0
    # Hypergeomteric probability: P(X = iFound) = choose iFound from iObjects *
    #           choose (iDraws - iFound) from (iTotal - iObjects) /
    #           choose iDraws from iTotal
    # Multivariate: P(X_i = iFound[i]) = choose(iFound1, iObjects1) *
    #           choose(iFound2, iObject2) * ... / choose(iDraws, iTotal)
    fDemon = float(_choose(iDraws, iTotal))
    # Ensure we handle last entry
    iRemObjects = iTotal - sum(aObjects)
    iRemFound = iDraws - sum(aFound)
    fNumerator = 1.0
    for iFound, iObjects in zip(aFound, aObjects):
        fNumerator *= _choose(iFound, iObjects)
    if iRemFound > 0 and iRemObjects > 0:
        fNumerator *= _choose(iRemFound, iRemObjects)
    return fNumerator / fDemon


def _hyper_prob_at_least(aFound, iDraws, aObjects, iTotal, iCurCol=0):
    """Returns the probablity of drawing at least aFound from aObjects objects
       of interest from iTotal objects in iDraw draws."""
    # This is the sum of hyper_prob(iCur, Draws, iObjects, iTotal) where
    # iCur in [iFound, min(iDraws, iObjects)]
    if len(aFound) != len(aObjects):
        raise RuntimeError('Invalid input: aFound : %s, aObjects: %s' % (
            ','.join([str(x) for x in aFound]),
            ','.join([str(x) for x in aObjects])))
    fProb = 0
    aThisFound = copy(aFound)
    for iCur in range(aFound[iCurCol], min(iDraws, aObjects[iCurCol]) + 1):
        aThisFound[iCurCol] = iCur
        if iCurCol < len(aFound) - 1:
            fProb += _hyper_prob_at_least(aThisFound, iDraws,
                                          aObjects, iTotal, iCurCol + 1)
        else:
            fProb += _multi_hyper_prob(aThisFound, iDraws, aObjects, iTotal)
    return fProb


class BaseDrawProbPlugin(BasePlugin):
    """Displays the probabilities for drawing cards from the current
       selection."""
    # pylint: disable=too-many-instance-attributes
    # we use a lot of attributes to pass the data around
    dTableVersions = {PhysicalCardSet: (4, 5, 6, 7)}
    aModelsSupported = (PhysicalCardSet,)

    sMenuName = "Card Draw probabilities"

    sHelpCategory = "card_sets:analysis"

    sHelpText = """Handle the probabilty of drawing cards.
                   Subclasses should override this with the
                   exact details of the game."""

    def get_menu_item(self):
        """Register on the 'Analyze' menu"""
        oCardDraw = Gtk.MenuItem(label=self.sMenuName)
        oCardDraw.connect("activate", self.activate)
        return ('Analyze', oCardDraw)

    # pylint: disable=attribute-defined-outside-init
    # we define lots of things here, rather than __init__, since this
    # is the plugin's entry point, and they need to reflect the current state
    def activate(self, _oWidget):
        """Create the actual dialog, and populate it."""
        if not self._check_cs_size('Card Draw probabilities', 500):
            return

        self.iTotal = 0
        self.dSelectedCounts = {}
        self.iSelectedCount = 0
        self.iOpeningDraw = 0

        # Get currently selected cards
        aSelectedCards = self._get_selected_abs_cards()

        if not aSelectedCards:
            do_complaint_error("No cards selected")
            return

        # Check that selection is acceptable
        if not self._check_selection(aSelectedCards):
            return

        self._setup_cardlists(aSelectedCards)

        # Query user if we have zero counts
        if 0 in self.dSelectedCounts.values():
            iRes = do_complaint_warning("Selected cards include cards with"
                                        " a count of 0.\n"
                                        "Do you want to continue?")
            if iRes == Gtk.ResponseType.CANCEL:
                return

        oMainTitle = Gtk.Label()
        self._set_draw_title_and_size(oMainTitle)

        # Look 15 cards into the deck by default, seems good start
        self.iMax = min(15, self.iTotal - self.iOpeningDraw)
        self.iDrawStep = 1  # Increments to use in table
        self.aAllChoices = _gen_choice_list(self.dSelectedCounts)
        self.iCardsToDraw = min(3, self.iSelectedCount)

        if self.iTotal <= self.iOpeningDraw:
            self._complain_size()
            return

        self.oResultsTable = Gtk.Table()
        oDialog = self._make_dialog(oMainTitle)
        self._fill_table(self)
        oDialog.set_size_request(800, 600)
        oDialog.show_all()

        oDialog.run()

    def _make_dialog(self, oMainTitle):
        """Create the dialog box."""
        oDialog = SutekhDialog("Card Draw probablities", self.parent,
                               Gtk.DialogFlags.DESTROY_WITH_PARENT,
                               ("_Close", Gtk.ResponseType.CLOSE))
        oDialog.connect("response", lambda oDialog, resp: oDialog.destroy())

        oWidgetBox = Gtk.HBox(False, 2)
        oNumDraws = Gtk.ComboBoxText()
        iIndex = 0
        for iNum in range(1, self.iMax + 1):
            oNumDraws.append_text(str(iNum))
            if iNum < self.iNumSteps:
                iIndex += 1
        oNumDraws.set_active(iIndex)
        oNumDraws.connect('changed', self._cols_changed)

        oStepSize = Gtk.ComboBoxText()
        for iNum in range(1, 11):
            oStepSize.append_text(str(iNum))
        oStepSize.set_active(0)
        oStepSize.connect('changed', self._steps_changed)

        iIndex = 0
        oCardToDrawCount = Gtk.ComboBoxText()
        for iNum in range(1, self.iSelectedCount + 1):
            oCardToDrawCount.append_text(str(iNum))
            if iNum < self.iCardsToDraw:
                iIndex += 1
        oCardToDrawCount.set_active(iIndex)
        oCardToDrawCount.connect('changed', self._rows_changed)

        oRecalcButton = Gtk.Button('recalculate table')

        oRecalcButton.connect('clicked', self._fill_table)

        oWidgetBox.pack_start(Gtk.Label('columns in table : '),
                              True, True, 0)
        oWidgetBox.pack_start(oNumDraws, True, True, 0)
        oWidgetBox.pack_start(Gtk.Label(' Step between columns : '),
                              True, True, 0)
        oWidgetBox.pack_start(oStepSize, True, True, 0)
        oWidgetBox.pack_start(Gtk.Label(' cards of interest : '),
                              True, True, 0)
        oWidgetBox.pack_start(oCardToDrawCount, True, True, 0)
        oWidgetBox.pack_start(Gtk.Label(' : '), True, True, 0)
        oWidgetBox.pack_start(oRecalcButton, True, True, 0)

        oDescLabel = Gtk.Label(label="Columns are number of draws (X)\n"
                               "rows are the number of cards (Y)\n"
                               "For the first row (0 cards), the "
                               "entry is the possiblity of "
                               "not drawing any of the selected cards "
                               "by the X'th draw\n"
                               "For the other rows, the entries are the "
                               "probability of seeing at least the listed "
                               "cards from the selection\n"
                               "by the X\'th draw with the number in "
                               "brackets being the probablity of seeing "
                               "exactly the listed cards\n"
                               "The first column represents the total "
                               "starting draw")

        oTitleLabel = Gtk.Label('Draw results :')
        oResultsBox = Gtk.VBox(homogeneous=False, spacing=2)
        oResultsBox.pack_start(oTitleLabel, False, False, 0)

        oResultsBox.pack_start(AutoScrolledWindow(self.oResultsTable),
                               True, True, 0)

        oDialog.vbox.pack_start(oMainTitle, False, False, 0)
        oDialog.vbox.pack_start(Gtk.Label('Card Probablities'),
                                False, False, 0)
        oDialog.vbox.pack_start(oDescLabel, False, False, 0)
        oDialog.vbox.pack_start(oWidgetBox, False, False, 0)
        oDialog.vbox.pack_start(oResultsBox, True, True, 0)
        return oDialog

    def _steps_changed(self, oComboBox):
        """Handle changes to the oStepSize combo box."""
        self.iDrawStep = int(oComboBox.get_active_text())

    def _rows_changed(self, oComboBox):
        """Handle changes to the oCardToDrawCount combo box."""
        self.iCardsToDraw = int(oComboBox.get_active_text())

    def _cols_changed(self, oComboBox):
        """Handle changes to the oNumDraws combo box."""
        self.iNumSteps = int(oComboBox.get_active_text())

    def _fill_table(self, _oWidget):
        """Fill Results Box with the draw results.

           oWidget is a dummy placeholder so this method can be called by the
           'connect' signal.
           """
        # This is messy, but does the job
        iNumCardRows = len([sum(x) for x in self.aAllChoices if
                            sum(x) <= self.iCardsToDraw])
        iNumRows = 2 * iNumCardRows + 5
        if len(self.aAllChoices[0]) > 1:
            iNumCols = 2 * self.iNumSteps + 5
            iOffset = 2
        else:
            iNumCols = 2 * self.iNumSteps + 3
            iOffset = 0
        self._setup_table(iNumRows, iNumCols)
        if iOffset > 0:
            self.oResultsTable.attach(Gtk.VSeparator(), 3, 4, 2, iNumRows,
                                      xpadding=0, ypadding=0,
                                      xoptions=Gtk.AttachOptions.FILL,
                                      yoptions=Gtk.AttachOptions.FILL)
            oLabel = Gtk.Label('Count')
            self.oResultsTable.attach(oLabel, 2, 3, 2, 3)
            self._setup_count_rows()
        self.oResultsTable.attach(self._get_table_draw_title(),
                                  4 + iOffset, 5 + iOffset, 2, 3)
        self.oResultsTable.attach(Gtk.HSeparator(), iOffset, iNumCols,
                                  1, 2, xpadding=0, ypadding=0,
                                  xoptions=Gtk.AttachOptions.FILL,
                                  yoptions=Gtk.AttachOptions.FILL)
        self.oResultsTable.attach(Gtk.VSeparator(), 1, 2, 1, iNumRows,
                                  xpadding=0, ypadding=0,
                                  xoptions=Gtk.AttachOptions.FILL,
                                  yoptions=Gtk.AttachOptions.FILL)
        self.oResultsTable.attach(Gtk.VSeparator(), 3 + iOffset, 4 + iOffset,
                                  2, iNumRows, xpadding=0, ypadding=0,
                                  xoptions=Gtk.AttachOptions.FILL,
                                  yoptions=Gtk.AttachOptions.FILL)
        for iCol in range(1, self.iNumSteps):
            oLabel = Gtk.Label('+ %d' % (iCol * self.iDrawStep))
            iTableCol = 2 * iCol + 3 + iOffset
            self.oResultsTable.attach(Gtk.VSeparator(), iTableCol,
                                      iTableCol + 1, 2, iNumRows,
                                      xpadding=0, ypadding=0,
                                      xoptions=Gtk.AttachOptions.FILL,
                                      yoptions=Gtk.AttachOptions.FILL)
            self.oResultsTable.attach(oLabel, iTableCol + 1, iTableCol + 2,
                                      2, 3)

        aSelectOrder = sorted(self.dSelectedCounts.items(),
                              key=lambda x: (x[1], x[0]), reverse=True)
        for iRow in range(iNumCardRows):
            oLabel = Gtk.Label(self._gen_row_label(iRow, aSelectOrder))
            iTableRow = 2 * iRow + 3
            self.oResultsTable.attach(Gtk.HSeparator(), 1 + iOffset,
                                      iNumCols, iTableRow, iTableRow + 1,
                                      xpadding=0, ypadding=0,
                                      xoptions=Gtk.AttachOptions.FILL,
                                      yoptions=Gtk.AttachOptions.FILL)
            self.oResultsTable.attach(oLabel, 2 + iOffset, 3 + iOffset,
                                      iTableRow + 1, iTableRow + 2)
        # Fill in zero row
        aCardCounts = [x[1] for x in aSelectOrder]
        self._fill_row(0, iOffset, True, aCardCounts)
        # Fill in other rows
        for iRow in range(1, iNumCardRows):
            self._fill_row(iRow, iOffset, False, aCardCounts)
        self.oResultsTable.show_all()

    def _setup_table(self, iNumRows, iNumCols):
        """Clear the table, and setup constant entries."""
        for oChild in self.oResultsTable.get_children():
            self.oResultsTable.remove(oChild)
        self.oResultsTable.resize(iNumRows, iNumCols)
        self.oResultsTable.set_col_spacings(0)
        self.oResultsTable.set_row_spacings(0)
        oTopLabel = Gtk.Label('Cards drawn')
        oLeftLabel = Gtk.Label('Number of cards seen')
        oLeftLabel.set_angle(270)
        self.oResultsTable.attach(oTopLabel, 0, iNumCols, 0, 1)
        self.oResultsTable.attach(oLeftLabel, 0, 1, 1, iNumRows)

    def _setup_count_rows(self):
        """Fill in the cumulative count rows."""
        iBottomRow = 3
        for iCardRow in range(self.iCardsToDraw + 1):
            self.oResultsTable.attach(Gtk.HSeparator(), 1, 3, iBottomRow,
                                      iBottomRow + 1, xpadding=0, ypadding=0,
                                      xoptions=Gtk.AttachOptions.FILL,
                                      yoptions=Gtk.AttachOptions.FILL)
            oLabel = Gtk.Label('%d' % iCardRow)
            iNumRows = len([x for x in self.aAllChoices if
                            sum(x) == iCardRow])
            iTopRow = iBottomRow + 2 * iNumRows
            self.oResultsTable.attach(oLabel, 2, 3, iBottomRow + 1, iTopRow)
            iBottomRow = iTopRow

    def _fill_row(self, iRow, iOffset, bZero, aCardCounts):
        """Fill a single row of the results table"""
        iTableRow = 2 * iRow + 4
        aThisDraw = self._gen_draw(iRow)
        for iCol in range(self.iNumSteps):
            iNumDraws = iCol * self.iDrawStep + self.iOpeningDraw
            if iNumDraws < self.iTotal:
                fProbExact = _multi_hyper_prob(aThisDraw, iNumDraws,
                                               aCardCounts,
                                               self.iTotal) * 100
                if not bZero:
                    fProbAccum = _hyper_prob_at_least(aThisDraw, iNumDraws,
                                                      aCardCounts,
                                                      self.iTotal) * 100
                    oResLabel = Gtk.Label('%3.2f (%3.2f)' % (fProbAccum,
                                                             fProbExact))
                else:
                    oResLabel = Gtk.Label('%3.2f' % fProbExact)
            else:
                if bZero:
                    oResLabel = Gtk.Label('all cards drawn')
                else:
                    oResLabel = Gtk.Label('')
            iTableCol = 2 * iCol + 4 + iOffset
            self.oResultsTable.attach(oResLabel, iTableCol, iTableCol + 1,
                                      iTableRow, iTableRow + 1)

    def _gen_draw(self, iRow):
        """Construct the card draw for the row"""
        return self.aAllChoices[iRow]

    def _gen_row_label(self, iRow, aSelectOrder):
        """Construct the label."""
        if iRow == 0:
            return 'None of the cards'
        aThisRow = self._gen_draw(iRow)
        sLabel = ''
        for oItem, iCount in zip(aSelectOrder, aThisRow):
            sLabel += u'%d \u00D7 %s\n' % (iCount, oItem[0].name)
        return sLabel

    # subclasses will override these to do the right thing for the card game
    def _check_selection(self, aSelectedCards):
        """Check that the selection is suitable.
           Return False if the list can't be used, True if it's acceptable"""
        raise NotImplementedError("Implement _check_selection")

    def _setup_cardlists(self, aSelectedCards):
        """Extract infomation from model and conver selection into format
           sutaible for the statistical tools.

           Fills in the dSelectedCounts dictionary and sets
           iSelectedCount and iTotal correctly."""
        raise NotImplementedError("Implement _setup_cardlists")

    def _get_table_draw_title(self):
        """Provide the correct title for the results table dialog"""
        raise NotImplementedError("Implement _get_table_draw_title")

    def _set_draw_title_and_size(self, oMainTitle):
        """Set draw size and add details of the draw in the dialog"""
        raise NotImplementedError("Implement _set_draw_title_and_size")

    def _complain_size(self):
        """Suitable complaint if the deck we're drawing from is too small"""
        raise NotImplementedError("Implement _complain_size")
