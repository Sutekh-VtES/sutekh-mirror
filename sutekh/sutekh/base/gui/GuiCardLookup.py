# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Lookup AbstractCards for a list of card names, presenting the user with a
   GUI to pick unknown cards from.  """

import re

from gi.repository import GObject, Gtk, Pango

from sqlobject import SQLObjectNotFound
from ..core.BaseTables import AbstractCard, PhysicalCard, Printing
from ..core.BaseAdapters import (IAbstractCard, IPhysicalCard, IExpansion,
                                 IPrinting, IPrintingName)
from ..core.CardLookup import (AbstractCardLookup, PhysicalCardLookup,
                               PrintingLookup, LookupFailed)
from ..core.BaseFilters import best_guess_filter
from .SutekhDialog import SutekhDialog, do_complaint_error
from .CellRendererSutekhButton import CellRendererSutekhButton
from .PhysicalCardView import PhysicalCardView
from .AutoScrolledWindow import AutoScrolledWindow
from .FilterModelPanes import add_accel_to_button


NO_CARD = "  No Card"

NO_EXP_AND_PRINT = "No Expansion and Printing"


def _sort_replacement(oModel, oIter1, oIter2, _oCol):
    """Sort replacement, honouring spaces"""
    oVal1 = oModel.get_value(oIter1, 2)
    oVal2 = oModel.get_value(oIter2, 2)
    if oVal1 < oVal2:
        return -1
    if oVal1 > oVal2:
        return 1
    return 0


class DummyController:
    """Dummy controller class, so we can use the card views directly"""
    def __init__(self, sFilterType):
        self.sFilterType = sFilterType

    filtertype = property(fget=lambda self: self.sFilterType)

    def set_card_text(self, _oCard):
        """Ignore card text updates."""
        pass


class ACLLookupView(PhysicalCardView):
    """Specialised version for the Card Lookup."""
    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so many public methods.

    def __init__(self, oDialogWindow, oConfig):
        oController = DummyController('PhysicalCard')
        super().__init__(oController, oDialogWindow, oConfig)
        self.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
        self._oModel.bExpansions = False

    def get_selected_card(self):
        """Return the selected card with a dummy expansion of ''."""
        sNewName = NO_CARD
        oModel, aSelection = self.get_selection().get_selected_rows()
        for oPath in aSelection:
            sNewName, _sExpansion, _iCount, _iDepth = \
                oModel.get_all_from_path(oPath)
            oAbsCard = oModel.get_abstract_card_from_path(oPath)
        return sNewName, '', oAbsCard

    def get_selected_abstract_card(self):
        """Return the actual abstract card selected."""
        oAbsCard = None
        oModel, aSelection = self.get_selection().get_selected_rows()
        for oPath in aSelection:
            oAbsCard = oModel.get_abstract_card_from_path(oPath)
        return oAbsCard

    def cleanup(self):
        """Call model cleanup to remove listeners, etc."""
        self._oModel.cleanup()


class PCLLookupView(PhysicalCardView):
    """Also show current allocation of cards in the physical card view."""
    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so many public methods.

    def __init__(self, oDialogWindow, oConfig):
        oController = DummyController('PhysicalCard')
        super().__init__(oController, oDialogWindow, oConfig)
        self.get_selection().set_mode(Gtk.SelectionMode.SINGLE)

    def get_selected_card(self):
        """Return the selected card and expansion."""
        sNewName = NO_CARD
        sExpansion = '  Unpecified Expansion'
        oModel, aSelection = self.get_selection().get_selected_rows()
        for oPath in aSelection:
            sNewName, sExpansion, _iCount, _iDepth = \
                oModel.get_all_from_path(oPath)
            oAbsCard = oModel.get_abstract_card_from_path(oPath)
        if sExpansion is None:
            sExpansion = ''
        return sNewName, sExpansion, oAbsCard

    def cleanup(self):
        """Call model cleanup to remove listeners, etc."""
        self._oModel.cleanup()


class ReplacementTreeView(Gtk.TreeView):
    """A TreeView which tracks the current set of replacement cards."""
    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so many public methods.

    def __init__(self, oCardListView, oFilterToggleButton):
        """Construct a Gtk.TreeView object showing the current
           card replacements.

           For abstract cards, the card names are stored as is.
           For physical cards, the card names have " [<expansion>]"
           appended.
           """
        # ListStore: count, missing card, replacement

        self._dToolTips = {}

        oModel = Gtk.ListStore(GObject.TYPE_INT, GObject.TYPE_STRING,
                               GObject.TYPE_STRING, GObject.TYPE_INT,
                               GObject.TYPE_PYOBJECT)

        super().__init__(oModel)
        self.oCardListView = oCardListView
        self.oModel = oModel
        self.oFilterToggleButton = oFilterToggleButton
        self.set_enable_search(False)  # Not much point searching this tree

        self._create_text_column('Missing Card', 1)
        self._create_text_column('Replace Card', 2)

        self._create_button_column("list-add", 'Set',
                                   'Use the selected card',
                                   self._set_to_selection)  # use selected card
        self._create_button_column("list-remove", 'Ignore',
                                   'Ignore the current card',
                                   self._set_ignore)  # ignore current card
        self._create_button_column("edit-find", 'Filter',
                                   'Filter on best guess',
                                   self._set_filter)  # filter out best guesses

        self.set_property('has-tooltip', True)
        self.connect('query-tooltip', self._show_tooltip)

        oModel.set_sort_func(2, _sort_replacement)
        oModel.set_sort_column_id(2, 0)

    # utility methods to simplify column creation
    def _create_button_column(self, sIconName, sLabel, sToolTip, fClicked):
        """Create a column with a button, usin oIcon and the function
           fClicked."""
        oCell = CellRendererSutekhButton(bShowIcon=True)
        oCell.load_icon(sIconName, self)
        oLabel = Gtk.Label(label=sLabel)
        oColumn = Gtk.TreeViewColumn("", oCell)
        oColumn.set_widget(oLabel)
        oColumn.set_fixed_width(22)
        oColumn.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        self.append_column(oColumn)
        oCell.connect('clicked', fClicked)
        self._dToolTips[oColumn] = sToolTip

    # pylint: disable=too-many-arguments
    # Need this many arguments from function signature
    # Show tooltips for the column buttons
    def _show_tooltip(self, _oWidget, _iXPos, _iYPos, _bKeyboard, oToolTip):
        """Test if a tooltip should be shown"""
        sToolTip = None
        # The positions passed in aren't relative to the right window for
        # get_path, so we query position directly
        _oMask, iXPos, iYPos, _oIgnore = self.get_bin_window().get_pointer()
        tRes = self.get_path_at_pos(iXPos, iYPos)
        if tRes:
            # path returned may be none
            sToolTip = self._dToolTips.get(tRes[1], None)
        if sToolTip:
            oToolTip.set_markup(sToolTip)
            return True
        return False

    # pylint: enable=too-many-arguments

    def _create_text_column(self, sLabel, iColumn):
        """Create a text column, using iColumn from the model"""
        oCell = Gtk.CellRendererText()
        oCell.set_property('style', Pango.Style.ITALIC)
        oColumn = Gtk.TreeViewColumn(sLabel, oCell, text=iColumn, weight=3)
        oColumn.set_expand(True)
        oColumn.set_sort_column_id(iColumn)
        self.append_column(oColumn)

    def _fix_selection(self, sName):
        """Fix the cursor position to accomodate the result of the rows
           being sorted"""
        oIter = self.oModel.get_iter_first()
        while oIter:
            sCurName = self.oModel.get_value(oIter, 1)
            if sName == sCurName:
                self.set_cursor(self.oModel.get_path(oIter))
                return
            oIter = self.oModel.iter_next(oIter)

    def _set_to_selection(self, _oCell, oPath):
        """Set the replacement card to the selected entry"""

        # We handle PhysicalCards on a like-for-like matching case.
        # For cases where the user selects an expansion with too few
        # cards, but where there are enough physical cards, we do the
        # best we can

        oIter = self.oModel.get_iter(oPath)
        sName = self.oModel.get_value(oIter, 1)

        sNewName, sExpansion, oAbsCard = self.oCardListView.get_selected_card()
        if sNewName == NO_CARD:
            do_complaint_error("Please select a card")
            return

        if sExpansion != '':
            sReplaceWith = sNewName + " [%s]" % (sExpansion,)
        else:
            sReplaceWith = sNewName

        self.oModel.set_value(oIter, 2, sReplaceWith)
        self.oModel.set_value(oIter, 3, Pango.Weight.NORMAL)
        self.oModel.set_value(oIter, 4, oAbsCard)
        GObject.timeout_add(1, self._fix_selection, sName)

    def _set_ignore(self, _oCell, oPath):
        """Mark the card as not having a replacement."""
        oIter = self.oModel.get_iter(oPath)
        sName = self.oModel.get_value(oIter, 1)
        self.oModel.set_value(oIter, 2, NO_CARD)
        self.oModel.set_value(oIter, 3, Pango.Weight.BOLD)
        GObject.timeout_add(1, self._fix_selection, sName)

    def _set_filter(self, _oCell, oPath):
        """Set the card list filter to the best guess filter for this card."""
        oIter = self.oModel.get_iter(oPath)
        sFullName = self.oModel.get_value(oIter, 1)
        sName, _sExp = self.parse_card_name(sFullName)

        oFilter = best_guess_filter(sName)
        self.oCardListView.get_model().selectfilter = oFilter

        if not self.oFilterToggleButton.get_active():
            self.oFilterToggleButton.set_active(True)
        else:
            self.oCardListView.load()

    def run_filter_dialog(self, _oButton):
        """Display the filter dialog and apply results."""
        self.oCardListView.get_filter(None, "CardName in $var0")
        self.oFilterToggleButton.set_active(
            self.oCardListView.get_model().applyfilter)

    def toggle_apply_filter(self, _oButton):
        """Toggle whether the filter is applied."""
        self.oCardListView.get_model().applyfilter = \
            self.oFilterToggleButton.get_active()
        self.oCardListView.load()

    def toggle_show_illegal(self, oButton):
        """Toggle whether the filter is applied."""
        self.oCardListView.get_model().hideillegal = not oButton.get_active()
        self.oCardListView.load()

    def show_search(self, _oButton):
        """Popup the search dialog"""
        self.oCardListView.emit('start-interactive-search')

    NAME_RE = re.compile(r"^(?P<name>.*?)( \[(?P<exp>[^]]+)\])?$")

    @classmethod
    def parse_card_name(cls, sName):
        """Parser the card name and expansion out of the string."""
        oMatch = cls.NAME_RE.match(sName)
        assert oMatch is not None
        return oMatch.group('name'), oMatch.group('exp')


class GuiLookup(AbstractCardLookup, PhysicalCardLookup, PrintingLookup):
    """Lookup AbstractCards. Use the user as the AI if a simple lookup fails.
       """

    def __init__(self, oConfig):
        super().__init__()
        self._oConfig = oConfig

    def lookup(self, aNames, sInfo):
        """Lookup missing abstract cards.

           Provides an implementation for AbstractCardLookup.
           """
        # pylint: disable=too-many-branches
        # Lots of different cases to consider, to several branches
        dCards = {}
        dUnknownCards = {}

        aNewNames = []  # If we need to recode the name

        for sName in aNames:
            if not sName:
                # None here is an explicit ignore from the lookup cache
                dCards[sName] = None
            else:
                # Check we can encode the name properly to avoid potential
                # errors later.
                try:
                    _sTemp = sName.encode('utf8')
                except UnicodeDecodeError:
                    # Wrong assumptions somewhere - let the user sort it
                    # out
                    # We bounce through unicode to ensure
                    # we have something usable everywhere
                    # FIXME: Fix best guess filter and card lookup
                    # code so we don't need to encode back to ascii
                    sName = sName.decode('ascii', 'replace').encode('ascii',
                                                                    'replace')
                try:
                    # Use IAbstractCard to cover more variations
                    oAbs = IAbstractCard(sName)
                    dCards[sName] = oAbs
                except SQLObjectNotFound:
                    dUnknownCards[sName] = None

            aNewNames.append(sName)

        if dUnknownCards:
            if not self._handle_unknown_abstract_cards(dUnknownCards, sInfo):
                raise LookupFailed("Lookup of missing cards aborted by the"
                                   " user.")

        def new_card(sName):
            """emulate python 2.5's a = x if C else y"""
            if sName in dCards:
                return dCards[sName]
            return dUnknownCards[sName]

        return [new_card(sName) for sName in aNewNames]

    def physical_lookup(self, dCardExpansions, dNameCards, dNamePrintings,
                        sInfo):
        """Lookup missing physical cards.

           Provides an implementation for PhysicalCardLookup.
           """
        aCards = []
        dUnknownCards = {}

        for sName in dCardExpansions:
            oAbs = dNameCards[sName]
            if oAbs is None:
                continue
            for tExpPrint in dCardExpansions[sName]:
                iCnt = dCardExpansions[sName][tExpPrint]
                oPrinting = dNamePrintings[tExpPrint]
                if iCnt > 0:
                    try:
                        aCards.extend(
                            [IPhysicalCard((oAbs, oPrinting))] * iCnt)
                    except SQLObjectNotFound:
                        dUnknownCards[(oAbs.name, tExpPrint)] = iCnt

        if dUnknownCards:
            # We need to lookup cards in the physical card view
            if not self._handle_unknown_physical_cards(dUnknownCards,
                                                       aCards, sInfo):
                raise LookupFailed("Lookup of missing cards aborted by the"
                                   " user.")

        return aCards

    def printing_lookup(self, aExpPrintNames, sInfo, dCardExpansions):
        """Lookup for printing names, excluding unkown expansions or
           printings."""
        dPrintings = {}
        dUnknownPrintings = {}
        for sExp, sPrintName in aExpPrintNames:
            oTrueExp = None
            if sExp:
                try:
                    oTrueExp = IExpansion(sExp)
                except SQLObjectNotFound:
                    # Unknown expansion, so we don't even try the printing
                    dUnknownPrintings[(sExp, sPrintName)] = None
                    continue
            else:
                continue
            try:
                oPrinting = IPrinting((oTrueExp, sPrintName))
                dPrintings[(sExp, sPrintName)] = oPrinting
            except SQLObjectNotFound:
                # Expansion known, but printing isn't
                dUnknownPrintings[(sExp, sPrintName)] = None

        if dUnknownPrintings:
            if not self._handle_unknown_printings(dUnknownPrintings, sInfo,
                                                  dCardExpansions):
                raise LookupFailed("Lookup of missing printings aborted by"
                                   " the user.")

        for tExpPrint, oNewPrint in dUnknownPrintings.items():
            if oNewPrint is None:
                continue
            dUnknownPrintings[tExpPrint] = oNewPrint

        for tExpPrint in aExpPrintNames:
            if tExpPrint not in dPrintings:
                dPrintings[tExpPrint] = dUnknownPrintings.get(tExpPrint, None)

        return dPrintings

    def _handle_unknown_physical_cards(self, dUnknownCards, aPhysCards, sInfo):
        """Handle unknwon physical cards

           We allow the user to select the correct replacements from the
           Physical Card List
           """
        # pylint: disable=too-many-locals
        # we use lots of variables for clarity

        oUnknownDialog, oHBox = self._create_dialog(
            sInfo, "The following card and expansion combinations could not "
            "be found:")

        oPhysCardView = PCLLookupView(oUnknownDialog, self._oConfig)
        oReplacementView = self._fill_dialog(oHBox, oPhysCardView)
        oModel = oReplacementView.get_model()

        # Populate the model with the card names and best guesses
        for (sName, tExpPrint), iCnt in dUnknownCards.items():
            sBestGuess = NO_CARD
            sExpName, sPrintName = tExpPrint
            if sPrintName:
                sFullName = "%s [%s (%s)]" % (sName, sExpName, sPrintName)
            else:
                sFullName = "%s [%s]" % (sName, sExpName)

            oIter = oModel.append(None)
            oModel.set(oIter, 0, iCnt, 1, sFullName, 2, sBestGuess,
                       3, Pango.Weight.BOLD, 4, None)

        oUnknownDialog.vbox.show_all()
        oPhysCardView.load()

        iResponse = oUnknownDialog.run()
        oUnknownDialog.destroy()

        oPhysCardView.cleanup()

        if iResponse == Gtk.ResponseType.OK:
            # For cards marked as replaced, add them to the list of
            # Physical Cards
            oIter = oModel.get_iter_first()
            while oIter is not None:
                sFullName, sNewFullName, oAbsCard = oModel.get(oIter, 1, 2, 4)
                sName, sExpPrintName = \
                    oReplacementView.parse_card_name(sFullName)

                sNewName, sNewExpPrintName = \
                    oReplacementView.parse_card_name(sNewFullName)

                if sNewName != NO_CARD:
                    tExpPrint = (sExpPrintName, None)
                    iCnt = dUnknownCards[(sName, tExpPrint)]

                    # Find First physical card that matches this name
                    # that's not in aPhysCards
                    oPhys = self._lookup_new_phys_card(oAbsCard,
                                                       sNewExpPrintName)
                    aPhysCards.extend([oPhys] * iCnt)

                oIter = oModel.iter_next(oIter)
            return True
        return False

    # pylint: disable=no-self-use
    # These are methods for convenience
    def _create_dialog(self, sInfo, sMsg):
        """Create the dialog to present to the user.

           This is common to the abstract + physical card cases"""
        oUnknownDialog = SutekhDialog(
            "Unknown cards found importing %s" % sInfo, None,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            ("_OK", Gtk.ResponseType.OK,
             "_Cancel", Gtk.ResponseType.CANCEL))

        sLabelText = ("While importing %s\n%s\n"
                      "Choose how to handle these cards?\n" % (sInfo, sMsg))

        oMesgLabel1 = Gtk.Label(label=sLabelText)
        oUnknownDialog.vbox.pack_start(oMesgLabel1, False, False, 0)

        oHBox = Gtk.HBox()
        oUnknownDialog.vbox.pack_start(oHBox, True, True, 0)

        oMesgLabel2 = Gtk.Label(label="OK creates the card set, Cancel "
                                "aborts the creation of the card set")
        oUnknownDialog.vbox.pack_start(oMesgLabel2, True, True, 0)

        return oUnknownDialog, oHBox

    def _fill_dialog(self, oHBox, oView):
        """Handle the view setup and default buttons for the lookup
           dialog."""
        oViewWin = AutoScrolledWindow(oView)
        oViewWin.set_size_request(200, 600)
        oHBox.pack_start(oViewWin, True, True, 0)

        oVBox = Gtk.VBox()
        oHBox.pack_start(oVBox, True, True, 0)

        # Add same shortcuts as the pane menus
        oAccelGroup = Gtk.AccelGroup()
        # oHBox is a child of a vbox which is a child of the dialog
        oHBox.get_parent().get_parent().add_accel_group(oAccelGroup)

        oFilterDialogButton = Gtk.Button('Specify Filter')
        oFilterApplyButton = Gtk.CheckButton("Apply Filter")
        oLegalButton = Gtk.CheckButton("Show illegal cards")
        oSearchButton = Gtk.Button("Search List")
        add_accel_to_button(oFilterDialogButton, "<Ctrl>s", oAccelGroup,
                            'Open the Filter Editing Dialog.\n'
                            'Shortcut :<b>Ctrl-S</b>')
        add_accel_to_button(oFilterApplyButton, "<Ctrl>t", oAccelGroup,
                            'Toggle the applied state of the filter.\n'
                            'Shortcut : <b>Ctrl-T</b>')
        add_accel_to_button(oLegalButton, "<Ctrl>l", oAccelGroup,
                            'Toggle the display of cards not legal for'
                            ' tournament play.\n'
                            'Shortcut : <b>Ctrl-L</b>')
        add_accel_to_button(oSearchButton, "<Ctrl>f", oAccelGroup,
                            'Open the search dailog for the cards.\n'
                            'Shortcut : <b>Ctrl-F</b>')

        oReplacementView = ReplacementTreeView(oView,
                                               oFilterApplyButton)

        oReplacementWin = AutoScrolledWindow(oReplacementView)
        oReplacementWin.set_size_request(600, 600)
        oVBox.pack_start(oReplacementWin, True, True, 0)

        oFilterButtons = Gtk.HBox(spacing=2)
        oVBox.pack_start(Gtk.HSeparator(), True, True, 0)
        oVBox.pack_start(oFilterButtons, True, True, 0)

        oFilterButtons.pack_start(oFilterDialogButton, True, True, 0)
        oFilterButtons.pack_start(oFilterApplyButton, True, True, 0)
        oFilterButtons.pack_start(oLegalButton, True, True, 0)
        oFilterButtons.pack_start(oSearchButton, True, True, 0)

        oFilterDialogButton.connect("clicked",
                                    oReplacementView.run_filter_dialog)
        oFilterApplyButton.connect("toggled",
                                   oReplacementView.toggle_apply_filter)
        oLegalButton.connect("toggled",
                             oReplacementView.toggle_show_illegal)
        oSearchButton.connect("clicked",
                              oReplacementView.show_search)

        return oReplacementView

    def _lookup_new_phys_card(self, oAbsCard, sNewExpName):
        """Lookup the physical card, given the correct name + expansion
           name."""
        if sNewExpName is not None:
            try:
                iPrintID = IPrinting(sNewExpName).id
            except SQLObjectNotFound:
                iPrintID = None
        else:
            iPrintID = None

        oPhys = PhysicalCard.selectBy(abstractCardID=oAbsCard.id,
                                      printingID=iPrintID).getOne()
        return oPhys

    # pylint: enable=no-self-use

    def _handle_unknown_abstract_cards(self, dUnknownCards, sInfo):
        """Handle the list of unknown abstract cards.

           We allow the user to select the correct replacements from the
           Abstract Card List.
           """
        # pylint: disable=too-many-locals
        # we use lots of variables for clarity
        oUnknownDialog, oHBox = self._create_dialog(
            sInfo, "The following card names could not be found")

        oAbsCardView = ACLLookupView(oUnknownDialog, self._oConfig)
        oReplacementView = self._fill_dialog(oHBox, oAbsCardView)
        oModel = oReplacementView.get_model()

        # Populate the model with the card names and best guesses
        for sName in dUnknownCards:
            oBestGuessFilter = best_guess_filter(sName)
            aCards = list(oBestGuessFilter.select(AbstractCard))
            if len(aCards) == 1:
                sBestGuess = aCards[0].name
                iWeight = Pango.Weight.NORMAL
                oCard = aCards[0]
            else:
                sBestGuess = NO_CARD
                iWeight = Pango.Weight.BOLD
                oCard = None

            oIter = oModel.append(None)
            # second 1 is the dummy card count
            oModel.set(oIter, 0, 1, 1, sName, 2, sBestGuess, 3, iWeight,
                       4, oCard)

        oUnknownDialog.vbox.show_all()
        oAbsCardView.load()

        iResponse = oUnknownDialog.run()
        oUnknownDialog.destroy()

        oAbsCardView.cleanup()

        if iResponse == Gtk.ResponseType.OK:
            # For cards marked as replaced, add them to the Holder
            oIter = oModel.get_iter_first()
            while oIter is not None:
                sName, oAbsCard = oModel.get(oIter, 1, 4)
                if oAbsCard is not None:
                    dUnknownCards[sName] = oAbsCard
                oIter = oModel.iter_next(oIter)
            return True
        return False

    def _handle_unknown_printings(self, dUnknownPrintings, sInfo,
                                  dCardExpansions):
        """Handle the list of unknown expansion + printings.

           We allow the user to select the correct replacements from the
           expansion / printing combinations listed in the database.
           """
        oUnknownDialog = SutekhDialog(
            "Unknown printings found importing %s" % sInfo, None,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            ("_OK", Gtk.ResponseType.OK,
             "_Cancel", Gtk.ResponseType.CANCEL))

        # Find all known expansion / printing combos and sort them
        # by name
        dKnownPrintings = dict(
            [(IPrintingName(x), x) for x in Printing.select()])
        dPrintingCards = {}
        for oCard in PhysicalCard.select():
            if oCard.printing:
                sKey = IPrintingName(oCard.printing)
                dPrintingCards.setdefault(sKey, [])
                dPrintingCards[sKey].append(oCard.abstractCard.name)

        oMesgLabel1 = Gtk.Label(
            label="While importing %s\n"
            "The following expansions and printings could not be found:\n"
            "Choose how to handle these printings?\n" % (sInfo))
        oMesgLabel2 = Gtk.Label(
            label="OK continues the card set creation process, "
            "Cancel aborts the creation of the card set")

        oUnknownDialog.vbox.pack_start(oMesgLabel1, False, False, 0)

        oButtonBox = Gtk.VBox()

        # Fill in the Printings and options
        dReplacement = {}
        aKnownPrintings = sorted(dKnownPrintings)
        # Insert 'No choice' at the front
        aKnownPrintings.insert(0, NO_EXP_AND_PRINT)
        for tExpPrint in dUnknownPrintings:
            # Find the corresponding cards
            aCards = []
            sPrintInfo = "%s (%s)" % tExpPrint
            for sCard in dCardExpansions:
                if tExpPrint in dCardExpansions[sCard]:
                    aCards.append('%s [%s]' % (sCard, sPrintInfo))
            oBox = Gtk.HBox()
            oLabel = Gtk.Label(label="%s is Unknown: " % sPrintInfo)
            oBox.pack_start(oLabel, True, True, 0)

            oPopup = Gtk.Button('Show cards')
            oPopup.connect('clicked', self._popup_list,
                           '\n'.join(sorted(aCards)), sPrintInfo)
            oBox.pack_start(oPopup, True, True, 0)

            oLabel2 = Gtk.Label(label="Replace with ")
            oBox.pack_start(oLabel2, True, True, 0)

            oSelector = Gtk.ComboBoxText()
            for sPrintName in aKnownPrintings:
                oSelector.append_text(sPrintName)

            dReplacement[tExpPrint] = oSelector

            oPopupExpList = Gtk.Button('Show cards')
            oPopupExpList.connect('clicked', self._popup_exp, oSelector,
                                  dPrintingCards)

            oBox.pack_start(dReplacement[tExpPrint], True, True, 0)
            oBox.pack_start(oPopupExpList, True, True, 0)
            oButtonBox.pack_start(oBox, True, True, 0)

        oUnknownDialog.vbox.pack_start(oButtonBox, True, True, 0)

        oUnknownDialog.vbox.pack_start(oMesgLabel2, True, True, 0)
        oUnknownDialog.vbox.show_all()

        iResponse = oUnknownDialog.run()

        oUnknownDialog.destroy()

        if iResponse == Gtk.ResponseType.OK:
            # For cards marked as replaced, add them to the Holder
            for tUnknownExpPrint in dUnknownPrintings:
                iPos = dReplacement[tUnknownExpPrint].get_active()
                if iPos < 0 or iPos >= len(aKnownPrintings):
                    sNewPrint = NO_EXP_AND_PRINT
                else:
                    sNewPrint = aKnownPrintings[iPos]
                if sNewPrint != NO_EXP_AND_PRINT:
                    dUnknownPrintings[tUnknownExpPrint] = \
                        dKnownPrintings[sNewPrint]
            return True
        return False

    @staticmethod
    def _popup_list(_oButton, sCardText, sPrint):
        """Popup the list of cards from the unknown expansion"""
        oCardDialog = SutekhDialog(
            "Cards with unknown expansion and print: %s" % sPrint, None,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            ("_Close", Gtk.ResponseType.CLOSE))
        oLabel = Gtk.Label(label=sCardText)
        oCardDialog.vbox.pack_start(AutoScrolledWindow(oLabel), True, True, 0)
        oCardDialog.set_size_request(300, 400)
        oCardDialog.show_all()
        oCardDialog.run()
        oCardDialog.destroy()

    @staticmethod
    def _popup_exp(_oButton, oSelector, dPrintingCards):
        """Popup the list of cards from the selected replacement expansion"""
        sNewName = oSelector.get_active_text()
        if sNewName == NO_EXP_AND_PRINT or sNewName is None:
            # No cards to show, so do nothing
            sTitle = "No Expansion Selected"
            oLabel = Gtk.Label(label='No Expansion selected')
        else:
            sTitle = "Cards with expansion %s" % sNewName
            # Show all cards with the given printing
            aCards = dPrintingCards[sNewName]
            oLabel = Gtk.Label(label='\n'.join(sorted(aCards)))
        oCardDialog = SutekhDialog(
            sTitle, None,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            ("_Close", Gtk.ResponseType.CLOSE))
        oCardDialog.vbox.pack_start(AutoScrolledWindow(oLabel), True, True, 0)
        oCardDialog.set_size_request(300, 400)
        oCardDialog.show_all()
        oCardDialog.run()
        oCardDialog.destroy()
