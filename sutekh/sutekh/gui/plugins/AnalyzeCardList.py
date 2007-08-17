# AnalyzeCardList.py
# Dialog to display deck analysis software
# Copyright 2006,2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.SutekhObjects import PhysicalCardSet, AbstractCardSet, PhysicalCard
from sutekh.Filters import CardTypeFilter
from sutekh.gui.PluginManager import CardListPlugin

class AnalyzeCardList(CardListPlugin):
    dTableVersions = {"PhysicalCardSet" : [3],
            "AbstractCardSet" : [3]}
    aModelsSupported = ["PhysicalCardSet","AbstractCardSet"]

    # Should this be defined in SutekhObjects??
    dTitleVoteMap = {
            'Primogen' : 1,
            'Prince' : 2,
            'Justicar' : 3,
            'Inner Circle' : 4,
            'Priscus' : 3,
            'Bishop' : 1,
            'Archbishop' : 2,
            'Cardinal' : 3,
            'Regent' : 4,
            'Independent with 1 vote' : 1,
            'Independent with 2 votes' : 2,
            'Independent with 3 votes' : 3,
            'Magaji' : 2,
            }

    def getMenuItem(self):
        """
        Overrides method from base class.
        """
        if not self.checkVersions() or not self.checkModelType():
            return None
        iAnalyze = gtk.MenuItem("Analyze Deck")
        iAnalyze.connect("activate", self.activate)
        return iAnalyze

    def getDesiredMenu(self):
        return "Plugins"

    def activate(self,oWidget):
        dlg = self.makeDialog()
        dlg.run()

    def makeDialog(self):
        parent = self.view.getWindow()
        name = "Analysis of Card List"
        deckName = self.view.sSetName
        if self.view.sSetType == 'PhysicalCardSet':
            oCS = PhysicalCardSet.byName(self.view.sSetName)
        else:
            oCS = AbstractCardSet.byName(self.view.sSetName)

        sComment = oCS.comment.replace('&','&amp;')
        sAuthor = oCS.author

        dlg = gtk.Dialog(name,parent,
                         gtk.DIALOG_DESTROY_WITH_PARENT,
                         (gtk.STOCK_OK, gtk.RESPONSE_OK))
        dlg.connect("response", lambda dlg, resp: dlg.destroy())
        oNotebook = gtk.Notebook()
        oMainLabel = gtk.Label()
        oMainLabel.set_line_wrap(True)
        oMainLabel.set_width_chars(60)
        oHappyFamiliesLabel = gtk.Label()
        oVampiresLabel = gtk.Label()
        oMastersLabel = gtk.Label()
        oCombatLabel = gtk.Label()

        oNotebook.append_page(oMainLabel,gtk.Label('Basic Info'));
        oNotebook.append_page(oHappyFamiliesLabel,gtk.Label('Happy Families Analysis'));
        oNotebook.append_page(oVampiresLabel,gtk.Label('Vampires'));
        oNotebook.append_page(oMastersLabel,gtk.Label('Master Cards'));
        oNotebook.append_page(oCombatLabel,gtk.Label('combat Cards'));

        sMainText = "Analysis Results for deck : <b>" + deckName + "</b>\nby <i>"+sAuthor+"</i>\n"+sComment+"\n"
        sVampText = "<b>Vampires :</b>\n"
        sMasterText = "<b>Master Cards :</b>\n"
        sHappyFamilyText = "<b>Happy Families Analysis :</b>\n"
        sCombatText = "<b>Combat Cards :</b>\n"

        self.iNumberUniqueVampires = 0
        self.iNumberMult = 0
        self.iMaxGroup = -500
        self.iMinGroup = 500
        self.dDeckVamps = {}
        self.dDeckClans = {}
        self.dDeckDisc = {}
        self.dDeckTitles = {}
        self.iVotes = 0
        self.iTotCapacity = 0
        self.dVampCapacity = {}
        self.iMinCapacity = 500
        self.iMaxCapacity = -500

        # Split out the card types of interest
        aAllCards = list(self.model.getCardIterator(None))
        aVampireCards = list(self.model.getCardIterator(CardTypeFilter('Vampire')))
        aCombatCards = list(self.model.getCardIterator(CardTypeFilter('Combat')))
        aReactionCards = list(self.model.getCardIterator(CardTypeFilter('Reaction')))
        aActionCards = list(self.model.getCardIterator(CardTypeFilter('Action')))
        aMasterCards = list(self.model.getCardIterator(CardTypeFilter('Master')))

        self.iNumberVampires = len(aVampireCards)
        self.iNumberCombats = len(aCombatCards)
        self.iNumberMasters = len(aMasterCards)
        self.iTotNumber = len(aAllCards)
        self.iNumberLibrary = self.iTotNumber - self.iNumberVampires

        for oCard in aVampireCards:
            if type(oCard) is PhysicalCard:
                self.processVampire(oCard.abstractCard)
            else:
                self.processVampire(oCard)

        for oCard in aMasterCards:
            if type(oCard) is PhysicalCard:
                self.processMaster(oCard.abstractCard)
            else:
                self.processMaster(oCard)

        for oCard in aCombatCards:
            if type(oCard) is PhysicalCard:
                self.processCombat(oCard.abstractCard)
            else:
                self.processCombat(oCard)

        sVampText += "<span foreground = \"blue\">Basic Crypt stats</span>\n"
        sMainText += "Number of Vampires = " + str(self.iNumberVampires) + "\n"
        sVampText += "Number of Vampires = " + str(self.iNumberVampires) + "\n"
        sMainText += "Number of Unique Vampires = " + str(self.iNumberUniqueVampires) + "\n"
        sVampText += "Number of Unique Vampires = " + str(self.iNumberUniqueVampires) + "\n"

        if self.iNumberVampires < 12:
            sMainText += "<span foreground = \"red\">Less than 12 Vampires</span>\n"
            sVampText += "<span foreground = \"red\">Less than 12 Vampires</span>\n"

        sVampText += "Minimum Group is : " + str(self.iMinGroup) + "\n"
        sVampText += "Maximum Group is : " + str(self.iMaxGroup) + "\n"

        if self.iMaxGroup - self.iMinGroup > 1:
            sMainText += "<span foreground = \"red\">Group Range Exceeded</span>\n"
            sVampText += "<span foreground = \"red\">Group Range Exceeded</span>\n"


        sVampText += "\n<span foreground = \"blue\">Crypt cost</span>\n"

        sVampText += "Cheapest is : " + str(self.iMinCapacity) + "\n"
        sVampText += "Most Expensive is : " + str(self.iMaxCapacity) + "\n"
        sVampText += "Average Capacity is : " + str(self.iTotCapacity/float(self.iNumberVampires)).ljust(5)[:5] + "\n\n"

        if self.iNumberVampires > 0:
            sVampText += "<span foreground = \"blue\">Clans</span>\n"
            for clan, number in self.dDeckClans.iteritems():
                sVampText += str(number) + " Vampires of clan " + str(clan) \
                           + " (" + str(number/float(self.iNumberVampires)*100).ljust(5)[:5] \
                           + " % of the crypt )\n"

            sVampText += "\n<span foreground = \"blue\">Titles</span>\n"
            iTitles = 0

            for title, number in self.dDeckTitles.iteritems():
                sVampText += str(number) + " vampires with the title " + str(title) \
                           + " (" + str(self.dTitleVoteMap[title]) + ") votes\n"
                iTitles += number

            sVampText += str(self.iVotes) + " votes in the crypt. Average votes per vampire is " \
                       + str(float(self.iVotes)/self.iNumberVampires).ljust(5)[:5] + "\n"

            sVampText += str(iTitles) + " titles in the crypt (" + \
                         str( iTitles/float(self.iNumberVampires)*100).ljust(5)[:5] + \
                         " % of the crypt )\n\n"

            sVampText += "<span foreground = \"blue\">Disciplines</span>\n"
            for discipline, number in sorted(self.dDeckDisc.iteritems()):
                # Maybe should sort this by number[0]?
                sVampText += str(number[0])+" Vampires with " + discipline \
                           + " (" + str(number[0]/float(self.iNumberVampires)*100).ljust(5)[:5] \
                           + "%), " + str(number[1]) + " at Superior (" \
                           + str(number[1]/float(self.iNumberVampires)*100).ljust(5)[:5] + " %)\n"

        sMainText += "Total Library Size            = " + str(self.iNumberLibrary) + "\n"

        if self.iNumberLibrary > 0:
            sMainText += "Number of Masters             = " + str(self.iNumberMasters) + " (" + str((self.iNumberMasters*100)/float(self.iNumberLibrary)).ljust(5)[:5] + "% of Library)\n"
            sMasterText += "Number of Masters             = " + str(self.iNumberMasters) + " (" + str((self.iNumberMasters*100)/float(self.iNumberLibrary)).ljust(5)[:5] +"% of Library)\n"

            sMainText += "Number of Combat cards        = " + str(self.iNumberCombats) + " (" + str((self.iNumberCombats*100)/float(self.iNumberLibrary)).ljust(5)[:5] + "% of Library)\n"
            sCombatText += "Number of Combat cards        = " + str(self.iNumberCombats) + " (" + str((self.iNumberCombats*100)/float(self.iNumberLibrary)).ljust(5)[:5] + "% of Library)\n"

        sMainText += "Number of Other Library Cards = " + str(self.iNumberLibrary - self.iNumberMasters - self.iNumberCombats) + "\n"
        sMainText += "Number of Multirole cards = " + str(self.iNumberMult) + "\n"

        print sMainText
        oMainLabel.set_markup(sMainText)
        oVampiresLabel.set_markup(sVampText)
        oMastersLabel.set_markup(sMasterText)
        oHappyFamiliesLabel.set_markup(sHappyFamilyText)
        oCombatLabel.set_markup(sCombatText)

        dlg.vbox.pack_start(oNotebook)
        dlg.show_all()

        return dlg

    def processVampire(self,oAbsCard):
        if oAbsCard.name not in self.dDeckVamps:
            self.iNumberUniqueVampires += 1
            self.dDeckVamps[oAbsCard.name] = 1
        else:
            self.dDeckVamps[oAbsCard.name] += 1

        self.iMaxGroup = max(self.iMaxGroup,oAbsCard.group)
        self.iMinGroup = min(self.iMinGroup,oAbsCard.group)

        self.iTotCapacity += oAbsCard.capacity

        self.iMaxCapacity = max(self.iMaxCapacity,oAbsCard.capacity)
        self.iMinCapacity = min(self.iMinCapacity,oAbsCard.capacity)

        self.dVampCapacity.setdefault(oAbsCard.capacity,0)
        self.dVampCapacity[oAbsCard.capacity] += 1

        for clan in oAbsCard.clan:
            if clan.name not in self.dDeckClans:
                self.dDeckClans[clan.name] = 1
            else:
                self.dDeckClans[clan.name] += 1

        for disc in oAbsCard.discipline:
            if disc.discipline.name in self.dDeckDisc:
                self.dDeckDisc[disc.discipline.name][0] += 1
            else:
                self.dDeckDisc[disc.discipline.name] = [1,0]

            if disc.level == 'superior':
                self.dDeckDisc[disc.discipline.name][1] += 1

        for title in oAbsCard.title:
            if title.name in self.dDeckTitles:
                self.dDeckTitles[title.name] += 1
            else:
                self.dDeckTitles[title.name] = 1

            self.iVotes+=self.dTitleVoteMap[title.name]

    def processMaster(self,oAbsCard):
        pass

    def processCombat(self,oAbsCard):
        pass

    def happyFamiliesAnalysis(self,oDeck):
        pass

plugin = AnalyzeCardList
