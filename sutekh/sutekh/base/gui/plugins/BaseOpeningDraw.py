# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Dialog to display deck analysis software
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>,
# GPL - see COPYING for details
"""Simulate the opening hand draw."""

from copy import copy
from enum import IntEnum
from random import choice

from gi.repository import GObject, Gtk

from ...core.BaseTables import PhysicalCardSet
from ...core.BaseAdapters import IAbstractCard
from ..BasePluginManager import BasePlugin
from ..SutekhDialog import SutekhDialog
from ..AutoScrolledWindow import AutoScrolledWindow


# Utility functions
def convert_to_abs(aCards):
    """Convert a list of possibly physical cards to a list of AbstractCards"""
    aRes = []
    for oCard in aCards:
        aRes.append(IAbstractCard(oCard))
    return aRes


def get_cards_filter(oModel, oFilter):
    """Get abstract card list for the given filter"""
    return convert_to_abs(list(oModel.get_card_iterator(oFilter)))


def get_grouped_probs(dProbs, dToCheck, dGroupedProbs):
    """Calculate the probabilities for the card groups"""
    for sCardName, fMean in dProbs.items():
        for sGroup, aCards in dToCheck.items():
            if sCardName in aCards:
                dGroupedProbs.setdefault(sGroup, {'avg': 0.0, 'cards': []})
                # Cumlative average
                dGroupedProbs[sGroup]['avg'] += fMean
                # Need this for the sublists in view
                dGroupedProbs[sGroup]['cards'].append(sCardName)


def get_flat_probs(aCards, iDraw):
    """Calculate the expected number of each card in the opening hand"""
    dCount = {}
    for oCard in aCards:
        dCount.setdefault(oCard.name, 0)
        dCount[oCard.name] += 1
    dProbs = {}
    iTot = len(aCards)
    for sName, iCount in dCount.items():
        dProbs[sName] = hypergeometric_mean(iCount, iDraw, iTot)
    return dProbs


def check_cards(dHand, dToCheck, dCount):
    """Check if a card is in the list and set dCount correctly."""
    for sCardName, iCount in dHand.items():
        for sToCheck, aList in dToCheck.items():
            if sCardName in aList:
                dCount.setdefault(sToCheck, 0)
                dCount[sToCheck] += iCount


def fill_string(dGroups, dInfo, dToCheck):
    """Construct a string to display for type info"""
    sResult = ''
    aSortedList = sorted(dInfo.items(), key=lambda x: (x[1], x[0]),
                         reverse=True)
    for sGroup, iGrpNum in dGroups.items():
        sResult += u'%d \u00D7 %s\n' % (iGrpNum, sGroup)
        for sCardName, iNum in aSortedList:
            if sCardName in dToCheck[sGroup]:
                sResult += u'<i>\t%d \u00D7 %s</i>\n' % (iNum, sCardName)
    return sResult


def format_dict(dInfo):
    """Construct a string for the dictionary of names and card numbers"""
    sResult = ''
    aSortedList = sorted(dInfo.items(), key=lambda x: (x[1], x[0]),
                         reverse=True)
    for sName, iNum in aSortedList:
        sResult += u'%d \u00D7 %s\n' % (iNum, sName)
    return sResult


def hypergeometric_mean(iItems, iDraws, iTotal):
    """Mean of the hypergeometric distribution for a population of iTotal
       with iItems of interest and drawing iDraws items.
       In the usual notation, iItems=n, iDraws=m, iTotal=N
       """
    return iItems * iDraws / float(iTotal)  # mean = nm/N


def fill_store(oStore, dProbs, dGroupedProbs):
    """Fill oStore with the grouped stats about the opening hand"""
    for sName, dEntry in dGroupedProbs.items():
        fMean = dEntry['avg']
        sVal = '%2.2f' % fMean
        oParentIter = oStore.append(None, (sName, sVal, 100 * fMean / 7))
        # Need percentage from mean out of 7
        for sCardName in dEntry['cards']:
            fMean = dProbs[sCardName]
            sVal = '%2.2f' % fMean
            oStore.append(oParentIter, (sCardName, sVal, 100 * fMean / 7))


def draw_cards(aCards, iDraw, bCopy=False):
    """Draw iDraw cards from the list without replacement."""
    if bCopy:
        aCards = copy(aCards)
    dHand = {}
    for _iCard in range(iDraw):
        oCard = choice(aCards)
        aCards.remove(oCard)  # drawing without replacement
        dHand.setdefault(oCard.name, 0)
        dHand[oCard.name] += 1
    return dHand, aCards


