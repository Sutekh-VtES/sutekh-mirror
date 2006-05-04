# AnalyzeDeck.py
# Dialog to display deck analysis software
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk
from SutekhObjects import *
from Filters import *

class AnalyzeDialog(gtk.Dialog):
    def __init__(self,parent,deckName):
        super(AnalyzeDialog,self).__init__("Analysis for deck " + deckName, \
              parent,gtk.DIALOG_DESTROY_WITH_PARENT, \
              (gtk.STOCK_OK, gtk.RESPONSE_OK))
        self.connect("response", lambda dlg, resp: dlg.destroy())
        Notebook=gtk.Notebook()
        self.MainLabel=gtk.Label()
        self.HappyFamiliesLabel=gtk.Label()
        self.VampiresLabel=gtk.Label()
        self.MastersLabel=gtk.Label()
        self.CombatLabel=gtk.Label()
        Notebook.append_page(self.MainLabel,gtk.Label('Basic Info'));
        Notebook.append_page(self.HappyFamiliesLabel,gtk.Label('Happy Families Analysis'));
        Notebook.append_page(self.VampiresLabel,gtk.Label('Vampires'));
        Notebook.append_page(self.MastersLabel,gtk.Label('Master Cards'));
        Notebook.append_page(self.CombatLabel,gtk.Label('combat Cards'));
        Deck=list(PhysicalCardSet.byName(deckName).cards)
        mainText="Analysis Results for deck : <b>"+deckName+"</b>\n"
        vampText="Vampies :\n"
        masterText="Master Cards :\n"
        happyFamilyText="Happy Families Analysis :\n"
        combatText="Combat Cards :\n"
        self.NumberUniqueVampires=0
        self.NumberMult=0
        self.NumberMasters=0
        self.MaxGroup=-500
        self.MinGroup=500
        self.deckVamps={}
        self.deckClans={}
        self.deckDisc={}
        # Split out the card types of interest
        Filter=FilterAndBox([DeckFilter(deckName),CardTypeFilter('Vampire')])
        vampireCards=list(PhysicalCard.select(Filter.getExpression()))
        Filter=FilterAndBox([DeckFilter(deckName),CardTypeFilter('Combat')])
        combatCards=list(PhysicalCard.select(Filter.getExpression()))
        Filter=FilterAndBox([DeckFilter(deckName),CardTypeFilter('Reaction')])
        reactionCards=list(PhysicalCard.select(Filter.getExpression()))
        Filter=FilterAndBox([DeckFilter(deckName),CardTypeFilter('Action')])
        actionCards=list(PhysicalCard.select(Filter.getExpression()))
        Filter=FilterAndBox([DeckFilter(deckName),CardTypeFilter('Master')])
        masterCards=list(PhysicalCard.select(Filter.getExpression()))
        self.NumberVampires=len(vampireCards)
        self.TotNumber = len(Deck)
        self.NumberLibrary=self.TotNumber-self.NumberVampires
        for card in vampireCards:
            self.processVampire(card.abstractCard)
        mainText=mainText+"Number of Vampires = "+str(self.NumberVampires)+"\n"
        vampText=vampText+"Number of Vampires = "+str(self.NumberVampires)+"\n"
        mainText=mainText+"Number of Unique Vampires = "+str(self.NumberUniqueVampires)+"\n"
        vampText=vampText+"Number of Unique Vampires = "+str(self.NumberUniqueVampires)+"\n"
        if self.NumberVampires<12:
            mainText=mainText+"<span foreground=\"red\">Less than 12 Vampires</span>\n"
            vampText=vampText+"<span foreground=\"red\">Less than 12 Vampires</span>\n"
        vampText=vampText+"Minimum Group is : "+str(self.MinGroup)+"\n"
        vampText=vampText+"Maximum Group is : "+str(self.MaxGroup)+"\n"
        if self.MaxGroup-self.MinGroup>1:
            mainText=mainText+"<span foreground=\"red\">Group Range Exceeded</span>\n"
            vampText=vampText+"<span foreground=\"red\">Group Range Exceeded</span>\n"
        if self.NumberVampires>0:
            for clan,number in self.deckClans.iteritems():
                vampText=vampText+str(number)+" Vampires of clan " + str(clan) + \
                      " (" + str(number/float(self.NumberVampires)*100).ljust(5)[:5] + \
                      " % of the crypt )\n"
            for discipline,number in sorted(self.deckDisc.iteritems()):
                # Maybe should sort this by number[0]?
                vampText=vampText+str(number[0])+" Vampires with " + discipline + \
                      " (" + str(number[0]/float(self.NumberVampires)*100).ljust(5)[:5] + \
                      "%), " + str(number[1]) + " at Superior (" + \
                      str(number[1]/float(self.NumberVampires)*100).ljust(5)[:5] + " %)\n"
        mainText=mainText+"Total Library Size            = "+str(self.NumberLibrary)+"\n"
        if self.NumberLibrary>0:
            mainText=mainText+"Number of Masters             = "+str(self.NumberMasters)+" (" + str((self.NumberMasters*100)/float(self.NumberLibrary)).ljust(5)[:5] +"% of Library)\n"
            masterText=masterText+"Number of Masters             = "+str(self.NumberMasters)+" (" + str((self.NumberMasters*100)/float(self.NumberLibrary)).ljust(5)[:5] +"% of Library)\n"
        mainText=mainText+"Number of Other Library Cards = "+str(self.NumberLibrary-self.NumberMasters)+"\n"
        mainText=mainText+"Number of Multirole cards = "+str(self.NumberMult)+"\n"
        self.MainLabel.set_markup(mainText)
        self.VampiresLabel.set_markup(vampText)
        self.MastersLabel.set_markup(masterText)
        self.HappyFamiliesLabel.set_markup(happyFamilyText)
        self.CombatLabel.set_markup(combatText)
        self.vbox.pack_start(Notebook)
        self.show_all()

    def processVampire(self,absCard):
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
        pass

    def happyFamiliesAnalysis(self,deck):
        pass
