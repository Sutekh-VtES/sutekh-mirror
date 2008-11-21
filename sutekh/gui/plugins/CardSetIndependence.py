# CardSetIndependence.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>,
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test whether card sets can be constructed independently"""

import gtk
from sutekh.core.SutekhObjects import PhysicalCardSet, IPhysicalCardSet
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.ScrolledList import ScrolledList
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint, \
        do_complaint_error
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow

# helper functions

class CardInfo(object):
    """Helper class to hold card set info"""
    def __init__(self):
        self.iCount = 0
        self.dCardSets = {}

    def format_cs(self):
        """Pretty print card set list"""
        return ", ".join(self.dCardSets)

def _get_cards(oCardSet, dCards):
    """Extract the abstract cards from the card set oCardSet"""
    # pylint: disable-msg=E1101
    # SQLObject + pyprotocol methods confuse pylint
    for oCard in oCardSet.cards:
        dCards.setdefault(oCard, CardInfo())
        dCards[oCard].iCount += 1
        dCards[oCard].dCardSets.setdefault(oCardSet.name, 0)
        dCards[oCard].dCardSets[oCardSet.name] += 1

def _make_align_list(aList):
    """Wrap the list of strings in an aligned widget for display."""
    oLabel = gtk.Label()
    oAlign = gtk.Alignment()
    oAlign.add(oLabel)
    oAlign.set_padding(0, 0, 5, 0) # offset a little from the left edge
    sContents = "\n".join(aList)
    oLabel.set_markup(sContents)
    return oAlign

def _display_results(dMissing, oParentCS):
    """Display the list of missing cards"""
    oResultDlg = SutekhDialog("Missing Cards", None,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
    oNotebook = gtk.Notebook()
    oNotebook.set_scrollable(True)
    oNotebook.popup_enable()
    dFormatted = {}
    aParentList = []
    for oCard, oInfo in dMissing.iteritems():
        sCardName = oCard.abstractCard.name
        if oCard.expansion:
            sExpansion = oCard.expansion.name
        else:
            sExpansion = "(unspecified expansion)"
        aParentList.append('<span foreground = "blue">'
                '%s [%s]</span> : Missing <span foreground="red">%d'
                '</span> copies (used in %s)'
                % (sCardName, sExpansion, oInfo.iCount, oInfo.format_cs()))
        for sCardSet, iCount in oInfo.dCardSets.iteritems():
            dFormatted.setdefault(sCardSet, [])
            dFormatted[sCardSet].append('<span foreground="blue">%s [%s]'
                    '</span>: Missing <span foreground="red">%d</span> copies'
                    ' (%d copies used here)' % (sCardName, sExpansion,
                        oInfo.iCount, iCount))
    oHeading = gtk.Label()
    oHeading.set_markup('Missing from %s' % oParentCS.name)
    oNotebook.append_page(AutoScrolledWindow(
        _make_align_list(aParentList), True), oHeading)
    for sCardSet, aMsgs in dFormatted.iteritems():
        oHeading = gtk.Label()
        oHeading.set_markup('Missing in %s' % sCardSet)
        oNotebook.append_page(AutoScrolledWindow(
            _make_align_list(aMsgs), True), oHeading)
    # pylint: disable-msg=E1101
    # pylint misses vbox methods
    oResultDlg.vbox.pack_start(oNotebook)
    oResultDlg.set_size_request(600, 600)
    oResultDlg.show_all()
    oResultDlg.run()
    oResultDlg.destroy()

def _test_card_sets(aCardSetNames, oParentCS):
    """Test if the Card Sets are actaully independent by
       looking for cards common to the sets"""
    dCards = {}
    for sCardSetName in aCardSetNames:
        oCS = IPhysicalCardSet(sCardSetName)
        _get_cards(oCS, dCards)
    dParent = {}
    _get_cards(oParentCS, dParent)
    dMissing = {}
    for oCard, oInfo in dCards.iteritems():
        if oCard not in dParent:
            dMissing[oCard] = oInfo
        elif dParent[oCard].iCount < oInfo.iCount:
            # the dict ensures we don't need a copy
            dMissing[oCard] = oInfo
            dMissing[oCard].iCount -= dParent[oCard].iCount
    if dMissing:
        _display_results(dMissing, oParentCS)
    else:
        sMessage = "No cards missing from %s" % oParentCS.name
        do_complaint(sMessage, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, True)

class CardSetIndependence(CardListPlugin):
    """Provides a plugin for testing whether card sets are independant.

       Independence in this cases means that there are enought cards in
       the parent card set to construct all the selected child card sets
       simulatenously.

       We don't test the case when parent is None, since there's nothing
       particularly sensible to say there. We also don't do anything
       when there is only 1 child, for similiar justification.
       """
    dTableVersions = {PhysicalCardSet : [1, 2, 3, 4, 5]}
    aModelsSupported = [PhysicalCardSet]

    def get_menu_item(self):
        """Register with the 'Plugins' Menu"""
        if not self.check_versions() or not self.check_model_type():
            return None
        oTest = gtk.MenuItem("Test Card Set Independence")
        oTest.connect("activate", self.activate)
        return ('Plugins', oTest)

    # pylint: disable-msg=W0613
    # oWidget required by function signature
    def activate(self, oWidget):
        """Create the dialog in response to the menu item."""
        oDlg = self.make_dialog()
        if oDlg:
            oDlg.run()

    # pylint: enable-msg=W0613

    def make_dialog(self):
        """Create the list of card sets to select"""
        # pylint: disable-msg=W0201, E1101
        # E1101: PyProtocols confuses pylint
        # W0201: No need to define oThisCardSet, oCSList & oInUseButton in
        # __init__
        self.oThisCardSet = IPhysicalCardSet(self.view.sSetName)
        if not self.oThisCardSet.parent:
            do_complaint_error("Card Set has no parent, so nothing to test.")
            return None
        oSelect = PhysicalCardSet.selectBy(
                parentID=self.oThisCardSet.parent.id).orderBy('name')
        bInUseSets = PhysicalCardSet.selectBy(
                parentID=self.oThisCardSet.parent.id, inuse=True).count() > 0
        aNames = [oCS.name for oCS in oSelect if oCS.name !=
                self.view.sSetName]
        if not aNames:
            do_complaint_error("No sibling card sets, so nothing to test.")
            return None
        oDlg = SutekhDialog("Choose Card Sets to Test", self.parent,
                          gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                          (gtk.STOCK_OK, gtk.RESPONSE_OK,
                           gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.oCSList = ScrolledList('Card Sets')
        # pylint: disable-msg=E1101
        # vbox confuses pylint
        oDlg.vbox.pack_start(self.oCSList)
        self.oCSList.set_size_request(150, 300)
        self.oCSList.fill_list(aNames)
        self.oInUseButton = gtk.CheckButton(label="Test against all cards sets"
                " marked as in use")
        if bInUseSets:
            oDlg.vbox.pack_start(self.oInUseButton, False, False)
            self.oInUseButton.connect("toggled", self.show_hide_list)
        oDlg.connect("response", self.handle_response)
        oDlg.show_all()
        return oDlg

    def show_hide_list(self, oWidget):
        """Hide the card set list when the user toggles the check box"""
        if oWidget.get_active():
            self.oCSList.set_select_none()
        else:
            self.oCSList.set_select_multiple()

    def handle_response(self, oDlg, oResponse):
        """Handle the response from the dialog."""
        # pylint: disable-msg=E1101
        # Pyprotocols confuses pylint
        if oResponse ==  gtk.RESPONSE_OK:
            if self.oInUseButton.get_active():
                oInUseSets = PhysicalCardSet.selectBy(
                        parentID=self.oThisCardSet.parent.id, inuse=True)
                aCardSetNames = [oCS.name for oCS in oInUseSets]
                if self.view.sSetName not in aCardSetNames:
                    aCardSetNames.append(self.view.sSetName)
            else:
                aCardSetNames = [self.view.sSetName]
                aCardSetNames.extend(self.oCSList.get_selection())
            _test_card_sets(aCardSetNames, self.oThisCardSet.parent)
        oDlg.destroy()


# pylint: disable-msg=C0103
# accept plugin name
plugin = CardSetIndependence
