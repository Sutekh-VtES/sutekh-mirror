# CardDrawSimluator.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Dialog to display deck analysis software
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>,
# GPL - see COPYING for details
"""
Simulate the opening hand draw
"""

import gtk, gobject
from copy import copy
from random import choice
from sutekh.core.SutekhObjects import PhysicalCardSet, AbstractCardSet, \
        IAbstractCard
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.core.Filters import CardTypeFilter, MultiCardTypeFilter, \
        CardFunctionFilter

# Utility functions

def get_library(aAllCards):
    "Extract the library cards from the list"
    aLibrary = []
    for oCard in aAllCards:
        # pylint: disable-msg=E1101
        # pylint doesn't see IAbstractCard methods
        oAbsCard = IAbstractCard(oCard)
        aTypes = [x.name for x in oAbsCard.cardtype]
        if aTypes[0] != 'Vampire' and aTypes[0] != 'Imbued':
            aLibrary.append(oAbsCard)
    return aLibrary

def convert_to_abs(aCards):
    "Convert a list of possibly physical cards to a list of AbstractCards"
    aRes = []
    for oCard in aCards:
        aRes.append(IAbstractCard(oCard))
    return aRes

def get_cards_filter(oModel, oFilter):
    "Get abstract card list for the given filter"
    return convert_to_abs(list(oModel.getCardIterator(oFilter)))


def check_card(oAbsCard, dToCheck, dCounts, dCards):
    "Process a drawn card"
    for sKey, aList in dToCheck.iteritems():
        if oAbsCard in aList:
            dCounts[sKey] += 1
            dCards[sKey].setdefault(oAbsCard.name, 0)
            dCards[sKey][oAbsCard.name] += 1


def setup_view(dCounts, dCards, sHeading):
    "Setup the TreeStore and TreeView for the results"
    oStore = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING,
            gobject.TYPE_FLOAT)
    oView = gtk.TreeView(oStore)
    # fill in data
    for sName, iVal in dCounts.iteritems():
        sVal = '%2.2f' % (iVal / 1000.0)
        oParentIter = oStore.append(None, (sName, sVal, iVal / 70.0))
        # Need percentage out of 7 (100 / (7*1000.0))
        for sCardName, iVal in dCards[sName].iteritems():
            sVal = '%2.2f' % (iVal / 1000.0)
            oStore.append(oParentIter, (sCardName, sVal,
                iVal / 70.0))

    oTextCol = gtk.TreeViewColumn(sHeading)
    oTextCell = gtk.CellRendererText()
    oTextCol.pack_start(oTextCell, True)
    oTextCol.add_attribute(oTextCell, 'text', 0)
    oValCol = gtk.TreeViewColumn("Expected Number")
    oValProgCell = gtk.CellRendererProgress()
    oValCol.pack_start(oValProgCell, True)
    oValCol.add_attribute(oValProgCell, 'value', 2)
    oValCol.add_attribute(oValProgCell, 'text', 1)
    # size request is 800x600, so grab about 3/4 of the column
    oTextCol.set_min_width(300)
    oTextCol.set_sort_column_id(0)
    oValCol.set_sort_column_id(1)
    oView.append_column(oTextCol)
    oView.append_column(oValCol)
    # set suitable default sort
    oStore.set_sort_column_id(0, gtk.SORT_ASCENDING)

    return oView

