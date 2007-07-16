# FilterDialog.py
# Dialog for setting Filter Parameters
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.gui.ScrolledList import ScrolledList
from sutekh import FilterParser

aFilterList = [
        "Clan IN $foo",
        "Discipline in $foo",
        "CardType in $foo && Clan in $bar",
        "CardType in $a AND Discipline in $b",
        "CardText in $a",
        "CardName in $name",
        "CardType in \"Vampire\" and ( Clan in $a or Discipline in $b)",
        "CardType in \"Vampire\" && Clan in $a && Group in $b",
        "CardType=\"Vampire\" && Discipline = $b && Group = $c",
        "CardType=\"Vampire\" && Discipline = $a && Capacity = $b",
        "CardType=\"Vampire\" && Sect=\"Sabbat\" && Title = $title",
        "CardType=\"Vampire\" && Discipline=\"Presence\",\"Dominate\" && Capacity = $cap",
        "CardType IN \"Imbued\" AND ( Creed = $a OR Virtue = $b )",
        "CardType = \"Action\" && Cost = $cost"
        ]

class FilterDialog(gtk.Dialog):
    def __init__(self,parent):
        super(FilterDialog,self).__init__("Specify Filter", \
              parent,gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
              ( gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.oParser=FilterParser.FilterParser()
        self.connect("response", self.buttonResponse)
        self.dExpanded={}
        self.dButtons={}
        self.set_default_size(800,450)
        self.Data = None
        self.wasCancelled = False
        oRadioGroup=None
        self.oExpandedArea=gtk.HBox()
        oRadioArea=gtk.VBox()
        self.sExpanded=None
        self.vbox.pack_start(self.oExpandedArea)
        self.vbox.pack_start(oRadioArea,)
        for sFilter in aFilterList:
            # Parse the filter into the seperate bits needed 
            try:
                oAST=self.oParser.apply(sFilter)
            except ValueError:
                self.__doComplaint("Invalid Filter Syntax: "+sFilter)
                continue
            aFilterParts=oAST.getValues()
            self.dExpanded[sFilter]=[]
            for oPart in aFilterParts:
                if type(oPart) is str:
                    oWidget=gtk.Label(oPart)
                    self.dExpanded[sFilter].append((oWidget,oPart))
                elif type(oPart) is list:
                    oWidget=self.__makeScrolledList(oPrevPart,oPart)
                    self.dExpanded[sFilter].append((oWidget,None))
                elif oPart is None:
                    oWidget=gtk.Entry(100)
                    oWidget.set_width_chars(30)
                    self.dExpanded[sFilter].append((oWidget,None))
                oPrevPart=oPart
            oRadioButton=gtk.RadioButton(oRadioGroup)
            if oRadioGroup is None:
                oRadioGroup=oRadioButton
                # First filter is expanded by default
                sToExpand=sFilter
            oRadioButton.set_label(sFilter)
            self.dButtons[sFilter]=oRadioButton
            oRadioButton.connect("clicked",self.__expandFilter,sFilter)
            oRadioArea.pack_start(oRadioButton)
        self.__expandFilter(oRadioButton, sToExpand)
        self.show_all()

    def __expandFilter(self, oRadioButton, sButtonName):
        """When the user selects a radio button, expand
           the options"""
        if sButtonName!=self.sExpanded:
            # Remove the previous filter 
            for child in self.oExpandedArea.get_children():
                self.oExpandedArea.remove(child)
            self.sExpanded=sButtonName
            for child,sFilterPart in self.dExpanded[sButtonName]:
                self.oExpandedArea.pack_start(child)
            self.oExpandedArea.show_all()

    def getFilter(self):
        return self.Data

    def Cancelled(self):
        return self.wasCancelled

    def buttonResponse(self,widget,response):
       if response ==  gtk.RESPONSE_OK:
           self.wasCancelled=False
           # Construct the Final filter string
           sFinalFilter=self.__parseDialogState()
           # Push this into yacc and get the constructed filter out of
           # it
           oAST=self.oParser.apply(sFinalFilter)
           self.Data=oAST.getFilter()
       else:
           self.wasCancelled=True
       self.hide()

    def __parseDialogState(self):
        # Ug, messier than I would like
        sResult=''
        for child,sFilterPart in self.dExpanded[self.sExpanded]:
           if type(child) is ScrolledList:
               # Some of this logic should be pushed down to ScrolledList
               sString=''
               Model,Selection=child.TreeView.get_selection().get_selected_rows()
               for oPath in Selection:
                   oIter= Model.get_iter(oPath)
                   name = Model.get_value(oIter,0)
                   if sFilterPart not in ['Group','Cost','Capacity','Life']:
                       sString+='"'+name+'"'+','
                   else:
                       if name!='X':
                           sString+=name+','
                       else:
                           sString+='-1,'
               if sString!='':
                   # Trim trailing comma
                   sResult+=sString[:-1]+' '
               else:
                   sResult+='$foo '
           elif type(child) is gtk.Entry:
               sText=child.get_text()
               if sText!='':
                   sResult+='"'+sText+'" '
               else:
                   sResult+='$foo '
           else:
               sResult+=sFilterPart+' '
        return sResult

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
