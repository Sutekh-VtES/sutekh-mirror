# CardSetCompare.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>,
# Copyright 2006, 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""Compare the contents of two card sets"""

import gtk
from sutekh.core.SutekhObjects import PhysicalCard, \
        PhysicalCardSet, IAbstractCard
from sutekh.core.Filters import PhysicalCardSetFilter
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error
from sutekh.gui.ScrolledList import ScrolledList
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow

def _get_card_set_list(aCardSetNames, bUseExpansions):
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
            if bUseExpansions:
                if oCard.expansion:
                    tKey = (oAbsCard.name, oCard.expansion.name)
                else:
                    tKey = (oAbsCard.name, 'Unspecified Expansion')
            else:
                tKey = (oAbsCard.name, None)
            dFullCardList.setdefault(tKey, {aCardSetNames[0] : 0,
                aCardSetNames[1] : 0})
            dFullCardList[tKey][sCardSetName] += 1
    dDifferences = { aCardSetNames[0] : [], aCardSetNames[1] : [] }
    aCommon = []
    for tCardInfo in dFullCardList:
        iDiff = dFullCardList[tCardInfo][aCardSetNames[0]] - \
                dFullCardList[tCardInfo][aCardSetNames[1]]
        iCommon = min(dFullCardList[tCardInfo][aCardSetNames[0]],
                dFullCardList[tCardInfo][aCardSetNames[1]])
        if iDiff > 0:
            dDifferences[aCardSetNames[0]].append((tCardInfo[0], tCardInfo[1],
                iDiff))
        elif iDiff < 0:
            dDifferences[aCardSetNames[1]].append((tCardInfo[0], tCardInfo[1],
                abs(iDiff)))
        if iCommon > 0:
            aCommon.append((tCardInfo[0], tCardInfo[1], iCommon))
    return (dDifferences, aCommon)


class CardSetCompare(CardListPlugin):
    """Compare Two Card Sets

       Display a gtk.Notebook containing tabs for common cards, and cards
       only in each of the card sets.
       """
    dTableVersions = {PhysicalCardSet : [5]}
    aModelsSupported = [PhysicalCardSet]

    def get_menu_item(self):
        """Register on the 'Plugins' menu."""
        if not self.check_versions() or not self.check_model_type():
            return None
        oCompare = gtk.MenuItem("Compare with another Card Set")
        oCompare.connect("activate", self.activate)
        return ('Plugins', oCompare)

    # pylint: disable-msg=W0613
    # oWidget required by gtk function signature
    def activate(self, oWidget):
        """Create the dialog for choosing the second card set."""
        oDlg = SutekhDialog("Choose Card Set to Compare with", self.parent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                    gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        oSelect = PhysicalCardSet.select().orderBy('name')
        oCSList = ScrolledList('Card Sets')
        oCSList.set_select_single()
        # pylint: disable-msg=E1101
        # pylint misses vbox methods
        oDlg.vbox.pack_start(oCSList)
        oUseExpansions = gtk.CheckButton("Consider Expansions as well")
        oDlg.vbox.pack_start(oUseExpansions)
        oCSList.set_size_request(150, 300)
        aVals = [oCS.name for oCS in oSelect if oCS.name != self.view.sSetName]
        oCSList.fill_list(aVals)
        oDlg.connect("response", self.handle_response, oCSList, oUseExpansions)
        oDlg.show_all()
        oDlg.run()
        oDlg.destroy()

    def handle_response(self, oWidget, iResponse, oCSList, oUseExpansions):
        """Handle response from the dialog."""
        if iResponse ==  gtk.RESPONSE_OK:
            aCardSetNames = [self.view.sSetName]
            aCardSetNames.extend(oCSList.get_selection())
            if len(aCardSetNames) != 2:
                do_complaint_error("Need to choose a card set to compare to")
            else:
                self.comp_card_sets(aCardSetNames, oUseExpansions.get_active())

    def comp_card_sets(self, aCardSetNames, bUseExpansions):
        """Display the results of comparing the card sets."""
        def format_list(aList, sColor):
            """Format the list of cards for display."""
            oLabel = gtk.Label()
            oAlign = gtk.Alignment()
            oAlign.add(oLabel)
            oAlign.set_padding(0, 0, 5, 0) # offset a little from the left edge
            if len(aList) > 0:
                sContents = ""
                aList.sort()
                aList.sort(key=lambda x: x[1], reverse=True)
                # sort alphabetically, then reverse sort by card count
                # stable sorting means this gives the desired ordering
                for sCardName, sExpansion, iCount in aList:
                    sContents += '%(num)d X <span foreground = "%(color)s">' \
                            '%(name)s' % {
                                    'num' : iCount,
                                    'color' : sColor,
                                    'name' : sCardName,
                                    }
                    if sExpansion:
                        sContents += " (%s)</span>\n" % sExpansion
                    else:
                        sContents += "</span>\n"
                oLabel.set_markup(sContents)
            else:
                oLabel.set_text('No Cards')
            return oAlign

        (dDifferences, aCommon) = _get_card_set_list(aCardSetNames,
                bUseExpansions)
        oResultDlg = SutekhDialog("Card Comparison", self.parent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        oNotebook = gtk.Notebook()
        oNotebook.set_scrollable(True)
        oNotebook.popup_enable()
        oHeading = gtk.Label()
        oHeading.set_markup('<span foreground = "blue">Common Cards</span>')
        oComm = format_list(aCommon, 'green')
        oNotebook.append_page(AutoScrolledWindow(oComm, True), oHeading)
        oDiff1 = format_list(dDifferences[aCardSetNames[0]], 'red')
        oHeading = gtk.Label()
        oHeading.set_markup('<span foreground = "red">Cards only in %s</span>'
                % aCardSetNames[0])
        oNotebook.append_page(AutoScrolledWindow(oDiff1, True), oHeading)
        oDiff2 = format_list(dDifferences[aCardSetNames[1]], 'red')
        oHeading = gtk.Label()
        oHeading.set_markup('<span foreground = "red">Cards only in %s</span>'
                % aCardSetNames[1])
        oNotebook.append_page(AutoScrolledWindow(oDiff2, True), oHeading)
        # pylint: disable-msg=E1101
        # pylint misses vbox methods
        oResultDlg.vbox.pack_start(oNotebook)
        oResultDlg.set_size_request(600, 600)
        oResultDlg.show_all()
        oResultDlg.run()
        oResultDlg.destroy()


# pylint: disable-msg=C0103
# accept plugin name
plugin = CardSetCompare
