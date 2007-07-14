# FilterDialog.py
# Dialog for setting Filter Parameters
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.Filters import MultiClanFilter, MultiDisciplineFilter,\
                           MultiCardTypeFilter, MultiExpansionFilter,\
                           MultiGroupFilter, CardNameFilter, CardTextFilter,\
                           FilterAndBox
from sutekh.SutekhObjects import Clan, Discipline, CardType, Expansion,\
                                 DisciplineAdapter
from sutekh.gui.ScrolledList import ScrolledList

class FilterDialog(gtk.Dialog):
    def __init__(self,parent):
        super(FilterDialog,self).__init__("Specify Filter", \
              parent,gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
              ( gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.set_default_size(800,450)
        self.wasCancelled = False
        self.State={}
        myHBox=gtk.HBox(False,0)
        oClanComment=gtk.Label("Any of these\nClans")
        oDiscComment=gtk.Label("Any of these\nDisciplines")
        oTypeComment=gtk.Label("Any of these\nCard Types")
        oExpComment=gtk.Label("Any of these\nExpansions")
        oGroupComment=gtk.Label("Any of these\nGroups")
        self.clanFrame=ScrolledList('Clans','All Clans')
        self.discFrame=ScrolledList('Disciplines','All Disciplines')
        self.typeFrame=ScrolledList('Card Types','All Types')
        self.expFrame=ScrolledList('Expansions','All Expansions')
        self.groupFrame=ScrolledList('Crypt Group','All Groups')
        textVBox=gtk.VBox(False,0)
        self.textFrame=gtk.Frame('Includes this Card Text')
        self.nameFrame=gtk.Frame('the Card Name includes')
        textVBox.pack_start(gtk.Label("AND"))
        textVBox.pack_start(oGroupComment)
        textVBox.pack_start(self.groupFrame)
        self.groupFrame.set_size_request(150,250)
        textVBox.pack_start(gtk.Label("AND"))
        textVBox.pack_start(self.nameFrame)
        textVBox.pack_start(gtk.Label("AND"))
        textVBox.pack_start(self.textFrame)
        tVBox=gtk.VBox(False,0)
        tVBox.pack_start(oClanComment)
        tVBox.pack_start(self.clanFrame)
        self.clanFrame.set_size_request(160,420)
        myHBox.pack_start(tVBox)
        tVBox=gtk.VBox(False,0)
        tVBox.pack_start(gtk.Label("AND"))
        tVBox.pack_start(oDiscComment)
        tVBox.pack_start(self.discFrame)
        self.discFrame.set_size_request(160,420)
        myHBox.pack_start(tVBox)
        tVBox=gtk.VBox(False,0)
        tVBox.pack_start(gtk.Label("AND"))
        tVBox.pack_start(oTypeComment)
        tVBox.pack_start(self.typeFrame)
        self.typeFrame.set_size_request(160,420)
        myHBox.pack_start(tVBox)
        tVBox=gtk.VBox(False,0)
        tVBox.pack_start(gtk.Label("AND"))
        tVBox.pack_start(oExpComment)
        tVBox.pack_start(self.expFrame)
        self.expFrame.set_size_request(160,420)
        myHBox.pack_start(tVBox)
        myHBox.pack_start(textVBox)
        self.State['clan']={}
        self.State['disc']={}
        self.State['type']={}
        self.State['exp']={}
        self.State['group']={}
        self.State['text']=''
        self.State['name']=''
        for clan in Clan.select().orderBy('name'):
            # Add clan to the list
            iter=self.clanFrame.get_list().append(None)
            self.clanFrame.get_list().set(iter,0,clan.name)
            self.State['clan'][clan.name]=False
        for discipline in Discipline.select().orderBy('name'):
            # add disciplie
            name=DisciplineAdapter.keys[discipline.name][-1]
            iter=self.discFrame.get_list().append(None)
            self.discFrame.get_list().set(iter,0,name)
            self.State['disc'][name]=False
        for type in CardType.select():
            iter=self.typeFrame.get_list().append(None)
            self.typeFrame.get_list().set(iter,0,type.name)
            self.State['type'][type.name]=False
        for exp in Expansion.select():
            iter=self.expFrame.get_list().append(None)
            self.expFrame.get_list().set(iter,0,exp.name)
            self.State['exp'][exp.name]=False
        for group in range(1,5+1):
            iter=self.groupFrame.get_list().append(None)
            self.groupFrame.get_list().set(iter,0,str(group))
            self.State['group'][str(group)]=False
        self.connect("response", self.buttonResponse)
        self.textEntry=gtk.Entry(100)
        self.textEntry.set_width_chars(20)
        self.textFrame.add(self.textEntry)
        self.nameEntry=gtk.Entry(100)
        self.nameEntry.set_width_chars(20)
        self.nameFrame.add(self.nameEntry)
        self.Data = None
        self.vbox.pack_end(myHBox)
        self.show_all()

    def getFilter(self):
        return self.Data

    def Cancelled(self):
        return self.wasCancelled

    def buttonResponse(self,widget,response):
       self.wasCancelled = False # Need to reset if filter is rerun
       andData=[]
       if response ==  gtk.RESPONSE_OK:
           aClans = []
           aDiscs = []
           aTypes = []
           aExps = []
           aGroups = []
           aText = []
           # Unset state
           for clanName in self.State['clan']:
               self.State['clan'][clanName]=False
           for discName in self.State['disc']:
               self.State['disc'][discName]=False
           for typeName in self.State['type']:
               self.State['type'][typeName]=False
           for expName in self.State['exp']:
               self.State['exp'][expName]=False
           for groupName in self.State['group']:
               self.State['group'][groupName]=False
           self.State['text']=''
           self.State['name']=''

           # Compile lists of clans and disciplines selected
           self.clanFrame.get_selection(aClans,self.State['clan'])
           if len(aClans) > 0:
               andData.append(MultiClanFilter(aClans))
           self.discFrame.get_selection(aDiscs,self.State['disc'])
           if len(aDiscs) > 0:
               andData.append(MultiDisciplineFilter(aDiscs))
           self.typeFrame.get_selection(aTypes,self.State['type'])
           if len(aTypes) > 0:
               andData.append(MultiCardTypeFilter(aTypes))
           self.expFrame.get_selection(aExps,self.State['exp'])
           if len(aExps) > 0:
               andData.append(MultiExpansionFilter(aExps))
           self.groupFrame.get_selection(aGroups,self.State['group'])
           if len(aGroups) > 0:
               andData.append(MultiGroupFilter([int(x) for x in aGroups]))

           # Add text lookup
           sCardText=self.textEntry.get_text()
           if sCardText!='':
               andData.append(CardTextFilter(sCardText))
               self.State['text']=sCardText

	   sPartialName=self.nameEntry.get_text()
           if sPartialName!='':
               andData.append(CardNameFilter(sPartialName))
               self.State['name']=sPartialName

           # Combine filters
           if len(andData)>1:
               self.Data = FilterAndBox(andData)
           elif len(andData)==1:
               self.Data=andData[0] # Avoid extra and
           else:
               self.Data = None
       else:
           self.clanFrame.reset(self.State['clan'])
           self.discFrame.reset(self.State['disc'])
           self.typeFrame.reset(self.State['type'])
           self.expFrame.reset(self.State['exp'])
           self.groupFrame.reset(self.State['group'])
           self.textEntry.set_text(self.State['text'])
           self.nameEntry.set_text(self.State['name'])
           self.wasCancelled = True
       self.hide()

