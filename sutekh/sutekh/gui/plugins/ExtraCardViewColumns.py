# ExtraCardViewColumns.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk, pango
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import SutekhDialog
from sutekh.core.SutekhObjects import AbstractCard, PhysicalCard, \
                                      AbstractCardSet, PhysicalCardSet
from sqlobject import SQLObjectNotFound

class ExtraCardViewColumns(CardListPlugin):
    dTableVersions = {}
    aModelsSupported = [AbstractCard, PhysicalCard, AbstractCardSet, PhysicalCardSet]

    def __init__(self,*args,**kws):
        super(ExtraCardViewColumns,self).__init__(*args,**kws)
        self._dCols = {}
        self._dCols['Card Type'] = self._renderCardType
        self._dCols['Clan'] = self._renderClan
        self._dCols['Disciplines'] = self._renderDisciplines
        self._dCols['Expansions'] = self._renderExpansions
        self._dCols['Group'] = self._renderGroup
        self._dCols['Capacity'] = self._renderCapacity

        self._dSortDataFuncs = {}
        self._dSortDataFuncs['Card Type'] = self._get_data_cardtype
        self._dSortDataFuncs['Clan'] = self._get_data_clan
        self._dSortDataFuncs['Disciplines'] = self._get_data_disciplines
        self._dSortDataFuncs['Expansions'] = self._get_data_expansions
        self._dSortDataFuncs['Group'] = self._get_data_group
        self._dSortDataFuncs['Capacity'] = self._get_data_capacity

        self._dCardCache = {} # Used for sorting

    # Rendering Functions

    def _getCard(self,oIter):
        if self.model.iter_depth(oIter) == 1:
            # Only try and lookup things that look like they should be cards
            try:
                sCardName = self.model.getNameFromIter(oIter).lower()
                # Cache lookups, so we don't hit the database so hard when sorting
                if not self._dCardCache.has_key(sCardName):
                     self._dCardCache[sCardName] = \
                             AbstractCard.byCanonicalName(sCardName)
                return self._dCardCache[sCardName]
            except SQLObjectNotFound:
                return None
        else:
            return None

    def _get_data_cardtype(self, oCard):
        if not oCard is None:
            aTypes = [x.name for x in oCard.cardtype]
            aTypes.sort()
            return ",".join(aTypes)
        return ""

    def _renderCardType(self,oColumn,oCell,oModel,oIter):
        oCard = self._getCard(oIter)
        oCell.set_property("text", self._get_data_cardtype(oCard))

    def _get_data_clan(self, oCard):
        if not oCard is None:
            aClans = [x.name for x in oCard.clan]
            aClans.sort()
            return ",".join(aClans)
        return ""

    def _renderClan(self,oColumn,oCell,oModel,oIter):
        oCard = self._getCard(oIter)
        oCell.set_property("text", self._get_data_clan(oCard))

    def _get_data_disciplines(self, oCard):
        if not oCard is None:
            aDis = [(oP.level != 'superior') and oP.discipline.name or oP.discipline.name.upper() for oP in oCard.discipline]
            aDis.sort()
            return ",".join(aDis)
        return ""

    def _renderDisciplines(self,oColumn,oCell,oModel,oIter):
        oCard = self._getCard(oIter)
        oCell.set_property("text", self._get_data_disciplines(oCard))

    def _get_data_expansions(self, oCard):
        if not oCard is None:
            aExp = [oP.expansion.shortname + "(" + oP.rarity.name + ")" for oP in oCard.rarity]
            aExp.sort()
            return ",".join(aExp)
        return ""

    def _renderExpansions(self,oColumn,oCell,oModel,oIter):
        oCard = self._getCard(oIter)
        oCell.set_property("text", self._get_data_expansions(oCard))

    def _get_data_group(self, oCard):
        if not oCard is None and not oCard.group is None:
            return oCard.group
        return -1

    def _renderGroup(self,oColumn,oCell,oModel,oIter):
        oCard = self._getCard(oIter)
        iGrp = self._get_data_group(oCard)
        if iGrp != -1:
            oCell.set_property("text", str(iGrp))
        else:
            oCell.set_property("text", "")

    def _get_data_capacity(self, oCard):
        if not oCard is None and not oCard.capacity is None:
            return oCard.capacity
        return -1

    def _renderCapacity(self,oColumn,oCell,oModel,oIter):
        oCard = self._getCard(oIter)
        iCap = self._get_data_capacity(oCard)
        if iCap != -1:
            oCell.set_property("text", str(iCap))
        else:
            oCell.set_property("text", "")


    # Dialog and Menu Item Creation

    def get_menu_item(self):
        """
        Overrides method from base class.
        """
        if not self.check_versions() or not self.check_model_type():
            return None
        iSelector = gtk.MenuItem("Select Extra Columns")
        iSelector.connect("activate", self.activate)
        return iSelector

    def get_desired_menu(self):
        return "Plugins"

    def activate(self,oWidget):
        dlg = self.makeDialog()
        dlg.run()

    def makeDialog(self):
        name = "Select Extra Columns ..."

        oDlg = SutekhDialog(name,self.parent,
                gtk.DIALOG_DESTROY_WITH_PARENT)
        oDlg.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        oDlg.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)

        oDlg.connect("response", self.handleResponse)

        self._aButtons = []
        aColsInUse = self.getColsInUse()
        for sName, fColFunc in self._dCols.iteritems():
            oBut = gtk.CheckButton(sName)
            oBut.set_active(sName in aColsInUse)
            oDlg.vbox.pack_start(oBut)
            self._aButtons.append(oBut)

        oDlg.show_all()

        return oDlg

    # Actions

    def handleResponse(self,oDlg,oResponse):
        if oResponse == gtk.RESPONSE_CLOSE:
            oDlg.destroy()
        elif oResponse == gtk.RESPONSE_OK:
            aColsInUse = []
            for oBut in self._aButtons:
                if oBut.get_active():
                    sLabel = oBut.get_label()
                    aColsInUse.append(sLabel)
            self.setColsInUse(aColsInUse)
            oDlg.destroy()

    def setColsInUse(self,aCols):
        iSortCol, iDir = self.model.get_sort_column_id()
        if iSortCol is not None and iSortCol > 1:
            # We're changing the columns, so restore sorting to default
            self.model.set_sort_column_id(0, 0) 

        for oCol in self._getColObjects():
            self.view.remove_column(oCol)


        for i, sCol in enumerate(aCols):
            oCell = gtk.CellRendererText()
            oCell.set_property('style', pango.STYLE_ITALIC)
            oColumn = gtk.TreeViewColumn(sCol, oCell)
            oColumn.set_cell_data_func(oCell, self._dCols[sCol])
            self.view.insert_column(oColumn, i+2)
            oColumn.set_sort_column_id(i+2)
            self.model.set_sort_func(i+2, self.sort_column, self._dSortDataFuncs[sCol])

    def sort_column(self, oModel, oIter1, oIter2, oGetData):
        """
        Stringwise comparision of oIter1 and oIter2. 
        Return -1 if oIter1 < oIter, 0 in ==, 1 if >
        """
        oCard1 = self._getCard(oIter1)
        oCard2 = self._getCard(oIter2)
        if oCard1 is None or oCard2 is None:
            # Not comparing cards
            sName1 = self.model.getNameFromIter(oIter1).lower()
            sName2 = self.model.getNameFromIter(oIter2).lower()
            if sName1 < sName2:
                return -1
            elif sName1 > sName2:
                return 1
            else:
                return 0
        oVal1 = oGetData(oCard1)
        oVal2 = oGetData(oCard2)
        if oVal1 < oVal2:
            return -1
        elif oVal1 > oVal2:
            return 1
        elif oCard1.name < oCard2.name:
            return -1
        else:
            return 1 # Card names assumed to be unique

    def getColsInUse(self):
        return [oCol.get_property("title") for oCol in self._getColObjects()]

    def _getColObjects(self):
        return [oCol for oCol in self.view.get_columns() if oCol.get_property("title") in self._dCols]

plugin = ExtraCardViewColumns
