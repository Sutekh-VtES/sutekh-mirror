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
        CardFunctionFilter, FilterNot

# Utility functions

def convert_to_abs(aCards):
    """Convert a list of possibly physical cards to a list of AbstractCards"""
    aRes = []
    for oCard in aCards:
        aRes.append(IAbstractCard(oCard))
    return aRes

def get_cards_filter(oModel, oFilter):
    """Get abstract card list for the given filter"""
    return convert_to_abs(list(oModel.getCardIterator(oFilter)))

def get_probs(dLibProbs, dToCheck, dGroupedProbs):
    """Calculate the probablilties for the card groups"""
    for sCardName, fMean in dLibProbs.iteritems():
        for sGroup, aCards in dToCheck.iteritems():
            if sCardName in aCards:
                dGroupedProbs.setdefault(sGroup, {'avg' : 0.0,
                    'cards' : []})
                # Cumlative average
                dGroupedProbs[sGroup]['avg'] += fMean
                # Need this for the sublists in view
                dGroupedProbs[sGroup]['cards'].append(sCardName)

def check_card(sCardName, dToCheck, dCount):
    """Check if a card is in the list and update dCount."""
    for sToCheck, aList in dToCheck.iteritems():
        if sCardName in aList:
            dCount.setdefault(sToCheck, 0)
            dCount[sToCheck] += 1

def fill_string(dGroups, aSortedList, dToCheck):
    """Construct a string to display for type info"""
    sResult = ''
    for sGroup, iNum in dGroups.iteritems():
        sResult += u'%d \u00D7 %s\n' % (iNum, sGroup)
        for sCardName, iNum in aSortedList:
            if sCardName in dToCheck[sGroup]:
                sResult += u'<i>\t%d \u00D7 %s</i>\n' % (iNum, sCardName)
    return sResult

def hypergeometric_mean(iItems, iDraws, iTotal):
    """Mean of the hypergeometric distribution for a population of iTotal
       with iItems of interest and drawing iDraws items.
       In the usual notation, iItems=n, iDraws=m, iTotal=N
       """
    return iItems * iDraws / float(iTotal) # mean = nm/N

def fill_store(oStore, dLibProbs, dGroupedProbs):
    """Fill oStore with the stats about the opening hand"""
    for sName, dEntry in dGroupedProbs.iteritems():
        fMean = dEntry['avg']
        sVal = '%2.2f' % fMean
        oParentIter = oStore.append(None, (sName, sVal, 100*fMean / 7))
        # Need percentage from mean out of 7
        for sCardName in dEntry['cards']:
            fMean = dLibProbs[sCardName]
            sVal = '%2.2f' % fMean
            oStore.append(oParentIter, (sCardName, sVal, 100*fMean / 7))

