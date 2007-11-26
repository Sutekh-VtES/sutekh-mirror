# ExtraCardViewColumns.py
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

    # Rendering Functions

    def _getCard(self,oIter):
        if self.model.iter_depth(oIter) == 1:
            # Only try and lookup things that look like they should be cards
            try:
                oCard = AbstractCard.byCanonicalName(self.model.getNameFromIter(oIter).lower())
                return oCard
            except SQLObjectNotFound:
                return None
        else:
            return None

    def _renderCardType(self,oColumn,oCell,oModel,oIter):
        oCard = self._getCard(oIter)
        if not oCard is None:
            aTypes = [x.name for x in oCard.cardtype]
            aTypes.sort()
            oCell.set_property("text", ",".join(aTypes))
        else:
            oCell.set_property("text","")

    def _renderClan(self,oColumn,oCell,oModel,oIter):
        oCard = self._getCard(oIter)
        if not oCard is None:
            aClans = [x.name for x in oCard.clan]
            aClans.sort()
            oCell.set_property("text", ",".join(aClans))
        else:
            oCell.set_property("text","")

    def _renderDisciplines(self,oColumn,oCell,oModel,oIter):
        oCard = self._getCard(oIter)
        if not oCard is None:
            aDis = [(oP.level != 'superior') and oP.discipline.name or oP.discipline.name.upper() for oP in oCard.discipline]
            aDis.sort()
            oCell.set_property("text",",".join(aDis))
        else:
            oCell.set_property("text","")

    def _renderExpansions(self,oColumn,oCell,oModel,oIter):
        oCard = self._getCard(oIter)
        if not oCard is None:
            aExp = [oP.expansion.shortname + "(" + oP.rarity.name + ")" for oP in oCard.rarity]
            aExp.sort()
            oCell.set_property("text",",".join(aExp))
        else:
            oCell.set_property("text","")

    def _renderGroup(self,oColumn,oCell,oModel,oIter):
        oCard = self._getCard(oIter)
        if not oCard is None and not oCard.group is None:
            oCell.set_property("text",str(oCard.group))
        else:
            oCell.set_property("text","")

    def _renderCapacity(self,oColumn,oCell,oModel,oIter):
        oCard = self._getCard(oIter)
        if not oCard is None and not oCard.capacity is None:
            oCell.set_property("text",str(oCard.capacity))
        else:
            oCell.set_property("text","")

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
        for oCol in self._getColObjects():
            self.view.remove_column(oCol)

        for i, sCol in enumerate(aCols):
            oCell = gtk.CellRendererText()
            oCell.set_property('style', pango.STYLE_ITALIC)
            self.view.insert_column_with_data_func(i + 2,sCol,oCell,self._dCols[sCol])

    def getColsInUse(self):
        return [oCol.get_property("title") for oCol in self._getColObjects()]

    def _getColObjects(self):
        return [oCol for oCol in self.view.get_columns() if oCol.get_property("title") in self._dCols]

plugin = ExtraCardViewColumns