def make_flat_view(dProbs, iDraw, sHeading, iWidth):
    """Setup a tree store with a flat probablity list."""
    oStore = Gtk.TreeStore(GObject.TYPE_STRING, GObject.TYPE_STRING,
                           GObject.TYPE_FLOAT)

    for sCardName, fMean in dProbs.items():
        sVal = '%2.2f' % fMean
        oStore.append(None, (sCardName, sVal, 100 * fMean / iDraw))

    return AutoScrolledWindow(create_view(oStore, sHeading, iWidth))


def make_grouped_view(dProbs, dGroupedProbs, sHeading, iWidth):
    """Setup the TreeStore for a dictionary of grouped probablities."""
    oStore = Gtk.TreeStore(GObject.TYPE_STRING, GObject.TYPE_STRING,
                           GObject.TYPE_FLOAT)
    fill_store(oStore, dProbs, dGroupedProbs)

    return AutoScrolledWindow(create_view(oStore, sHeading, iWidth))


def create_view(oStore, sHeading, iWidth):
    """Setup the TreeView for the results"""
    oView = Gtk.TreeView(oStore)
    oTextCol = Gtk.TreeViewColumn(sHeading)
    oTextCell = Gtk.CellRendererText()
    oTextCol.pack_start(oTextCell, True)
    oTextCol.add_attribute(oTextCell, 'text', 0)
    oValCol = Gtk.TreeViewColumn("Expected Number")
    oValProgCell = Gtk.CellRendererProgress()
    oValCol.pack_start(oValProgCell, True)
    oValCol.add_attribute(oValProgCell, 'value', 2)
    oValCol.add_attribute(oValProgCell, 'text', 1)
    # Take up space not reserved for progress bar column
    oTextCol.set_min_width(iWidth - 60)
    oTextCol.set_sort_column_id(0)
    oTextCol.set_expand(True)
    oValCol.set_sort_column_id(1)
    # limit space taken by progress bars
    oValCol.set_max_width(60)
    oValCol.set_expand(False)
    oView.append_column(oTextCol)
    oView.append_column(oValCol)
    # set suitable default sort
    oStore.set_sort_column_id(0, Gtk.SortType.ASCENDING)

    return oView


def fill_frame(sDetails, sHeading):
    """Draw a Gtk.Frame for the given detail type"""
    oFrame = Gtk.Frame()
    oFrame.set_label(sHeading)
    oLabel = Gtk.Label()
    oLabel.set_markup(sDetails)
    oFrame.add(oLabel)
    return oFrame


