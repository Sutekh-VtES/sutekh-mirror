# FilterDialog.py
# Dialog for setting Filter Parameters
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk
import copy
from sutekh.gui.ScrolledList import ScrolledList
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.core import FilterParser
from sutekh.gui.ConfigFile import ConfigFileListener

aDefaultFilterList = [
        "Clan IN $foo",
        "Discipline in $foo",
        "CardType in $foo",
        "CardText in $foo",
        "CardName in $foo",
        "AbstractCardSetName in $foo",
        "PhysicalCardSetName in $foo",
        "PhysicalExpansion in $foo"
        ]

class FilterDialog(SutekhDialog, ConfigFileListener):

    __iAddButtonResponse = 1
    __iDeleteButtonResponse = 2
    __iEditButtonResponse = 3

    def __init__(self, oParent, oConfig, sFilterType):
        super(FilterDialog, self).__init__("Specify Filter",
                oParent, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        # Need to add these buttons so we get the right order
        self.add_button( "Add New Filter", self.__iAddButtonResponse)
        # Want a reference to this button, so we can fiddle active state
        self.__oEditButton =  self.add_button( "Edit Filter",
                self.__iEditButtonResponse)
        self.__oDeleteButton = self.add_button("Delete Filter",
                self.__iDeleteButtonResponse)
        self.action_area.pack_start(gtk.VSeparator(), expand=True)
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.__oDeleteButton.set_sensitive(False)
        self.__oEditButton.set_sensitive(False)
        self.__oParser = FilterParser.FilterParser()
        self.__oConfig = oConfig
        self.__sFilterType = sFilterType
        self.connect("response", self.__button_response)
        self.__dExpanded = {}
        self.__dASTs = {}
        self.__dButtons = {}
        self.set_default_size(700, 550)
        self.__oData = None
        self.__bWasCancelled = False
        self.__oRadioGroup = None
        oFrame = gtk.Frame("Current Filter to Edit")
        self.__oExpandedArea = gtk.HBox(spacing=5)
        oFrame.add(self.__oExpandedArea)
        self.__oRadioArea = gtk.VBox()
        self.__sExpanded = None
        oHScrolledWindow = AutoScrolledWindow(oFrame, True)
        oHScrolledWindow.set_size_request(680, 450)
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
            except ValueError, oExcep:
                do_complaint_error("Invalid Filter: %s\n Error: %s" % (sFilter, str(oExcep)))
                continue
            sId = self.__add_filter_to_dialog(oAST, sFilter)
            self.__aDefaultLabels.append(sId)
        self.__expand_filter(self.__oRadioGroup, self.__aDefaultLabels[0])
        # Load other filters from config file
        aAllFilters = oConfig.getFiltersKeys()
        sMessages = ''
        for sId, sFilter in aAllFilters:
            try:
                oAST = self.__oParser.apply(sFilter)
                self.__add_filter_to_dialog(oAST, sFilter, sId)
            except ValueError:
                sMessages += sFilter + "\n"
                self.__oConfig.removeFilter(sFilter, sId)
        if sMessages != '':
            do_complaint_error("The Following Invalid filters have been removed from the config file:\n " + sMessages)
        self.show_all()
        # Add Listener, so we catch changes in future
        oConfig.addListener(self)

    def __expand_filter(self, oRadioButton, sId):
        """
        When the user selects a radio button, expand
        the options
        """
        if sId != self.__sExpanded and sId in self.__dExpanded.keys():
            # Remove the previous filter
            for oChild in self.__oExpandedArea.get_children():
                self.__oExpandedArea.remove(oChild)
            self.__sExpanded = sId
            for oChild in self.__dExpanded[sId]:
                self.__oExpandedArea.pack_start(oChild, expand=False)
            self.__oExpandedArea.show_all()
            if sId not in self.__aDefaultLabels:
                # User defined filter, can be deleted & edited
                self.__oDeleteButton.set_sensitive(True)
                self.__oEditButton.set_sensitive(True)
            else:
                self.__oDeleteButton.set_sensitive(False)
                self.__oEditButton.set_sensitive(False)

    def __add_filter_to_dialog(self, oAST, sFilter, sId=''):
        if sId == '' or sId in self.__dExpanded.keys():
            # ensure we have a unique key here
            iNum = len(self.__dExpanded)
            sId = 'Filter '+str(iNum)
            while sId in self.__dExpanded.keys():
                iNum += 1
                sId = 'Filter '+str(iNum)
        self.__dFilterList[sId] = sFilter
        if self.__sFilterType not in oAST.get_type():
            return sId
        self.__dExpanded[sId] = []
        self.__dASTs[sId] = oAST
        aFilterParts = oAST.get_values()
        self.__add_parts_to_dialog(aFilterParts, sFilter, sId)
        return sId

    def __replace_filter_in_dialog(self, oAST, sOldFilter, sNewFilter, sId):
        """
        Replace an existing filter with the new one
        Preserve selections if possible
        """
        self.__dFilterList[sId] = sNewFilter
        if self.__sFilterType in oAST.get_type():
            aFilterParts = oAST.get_values()
            if sId in self.__dExpanded.keys():
                # Temporary copy of the values, so we can reuse the values
                aOldFilterWidgets = self.__dExpanded[sId]
                aOldASTValues = self.__dASTs[sId].get_values()
                self.__dExpanded[sId] = []
                self.__dASTs[sId] = oAST
                oRadioButton = self.__dButtons[sId]
                self.__oRadioArea.remove(oRadioButton)
                del self.__dButtons[sId]
                self.__add_parts_to_dialog(aFilterParts, sNewFilter, sId)
                self.__oRadioGroup.clicked()
                self.__dButtons[sId].clicked()
                # We update the new filter with values from the old filter where
                # appropriate
                aNewValues = oAST.get_values()
                self.__copy_values(zip(self.__dExpanded[sId], aNewValues),
                        zip(aOldFilterWidgets, aOldASTValues))

    def __copy_values(self, aNewFilterVals, aOldFilterVals):
        for oWidget, oFilterPart in aNewFilterVals:
            if type(oWidget) is ScrolledList or type(oWidget) is gtk.Entry:
                for oOldWidget, oOldPart in aOldFilterVals:
                    if type(oOldWidget) is ScrolledList or \
                            type(oOldWidget) is gtk.Entry:
                        if oOldPart.node.filtertype == oFilterPart.node.filtertype and \
                                oOldPart.node.get_name() == oFilterPart.node.get_name():
                            if type(oWidget) is ScrolledList:
                                aSelection = oOldWidget.get_selection()
                                oWidget.set_selection(aSelection)
                            else:
                                oWidget.set_text(oOldWidget.get_text())

    def __add_parts_to_dialog(self, aFilterParts, sFilter, sId):
        sPrevName = None
        for oPart in aFilterParts:
            if oPart.is_value():
                oWidget = gtk.Label(oPart.value)
                self.__dExpanded[sId].append(oWidget)
            elif oPart.is_list():
                assert(sPrevName is not None)
                oWidget = self.__make_scrolled_list(sPrevName, oPart.value)
                self.__dExpanded[sId].append(oWidget)
            elif oPart.is_entry():
                oWidget = gtk.Entry(100)
                oWidget.set_width_chars(30)
                self.__dExpanded[sId].append(oWidget)
            elif oPart.is_None():
                oWidget = gtk.Label('')
                self.__dExpanded[sId].append(oWidget)
            sPrevName = oPart.value
        oRadioButton = gtk.RadioButton(self.__oRadioGroup)
        if self.__oRadioGroup is None:
            self.__oRadioGroup = oRadioButton
        oRadioButton.set_label(sFilter)
        self.__dButtons[sId] = oRadioButton
        oRadioButton.connect("toggled", self.__expand_filter, sId)
        self.__oRadioArea.pack_start(oRadioButton)

    def __remove_filter_from_dialog(self, sId):
        sFilter = self.__dFilterList[sId]
        self.__oConfig.removeFilter(sFilter, sId)

    def removeFilter(self, sFilter, sId):
        del self.__dFilterList[sId]
        if sId in self.__dASTs:
            del self.__dASTs[sId]
            del self.__dExpanded[sId]
            oRadioButton = self.__dButtons[sId]
            self.__oRadioArea.remove(oRadioButton)
            del self.__dButtons[sId]
            self.__oRadioGroup.clicked()
            self.__oRadioArea.show_all()

    def getFilter(self):
        return self.__oData

    def Cancelled(self):
        return self.__bWasCancelled

    def __button_response(self, oWidget, iResponse):
        if iResponse ==  gtk.RESPONSE_OK:
            self.__bWasCancelled = False
            # Construct the Final filter string
            oNewAST = self.__parse_dialog_state()
            # Push this into yacc and get the constructed filter out of
            # it
            self.__oData = oNewAST.get_filter()
        elif iResponse == self.__iAddButtonResponse:
            self.__do_add_edit_filter_dialog()
            # Recursive, not sure if that's such a good thing
            return self.run()
        elif iResponse == self.__iDeleteButtonResponse:
            self.__do_remove_filter()
            return self.run()
        elif iResponse == self.__iEditButtonResponse:
            sFilter = self.__dFilterList[self.__sExpanded]
            self.__do_add_edit_filter_dialog(sFilter)
            return self.run()
        else:
            self.__bWasCancelled = True
        self.hide()

    def __parse_dialog_state(self):
        # FIXME: Should be defined somewhere else for better maintainability
        oNewAST = copy.deepcopy(self.__dASTs[self.__sExpanded])
        aNewFilterValues = oNewAST.get_values()
        # Need pointers to the new nodes
        for (oChild, oFilterPart) in zip(self.__dExpanded[self.__sExpanded],
                aNewFilterValues):
            if type(oChild) is ScrolledList:
                # Some of this logic should be pushed down to ScrolledList
                aVals = []
                aSelection = oChild.get_selection()
                for sName in aSelection:
                    if oFilterPart.node.filtertype in FilterParser.aWithFilters:
                        sPart1, sPart2 = sName.split(' with ')
                        # Ensure no issues with spaces, etc.
                        aVals.append('"' + sPart1 + '" with "' + sPart2 + '"')
                    else:
                        aVals.append('"' + sName + '"')
                if aVals != []:
                    oFilterPart.node.setValues(aVals)
            elif type(oChild) is gtk.Entry:
                sText = oChild.get_text()
                if sText != '':
                    oFilterPart.node.setValues(['"' + sText + '"'])
        return oNewAST

    def __make_scrolled_list(self, sName, aVals):
        oWidget = ScrolledList(sName)
        oWidget.set_size_request(200, 400)
        oWidget.fill_list(aVals)
        return oWidget

    def __do_add_edit_filter_dialog(self, sEditFilter=''):
        if sEditFilter == '':
            sTitle = "Enter the New Filter"
        else:
            sTitle = "Edit the Filter"
        oEditFilterDialog = SutekhDialog(sTitle, self,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                    gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        sHelpText = "<b>Filter Syntx</b>\n" \
                "<i>FilterPart</i> { <b>OP</b> <i>FilterPart</i> } .... \n" \
                "where <b>OP</b> is either AND or OR\n" \
                "and <i>FilterPart</i> is FilterType IN comma seperated list of values\n" \
                "or FilterType = $variable \n" \
                "NOT FilterType will invert the meaning of the filter.\n" \
                "FilterType can be any of the following\n"
        for oFilterType in FilterParser.aFilters:
            if self.__sFilterType in oFilterType.types:
                sHelpText += "<b>" + oFilterType.keyword + "</b> which takes " \
                        + oFilterType.helptext + "\n"
        oHelpText = gtk.Label()
        oHelpText.set_markup(sHelpText)
        oHelpText.set_selectable(True)
        oEntry = gtk.Entry(300)
        oEntry.set_text(sEditFilter)
        oEntry.set_width_chars(70)
        oEditFilterDialog.vbox.pack_start(oHelpText)
        oEditFilterDialog.vbox.pack_start(oEntry)
        oEditFilterDialog.show_all()
        bDone = False
        while not bDone:
            iResponse = oEditFilterDialog.run()
            if iResponse == gtk.RESPONSE_OK:
                sFilter = oEntry.get_text()
                try:
                    oAST = self.__oParser.apply(sFilter)
                except ValueError, oExcep:
                    do_complaint_error("Invalid Filter: %s\n Error: %s" % (sFilter, str(oExcep)))
                    # Rerun the dialog, should do the right thing
                    continue
                aWrongVals = oAST.get_invalid_values()
                if aWrongVals is not None:
                    sMessage = "The following values are invalid for the filter\n"
                    for sVal in aWrongVals:
                        sMessage += sVal + '\n'
                    do_complaint_error(sMessage)
                    continue
                if self.__sFilterType not in oAST.get_type():
                    sMessage = "Filter isn't valid for this pane\n"
                    do_complaint_error(sMessage)
                    continue
                if sEditFilter == '':
                    self.__oConfig.addFilter(sFilter)
                else:
                    self.__oConfig.replaceFilter(sEditFilter, sFilter,
                            self.__sExpanded)
            bDone = True
            oEditFilterDialog.destroy()

    def replaceFilter(self, sOldFilter, sNewFilter, sId):
        try:
            # Should be safe, but just in case
            oAST = self.__oParser.apply(sNewFilter)
        except ValueError, oExcep:
            do_complaint_error("Invalid Filter: %s\n Error: %s" % (sNewFilter, str(oExcep)))
            return
        self.__replace_filter_in_dialog(oAST, sOldFilter, sNewFilter, sId)
        self.__oRadioArea.show_all()

    def addFilter(self, sFilter, sId):
        try:
            # Should be safe, but just in case
            oAST = self.__oParser.apply(sFilter)
        except ValueError, oExcep:
            do_complaint_error("Invalid Filter: %s\n Error: %s" % (sFilter, str(oExcep)))
            return
        self.__add_filter_to_dialog(oAST, sFilter, sId)
        self.__oRadioArea.show_all()

    def __do_remove_filter(self):
        sId = self.__sExpanded
        # Needed because this changes self.__sExpanded
        self.__remove_filter_from_dialog(sId)
