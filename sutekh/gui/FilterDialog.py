# FilterDialog.py
# Dialog for setting Filter Parameters
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk
import copy
from sutekh.gui.ScrolledList import ScrolledList
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh import FilterParser
from sutekh.gui.ConfigFile import ConfigFileListener

aDefaultFilterList = [
        "Clan IN $foo",
        "Discipline in $foo",
        "CardType in $foo",
        "CardText in $foo",
        "CardName in $foo"
        ]

class FilterDialog(gtk.Dialog,ConfigFileListener):

    __iAddButtonResponse = 1
    __iDeleteButtonResponse = 2
    __iEditButtonResponse = 3

    def __init__(self,parent,oConfig):
        super(FilterDialog,self).__init__("Specify Filter", \
                parent,gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        # Need to add these buttons so we get the right order
        self.add_button( "Add New Filter", self.__iAddButtonResponse)
        # Want a reference to this button, so we can fiddle active state
        self.__oEditButton =  self.add_button( "Edit Filter",\
                self.__iEditButtonResponse)
        self.__oDeleteButton = self.add_button("Delete Filter",\
                self.__iDeleteButtonResponse)
        self.action_area.pack_start(gtk.VSeparator(),expand=True)
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.__oDeleteButton.set_sensitive(False)
        self.__oEditButton.set_sensitive(False)
        self.__oParser = FilterParser.FilterParser()
        self.__oConfig = oConfig
        self.connect("response", self.__buttonResponse)
        self.__dExpanded = {}
        self.__dASTs = {}
        self.__dButtons = {}
        self.set_default_size(700,550)
        self.__oData = None
        self.__bWasCancelled = False
        self.__oRadioGroup = None
        oFrame = gtk.Frame("Current Filter to Edit")
        self.__oExpandedArea = gtk.HBox(spacing=5)
        oFrame.add(self.__oExpandedArea)
        self.__oRadioArea = gtk.VBox()
        self.__sExpanded = None
        oHScrolledWindow = AutoScrolledWindow(oFrame,True)
        oHScrolledWindow.set_size_request(680,450)
        self.vbox.pack_start(oHScrolledWindow)
        self.vbox.pack_start(self.__oRadioArea)
        self.vbox.set_homogeneous(False)
        self.__dFilterList = {}
        self.__aDefaultLabels = []
        # Setup default filters
        # First filter is expanded by default
        for sFilter in aDefaultFilterList:
            # Parse the filter into the seperate bits needed
            try:
                oAST = self.__oParser.apply(sFilter)
            except ValueError:
                self.__doComplaint("Invalid Filter Syntax: "+sFilter)
                continue
            sId = self.__addFilterToDialog(oAST,sFilter)
            self.__aDefaultLabels.append(sId)
        self.__expandFilter(self.__oRadioGroup, self.__aDefaultLabels[0])
        # Load other filters from config file
        aAllFilters = oConfig.getFiltersKeys()
        sMessages = ''
        for sId,sFilter in aAllFilters:
            try:
                oAST = self.__oParser.apply(sFilter)
                self.__addFilterToDialog(oAST,sFilter,sId)
            except ValueError:
                sMessages += sFilter + "\n"
                self.__oConfig.removeFilter(sFilter)
        if sMessages != '':
            self.__doComplaint("The Following Invalid filters have been removed from the config file:\n "+sMessages)
        self.show_all()
        # Add Listener, so we catch changes in future
        oConfig.addListener(self)

    def __expandFilter(self, oRadioButton, sId):
        """When the user selects a radio button, expand
           the options"""
        if sId != self.__sExpanded:
            # Remove the previous filter
            for child in self.__oExpandedArea.get_children():
                self.__oExpandedArea.remove(child)
            self.__sExpanded = sId
            for child in self.__dExpanded[sId]:
                self.__oExpandedArea.pack_start(child,expand=False)
            self.__oExpandedArea.show_all()
            if sId not in self.__aDefaultLabels:
                # User defined filter, can be deleted & edited
                self.__oDeleteButton.set_sensitive(True)
                self.__oEditButton.set_sensitive(True)
            else:
                self.__oDeleteButton.set_sensitive(False)
                self.__oEditButton.set_sensitive(False)

    def __addFilterToDialog(self,oAST,sFilter,sId=''):
        aFilterParts = oAST.getValues()
        if sId == '' or sId in self.__dExpanded.keys():
            # ensure we have a unique key here
            iNum = len(self.__dExpanded)
            sId = 'Filter '+str(iNum)
            while sId in self.__dExpanded.keys():
                iNum += 1
                sId = 'Filter '+str(iNum)
        self.__dFilterList[sId] = sFilter
        self.__dExpanded[sId] = []
        self.__dASTs[sId] = oAST
        self.__addPartsToDialog(aFilterParts,sFilter,sId)
        return sId

    def __replaceFilterInDialog(self,oAST,sOldFilter,sNewFilter,sId):
        aFilterParts = oAST.getValues()
        self.__dFilterList[sId] = sNewFilter
        self.__dExpanded[sId] = []
        self.__dASTs[sId] = oAST
        oRadioButton = self.__dButtons[sId]
        self.__oRadioArea.remove(oRadioButton)
        del self.__dButtons[sId]
        self.__addPartsToDialog(aFilterParts,sNewFilter,sId)
        self.__oRadioGroup.clicked()
        self.__dButtons[sId].clicked()

    def __addPartsToDialog(self,aFilterParts,sFilter,sId):
        sPrevName = None
        for oPart in aFilterParts:
            if oPart.isValue():
                oWidget = gtk.Label(oPart.value)
                self.__dExpanded[sId].append(oWidget)
            elif oPart.isList():
                assert(sPrevName is not None)
                oWidget = self.__makeScrolledList(sPrevName,oPart.value)
                self.__dExpanded[sId].append(oWidget)
            elif oPart.isEntry():
                oWidget = gtk.Entry(100)
                oWidget.set_width_chars(30)
                self.__dExpanded[sId].append(oWidget)
            sPrevName = oPart.value
        oRadioButton = gtk.RadioButton(self.__oRadioGroup)
        if self.__oRadioGroup is None:
            self.__oRadioGroup = oRadioButton
        oRadioButton.set_label(sFilter)
        self.__dButtons[sId] = oRadioButton
        oRadioButton.connect("toggled",self.__expandFilter,sId)
        self.__oRadioArea.pack_start(oRadioButton)

    def __removeFilterFromDialog(self,sId):
        sFilter = self.__dFilterList[sId]
        self.__oConfig.removeFilter(sFilter,sId)

    def removeFilter(self,sFilter,sId):
        del self.__dASTs[sId]
        del self.__dExpanded[sId]
        del self.__dFilterList[sId]
        oRadioButton = self.__dButtons[sId]
        self.__oRadioArea.remove(oRadioButton)
        del self.__dButtons[sId]
        self.show_all()

    def getFilter(self):
        return self.__oData

    def Cancelled(self):
        return self.__bWasCancelled

    def __buttonResponse(self,widget,response):
        if response ==  gtk.RESPONSE_OK:
            self.__bWasCancelled = False
            # Construct the Final filter string
            oNewAST = self.__parseDialogState()
            # Push this into yacc and get the constructed filter out of
            # it
            self.__oData = oNewAST.getFilter()
        elif response == self.__iAddButtonResponse:
            self.__doAddEditFilterDialog()
            # Recursive, not sure if that's such a good thing
            return self.run()
        elif response == self.__iDeleteButtonResponse:
            self.__doRemoveFilter()
            return self.run()
        elif response == self.__iEditButtonResponse:
            sFilter = self.__dFilterList[self.__sExpanded]
            self.__doAddEditFilterDialog(sFilter)
            return self.run()
        else:
            self.__bWasCancelled = True
        self.hide()

    def __parseDialogState(self):
        # FIXME: Should be defined somewhere else for better maintainability
        oNewAST = copy.deepcopy(self.__dASTs[self.__sExpanded])
        aNewFilterValues = oNewAST.getValues()
        # Need pointers to the new nodes
        for (child,oFilterPart) in zip(self.__dExpanded[self.__sExpanded],aNewFilterValues):
            if type(child) is ScrolledList:
                # Some of this logic should be pushed down to ScrolledList
                aVals = []
                Model,Selection = child.TreeView.get_selection().get_selected_rows()
                for oPath in Selection:
                    oIter = Model.get_iter(oPath)
                    name = Model.get_value(oIter,0)
                    if oFilterPart.node.filtertype not in FilterParser.aNumericFilters:
                        if oFilterPart.node.filtertype in FilterParser.aWithFilters:
                            sPart1,sPart2 = name.split(' with ')
                            # Ensure no issues with spaces, etc.
                            aVals.append('"' + sPart1 + '" with "' + sPart2 + '"')
                        else:
                            aVals.append('"' + name + '"')
                    else:
                        if name != 'X':
                            aVals.append(name)
                        else:
                            aVals.append('-1')
                if aVals != []:
                    oFilterPart.node.setValues(aVals)
            elif type(child) is gtk.Entry:
                sText = child.get_text()
                if sText != '':
                    oFilterPart.node.setValues(['"' + sText + '"'])
        return oNewAST

    def __makeScrolledList(self,sName,aVals):
        oWidget = ScrolledList(sName)
        oWidget.set_size_request(200,400)
        aList = oWidget.get_list()
        aList.clear()
        for sEntry in aVals:
            oIter = aList.append(None)
            aList.set(oIter,0,sEntry)
        return oWidget

    def __doComplaint(self,sMessage):
        oComplaint = gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
                gtk.BUTTONS_CLOSE,sMessage)
        oComplaint.run()
        oComplaint.destroy()

    def __doAddEditFilterDialog(self,sEditFilter=''):
        if sEditFilter == '':
            sTitle = "Enter the New Filter"
        else:
            sTitle = "Edit the Filter"
        oEditFilterDialog = gtk.Dialog(sTitle,self,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                ( gtk.STOCK_OK, gtk.RESPONSE_OK,
                    gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL ) )
        sHelpText = "<b>Filter Syntx</b>\n" \
                "<i>FilterPart</i> { <b>OP</b> <i>FilterPart</i> } .... \n" \
                "where <b>OP</b> is either AND or OR\n" \
                "and <i>FilterPart</i> is FilterType IN comma seperated list of values\n" \
                "or FilterType = $variable \n" \
                "FilterType can be any of the following\n"
        for oFilterType in FilterParser.aFilters:
            sHelpText += "<b>"+oFilterType.keyword+"</b> which takes "+oFilterType.helptext+"\n"
        oHelpText = gtk.Label()
        oHelpText.set_markup(sHelpText)
        oEntry = gtk.Entry(300)
        oEntry.set_text(sEditFilter)
        oEntry.set_width_chars(70)
        oEditFilterDialog.vbox.pack_start(oHelpText)
        oEditFilterDialog.vbox.pack_start(oEntry)
        oEditFilterDialog.show_all()
        bDone = False
        while not bDone:
            response = oEditFilterDialog.run()
            if response == gtk.RESPONSE_OK:
                sFilter = oEntry.get_text()
                try:
                    oAST = self.__oParser.apply(sFilter)
                except ValueError:
                    self.__doComplaint("Invalid Filter Syntax: "+sFilter)
                    # Rerun the dialog, should do the right thing
                    continue
                aWrongVals = oAST.getInvalidValues()
                if aWrongVals is not None:
                    sMessage = "The following values are invalid for the filter\n"
                    for sVal in aWrongVals:
                        sMessage += sVal + '\n'
                    self.__doComplaint(sMessage)
                    continue
                if sEditFilter == '':
                    self.__oConfig.addFilter(sFilter)
                else:
                    self.__oConfig.replaceFilter(sEditFilter,sFilter,self.__sExpanded)
            bDone = True
            oEditFilterDialog.destroy()

    def replaceFilter(self,sOldFilter,sNewFilter,sId):
        try:
            # Should be safe, but just in case
            oAST = self.__oParser.apply(sNewFilter)
        except ValueError:
            self.__doComplaint("Invalid Filter Syntax: " + sNewFilter)
            return
        self.__replaceFilterInDialog(oAST,sOldFilter,sNewFilter,sId)
        self.show_all()

    def addFilter(self,sFilter,sId):
        try:
            # Should be safe, but just in case
            oAST = self.__oParser.apply(sFilter)
        except ValueError:
            self.__doComplaint("Invalid Filter Syntax: " + sFilter)
            return
        self.__addFilterToDialog(oAST,sFilter,sId)
        self.show_all()

    def __doRemoveFilter(self):
        sId = self.__sExpanded
        # Needed because this changes self.__sExpanded
        self.__oRadioGroup.clicked()
        self.__removeFilterFromDialog(sId)