def setup_view(dLibProbs, dGroupedProbs, sHeading):
    """Setup the TreeStore and TreeView for the results"""
    oStore = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING,
            gobject.TYPE_FLOAT)
    fill_store(oStore, dLibProbs, dGroupedProbs)

    oView = gtk.TreeView(oStore)

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
    # limit space taken by progress bars
    oValCol.set_max_width(70)
    oValCol.set_min_width(40)
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
    # responses for the hand dialog
    BACK, FORWARD, BREAKDOWN = range(1, 4)

    # pylint: disable-msg=W0142
    # **magic OK here
    def __init__(self, *aArgs, **kwargs):
        super(OpeningHandSimulator, self).__init__(*aArgs, **kwargs)
        self.dCardTypes = {}
        self.dCardProperties = {}
        self.aLibrary = []
        self.iTotHands = 0
        self.iCurHand = 0
        self.aDrawnHands = []
        self.bShowDetails = False

    def get_menu_item(self):
        """
        Overrides method from base class.
        """
        if not self.check_versions() or not self.check_model_type():
            return None
        iCardDraw = gtk.MenuItem("Simulate opening hand")
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
        oLibFilter = FilterNot(MultiCardTypeFilter(['Imbued', 'Vampire']))

        self.aLibrary = get_cards_filter(self.model, oLibFilter)

        if len(self.aLibrary) < 7:
            do_complaint_error('Library needs to be larger than opening hand')
            return

        for sType in MultiCardTypeFilter.get_values():
            aList = get_cards_filter(self.model, CardTypeFilter(sType))
            if len(aList) > 0 and aList[0] in self.aLibrary:
                self.dCardTypes[sType] = set([oC.name for oC in aList])

        for sFunction in CardFunctionFilter.get_values():
            aList = get_cards_filter(self.model, CardFunctionFilter(sFunction))
            if len(aList) > 0:
                self.dCardProperties[sFunction] = set([oC.name for oC in
                    aList])

        oDialog = SutekhDialog(sDiagName, self.parent,
                gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK))

        self._fill_stats(oDialog)

        oShowButton = gtk.Button('draw sample hands')
        oShowButton.connect('clicked', self._fill_dialog)

        # pylint: disable-msg=E1101
        # vbox methods not detected by pylint
        oDialog.vbox.pack_start(oShowButton, False, False)

        oDialog.set_size_request(800, 600)

        oDialog.show_all()

        oDialog.run()
        oDialog.destroy()
        # clean up
        self.dCardTypes = {}
        self.dCardProperties = {}
        self.aLibrary = []
        self.iTotHands = 0
        self.iCurHand = 0
        self.aDrawnHands = []
    # pylint: enable-msg=W0613

    def _fill_stats(self, oDialog):
        "Fill in the stats from the draws"
        dTypeProbs = {}
        dPropProbs = {}
        dLibProbs = self._get_lib_props()
        get_probs(dLibProbs, self.dCardTypes, dTypeProbs)
        get_probs(dLibProbs, self.dCardProperties, dPropProbs)
        # setup display widgets
        oHBox = gtk.HBox(False, 3)
        # pylint: disable-msg=E1101
        # vbox methods not detected by pylint
        oDialog.vbox.pack_start(oHBox)
        oHBox.pack_start(AutoScrolledWindow(setup_view(dLibProbs,
            dTypeProbs, 'Card Types')))
        oHBox.pack_start(AutoScrolledWindow(setup_view(dLibProbs,
            dPropProbs, 'Card Properties')))
        oHBox.show_all()

    def _get_lib_props(self):
        """Calculate the expected number of each card in the opening hand"""
        dLibCount = {}
        for oCard in self.aLibrary:
            dLibCount.setdefault(oCard.name, 0)
            dLibCount[oCard.name] += 1
        dLibProbs = {}
        iTot = len(self.aLibrary)
        for sName, iCount in dLibCount.iteritems():
            dLibProbs[sName] = hypergeometric_mean(iCount, 7, iTot)
        return dLibProbs

    # pylint: disable-msg=W0613
    # oButton required by function signature
    def _fill_dialog(self, oButton):
        "Fill the dialog with the draw results"
        oDialog = SutekhDialog ('Sample Hands', self.parent,
                gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT)
        # We need to have access to the back button
        # pylint: disable-msg=E1101
        # pylint doesn't see vbox + action_area methods
        oShowButton = oDialog.add_button('Show details', self.BREAKDOWN)
        oDialog.action_area.pack_start(gtk.VSeparator(), expand=True)
        oBackButton = oDialog.add_button(gtk.STOCK_GO_BACK, self.BACK)
        oBackButton.set_sensitive(False)
        oDialog.add_button(gtk.STOCK_GO_FORWARD, self.FORWARD)
        oDialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        self.bShowDetails = False
        if len(self.aDrawnHands) > 0:
            self.iCurHand = self.iTotHands
            oHandBox = self._redraw_hand()
            if self.iTotHands > 1:
                oBackButton.set_sensitive(True)
        else:
            oHandBox = self._draw_new_hand() # construct the hand
        oDialog.vbox.pack_start(oHandBox)
        oDialog.connect('response', self._next_hand, oBackButton, oShowButton)

        oDialog.show_all()
        oDialog.run()

    # pylint: disable-msg=R0912
    # We need to handle all the responses, so the number of branches is large
    def _next_hand(self, oDialog, iResponse, oBackButton, oShowButton):
        """Change the shown hand in the dialog."""
        def change_hand(oVBox, oNewHand, oDetailBox):
            """Replace the existing widget in oVBox with oNewHand."""
            for oChild in oVBox.get_children():
                if type(oChild) is gtk.VBox:
                    oVBox.remove(oChild)
            oVBox.pack_start(oNewHand, False, False)
            if oDetailBox:
                oVBox.pack_start(oDetailBox)

        oDetailBox = None
        if iResponse == self.BACK:
            self.iCurHand -= 1
            if self.iCurHand == 1:
                oBackButton.set_sensitive(False)
            oNewHand = self._redraw_hand()
        elif iResponse == self.FORWARD:
            oBackButton.set_sensitive(True)
            if self.iCurHand == self.iTotHands:
                # Create a new hand
                oNewHand = self._draw_new_hand()
            else:
                self.iCurHand += 1
                oNewHand = self._redraw_hand()
        elif iResponse == self.BREAKDOWN:
            # show / hide the detailed breakdown
            oNewHand = self._redraw_hand()
            if self.bShowDetails:
                self.bShowDetails = False
                oShowButton.set_label('Show details')
            else:
                self.bShowDetails = True
                oShowButton.set_label('Hide details')
        else:
            # OK response
            oDialog.destroy()
            return

        if self.bShowDetails:
            oDetailBox = self._redraw_detail_box()
        change_hand(oDialog.vbox, oNewHand, oDetailBox)
        oDialog.show_all()

    def _draw_new_hand(self):
        "Create a new sample hand"
        self.iTotHands += 1
        self.iCurHand += 1
        aThisLib = copy(self.aLibrary)
        dHand = {}
        dProps = {}
        dTypes = {}
        # pylint: disable-msg=W0612
        # iCard is a loop counter, and is ignored
        for iCard in range(7):
            oCard = choice(aThisLib)
            aThisLib.remove(oCard) # drawing without replacement
            dHand.setdefault(oCard.name, 0)
            dHand[oCard.name] += 1
            check_card(oCard.name, self.dCardTypes, dTypes)
            check_card(oCard.name, self.dCardProperties, dProps)
        sHand = ''
        aSortedList = sorted(dHand.items(), key=lambda x: (x[1], x[0]),
                reverse=True)
        for sName, iNum in aSortedList:
            sHand += u'%d \u00D7 %s\n' % (iNum, sName)
        sTypes = fill_string(dTypes, aSortedList, self.dCardTypes)
        sProps = fill_string(dProps, aSortedList, self.dCardProperties)
        self.aDrawnHands.append([sHand, sTypes, sProps])
        return self._redraw_hand()

    def _redraw_hand(self):
        """Create a gtk.HBox holding a hand"""
        oHandBox = gtk.VBox(False, 2)
        oDrawLabel = gtk.Label()
        oHandLabel = gtk.Label()
        oDrawLabel.set_markup('<b>Hand Number %d :</b>' % self.iCurHand)
        oHandLabel.set_markup(self.aDrawnHands[self.iCurHand - 1][0])
        oHandBox.pack_start(oDrawLabel, False, False)
        oAlign = gtk.Alignment(xalign=0.5, xscale=0.7)
        oAlign.add(gtk.HSeparator())
        oHandBox.pack_start(oAlign, False, False)
        oHandBox.pack_start(oHandLabel)
        return oHandBox

    def _redraw_detail_box(self):
        """Fill in the details for the given hand"""
        def fill_frame(sDetails, sHeading):
            """Draw a gtk.Frame for the given detail type"""
            oFrame = gtk.Frame(sHeading)
            oLabel = gtk.Label()
            oLabel.set_markup(sDetails)
            oFrame.add(oLabel)
            return oFrame
        oDetailBox = gtk.VBox(False, 2)
        oHBox = gtk.HBox(False, 2)
        oHBox.pack_start(fill_frame(self.aDrawnHands[self.iCurHand -1][1],
            'Card Types'))
        oHBox.pack_start(fill_frame(self.aDrawnHands[self.iCurHand -1][2],
            'Card Properties'))
        oDetailBox.pack_start(oHBox)
        return oDetailBox

# pylint: disable-msg=C0103
# plugin name doesn't match rule
plugin = OpeningHandSimulator
