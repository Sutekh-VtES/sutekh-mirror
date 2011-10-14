# CardSetCompare.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>,
# Copyright 2006, 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""Compare the contents of two card sets"""

import gtk
from sutekh.core.SutekhObjects import PhysicalCard, IPhysicalCard, \
        PhysicalCardSet, IAbstractCard, IPhysicalCardSet
from sutekh.core.Filters import PhysicalCardSetFilter
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error
from sutekh.gui.CardSetsListView import CardSetsListView
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.gui.GuiCardSetFunctions import create_card_set

UNKNOWN_EXP = 'Unspecified Expansion'


def _get_card_set_list(aCardSetNames, bIgnoreExpansions):
    """Get the differences and common cards for the card sets."""
    # Only compare abstract cards
    dFullCardList = {}
    for sCardSetName in aCardSetNames:
        oFilter = PhysicalCardSetFilter(sCardSetName)
        oCardSet = oFilter.select(PhysicalCard)
        for oCard in oCardSet:
            # pylint: disable-msg=E1101
            # pylint doesn't see IAbstractCard methods
            oAbsCard = IAbstractCard(oCard)
            if bIgnoreExpansions:
                oKey = (oAbsCard, oAbsCard.name, None)
            else:
                if oCard.expansion:
                    oKey = (oCard, oAbsCard.name, oCard.expansion.name)
                else:
                    oKey = (oAbsCard, oAbsCard.name, UNKNOWN_EXP)
            dFullCardList.setdefault(oKey, {aCardSetNames[0]: 0,
                aCardSetNames[1]: 0})
            dFullCardList[oKey][sCardSetName] += 1
    dDifferences = {aCardSetNames[0]: {}, aCardSetNames[1]: {}}
    dCommon = {}
    for tCardInfo in dFullCardList:
        iDiff = dFullCardList[tCardInfo][aCardSetNames[0]] - \
                dFullCardList[tCardInfo][aCardSetNames[1]]
        iCommon = min(dFullCardList[tCardInfo][aCardSetNames[0]],
                dFullCardList[tCardInfo][aCardSetNames[1]])
        if iDiff > 0:
            dDifferences[aCardSetNames[0]][tCardInfo[0]] = (tCardInfo[1],
                    tCardInfo[2], iDiff)
        elif iDiff < 0:
            dDifferences[aCardSetNames[1]][tCardInfo[0]] = (tCardInfo[1],
                    tCardInfo[2], abs(iDiff))
        if iCommon > 0:
            dCommon[tCardInfo[0]] = (tCardInfo[1], tCardInfo[2], iCommon)
    return (dDifferences, dCommon)


