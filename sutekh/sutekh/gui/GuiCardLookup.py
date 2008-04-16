# GuiCardLookup.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""
Lookup AbstractCards for a list of card names, presenting the user with a GUI
to pick unknown cards from.
"""

import gtk
import pango
import gobject
from sqlobject import SQLObjectNotFound
from sutekh.core.SutekhObjects import AbstractCard, PhysicalCard, IExpansion, \
        MapPhysicalCardToPhysicalCardSet, Expansion
from sutekh.core.CardLookup import AbstractCardLookup, PhysicalCardLookup, \
        ExpansionLookup, LookupFailed
from sutekh.core.Filters import CardNameFilter
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error
from sutekh.gui.CellRendererSutekhButton import CellRendererSutekhButton
from sutekh.gui.PhysicalCardView import PhysicalCardView
from sutekh.gui.AbstractCardView import AbstractCardView
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow

class DummyController(object):
    """Dummy controller class, so we can use the card views directly"""
    def __init__(self, sFilterType):
        self.sFilterType = sFilterType

    filtertype = property(fget=lambda self: self.sFilterType)

    def set_card_text(self, sCardName):
        """Ignore card text updates."""
        pass

class ACLlookupView(AbstractCardView):
    """Specialised version for the Card Lookup."""
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods.

    def __init__(self, oDialogWindow):
        oController = DummyController('AbstractCard')
        super(ACLlookupView, self).__init__(oController, oDialogWindow)
        self.get_selection().set_mode(gtk.SELECTION_SINGLE)

    @staticmethod
    def is_physical():
        """Whether this is a physical card view (False)."""
        return False

    def get_selected_card(self):
        """Return the selected card with a dummy expansion of ''."""
        sNewName = 'No Card'
        oModel, aSelection = self.get_selection().get_selected_rows()
        for oPath in aSelection:
            sNewName = oModel.get_card_name_from_path(oPath)
        return sNewName, ''

class PCLwithNumbersView(PhysicalCardView):
    """Also show current allocation of cards in the physical card view."""
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods.

    def __init__(self, oDialogWindow):
        oController = DummyController('PhysicalCard')
        super(PCLwithNumbersView, self).__init__(oController, oDialogWindow)
        self.get_selection().set_mode(gtk.SELECTION_SINGLE)
        self.dAssignedCards = {}
        oCell1 = gtk.CellRendererText()
        self.oCardCountCol = gtk.TreeViewColumn("Set #", oCell1)
        self.oCardCountCol.set_cell_data_func(oCell1,
            self._render_cardcount_column)

    @staticmethod
    def is_physical():
        """Whether this is a physical card view (True)."""
        return True

    def get_selected_card(self):
        """Return the selected card and expansion."""
        sNewName = 'No Card'
        sExpansion = '  Unpecified Expansion'
        oModel, aSelection = self.get_selection().get_selected_rows()
        for oPath in aSelection:
            # pylint: disable-msg=W0612
            # only interested in sNewName and sExpansion
            sNewName, sExpansion, iCount, iDepth = \
                oModel.get_all_from_path(oPath)
        if sExpansion is None:
            sExpansion = ''
        return sNewName, sExpansion

    def set_card_set_holder_numbers(self, aPhysCards, dCandCards):
        """
        Mark numbers already found for the card set in the model
        aPhysCards is those cards assigned without any issue by physical_lookup
        dCandCards is those cards currently selected by the user to be added
        """
        self.dAssignedCards = {}
        aCandCards = []
        for aTheseCards in dCandCards.itervalues():
            aCandCards.extend(aTheseCards)
        for oCard in aPhysCards + aCandCards:
            sName = oCard.abstractCard.name
            self.dAssignedCards.setdefault(sName, {})
            if oCard.expansion is None:
                sExpansion = '  Unspecified Expansion'
            else:
                sExpansion = oCard.expansion.name
            self.dAssignedCards[sName].setdefault(sExpansion, 0)
            self.dAssignedCards[sName][sExpansion] += 1
            for oType in oCard.abstractCard.cardtype:
                # Also do the right thing for esction headers
                self.dAssignedCards.setdefault(oType.name, 0)
                self.dAssignedCards[oType.name] += 1

    def remove_card_set_column(self):
        """Disable the card count column."""
        self.remove_column(self.oCardCountCol)

    def add_card_set_count_column(self):
        """Enable the card count column."""
        self.insert_column(self.oCardCountCol, 1)

    # pylint: disable-msg=W0613
    # oColumn, oModel required by function signature
    def _render_cardcount_column(self, oColumn, oCell, oModel, oIter):
        """Render card count into card count cell."""
        iCnt = self._get_cardcount_data(oIter)
        if iCnt is not None:
            oCell.set_property("text", str(iCnt))
        else:
            oCell.set_property("text", "")

    # pylint: enable-msg=W0613

    def _get_cardcount_data(self, oIter):
        """Return the number of cards that fall within a model iterator."""
        iDepth = self._oModel.iter_depth(oIter)
        if iDepth == 0:
            sSectionName = self._oModel.get_name_from_iter(oIter)
            if sSectionName in self.dAssignedCards:
                return self.dAssignedCards[sSectionName]
        elif iDepth == 1:
            # Get Card Name from this
            sCardName = self._oModel.get_name_from_iter(oIter)
            if sCardName in self.dAssignedCards:
                # Get total for this card
                iTot = 0
                for sExpansion, iCnt in \
                    self.dAssignedCards[sCardName].iteritems():
                    iTot += iCnt
                return iTot
        elif iDepth == 2:
            oPath = self._oModel.get_path(oIter)
            sCardName, sExpansion, iCnt, iDepth = \
                self._oModel.get_all_from_path(oPath)
            if sCardName in self.dAssignedCards:
                if sExpansion in self.dAssignedCards[sCardName]:
                    return self.dAssignedCards[sCardName][sExpansion]
                else:
                    return 0
        return None

class ReplacementTreeView(gtk.TreeView):
    """A TreeView which tracks the current set of replacement cards."""
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods.

    def __init__(self, oCardListView, oFilterToggleButton):
        """Construct a gtk.TreeView object showing the current
           card replacements.

           For abstract cards, the card names are stored as is.
           For physical cards, the card names have " exp: <expansion>"
           appended.
           """
        # ListStore: count, missing card, replacement
        oModel = gtk.ListStore(gobject.TYPE_INT, gobject.TYPE_STRING,
                               gobject.TYPE_STRING)

        super(ReplacementTreeView, self).__init__(oModel)
        self.oCardListView = oCardListView
        self.oModel = oModel
        self.bPhysical = self.oCardListView.is_physical()
        self.oFilterToggleButton = oFilterToggleButton

        if self.bPhysical:
            self.dCandidateCards = {}

            oCell1 = gtk.CellRendererText()
            oCell1.set_property('style', pango.STYLE_ITALIC)

            oColumn1 = gtk.TreeViewColumn("#", oCell1, text=0)
            oColumn1.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            oColumn1.set_fixed_width(40)
            self.append_column(oColumn1)

        oCell2 = gtk.CellRendererText()
        oCell2.set_property('style', pango.STYLE_ITALIC)

        oCell3 = gtk.CellRendererText()
        oCell3.set_property('style', pango.STYLE_ITALIC)

        oCell4 = CellRendererSutekhButton(bShowIcon=True)
        oCell4.load_icon(gtk.STOCK_OK, self) # use selected card

        oCell5 = CellRendererSutekhButton(bShowIcon=True)
        oCell5.load_icon(gtk.STOCK_REMOVE, self) # ignore current card

        oCell6 = CellRendererSutekhButton(bShowIcon=True)
        oCell6.load_icon(gtk.STOCK_FIND, self) # filter out best guesses

        oColumn2 = gtk.TreeViewColumn("Missing Card", oCell2, text=1)
        oColumn2.set_expand(True)
        oColumn2.set_sort_column_id(1)
        self.append_column(oColumn2)

        oColumn3 = gtk.TreeViewColumn("Replace With", oCell3, text=2)
        oColumn3.set_expand(True)
        oColumn3.set_sort_column_id(2)
        self.append_column(oColumn3)

        oLabel4 = gtk.Label("Set")
        oLabel4.set_tooltip_text("Use the selected card")
        oColumn4 = gtk.TreeViewColumn("", oCell4)
        oColumn4.set_widget(oLabel4)
        oColumn4.set_fixed_width(22)
        oColumn4.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.append_column(oColumn4)

        oLabel5 = gtk.Label("Ignore")
        oLabel5.set_tooltip_text("Ignore the current card")
        oColumn5 = gtk.TreeViewColumn("", oCell5)
        oColumn5.set_widget(oLabel5)
        oColumn5.set_fixed_width(22)
        oColumn5.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.append_column(oColumn5)

        oLabel6 = gtk.Label("Filter")
        oLabel6.set_tooltip_text("Filter on best guess")
        oColumn6 = gtk.TreeViewColumn("", oCell6)
        oColumn6.set_widget(oLabel6)
        oColumn6.set_fixed_width(22)
        oColumn6.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.append_column(oColumn6)

        oCell4.connect('clicked', self._set_to_selection)
        oCell5.connect('clicked', self._set_ignore)
        oCell6.connect('clicked', self._set_filter)

    # pylint: disable-msg=W0613
    # oCell required by function signature
    def _set_to_selection(self, oCell, oPath):
        """Set the replacement card to the selected entry"""

        # We handle PhysicalCards on a like-for-like matching case.
        # For cases where the user selects an expansion with too few
        # cards, but where there are enough phyiscal cards, we do the
        # best we can

        oIter = self.oModel.get_iter(oPath)
        iCnt, sFullName = self.oModel.get(oIter, 0, 1)

        sNewName, sExpansion = self.oCardListView.get_selected_card()
        if sNewName == 'No Card':
            do_complaint_error("Please select a card")
            return

        if self.bPhysical:
            self.dCandidateCards[sFullName] = []
            aTheseCards = self.dCandidateCards[sFullName]

            aAssignedCards = []
            for aButtonCards in self.dCandCards.itervalues():
                aAssignedCards.extend(aButtonCards)

            if not self._check_physical_cards(sNewName, iCnt, self.aPhysCards,
                                          aAssignedCards, aTheseCards):
                do_complaint_error("Not enough copies of %s" % sNewName)
                return

            if not self._check_cards_with_expansion(sNewName,
                           sExpansion, iCnt, self.aPhysCards,
                           aAssignedCards, aTheseCards):
                do_complaint_error(
                    "Not enough copies of %s from expansion %s\n." \
                    "Ignoring the expansion specification" % \
                    (sNewName, sExpansion))
                sExpansion = ''

            self.oCardListView.set_card_set_holder_numbers(self.aPhysCards,
                self.dCandidateCards)
            self.oCardListView.queue_draw()

        if sExpansion != '':
            sReplaceWith = sNewName + "  exp: " + sExpansion
        else:
            sReplaceWith = sNewName

        self.oModel.set_value(oIter, 2, sReplaceWith)

    def _set_ignore(self, oCell, oPath):
        """Mark the card as not having a replacement."""
        oIter = self.oModel.get_iter(oPath)
        sFullName = self.oModel.get_value(oIter, 1)

        if self.bPhysical:
            if sFullName in self.dCandidateCards:
                del self.dCandidateCards[sFullName]
                self.oCardListView.set_card_set_holder_numbers(self.aPhysCards,
                    self.dCandidateCards)
                self.oCardListView.queue_draw()

        self.oModel.set_value(oIter, 2, "No Card")

    def _set_filter(self, oCell, oPath):
        """Set the card list filter to the best guess filter for this card."""
        oIter = self.oModel.get_iter(oPath)
        sFullName = self.oModel.get_value(oIter, 1)

        aParts = sFullName.split(' exp: ')
        sName = aParts[0]

        oFilter = self.best_guess_filter(sName)
        self.oCardListView.get_model().selectfilter = oFilter

        if not self.oFilterToggleButton.get_active():
            self.oFilterToggleButton.set_active(True)
        else:
            self.oCardListView.load()

    # pylint: enable-msg=W0613

    @staticmethod
    def _check_physical_cards(sName, iCnt, aPhysCards, aAssignedCards,
                              aSelectedCards):
        """Check that there are enough physical cards to fulfill the
           request.
        """
        try:
            # pylint: disable-msg=E1101
            # SQLObject methods confuse pylint
            oAbs = AbstractCard.byCanonicalName(sName.encode('utf8').lower())
            # pylint: enable-msg=E1101
        except SQLObjectNotFound:
            # Can't find the card, so can't fulfil the request
            return False

        aCandPhysCards = PhysicalCard.selectBy(abstractCardID=oAbs.id)
        for oCard in aCandPhysCards:
            if oCard not in aPhysCards and oCard not in aAssignedCards:
                # Card is a feasible replacement
                iCnt -= 1
                aSelectedCards.append(oCard)
                if iCnt == 0:
                    return True # Can fulfill the request

        return False

    @staticmethod
    def _check_cards_with_expansion(sName, sExpansion, iCnt, aPhysCards,
                                    aAssignedCards, aSelectedCards):
        """Check that there are enough physical cards of the specified
           expansion to fulfill the request.
        """
        # pylint: disable-msg=E1101
        # SQLObject methods confuse pylint
        oAbs = AbstractCard.byCanonicalName(sName.encode('utf8').lower())
        try:
            iExpID = IExpansion(sExpansion).id
        except SQLObjectNotFound:
            iExpID = None
        except KeyError:
            iExpID = None
        # pylint: enable-msg=E1101

        aCandPhysCards = PhysicalCard.selectBy(abstractCardID=oAbs.id,
                                               expansionID=iExpID)
        for oCard in aCandPhysCards:
            if oCard not in aPhysCards and oCard not in aAssignedCards:
                # Card is a feasible replacement
                iCnt -= 1
                # Cycle set of currently selected cards
                aSelectedCards.insert(0, oCard)
                aSelectedCards.pop()
                if iCnt == 0:
                    return True # Can fulfill the request

        return False

    # pylint: disable-msg=W0613
    # oButton required by function signature
    def run_filter_dialog(self, oButton):
        """Display the filter dialog and apply results."""
        self.oCardListView.get_filter(None)
        self.oFilterToggleButton.set_active(
            self.oCardListView.get_model().applyfilter)

    def toggle_apply_filter(self, oButton):
        """Toggle whether the filter is applied."""
        self.oCardListView.get_model().applyfilter = \
            self.oFilterToggleButton.get_active()
        self.oCardListView.load()

    # pylint: enable-msg=W0613

    def toggle_show_cardcount(self, oShowCountsButton):
        """Toggle whether the column with the card counts is visible."""
        if oShowCountsButton.get_active():
            self.oCardListView.set_card_set_holder_numbers(self.aPhysCards,
                self.dCandidateCards)
            self.oCardListView.add_card_set_count_column()
            self.oCardListView.queue_draw()
        else:
            self.oCardListView.remove_card_set_column()

    @staticmethod
    def best_guess_filter(sName):
        """Create a filter for selecting close matches to a card name."""
        # Set the filter on the Card List to one the does a
        # Best guess search
        sFilterString = ' ' + sName.lower() + ' '
        # Kill the's in the string
        sFilterString = sFilterString.replace(' the ', '')
        # Kill commas, as possible issues
        sFilterString = sFilterString.replace(',', '')
        # Wildcard spaces
        sFilterString = sFilterString.replace(' ', '%').lower()
        # Stolen semi-concept from soundex - replace vowels with wildcards
        # Should these be %'s ??
        # (Should at least handle the Rotscheck variation as it stands)
        sFilterString = sFilterString.replace('a', '_')
        sFilterString = sFilterString.replace('e', '_')
        sFilterString = sFilterString.replace('i', '_')
        sFilterString = sFilterString.replace('o', '_')
        sFilterString = sFilterString.replace('u', '_')
        return CardNameFilter(sFilterString)


class GuiLookup(AbstractCardLookup, PhysicalCardLookup, ExpansionLookup):
    """Lookup AbstractCards. Use the user as the AI if a simple lookup fails.
    """

    def __init__(self, oConfig):
        super(GuiLookup, self).__init__()
        self._oConfig = oConfig

    def lookup(self, aNames, sInfo):
        """Lookup missing abstract cards.

           Provides an implementation for AbstractCardLookup.
        """
        dCards = {}
        dUnknownCards = {}

        for sName in aNames:
            if not sName:
                # None here is an explicit ignore from the lookup cache
                dCards[sName] = None
            else:
                try:
                    # pylint: disable-msg=E1101
                    # SQLObject methods confuse pylint
                    oAbs = AbstractCard.byCanonicalName(
                                sName.encode('utf8').lower())
                    # pylint: enable-msg=E1101
                    dCards[sName] = oAbs
                except SQLObjectNotFound:
                    dUnknownCards[sName] = None

        if dUnknownCards:
            if not self._handle_unknown_abstract_cards(dUnknownCards, sInfo):
                raise LookupFailed("Lookup of missing cards aborted by the" \
                                   " user.")

        for sName, sNewName in dUnknownCards.items():
            if sNewName is None:
                continue
            try:
                # pylint: disable-msg=E1101
                # SQLObject methods confuse pylint
                oAbs = AbstractCard.byCanonicalName(
                                        sNewName.encode('utf8').lower())
                # pylint: enable-msg=E1101
                dUnknownCards[sName] = oAbs
            except SQLObjectNotFound:
                raise RuntimeError("Unexpectedly encountered missing" \
                                   " abstract card '%s'." % sNewName)

        def new_card(sName):
            """emulate python 2.5's a = x if C else y"""
            if sName in dCards:
                return dCards[sName]
            else:
                return dUnknownCards[sName]

        return [new_card(sName) for sName in aNames]

    def physical_lookup(self, dCardExpansions, dNameCards, dNameExps, sInfo):
        """Lookup missing physical cards.

           Provides an implementation for PhysicalCardLookup.
        """
        aCards = []
        dUnknownCards = {}

        for sName in dCardExpansions:
            oAbs = dNameCards[sName]
            if oAbs is None:
                continue
            try:
                for sExpansionName in dCardExpansions[sName]:
                    iCnt = dCardExpansions[sName][sExpansionName]
                    oExpansion = dNameExps[sExpansionName]
                    if oExpansion is not None:
                        aPhysCards = PhysicalCard.selectBy(
                                        abstractCardID=oAbs.id,
                                        expansionID=oExpansion.id)
                    else:
                        aPhysCards = PhysicalCard.selectBy(
                                abstractCardID=oAbs.id, expansionID=None)
                    dCardSetCounts = {}
                    for oCard in aPhysCards:
                        iCSCount = MapPhysicalCardToPhysicalCardSet.selectBy(
                                physicalCardID=oCard.id).count()
                        dCardSetCounts[oCard] = iCSCount
                    # Order by count, so we try cards in the fewest card sets
                    # first
                    aPossCards = sorted(dCardSetCounts.items(),
                            key=lambda t: t[1])
                    for oPhys, iCSCount in aPossCards:
                        if oPhys not in aCards \
                                and iCnt > 0:
                            aCards.append(oPhys)
                            iCnt -= 1
                            if iCnt == 0:
                                break
                    if iCnt > 0:
                        dUnknownCards.setdefault((oAbs.name, sExpansionName),
                                0)
                        dUnknownCards[(oAbs.name, sExpansionName)] = iCnt
            except SQLObjectNotFound:
                for sExpansionName in dCardExpansions[sName]:
                    iCnt = dCardExpansions[sName][sExpansionName]
                    oExpansion = dNameExps[sExpansionName]
                    if iCnt > 0:
                        dUnknownCards.setdefault((oAbs.name, sExpansionName),
                                0)
                        dUnknownCards[(oAbs.name, sExpansionName)] = iCnt

        if dUnknownCards:
            # We need to lookup cards in the physical card view
            if not self._handle_unknown_physical_cards(dUnknownCards,
                                                       aCards, sInfo):
                raise LookupFailed("Lookup of missing cards aborted by the" \
                                   " user.")

        return aCards

    def expansion_lookup(self, aExpansionNames, sInfo):
        """Lookup missing expansions.

           Provides an implementation for ExpansionLookup.
        """
        dExps = {}
        dUnknownExps = {}

        for sExp in aExpansionNames:
            if not sExp:
                dExps[sExp] = None
            else:
                try:
                    oExp = IExpansion(sExp)
                    dExps[sExp] = oExp
                except KeyError:
                    dUnknownExps[sExp] = None

        if dUnknownExps:
            if not self._handle_unknown_expansions(dUnknownExps, sInfo):
                raise LookupFailed("Lookup of missing expansions aborted by" \
                                   " the user.")

        for sName, sNewName in dUnknownExps.items():
            if sNewName is None:
                continue
            try:
                oExp = IExpansion(sNewName)
                dUnknownExps[sName] = oExp
            except KeyError:
                raise RuntimeError("Unexpectedly encountered" \
                                   " missing expansion '%s'." % sNewName)

        def new_exp(sName):
            """emulate python 2.5's a = x if C else y"""
            if sName in dExps:
                return dExps[sName]
            else:
                return dUnknownExps[sName]

        return [new_exp(sName) for sName in aExpansionNames]

    def _handle_unknown_physical_cards(self, dUnknownCards, aPhysCards, sInfo):
        """Handle unknwon physical cards

           We allow the user to select the correct replacements from the
           Physical Card List
        """

        oUnknownDialog = SutekhDialog( \
                "Unknown Physical cards found importing %s" % sInfo, None,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                 gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        # TODO: document this gets used or clean it up somehow
        # Needed by the cardlist model's call the the filter dialog
        oUnknownDialog.config_file = self._oConfig

        sMsg1 = "While importing %s\n" \
          "The following cards could not be found in the Physical Card List:" \
          "\nChoose how to handle these cards?\n" % sInfo

        sMsg2 = "OK creates the card set, " \
          "Cancel aborts the creation of the card set"

        # pylint: disable-msg=E1101
        # vbox confuses pylint

        oMesgLabel1 = gtk.Label()
        oMesgLabel1.set_text(sMsg1)
        oUnknownDialog.vbox.pack_start(oMesgLabel1, False, False)

        oHBox = gtk.HBox()
        oUnknownDialog.vbox.pack_start(oHBox, True, True)

        oMesgLabel2 = gtk.Label()
        oMesgLabel2.set_text(sMsg2)
        oUnknownDialog.vbox.pack_start(oMesgLabel2)

        oPhysCardView = PCLwithNumbersView(oUnknownDialog)
        oViewWin = AutoScrolledWindow(oPhysCardView)
        oViewWin.set_size_request(200, 600)
        oHBox.pack_start(oViewWin, True, True)

        oVBox = gtk.VBox()
        oHBox.pack_start(oVBox)

        oFilterDialogButton = gtk.Button("Specify Filter")
        oFilterApplyButton = gtk.CheckButton("Apply Filter to view")
        oShowCountsButton = gtk.CheckButton("Show cards assigned to this" \
                                            " card set")
        oShowCountsButton.set_active(True)

        oReplacementView = ReplacementTreeView(oPhysCardView,
                                               oFilterApplyButton)
        oModel = oReplacementView.get_model()

        oReplacementWin = AutoScrolledWindow(oReplacementView)
        oReplacementWin.set_size_request(400, 600)
        oVBox.pack_start(oReplacementWin, True, True)

        oFilterButtons = gtk.HBox()
        oVBox.pack_start(gtk.HSeparator())
        oVBox.pack_start(oFilterButtons)

        oFilterButtons.pack_start(oFilterDialogButton)
        oFilterButtons.pack_start(oFilterApplyButton)
        oFilterButtons.pack_start(oShowCountsButton)

        oFilterDialogButton.connect("clicked",
            oReplacementView.run_filter_dialog)
        oFilterApplyButton.connect("toggled",
            oReplacementView.toggle_apply_filter)
        oShowCountsButton.connect("toggled",
            oReplacementView.toggle_show_cardcount)

        # Populate the model with the card names and best guesses
        for (sName, sExpName), iCnt in dUnknownCards.items():
            sBestGuess = "No Card"
            sFullName = "%s exp: %s" % (sName, sExpName)

            oIter = oModel.append(None)
            oModel.set(oIter, 0, iCnt, 1, sFullName, 2, sBestGuess)

        oUnknownDialog.vbox.show_all()

        iResponse = oUnknownDialog.run()
        oUnknownDialog.destroy()

        if iResponse == gtk.RESPONSE_OK:
            # For cards marked as replaced, add them to the list of
            # Physical Cards
            oIter = oModel.get_iter_root()
            while not oIter is None:
                sFullName, sNewFullName = oModel.get(oIter, 1, 2)
                sName, sExpName = sFullName.split(' exp: ')

                aParts = sNewFullName.split(' exp: ')
                sNewName = aParts[0]
                if len(aParts) == 1:
                    sNewExpName = aParts[1]
                    try:
                        iExpID = IExpansion(sNewExpName).id
                    except SQLObjectNotFound:
                        iExpID = None
                    except KeyError:
                        iExpID = None
                else:
                    sNewExpName = ''

                iCnt = dUnknownCards[(sName, sExpName)]

                if sNewName != "No Card":
                    # Find First physical card that matches this name
                    # that's not in aPhysCards
                    oAbs = AbstractCard.byCanonicalName(
                            sNewName.encode('utf8').lower())
                    if sNewExpName != '':
                        aCandPhysCards = PhysicalCard.selectBy(
                            abstractCardID=oAbs.id, expansionID=iExpID)
                    else:
                        aCandPhysCards = PhysicalCard.selectBy(
                            abstractCardID=oAbs.id)
                    for oCard in aCandPhysCards:
                        if oCard not in aPhysCards:
                            if iCnt > 0:
                                iCnt -= 1
                                aPhysCards.append(oCard)
            return True
        else:
            return False

    def _handle_unknown_abstract_cards(self, dUnknownCards, sInfo):
        """Handle the list of unknown abstract cards.

           We allow the user to select the correct replacements from the
           Abstract Card List.
           """
        oUnknownDialog = SutekhDialog( \
                "Unknown cards found importing %s" % sInfo, None,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                 gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        # TODO: document this gets used or clean it up somehow
        # Needed by the cardlist model's call the the filter dialog
        oUnknownDialog.config_file = self._oConfig

        sMsg1 = "While importing %s\n" \
                "The following card names could not be found:\n" \
                "Choose how to handle these cards?\n" % (sInfo)

        sMsg2 = "OK creates the card set, " \
                "Cancel aborts the creation of the card set"

        # pylint: disable-msg=E1101
        # vbox confuses pylint

        oMesgLabel1 = gtk.Label()
        oMesgLabel1.set_text(sMsg1)
        oUnknownDialog.vbox.pack_start(oMesgLabel1, False, False)

        oHBox = gtk.HBox()
        oUnknownDialog.vbox.pack_start(oHBox, True, True)

        oMesgLabel2 = gtk.Label()
        oMesgLabel2.set_text(sMsg2)
        oUnknownDialog.vbox.pack_start(oMesgLabel2)

        oAbsCardView = ACLlookupView(oUnknownDialog)
        oViewWin = AutoScrolledWindow(oAbsCardView)
        oViewWin.set_size_request(200, 600)
        oHBox.pack_start(oViewWin, True, True)

        oVBox = gtk.VBox()
        oHBox.pack_start(oVBox)

        oFilterDialogButton = gtk.Button("Specify Filter")
        oFilterApplyButton = gtk.CheckButton("Apply Filter to view")

        oReplacementView = ReplacementTreeView(oAbsCardView,
            oFilterApplyButton)
        oModel = oReplacementView.get_model()

        oReplacementWin = AutoScrolledWindow(oReplacementView)
        oReplacementWin.set_size_request(400, 600)
        oVBox.pack_start(oReplacementWin, True, True)

        oFilterButtons = gtk.HBox()
        oVBox.pack_start(gtk.HSeparator())
        oVBox.pack_start(oFilterButtons)

        oFilterButtons.pack_start(oFilterDialogButton)
        oFilterButtons.pack_start(oFilterApplyButton)

        oFilterDialogButton.connect("clicked",
            oReplacementView.run_filter_dialog)
        oFilterApplyButton.connect("toggled",
            oReplacementView.toggle_apply_filter)

        # Populate the model with the card names and best guesses
        for sName in dUnknownCards:
            oBestGuessFilter = oReplacementView.best_guess_filter(sName)
            aCards = list(oBestGuessFilter.select(AbstractCard).distinct())
            if len(aCards) == 1:
                sBestGuess = aCards[0].name
            else:
                sBestGuess = "No Card"

            oIter = oModel.append(None)
            # second 1 is the dummy card count
            oModel.set(oIter, 0, 1, 1, sName, 2, sBestGuess)

        oUnknownDialog.vbox.show_all()

        iResponse = oUnknownDialog.run()
        oUnknownDialog.destroy()

        if iResponse == gtk.RESPONSE_OK:
            # For cards marked as replaced, add them to the Holder
            oIter = oModel.get_iter_root()
            while not oIter is None:
                sName, sNewName = oModel.get(oIter, 1, 2)
                if sNewName != "No Card":
                    dUnknownCards[sName] = sNewName
            return True
        else:
            return False

    @staticmethod
    def _handle_unknown_expansions(dUnknownExps, sInfo):
        """Handle the list of unknown expansions.

           We allow the user to select the correct replacements from the
           expansions listed in the database.
           """
        oUnknownDialog = SutekhDialog(
            "Unknown expansions found importing %s" % sInfo, None,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_OK, gtk.RESPONSE_OK,
             gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        aKnownExpansions = list(Expansion.select())

        oMesgLabel1 = gtk.Label()
        oMesgLabel2 = gtk.Label()

        sMsg1 = "While importing %s\n" \
                "The following expansions could not be found:\n" \
                "Choose how to handle these expansions?\n" % (sInfo)
        sMsg2 = "OK continues the card set creation process, " \
                "Cancel aborts the creation of the card set"

        # pylint: disable-msg=E1101
        # vbox confuses pylint

        oMesgLabel1.set_text(sMsg1)
        oUnknownDialog.vbox.pack_start(oMesgLabel1, False, False)

        oButtonBox = gtk.VBox()

        # Fill in the Expansions and options
        dReplacement = {}
        for sName in dUnknownExps:
            oBox = gtk.HBox()
            oLabel = gtk.Label("%s is Unknown: Replace with " % sName)
            oBox.pack_start(oLabel)

            oSelector = gtk.combo_box_new_text()
            oSelector.append_text("No Expansion")
            for oExp in aKnownExpansions:
                oSelector.append_text(oExp.name)

            dReplacement[sName] = oSelector

            oBox.pack_start(dReplacement[sName])
            oButtonBox.pack_start(oBox)

        oUnknownDialog.vbox.pack_start(oButtonBox, True, True)

        oMesgLabel2.set_text(sMsg2)

        oUnknownDialog.vbox.pack_start(oMesgLabel2)
        oUnknownDialog.vbox.show_all()

        iResponse = oUnknownDialog.run()

        oUnknownDialog.destroy()

        if iResponse == gtk.RESPONSE_OK:
            # For cards marked as replaced, add them to the Holder
            for sName in dUnknownExps:
                sNewName = dReplacement[sName].get_active_text()
                if sNewName != "No Expansion":
                    dUnknownExps[sName] = sNewName
            return True
        else:
            return False
