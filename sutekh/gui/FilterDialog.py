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

    AddButtonResponse = 1
    DeleteButtonResponse = 2

    def __init__(self,parent):
        super(FilterDialog,self).__init__("Specify Filter", \
                parent,gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        # Need to add these buttons so we get the right order
        self.add_button( "Add New Filter", self.AddButtonResponse)
        # Want a reference to this button, so we can fiddle active state
        self.oDeleteButton = self.add_button("Delete Filter",\
                self.DeleteButtonResponse)
        self.action_area.pack_start(gtk.VSeparator(),expand=True)
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.oDeleteButton.set_sensitive(False)
        self.oParser=FilterParser.FilterParser()
        self.connect("response", self.buttonResponse)
        self.dExpanded={}
        self.dASTs={}
        self.dButtons={}
        self.set_default_size(700,550)
        self.Data = None
        self.wasCancelled = False
        self.oRadioGroup=None
        oFrame=gtk.Frame("Current Filter to Edit")
        oFrame.set_size_request(700,430)
        self.oExpandedArea=gtk.HBox(spacing=5)
        oFrame.add(self.oExpandedArea)
        self.oRadioArea=gtk.VBox()
        self.sExpanded=None
        self.vbox.pack_start(oFrame)
        self.vbox.pack_start(self.oRadioArea)
        self.vbox.set_homogeneous(False)
        self.aFilterList=aDefaultFilterList
        # First filter is expanded by default
        for sFilter in self.aFilterList:
            # Parse the filter into the seperate bits needed
            try:
                oAST=self.oParser.apply(sFilter)
            except ValueError:
                self.__doComplaint("Invalid Filter Syntax: "+sFilter)
                continue
            self.__addFilterToDialog(oAST,sFilter)
        self.__expandFilter(self.oRadioGroup, "0 : "+self.aFilterList[0],0)
        self.show_all()

    def __expandFilter(self, oRadioButton, sName, iNum):
        """When the user selects a radio button, expand
           the options"""
        if sName!=self.sExpanded:
            # Remove the previous filter
            for child in self.oExpandedArea.get_children():
                self.oExpandedArea.remove(child)
            self.sExpanded=sName
            for child in self.dExpanded[sName]:
                self.oExpandedArea.pack_start(child,expand=False)
            self.oExpandedArea.show_all()
            if iNum>=len(aDefaultFilterList):
                # User defined filter, can be deleted
                self.oDeleteButton.set_sensitive(True)
            else:
                self.oDeleteButton.set_sensitive(False)

    def __addFilterToDialog(self,oAST,sFilter):
        aFilterParts=oAST.getValues()
        iNum=len(self.dExpanded)
        # Should we try harder to make sure this is unique?
        # do .... while sName in dExpanded.keys() type construction?
        sName=str(iNum)+" : "+sFilter
        self.dExpanded[sName]=[]
        self.dASTs[sName]=oAST
        for oPart in aFilterParts:
            if oPart.isValue():
                oWidget=gtk.Label(oPart.value)
                self.dExpanded[sName].append(oWidget)
            elif oPart.isList():
                oWidget=self.__makeScrolledList(sPrevName,oPart.value)
                self.dExpanded[sName].append(oWidget)
            elif oPart.isEntry():
                oWidget=gtk.Entry(100)
                oWidget.set_width_chars(30)
                self.dExpanded[sName].append(oWidget)
            sPrevName=oPart.value
        oRadioButton=gtk.RadioButton(self.oRadioGroup)
        if self.oRadioGroup is None:
            self.oRadioGroup=oRadioButton
        oRadioButton.set_label(sFilter)
        self.dButtons[sName]=oRadioButton
        oRadioButton.connect("clicked",self.__expandFilter,sName, iNum)
        self.oRadioArea.pack_start(oRadioButton)

    def getFilter(self):
        return self.Data

    def Cancelled(self):
        return self.wasCancelled

    def buttonResponse(self,widget,response):
        if response ==  gtk.RESPONSE_OK:
            self.wasCancelled=False
            # Construct the Final filter string
            oNewAST=self.__parseDialogState()
            # Push this into yacc and get the constructed filter out of
            # it
            self.Data=oNewAST.getFilter()
        elif response == self.AddButtonResponse:
            self.doAddFilter()
            # Recursive, not sure if that's such a good thing
            return self.run()
        elif response == self.DeleteButtonResponse:
            self.__doComplaint("Delete not yet implemented")
            return self.run()
        else:
            self.wasCancelled=True
        self.hide()

    def __parseDialogState(self):
        # FIXME: Should be defined somewhere else for better maintainability
        aNumericFilters=['Group','Cost','Capacity','Life']
        aWithFilters=['Expansion_with_Rarity','Discipline_with_Level']
        oNewAST=copy.deepcopy(self.dASTs[self.sExpanded])
        aNewFilterValues=oNewAST.getValues()
        # Need pointers to the new nodes
        for (child,oFilterPart) in zip(self.dExpanded[self.sExpanded],aNewFilterValues):
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

    def doAddFilter(self):
        oNewFilterDialog=gtk.Dialog("Enter the New Filter",self,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                ( gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL ) )
        oEntry=gtk.Entry(300)
        oEntry.set_width_chars(70)
        oNewFilterDialog.vbox.pack_start(oEntry)
        oNewFilterDialog.show_all()
        response=oNewFilterDialog.run()
        if response==gtk.RESPONSE_OK:
            sFilter=oEntry.get_text()
            try:
                oAST=self.oParser.apply(sFilter)
            except ValueError:
                self.__doComplaint("Invalid Filter Syntax: "+sFilter)
                oNewFilterDialog.destroy()
                return
            self.__addFilterToDialog(oAST,sFilter)
            self.show_all()
        oNewFilterDialog.destroy()
