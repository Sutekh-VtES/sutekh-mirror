# CardDrawSimluator.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Dialog to display deck analysis software
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>,
# GPL - see COPYING for details
"""
Calculate probailibities for drawing the current selection
"""

import gtk
from copy import copy
from sutekh.core.SutekhObjects import PhysicalCardSet, AbstractCardSet, \
        IAbstractCard
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow


def choose(iChoices, iTotal):
    """
    Returns number of unordered combinations of iChoices objects from iTotal
      (iTotal)(iTotal-1)...(iTotal-iChoices+1)/iChoices!
    """
    if iChoices > 0:
        iDenom = iChoices
    else:
        return 1 # 0!/0! = 1, since 0! = 1
    iNumerator = iTotal
    for iNum in range(1, iChoices):
        iNumerator *= (iTotal - iNum)
        iDenom *= iNum
    return iNumerator / iDenom

def gen_choice_list(dSelectedCounts):
    """Recursively generate all possible choices"""
    aList = []
    aSelectOrder = sorted(dSelectedCounts.items(), key=lambda x: (x[1], x[0]),
            reverse=True)
    sThisItem = aSelectOrder[0][0]
    if len(dSelectedCounts) > 1:
        dNew = copy(dSelectedCounts)
        del dNew[sThisItem]
        aSubLists = gen_choice_list(dNew)
        for iChoice in range(dSelectedCounts[sThisItem]+1):
            for aChoices in aSubLists:
                aThisList = [iChoice]
                aThisList.extend(aChoices)
                aList.append(aThisList)
    else:
        aList = [[x] for x in range(dSelectedCounts[sThisItem]+1)]
    return aList

def multi_hyper_prob(aFound, iDraws, aObjects, iTotal):
    """
    Multivariate hypergeometric probability:
    Given a list of draw numbers: aFound = [iFound1, iFound2 ... iFoundN]
    form aObjects = [iObjects1, iObjects2 ... iObjectsN]
    return the probably of seeing exactly aFound from iDraws
    """
    # Complain about impossible cases
    if len(aFound) != len(aObjects):
        raise RuntimeError('Invalid input: aFound : %s, aObjects: %s' % (
            ','.join([str(x) for x in aFound]), ','.join([str(x) for x in
                aObjects])))
    if sum(aFound) < 0 or min(aFound) < 0 or sum(aObjects) < 0 or \
            iTotal <= 0 or iDraws <= 0 or min(aObjects) < 0 or \
            sum(aObjects) > iTotal or iDraws > iTotal:
        raise RuntimeError('Invalid values for multivariate hypergeomtric'
                ' probability calculation: aFound: %s iDraws: %d'
                ' aObjects: %s iTotal: %d' % (','.join([str(x) for x in
                    aFound]), iDraws, ','.join([str(x) for x in aObjects]),
                    iTotal))
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
    fDemon = float(choose(iDraws, iTotal))
    # Ensure we handle last entry
    iRemObjects = iTotal - sum(aObjects)
    iRemFound = iDraws - sum(aFound)
    fNumerator = 1.0
    for iFound, iObjects in zip(aFound, aObjects):
        fNumerator *= choose(iFound, iObjects)
    if iRemFound > 0 and iRemObjects > 0:
        fNumerator *= choose(iRemFound, iRemObjects)
    return fNumerator / fDemon

def hyper_prob_at_least(aFound, iDraws, aObjects, iTotal, iCurCol=0):
    """
    Returns the probablity of drawing at least aFound from aObjects objects
    of interest from iTotal objects in iDraw draws
    """
    # This is the sum of hyper_prob(iCur, Draws, iObjects, iTotal) where
    # iCur in [iFound, min(iDraws, iObjects)]
    if len(aFound) != len(aObjects):
        raise RuntimeError('Invalid input: aFound : %s, aObjects: %s' % (
            ','.join([str(x) for x in aFound]), ','.join([str(x) for x in
                aObjects])))
    fProb = 0
    aThisFound = copy(aFound)
    for iCur in range(aFound[iCurCol], min(iDraws, aObjects[iCurCol]) + 1):
        aThisFound[iCurCol] = iCur
        if iCurCol < len(aFound) - 1:
            fProb += hyper_prob_at_least(aThisFound, iDraws,
                    aObjects, iTotal, iCurCol + 1)
        else:
            fProb += multi_hyper_prob(aThisFound, iDraws, aObjects, iTotal)
    return fProb

