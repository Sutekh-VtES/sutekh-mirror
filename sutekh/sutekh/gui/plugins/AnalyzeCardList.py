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
        # Oh, popup_enable and scrollable - how I adore thee
        oNotebook.set_scrollable(True)
        oNotebook.popup_enable()

        oMainLabel = gtk.Label()
        oMainLabel.set_line_wrap(True)
        oMainLabel.set_width_chars(60)
        oHappyFamiliesLabel = gtk.Label()
        oVampiresLabel = gtk.Label()
        oImbuedLabel = gtk.Label()
        oMastersLabel = gtk.Label()
        oCombatLabel = gtk.Label()
        oActionsLabel = gtk.Label()
        oActModLabel = gtk.Label()
        oActModLabel = gtk.Label()
        oRetainersLabel = gtk.Label()
        oAlliesLabel = gtk.Label()
        oEventsLabel = gtk.Label()
        oPowConvLabel = gtk.Label()
        oReactionLabel = gtk.Label()

        oNotebook.append_page(oMainLabel,gtk.Label('Basic Info'));
        oNotebook.append_page(oHappyFamiliesLabel,gtk.Label('Happy Families Analysis'));
        oNotebook.append_page(oVampiresLabel,gtk.Label('Vampires'));
        oNotebook.append_page(oAlliesLabel,gtk.Label('Allies'));
        oNotebook.append_page(oMastersLabel,gtk.Label('Master Cards'));
        oNotebook.append_page(oCombatLabel,gtk.Label('Combat Cards'));
        oNotebook.append_page(oActionsLabel,gtk.Label('Actions'));
        oNotebook.append_page(oActModLabel,gtk.Label('Action Modifiers'));
        oNotebook.append_page(oReactionLabel,gtk.Label('Reactions'));
        oNotebook.append_page(oRetainersLabel,gtk.Label('Retainers and Equipment'));
        oNotebook.append_page(oEventsLabel,gtk.Label('Events'));
        oNotebook.append_page(oImbuedLabel,gtk.Label('Imbued'));
        oNotebook.append_page(oPowConvLabel,gtk.Label('Powers and Convictions'));

        sMainText = "Analysis Results for deck : <b>" + deckName + "</b>\nby <i>"+sAuthor+"</i>\n"+sComment+"\n"

        self.iMaxGroup = -500
        self.iMinGroup = 500
        self.iNumberMult = 0

        # Split out the card types of interest
        aAllCards = list(self.model.getCardIterator(None))
        self.iTotNumber = len(aAllCards)
        # Split the cards by type
        aVampireCards = list(self.model.getCardIterator(CardTypeFilter('Vampire')))
        self.iNumberVampires = len(aVampireCards)
        aImbuedCards = list(self.model.getCardIterator(CardTypeFilter('Imbued')))
        self.iNumberImbued = len(aImbuedCards)
        aCombatCards = list(self.model.getCardIterator(CardTypeFilter('Combat')))
        self.iNumberCombats = len(aCombatCards)
        aReactionCards = list(self.model.getCardIterator(CardTypeFilter('Reaction')))
        self.iNumberReaction = len(aReactionCards)
        aActionCards = list(self.model.getCardIterator(CardTypeFilter('Action')))
        self.iNumberAction = len(aActionCards)
        aActModCards = list(self.model.getCardIterator(CardTypeFilter('Action Modifier')))
        self.iNumberActMod = len(aActModCards)
        aRetainerCards = list(self.model.getCardIterator(CardTypeFilter('Retainer')))
        self.iNumberRetainers = len(aRetainerCards)
        aAlliesCards = list(self.model.getCardIterator(CardTypeFilter('Ally')))
        self.iNumberAllies = len(aAlliesCards)
        aEquipCards = list(self.model.getCardIterator(CardTypeFilter('Equipment')))
        self.iNumberEquipment = len(aEquipCards)
        aPoliticsCards = list(self.model.getCardIterator(CardTypeFilter('Political Action')))
        self.iNumberPolitics = len(aPoliticsCards)
        aPowerCards = list(self.model.getCardIterator(CardTypeFilter('Power')))
        self.iNumberPower = len(aPowerCards)
        aConvictionCards = list(self.model.getCardIterator(CardTypeFilter('Conviction')))
        self.iNumberConviction = len(aConvictionCards)
        aEventCards = list(self.model.getCardIterator(CardTypeFilter('Event')))
        self.iNumberEvents = len(aEventCards)
        aMasterCards = list(self.model.getCardIterator(CardTypeFilter('Master')))
        self.iNumberMasters = len(aMasterCards)

        self.iNumberLibrary = self.iTotNumber - self.iNumberVampires - self.iNumberImbued

        oVampiresLabel.set_markup(self.processVampire(aVampireCards))
        oImbuedLabel.set_markup(self.processImbued(aImbuedCards))
        oMastersLabel.set_markup(self.processMaster(aMasterCards))
        oCombatLabel.set_markup(self.processCombat(aCombatCards))

        oHappyFamiliesLabel.set_markup(self.happyFamiliesAnalysis(aAllCards))

        # Set main notebook text

        sMainText += "Number of Vampires = " + str(self.iNumberVampires) + "\n"
        sMainText += "Number of Imbued = " + str(self.iNumberImbued) + "\n"
        sMainText += "Minimum Group in Crpyt = " + str(self.iMinGroup) + "\n"
        sMainText += "Maximum Group in Crypt = " + str(self.iMaxGroup) + "\n"

        if (self.iNumberVampires + self.iNumberImbued) < 12:
            sMainText += "<span foreground = \"red\">Less than 12 Crypt Cards</span>\n"

        if self.iMaxGroup - self.iMinGroup > 1:
            sMainText += "<span foreground = \"red\">Group Range Exceeded</span>\n"

        sMainText += "Total Library Size = " + str(self.iNumberLibrary) + "\n"

        if self.iNumberLibrary > 0:
            sMainText += "Number of Masters = " + \
                    str(self.iNumberMasters) + " (" + \
                    str((self.iNumberMasters*100)/
                            float(self.iNumberLibrary)).ljust(5)[:5] + \
                    "% of Library)\n"
            sMainText += "Number of Combat cards = " + \
                    str(self.iNumberCombats) + " (" + \
                    str((self.iNumberCombats*100)/
                            float(self.iNumberLibrary)).ljust(5)[:5] + \
                    "% of Library)\n"
            sMainText += "Number of Action cards = " + \
                    str(self.iNumberAction) + " (" + \
                    str((self.iNumberAction*100)/
                            float(self.iNumberLibrary)).ljust(5)[:5] + \
                    "% of Library)\n"
            sMainText += "Number of Action Modifiers = " + \
                    str(self.iNumberActMod) + " (" + \
                    str((self.iNumberActMod*100)/
                            float(self.iNumberLibrary)).ljust(5)[:5] + \
                    "% of Library)\n"
            sMainText += "Number of Reaction cards = " + \
                    str(self.iNumberReaction) + " (" + \
                    str((self.iNumberReaction*100) /
                            float(self.iNumberLibrary)).ljust(5)[:5] + \
                    "% of Library)\n"
            sMainText += "Number of Allies = " + \
                    str(self.iNumberAllies) + " (" + \
                    str((self.iNumberAllies*100) /
                            float(self.iNumberLibrary)).ljust(5)[:5] + \
                    "% of Library)\n"
            sMainText += "Number of Retainers = " + \
                    str(self.iNumberRetainers) + " (" + \
                    str((self.iNumberRetainers*100) /
                            float(self.iNumberLibrary)).ljust(5)[:5] + \
                    "% of Library)\n"
            sMainText += "Number of Equipment cards = " + \
                    str(self.iNumberEquipment) + " (" + \
                    str((self.iNumberEquipment*100)/
                            float(self.iNumberLibrary)).ljust(5)[:5] + \
                    "% of Library)\n"
            sMainText += "Number of Event cards = " + \
                    str(self.iNumberEvents) + " (" + \
                    str((self.iNumberEvents*100)/
                            float(self.iNumberLibrary)).ljust(5)[:5] + \
                    "% of Library)\n"
            sMainText += "Number of Convictions = " + \
                    str(self.iNumberConviction) + " (" + \
                    str((self.iNumberConviction*100)/
                            float(self.iNumberLibrary)).ljust(5)[:5] + \
                    "% of Library)\n"
            sMainText += "Number of Powers = " + \
                    str(self.iNumberPower) + " (" + \
                    str((self.iNumberPower*100)/
                            float(self.iNumberLibrary)).ljust(5)[:5] + \
                    "% of Library)\n"

        sMainText += "Number of Multirole cards = " + \
                str(self.iNumberMult) + " (" + \
                str((self.iNumberMult*100)/
                        float(self.iNumberLibrary)).ljust(5)[:5] + \
                "% of Library)\n"

        oMainLabel.set_markup(sMainText)

        dlg.vbox.pack_start(oNotebook)
        dlg.show_all()

        return dlg

    def processVampire(self,aCards):

        dDeckVamps = {}
        dVampCapacity = {}
        dDeckTitles = {}
        dDeckClans = {}
        dDeckDisc = {}

        iTotCapacity = 0
        iNumberUniqueVampires = 0
        iMaxCapacity = -500
        iMinCapacity = 500
        iVampMinGroup = 500
        iVampMaxGroup = -500
        iVotes = 0
        iTitles = 0

        for oCard in aCards:
            if type(oCard) is PhysicalCard:
                oAbsCard = oCard.abstractCard
            else:
                oAbsCard = oCard

            if oAbsCard.name not in dDeckVamps:
                iNumberUniqueVampires += 1
                dDeckVamps[oAbsCard.name] = 1
            else:
                dDeckVamps[oAbsCard.name] += 1

            self.iMaxGroup = max(self.iMaxGroup,oAbsCard.group)
            self.iMinGroup = min(self.iMinGroup,oAbsCard.group)
            iVampMaxGroup = max(iVampMaxGroup,oAbsCard.group)
            iVampMinGroup = min(iVampMinGroup,oAbsCard.group)

            iTotCapacity += oAbsCard.capacity
            iMaxCapacity = max(iMaxCapacity,oAbsCard.capacity)
            iMinCapacity = min(iMinCapacity,oAbsCard.capacity)

            dVampCapacity.setdefault(oAbsCard.capacity,0)
            dVampCapacity[oAbsCard.capacity] += 1

            for clan in oAbsCard.clan:
                if clan.name not in dDeckClans:
                    dDeckClans[clan.name] = 1
                else:
                    dDeckClans[clan.name] += 1

            for disc in oAbsCard.discipline:
                if disc.discipline.name in dDeckDisc:
                    dDeckDisc[disc.discipline.name][0] += 1
                else:
                    dDeckDisc[disc.discipline.name] = [1,0]

                if disc.level == 'superior':
                    dDeckDisc[disc.discipline.name][1] += 1

            for title in oAbsCard.title:
                iTitles += 1
                if title.name in dDeckTitles:
                    dDeckTitles[title.name] += 1
                else:
                    dDeckTitles[title.name] = 1

                iVotes+=self.dTitleVoteMap[title.name]

        # Build up Text
        sVampText = "<b>Vampires :</b>\n"
        sVampText += "<span foreground = \"blue\">Basic Crypt stats</span>\n"
        sVampText += "Number of Vampires = " + str(self.iNumberVampires) + "\n"
        sVampText += "Number of Unique Vampires = " + str(iNumberUniqueVampires) + "\n"

        if self.iNumberVampires > 0:
            sVampText += "Minimum Group is : " + str(iVampMinGroup) + "\n"
            sVampText += "Maximum Group is : " + str(iVampMaxGroup) + "\n"

            sVampText += "\n<span foreground = \"blue\">Crypt cost</span>\n"
            sVampText += "Cheapest is : " + str(iMinCapacity) + "\n"
            sVampText += "Most Expensive is : " + str(iMaxCapacity) + "\n"
            sVampText += "Average Capacity is : " + str(iTotCapacity / float(self.iNumberVampires)).ljust(5)[:5] + "\n\n"

            sVampText += "<span foreground = \"blue\">Clans</span>\n"
            for clan, number in dDeckClans.iteritems():
                sVampText += str(number) + " Vampires of clan " + str(clan) \
                           + " (" + str(number / float(self.iNumberVampires)*100).ljust(5)[:5] \
                           + " % of the crypt )\n"

            sVampText += "\n<span foreground = \"blue\">Titles</span>\n"

            for title, number in dDeckTitles.iteritems():
                sVampText += str(number) + " vampires with the title " + str(title) \
                           + " (" + str(self.dTitleVoteMap[title]) + ") votes\n"

            sVampText += str(iVotes) + " votes in the crypt. Average votes per vampire is " \
                       + str(float(iVotes)/self.iNumberVampires).ljust(5)[:5] + "\n"

            sVampText += str(iTitles) + " titles in the crypt (" + \
                         str(iTitles / float(self.iNumberVampires)*100).ljust(5)[:5] + \
                         " % of the crypt )\n\n"

            sVampText += "<span foreground = \"blue\">Disciplines</span>\n"
            for discipline, number in sorted(dDeckDisc.iteritems()):
                # Maybe should sort this by number[0]?
                sVampText += str(number[0])+" Vampires with " + discipline \
                           + " (" + str(number[0] / float(self.iNumberVampires)*100).ljust(5)[:5] \
                           + "%), " + str(number[1]) + " at Superior (" \
                           + str(number[1] / float(self.iNumberVampires)*100).ljust(5)[:5] + " %)\n"

        return sVampText

    def processMaster(self,aCards):
        for oCard in aCards:
            if type(oCard) is PhysicalCard:
                oAbsCard = oCard.abstractCard
            else:
                oAbsCard = oCard

        # Build up Text
        sMasterText = "<b>Master Cards :</b>\n"
        sMasterText += "Number of Masters = " + str(self.iNumberMasters) + " (" + str((self.iNumberMasters*100) / float(self.iNumberLibrary)).ljust(5)[:5] +"% of Library)\n"
        return sMasterText

    def processCombat(self,aCards):
        for oCard in aCards:
            if type(oCard) is PhysicalCard:
                oAbsCard = oCard.abstractCard
            else:
                oAbsCard = oCard

        # Build up Text
        sCombatText = "<b>Combat Cards :</b>\n"
        sCombatText += "Number of Combat cards = " + str(self.iNumberCombats) + " (" + str((self.iNumberCombats*100) / float(self.iNumberLibrary)).ljust(5)[:5] + "% of Library)\n"
        return sCombatText

    def processImbued(self,aCards):
        dDeckImbued = {}

        iMaxLife = -500
        iMinLife = 500
        iTotLife = 0
        iImbMinGroup = 500
        iImbMaxGroup = -500
        iNumberUniqueImbued = 0

        for oCard in aCards:
            if type(oCard) is PhysicalCard:
                oAbsCard = oCard.abstractCard
            else:
                oAbsCard = oCard

            if oAbsCard.name not in dDeckImbued:
                iNumberUniqueImbued += 1
                dDeckImbued[oAbsCard.name] = 1
            else:
                dDeckImbued[oAbsCard.name] += 1

            self.iMaxGroup = max(self.iMaxGroup,oAbsCard.group)
            self.iMinGroup = min(self.iMinGroup,oAbsCard.group)
            iImbMaxGroup = max(iImbMaxGroup,oAbsCard.group)
            iImbMinGroup = min(iImbMinGroup,oAbsCard.group)

            iTotLife += oAbsCard.life
            iMaxLife = max(iMaxLife,oAbsCard.life)
            iMinLife = min(iMinLife,oAbsCard.life)

        # Build up Text
        sImbuedText = "<b>Imbued</b>\n"
        sImbuedText += "<span foreground = \"blue\">Basic Crypt stats</span>\n"
        sImbuedText += "Number of Imbued = " + str(self.iNumberImbued) + "\n"
        sImbuedText += "Number of Uniueq Imbued = " + str(iNumberUniqueImbued) + "\n"
        if self.iNumberImbued > 0:
            sImbuedText += "Minimum Group is : " + str(iImbMinGroup) + "\n"
            sImbuedText += "Maximum Group is : " + str(iImbMaxGroup) + "\n"

            sImbuedText += "\n<span foreground = \"blue\">Crypt cost</span>\n"

            sImbuedText += "Cheapest is : " + str(iMinLife) + "\n"
            sImbuedText += "Most Expensive is : " + str(iMaxLife) + "\n"
            sImbuedText += "Average Life is : " + str(iTotLife / float(self.iNumberImbued)).ljust(5)[:5] + "\n\n"

        return sImbuedText

    def happyFamiliesAnalysis(self,aAllCards):
        for oCard in aAllCards:
            if type(oCard) is PhysicalCard:
                oAbsCard = oCard.abstractCard
            else:
                oAbsCard = oCard

            aTypes = [x.name for x in oAbsCard.cardtype]
            if len(aTypes)>1:
                # Since we examining all the cards, do this here
                self.iNumberMult += 1

        # Build up Text
        sHappyFamilyText = "<b>Happy Families Analysis :</b>\n"
        return sHappyFamilyText

plugin = AnalyzeCardList
