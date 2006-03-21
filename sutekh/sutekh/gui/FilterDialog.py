# Dialog for setting Filter Parameters
import gtk, gobject
from Filters import *
from SutekhObjects import *
from AutoScrolledWindow import AutoScrolledWindow

class InternalScroll(gtk.Frame):
    def __init__(self,title):
        super(InternalScroll,self).__init__(None)
        self.List=gtk.ListStore(gobject.TYPE_STRING)
        self.TreeView=gtk.TreeView(self.List)
        self.TreeView.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        myScroll=AutoScrolledWindow(self.TreeView)
        self.add(myScroll)
        oCell1=gtk.CellRendererText()
        oColumn=gtk.TreeViewColumn(title,oCell1,text=0)
        self.List.append(None) # Create empty items at top of list
        self.TreeView.append_column(oColumn)
        self.set_shadow_type(gtk.SHADOW_NONE)
        self.show_all()

    def get_list(self):
        return self.List

    def get_view(self):
        return self.TreeView

    def reset(self,State):
        Model=self.TreeView.get_model()
        oIter=Model.get_iter_first()
        while oIter != None:
           name=Model.get_value(oIter,0)
           if name != None and State[name]:
               self.TreeView.get_selection().select_iter(oIter)
           else:
               self.TreeView.get_selection().unselect_iter(oIter)
           oIter=Model.iter_next(oIter)

    def get_selection(self,selList,State):
        Model,Selection = self.TreeView.get_selection().get_selected_rows()
        for oPath in Selection:
            oIter = Model.get_iter(oPath)
            name = Model.get_value(oIter,0)
            if name!=None:
               State[name]=True
               selList.append(name)



class FilterDialog(gtk.Dialog):
    def __init__(self,parent):
        super(FilterDialog,self).__init__("Specify Filter", \
              parent,gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
              ( gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.set_default_size(400,200)
        self.wasCancelled = False
        self.State={}
        myHBox=gtk.HBox(False,0)
        self.clanFrame=InternalScroll('Clans')
        self.discFrame=InternalScroll('Disciplines')
        self.typeFrame=InternalScroll('Card Types')
        self.textFrame=gtk.Frame('Card Text')
        myHBox.pack_start(self.clanFrame)
        myHBox.pack_start(self.discFrame)
        myHBox.pack_start(self.typeFrame)
        myHBox.pack_start(self.textFrame)
        self.State['clan']={}
        self.State['disc']={}
        self.State['type']={}
        self.State['text']=''
        for clan in Clan.select().orderBy('name'):
            # Add clan to the list
            iter=self.clanFrame.get_list().append(None)
            self.clanFrame.get_list().set(iter,0,clan.name)
            self.State['clan'][clan.name]=False
        for discipline in Discipline.select().orderBy('name'):
            # add disciplie
            name=DisciplineAdapter.keys[discipline.name][1]
            iter=self.discFrame.get_list().append(None)
            self.discFrame.get_list().set(iter,0,name)
            self.State['disc'][name]=False
        for type in CardType.select():
            iter=self.typeFrame.get_list().append(None)
            self.typeFrame.get_list().set(iter,0,type.name)
            self.State['type'][type.name]=False
        self.connect("response", self.buttonResponse)
        self.textEntry=gtk.Entry(100)
        self.textFrame.add(self.textEntry)
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
           aText = []
           # Unset state
           for clanName in self.State['clan']:
               self.State['clan'][clanName]=False
           for discName in self.State['disc']:
               self.State['disc'][discName]=False
           for typeName in self.State['type']:
               self.State['type'][typeName]=False
           self.State['text']=''

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

           # Add text lookup			   
           aText=self.textEntry.get_text()
           if aText!='':
               andData.append(CardTextFilter(aText))
               self.State['text']=aText

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
           self.textEntry.set_text(self.State['text'])
           self.wasCancelled = True
       self.hide()