class CardDrawSimPlugin(CardListPlugin):
    """
    Displays the probabilities for drawing cards from the current selection
    """
    dTableVersions = {PhysicalCardSet : [3, 4],
            AbstractCardSet : [3]}
    aModelsSupported = [PhysicalCardSet,
            AbstractCardSet]

    def get_menu_item(self):
        """Overrides method from base class."""
        if not self.check_versions() or not self.check_model_type():
            return None
        iCardDraw = gtk.MenuItem("Card Draw probabilities")
        iCardDraw.connect("activate", self.activate)
        return iCardDraw

    def get_desired_menu(self):
        """Menu to associate with"""
        return "Plugins"

    # pylint: disable-msg=W0613, W0201
    # W0613 - oWidget has to be here, although it's unused
    # W0201 - we define lots of things here, rather than __init__, since this
    # is the plugin's entry point, and they need to reflect the current state
    def activate(self, oWidget):
        """Create the actual dialog, and populate it."""
        sDiagName = "Card Draw probablities"
        self.iTotal = 0
        self.dSelectedCounts = {}
        self.iSelectedCount = 0

        # Get currently selected cards
        aSelectedCards, bCrypt, bLibrary = self._get_selected_cards()

        if len(aSelectedCards) == 0:
            do_complaint_error("No cards selected")
            return

        # Check that selection doesn't mix crypt and libraries
        if bLibrary and bCrypt:
            do_complaint_error("Can't operate on selections including both"
                    " Crypt and Library cards")
            return

        self._setup_cardlists(aSelectedCards, bCrypt)

        oMainTitle = gtk.Label()
        if bCrypt:
            oMainTitle.set_markup('<b>Crypt:</b> Drawing from <b>%d</b>'
                    'cards' % self.iTotal)
            self.iOpeningDraw = 4
            self.iNumSteps = min(2, self.iTotal - self.iOpeningDraw)
        else:
            oMainTitle.set_markup('<b>Library:</b> Drawing from <b>%d</b>'
                    'cards' % self.iTotal)
            self.iOpeningDraw = 7
            # Look 15 cards into the deck by default, seems good start
            self.iNumSteps = min(8, self.iTotal - self.iOpeningDraw)
        self.iMax = min(15, self.iTotal - self.iOpeningDraw)
        self.iDrawStep = 1 # Increments to use in table
        self.aAllChoices = gen_choice_list(self.dSelectedCounts)
        self.iCardsToDraw = min(10, len(self.aAllChoices))

        if self.iTotal <= self.iOpeningDraw:
            if bLibrary:
                do_complaint_error("Library must be larger than the opening"
                        "hand")
            else:
                do_complaint_error("Crypt must be larger than"
                        " the opening draw")
            return

        oDialog = SutekhDialog(sDiagName, self.parent,
                gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK))
        oDialog.connect("response", lambda oDialog, resp: oDialog.destroy())

        oWidgetBox = gtk.HBox(False, 2)
        oNumDraws = gtk.combo_box_new_text()
        iIndex = 0
        for iNum in range(1, self.iMax + 1):
            oNumDraws.append_text(str(iNum))
            if iNum < self.iNumSteps:
                iIndex += 1
        oNumDraws.set_active(iIndex)
        oNumDraws.connect('changed', self._cols_changed)

        oStepSize = gtk.combo_box_new_text()
        for iNum in range(1, 11):
            oStepSize.append_text(str(iNum))
        oStepSize.set_active(0)
        oStepSize.connect('changed', self._steps_changed)

        iIndex = 0
        oCardToDrawCount = gtk.combo_box_new_text()
        for iNum in range(1, len(self.aAllChoices) + 1):
            oCardToDrawCount.append_text(str(iNum))
            if iNum < self.iCardsToDraw:
                iIndex += 1
        oCardToDrawCount.set_active(iIndex)
        oCardToDrawCount.connect('changed', self._rows_changed)

        oRecalcButton = gtk.Button('recalculate table')

        oRecalcButton.connect('clicked', self._fill_table, bCrypt)

        oWidgetBox.pack_start(gtk.Label('columns in table : '))
        oWidgetBox.pack_start(oNumDraws)
        oWidgetBox.pack_start(gtk.Label(' Step between columns : '))
        oWidgetBox.pack_start(oStepSize)
        oWidgetBox.pack_start(gtk.Label(' rows in table : '))
        oWidgetBox.pack_start(oCardToDrawCount)
        oWidgetBox.pack_start(gtk.Label(' : '))
        oWidgetBox.pack_start(oRecalcButton)

        self.oResultsBox = gtk.VBox(False, 2)

        oDescLabel = gtk.Label("Columns are number of draws (X)\n"
                "rows are the number of cards (Y)\n"
                "For the first row (0 cards), the entry is the possiblity of"
                "Not drawing any of the selected cards by the X'th draw\n"
                "For the other rows, the entries are the probability of "
                "seeing at least the list number of cards from the selection\n"
                "by the X\'th draw with the number in brackets being the "
                "probablity of seeing eactly the listed cards\n"
                "The first column represents the opening hand or crypt draw")

        oTitleLabel = gtk.Label('Draw results :')
        self.oResultsBox.pack_start(oTitleLabel, False, False)

        # pylint: disable-msg=E1101
        # pylint doesn't detect gtk methods correctly

        self.oResultsTable = gtk.Table()
        self.oResultsBox.pack_start(AutoScrolledWindow(self.oResultsTable,
            True))

        oDialog.vbox.pack_start(oMainTitle, False, False)
        oDialog.vbox.pack_start(gtk.Label('Card Probablities'), False, False)
        oDialog.vbox.pack_start(oDescLabel, False, False)
        oDialog.vbox.pack_start(oWidgetBox, False, False)
        oDialog.vbox.pack_start(self.oResultsBox)
        self._fill_table(self, bCrypt)
        oDialog.set_size_request(800, 600)
        oDialog.show_all()

        oDialog.run()
    # pylint: enable-msg=W0613, W0201

    def _setup_cardlists(self, aSelectedCards, bCrypt):
        """Extract the needed card info from the model"""
        aAllCards = list(self.model.getCardIterator(None))
        aAllAbsCards = [IAbstractCard(oCard) for oCard in aAllCards]
        iCryptSize = 0
        iLibrarySize = 0
        self.dSelectedCounts = {}
        self.iSelectedCount = 0
        for oCard in aAllAbsCards:
            aTypes = [oType.name for oType in oCard.cardtype]
            if aTypes[0] == 'Vampire' or aTypes[0] == 'Imbued':
                iCryptSize += 1
            else:
                iLibrarySize += 1
            if oCard in aSelectedCards:
                self.dSelectedCounts.setdefault(oCard, 0)
                self.dSelectedCounts[oCard] += 1
                self.iSelectedCount += 1
            # The assumption is that the user is interested in all copies of
            # the selected cards (as it seems the most useful), so we treat
            # the selection of any instance of the card in the list as
            # selecting all of them
        if bCrypt:
            self.iTotal = iCryptSize
        else:
            self.iTotal = iLibrarySize

    def _get_selected_cards(self):
        """Extract selected cards from the selection."""
        aSelectedCards = []
        bCrypt = False
        bLibrary = False
        # pylint: disable-msg=W0612
        # oModel will be unused
        oModel, aSelection = self.view.get_selection().get_selected_rows()
        for oPath in aSelection:
            # pylint: disable-msg=E1101
            # pylint doesn't pick up adaptor's methods correctly
            oCard = IAbstractCard(self.model.getCardNameFromPath(oPath))
            aTypes = [oType.name for oType in oCard.cardtype]
            if aTypes[0] == 'Vampire' or aTypes[0] == 'Imbued':
                bCrypt = True
            else:
                bLibrary = True
            aSelectedCards.append(oCard)

        return aSelectedCards, bCrypt, bLibrary

    def _steps_changed(self, oComboBox):
        """Handle changes to the oStepSize combo box."""
        self.iDrawStep = int(oComboBox.get_active_text())

    def _rows_changed(self, oComboBox):
        """Handle changes to the oCardToDrawCount combo box."""
        self.iCardsToDraw = int(oComboBox.get_active_text())

    def _cols_changed(self, oComboBox):
        """Handle changes to the oNumDraws combo box."""
        self.iNumSteps = int(oComboBox.get_active_text())

    # pylint: disable-msg=W0613
    # oWidget is dielibrately unused
    def _fill_table(self, oWidget, bCrypt):
        """Fill Results Box with the draw results.

           oWidget is a dummy placeholder so this method can be called by the
           'connect' signal.
           """
        # This is messy, but does the job
        for oChild in self.oResultsTable.get_children():
            self.oResultsTable.remove(oChild)
        aSelectOrder = sorted(self.dSelectedCounts.items(),
                key=lambda x: (x[1], x[0]), reverse=True)
        self.oResultsTable.resize(2*self.iCardsToDraw+5, 2*self.iNumSteps+3)
        self.oResultsTable.set_col_spacings(0)
        self.oResultsTable.set_row_spacings(0)
        oTopLabel = gtk.Label('Cards drawn')
        oLeftLabel = gtk.Label('Number of cards seen')
        oLeftLabel.set_angle(270)
        self.oResultsTable.attach(oTopLabel, 0, 2*self.iNumSteps+4, 0, 1)
        self.oResultsTable.attach(oLeftLabel, 0, 1, 0, 2*self.iCardsToDraw+6)
        self.oResultsTable.attach(gtk.HSeparator(), 0, 2*self.iNumSteps+4, 1,
                2, xpadding=0, ypadding=0, xoptions=gtk.FILL,
                yoptions=gtk.FILL)
        self.oResultsTable.attach(gtk.VSeparator(), 1, 2, 1,
                2 * self.iCardsToDraw + 6, xpadding=0, ypadding=0,
                xoptions=gtk.FILL, yoptions=gtk.FILL)
        if bCrypt:
            oOpeningLabel = gtk.Label('Opening Draw')
        else:
            oOpeningLabel = gtk.Label('Opening Hand')
        self.oResultsTable.attach(gtk.VSeparator(), 3, 4, 2,
                2 * self.iCardsToDraw + 6, xpadding=0, ypadding=0,
                xoptions=gtk.FILL, yoptions=gtk.FILL)
        self.oResultsTable.attach(oOpeningLabel, 4, 5, 2, 3)
        for iCol in range(1, self.iNumSteps):
            oLabel = gtk.Label('+ %d' % (iCol * self.iDrawStep))
            self.oResultsTable.attach(gtk.VSeparator(), 2 * iCol + 3,
                    2 * iCol + 4, 2, 2*self.iCardsToDraw+6, xpadding=0,
                    ypadding=0, xoptions=gtk.FILL, yoptions=gtk.FILL)
            self.oResultsTable.attach(oLabel, 2 * iCol + 4, 2 * iCol + 5, 2, 3)
        for iRow in range(self.iCardsToDraw):
            oLabel = gtk.Label(self._gen_row_label(iRow, aSelectOrder))
            self.oResultsTable.attach(gtk.HSeparator(), 1,
                    2 * self.iNumSteps + 4, 2 * iRow + 3, 2 * iRow + 4,
                    xpadding=0, ypadding=0, xoptions=gtk.FILL,
                    yoptions=gtk.FILL)
            self.oResultsTable.attach(oLabel, 2, 3, 2 * iRow + 4, 2 * iRow + 5)
        # Fill in zero row
        for iCol in range(self.iNumSteps):
            iNumDraws = iCol * self.iDrawStep + self.iOpeningDraw
            if iNumDraws < self.iTotal:
                fProbExact = multi_hyper_prob([0], iNumDraws,
                        [self.iSelectedCount], self.iTotal)*100
                oResLabel = gtk.Label('%3.2f' % fProbExact)
            else:
                oResLabel = gtk.Label('all cards drawn')
            self.oResultsTable.attach(oResLabel, 2*iCol+4, 2*iCol+5, 4, 5)
        # Fill in other rows
        aCardCounts = [x[1] for x in aSelectOrder]
        for iRow in range(1, self.iCardsToDraw):
            aThisDraw = self._gen_draw(iRow)
            for iCol in range(self.iNumSteps):
                iNumDraws = iCol * self.iDrawStep + self.iOpeningDraw
                if iNumDraws < self.iTotal:
                    fProbExact = multi_hyper_prob(aThisDraw, iNumDraws,
                            aCardCounts, self.iTotal)*100
                    fProbAccum = hyper_prob_at_least(aThisDraw, iNumDraws,
                            aCardCounts, self.iTotal)*100
                    oResLabel = gtk.Label('%3.2f (%3.2f)' % (fProbAccum,
                        fProbExact))
                else:
                    oResLabel = gtk.Label('')
                self.oResultsTable.attach(oResLabel, 2*iCol+4, 2*iCol+5,
                        2*iRow+4, 2*iRow+5)
        self.oResultsTable.show_all()
    # pylint: enable-msg=W0613

    def _gen_draw(self, iRow):
        """Construct the card draw for the row"""
        return self.aAllChoices[iRow]

    def _gen_row_label(self, iRow, aSelectOrder):
        """Construct the label."""
        if iRow == 0:
            return '0 cards'
        aThisRow = self._gen_draw(iRow)
        sLabel = ''
        for oItem, iCount in zip(aSelectOrder, aThisRow):
            sLabel += u'%d \u00D7 %s\n' % (iCount, oItem[0].name)
        return sLabel

# pylint: disable-msg=C0103
# plugin name doesn't match, but ignore that
plugin = CardDrawSimPlugin
