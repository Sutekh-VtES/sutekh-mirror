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
    for iNum in range(1,iChoices):
        iNumerator *= (iTotal - iNum)
        iDenom *= iNum
    return iNumerator / iDenom

def hyper_prob(iFound, iDraws, iObjects, iTotal):
    """
    Returns the probablity of drawing exactly iFound from iObjects objects of
    interest from iTotal objects in iDraw draws
    """
    # Complain about impossible cases
    if iObjects <= 0 or iFound < 0 or iTotal <= 0 or iDraws <= 0 or \
            iObjects > iTotal or iDraws > iTotal:
        raise RuntimeError('Invalid values for hypergeomtric probability'
                'calculation: iFound: %d iDraws: %d iObjects: %d iTotal: %d' % (
                    iFound, iDraws, iObjects, iTotal))
    # Eliminate trivial cases
    if iFound > iDraws:
        return 0.0
    if iFound > iObjects:
        return 0.0
    # Hypergeomtric probability: P(X = iFound) = choose iFound from iObjects *
    #           choose (iDraws - iFound) from (iTotal - iObjects) /
    #           choose iDraws from iTotal
    return choose(iFound, iObjects) * choose(iDraws - iFound, iTotal - iObjects) \
            / float(choose(iDraws, iTotal))

def hyper_prob_at_least(iFound, iDraws, iObjects, iTotal):
    """
    Returns the probablity of drawing at lieast iFound from iObjects objects
    of interest from iTotal objects in iDraw draws
    """
    # This is the sum of hyper_prob(iCur, Draws, iObjects, iTotal) where
    # iCur in [iFound, min(iDraws, iObjects)]
    fProb = 0
    for iCur in range(iFound, min(iDraws, iObjects)+1):
        fProb += hyper_prob(iCur, iDraws, iObjects, iTotal)
    return fProb

