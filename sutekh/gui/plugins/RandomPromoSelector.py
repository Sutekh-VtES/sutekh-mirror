# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Dialog to display deck analysis software
# Copyright 2011 Simon Cross <hodgestar+sutekh@gmail.com>,
# GPL - see COPYING for details
"""Draw random groups of cards from a card set.

For example, this is useful for generating sets of promos to
hand out at a tournament.
"""

import gtk
from random import shuffle
from sutekh.base.core.BaseObjects import PhysicalCardSet, IAbstractCard
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.base.gui.SutekhDialog import SutekhDialog
from sutekh.base.gui.AutoScrolledWindow import AutoScrolledWindow


class RandomPromoDialog(SutekhDialog):
    # pylint: disable=R0904
    # R0904 - gtk Widget, so has many public methods
    """Dialog for displaying random sets of cards."""

    def __init__(self, oParent, aCards):
        super(RandomPromoDialog, self).__init__(
            'Generate random groups of cards',
            oParent, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_OK, gtk.RESPONSE_OK,
             gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        oCardsPerGroupAdj = gtk.Adjustment(value=2, lower=1, upper=100,
                                           step_incr=1)
        oNumberOfGroupsAdj = gtk.Adjustment(value=10, lower=1, upper=100,
                                            step_incr=1)

        self._aCards = aCards
        self._oCardsPerGroup = gtk.SpinButton(oCardsPerGroupAdj)
        self._oNumberOfGroups = gtk.SpinButton(oNumberOfGroupsAdj)
        self._oResultsBuffer = gtk.TextBuffer()

        oHbox = gtk.HBox()
        oHbox.pack_start(gtk.Label("Cards per group:"), expand=False,
                         padding=5)
        oHbox.pack_start(self._oCardsPerGroup, expand=False)
        # pylint: disable=E1101
        # vbox confuses pylint
        self.vbox.pack_start(oHbox, expand=False)

        oHbox = gtk.HBox()
        oHbox.pack_start(gtk.Label("Number of groups:"), expand=False,
                         padding=5)
        oHbox.pack_start(self._oNumberOfGroups, expand=False)
        self.vbox.pack_start(oHbox, expand=False)

        oResampleButton = gtk.Button("Resample")
        self.vbox.pack_start(oResampleButton, expand=False)

        self.vbox.pack_start(gtk.Label("Groups:"), expand=False)
        oResults = gtk.TextView(self._oResultsBuffer)
        oResults.set_editable(False)
        self.vbox.pack_start(AutoScrolledWindow(oResults))

        self._oCardsPerGroup.connect('value-changed', self._update_results)
        self._oNumberOfGroups.connect('value-changed', self._update_results)
        oResampleButton.connect('clicked', self._resample)

        self._resample(None)

        self.show_all()

    def _resample(self, _oWidget):
        """Shuffle the internal list of cards."""
        shuffle(self._aCards)
        self._update_results(None)

    def _update_results(self, _oWidget):
        """Update the text showing the groups of cards."""
        iCardsPerGroup = int(self._oCardsPerGroup.get_value())
        iSampleSize = int(iCardsPerGroup * self._oNumberOfGroups.get_value())
        iSampleSize = min(iSampleSize, len(self._aCards))

        aStrs, iCnt = [], 0
        while iCnt < iSampleSize:
            oCard = self._aCards[iCnt]
            aStrs.append(oCard.name)
            if iCnt % iCardsPerGroup == iCardsPerGroup - 1:
                aStrs.append(u"--")
            iCnt += 1
        self._oResultsBuffer.set_text("\n".join(aStrs))


class RandomPromoSelector(SutekhPlugin):
    """Generate random groups of cards."""
    dTableVersions = {PhysicalCardSet: (4, 5, 6, 7)}
    aModelsSupported = (PhysicalCardSet,)

    # pylint: disable=W0142
    # **magic OK here
    def __init__(self, *args, **kwargs):
        super(RandomPromoSelector, self).__init__(*args, **kwargs)

    def get_menu_item(self):
        """Register on the 'Actions' menu"""
        if not self.check_versions() or not self.check_model_type():
            return None
        oCardDraw = gtk.MenuItem("Generate random groups of cards")
        oCardDraw.connect("activate", self.activate)
        return ('Actions', oCardDraw)

    def activate(self, _oWidget):
        """Create the actual dialog, and populate it"""
        oFilter = self.model.get_current_filter()
        aCards = [IAbstractCard(oCard) for oCard
                  in self.model.get_card_iterator(oFilter)]

        oDialog = RandomPromoDialog(self.parent, aCards)
        oDialog.set_size_request(450, 600)
        oDialog.show_all()

        oDialog.run()
        oDialog.destroy()


plugin = RandomPromoSelector
