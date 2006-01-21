import gtk
from SutekhObjects import *

# GUI Classes

class AnalyzeDeckDialog(gtk.MessageDialog):
    def init(self,deckName):
        # Placeholder typ function here
        super(AnalyzeDeckDialog).__init__ \
              (None,0,gtk.MESSAGE_INFO,gtk.BUTTONS_CLOSE,None)
        self.connect("response", lambda dlg, resp: dlg.destroy())
        Deck=PhysicalCardSet.byName(deckName)
        text="Analysis Results for deck : <b>"+deckName+"</b>\n"
        self.NumberVampires=0
        self.NumberLibrary=0
        self.NumberMasters=0
        self.MaxGroup=-500
        self.MinGroup=500
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
        if self.NumberVampires<12:
            text=text+"<span foreground=\"red\">Less than 12 Vampires</span>\n"
        for clan,number in self.deckClans.iteritems():
            text=text+str(number)+" Vampires of clan " + clan + \ 
                  " (" + str(number/float(self.NumberVampires)*100).rjust[5][:5] + \
                  " % of the crypt )\n"
        for discpline,number in sorted(self.deckDisc.iteritems()):
            # Maybe should sort this by number[0]?
            text=text+str(number[0])+" Vampires with " + discipline + \
                  ",  (" + str(number[0]/float(self.NumberVampires)*100)[:5] +
                  "%) " + str(number[1]) + " at Superior (" + \
                  str(number[1]/float(self.NumberVampires)*100)[:5] + " %)\n"
        text=text+"Number of Masters             = "+str(self.NumberMasters)+"\n"
        text=text+"Number of Other Library Cards = "+str(self.NumberLibrary-self.NumberMasters)+"\n"
        AnalyzeWindow.set_markup(text)
        AnalyzeWindow.run()

    def processVampire(self,absCard):
        self.NumberVampires+=1
        if absCard.group>self.MaxGroup:
            self.MaxGroup=absCard.group
        if absCard.group<self.MinGroup:
            self.MinGroup=absCard.group
        if absCard.clan not in self.deckClans:
            self.deckClans[absCard.clan]=1
        else:
            self.deckClans[absCard.clan]+=1
        for disc in absCard.discipline:
            if disc.name in self.deckDisc:
                self.deckDisc[disc.name][0]+=1
            else:
                self.deckDisc[disc.name]=[1,0]
            if disc.level == 'superior':
                self.deckDisc[disc.name][1]+=1

    def processMaster(self,absCard):
        self.NumberMasters+=1