class CardDrawSimPlugin(CardListPlugin):
    """
    Plugin to analyze card sets.
    Displays various interesting stats, and does
    a Happy Family analysis of the deck
    """
    dTableVersions = {PhysicalCardSet : [3, 4],
            AbstractCardSet : [3]}
    aModelsSupported = [PhysicalCardSet,
            AbstractCardSet]

    def get_menu_item(self):
        """
        Overrides method from base class.
        """
        if not self.check_versions() or not self.check_model_type():
            return None
        iCardDraw = gtk.MenuItem("Card Draw simulator")
        iCardDraw.connect("activate", self.activate)
        return iCardDraw

    def get_desired_menu(self):
        "Menu to associate with"
        return "Plugins"

    def activate(self, oWidget):
        "Create the actual dialog, and populate it"
        sDiagName = "Card Draw probablities"
        sCSName = self.view.sSetName
        bCrypt = False
        bLibrary = False

        # Get currently selected cards
        oModel, aSelection = self.view.get_selection().get_selected_rows()
        aSelectedCards = []
        for oPath in aSelection:
            oCard = IAbstractCard(self.model.getCardNameFromPath(oPath))
            aTypes = [oType.name for oType in oCard.cardtype]
            if aTypes[0] == 'Vampire' or aTypes[0] == 'Imbued':
                bCrypt = True
            else:
                bLibrary = True
            aSelectedCards.append(oCard)

        if len(aSelection) == 0:
            do_complaint_error("No cards selected")
            return

        # Check that selection doesn't mix crypt and libraries
        if bLibrary and bCrypt:
            do_complaint_error("Can't operate on selections including both"
                    " Crypt and Library cards")
            return

        # setup
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
            # The assumption is that the user is interested in all copies of the
            # selected cards (as it seems the most useful), so we treat the
            # selection of any instance of the card in the list as selecting
            # all of them

        oMainTitle = gtk.Label()
        if bCrypt:
            oMainTitle.set_markup('<b>Crypt:</b> Drawing from <b>%d</b> cards' % iCryptSize)
            self.iOpeningDraw = 4
            self.iTotal = iCryptSize
            self.iNumSteps = min(2, iCryptSize-self.iOpeningDraw)
        else:
            oMainTitle.set_markup('<b>Library:</b> Drawing from <b>%d</b> cards' % iLibrarySize)
            self.iOpeningDraw = 7
            self.iNumSteps = min(8, iLibrarySize-self.iOpeningDraw) # Look 15 cards into the deck, seems good start
            self.iTotal = iLibrarySize
        self.iMax = min(15, self.iTotal-self.iOpeningDraw)
        self.iDrawStep = 1 # Increments to use in table
        self.iCardsToDraw = min(10, self.iSelectedCount)

        if self.iTotal <= self.iOpeningDraw:
            if bLibrary:
                do_complaint_error("Library must be larger than the opening hand")
            else:
                do_complaint_error("Crypt must be larger than the opening draw")
            return

        dlg = SutekhDialog(sDiagName, self.parent,
                gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK))
        dlg.connect("response", lambda dlg, resp: dlg.destroy())

        aNames = [x.name for x in self.dSelectedCounts]
        oProbLabel = gtk.Label()
        if len(aNames) > 1:
            oProbLabel.set_markup('Probablities of selecting any of: '
                    '<i>%s</i> (%d cards)' % (
                        "; ".join(aNames), self.iSelectedCount))
        else:
            oProbLabel.set_markup('Probablity of selecting <i>%s</i> '
                    '(%d cards)' % (aNames[0], self.iSelectedCount))
        oProbLabel.set_line_wrap(True)
        oProbLabel.set_size_request(600, -1)

        oWidgetBox = gtk.HBox(False, 2)
        oNumDraws = gtk.combo_box_new_text()
        iIndex = 0
        for iNum in range(1,self.iMax + 1):
            oNumDraws.append_text(str(iNum))
            if iNum < self.iNumSteps:
                iIndex += 1
        oNumDraws.set_active(iIndex)
        oNumDraws.connect('changed', self._cols_changed)

        oStepSize = gtk.combo_box_new_text()
        for iNum in range(1,11):
            oStepSize.append_text(str(iNum))
        oStepSize.set_active(0)
        oStepSize.connect('changed', self._steps_changed)

        iIndex = 0
        oCardToDrawCount = gtk.combo_box_new_text()
        for iNum in range(1, self.iSelectedCount+1):
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
                "For the other rows, the entries are the probability of"
                "seeing at least Y cards from the selection by the X\'th draw\n"
                "with the number in brackets being the probablity of"
                "seeing eactly Y cards by the X'th draw\n"
                "The first column represents the opening hand or crypt draw")

        oTitleLabel = gtk.Label('Draw results :')
        self.oResultsBox.pack_start(oTitleLabel, False, False)

        self.oResultsTable = gtk.Table()
        self.oResultsBox.pack_start(AutoScrolledWindow(self.oResultsTable, True))

        dlg.vbox.pack_start(oMainTitle, False, False)
        dlg.vbox.pack_start(oProbLabel, False, False)
        dlg.vbox.pack_start(oDescLabel, False, False)
        dlg.vbox.pack_start(oWidgetBox, False, False)
        dlg.vbox.pack_start(self.oResultsBox)
        self._fill_table(self, bCrypt)
        dlg.set_size_request(800, 600)
        dlg.show_all()

        dlg.run()

    def _steps_changed(self, oComboBox):
        self.iDrawStep = int(oComboBox.get_active_text())

    def _rows_changed(self, oComboBox):
        self.iCardsToDraw = int(oComboBox.get_active_text())

    def _cols_changed(self, oComboBox):
        self.iNumSteps = int(oComboBox.get_active_text())

    def _fill_table(self, oWidget, bCrypt):
        """
        Fill Results Box with the draw results
        """
        for oChild in self.oResultsTable.get_children():
            self.oResultsTable.remove(oChild)
        self.oResultsTable.resize(2*self.iCardsToDraw+5, 2*self.iNumSteps+3)
        self.oResultsTable.set_col_spacings(0)
        self.oResultsTable.set_row_spacings(0)
        oTopLabel = gtk.Label('Cards drawn')
        oLeftLabel = gtk.Label('Number of cards seen')
        oLeftLabel.set_angle(270)
        self.oResultsTable.attach(oTopLabel, 0, 2*self.iNumSteps+4, 0, 1)
        self.oResultsTable.attach(oLeftLabel, 0, 1, 0, 2*self.iCardsToDraw+6)
        self.oResultsTable.attach(gtk.HSeparator(), 0, 2*self.iNumSteps+4, 1, 2,
                xpadding=0, ypadding=0, xoptions=gtk.FILL, yoptions=gtk.FILL)
        self.oResultsTable.attach(gtk.VSeparator(), 1, 2, 1,
                2*self.iCardsToDraw+6, xpadding=0, ypadding=0,
                xoptions=gtk.FILL, yoptions=gtk.FILL)
        if bCrypt:
            oOpeningLabel = gtk.Label('Opening Draw')
        else:
            oOpeningLabel = gtk.Label('Opening Hand')
        self.oResultsTable.attach(gtk.VSeparator(), 3, 4, 2,
                2*self.iCardsToDraw+6, xpadding=0, ypadding=0,
                xoptions=gtk.FILL, yoptions=gtk.FILL)
        self.oResultsTable.attach(oOpeningLabel, 4, 5, 2, 3)
        for iNum in range(1, self.iNumSteps):
            oLabel = gtk.Label('+ %d' % (iNum*self.iDrawStep))
            self.oResultsTable.attach(gtk.VSeparator(), 2*iNum+3, 2*iNum+4, 2,
                    2*self.iCardsToDraw+6, xpadding=0, ypadding=0,
                    xoptions=gtk.FILL, yoptions=gtk.FILL)
            self.oResultsTable.attach(oLabel, 2*iNum+4, 2*iNum+5, 2, 3)
        for iNum in range(self.iCardsToDraw+1):
            oLabel = gtk.Label('%d' % iNum)
            self.oResultsTable.attach(gtk.HSeparator(), 1, 2*self.iNumSteps+4,
                    2*iNum+3, 2*iNum+4, xpadding=0, ypadding=0,
                    xoptions=gtk.FILL, yoptions=gtk.FILL)
            self.oResultsTable.attach(oLabel, 2, 3, 2*iNum+4, 2*iNum+5)
        # Fill in zero row
        for iCol in range(self.iNumSteps):
            iNumDraws = iCol * self.iDrawStep + self.iOpeningDraw
            fProbExact = hyper_prob(0, iNumDraws,
                    self.iSelectedCount, self.iTotal)*100
            oResLabel = gtk.Label('%3.2f' % fProbExact)
            self.oResultsTable.attach(oResLabel, 2*iCol+4, 2*iCol+5, 4, 5)
        # Fill in other rows
        for iRow in range(self.iCardsToDraw):
            for iCol in range(self.iNumSteps):
                iThisDraw = iRow+1
                iNumDraws = iCol * self.iDrawStep + self.iOpeningDraw
                fProbExact = hyper_prob(iThisDraw, iNumDraws,
                        self.iSelectedCount, self.iTotal)*100
                fProbAccum = hyper_prob_at_least(iThisDraw, iNumDraws,
                        self.iSelectedCount, self.iTotal)*100
                oResLabel = gtk.Label('%3.2f (%3.2f)' % (fProbAccum, fProbExact))
                self.oResultsTable.attach(oResLabel, 2*iCol+4, 2*iCol+5,
                        2*iRow+6, 2*iRow+7)
        self.oResultsTable.show_all()

plugin = CardDrawSimPlugin
