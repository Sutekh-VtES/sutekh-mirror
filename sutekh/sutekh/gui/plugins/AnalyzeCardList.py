# AnalyzeCardList.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Dialog to display deck analysis software
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>,
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details
"""
Display interesting statistics and properties of the card set
"""

import gtk
from sutekh.core.SutekhObjects import PhysicalCardSet, AbstractCardSet, IAbstractCard
from sutekh.core.Filters import CardTypeFilter
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import SutekhDialog
from sutekh.gui.MultiSelectComboBox import MultiSelectComboBox

class AnalyzeCardList(CardListPlugin):
    """
    Plugin to analyze card sets.
    Displays various interesting stats, and does
    a Happy Family analysis of the deck
    """
    dTableVersions = {PhysicalCardSet : [3, 4],
            AbstractCardSet : [3]}
    aModelsSupported = [PhysicalCardSet,
            AbstractCardSet]

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

    def _percentage(self, iNum, iTot, sDesc):
        "Utility function for calculating percentages"
        if iTot>0:
            fPrec = iNum/float(iTot)
        else:
            fPrec = 0.0
        return '<i>(%5.3f %% of %s)</i>' % (fPrec*100, sDesc)

    def _get_abstract_cards(self, aCards):
        "Get the asbtract cards given the list of names"
        return [IAbstractCard(x) for x in aCards]

    def _get_sort_key(self, x):
        "Ensure we sort on the right key"
        return x[1][0]

    def get_menu_item(self):
        """
        Overrides method from base class.
        """
        if not self.check_versions() or not self.check_model_type():
            return None
        iAnalyze = gtk.MenuItem("Analyze Deck")
        iAnalyze.connect("activate", self.activate)
        return iAnalyze

    def get_desired_menu(self):
        "Menu to associate with"
        return "Plugins"

    def activate(self, oWidget):
        "Run the plugin"
        dlg = self.make_dialog()
        dlg.run()

    def make_dialog(self):
        "Create the actual dialog, and populate it"
        name = "Analysis of Card List"
        deckName = self.view.sSetName
        oCS = self._cModelType.byName(self.view.sSetName)

        sComment = oCS.comment.replace('&', '&amp;')
        sAuthor = oCS.author

        dlg = SutekhDialog(name, self.parent,
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
        oVampiresLabel = gtk.Label()
        oImbuedLabel = gtk.Label()
        oMastersLabel = gtk.Label()
        oCombatLabel = gtk.Label()
        oActionsLabel = gtk.Label()
        oActModLabel = gtk.Label()
        oRetainersLabel = gtk.Label()
        oAlliesLabel = gtk.Label()
        oEventsLabel = gtk.Label()
        oPowersLabel = gtk.Label()
        oConvictionsLabel = gtk.Label()
        oReactionLabel = gtk.Label()
        oEquipmentLabel = gtk.Label()
        oPoliticalLabel = gtk.Label()
        oMultiLabel = gtk.Label()

        oHappyBox = gtk.VBox(False, 2)

        self.iMaxGroup = -500
        self.iMinGroup = 500
        self.iNumberMult = 0
        self.aMultiCards = []
        self.dCryptDisc = {}
        self.dDeckDisc = {}
        self.dLibDisc = {}
        self.dLibClan = {}

        # Split out the card types of interest
        aAllCards = list(self.model.getCardIterator(None))
        self.iTotNumber = len(aAllCards)
        # Split the cards by type
        # Crypt Cards
        aVampireCards = list(self.model.getCardIterator(CardTypeFilter('Vampire')))
        self.iNumberVampires = len(aVampireCards)
        aImbuedCards = list(self.model.getCardIterator(CardTypeFilter('Imbued')))
        self.iNumberImbued = len(aImbuedCards)
        self.iCryptSize = self.iNumberImbued + self.iNumberVampires

        oVampiresLabel.set_markup(self.process_vampire(aVampireCards))
        oImbuedLabel.set_markup(self.process_imbued(aImbuedCards))

        # Library Cards
        aCombatCards = list(self.model.getCardIterator(CardTypeFilter('Combat')))
        self.iNumberCombats = len(aCombatCards)
        aReactionCards = list(self.model.getCardIterator(CardTypeFilter('Reaction')))
        self.iNumberReactions = len(aReactionCards)
        aActionCards = list(self.model.getCardIterator(CardTypeFilter('Action')))
        self.iNumberActions = len(aActionCards)
        aActModCards = list(self.model.getCardIterator(CardTypeFilter('Action Modifier')))
        self.iNumberActMods = len(aActModCards)
        aRetainerCards = list(self.model.getCardIterator(CardTypeFilter('Retainer')))
        self.iNumberRetainers = len(aRetainerCards)
        aAlliesCards = list(self.model.getCardIterator(CardTypeFilter('Ally')))
        self.iNumberAllies = len(aAlliesCards)
        aEquipCards = list(self.model.getCardIterator(CardTypeFilter('Equipment')))
        self.iNumberEquipment = len(aEquipCards)
        aPoliticalCards = list(self.model.getCardIterator(CardTypeFilter('Political Action')))
        self.iNumberPoliticals = len(aPoliticalCards)
        aPowerCards = list(self.model.getCardIterator(CardTypeFilter('Power')))
        self.iNumberPowers = len(aPowerCards)
        aConvictionCards = list(self.model.getCardIterator(CardTypeFilter('Conviction')))
        self.iNumberConvictions = len(aConvictionCards)
        aEventCards = list(self.model.getCardIterator(CardTypeFilter('Event')))
        self.iNumberEvents = len(aEventCards)
        aMasterCards = list(self.model.getCardIterator(CardTypeFilter('Master')))
        self.iNumberMasters = len(aMasterCards)

        self.iNumberLibrary = self.iTotNumber - self.iNumberVampires \
                - self.iNumberImbued

        # Do happy family analysis, since that also does multi-card count
        self.happy_families_init(aAllCards, oHappyBox)

        # Set markup for all labels

        oCombatLabel.set_markup(self.process_combat(aCombatCards))
        oReactionLabel.set_markup(self.process_reaction(aReactionCards))
        oActModLabel.set_markup(self.process_action_modifier(aActModCards))
        oAlliesLabel.set_markup(self.process_allies(aAlliesCards))
        oEventsLabel.set_markup(self.process_event(aEventCards))
        oActionsLabel.set_markup(self.process_action(aActionCards))
        oPoliticalLabel.set_markup(self.process_political_action(aPoliticalCards))
        oRetainersLabel.set_markup(self.process_retainer(aRetainerCards))
        oEquipmentLabel.set_markup(self.process_equipment(aEquipCards))
        oPowersLabel.set_markup(self.process_power(aPowerCards))
        oConvictionsLabel.set_markup(self.process_conviction(aConvictionCards))
        oMastersLabel.set_markup(self.process_master(aMasterCards))
        oMultiLabel.set_markup(self.process_multi(self.aMultiCards))

        oMainBox = gtk.VBox(False, 2)

        oNotebook.append_page(oMainBox, gtk.Label('Basic Info'));
        oNotebook.append_page(oHappyBox, gtk.Label('Happy Families Analysis'));
        if self.iNumberVampires > 0:
            oNotebook.append_page(oVampiresLabel, gtk.Label('Vampires'));
        if self.iNumberAllies > 0:
            oNotebook.append_page(oAlliesLabel, gtk.Label('Allies'));
        if self.iNumberMasters > 0:
            oNotebook.append_page(oMastersLabel, gtk.Label('Master Cards'));
        if self.iNumberCombats > 0:
            oNotebook.append_page(oCombatLabel, gtk.Label('Combat Cards'));
        if self.iNumberActions > 0:
            oNotebook.append_page(oActionsLabel, gtk.Label('Actions'));
        if self.iNumberPoliticals > 0:
            oNotebook.append_page(oPoliticalLabel, gtk.Label('Political Actions'));
        if self.iNumberActMods > 0:
            oNotebook.append_page(oActModLabel, gtk.Label('Action Modifiers'));
        if self.iNumberReactions > 0:
            oNotebook.append_page(oReactionLabel, gtk.Label('Reactions'));
        if self.iNumberRetainers > 0:
            oNotebook.append_page(oRetainersLabel, gtk.Label('Retainers'))
        if self.iNumberEquipment > 0:
            oNotebook.append_page(oEquipmentLabel, gtk.Label('Equipment'));
        if self.iNumberImbued > 0:
            oNotebook.append_page(oImbuedLabel, gtk.Label('Imbued'));
        if self.iNumberPowers > 0:
            oNotebook.append_page(oPowersLabel, gtk.Label('Powers'));
        if self.iNumberConvictions > 0:
            oNotebook.append_page(oConvictionsLabel, gtk.Label('Convictions'));
        if self.iNumberEvents > 0:
            oNotebook.append_page(oEventsLabel, gtk.Label('Events'));
        if self.iNumberMult > 0:
            oNotebook.append_page(oMultiLabel, gtk.Label('Multi-Role Cards'));

        sMainText = "Analysis Results for deck : <b>" + deckName + "</b>\nby <i>"+sAuthor+"</i>\n"+sComment+"\n"

        # Set main notebook text

        sMainText += "Number of Vampires = " + str(self.iNumberVampires) + "\n"
        sMainText += "Number of Imbued = " + str(self.iNumberImbued) + "\n"
        sMainText += "Total Crypt size = " + str(self.iCryptSize) + "\n"
        sMainText += "Minimum Group in Crpyt = " + str(self.iMinGroup) + "\n"
        sMainText += "Maximum Group in Crypt = " + str(self.iMaxGroup) + "\n"

        if self.iCryptSize < 12:
            sMainText += "<span foreground = \"red\">Less than 12 Crypt Cards</span>\n"

        if self.iMaxGroup - self.iMinGroup > 1:
            sMainText += "<span foreground = \"red\">Group Range Exceeded</span>\n"

        sMainText += "Total Library Size = " + str(self.iNumberLibrary) + "\n"

        oMainBox.pack_start(oMainLabel)

        if self.iNumberLibrary > 0:
            oLibNotebook = gtk.Notebook()
            oMainBox.pack_start(oLibNotebook)

            oTypeLabel = gtk.Label()
            oDiscLabel = gtk.Label()
            oClanLabel = gtk.Label()

            oLibNotebook.append_page(oTypeLabel, gtk.Label('Card Types'));
            oLibNotebook.append_page(oDiscLabel, gtk.Label('Disciplines'));
            oLibNotebook.append_page(oClanLabel, gtk.Label('Clan Requirements'));

            # Stats by card type

            sTypeText = self._format_card_line('Action cards',
                    self.iNumberActions)
            sTypeText += self._format_card_line('Action Modifier cards',
                    self.iNumberActMods)
            sTypeText += self._format_card_line('Ally cards',
                    self.iNumberAllies)
            sTypeText += self._format_card_line('Combat cards',
                    self.iNumberCombats)
            sTypeText += self._format_card_line('Convictions cards',
                    self.iNumberConvictions)
            sTypeText += self._format_card_line('Equipment cards',
                    self.iNumberEquipment)
            sTypeText += self._format_card_line('Event cards',
                    self.iNumberEvents)
            sTypeText += self._format_card_line('Master cards',
                    self.iNumberMasters)
            sTypeText += self._format_card_line('Political Action cards',
                    self.iNumberPoliticals)
            sTypeText += self._format_card_line('Power cards',
                    self.iNumberPowers)
            sTypeText += self._format_card_line('Reaction cards',
                    self.iNumberReactions)
            sTypeText += self._format_card_line('Retainer cards',
                    self.iNumberRetainers) +'\n'

            sTypeText += self._format_card_line('Multirole cards',
                    self.iNumberMult)

            oTypeLabel.set_markup(sTypeText)

            # Stats by discipline

            sDiscText = self._format_card_line('Master cards',
                    self.iNumberMasters)
            sDiscText += self._format_card_line('non-master cards with No '
                    'discipline requirement', self.dLibDisc['No Discipline'])
            sDiscText += '\n'

            for sDisc in sorted(self.dLibDisc):
                iNum = self.dLibDisc[sDisc]
                if sDisc != 'No Discipline' and iNum > 0:
                    sDiscDesc = 'non-master cards with %s' % sDisc
                    sDiscText += self._format_card_line(sDiscDesc, iNum)

            oDiscLabel.set_markup(sDiscText)
            # Stats by clan requirement
            sClanText = self._format_card_line('cards with No clan '
                    'requirement', self.dLibClan['No Clan']) + '\n'

            for sClan in sorted(self.dLibClan):
                iNum = self.dLibClan[sClan]
                if sClan != 'No Clan' and iNum > 0:
                    sClanDesc = 'cards requiring %s' % sClan
                    sClanText += self._format_card_line(sClanDesc, iNum)

            oClanLabel.set_markup(sClanText)

        oMainLabel.set_markup(sMainText)

        dlg.vbox.pack_start(oNotebook)
        dlg.show_all()
        oNotebook.set_current_page(0)

        return dlg

    def _format_card_line(self, sString, iNum):
        """Format card lines for notebook"""
        sPer = self._percentage(iNum, self.iNumberLibrary, "Library")
        return "Number of %(type)s = %(num)d %(per)s\n" % {
                'type' : sString,
                'num' : iNum,
                'per' : sPer,
                }

    def _get_card_costs(self, aAbsCards):
        """
        Calculate the cost of the list of Abstract Cards
        Return lists of costs, for pool, blood and convictions
        Each list contains: Number with variable cost, Maximum Cost, Total Cost,
        Number of cards with a cost
        """
        dCosts = {}
        for sType in ['blood', 'pool', 'conviction']:
            dCosts.setdefault(sType, [0, 0, 0, 0])
        for oAbsCard in aAbsCards:
            if oAbsCard.cost is not None:
                dCosts[oAbsCard.costtype][3] += 1
                if oAbsCard.cost == -1:
                    dCosts[oAbsCard.costtype][0] += 1
                else:
                    iMaxCost = dCosts[oAbsCard.costtype][1]
                    dCosts[oAbsCard.costtype][1] = max(iMaxCost, oAbsCard.cost)
                    dCosts[oAbsCard.costtype][2] += oAbsCard.cost
        return dCosts['blood'], dCosts['pool'], dCosts['conviction']

    def _get_card_disciplines(self, aAbsCards):
        """
        Extract the set of disciplines and virtues from the cards
        """
        dDisciplines = {}
        dVirtues = {}
        iNoneCount = 0
        for oAbsCard in aAbsCards:
            if not len(oAbsCard.discipline) == 0:
                aThisDisc = [oP.discipline.fullname for oP in oAbsCard.discipline]
            else:
                aThisDisc = []
            if not len(oAbsCard.virtue) == 0:
                aThisVirtue = [oV.fullname for oV in oAbsCard.virtue]
            else:
                aThisVirtue = []
            for sDisc in aThisDisc:
                dDisciplines.setdefault(sDisc, 0)
                dDisciplines[sDisc] += 1
            for sVirtue in aThisVirtue:
                dVirtues.setdefault(sVirtue, 0)
                dVirtues[sVirtue] += 1
            if len(oAbsCard.discipline) == 0 and len(oAbsCard.virtue) == 0:
                iNoneCount += 1
        return dDisciplines, dVirtues, iNoneCount

    def _get_card_clan_multi(self, aAbsCards):
        """
        Extra the clan requirements and the multi discipline cards
        form the list of Abstract Cards
        """
        dClan = {}
        iClanRequirement = 0
        dMulti = {}

        for oAbsCard in aAbsCards:
            if not len(oAbsCard.clan) == 0:
                iClanRequirement += 1
                aClans = [x.name for x in oAbsCard.clan]
                for sClan in aClans:
                    dClan.setdefault(sClan, 0)
                    dClan[sClan] += 1
            aTypes = [x.name for x in oAbsCard.cardtype]
            if len(aTypes) > 1:
                sKey = "/".join(sorted(aTypes))
                dMulti.setdefault(sKey, 0)
                dMulti[sKey] += 1
        return iClanRequirement, dClan, dMulti

    def _format_cost_numbers(self, sCardType, sCostString, aCost, iNum):
        sVarPercent = self._percentage(aCost[0], iNum, '%s cards' % sCardType)
        sNumPercent = self._percentage(aCost[3], iNum, '%s cards' % sCardType)
        sText = "Most Expensive %(name)s Card  (%(type)s) = %(max)d\n" \
                "Cards with variable cost = %(var)d %(per)s\n" \
                "Cards with %(type)s cost = %(numcost)d %(percost)s\n" \
                "Average %(name)s card %(type)s cost = %(avg)5.3f\n" % {
                        'name' : sCardType,
                        'type' : sCostString,
                        'var' : aCost[0],
                        'per' : sVarPercent,
                        'max' : aCost[1],
                        'avg' : aCost[2] / float(iNum),
                        'numcost' : aCost[3],
                        'percost' : sNumPercent,
                        }
        return sText

    def _format_disciplines(self, sDiscType, dDisc, iNum):
        """
        Format the display of disciplines and virtues
        """
        sText = ''
        for sDisc, iNum in sorted(dDisc.items(), key=lambda x: x[1], reverse=True):
            sText += 'Number of cards requiring %s %s = %d\n' % (sDiscType, sDisc, iNum)
        return sText

    def _format_clan(self, sCardType, iClanRequirement, dClan, iNum):
        sText = ''
        if iClanRequirement > 0:
            sPer = self._percentage(iClanRequirement, iNum, 'Library')
            sText += "Number of %(type)s with a Clan requirement = %(num)d %(per)s\n" % {
                    'type' : sCardType,
                    'num' : iClanRequirement,
                    'per' : sPer,
                    }
            for sClan, iClanNum in sorted(dClan.items(), key=lambda x: x[1],
                    reverse=True):
                sPer = self._percentage(iClanNum, iNum, '%s cards' % sCardType)
                sText += 'Number of %(type)s requiring %(clan)s = %(num)d %(per)s\n' % {
                        'type' : sCardType,
                        'clan' : sClan,
                        'num' : iClanNum,
                        'per' : sPer,
                        }
        return sText

    def _format_multi(self, sCardType, dMulti, iNum):
        sText = ''
        if len(dMulti) > 0:
            for sType, iMulti in sorted(dMulti.items(), key=lambda x: x[1],
                    reverse=True):
                sPer = self._percentage(iMulti, iNum, '%s cards' % sCardType)
                sText += '%(num)d %(type)s cards are %(multitype)s cards %(per)s\n' % {
                        'num' : iMulti,
                        'type' : sCardType,
                        'multitype' : sType,
                        'per' : sPer,
                        }
        return sText

    def process_vampire(self, aCards):
        """Process the list of vampires"""
        dDeckVamps = {}
        dVampCapacity = {}
        dDeckTitles = {}
        dDeckClans = {}

        iTotCapacity = 0
        iNumberUniqueVampires = 0
        iMaxCapacity = -500
        iMinCapacity = 500
        iVampMinGroup = 500
        iVampMaxGroup = -500
        iVotes = 0
        iTitles = 0

        for oAbsCard in self._get_abstract_cards(aCards):
            if oAbsCard.name not in dDeckVamps:
                iNumberUniqueVampires += 1
                dDeckVamps[oAbsCard.name] = 1
            else:
                dDeckVamps[oAbsCard.name] += 1

            self.iMaxGroup = max(self.iMaxGroup, oAbsCard.group)
            self.iMinGroup = min(self.iMinGroup, oAbsCard.group)
            iVampMaxGroup = max(iVampMaxGroup, oAbsCard.group)
            iVampMinGroup = min(iVampMinGroup, oAbsCard.group)

            iTotCapacity += oAbsCard.capacity
            iMaxCapacity = max(iMaxCapacity, oAbsCard.capacity)
            iMinCapacity = min(iMinCapacity, oAbsCard.capacity)

            dVampCapacity.setdefault(oAbsCard.capacity, 0)
            dVampCapacity[oAbsCard.capacity] += 1

            for clan in oAbsCard.clan:
                if clan.name not in dDeckClans:
                    dDeckClans[clan.name] = 1
                else:
                    dDeckClans[clan.name] += 1

            for oDisc in oAbsCard.discipline:
                self.dDeckDisc.setdefault(oDisc.discipline.fullname, [0, 0])
                self.dDeckDisc[oDisc.discipline.fullname][0] += 1
                if oDisc.level == 'superior':
                    self.dDeckDisc[oDisc.discipline.fullname][1] += 1

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
        sVampText += "Number of Vampires = " + str(self.iNumberVampires) + \
                self._percentage(self.iNumberVampires, self.iCryptSize, "Crypt") + "\n"
        sVampText += "Number of Unique Vampires = " + str(iNumberUniqueVampires) + "\n"

        if self.iNumberVampires > 0:
            sVampText += "Minimum Group is : " + str(iVampMinGroup) + "\n"
            sVampText += "Maximum Group is : " + str(iVampMaxGroup) + "\n"

            sVampText += "\n<span foreground = \"blue\">Crypt cost</span>\n"
            sVampText += "Cheapest is : " + str(iMinCapacity) + "\n"
            sVampText += "Most Expensive is : " + str(iMaxCapacity) + "\n"
            sVampText += "Average Capacity is : " + str(iTotCapacity / \
                    float(self.iNumberVampires)).ljust(5)[:5] + "\n\n"

            sVampText += "<span foreground = \"blue\">Clans</span>\n"
            for clan, number in dDeckClans.iteritems():
                sVampText += str(number) + " Vampires of clan " + str(clan) + ' ' + \
                        self._percentage(number,
                            self.iCryptSize, "Crypt") + '\n'

            sVampText += "\n<span foreground = \"blue\">Titles</span>\n"

            for title, number in dDeckTitles.iteritems():
                sVampText += str(number) + " vampires with the title " + str(title) \
                           + " (" + str(self.dTitleVoteMap[title]) + ") votes\n"

            sVampText += str(iVotes) + " votes in the crypt. Average votes per vampire is " \
                       + str(iVotes / float(self.iNumberVampires)).ljust(5)[:5] + "\n"

            sVampText += str(iTitles) + " titles in the crypt " + \
                        self._percentage(iTitles,
                            self.iCryptSize, "Crypt") + '\n'

            sVampText += "<span foreground = \"blue\">Disciplines</span>\n"
            for discipline, number in sorted(self.dDeckDisc.iteritems(),
                    key=self._get_sort_key, reverse=True):
                sVampText += str(number[0])+" Vampires with " + discipline \
                           + ' ' + self._percentage(number[0],
                                   self.iCryptSize, "Crypt") + ", " \
                           + str(number[1]) + " at Superior " + \
                           self._percentage(number[1],
                                   self.iCryptSize, "Crypt") + '\n'
                self.dCryptDisc.setdefault(number[0], [])
                self.dCryptDisc[number[0]].append(discipline)

        return sVampText

    def process_master(self, aCards):
        aAbsCards = self._get_abstract_cards(aCards)
        aBlood, aPool, aConviction = self._get_card_costs(aAbsCards)

        iClanRequirement, dClan, dMulti = self._get_card_clan_multi(aAbsCards)

        # Build up Text
        sText = "<b>Master Cards :</b>\n"
        sText += "Number of Masters = " + str(self.iNumberMasters) + ' ' + \
                self._percentage(self.iNumberMasters,
                        self.iNumberLibrary, "Library") + '\n'
        if self.iNumberMasters > 0:
            sText += self._format_cost_numbers('Master', 'pool',
                    aPool, self.iNumberMasters)
            sText += self._format_clan('Master', iClanRequirement,
                    dClan, self.iNumberMasters)
            sText += self._format_multi('Master', dMulti, self.iNumberMasters)
        return sText

    def _default_text(self, aAbsCards, sType, iNum):
        aBlood, aPool, aConviction = self._get_card_costs(aAbsCards)
        iClanRequirement = 0
        dDisciplines, dVirtues, iNoneCount = \
                self._get_card_disciplines(aAbsCards)

        iClanRequirement, dClan, dMulti = self._get_card_clan_multi(aAbsCards)

        # Build up Text
        sPerCards = self._percentage(iNum, self.iNumberLibrary, 'Library')
        sText = "<b>%(type)s Cards :</b>\n" \
                "Number of %(type)s cards = %(num)d %(per)s\n" % {
                        'type' : sType,
                        'num' : iNum,
                        'per' : sPerCards
                        }
        if iNum > 0:
            if aBlood[1] > 0:
               sText += self._format_cost_numbers(sType, 'blood',
                       aBlood, iNum)
            if aConviction[1] > 0:
               sText += self._format_cost_numbers(sType, 'conviction',
                       aConviction, iNum)
            if aPool[1] > 0:
               sText += self._format_cost_numbers(sType, 'pool',
                       aPool, iNum)

            sText += self._format_clan(sType, iClanRequirement,
                    dClan, iNum)
            sText += 'Number of cards with no discipline/virtue requirement = %d\n' % iNoneCount
            if len(dDisciplines) > 0:
                sText += self._format_disciplines('discipline', dDisciplines, iNum)
            if len(dVirtues) > 0:
                sText += self._format_disciplines('virtue', dVirtues, iNum)
            sText += self._format_multi(sType, dMulti, iNum)
        return sText

    def process_combat(self, aCards):
        aAbsCards = self._get_abstract_cards(aCards)
        sText = self._default_text(aAbsCards, 'Combat', self.iNumberCombats)
        return sText

    def process_action_modifier(self, aCards):
        aAbsCards = self._get_abstract_cards(aCards)
        sText = self._default_text(aAbsCards, 'Action Modifier', self.iNumberActMods)
        return sText

    def process_reaction(self, aCards):
        aAbsCards = self._get_abstract_cards(aCards)
        sText = self._default_text(aAbsCards, 'Reaction', self.iNumberReactions)
        return sText

    def process_event(self, aCards):
        sEventText = "<b>Event Cards :</b>\n"
        sEventText += "Number of Event cards = " + str(self.iNumberEvents) + ' '+ \
                           self._percentage(self.iNumberEvents,
                                   self.iNumberLibrary, "Library") + '\n'
        return sEventText

    def process_action(self, aCards):
        aAbsCards = self._get_abstract_cards(aCards)
        sText = self._default_text(aAbsCards, 'Action', self.iNumberActions)
        return sText

    def process_political_action(self, aCards):
        aAbsCards = self._get_abstract_cards(aCards)
        sText = self._default_text(aAbsCards, 'Political Action', self.iNumberPoliticals)
        return sText

    def process_allies(self, aCards):
        aAbsCards = self._get_abstract_cards(aCards)
        sText = self._default_text(aAbsCards, 'Ally', self.iNumberAllies)
        return sText

    def process_retainer(self, aCards):
        aAbsCards = self._get_abstract_cards(aCards)
        sText = self._default_text(aAbsCards, 'Retainer', self.iNumberRetainers)
        return sText

    def process_equipment(self, aCards):
        aAbsCards = self._get_abstract_cards(aCards)
        sText = self._default_text(aAbsCards, 'Equipment', self.iNumberEquipment)
        return sText

    def process_conviction(self, aCards):
        aAbsCards = self._get_abstract_cards(aCards)
        sText = self._default_text(aAbsCards, 'Conviction', self.iNumberConvictions)
        return sText

    def process_power(self, aCards):
        aAbsCards = self._get_abstract_cards(aCards)
        sText = self._default_text(aAbsCards, 'Power', self.iNumberPowers)
        return sText


    def process_multi(self, aCards):
        """Stats about the multirole cards"""
        aAbsCards = self._get_abstract_cards(aCards)
        dMulti = {}
        sPerCards = self._percentage(self.iNumberMult, self.iNumberLibrary,
                'Library')
        sText = "<b>Multirole Cards :</b>\n" \
                "Number of Multirole cards = %(num)d %(per)s\n" % {
                        'num' : self.iNumberMult,
                        'per' : sPerCards
                        }
        for oAbsCard in aAbsCards:
            aTypes = [x.name for x in oAbsCard.cardtype]
            if len(aTypes) > 1:
                sKey = "/".join(sorted(aTypes))
                dMulti.setdefault(sKey, 0)
                dMulti[sKey] += 1
        print dMulti, dMulti.items()
        for sMultiType, iNum in sorted(dMulti.items(), key=lambda x: x[1],
                reverse=True):
            sPer = self._percentage(iNum, self.iNumberLibrary, 'Library')
            sText += 'Number of %(multitype)s cards = %(num)d %(per)s\n' % {
                    'multitype' : sMultiType,
                    'num' : iNum,
                    'per' : sPer,
                    }

        return sText


    def process_imbued(self, aCards):
        dDeckImbued = {}
        dDeckVirt = {}

        iMaxLife = -500
        iMinLife = 500
        iTotLife = 0
        iImbMinGroup = 500
        iImbMaxGroup = -500
        iNumberUniqueImbued = 0

        for oAbsCard in self._get_abstract_cards(aCards):
            if oAbsCard.name not in dDeckImbued:
                iNumberUniqueImbued += 1
                dDeckImbued[oAbsCard.name] = 1
            else:
                dDeckImbued[oAbsCard.name] += 1

            for virtue in oAbsCard.virtue:
                dDeckVirt.setdefault(virtue.fullname, [0])
                # List, so we can use _get_sort_key
                dDeckVirt[virtue.fullname][0] += 1

            self.iMaxGroup = max(self.iMaxGroup, oAbsCard.group)
            self.iMinGroup = min(self.iMinGroup, oAbsCard.group)
            iImbMaxGroup = max(iImbMaxGroup, oAbsCard.group)
            iImbMinGroup = min(iImbMinGroup, oAbsCard.group)

            iTotLife += oAbsCard.life
            iMaxLife = max(iMaxLife, oAbsCard.life)
            iMinLife = min(iMinLife, oAbsCard.life)

        # Build up Text
        sImbuedText = "<b>Imbued</b>\n"
        sImbuedText += "<span foreground = \"blue\">Basic Crypt stats</span>\n"
        sImbuedText += "Number of Imbued = " + str(self.iNumberImbued) + \
                self._percentage(self.iNumberImbued, self.iCryptSize, "Crypt") + "\n"
        sImbuedText += "Number of Unique Imbued = " + str(iNumberUniqueImbued) + "\n"
        if self.iNumberImbued > 0:
            sImbuedText += "Minimum Group is : " + str(iImbMinGroup) + "\n"
            sImbuedText += "Maximum Group is : " + str(iImbMaxGroup) + "\n"

            sImbuedText += "\n<span foreground = \"blue\">Crypt cost</span>\n"

            sImbuedText += "Cheapest is : " + str(iMinLife) + "\n"
            sImbuedText += "Most Expensive is : " + str(iMaxLife) + "\n"
            sImbuedText += "Average Life is : " + str(iTotLife / float(self.iNumberImbued)).ljust(5)[:5] + "\n\n"

            for virtue, number in sorted(dDeckVirt.iteritems(),
                    key=self._get_sort_key, reverse=True):
                sImbuedText += str(number[0])+" Imbued with " + virtue \
                           + ' ' + self._percentage(number[0],
                                   self.iCryptSize, "Crypt") + '\n'
                # Treat virtues as inferior disciplines for happy families
                self.dCryptDisc.setdefault(number[0], [])
                self.dCryptDisc[number[0]].append(virtue)

        return sImbuedText

    def happy_families_init(self, aCards, oHFVBox):
        """Setup data and tab for HF analysis"""
        oMainLabel = gtk.Label()

        oHFVBox.pack_start(oMainLabel)

        self.dLibDisc.setdefault('No Discipline', 0)
        self.dLibClan.setdefault('No Clan', 0)

        for oAbsCard in self._get_abstract_cards(aCards):
            aTypes = [x.name for x in oAbsCard.cardtype]
            if len(aTypes)>1:
                # Since we examining all the cards, do this here
                self.iNumberMult += 1
                self.aMultiCards.append(oAbsCard)
            if aTypes[0] != 'Vampire' and aTypes[0] != 'Imbued' \
                    and aTypes[0] != 'Master':
                # Non-Master Library card, so extract disciplines
                if len(oAbsCard.discipline) > 0:
                    for disc in oAbsCard.discipline:
                        self.dLibDisc.setdefault(disc.discipline.fullname, 0)
                        self.dLibDisc[disc.discipline.fullname] += 1
                elif len(oAbsCard.virtue) > 0:
                    for virtue in oAbsCard.virtue:
                        self.dLibDisc.setdefault(virtue.fullname, 0)
                        self.dLibDisc[virtue.fullname] += 1
                else:
                    self.dLibDisc['No Discipline'] += 1

            if aTypes[0] != 'Vampire' and aTypes[0] != 'Imbued':
                # Extract clan information
                if len(oAbsCard.clan) > 0:
                    for oClan in oAbsCard.clan:
                        self.dLibClan.setdefault(oClan.name, 0)
                        self.dLibClan[oClan.name] += 1
                else:
                    self.dLibClan['No Clan'] += 1


        # Build up Text
        sHappyFamilyText = "<b>Happy Families Analysis :</b>\n"
        if self.iNumberImbued > 0:
            sHappyFamilyText += "\n<span foreground = \"red\">This is not optimised for Imbued, and treats them as small vampires</span>\n"

        if self.iCryptSize == 0:
            sHappyFamilyText += "\n<span foreground = \"red\">Need to have a crypt to do the analysis</span>\n"
            oMainLabel.set_markup(sHappyFamilyText)
            oHFVBox.show_all()
            return

        if len(self.dDeckDisc) < 1:
            # Crypt only has Smudge, for example
            sHappyFamilyText += "\n<span foreground = \"red\">Need disciplines to do analysis</span>\n"
            oMainLabel.set_markup(sHappyFamilyText)
            oHFVBox.show_all()
            return

        aTopVampireDisc = sorted(self.dCryptDisc, reverse=True)
        aSortedDiscs = []
        for iNum in aTopVampireDisc:
            for sDisc in self.dCryptDisc[iNum]:
                aSortedDiscs.append(sDisc)
        for sDisc in self.dDeckDisc:
            self.dLibDisc.setdefault(sDisc, 0) # Need to ensure all these are defined

        iHFMasters = int(round(0.2 * self.iNumberLibrary))

        iNonMasters = self.iNumberLibrary - self.iNumberMasters

        sHappyFamilyText += "\n<b>Master Cards</b>\n"
        sHappyFamilyText += str(self.iNumberMasters) + " Masters " + \
                self._percentage(self.iNumberMasters,
                        self.iNumberLibrary, "Library") + \
                ",\nHappy Families recommends 20%, which would be " + \
                str(iHFMasters) + '  : '

        sHappyFamilyText += "<span foreground = \"blue\">Difference = " + \
                str(abs(iHFMasters - self.iNumberMasters)) + "</span>\n"

        oMainLabel.set_markup(sHappyFamilyText)

        oHBox = gtk.HBox(False, 2)

        # self.dCryptDisc and dLibDisc have the info we need about the disciplines

        oComboBox = gtk.combo_box_new_text()
        iMax = min(6, len(self.dDeckDisc)) + 1
        for iNum in range(1, iMax):
            oComboBox.append_text(str(iNum))
        oComboBox.append_text('Use list of disciplines')
        oComboBox.set_active(1)

        oHBox.pack_start(gtk.Label('Number of Disciplines'))
        oHBox.pack_start(oComboBox)
        oHBox.pack_start(gtk.Label(' : '))

        oDiscWidget = MultiSelectComboBox()
        oDiscWidget.fill_list(aSortedDiscs)

        oDiscWidget.set_sensitive(False)

        oDiscWidget.set_list_size(200, 400)

        oHBox.pack_start(oDiscWidget)

        oHFVBox.pack_start(oHBox, False, False)

        oComboBox.connect('changed', self._combo_changed, oDiscWidget)

        oResLabel = gtk.Label()

        oButton = gtk.Button('Recalculate Happy Family Analysis')

        oButton.connect('clicked', self._redo_happy_family, oHFVBox, oComboBox,
                oDiscWidget, oResLabel, aSortedDiscs, iNonMasters)

        oHFVBox.pack_start(oButton, False, False)

        oResLabel.set_markup(self._happy_lib_analysis(aSortedDiscs[:2],
            iNonMasters))

        oHFVBox.pack_start(oResLabel)
        oHFVBox.show_all()

    def _combo_changed(self, oComboBox, oDiscWidget):
        """Toggle the sensitivity of the Discipline select widget as needed"""
        if oComboBox.get_active_text() == 'Use list of disciplines':
            oDiscWidget.set_sensitive(True)
        else:
            oDiscWidget.set_sensitive(False)

    def _redo_happy_family(self, oButton, oHFVBox, oComboBox, oDiscWidget,
            oResLabel, aSortedDiscs, iNonMasters):
        """Redo the HF analysis based on button press"""
        if oComboBox.get_active_text() == 'Use list of disciplines':
            aTheseDiscs = oDiscWidget.get_selection()
            if not aTheseDiscs:
                return # Just ignore the zero selection case
        else:
            iNumDiscs = int(oComboBox.get_active_text())
            aTheseDiscs = aSortedDiscs[:iNumDiscs]
        oResLabel.hide()
        oResLabel.set_markup(self._happy_lib_analysis(aTheseDiscs, iNonMasters))
        oResLabel.show()
        oHFVBox.show_all()

    def _happy_lib_analysis(self, aDiscsToUse, iNonMasters):

        iNumberToShow = len(aDiscsToUse)

        sHappyFamilyText = "<b>" + str(iNumberToShow) + " Discipline Case</b>\n"
        sHappyFamilyText += "Disciplines : <i>%s</i>\n" % ",".join(aDiscsToUse)
        fDemon = float(self.iCryptSize)
        dDiscs = {}
        for sDisc in aDiscsToUse:
            fDemon += self.dDeckDisc[sDisc][0]
        iHFNoDiscipline = int((iNonMasters * self.iCryptSize / fDemon ))
        iDiff = iNonMasters - iHFNoDiscipline
        dDiscNumbers = {}
        for sDisc in aDiscsToUse:
            iHFNumber = int(iNonMasters * self.dDeckDisc[sDisc][0] / fDemon )
            dDiscNumbers[sDisc] = iHFNumber
            iDiff -= iHFNumber

        if iDiff > 0:
            iHFNoDiscipline += iDiff # Shove rounding errors here

        sHappyFamilyText += "Number of Cards requiring No discipline : " + \
                str(self.dLibDisc['No Discipline']) + '\n'
        sHappyFamilyText += "Happy Families recommends " + \
                str(iHFNoDiscipline) + ' : '
        sHappyFamilyText += "<span foreground = \"blue\">Difference = " + \
                str(abs(iHFNoDiscipline - self.dLibDisc['No Discipline'])) + \
                "</span>\n"
        for sDisc in aDiscsToUse:
            iCryptNum = self.dDeckDisc[sDisc][0]
            iHFNum = dDiscNumbers[sDisc]
            sHappyFamilyText += "Number of Cards requiring " + sDisc + " : " + \
                    str(self.dLibDisc[sDisc]) + \
                    " (" + str(iCryptNum) + " crypt members)\n"
            sHappyFamilyText += "Happy Families recommends " + \
                    str(iHFNum) + '  : '
            sHappyFamilyText += "<span foreground = \"blue\">Difference = " + \
                    str(abs(iHFNum - self.dLibDisc[sDisc])) + "</span>\n"
        return sHappyFamilyText



plugin = AnalyzeCardList
