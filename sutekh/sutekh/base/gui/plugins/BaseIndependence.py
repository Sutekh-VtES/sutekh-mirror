# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>,
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test whether card sets can be constructed independently"""

from gi.repository import Gtk
from ...core.BaseTables import PhysicalCardSet
from ...core.BaseAdapters import (IPhysicalCardSet, IAbstractCard,
                                  IPhysicalCard, IPrintingName)
from ...core.BaseFilters import ParentCardSetFilter
from ..BasePluginManager import BasePlugin
from ..CardSetsListView import CardSetsListView
from ..SutekhDialog import (SutekhDialog, NotebookDialog,
                            do_info_message, do_complaint_error)
from ..AutoScrolledWindow import AutoScrolledWindow
from ..GuiCardSetFunctions import create_card_set


# helper functions and classes
class CardInfo:
    """Helper class to hold card set info"""
    def __init__(self):
        self.iCount = 0
        self.dCardSets = {}

    def format_cs(self):
        """Pretty print card set list"""
        return ", ".join(self.dCardSets)


def _get_cards(oCardSet, dCards, bIgnoreExpansions):
    """Extract the abstract cards from the card set oCardSet"""
    if bIgnoreExpansions:
        fCard = lambda oCard: oCard.abstractCard
    else:
        fCard = lambda oCard: oCard
    for oCard in oCardSet.cards:
        oCard = fCard(oCard)
        dCards.setdefault(oCard, CardInfo())
        dCards[oCard].iCount += 1
        dCards[oCard].dCardSets.setdefault(oCardSet.name, 0)
        dCards[oCard].dCardSets[oCardSet.name] += 1


def _make_align_list(aList):
    """Wrap the list of strings in an aligned widget for display."""
    oLabel = Gtk.Label()
    oAlign = Gtk.Alignment()
    oAlign.add(oLabel)
    oAlign.set_padding(0, 0, 5, 0)  # offset a little from the left edge
    sContents = "\n".join(aList)
    oLabel.set_markup(sContents)
    oLabel.set_selectable(True)
    return oAlign


class BaseIndependence(BasePlugin):
    """Provides a plugin for testing whether card sets are independant.

       Independence in this cases means that there are enought cards in
       the parent card set to construct all the selected child card sets
       simulatenously.

       We don't test the case when parent is None, since there's nothing
       particularly sensible to say there. We also don't do anything
       when there is only 1 child, for similiar justification.
       """
    dTableVersions = {PhysicalCardSet: (5, 6, 7, )}
    aModelsSupported = (PhysicalCardSet,)

    sMenuName = "Test Card Set Independence"

    sHelpCategory = "card_sets:analysis"

    sHelpText = """This tool tests the current card set against other card
                   sets with the same parent, and considers whether there
                   are enough cards in the parent card set to simultaneously
                   construct all the selected sets. Multiple decks can be
                   selected from the list of card sets.

                   You can test the current card set against all sets with the
                   same parent which are marked as _In Use_ by checking the
                   _Test against all card sets marked as in use_ checkbox when
                   selecting decks for comparison. This checkbox overrides any
                   selected entries in the list.

                   By default the independence test is strict and checks
                   whether the parent set contains enough cards to build all
                   the selected child sets with exactly the card expansions
                   specified. A less strict check which ignores expansions may
                   be selected by checking _Ignore card expansions_.

                   The first tab of the results displays the full list of cards
                   of which there is a shortage in the parent card set. For
                   each selected set which includes any of these cards, the
                   list of cards relevant to that set is shown in a separate
                   tab.

                   The full list of cards has a 'Create Card Set' button,
                   which can be used to create a card set containing the
                   specific cards listed."""

    def get_menu_item(self):
        """Register with the 'Analyze' Menu"""
        oTest = Gtk.MenuItem(label=self.sMenuName)
        oTest.connect("activate", self.activate)
        return ('Analyze', oTest)

    def activate(self, _oWidget):
        """Create the dialog in response to the menu item."""
        oDlg = self.make_dialog()
        if oDlg:
            oDlg.run()

    def make_dialog(self):
        """Create the list of card sets to select"""
        # pylint: disable=attribute-defined-outside-init
        # No need to define oThisCardSet, oCSView & oInUseButton in __init__
        self.oThisCardSet = self._get_card_set()
        if not self.oThisCardSet.parent:
            do_complaint_error("Card Set has no parent, so nothing to test.")
            return None

        bInUseSets = PhysicalCardSet.selectBy(
            parentID=self.oThisCardSet.parent.id, inuse=True).count() > 0
        oDlg = SutekhDialog(
            "Choose Card Sets to Test", self.parent,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            ("_OK", Gtk.ResponseType.OK, "_Cancel", Gtk.ResponseType.CANCEL))
        self.oCSView = CardSetsListView(None, oDlg)
        oDlg.vbox.pack_start(AutoScrolledWindow(self.oCSView), True, True, 0)
        self.oCSView.set_select_multiple()
        self.oCSView.exclude_set(self.view.sSetName)
        # exclude all parents
        oParentSet = self.oThisCardSet.parent
        while oParentSet:
            self.oCSView.exclude_set(oParentSet.name)
            oParentSet = oParentSet.parent
        # Add filter so we only show the sibling card sets
        oFilter = ParentCardSetFilter([self.oThisCardSet.parent.name])
        self.oCSView.set_filter(oFilter, None)
        self.oCSView.load()
        self.oCSView.expand_to_entry(self.view.sSetName)
        self.oIgnoreExpansions = Gtk.CheckButton(
            label="Ignore card expansions")
        oDlg.vbox.pack_start(self.oIgnoreExpansions, False, False, 0)
        self.oInUseButton = Gtk.CheckButton(label="Test against all cards sets"
                                            " marked as in use")
        if bInUseSets:
            oDlg.vbox.pack_start(self.oInUseButton, False, False, 0)
            self.oInUseButton.connect("toggled", self.show_hide_list)
        oDlg.connect("response", self.handle_response)
        oDlg.set_size_request(600, 600)
        oDlg.show_all()
        return oDlg

    def show_hide_list(self, oWidget):
        """Hide the card set selection when the user toggles the check box"""
        if oWidget.get_active():
            self.oCSView.set_select_none()
        else:
            self.oCSView.set_select_multiple()

    def handle_response(self, oDlg, oResponse):
        """Handle the response from the dialog."""
        if oResponse == Gtk.ResponseType.OK:
            bIgnoreExpansions = self.oIgnoreExpansions.get_active()
            if self.oInUseButton.get_active():
                oInUseSets = PhysicalCardSet.selectBy(
                    parentID=self.oThisCardSet.parent.id, inuse=True)
                aCardSetNames = [oCS.name for oCS in oInUseSets]
                if self.view.sSetName not in aCardSetNames:
                    aCardSetNames.append(self.view.sSetName)
            else:
                aCardSetNames = [self.view.sSetName]
                aSelected = self.oCSView.get_all_selected_sets()
                if aSelected:
                    aCardSetNames.extend(aSelected)
            # We may have only 1 set here, but we will still do the
            # right thing in that case.
            self._test_card_sets(aCardSetNames, self.oThisCardSet.parent,
                                 bIgnoreExpansions)
        oDlg.destroy()

    def _display_results(self, dMissing, oParentCS):
        """Display the list of missing cards"""
        oResultDlg = NotebookDialog("Missing Cards", None,
                                    Gtk.DialogFlags.MODAL |
                                    Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                    ("_Close", Gtk.ResponseType.CLOSE))
        dFormatted = {}
        aParentList = []
        for oCard, oInfo in sorted(dMissing.items(),
                                   key=lambda x: IAbstractCard(x[0]).name):
            sCardName = self._escape(IAbstractCard(oCard).name)
            if not hasattr(oCard, 'printing'):
                sPrinting = ""
            elif oCard.printing:
                sPrinting = " [%s]" % self._escape(
                    IPrintingName(oCard.printing))
            else:
                sPrinting = " [(unspecified expansion)]"
            aParentList.append('<span foreground = "blue">'
                               '%s%s</span> : Missing '
                               '<span foreground="red">%d'
                               '</span> copies (used in %s)'
                               % (sCardName, sPrinting, oInfo.iCount,
                                  self._escape(oInfo.format_cs())))
            for sCardSet, iCount in oInfo.dCardSets.items():
                dFormatted.setdefault(sCardSet, [])
                dFormatted[sCardSet].append('<span foreground="blue">%s%s'
                                            '</span>: Missing '
                                            '<span foreground="red">%d'
                                            '</span> copies (%d copies '
                                            'used here)' % (sCardName,
                                                            sPrinting,
                                                            oInfo.iCount,
                                                            iCount))

        oPage = Gtk.VBox(homogeneous=False)
        oPage.pack_start(AutoScrolledWindow(_make_align_list(aParentList)),
                         True, True, 0)
        oButton = Gtk.Button(label='Create Card Set from this list')
        oButton.connect('clicked', self.create_card_set,
                        dMissing)
        oPage.pack_start(oButton, False, True, 0)
        oResultDlg.add_widget_page(
            oPage, 'Missing from %s' % self._escape(oParentCS.name),
            bMarkup=True)

        for sCardSet, aMsgs in dFormatted.items():
            oResultDlg.add_widget_page(
                AutoScrolledWindow(_make_align_list(aMsgs)),
                'Missing in %s' % self._escape(sCardSet), bMarkup=True)
        oResultDlg.set_size_request(600, 600)
        oResultDlg.show_all()
        oResultDlg.run()
        oResultDlg.destroy()

    def _test_card_sets(self, aCardSetNames, oParentCS, bIgnoreExpansions):
        """Test if the Card Sets are actaully independent by
           looking for cards common to the sets"""
        dCards = {}
        for sCardSetName in aCardSetNames:
            oCS = IPhysicalCardSet(sCardSetName)
            _get_cards(oCS, dCards, bIgnoreExpansions)
        dParent = {}
        _get_cards(oParentCS, dParent, bIgnoreExpansions)
        dMissing = {}
        for oCard, oInfo in dCards.items():
            if oCard not in dParent:
                dMissing[oCard] = oInfo
            elif dParent[oCard].iCount < oInfo.iCount:
                # the dict ensures we don't need a copy
                dMissing[oCard] = oInfo
                dMissing[oCard].iCount -= dParent[oCard].iCount
        if dMissing:
            self._display_results(dMissing, oParentCS)
        else:
            sMessage = "No cards missing from %s" % oParentCS.name
            do_info_message(sMessage)

    def create_card_set(self, _oButton, dMissing):
        """Create a card set from the card list"""
        sCSName = create_card_set(self.parent)
        if not sCSName:
            return  # User cancelled, so skip out
        oCardSet = IPhysicalCardSet(sCSName)
        # Turn data into a list of cards to add
        aCards = []
        for oCard, oInfo in dMissing.items():
            if not hasattr(oCard, 'printing'):
                # Dealing with abstract cards in the list
                oPhysCard = IPhysicalCard((oCard, None))
            else:
                oPhysCard = oCard
            for _iCardCnt in range(oInfo.iCount):
                aCards.append(oPhysCard)
        self._commit_cards(oCardSet, aCards)
        self._open_cs(sCSName)
