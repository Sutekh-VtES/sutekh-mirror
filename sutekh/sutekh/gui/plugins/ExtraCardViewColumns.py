# ExtraCardViewColumns.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details
"""Display extra columns in the tree view"""

import gtk
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.gui.CellRendererIcons import CellRendererIcons, SHOW_TEXT_ONLY, \
        SHOW_ICONS_ONLY, SHOW_ICONS_AND_TEXT
from sutekh.core.SutekhObjects import PhysicalCard, PhysicalCardSet
from sqlobject import SQLObjectNotFound


SORT_COLUMN_OFFSET = 100  # ensure we don't clash with other extra columns


class ExtraCardViewColumns(SutekhPlugin):
    """Add extra columns to the card list view.

       Allow the card list to be sorted on these columns
       """

    COLUMNS = {
        'Card Type': None,
        'Clans and Creeds': None,
        'Disciplines and Virtues': None,
        'Expansions': None,
        'Group': None,
        'Title': None,
        'Sect': None,
        'Card Text': None,
        'Capacity or Life': None,
        'Cost': None,
    }

    DEFAULT_MODE = 'Show Icons and Names'

    MODES = {
            DEFAULT_MODE: SHOW_ICONS_AND_TEXT,
            'Show Icons only': SHOW_ICONS_ONLY,
            'Show Text only': SHOW_TEXT_ONLY,
            }

    OPTION_STR = ", ".join('"%s"' % sKey for sKey in sorted(COLUMNS.keys()))
    EXTRA_COLUMNS = "extra columns"
    ICON_MODE = "column mode"
    ICON_OPT_STR = ", ".join('"%s"' % sKey for sKey in sorted(MODES.keys()))

    dTableVersions = {}
    aModelsSupported = (PhysicalCardSet, PhysicalCard)
    dPerPaneConfig = {
        EXTRA_COLUMNS: 'option_list(%s, default=list())' % OPTION_STR,
        ICON_MODE: 'option(%s, default="%s")' % (ICON_OPT_STR, DEFAULT_MODE),
    }

    dCardListConfig = dPerPaneConfig

    _dWidths = {
            'Card Type': 100,
            'Clans and Creeds': 100,
            'Disciplines and Virtues': 150,
            'Expansions': 600,
            'Group': 40,
            'Capacity or Life': 40,
            'Cost': 100,
            }

    # pylint: disable-msg=W0142
    # **magic OK here
    def __init__(self, *args, **kwargs):
        super(ExtraCardViewColumns, self).__init__(*args, **kwargs)
        self._dCols = {}
        self._dCols['Card Type'] = self._render_card_type
        self._dCols['Clans and Creeds'] = self._render_clan
        self._dCols['Disciplines and Virtues'] = self._render_disciplines
        self._dCols['Expansions'] = self._render_expansions
        self._dCols['Group'] = self._render_group
        self._dCols['Title'] = self._render_title
        self._dCols['Sect'] = self._render_sect
        self._dCols['Card Text'] = self._render_card_text
        self._dCols['Capacity or Life'] = self._render_capacity
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
        self._dSortDataFuncs['Capacity or Life'] = \
                self._get_data_capacity
        self._dSortDataFuncs['Cost'] = self._get_data_cost_sortkey

        self._iShowMode = SHOW_ICONS_AND_TEXT
        self._oFirstBut = None
        self.perpane_config_updated()
    # pylint: enable-msg=W0142

    # Rendering Functions

    def _get_card(self, oIter):
        """For the given iterator, get the associated abstract card"""
        if self.model.iter_depth(oIter) == 1:
            # Only try and lookup things that look like they should be cards
            try:
                oAbsCard = self.model.get_abstract_card_from_iter(oIter)
                return oAbsCard
            except SQLObjectNotFound:
                return None
        else:
            return None

    # pylint: disable-msg=R0201
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

    def _render_card_type(self, _oColumn, oCell, _oModel, oIter):
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

    def _render_clan(self, _oColumn, oCell, _oModel, oIter):
        """display the clan"""
        oCard = self._get_card(oIter)
        aText, aIcons = self._get_data_clan(oCard)
        oCell.set_data(aText, aIcons, self._iShowMode)

    def _get_data_disciplines(self, oCard, bGetIcons=True):
        """get discipline info for card"""
        if not oCard is None:
            # There are better ways of doing this, but this is 1st draft
            # attempt, so we'll do the firt that occurs to me
            aInfo = [((oP.level != 'superior') and oP.discipline.name or
                oP.discipline.name.upper(), oP.discipline.name) for
                oP in oCard.discipline]
            if aInfo:
                # We sort inf before SUP, so swapcase
                aInfo.sort(key=lambda x: x[0].swapcase())
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

    def _render_disciplines(self, _oColumn, oCell, _oModel, oIter):
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
                aIcons = [None] * len(aExp)
            return aExp, aIcons
        return [], []

    def _render_expansions(self, _oColumn, oCell, _oModel, oIter):
        """Display expansion info"""
        oCard = self._get_card(oIter)
        aText, aIcons = self._get_data_expansions(oCard)
        oCell.set_data(aText, aIcons, self._iShowMode)

    def _get_data_group(self, oCard, _bGetIcons=True):
        """get the group info for the card"""
        if not oCard is None and not oCard.group is None:
            return oCard.group, [None]
        # We use -1 for the any group, so flag with a very different number
        return -100, [None]

    def _render_group(self, _oColumn, oCell, _oModel, oIter):
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

    def _get_data_capacity(self, oCard, _bGetIcons=True):
        """Get the card's capacity"""
        if not oCard is None and not oCard.capacity is None:
            return oCard.capacity, [None]
        if not oCard is None and not oCard.life is None:
            return oCard.life, [None]
        return -1, [None]

    def _render_capacity(self, _oColumn, oCell, _oModel, oIter):
        """Display capacity in the column"""
        oCard = self._get_card(oIter)
        iCap, aIcons = self._get_data_capacity(oCard)
        if iCap != -1:
            oCell.set_data([str(iCap)], aIcons, SHOW_TEXT_ONLY)
        else:
            oCell.set_data([""], aIcons, SHOW_TEXT_ONLY)

    def _get_data_cost(self, oCard, _bGetIcons=True):
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

    def _render_cost(self, _oColumn, oCell, _oModel, oIter):
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
                aIcons = [None] * len(aTitles)
            return aTitles, aIcons
        return [], []

    def _render_title(self, _oColumn, oCell, _oModel, oIter):
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
                aIcons = [None] * len(aSects)
            return aSects, aIcons
        return [], []

    def _render_sect(self, _oColumn, oCell, _oModel, oIter):
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
                aIcons = [None] * len(aTexts)
            return aTexts, aIcons
        return [], []

    def _render_card_text(self, _oColumn, oCell, _oModel, oIter):
        """Display card text in the column"""
        oCard = self._get_card(oIter)
        aTexts, aIcons = self._get_data_card_text(oCard)
        oCell.set_data(aTexts, aIcons, SHOW_TEXT_ONLY)

    # pylint: enable-msg=R0201

    def sort_column(self, _oModel, oIter1, oIter2, oGetData):
        """Stringwise comparision of oIter1 and oIter2.

           Return -1 if oIter1 < oIter, 0 in ==, 1 if >
           """
        oCard1 = self._get_card(oIter1)
        oCard2 = self._get_card(oIter2)
        if oCard1 is None or oCard2 is None:
            # Not comparing cards, fall-back to default
            return self.model.sort_equal_iters(oIter1, oIter2)
        # Don't use icon info when sorting
        oVal1 = oGetData(oCard1, False)[0]
        oVal2 = oGetData(oCard2, False)[0]
        # convert to string for sorting
        if isinstance(oVal1, list):
            oVal1 = " ".join(oVal1)
            oVal2 = " ".join(oVal2)
        iRes = cmp(oVal1, oVal2)
        if iRes == 0:
            # Values agree, so do fall back sort
            iRes = self.model.sort_equal_iters(oIter1, oIter2)
        return iRes

    # Actions

    def set_cols_in_use(self, aCols):
        """Add columns to the view"""
        iSortCol, _iDir = self.model.get_sort_column_id()
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
            oColumn.set_sort_column_id(iNum + 3 + SORT_COLUMN_OFFSET)
            self.model.set_sort_func(iNum + 3 + SORT_COLUMN_OFFSET,
                    self.sort_column, self._dSortDataFuncs[sCol])

    def get_cols_in_use(self):
        """Get which extra columns have been added to view"""
        return [oCol.get_property("title") for oCol in self._get_col_objects()]

    def _get_col_objects(self):
        """Get the actual TreeColumn in the view"""
        return [oCol for oCol in self.view.get_columns() if
                oCol.get_property("title") in self._dCols]

    # Config Update

    def perpane_config_updated(self, _bDoReload=True):
        """Called by base class on config updates."""
        aCols = None
        if self.check_versions() and self.check_model_type():
            aCols = self.get_perpane_item(self.EXTRA_COLUMNS)
            sShowMode = self.get_perpane_item(self.ICON_MODE)
            self._iShowMode = self.MODES.get(sShowMode, self.DEFAULT_MODE)
        if aCols is not None:
            # Need to accept empty lists so we remove columns
            self.set_cols_in_use(aCols)


plugin = ExtraCardViewColumns
