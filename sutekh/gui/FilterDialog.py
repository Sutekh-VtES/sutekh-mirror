# FilterDialog.py
# Dialog for setting Filter Parameters
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk
import copy
from sutekh.gui.ScrolledList import ScrolledList
from sutekh import FilterParser

aDefaultFilterList = [
        "Clan IN $foo",
        "Discipline in $foo",
        "CardType in $foo",
        "CardText in $foo",
        "CardName in $foo"
        ]

class FilterDialog(gtk.Dialog):

    __iAddButtonResponse = 1
    __iDeleteButtonResponse = 2

    def __init__(self,parent,oConfig):
        super(FilterDialog,self).__init__("Specify Filter", \
                parent,gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        # Need to add these buttons so we get the right order
        self.add_button( "Add New Filter", self.__iAddButtonResponse)
        # Want a reference to this button, so we can fiddle active state
        self.__oDeleteButton = self.add_button("Delete Filter",\
                self.__iDeleteButtonResponse)
        self.action_area.pack_start(gtk.VSeparator(),expand=True)
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.__oDeleteButton.set_sensitive(False)
        self.__oParser=FilterParser.FilterParser()
        self.__oConfig=oConfig
        self.connect("response", self.__buttonResponse)
        self.__dExpanded={}
        self.__dASTs={}
        self.__dButtons={}
        self.set_default_size(700,550)
        self.__oData = None
        self.__bWasCancelled = False
        self.__oRadioGroup=None
        oFrame=gtk.Frame("Current Filter to Edit")
        oFrame.set_size_request(700,430)
        self.__oExpandedArea=gtk.HBox(spacing=5)
        oFrame.add(self.__oExpandedArea)
        self.__oRadioArea=gtk.VBox()
        self.__sExpanded=None
        self.vbox.pack_start(oFrame)
        self.vbox.pack_start(self.__oRadioArea)
        self.vbox.set_homogeneous(False)
        self.__iDefaultNum=len(aDefaultFilterList)
        self.__aFilterList=aDefaultFilterList
        # First filter is expanded by default
        for sFilter in self.__aFilterList:
            # Parse the filter into the seperate bits needed
            try:
                oAST=self.__oParser.apply(sFilter)
            except ValueError:
                self.__doComplaint("Invalid Filter Syntax: "+sFilter)
                continue
            self.__addFilterToDialog(oAST,sFilter)
        self.__expandFilter(self.__oRadioGroup, "0 : "+self.__aFilterList[0],0)
        self.show_all()

    def __expandFilter(self, oRadioButton, sName, iNum):
        """When the user selects a radio button, expand
           the options"""
        if sName!=self.__sExpanded:
            # Remove the previous filter
            for child in self.__oExpandedArea.get_children():
                self.__oExpandedArea.remove(child)
            self.__sExpanded=sName
            for child in self.__dExpanded[sName]:
                self.__oExpandedArea.pack_start(child,expand=False)
            self.__oExpandedArea.show_all()
            if iNum>=self.__iDefaultNum:
                # User defined filter, can be deleted
                self.__oDeleteButton.set_sensitive(True)
            else:
                self.__oDeleteButton.set_sensitive(False)

    def __addFilterToDialog(self,oAST,sFilter):
        aFilterParts=oAST.getValues()
        iNum=len(self.__dExpanded)
        # Should we try harder to make sure this is unique?
        # do .... while sName in dExpanded.keys() type construction?
        sName=str(iNum)+" : "+sFilter
        self.__dExpanded[sName]=[]
        self.__dASTs[sName]=oAST
        for oPart in aFilterParts:
            if oPart.isValue():
                oWidget=gtk.Label(oPart.value)
                self.__dExpanded[sName].append(oWidget)
            elif oPart.isList():
                oWidget=self.__makeScrolledList(sPrevName,oPart.value)
                self.__dExpanded[sName].append(oWidget)
            elif oPart.isEntry():
                oWidget=gtk.Entry(100)
                oWidget.set_width_chars(30)
                self.__dExpanded[sName].append(oWidget)
            sPrevName=oPart.value
        oRadioButton=gtk.RadioButton(self.__oRadioGroup)
        if self.__oRadioGroup is None:
            self.__oRadioGroup=oRadioButton
        oRadioButton.set_label(sFilter)
        self.__dButtons[sName]=oRadioButton
        oRadioButton.connect("clicked",self.__expandFilter,sName, iNum)
        self.__oRadioArea.pack_start(oRadioButton)

    def getFilter(self):
        return self.__oData

    def Cancelled(self):
        return self.__bWasCancelled

    def updateFilters(self):
        # For rereading config changes, etc
        aAllFilters=self.__oConfig.getFilters()
        sMessages=''
        for sFilter in aAllFilters:
            if sFilter not in self.__aFilterList:
                try:
                    oAST=self.__oParser.apply(sFilter)
                    self.__addFilterToDialog(oAST,sFilter)
                    self.__aFilterList.append(sFilter)
                except ValueError:
                    sMessages+=sFilter+"\n"
                    self.__oConfig.removeFilter(sFilter)
        if sMessages!='':
            self.__doComplaint("The Following Invalid filters have been removed from the config file:\n "+sMessages)
        self.show_all()

    def __buttonResponse(self,widget,response):
        if response ==  gtk.RESPONSE_OK:
            self.__bWasCancelled=False
            # Construct the Final filter string
            oNewAST=self.__parseDialogState()
            # Push this into yacc and get the constructed filter out of
            # it
            self.__oData=oNewAST.getFilter()
        elif response == self.__iAddButtonResponse:
            self.__doAddFilter()
            # Recursive, not sure if that's such a good thing
            return self.run()
        elif response == self.__iDeleteButtonResponse:
            self.__doComplaint("Delete not yet implemented")
            return self.run()
        else:
            self.__bWasCancelled=True
        self.hide()

    def __parseDialogState(self):
        # FIXME: Should be defined somewhere else for better maintainability
        aNumericFilters=['Group','Cost','Capacity','Life']
        aWithFilters=['Expansion_with_Rarity','Discipline_with_Level']
        oNewAST=copy.deepcopy(self.__dASTs[self.__sExpanded])
        aNewFilterValues=oNewAST.getValues()
        # Need pointers to the new nodes
        for (child,oFilterPart) in zip(self.__dExpanded[self.__sExpanded],aNewFilterValues):
            if type(child) is ScrolledList:
                # Some of this logic should be pushed down to ScrolledList
                aVals=[]
                Model,Selection=child.TreeView.get_selection().get_selected_rows()
                for oPath in Selection:
                    oIter= Model.get_iter(oPath)
                    name = Model.get_value(oIter,0)
                    if oFilterPart.node.filtertype not in aNumericFilters:
                        if oFilterPart.node.filtertype in aWithFilters:
                            sPart1,sPart2=name.split(' : ')
                            aVals.append('"'+sPart1+'" with "'+sPart2+'"')
                        else:
                            aVals.append('"'+name+'"')
                    else:
                        if name!='X':
                            aVals.append(name)
                        else:
                            aVals.append('-1')
                if aVals!=[]:
                    oFilterPart.node.setValues(aVals)
            elif type(child) is gtk.Entry:
                sText=child.get_text()
                if sText!='':
                    oFilterPart.node.setValues(['"'+sText+'"'])
        return oNewAST

    def __makeScrolledList(self,sName,aVals):
        oWidget=ScrolledList(sName)
        oWidget.set_size_request(160,420)
        aList=oWidget.get_list()
        aList.clear()
        for sEntry in aVals:
            iter=aList.append(None)
            aList.set(iter,0,sEntry)
        return oWidget

    def __doComplaint(self,sMessage):
        oComplaint=gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
                gtk.BUTTONS_CLOSE,sMessage)
        oComplaint.run()
        oComplaint.destroy()

    def __doAddFilter(self):
        oNewFilterDialog=gtk.Dialog("Enter the New Filter",self,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                ( gtk.STOCK_OK, gtk.RESPONSE_OK,
                    gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL ) )
        oEntry=gtk.Entry(300)
        oEntry.set_width_chars(70)
        oNewFilterDialog.vbox.pack_start(oEntry)
        oNewFilterDialog.show_all()
        response=oNewFilterDialog.run()
        if response==gtk.RESPONSE_OK:
            sFilter=oEntry.get_text()
            try:
                oAST=self.__oParser.apply(sFilter)
            except ValueError:
                self.__doComplaint("Invalid Filter Syntax: "+sFilter)
                oNewFilterDialog.destroy()
                return
            self.__addFilterToDialog(oAST,sFilter)
            self.__oConfig.addFilter(sFilter)
            self.__aFilterList.append(sFilter)
            self.show_all()
        oNewFilterDialog.destroy()
