# Dialog for setting Filter Parameters
import gtk
from Filters import *
from SutekhObjects import *
        
class FilterDialog(gtk.Dialog):
    def __init__(self,parent):
        super(FilterDialog,self).__init__("Specify Filter", \
              parent,gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
              ( gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.wasCancelled = False
        myHBox=gtk.HBox(False,0)
        clanFrame=gtk.Frame('Clans to Filter on')
        discFrame=gtk.Frame('Disciplines to Filter on')
        myHBox.pack_end(clanFrame)
        myHBox.pack_end(discFrame)
        clanHBox=gtk.HBox(False,0)
        discHBox=gtk.HBox(False,0)
        clanFrame.add(clanHBox)
        discFrame.add(discHBox)
        vBox1={}
        vBox2={}
        vBox1[0]=gtk.VButtonBox() # Clans
        vBox1[1]=gtk.VButtonBox() # Clans
        vBox1[2]=gtk.VButtonBox() # Clans
        vBox2[0]=gtk.VButtonBox() # Discplines
        vBox2[1]=gtk.VButtonBox() # Discplines
        vBox2[2]=gtk.VButtonBox() # Discplines
        clanHBox.pack_start(vBox1[0])
        clanHBox.pack_start(vBox1[1])
        clanHBox.pack_start(vBox1[2])
        discHBox.pack_start(vBox2[0])
        discHBox.pack_start(vBox2[1])
        discHBox.pack_start(vBox2[2])
        self.vbox.pack_start(myHBox)
        self.clanCheckBoxes={}
        self.discCheckBoxes={}
        i=0
        for clan in Clan.select().orderBy('name'):
            # Add clan to the list
            self.clanCheckBoxes[clan.name] = gtk.CheckButton(clan.name)
            self.clanCheckBoxes[clan.name].set_active(False)
            vBox1[i].add(self.clanCheckBoxes[clan.name])
            i=i+1
            if (i>2):
                i=0
        i=0
        for discipline in Discipline.select().orderBy('name'):
            # add disciplie
            name=DisciplineAdapter.keys[discipline.name][1]
            self.discCheckBoxes[name]= gtk.CheckButton(name)
            self.discCheckBoxes[name].set_active(False)
            vBox2[i].add(self.discCheckBoxes[name])
            i=i+1
            if (i>2):
                i=0
        self.connect("response", self.buttonResponse)
        self.Data = None
        self.show_all()

    def getFilter(self):
        return self.Data

    def Cancelled(self):
        return self.wasCancelled

    def run(self):
        self.oldClanState={}
        self.oldDiscState={}
        for clanButton in self.clanCheckBoxes:
            if self.clanCheckBoxes[clanButton].get_active():
                self.oldClanState[clanButton]=True
            else:
                self.oldClanState[clanButton]=False
        for discButton in self.discCheckBoxes:
            if self.discCheckBoxes[discButton].get_active():
                self.oldDiscState[discButton]=True
            else:
                self.oldDiscState[discButton]=False
        return super(FilterDialog,self).run()


    def buttonResponse(self,widget,response):
       self.wasCancelled = False # Need to reset if filter is rerun
       if response ==  gtk.RESPONSE_OK:
           aClans = []
           aDiscs = []
       
           # Compile lists of clans and disciplines selected
           for clanButton in self.clanCheckBoxes:
               if self.clanCheckBoxes[clanButton].get_active():
                   aClans.append(clanButton)
           for discButton in self.discCheckBoxes:
               if self.discCheckBoxes[discButton].get_active():
                   aDiscs.append(discButton)
                   
           # Create Filters for all Selected Clans and Disciplines
           if len(aClans)>0 and len(aDiscs)>0:
               self.data = FilterAndBox([MultiClanFilter(aClans),
                                         MultiDisciplineFilter(aDiscs)])
           elif len(aClans) > 0:
               self.Data = MultiClanFilter(aClans)
           elif len(aDiscs) > 0:
               self.Data = MultiDisciplineFilter(aDiscs)
           else:
               self.Data = None
       else:
           print "restoring state"
           for clanButton in self.clanCheckBoxes:
               if self.oldClanState[clanButton]:
                   self.clanCheckBoxes[clanButton].set_active(True)
               else:
                   self.clanCheckBoxes[clanButton].set_active(False)
           for discButton in self.discCheckBoxes:
               if self.oldDiscState[discButton]:
                   self.discCheckBoxes[discButton].set_active(True)
               else:
                   self.discCheckBoxes[discButton].set_active(False)
           self.wasCancelled = True
               
       self.hide()