class BaseOpeningDraw(BasePlugin):
    """Simulate opening hands."""
    dTableVersions = {PhysicalCardSet: (4, 5, 6, 7)}
    aModelsSupported = (PhysicalCardSet,)
    # responses for the hand dialog
    class Choice(IntEnum):
        """Choices we offer the user on the window"""
        BACK = 1
        FORWARD = 2
        BREAKDOWN = 3

    MAXSIZE = 500
    COLUMN_WIDTH = 450

    sMenuName = "Simulate opening hand"

    sHelpCategory = "card_sets:analysis"

    # Subclasses should override this to provide game
    # specific details
    sHelpText = """Simulates the opening hand"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.iCurHand = 0
        self.aDrawnHands = []
        self.bShowDetails = False

    def get_menu_item(self):
        """Register on the 'Analyze' menu"""
        oCardDraw = Gtk.MenuItem(label=self.sMenuName)
        oCardDraw.connect("activate", self.activate)
        return ('Analyze', oCardDraw)

    def activate(self, _oWidget):
        """Create the actual dialog, and populate it"""
        sDiagName = "Opening Hand"
        if not self._check_cs_size(sDiagName, self.MAXSIZE):
            return

        if not self._get_cards():
            return

        oDialog = SutekhDialog(sDiagName, self.parent,
                               Gtk.DialogFlags.MODAL |
                               Gtk.DialogFlags.DESTROY_WITH_PARENT,
                               ("_Close", Gtk.ResponseType.CLOSE))
        oDialog.set_size_request(900, 600)

        self._fill_stats(oDialog)

        oShowButton = Gtk.Button('draw sample hands')
        oShowButton.connect('clicked', self._fill_dialog)

        oDialog.vbox.pack_start(oShowButton, False, False, 0)

        oDialog.show_all()

        oDialog.run()
        oDialog.destroy()
        self._cleanup()

    def _get_cards(self):
        """Extract relevant cards from the card set.

           Return false if the card set is unacceptable (too few cards, etc.)
           """
        raise NotImplementedError("implement _get_cards")

    def _cleanup(self):
        """Cleanup state after plugin run."""
        # Subclasses should extend this
        self.iCurHand = 0
        self.aDrawnHands = []
        self.bShowDetails = False

    def _setup_flat_view(self, aCards, iDraw, sTitle):
        """Create a flat store of card draw probablities."""
        dProbs = get_flat_probs(aCards, iDraw)

        return make_flat_view(dProbs, iDraw, sTitle, self.COLUMN_WIDTH)

    def _setup_grouped_view(self, dFlatProbs, dGroups, sTitle):
        """Create a grouped store of card draw probablilities."""
        dGroupedProbs = {}
        get_grouped_probs(dFlatProbs, dGroups, dGroupedProbs)
        return make_grouped_view(dFlatProbs, dGroupedProbs, sTitle,
                                 self.COLUMN_WIDTH)

    def _fill_stats(self, oDialog):
        """Add all the stats to the dialog."""
        raise NotImplementedError("implement _fill_stats")

    def _fill_dialog(self, _oButton):
        """Fill the dialog with the draw results"""
        oDialog = SutekhDialog('Sample Hands', self.parent,
                               Gtk.DialogFlags.MODAL |
                               Gtk.DialogFlags.DESTROY_WITH_PARENT)
        # We need to have access to the back button
        oShowButton = oDialog.add_button('Show details', self.Choice.BREAKDOWN)
        oDialog.action_area.pack_start(Gtk.VSeparator(), True, True, 0)
        oBackButton = oDialog.add_button("Back", self.Choice.BACK)
        oBackImage = Gtk.Image.new_from_icon_name('go-previous',
                                                  Gtk.IconSize.BUTTON)
        oBackButton.set_image(oBackImage)
        oBackButton.set_always_show_image(True)
        oBackButton.set_sensitive(False)
        oForwardButton = oDialog.add_button("Forward", self.Choice.FORWARD)
        oForwardImage = Gtk.Image.new_from_icon_name('go-next',
                                                     Gtk.IconSize.BUTTON)
        oForwardButton.set_image(oForwardImage)
        oForwardButton.set_always_show_image(True)
        oDialog.add_button("_Close", Gtk.ResponseType.CLOSE)
        self.bShowDetails = False
        if self.aDrawnHands:
            self.iCurHand = len(self.aDrawnHands)
            oHandBox = self._redraw_hand()
            if len(self.aDrawnHands) > 1:
                oBackButton.set_sensitive(True)
        else:
            oHandBox = self._draw_new_hand()  # construct the hand
        oDialog.vbox.pack_start(oHandBox, True, True, 0)
        oDialog.connect('response', self._next_hand, oBackButton, oShowButton)

        oDialog.show_all()
        oDialog.run()

    # pylint: disable=too-many-branches
    # We need to handle all the responses, so the number of branches is large
    def _next_hand(self, oDialog, iResponse, oBackButton, oShowButton):
        """Change the shown hand in the dialog."""
        def change_hand(oVBox, oNewHand, oDetailBox):
            """Replace the existing widget in oVBox with oNewHand."""
            for oChild in oVBox.get_children():
                if isinstance(oChild, Gtk.VBox):
                    oVBox.remove(oChild)
            oVBox.pack_start(oNewHand, False, False, 0)
            if oDetailBox:
                oVBox.pack_start(oDetailBox, True, True, 0)

        oDetailBox = None
        if iResponse == self.Choice.BACK:
            self.iCurHand -= 1
            if self.iCurHand == 1:
                oBackButton.set_sensitive(False)
            oNewHand = self._redraw_hand()
        elif iResponse == self.Choice.FORWARD:
            oBackButton.set_sensitive(True)
            if self.iCurHand == len(self.aDrawnHands):
                # Create a new hand
                oNewHand = self._draw_new_hand()
            else:
                self.iCurHand += 1
                oNewHand = self._redraw_hand()
        elif iResponse == self.Choice.BREAKDOWN:
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
        """Create a new sample hand"""
        self.iCurHand += 1
        self.aDrawnHands.append(self._do_draw_hand())
        return self._redraw_hand()

    def _redraw_hand(self):
        """Create a Gtk.HBox holding a hand"""
        oHandBox = Gtk.VBox(homogeneous=False, spacing=2)
        oDrawLabel = Gtk.Label()
        oDrawLabel.set_markup('<b>Hand Number %d :</b>' % self.iCurHand)
        oHandBox.pack_start(oDrawLabel, False, False, 0)
        oAlign = Gtk.Alignment(xalign=0.5, xscale=0.7)
        oAlign.add(Gtk.HSeparator())
        oHandBox.pack_start(oAlign, False, False, 0)
        oHBox = Gtk.HBox()
        oHandBox.pack_start(oHBox, True, True, 0)
        self._fill_hand(oHBox)
        return oHandBox

    def _fill_hand(self, oHBox):
        """Fill the Box with the details of the hand."""
        raise NotImplementedError("implement _fill_hand")

    def _do_draw_hand(self):
        """Draw the current hand."""
        raise NotImplementedError("implement _do_draw_hand")

    def _redraw_detail_box(self):
        """Fill in detailed breakdown of the current drawn hand."""
        raise NotImplementedError("implement _redraw_detail_box")
