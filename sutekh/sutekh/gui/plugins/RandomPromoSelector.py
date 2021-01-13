# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Dialog to display deck analysis software
# Copyright 2011 Simon Cross <hodgestar+sutekh@gmail.com>,
# GPL - see COPYING for details
"""Draw random groups of cards from a card set.

For example, this is useful for generating sets of promos to
hand out at a tournament.
"""

from random import shuffle

from gi.repository import Gtk

from sutekh.base.core.BaseTables import PhysicalCardSet
from sutekh.base.core.BaseAdapters import IAbstractCard
from sutekh.base.gui.SutekhDialog import SutekhDialog
from sutekh.base.gui.AutoScrolledWindow import AutoScrolledWindow

from sutekh.gui.PluginManager import SutekhPlugin


class RandomPromoDialog(SutekhDialog):
    # pylint: disable=too-many-public-methods
    # Gtk Widget, so has many public methods
    """Dialog for displaying random sets of cards."""

    def __init__(self, oParent, aCards):
        super().__init__(
            'Generate random groups of cards', oParent,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            ("_OK", Gtk.ResponseType.OK,
             "_Cancel", Gtk.ResponseType.CANCEL))

        oCardsPerGroupAdj = Gtk.Adjustment(value=2, lower=1, upper=100,
                                           step_incr=1)
        oNumberOfGroupsAdj = Gtk.Adjustment(value=10, lower=1, upper=100,
                                            step_incr=1)

        self._aCards = aCards
        self._oCardsPerGroup = Gtk.SpinButton()
        self._oCardsPerGroup.set_adjustment(oCardsPerGroupAdj)
        self._oNumberOfGroups = Gtk.SpinButton()
        self._oNumberOfGroups.set_adjustment(oNumberOfGroupsAdj)
        self._oResultsBuffer = Gtk.TextBuffer()

        oHbox = Gtk.HBox()
        oHbox.pack_start(Gtk.Label(label="Cards per group:"), False, True, 5)
        oHbox.pack_start(self._oCardsPerGroup, False, True, 0)
        # pylint: disable=no-member
        # vbox confuses pylint
        self.vbox.pack_start(oHbox, False, True, 0)

        oHbox = Gtk.HBox()
        oHbox.pack_start(Gtk.Label(label="Number of groups:"), False, True, 5)
        oHbox.pack_start(self._oNumberOfGroups, False, True, 0)
        self.vbox.pack_start(oHbox, False, True, 0)

        oResampleButton = Gtk.Button(label="Resample")
        self.vbox.pack_start(oResampleButton, False, True, 0)

        self.vbox.pack_start(Gtk.Label(label="Groups:"), False, True, 0)
        oResults = Gtk.TextView()
        oResults.set_buffer(self._oResultsBuffer)
        oResults.set_editable(False)
        self.vbox.pack_start(AutoScrolledWindow(oResults), True, True, 0)

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_menu_item(self):
        """Register on the 'Actions' menu"""
        oCardDraw = Gtk.MenuItem(label="Generate random groups of cards")
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