class CardSetCompare(SutekhPlugin):
    """Compare Two Card Sets

       Display a gtk.Notebook containing tabs for common cards, and cards
       only in each of the card sets.
       """
    dTableVersions = {PhysicalCardSet: (5, 6)}
    aModelsSupported = (PhysicalCardSet,)

    def get_menu_item(self):
        """Register on the 'Analyze' menu."""
        if not self.check_versions() or not self.check_model_type():
            return None
        oCompare = gtk.MenuItem("Compare with another Card Set")
        oCompare.connect("activate", self.activate)
        return ('Analyze', oCompare)

    def activate(self, _oWidget):
        """Create the dialog for choosing the second card set."""
        oDlg = SutekhDialog("Choose Card Set to Compare with", self.parent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                    gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        oCSView = CardSetsListView(None, oDlg)
        # pylint: disable-msg=E1101
        # pylint misses vbox methods
        oCSView.set_select_single()
        oCSView.exclude_set(self.view.sSetName)
        oDlg.vbox.pack_start(AutoScrolledWindow(oCSView), expand=True)
        oIgnoreExpansions = gtk.CheckButton("Ignore Expansions")
        oDlg.vbox.pack_start(oIgnoreExpansions)
        oCSView.set_size_request(450, 300)
        oDlg.connect("response", self.handle_response, oCSView,
                oIgnoreExpansions)
        oDlg.show_all()
        oDlg.run()
        oDlg.destroy()

    def handle_response(self, _oWidget, iResponse, oCSView, oIgnoreExpansions):
        """Handle response from the dialog."""
        if iResponse == gtk.RESPONSE_OK:
            aCardSetNames = [self.view.sSetName]
            sSet = oCSView.get_selected_card_set()
            if not sSet:
                do_complaint_error("Need to choose a card set to compare to")
            else:
                aCardSetNames.append(sSet)
                self.comp_card_sets(aCardSetNames,
                        oIgnoreExpansions.get_active())

    def comp_card_sets(self, aCardSetNames, bIgnoreExpansions):
        """Display the results of comparing the card sets."""
        def format_list(dCardInfo, sColor):
            """Format the list of cards for display."""
            oLabel = gtk.Label()
            oAlign = gtk.Alignment()
            oAlign.add(oLabel)
            oAlign.set_padding(0, 0, 5, 0)  # offset from the left edge
            oGroupedCards = self.model.groupby(dCardInfo, IAbstractCard)
            sContents = ""
            for sGroup, oGroupIter in oGroupedCards:
                aList = [dCardInfo[x] for x in oGroupIter]
                iTot = sum([x[2] for x in aList])
                aList.sort()
                sContents += '<span foreground="blue">%s - %d cards' \
                        '</span>\n' % (sGroup, iTot)
                for sCardName, sExpansion, iCount in aList:
                    sContents += u'\t%(num)d \u00D7 <span foreground =' \
                            ' "%(color)s"> %(name)s' % {
                                    'num': iCount,
                                    'color': sColor,
                                    'name': sCardName,
                                    }
                    if sExpansion:
                        sContents += " (%s)</span>\n" % sExpansion
                    else:
                        sContents += "</span>\n"
            if sContents:
                oLabel.set_markup(sContents)
            else:
                oLabel.set_text('No Cards')
            return oAlign

        def make_page(oList, dCardData):
            """Setup the list + button for the notebook"""
            oPage = gtk.VBox(False)
            oPage.pack_start(AutoScrolledWindow(oList, True), True)
            if dCardData:
                oButton = gtk.Button('Create Card Set from this list')
                oButton.connect('clicked', self.create_card_set,
                        dCardData)
                oPage.pack_start(oButton, False)
            return oPage

        (dDifferences, dCommon) = _get_card_set_list(aCardSetNames,
                bIgnoreExpansions)
        oResultDlg = SutekhDialog("Card Comparison", self.parent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        oNotebook = gtk.Notebook()
        oNotebook.set_scrollable(True)
        oNotebook.popup_enable()
        oHeading = gtk.Label()
        sTabText = 'Common Cards'
        oHeading.set_markup('<span foreground = "blue">%s</span>' % sTabText)
        oComm = format_list(dCommon, 'green')
        oPage = make_page(oComm, dCommon)
        oNotebook.append_page_menu(oPage, oHeading, gtk.Label(sTabText))
        oHeading = gtk.Label()
        sTabText = 'Cards only in %s' % self.escape(aCardSetNames[0])
        oHeading.set_markup('<span foreground = "red">%s</span>' % sTabText)
        oDiff1 = format_list(dDifferences[aCardSetNames[0]], 'red')
        oPage = make_page(oDiff1, dDifferences[aCardSetNames[0]])
        oNotebook.append_page_menu(oPage, oHeading, gtk.Label(sTabText))
        sTabText = 'Cards only in %s' % self.escape(aCardSetNames[1])
        oHeading = gtk.Label()
        oHeading.set_markup('<span foreground = "red">%s</span>' % sTabText)
        oDiff2 = format_list(dDifferences[aCardSetNames[1]], 'red')
        oPage = make_page(oDiff2, dDifferences[aCardSetNames[1]])
        oNotebook.append_page_menu(oPage, oHeading, gtk.Label(sTabText))
        # pylint: disable-msg=E1101
        # pylint misses vbox methods
        oResultDlg.vbox.pack_start(oNotebook)
        oResultDlg.set_size_request(600, 600)
        oResultDlg.show_all()
        oResultDlg.run()
        oResultDlg.destroy()

    def create_card_set(self, _oButton, dCardData):
        """Create a card set from the card list"""
        sCSName = create_card_set(self.parent)
        if not sCSName:
            return  # User cancelled, so skip out
        oCardSet = IPhysicalCardSet(sCSName)
        for oCard in dCardData:
            _sCardName, sExpansionName, iCnt = dCardData[oCard]
            if sExpansionName == UNKNOWN_EXP:
                # Dealing with abstract cards in the list
                oPhysCard = IPhysicalCard((oCard, None))
            else:
                # Dealing with pysical cards in the list
                oPhysCard = oCard
            # pylint: disable-msg=E1101
            # E1101 - sqlobject confuses pylint
            for _iNum in range(iCnt):
                oCardSet.addPhysicalCard(oPhysCard)
        self.open_cs(sCSName)


plugin = CardSetCompare
