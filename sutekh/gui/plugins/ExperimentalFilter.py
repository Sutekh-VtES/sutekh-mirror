# ExperimentalFilter.py
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test case for the proposed modified Filter approach."""

import gtk
from sutekh.gui.PluginManager import CardListPlugin
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
        "CardType= Action && Cost= $cost"
        ]

class ExpFilter(CardListPlugin):
    dTableVersions = {"PhysicalCardSet" : [3],
            "AbstractCardSet" : [3],
            "PhysicalCard" : [2] }
    aModelsSupported = ["PhysicalCardSet","AbstractCardSet",\
            "PhysicalCard","AbstractCard"]
    def __init__(self,*args,**kws):
        super(ExpFilter,self).__init__(*args,**kws)
        self.oDlg=None

    def getMenuItem(self):
        """
        Overrides method from base class.
        """
        if not self.checkVersions() or not self.checkModelType():
            return None
        iDF = gtk.MenuItem("Experimental Filter")
        iDF.connect("activate", self.activate)
        return iDF

    def getDesiredMenu(self):
        return "Filter"

    def activate(self,oWidget):
        if self.oDlg is None:
            self.makeDialog()
            self.oDlg.run()
        else:
            self.oDlg.show()

    def makeDialog(self):
        self.dExpanded={}
        self.dButtons={}
        parent = self.view.getWindow()

        self.oDlg = gtk.Dialog("Experimental Filter",parent,
                          gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                          (gtk.STOCK_OK, gtk.RESPONSE_OK,
                           gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.oDlg.connect("response", self.handleResponse)
        oRadioGroup=None
        self.oExpandedArea=gtk.HBox()
        oRadioArea=gtk.VBox()
        self.sExpanded=None
        self.oDlg.vbox.pack_start(self.oExpandedArea)
        self.oDlg.vbox.pack_start(oRadioArea,)
        oParser=FilterParser.DialogFilterParser()
        oFParser=FilterParser.FinalFilterParser()
        for sFilter in aFilterList:
            # Parse the filter into the seperate bits needed 
            self.dExpanded[sFilter]=oParser.apply(sFilter)
            oAST=oFParser.apply(sFilter)
            oRadioButton=gtk.RadioButton(oRadioGroup)
            if oRadioGroup is None:
                oRadioGroup=oRadioButton
                # First filter is expanded by default
                sToExpand=sFilter
            oRadioButton.set_label(sFilter)
            self.dButtons[sFilter]=oRadioButton
            oRadioButton.connect("clicked",self.expandFilter,sFilter)
            oRadioArea.pack_start(oRadioButton)
        self.expandFilter(oRadioButton, sToExpand)
        self.oDlg.show_all()

    def expandFilter(self, oRadioButton, sButtonName):
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

    def handleResponse(self,oWidget,oResponse):
       if oResponse ==  gtk.RESPONSE_OK:
           # Construct the Final filter string
           sFinalFilter=self.parseDialogState()
           #if sFinalFilter is None:
           #    return
           print sFinalFilter
           # Push this into yacc and get the constructed filter out of
           # it
           oParser=FilterParser.FinalFilterParser()
           res=oParser.apply(sFinalFilter)
           if res is None:
               return
           # Needs error checking, and shouldn't kludge setting filter like
           # this
           self.model.selectfilter=res
           self.view.runFilter(True)
           # Run the filter
           self.view.load()

       self.oDlg.hide()

    def parseDialogState(self):
        # Ug, messier than I would like
        sResult=''
        for child,sFilterPart in self.dExpanded[self.sExpanded]:
           if type(child) is ScrolledList:
               # Some of this logic should be pushed down to ScrolledList
               sString=sFilterPart+'='
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
               if sString[-1]!='=':
                   sResult+=sString[:-1]+' '
               else:
                   sResult+=sString[:-1]+'= $foo'
                   #self.Complain()
                   #return None
           elif type(child) is gtk.Entry:
               sText=child.get_text()
               if sText!='':
                   sResult+=sFilterPart+'="'+sText+'"'+' '
               else:
                   sResult+=sFilterPart+'= $foo'
                   #self.Complain()
                   #return None
           else:
               sResult+=sFilterPart+' '
        return sResult

    def Complain(self):
        print "Complaining bitterly"

plugin = ExpFilter
