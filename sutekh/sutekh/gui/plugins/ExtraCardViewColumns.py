# ExtraCardViewColumns.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details
"""Disply extra columns in the tree view"""

import gtk
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import SutekhDialog
from sutekh.gui.CellRendererIcons import CellRendererIcons, SHOW_TEXT_ONLY, \
        SHOW_ICONS_ONLY, SHOW_ICONS_AND_TEXT
from sutekh.core.SutekhObjects import AbstractCard, PhysicalCard, \
           PhysicalCardSet
from sqlobject import SQLObjectNotFound

class ExtraCardViewColumns(CardListPlugin):
    """Add extra columns to the card list view.

       Allow the card list to be sorted on these columns
       """
    dTableVersions = {}
    aModelsSupported = [PhysicalCardSet, PhysicalCard]

    _dWidths = {
            'Card Type' : 100,
            'Clans and Creeds' : 100,
            'Disciplines and Virtues' : 150,
            'Expansions' : 600,
            'Group' : 40,
            'Capacity or Life(Imbued)' : 40,
            'Cost' : 100,
            }

    _dModes = {
            'Show Icons and Names' : SHOW_ICONS_AND_TEXT,
            'Show Icons only' : SHOW_ICONS_ONLY,
            'Show Text only' : SHOW_TEXT_ONLY,
            }

    # pylint: disable-msg=W0142
    # **magic OK here
    def __init__(self, *aArgs, **kwargs):
        super(ExtraCardViewColumns, self).__init__(*aArgs, **kwargs)
        self._dCols = {}
        self._dCols['Card Type'] = self._render_card_type
        self._dCols['Clans and Creeds'] = self._render_clan
        self._dCols['Disciplines and Virtues'] = self._render_disciplines
        self._dCols['Expansions'] = self._render_expansions
        self._dCols['Group'] = self._render_group
        self._dCols['Title'] = self._render_title
        self._dCols['Sect'] = self._render_sect
        self._dCols['Card Text'] = self._render_card_text
        self._dCols['Capacity or Life(Imbued)'] = self._render_capacity
        self._dCols['Cost'] = self._render_cost

        self._dSortDataFuncs = {}
        self._dSortDataFuncs['Card Type'] = self._get_data_cardtype
        self._dSortDataFuncs['Clans and Creeds'] = self._get_data_clan
        self._dSortDataFuncs['Disciplines and Virtues'] = \
                self._get_data_disciplines
        self._dSortDataFuncs['Expansions'] = self._get_data_expansions
        self._dSortDataFuncs['Group'] = self._get_data_group
        self._dSortDataFuncs['Title'] = self._get_data_title
        self._dSortDataFuncs['Sect'] = self._get_data_sect
        self._dSortDataFuncs['Card Text'] = self._get_data_card_text
        self._dSortDataFuncs['Capacity or Life(Imbued)'] = \
                self._get_data_capacity
        self._dSortDataFuncs['Cost'] = self._get_data_cost_sortkey

        self._dCardCache = {} # Used for sorting
        self._iShowMode = SHOW_ICONS_AND_TEXT
        self._oFirstBut = None
    # pylint: enable-msg=W0142

    # Rendering Functions

    def _get_card(self, oIter):
        """For the given iterator, get the associated abstract card"""
        if self.model.iter_depth(oIter) == 1:
            # Only try and lookup things that look like they should be cards
            try:
                sCardName = self.model.get_name_from_iter(oIter).lower()
                # Cache lookups, so we don't hit the database so hard when
                # sorting
                if not self._dCardCache.has_key(sCardName):
                    # pylint: disable-msg=E1101
                    # pylint + AbstractCard method wierdness
                    self._dCardCache[sCardName] = \
                            AbstractCard.byCanonicalName(sCardName)
                return self._dCardCache[sCardName]
            except SQLObjectNotFound:
                return None
        else:
            return None

    # pylint: disable-msg=R0201, W0613
    # Making these functions for clarity
    # several unused paramaters due to function signatures
    # The bGetIcons parameter is needed to avoid icon lookups, etc when
    # sorting
    def _get_data_cardtype(self, oCard, bGetIcons=True):
        """Return the card type"""
        if not oCard is None:
            aTypes = [x.name for x in oCard.cardtype]
            aTypes.sort()
            aIcons = []
            if bGetIcons:
                dIcons = self.icon_manager.get_icon_list(oCard.cardtype)
                if dIcons:
                    aIcons = [dIcons[x] for x in aTypes]
            return " /|".join(aTypes).split("|"), aIcons
        return [], []

    def _render_card_type(self, oColumn, oCell, oModel, oIter):
        """display the card type(s)"""
        oCard = self._get_card(oIter)
        aText, aIcons = self._get_data_cardtype(oCard, True)
        oCell.set_data(aText, aIcons, self._iShowMode)

    def _get_data_clan(self, oCard, bGetIcons=True):
        """get the clan for the card"""
        if not oCard is None:
            aClans = [x.name for x in oCard.clan]
            aIcons = []
            if aClans:
                aClans.sort()
                if bGetIcons:
                    dIcons = self.icon_manager.get_icon_list(oCard.clan)
                    if dIcons:
                        aIcons = [dIcons[x] for x in aClans]
                return " /|".join(aClans).split("|"), aIcons
            else:
                aCreed = [x.name for x in oCard.creed]
                aCreed.sort()
                if bGetIcons:
                    dIcons = self.icon_manager.get_icon_list(oCard.creed)
                    if dIcons:
                        aIcons = [dIcons[x] for x in aCreed]
                return " /|".join(aCreed).split("|"), aIcons
        return [], []

    def _render_clan(self, oColumn, oCell, oModel, oIter):
        """display the clan"""
        oCard = self._get_card(oIter)
        aText, aIcons = self._get_data_clan(oCard)
        oCell.set_data(aText, aIcons, self._iShowMode)

    def _get_data_disciplines(self, oCard, bGetIcons=True):
        """get disipline info for card"""
        if not oCard is None:
            # There are better ways of doing this, but this is 1st draft
            # attempt, so we'll do the firt that occurs to me
            aInfo = [((oP.level != 'superior') and oP.discipline.name or
                oP.discipline.name.upper(), oP.discipline.name) for
                oP in oCard.discipline]
            if aInfo:
                aInfo.sort(key=lambda x: x[0])
                if bGetIcons:
                    dIcons = self.icon_manager.get_icon_list(oCard.discipline)
                    aIcons = [dIcons[x[1]] for x in aInfo]
                else:
                    aIcons = []
                aDis = ", ".join([x[0] for x in aInfo]).split(" ")
                return aDis, aIcons
            else:
                aInfo = [oV.name for oV in oCard.virtue]
                if aInfo:
                    aInfo.sort()
                    if bGetIcons:
                        dIcons = self.icon_manager.get_icon_list(oCard.virtue)
                        aIcons = [dIcons[x] for x in aInfo]
                    else:
                        aIcons = []
                    aVirt = ", ".join(aInfo).split(" ")
                    return aVirt, aIcons
        return [], []

    def _render_disciplines(self, oColumn, oCell, oModel, oIter):
        """display the card disciplines"""
        oCard = self._get_card(oIter)
        aText, aIcons = self._get_data_disciplines(oCard)
        oCell.set_data(aText, aIcons, self._iShowMode)

    def _get_data_expansions(self, oCard, bGetIcons=True):
        """get expansion info"""
        if not oCard is None:
            aExp = [oP.expansion.shortname + "(" + oP.rarity.name + ")" for
                    oP in oCard.rarity]
            aExp.sort()
            aIcons = []
            if bGetIcons:
                aIcons = [None]*len(aExp)
            return aExp, aIcons
        return [], []

    def _render_expansions(self, oColumn, oCell, oModel, oIter):
        """Display expanson info"""
        oCard = self._get_card(oIter)
        aText, aIcons = self._get_data_expansions(oCard)
        oCell.set_data(aText, aIcons, self._iShowMode)

    def _get_data_group(self, oCard, bGetIcons=True):
        """get the group info for the card"""
        if not oCard is None and not oCard.group is None:
            return oCard.group, [None]
        # We use -1 for the any group, so flag with a very different number
        return -100, [None]

    def _render_group(self, oColumn, oCell, oModel, oIter):
        """Display the group info"""
        oCard = self._get_card(oIter)
        iGrp, aIcons = self._get_data_group(oCard)
        if iGrp != -100:
            if iGrp == -1:
                oCell.set_data(['Any'], aIcons, SHOW_TEXT_ONLY)
            else:
                oCell.set_data([str(iGrp)], aIcons, SHOW_TEXT_ONLY)
        else:
            oCell.set_data([""], aIcons, SHOW_TEXT_ONLY)

    def _get_data_capacity(self, oCard, bGetIcons=True):
        """Get the card's capacity"""
        if not oCard is None and not oCard.capacity is None:
            return oCard.capacity, [None]
        if not oCard is None and not oCard.life is None:
            return oCard.life, [None]
        return -1, [None]

    def _render_capacity(self, oColumn, oCell, oModel, oIter):
        """Display capacity in the column"""
        oCard = self._get_card(oIter)
        iCap, aIcons = self._get_data_capacity(oCard)
        if iCap != -1:
            oCell.set_data([str(iCap)], aIcons, SHOW_TEXT_ONLY)
        else:
            oCell.set_data([""], aIcons, SHOW_TEXT_ONLY)

    def _get_data_cost(self, oCard, bGetIcons=True):
        """Get the card's cost"""
        if not oCard is None and not oCard.cost is None:
            return oCard.cost, oCard.costtype, [None]
        return 0, "", [None]

    def _get_data_cost_sortkey(self, oCard, bGetIcons=True):
        """Get the sort key for sorting by cost.

           We want to group the cost types together, since the different
           types aren't comparable, hence the key is constructed as
           costtype + cost.
           We ensure that cost X cards sort after other values.
           """
        iCost, sCostType, aIcons = self._get_data_cost(oCard, bGetIcons)
        if iCost > 0:
            sKey = "%s %d" % (sCostType, iCost)
        elif iCost == -1:
            sKey = "%s X" % sCostType
        else:
            sKey = ""
        return sKey, aIcons

    def _render_cost(self, oColumn, oCell, oModel, oIter):
        """Display cost in the column"""
        oCard = self._get_card(oIter)
        iCost, sCostType, aIcons = self._get_data_cost(oCard)
        if iCost > 0:
            oCell.set_data(["%d %s" % (iCost, sCostType)], aIcons,
                SHOW_TEXT_ONLY)
        elif iCost == -1:
            oCell.set_data(["X %s" % sCostType], aIcons,
                SHOW_TEXT_ONLY)
        else:
            oCell.set_data([""], aIcons, SHOW_TEXT_ONLY)


    def _get_data_title(self, oCard, bGetIcons=True):
        """Get the card's title."""
        if not oCard is None:
            aTitles = [oT.name for oT in oCard.title]
            aTitles.sort()
            aIcons = []
            if bGetIcons:
                aIcons = [None]*len(aTitles)
            return aTitles, aIcons
        return [], []

    def _render_title(self, oColumn, oCell, oModel, oIter):
        """Display title in the column"""
        oCard = self._get_card(oIter)
        aTitles, aIcons = self._get_data_title(oCard)
        oCell.set_data(aTitles, aIcons, SHOW_TEXT_ONLY)

    def _get_data_sect(self, oCard, bGetIcons=True):
        """Get the card's sect."""
        if not oCard is None:
            aSects = [oS.name for oS in oCard.sect]
            aSects.sort()
            aIcons = []
            if bGetIcons:
                aIcons = [None]*len(aSects)
            return aSects, aIcons
        return [], []

    def _render_sect(self, oColumn, oCell, oModel, oIter):
        """Display sect in the column"""
        oCard = self._get_card(oIter)
        aSects, aIcons = self._get_data_sect(oCard)
        oCell.set_data(aSects, aIcons, SHOW_TEXT_ONLY)

    def _get_data_card_text(self, oCard, bGetIcons=True):
        """Get the card's card text."""
        if not oCard is None:
            aTexts = [oCard.text.replace("\n", " ")]
            aIcons = []
            if bGetIcons:
                aIcons = [None]*len(aTexts)
            return aTexts, aIcons
        return [], []

    def _render_card_text(self, oColumn, oCell, oModel, oIter):
        """Display card text in the column"""
        oCard = self._get_card(oIter)
        aTexts, aIcons = self._get_data_card_text(oCard)
        oCell.set_data(aTexts, aIcons, SHOW_TEXT_ONLY)

    # pylint: enable-msg=R0201
    # Dialog and Menu Item Creation

    def get_menu_item(self):
        """Register on 'Plugins' menu"""
        if not self.check_versions() or not self.check_model_type():
            return None
        oSelector = gtk.MenuItem("Select Extra Columns")
        oSelector.connect("activate", self.activate)
        return ('Plugins', oSelector)

    # W0613 - oWidget required by function signature
    def activate(self, oWidget):
        """Handle menu activation"""
        oDlg = self.make_dialog()
        oDlg.run()

    # W0613: oModel required by gtk's function signature
    def sort_column(self, oModel, oIter1, oIter2, oGetData):
        """Stringwise comparision of oIter1 and oIter2.

           Return -1 if oIter1 < oIter, 0 in ==, 1 if >
           """
        oCard1 = self._get_card(oIter1)
        oCard2 = self._get_card(oIter2)
        if oCard1 is None or oCard2 is None:
            # Not comparing cards, sort on name only
            sName1 = self.model.get_name_from_iter(oIter1).lower()
            sName2 = self.model.get_name_from_iter(oIter2).lower()
            if sName1 < sName2:
                iRes = -1
            elif sName1 > sName2:
                iRes = 1
            else:
                iRes = 0
            return iRes
        # Don't use icon info when sorting
        oVal1 = oGetData(oCard1, False)[0]
        oVal2 = oGetData(oCard2, False)[0]
        # convert to string for sorting
        if isinstance(oVal1, list):
            oVal1 = " ".join(oVal1)
            oVal2 = " ".join(oVal2)
        if oVal1 < oVal2:
            iRes = -1
        elif oVal1 > oVal2:
            iRes = 1
        else:
            # Values agrees, so sort on card name
            iRes = cmp(oCard1.name, oCard2.name)
        return iRes

    # pylint: enable-msg=W0613

    def make_dialog(self):
        """Create the column selection dialog"""
        sName = "Select Extra Columns ..."

        oDlg = SutekhDialog(sName, self.parent,
                gtk.DIALOG_DESTROY_WITH_PARENT)
        oDlg.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        oDlg.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)

        oDlg.connect("response", self.handle_response)

        # pylint: disable-msg=W0201
        # no point in defining this in __init__
        self._aButtons = []
        aColsInUse = self.get_cols_in_use()
        # pylint: disable-msg=E1101
        # pylint doesn't detect vbox's methods
        for sName in self._dCols:
            oBut = gtk.CheckButton(sName)
            oBut.set_active(sName in aColsInUse)
            oDlg.vbox.pack_start(oBut)
            self._aButtons.append(oBut)

        oDlg.vbox.pack_start(gtk.HSeparator())

        oIter = self._dModes.iterkeys()
        for sName in oIter:
            self._oFirstBut = gtk.RadioButton(None, sName, False)
            if self._iShowMode == self._dModes[sName]:
                self._oFirstBut.set_active(True)
            oDlg.vbox.pack_start(self._oFirstBut, expand=False)
            break
        for sName in oIter:
            oBut = gtk.RadioButton(self._oFirstBut, sName)
            oDlg.vbox.pack_start(oBut, expand=False)
            if self._iShowMode == self._dModes[sName]:
                oBut.set_active(True)

        oDlg.show_all()

        return oDlg

    # Actions

    def handle_response(self, oDlg, oResponse):
        """Handle user response from the dialog"""
        if oResponse == gtk.RESPONSE_CANCEL:
            oDlg.destroy()
        elif oResponse == gtk.RESPONSE_OK:
            aColsInUse = []
            for oBut in self._aButtons:
                if oBut.get_active():
                    sLabel = oBut.get_label()
                    aColsInUse.append(sLabel)
            for oBut in self._oFirstBut.get_group():
                sName = oBut.get_label()
                if oBut.get_active():
                    self._iShowMode = self._dModes[sName]

            self.set_cols_in_use(aColsInUse)
            oDlg.destroy()

    def set_cols_in_use(self, aCols):
        """Add columns to the view"""
        # pylint: disable-msg=W0612
        # iDir is returned, although we don't need it
        iSortCol, iDir = self.model.get_sort_column_id()
        # pylint: enable-msg=W0612
        if iSortCol is not None and iSortCol > 1:
            # We're changing the columns, so restore sorting to default
            self.model.set_sort_column_id(0, 0)

        for oCol in self._get_col_objects():
            self.view.remove_column(oCol)

        for iNum, sCol in enumerate(aCols):
            oCell = CellRendererIcons()
            oColumn = gtk.TreeViewColumn(sCol, oCell)
            oColumn.set_cell_data_func(oCell, self._dCols[sCol])
            oColumn.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            oColumn.set_fixed_width(self._dWidths.get(sCol, 100))
            oColumn.set_resizable(True)
            self.view.insert_column(oColumn, iNum + 3)
            oColumn.set_sort_column_id(iNum + 3)
            self.model.set_sort_func(iNum + 3, self.sort_column,
                    self._dSortDataFuncs[sCol])

    def get_cols_in_use(self):
        """Get which extra columns have been added to view"""
        return [oCol.get_property("title") for oCol in self._get_col_objects()]

    def _get_col_objects(self):
        """Get the actual TreeColumn in the view"""
        return [oCol for oCol in self.view.get_columns() if
                oCol.get_property("title") in self._dCols]

# pylint: disable-msg=C0103
# accept plugin name
plugin = ExtraCardViewColumns