class OpeningHandSimulator(CardListPlugin):
    """
    Simulate opening hands
    """
    dTableVersions = {PhysicalCardSet : [3, 4],
            AbstractCardSet : [3]}
    aModelsSupported = [PhysicalCardSet,
            AbstractCardSet]

    # pylint: disable-msg=W0142
    # **magic OK here
    def __init__(self, *aArgs, **kwargs):
        super(OpeningHandSimulator, self).__init__(aArgs, kwargs)
        self.dCardTypes = {}
        self.dCardProperties = {}
        self.aLibrary = []
        self.iNumHands = 10

    def get_menu_item(self):
        """
        Overrides method from base class.
        """
        if not self.check_versions() or not self.check_model_type():
            return None
        iCardDraw = gtk.MenuItem("Smulate opening hand")
        iCardDraw.connect("activate", self.activate)
        return iCardDraw

    def get_desired_menu(self):
        "Menu to associate with"
        return "Plugins"

    # pylint: disable-msg=W0613
    # oWidget required by function signature
    def activate(self, oWidget):
        "Create the actual dialog, and populate it"
        sDiagName = "Opening Hand"
        aAllCards = list(self.model.getCardIterator(None))

        self.aLibrary = get_library(aAllCards)

        if len(self.aLibrary) < 7:
            do_complaint_error('Library needs to be larger than opening hand')
            return


        for sType in MultiCardTypeFilter.get_values():
            aList = get_cards_filter(self.model, CardTypeFilter(sType))
            if len(aList) > 0 and aList[0] in self.aLibrary:
                self.dCardTypes[sType] = aList

        for sFunction in CardFunctionFilter.get_values():
            aList = get_cards_filter(self.model, CardFunctionFilter(sFunction))
            if len(aList) > 0:
                self.dCardProperties[sFunction] = aList

        oDialog = SutekhDialog(sDiagName, self.parent,
                gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK))

        self._fill_stats(oDialog)

        oShowButton = gtk.Button('show 10 sample hands')
        oShowButton.connect('clicked', self._fill_dialog)

        # pylint: disable-msg=E1101
        # vbox methods not detected by pylint
        oDialog.vbox.pack_start(oShowButton, False, False)

        oDialog.set_size_request(800, 600)

        oDialog.show_all()

        oDialog.run()
        oDialog.destroy()
    # pylint: enable-msg=W0613

    def _fill_stats(self, oDialog):
        "Fill in the stats from the draws"
        # Get stats from 100 hand draws
        dTypeCounts = {}
        dTypeCards = {}
        dPropCounts = {}
        dPropCards = {}
        for sKey in self.dCardTypes:
            dTypeCounts[sKey] = 0
            dTypeCards[sKey] = {}
        for sKey in self.dCardProperties:
            dPropCounts[sKey] = 0
            dPropCards[sKey] = {}
        # pylint: disable-msg=W0612
        # iDraw, iCard are just loop counters, and are ignored
        for iDraw in range(1000):
            aThisLib = copy(self.aLibrary)
            for iCard in range(7):
                oCard = choice(aThisLib)
                aThisLib.remove(oCard) # drawing without replacement
                check_card(oCard, self.dCardTypes, dTypeCounts, dTypeCards)
                check_card(oCard, self.dCardProperties, dPropCounts, dPropCards)
        # setup display widgets

        oHBox = gtk.HBox(False, 3)
        # pylint: disable-msg=E1101
        # vbox methods not detected by pylint
        oDialog.vbox.pack_start(oHBox)

        oHBox.pack_start(AutoScrolledWindow(setup_view(dTypeCounts,
            dTypeCards, 'Card Types')))
        oHBox.pack_start(AutoScrolledWindow(setup_view(dPropCounts,
            dPropCards, 'Card Properties')))
        oHBox.show_all()

    # pylint: disable-msg=W0613
    # oButton required by function signature
    def _fill_dialog(self, oButton):
        "Fill the dialog with the draw results"
        oDialog = SutekhDialog ('Sample Hands', self.parent,
                gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK))
        oResultsTable = gtk.Table(5, 2)
        # pylint: disable-msg=E1101
        # pylint doesn't see vbox methods
        oDialog.vbox.pack_start(oResultsTable, False, False)
        for iDraw in range(self.iNumHands):
            oHandBox = gtk.VBox(False, 2)
            oDrawLabel = gtk.Label()
            oDrawLabel.set_markup('<b>Hand Number %d :</b>' % (iDraw + 1))
            oHandBox.pack_start(oDrawLabel)
            oHandBox.pack_start(self._draw_hand(), False, False)
            iCol = iDraw / 5
            iRow = iDraw % 5
            oResultsTable.attach(oHandBox, iRow, iRow+1, iCol, iCol+1)
        oDialog.show_all()
        oDialog.run()
        oDialog.destroy()

    def _draw_hand(self):
        "Create a gtk.Label containing a sample hand"
        aThisLib = copy(self.aLibrary)
        dHand = {}
        oHandLabel = gtk.Label()
        # pylint: disable-msg=W0612
        # iCard is a loop counter, and is ignored
        for iCard in range(7):
            oCard = choice(aThisLib)
            aThisLib.remove(oCard) # drawing without replacement
            dHand.setdefault(oCard.name, 0)
            dHand[oCard.name] += 1
        sHand = ''
        for sName, iNum in sorted(dHand.items(), key=lambda x: x[1],
                reverse=True):
            sHand += '\t%d X %s\n' % (iNum, sName)
        oHandLabel.set_markup(sHand)
        return oHandLabel

# pylint: disable-msg=C0103
# plugin name doesn't match rule
plugin = OpeningHandSimulator
