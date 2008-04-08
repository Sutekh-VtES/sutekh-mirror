# ExtraCardViewColumns.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details
"Disply extra columns in the tree view"

import gtk, pango
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import SutekhDialog
from sutekh.core.SutekhObjects import AbstractCard, PhysicalCard, \
           AbstractCardSet, PhysicalCardSet
from sqlobject import SQLObjectNotFound

class ExtraCardViewColumns(CardListPlugin):
    """
    Add extra columns to the card list view.
    Allow the card list to be sorted on these columns
    """
    dTableVersions = {}
    aModelsSupported = [AbstractCard, PhysicalCard, AbstractCardSet,
            PhysicalCardSet]

    # pylint: disable-msg=W0142
    # **magic OK here
    def __init__(self, *aArgs, **kwargs):
        super(ExtraCardViewColumns, self).__init__(*aArgs, **kwargs)
        self._dCols = {}
        self._dCols['Card Type'] = self._render_card_type
        self._dCols['Clan'] = self._render_clan
        self._dCols['Disciplines'] = self._render_disciplines
        self._dCols['Expansions'] = self._render_expansions
        self._dCols['Group'] = self._render_group
        self._dCols['Capacity'] = self._render_capacity

        self._dSortDataFuncs = {}
        self._dSortDataFuncs['Card Type'] = self._get_data_cardtype
        self._dSortDataFuncs['Clan'] = self._get_data_clan
        self._dSortDataFuncs['Disciplines'] = self._get_data_disciplines
        self._dSortDataFuncs['Expansions'] = self._get_data_expansions
        self._dSortDataFuncs['Group'] = self._get_data_group
        self._dSortDataFuncs['Capacity'] = self._get_data_capacity

        self._dCardCache = {} # Used for sorting
    # pylint: enable-msg=W0142

    # Rendering Functions

    def _get_card(self, oIter):
        "For the given iterator, get the associated abstract card"
        if self.model.iter_depth(oIter) == 1:
            # Only try and lookup things that look like they should be cards
            try:
                sCardName = self.model.getNameFromIter(oIter).lower()
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
    def _get_data_cardtype(self, oCard):
        "Return the card type"
        if not oCard is None:
            aTypes = [x.name for x in oCard.cardtype]
            aTypes.sort()
            return ",".join(aTypes)
        return ""

    def _render_card_type(self, oColumn, oCell, oModel, oIter):
        "display the card type(s)"
        oCard = self._get_card(oIter)
        oCell.set_property("text", self._get_data_cardtype(oCard))

    def _get_data_clan(self, oCard):
        "get the clan for the card"
        if not oCard is None:
            aClans = [x.name for x in oCard.clan]
            aClans.sort()
            return ",".join(aClans)
        return ""

    def _render_clan(self, oColumn, oCell, oModel, oIter):
        "display the clan"
        oCard = self._get_card(oIter)
        oCell.set_property("text", self._get_data_clan(oCard))

    def _get_data_disciplines(self, oCard):
        "get disipline info for card"
        if not oCard is None:
            aDis = [(oP.level != 'superior') and oP.discipline.name 
                    or oP.discipline.name.upper() for oP in oCard.discipline]
            aDis.sort()
            return ",".join(aDis)
        return ""

    def _render_disciplines(self, oColumn, oCell, oModel, oIter):
        "display the card disciplines"
        oCard = self._get_card(oIter)
        oCell.set_property("text", self._get_data_disciplines(oCard))

    def _get_data_expansions(self, oCard):
        "get expansion info"
        if not oCard is None:
            aExp = [oP.expansion.shortname + "(" + oP.rarity.name + ")" for 
                    oP in oCard.rarity]
            aExp.sort()
            return ",".join(aExp)
        return ""

    def _render_expansions(self, oColumn, oCell, oModel, oIter):
        "Display expanson info"
        oCard = self._get_card(oIter)
        oCell.set_property("text", self._get_data_expansions(oCard))

    def _get_data_group(self, oCard):
        "get the group info for the card"
        if not oCard is None and not oCard.group is None:
            return oCard.group
        return -1

    def _render_group(self, oColumn, oCell, oModel, oIter):
        "Display the group info"
        oCard = self._get_card(oIter)
        iGrp = self._get_data_group(oCard)
        if iGrp != -1:
            oCell.set_property("text", str(iGrp))
        else:
            oCell.set_property("text", "")

    def _get_data_capacity(self, oCard):
        "Get the cards capacity"
        if not oCard is None and not oCard.capacity is None:
            return oCard.capacity
        return -1

    def _render_capacity(self, oColumn, oCell, oModel, oIter):
        "Display capacity in the column"
        oCard = self._get_card(oIter)
        iCap = self._get_data_capacity(oCard)
        if iCap != -1:
            oCell.set_property("text", str(iCap))
        else:
            oCell.set_property("text", "")

    # pylint: enable-msg=R0201, W0613
    # Dialog and Menu Item Creation

    def get_menu_item(self):
        """Register on 'Plugins' menu"""
        if not self.check_versions() or not self.check_model_type():
            return None
        oSelector = gtk.MenuItem("Select Extra Columns")
        oSelector.connect("activate", self.activate)
        return ('Plugins', oSelector)

    # pylint: disable-msg=W0613
    # oWidget required by function signature
    def activate(self, oWidget):
        "Handle menu activation"
        oDlg = self.make_dialog()
        oDlg.run()
    # pylint: enable-msg=W0613

    def make_dialog(self):
        "Create the column selection dialog"
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
        for sName in self._dCols:
            oBut = gtk.CheckButton(sName)
            oBut.set_active(sName in aColsInUse)
            # pylint: disable-msg=E1101
            # pylint doesn't detect vbox's methods
            oDlg.vbox.pack_start(oBut)
            self._aButtons.append(oBut)

        oDlg.show_all()

        return oDlg

    # Actions

    def handle_response(self, oDlg, oResponse):
        "Handle user response from the dialog"
        if oResponse == gtk.RESPONSE_CANCEL:
            oDlg.destroy()
        elif oResponse == gtk.RESPONSE_OK:
            aColsInUse = []
            for oBut in self._aButtons:
                if oBut.get_active():
                    sLabel = oBut.get_label()
                    aColsInUse.append(sLabel)
            self.set_cols_in_use(aColsInUse)
            oDlg.destroy()

    def set_cols_in_use(self, aCols):
        "Add columns to the view"
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
            oCell = gtk.CellRendererText()
            oCell.set_property('style', pango.STYLE_ITALIC)
            oColumn = gtk.TreeViewColumn(sCol, oCell)
            oColumn.set_cell_data_func(oCell, self._dCols[sCol])
            self.view.insert_column(oColumn, iNum + 2)
            oColumn.set_sort_column_id(iNum + 2)
            self.model.set_sort_func(iNum + 2, self.sort_column,
                    self._dSortDataFuncs[sCol])

    # pylint: disable-msg=W0613
    # oModel required by gtk's function signature
    def sort_column(self, oModel, oIter1, oIter2, oGetData):
        """
        Stringwise comparision of oIter1 and oIter2. 
        Return -1 if oIter1 < oIter, 0 in ==, 1 if >
        """
        oCard1 = self._get_card(oIter1)
        oCard2 = self._get_card(oIter2)
        if oCard1 is None or oCard2 is None:
            # Not comparing cards, sort on name only
            sName1 = self.model.getNameFromIter(oIter1).lower()
            sName2 = self.model.getNameFromIter(oIter2).lower()
            if sName1 < sName2:
                iRes = -1
            elif sName1 > sName2:
                iRes = 1
            else:
                iRes = 0
            return iRes
        oVal1 = oGetData(oCard1)
        oVal2 = oGetData(oCard2)
        if oVal1 < oVal2:
            iRes = -1
        elif oVal1 > oVal2:
            iRes = 1
        elif oCard1.name < oCard2.name:
            # Values agrees, so sort on card name
            iRes = -1
        else:
            iRes = 1 # Card names assumed to be unique
        return iRes
    # pylint: enable-msg=W0613

    def get_cols_in_use(self):
        "Get which extra columns have been added to view"
        return [oCol.get_property("title") for oCol in self._get_col_objects()]

    def _get_col_objects(self):
        "Get the actual TreeColumn in the view"
        return [oCol for oCol in self.view.get_columns() if 
                oCol.get_property("title") in self._dCols]

# pylint: disable-msg=C0103
# accept plugin name
plugin = ExtraCardViewColumns
