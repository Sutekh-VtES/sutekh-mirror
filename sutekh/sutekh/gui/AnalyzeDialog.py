import gtk
from SutekhObjects import *

# GUI Classes
#              #parent,gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \

class AnalyzeDialog(gtk.Dialog):
    def __init__(self,parent,deckName):
        super(AnalyzeDialog,self).__init__("Analysis for deck " + deckName, \
              parent,gtk.DIALOG_DESTROY_WITH_PARENT, \
              (gtk.STOCK_OK, gtk.RESPONSE_OK))
        self.connect("response", lambda dlg, resp: dlg.destroy())
        Label=gtk.Label()
        Deck=PhysicalCardSet.byName(deckName)
        text="Analysis Results for deck : <b>"+deckName+"</b>\n"
        self.NumberVampires=0
        self.NumberUniqueVampires=0
        self.NumberLibrary=0
        self.NumberMasters=0
        self.MaxGroup=-500
        self.MinGroup=500
        self.deckVamps={}
        self.deckClans={}
        self.deckDisc={}
        for card in Deck.cards:
            thisAbsCard=card.abstractCard
            for cardType in thisAbsCard.cardtype:
                if cardType.name=="Vampire":
                    self.processVampire(thisAbsCard)
                else:
                    self.NumberLibrary+=1    
                if cardType.name=="Master":
                    self.processMaster(thisAbsCard)
        text=text+"Number of Vampires = "+str(self.NumberVampires)+"\n"
        text=text+"Number of Unique Vampires = "+str(self.NumberUniqueVampires)+"\n"
        if self.NumberVampires<12:
            text=text+"<span foreground=\"red\">Less than 12 Vampires</span>\n"
        for clan,number in self.deckClans.iteritems():
            text=text+str(number)+" Vampires of clan " + str(clan) + \
                  " (" + str(number/float(self.NumberVampires)*100).ljust(5)[:5] + \
                  " % of the crypt )\n"
        for discipline,number in sorted(self.deckDisc.iteritems()):
            # Maybe should sort this by number[0]?
            text=text+str(number[0])+" Vampires with " + discipline + \
                  " (" + str(number[0]/float(self.NumberVampires)*100).ljust(5)[:5] + \
                  "%), " + str(number[1]) + " at Superior (" + \
                  str(number[1]/float(self.NumberVampires)*100).ljust(5)[:5] + " %)\n"
        text=text+"Number of Masters             = "+str(self.NumberMasters)+"\n"
        text=text+"Number of Other Library Cards = "+str(self.NumberLibrary-self.NumberMasters)+"\n"
        Label.set_markup(text)
        self.vbox.pack_start(Label)
        self.show_all()

    def processVampire(self,absCard):
        self.NumberVampires+=1
        if absCard.name not in self.deckVamps:
            self.NumberUniqueVampires+=1
            self.deckVamps[absCard.name]=1
        else:
            self.deckVamps[absCard.name]+=1
        if absCard.group>self.MaxGroup:
            self.MaxGroup=absCard.group
        if absCard.group<self.MinGroup:
            self.MinGroup=absCard.group
        for clan in absCard.clan:
            if clan.name not in self.deckClans:
                self.deckClans[clan.name]=1
            else:
                self.deckClans[clan.name]+=1
        for disc in absCard.discipline:
            if disc.discipline.name in self.deckDisc:
                self.deckDisc[disc.discipline.name][0]+=1
            else:
                self.deckDisc[disc.discipline.name]=[1,0]
            if disc.level == 'superior':
                self.deckDisc[disc.discipline.name][1]+=1

    def processMaster(self,absCard):
        self.NumberMasters+=1
