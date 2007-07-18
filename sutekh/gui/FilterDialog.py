# FilterDialog.py
# Dialog for setting Filter Parameters
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk
import copy
from sutekh.gui.ScrolledList import ScrolledList
from sutekh import FilterParser

aFilterList = [
        "Clan IN $foo",
        "Discipline in $foo",
        "CardType in $foo && Clan in $bar",
        "CardType in $a AND Discipline in $b",
        "CardText in $a",
        "CardName in $name",
        "CardType in \"Vampire\" && Clan in $a && Group in $b",
        "CardType=\"Vampire\" && Discipline = $b && Group = $c",
        "CardType=\"Vampire\" && Discipline=\"Presence\",\"Dominate\" && Capacity = $cap",
        "CardType IN \"Imbued\" AND ( Creed = $a OR Virtue = $b )",
        "CardType in \"Vampire\" AND Discipline_with_Level = $foo",
        "Expansion_with_Rarity = $foo",
        "CardType = \"Action\" && Cost = $cost"
        ]

class FilterDialog(gtk.Dialog):
    def __init__(self,parent):
        super(FilterDialog,self).__init__("Specify Filter", \
              parent,gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
              ( "Add New Filter", 1, gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL ))
        self.oParser=FilterParser.FilterParser()
        self.connect("response", self.buttonResponse)
        self.dExpanded={}
        self.dASTs={}
        self.dButtons={}
        self.set_default_size(800,450)
        self.Data = None
        self.wasCancelled = False
        self.oRadioGroup=None
        self.oExpandedArea=gtk.HBox()
        self.oRadioArea=gtk.VBox()
        self.sExpanded=None
        self.vbox.pack_start(self.oExpandedArea)
        self.vbox.pack_start(self.oRadioArea)
        for sFilter in aFilterList:
            # Parse the filter into the seperate bits needed 
            try:
                oAST=self.oParser.apply(sFilter)
            except ValueError:
                self.__doComplaint("Invalid Filter Syntax: "+sFilter)
                continue
            if self.oRadioGroup is None:
                # First filter is expanded by default
                sToExpand=sFilter
            self.__addFilterToDialog(oAST,sFilter)
        self.__expandFilter(self.oRadioGroup, sToExpand)
        self.show_all()

    def __expandFilter(self, oRadioButton, sButtonName):
        """When the user selects a radio button, expand
           the options"""
        if sButtonName!=self.sExpanded:
            # Remove the previous filter 
            for child in self.oExpandedArea.get_children():
                self.oExpandedArea.remove(child)
            self.sExpanded=sButtonName
            for child in self.dExpanded[sButtonName]:
                self.oExpandedArea.pack_start(child)
            self.oExpandedArea.show_all()

    def __addFilterToDialog(self,oAST,sFilter):
        aFilterParts=oAST.getValues()
        self.dExpanded[sFilter]=[]
        self.dASTs[sFilter]=oAST
        for oPart in aFilterParts:
            if oPart.isValue():
                oWidget=gtk.Label(oPart.value)
                self.dExpanded[sFilter].append(oWidget)
            elif oPart.isList():
                oWidget=self.__makeScrolledList(sPrevName,oPart.value)
                self.dExpanded[sFilter].append(oWidget)
            elif oPart.isEntry():
                oWidget=gtk.Entry(100)
                oWidget.set_width_chars(30)
                self.dExpanded[sFilter].append(oWidget)
            sPrevName=oPart.value
        oRadioButton=gtk.RadioButton(self.oRadioGroup)
        if self.oRadioGroup is None:
            self.oRadioGroup=oRadioButton
        oRadioButton.set_label(sFilter)
        self.dButtons[sFilter]=oRadioButton
        oRadioButton.connect("clicked",self.__expandFilter,sFilter)
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
       elif response == 1:
           self.doAddFilter()
           # Recursive, not sure if that's such a good thing
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
