# Dialog for setting Filter Parameters
import gtk
from Filters import *
from SutekhObjects import *
        
class FilterDialog(gtk.Dialog):
    def __init__(self,parent):
        super(FilterDialog,self).__init__("Specify Filter", \
              parent,gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
              ( gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
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
        clanHBox.pack_end(vBox1[0])
        clanHBox.pack_end(vBox1[1])
        clanHBox.pack_end(vBox1[2])
        discHBox.pack_end(vBox2[0])
        discHBox.pack_end(vBox2[1])
        discHBox.pack_end(vBox2[2])
        self.vbox.pack_start(myHBox)
        self.clanCheckBoxes={}
        self.discCheckBoxes={}
        i=0
        for clan in Clan.select():
            # Add clan to the list
            self.clanCheckBoxes[clan.name] = gtk.CheckButton(clan.name)
            self.clanCheckBoxes[clan.name].set_active(False)
            vBox1[i].add(self.clanCheckBoxes[clan.name])
            i=i+1
            if (i>2):
                i=0
        i=0
        for discipline in Discipline.select():
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

    def buttonResponse(self,widget,response):
       if response ==  gtk.RESPONSE_OK:
           ClanFilters=[]
           DiscFilters=[]
           # Create Clan Filters for all Selected Clans
           for clanButton in self.clanCheckBoxes:
               if self.clanCheckBoxes[clanButton].get_active():
                   ClanFilters.append(ClanFilter(clanButton))
           for discButton in self.discCheckBoxes:
               if self.discCheckBoxes[discButton].get_active():
                   DiscFilters.append(DisciplineFilter(discButton))
           # Create Discipline Filters for all Selected Disciplines
           if len(ClanFilters) > 0:
               cF=FilterOrBox(ClanFilters)
               self.Data=cF
           if len(DiscFilters) > 0:
               dF=FilterOrBox(DiscFilters)
               self.Data=dF
           if len(DiscFilters)>0 and len(ClanFilters)>0:
               self.Data = FilterAndBox([cF,dF])
       self.destroy()

