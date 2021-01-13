# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Dialog to display deck analysis software
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>,
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details
# pylint: disable=too-many-lines
# This covers a lot of cases, and splitting it into multiple
# files won't gain any clarity

"""Display interesting statistics and properties of the card set."""

from gi.repository import Gtk

from sqlobject import SQLObjectNotFound

from sutekh.base.core.BaseTables import PhysicalCardSet, Printing
from sutekh.base.core.BaseAdapters import (IAbstractCard, IPhysicalCard,
                                           IKeyword)
from sutekh.base.core.BaseFilters import (CardTypeFilter, FilterNot,
                                          KeywordFilter)
from sutekh.base.gui.SutekhDialog import NotebookDialog
from sutekh.base.gui.GuiUtils import wrap
from sutekh.base.gui.MultiSelectComboBox import MultiSelectComboBox
from sutekh.base.gui.AutoScrolledWindow import AutoScrolledWindow

from sutekh.core.SutekhTables import CRYPT_TYPES
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.core.Abbreviations import Titles

UNSLEEVED = "<span foreground='green'>%s may be played unsleeved</span>\n"
SLEEVED = "<span foreground='orange'>%s should be sleeved</span>\n"
SPECIAL = {'Not Tournament Legal Cards', 'Multirole', 'Mixed Card Backs'}

RT_WATCHLIST = 'RT:Watchlist'
RT_BANNED = 'RT:Banned'

# Lookup for titles for the not legal tabs
ILLEGAL_LOOKUP = {
    RT_BANNED: 'Cards Banned in Rapid Thoughts',
    RT_WATCHLIST: 'Cards on the Rapid Thoughts Watchlist',
    'Not Tournament Legal Cards': 'Not Tournament Legal Cards',
}


# utility functions
def _percentage(iNum, iTot, sDesc):
    """Utility function for calculating _percentages"""
    if iTot > 0:
        fPrec = iNum / float(iTot)
    else:
        fPrec = 0.0
    return '<i>(%5.3f %% of %s)</i>' % (fPrec * 100, sDesc)


def _get_abstract_cards(aCards):
    """Get the abstract cards given the list of names"""
    return [IAbstractCard(x) for x in aCards]


def _lookup_discipline(sKey, dDisciplines):
    """Return the object with the fullname sKey"""
    return [x for x in dDisciplines if sKey == x.fullname][0]


def _disc_sort_key(tData):
    """Sort disciplines by reverse number, then reverse superior number,
       then alphabetically by name"""
    return (-tData[1][1], -tData[1][2], tData[0].fullname)


def _format_card_line(sString, sTrailer, iNum, iLibSize):
    """Format card lines for notebook"""
    sPer = _percentage(iNum, iLibSize, "Library")
    return "Number of %(type)s %(trail)s = %(num)d %(per)s\n" % {
        'type': sString,
        'trail': sTrailer,
        'num': iNum,
        'per': sPer,
        }


def _load_printing_back_info():
    """Load the different card back types from the printings."""
    dBacks = {None: None}  # Unspecified printing maps to None
    for oPrinting in Printing.select():
        for oProp in oPrinting.properties:
            if oProp.value.startswith('Back Type: '):
                sValue = oProp.value.replace('Back Type: ', '')
                dBacks[oPrinting] = sValue
    return dBacks


def _get_card_costs(aCards):
    """Calculate the cost of the list of Abstract Cards

       Return lists of costs, for pool, blood and convictions
       Each list contains: Number with variable cost, Maximum Cost, Total Cost,
       Number of cards with a cost
       """
    dCosts = {}
    for sType in ('blood', 'pool', 'conviction'):
        dCosts.setdefault(sType, [0, 0, 0, 0])
    for oAbsCard in aCards:
        if oAbsCard.cost is not None:
            dCosts[oAbsCard.costtype][3] += 1
            if oAbsCard.cost == -1:
                dCosts[oAbsCard.costtype][0] += 1
            else:
                iMaxCost = dCosts[oAbsCard.costtype][1]
                dCosts[oAbsCard.costtype][1] = max(iMaxCost, oAbsCard.cost)
                dCosts[oAbsCard.costtype][2] += oAbsCard.cost
    return dCosts['blood'], dCosts['pool'], dCosts['conviction']


def _get_card_disciplines(aCards):
    """Extract the set of disciplines and virtues from the cards"""
    dDisciplines = {}
    dVirtues = {}
    iNoneCount = 0
    for oAbsCard in aCards:
        if oAbsCard.discipline:
            aThisDisc = [oP.discipline.fullname for oP
                         in oAbsCard.discipline]
        else:
            aThisDisc = []
        if oAbsCard.virtue:
            aThisVirtue = [oV.fullname for oV in oAbsCard.virtue]
        else:
            aThisVirtue = []
        for sDisc in aThisDisc:
            dDisciplines.setdefault(sDisc, 0)
            dDisciplines[sDisc] += 1
        for sVirtue in aThisVirtue:
            dVirtues.setdefault(sVirtue, 0)
            dVirtues[sVirtue] += 1
        if not oAbsCard.discipline and not oAbsCard.virtue:
            iNoneCount += 1
    return dDisciplines, dVirtues, iNoneCount


def _get_card_clan_multi(aCards):
    """Extract the clan requirements and the multi discipline cards
       form the list of Abstract Cards"""
    dClan = {}
    iClanRequirement = 0
    dMulti = {}
    for oAbsCard in aCards:
        if oAbsCard.clan:
            iClanRequirement += 1
            aClans = [x.name for x in oAbsCard.clan]
            for sClan in aClans:
                dClan.setdefault(sClan, 0)
                dClan[sClan] += 1
        aTypes = [x.name for x in oAbsCard.cardtype]
        if aTypes:
            sKey = "/".join(sorted(aTypes))
            dMulti.setdefault(sKey, 0)
            dMulti[sKey] += 1
    return iClanRequirement, dClan, dMulti


def _format_cost_numbers(sCardType, sCostString, aCost, iNum):
    """Format the display of the card cost information"""
    sVarPercent = _percentage(aCost[0], iNum, '%s cards' % sCardType)
    sNumPercent = _percentage(aCost[3], iNum, '%s cards' % sCardType)
    if iNum > 0:
        fAvg = aCost[2] / float(iNum)
    else:
        fAvg = 0.0
    sText = "Most Expensive %(name)s Card  (%(type)s) = %(max)d\n" \
            "Cards with variable cost = %(var)d %(per)s\n" \
            "Cards with %(type)s cost = %(numcost)d %(percost)s\n" \
            "Average %(name)s card %(type)s cost = %(avg)5.3f\n" % {
                'name': sCardType,
                'type': sCostString,
                'var': aCost[0],
                'per': sVarPercent,
                'max': aCost[1],
                'avg': fAvg,
                'numcost': aCost[3],
                'percost': sNumPercent,
                }
    return sText


def _crypt_avg(iCostTot, iCryptSize):
    """Calculate the crypt averages"""
    if iCryptSize > 0:
        fAvg = float(iCostTot) / iCryptSize
    else:
        fAvg = 0.0
    if iCryptSize < 4:
        fAvgDraw = iCryptSize * fAvg
    else:
        fAvgDraw = 4 * fAvg

    return fAvg, fAvgDraw


def _format_disciplines(sDiscType, dDisc):
    """Format the display of disciplines and virtues"""
    sText = ''
    for sDisc, iCnt in sorted(dDisc.items(), key=lambda x: x[1],
                              reverse=True):
        sText += 'Number of cards requiring %s %s = %d\n' % (sDiscType,
                                                             sDisc, iCnt)
    return sText


def _format_clan(sCardType, iClanRequirement, dClan, iNum):
    """Format the clan requirements list for display"""
    sText = ''
    if iClanRequirement > 0:
        sPer = _percentage(iClanRequirement, iNum, '%s cards' % sCardType)
        sText += ("Number of %(type)s with a Clan requirement = %(num)d "
                  "%(per)s\n") % {'type': sCardType, 'num': iClanRequirement,
                                  'per': sPer, }
        for sClan, iClanNum in sorted(dClan.items(), key=lambda x: x[1],
                                      reverse=True):
            sPer = _percentage(iClanNum, iNum, '%s cards' % sCardType)
            sText += ('Number of %(type)s requiring %(clan)s = %(num)d '
                      '%(per)s\n') % {'type': sCardType, 'clan': sClan,
                                      'num': iClanNum, 'per': sPer, }
    return sText


def _format_multi(sCardType, dMulti, iNum):
    """Format the multi-role cards list for display"""
    sText = ''
    for sType, iMulti in sorted(dMulti.items(), key=lambda x: x[1],
                                reverse=True):
        sPer = _percentage(iMulti, iNum, '%s cards' % sCardType)
        sText += ('%(num)d %(type)s cards are %(multitype)s cards'
                  ' %(per)s\n') % {'num': iMulti, 'type': sCardType,
                                   'multitype': sType, 'per': sPer, }
    return sText


def _get_back_counts(aPhysCards, dBacks):
    """Get the counts of the different expansions for the list"""
    dCounts = {}
    for oCard in aPhysCards:
        # We get 'Other' if we have a printing that is missing
        # Back information
        oKey = dBacks.get(oCard.printing, 'Other')
        dCounts.setdefault(oKey, 0)
        dCounts[oKey] += 1
    return dCounts


def _split_into_crypt_lib(aPhysCards):
    """Split a list of physical cards into crypt and library"""
    aCrypt = []
    aLib = []
    for oCard in aPhysCards:
        oAbsCard = IAbstractCard(oCard)
        sType = [x.name for x in oAbsCard.cardtype][0]
        if sType in CRYPT_TYPES:
            aCrypt.append(oCard)
        else:
            aLib.append(oCard)
    return aCrypt, aLib


def _check_same(aPhysCards, dBacks):
    """Check that all the crypt cards and all the library cards have the
       same backs"""
    aCrypt, aLib = _split_into_crypt_lib(aPhysCards)
    dCrypt = _get_back_counts(aCrypt, dBacks)
    dLib = _get_back_counts(aLib, dBacks)
    if len(dCrypt) > 1 or len(dLib) > 1:
        return False  # Differing backs
    if 'PDF' in dCrypt or 'PDF' in dLib:
        return False  # PDF set in use, so must be sleeved
    return True


def _simple_back_checks(dCards, sType):
    """Simple checks on the card backs. Returns None if we need
       further investigation"""
    if "PDF" in dCards:
        sText = "%s has cards from a V:EKN pdf expansion.\n" % sType
        sText += SLEEVED % sType
        return sText
    if len(dCards) == 1 and None not in dCards:
        sText = "All %s cards have identical backs\n" % sType.lower()
        sText += UNSLEEVED % sType
        return sText
    if None in dCards:
        sText = ("%s has cards from unspecified expansions."
                 " Ignoring the %s\n" % (sType, sType.lower()))
        return sText
    return None


def _percentage_backs(dCards, iSize, fPer, sType):
    """Checks that the percentage of cards with a single back are not too
       small"""
    sText = ""
    bOK = True
    for sGroupName in dCards:
        fThisPer = float(dCards[sGroupName]) / float(iSize) * 100
        sText += "%d %s backs (%2.1f%% of the %s).\n" % (dCards[sGroupName],
                                                         sGroupName,
                                                         fThisPer,
                                                         sType.lower())
        if fThisPer < fPer:
            sText += ("Group of cards with the same back that's smaller"
                      " than %2.1f%% of the %s.\n" % (fPer, sType.lower()))
            bOK = False
    return sText, bOK


def _group_backs(dCards, aCards, iNum, dBacks):
    """Check for that cards of a single back don't belong to too few different
       card groups"""
    # No more than 2 distinct vampires of in a group of common backs
    aCardsByExp = []
    bOK = True
    sText = ""
    for sGrpName in dCards:
        aCardsByExp.append([oCard for oCard in aCards if
                            dBacks[oCard.printing] == sGrpName])
    for aExpCards in aCardsByExp:
        # For each expansion, count number of distinct cards
        aNames = {x.abstractCard.name for x in aExpCards}
        if len(aNames) < iNum:
            sText += ("Group of fewer than %d different cards"
                      " with the same back.\n" % iNum)
            sText += "\t" + ", ".join(aNames) + "\n"
            bOK = False
    if not bOK:
        return sText, aCardsByExp
    return None, aCardsByExp


class DisciplineNumberSelect(Gtk.HBox):
    # pylint: disable=too-many-public-methods
    # Gtk.Widget so many public methods
    """Holds a combo box and a discpline list for choosing a list
       of disciplines to use."""

    _sUseList = 'Use list of disciplines'

    def __init__(self, aSortedDisciplines, oDlg):
        super().__init__(False, 2)
        self._aSortedDisciplines = aSortedDisciplines
        # Never show more than 5 disciplines here - people can use the
        # discpline list in the combo box if they want more
        self._oComboBox = Gtk.ComboBoxText()
        for iNum in range(1, min(5, len(aSortedDisciplines)) + 1):
            self._oComboBox.append_text('%d' % iNum)
        self._oComboBox.append_text(self._sUseList)
        self._oComboBox.set_active(1)
        self.pack_start(Gtk.Label(label='Number of Disciplines'),
                        False, True, 0)
        self.pack_start(self._oComboBox, False, True, 0)
        self.pack_start(Gtk.Label(label=' : '), False, True, 0)
        self._oDiscWidget = MultiSelectComboBox(oDlg)
        self._oDiscWidget.fill_list(self._aSortedDisciplines)
        self._oDiscWidget.set_sensitive(False)
        self._oDiscWidget.set_list_size(200, 400)
        self.pack_start(self._oDiscWidget, False, True, 0)
        self._oComboBox.connect('changed', self._combo_changed)

    def _combo_changed(self, _oWidget):
        """Toggle the sensitivity of the Discipline select widget as needed"""
        sText = self._oComboBox.get_active_text()
        if sText == self._sUseList:
            self._oDiscWidget.set_sensitive(True)
        else:
            self._oDiscWidget.set_sensitive(False)

    def get_disciplines(self):
        """Get the list of disciplines to use."""
        sText = self._oComboBox.get_active_text()
        if sText == 'Use list of disciplines':
            aTheseDiscs = self._oDiscWidget.get_selection()
        else:
            iNumDiscs = int(sText)
            aTheseDiscs = self._aSortedDisciplines[:iNumDiscs]
        return aTheseDiscs


class AnalyzeCardList(SutekhPlugin):
    """Plugin to analyze card sets.

      Displays various interesting stats, and does a Happy Family
      analysis of the deck
       """
    dTableVersions = {PhysicalCardSet: (6, 7)}
    aModelsSupported = (PhysicalCardSet,)

    sMenuName = "Analyze Deck"

    sHelpCategory = "card_sets:analysis"

    sHelpText = """This tool examines a card set and displays various
                   statistics about it which are intended to give you
                   some indication of how the card set will operate as
                   a deck.

                   It displays several tabs, each of which summarises
                   different aspects of the card set. The first tab
                   summarises some basic information about the entire set.
                   The second tab implements Legbiter's Happy Family
                   analysis for the card set. The remaining tabs
                   consider specific card types.

                   The happy family implementation allows you either to
                   select the number of disciplines to use, or to select
                   the disciplines to consider manually."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dBacks = _load_printing_back_info()
        # dictionary of individual analysis pages
        self._dConstruct = {
            'Vampire': self._process_vampire,
            'Imbued': self._process_imbued,
            'Combat': self._process_combat,
            'Reaction': self._process_reaction,
            'Action': self._process_action,
            'Action Modifier': self._process_action_modifier,
            'Retainer': self._process_retainer,
            'Equipment': self._process_equipment,
            'Ally': self._process_allies,
            'Political Action': self._process_political_action,
            'Power': self._process_power,
            'Conviction': self._process_conviction,
            'Event': self._process_event,
            'Master': self._process_master,
            'Multirole': self._process_multi,
            'Not Tournament Legal Cards': self._process_non_legal,
            'Mixed Card Backs': self._process_backs,
        }

    def get_menu_item(self):
        """Register on the 'Analyze' Menu"""
        oAnalyze = Gtk.MenuItem(label=self.sMenuName)
        oAnalyze.connect("activate", self.activate)
        oAnalyzeRT = Gtk.MenuItem(label="Analyze Deck (Rapids Thoughts)")
        oAnalyzeRT.connect("activate", self.activate_rt)
        return [('Analyze', oAnalyze), ('Analyze', oAnalyzeRT)]

    def activate(self, _oWidget):
        """Activate for non RT analysis"""
        self.activate_heart(False)

    def activate_rt(self, _oWidget):
        """Activate for non RT analysis"""
        self.activate_heart(True)

    # pylint: disable=attribute-defined-outside-init
    # We define a lot of class variables here, because a) this is the
    # plugin entry point, and, b) they need to reflect the current CardSet,
    # so they can't be filled properly in __init__
    # pylint: disable=too-many-branches, too-many-locals, too-many-statements
    # This is responsible for filling the whole notebook, so quite a long
    # function with several branches and variables, and there's no benefit
    # to splitting it up further
    def activate_heart(self, bRapid=False):
        """Create the actual dialog, and populate it"""
        if not self._check_cs_size('Analyze Deck', 500):
            return
        oDlg = NotebookDialog("Analysis of Card List", self.parent,
                              Gtk.DialogFlags.DESTROY_WITH_PARENT,
                              ("_Close", Gtk.ResponseType.CLOSE))
        oDlg.connect("response", lambda oDlg, resp: oDlg.destroy())

        self.dTypeNumbers = {}
        dCardLists = {}

        aAllPhysCards = [IPhysicalCard(x) for x in
                         self.model.get_card_iterator(None)]
        aAllCards = _get_abstract_cards(aAllPhysCards)

        for sCardType in self._dConstruct:
            if sCardType not in SPECIAL:
                dCardLists[sCardType] = _get_abstract_cards(
                    self.model.get_card_iterator(CardTypeFilter(sCardType)))
                self.dTypeNumbers[sCardType] = len(dCardLists[sCardType])
            elif sCardType == 'Multirole':
                # Multirole values start empty, and are filled in later
                dCardLists[sCardType] = []
                self.dTypeNumbers[sCardType] = 0
            elif sCardType == 'Not Tournament Legal Cards':
                dCardLists[sCardType] = _get_abstract_cards(
                    self.model.get_card_iterator(
                        FilterNot(self.model.oLegalFilter)))
                self.dTypeNumbers[sCardType] = len(dCardLists[sCardType])
                if bRapid:
                    try:
                        for sType in [RT_BANNED, RT_WATCHLIST]:
                            dCardLists[sType] = _get_abstract_cards(
                                self.model.get_card_iterator(
                                    KeywordFilter(IKeyword(sType))))
                            self.dTypeNumbers[sType] = \
                                len(dCardLists[sType])
                    except SQLObjectNotFound:
                        # We ignore this if the keywords aren't present
                        self.dTypeNumbers[RT_BANNED] = 0
                        self.dTypeNumbers[RT_WATCHLIST] = 0
            elif sCardType == 'Mixed Card Backs':
                # Assume not mixed, so we skip
                self.dTypeNumbers[sCardType] = 0
                if not _check_same(aAllPhysCards, self._dBacks):
                    self.dTypeNumbers[sCardType] = len(aAllPhysCards)
                dCardLists[sCardType] = aAllPhysCards

        oHappyBox = Gtk.VBox(homogeneous=False, spacing=2)

        self.iTotNumber = len(aAllCards)
        self.dCryptStats = {}
        self.dLibStats = {}

        self.iCryptSize = sum([self.dTypeNumbers[x] for x in CRYPT_TYPES])
        self.iLibSize = len(aAllCards) - self.iCryptSize
        self.get_crypt_stats(dCardLists['Vampire'], dCardLists['Imbued'])
        self.get_library_stats(aAllCards, dCardLists)
        # Do happy family analysis
        self.happy_families_init(oHappyBox, oDlg)

        # Fill the dialog with the results
        oMainBox = Gtk.VBox(homogeneous=False, spacing=2)
        oDlg.add_widget_page(oMainBox, 'Basic Info')
        oDlg.add_widget_page(oHappyBox, 'Happy Families Analysis')

        # overly clever? crypt cards first, then alphabetical, then specials
        aOrderToList = (sorted(CRYPT_TYPES) +
                        [x for x in sorted(self.dTypeNumbers) if
                         (x not in CRYPT_TYPES and x not in SPECIAL
                          and x not in [RT_BANNED, RT_WATCHLIST])] +
                        sorted(SPECIAL))
        for sCardType in aOrderToList:
            if self.dTypeNumbers[sCardType]:
                fProcess = self._dConstruct[sCardType]
                oDlg.add_widget_page(wrap(fProcess(dCardLists[sCardType])),
                                     sCardType)
        if bRapid:
            fProcess = self._dConstruct['Not Tournament Legal Cards']
            for sType in [RT_BANNED, RT_WATCHLIST]:
                if self.dTypeNumbers[sType]:
                    oDlg.add_widget_page(wrap(fProcess(dCardLists[sType],
                                                       sType)),
                                         ILLEGAL_LOOKUP[sType])

        # Setup the main notebook
        oTitle, oDesc, oDetails = self._prepare_main(bRapid)
        oMainBox.pack_start(oTitle, False, True, 0)
        # Excess Space goes to the description
        oMainBox.pack_start(oDesc, True, True, 0)
        oMainBox.pack_start(oDetails, False, True, 0)
        if self.iLibSize > 0:
            oMainBox.pack_start(self._process_library(), False, True, 0)
        oDlg.show_all()
        oDlg.notebook.set_current_page(0)
        oDlg.run()

    # pylint: enable=attribute-defined-outside-init
    # pylint: enable=too-many-branches, too-many-statements

    def get_crypt_stats(self, aVampireCards, aImbuedCards):
        """Extract the relevant statistics about the crypt from the lists
           of cards."""
        def get_info(aVampires, aImbued, sClass):
            """Extract the minimum and maximum for the sets into
               self.dCryptStats, using keys of the form 'vampire min sClass'"""
            sMax = 'max %s' % sClass
            sMin = 'min %s' % sClass
            if aImbued:
                iIMax = self.dCryptStats['imbued ' + sMax] = max(aImbued)
                iIMin = self.dCryptStats['imbued ' + sMin] = min(aImbued)
            else:
                iIMax = -500
                iIMin = 500
            if aVampires:
                iVMax = self.dCryptStats['vampire ' + sMax] = max(aVampires)
                iVMin = self.dCryptStats['vampire ' + sMin] = min(aVampires)
            else:
                iVMax = -500
                iVMin = 500
            self.dCryptStats[sMax] = max(iVMax, iIMax)
            self.dCryptStats[sMin] = min(iVMin, iIMin)

        # Skip the any group case, as it has no effect here
        get_info([x.group for x in aVampireCards if x.group != -1],
                 [x.group for x in aImbuedCards if x.group != -1], 'group')
        get_info([x.capacity for x in aVampireCards],
                 [x.life for x in aImbuedCards], 'cost')
        aAllCosts = sorted([x.capacity for x in aVampireCards] +
                           [x.life for x in aImbuedCards])
        self.dCryptStats['total cost'] = sum(aAllCosts)
        self.dCryptStats['min draw'] = sum(aAllCosts[0:4])
        self.dCryptStats['max draw'] = sum(aAllCosts[-1:-5:-1])
        # Extract discipline stats (will be used in display + HF)
        dDiscs = {}
        self.dCryptStats['crypt discipline'] = dDiscs
        for oCard in aVampireCards:
            for oDisc in oCard.discipline:
                dDiscs.setdefault(oDisc.discipline, ['discipline', 0, 0])
                dDiscs[oDisc.discipline][1] += 1
                if oDisc.level == 'superior':
                    dDiscs[oDisc.discipline][2] += 1
        # We treat virtues as inferior discipline for happy family analysis
        for oCard in aImbuedCards:
            for oVirt in oCard.virtue:
                dDiscs.setdefault(oVirt, ['virtue', 0, 0])
                dDiscs[oVirt][1] += 1

    def get_library_stats(self, aAllCards, dCardLists):
        """Extract the relevant library stats from the list of cards"""
        aCryptCards = []
        for sType in CRYPT_TYPES:
            aCryptCards.extend(dCardLists[sType])
        aLibCards = [x for x in aAllCards if x not in aCryptCards]
        # Extract the relevant stats
        self.dLibStats['clan'] = {'No Clan': 0}
        self.dLibStats['discipline'] = {'No Discipline': 0}
        for oCard in aLibCards:
            if len(oCard.cardtype) > 1:
                self.dTypeNumbers['Multirole'] += 1
                dCardLists['Multirole'].append(oCard)
            if oCard.clan:
                aClans = [x.name for x in oCard.clan]
            elif oCard.creed:
                aClans = [x.name for x in oCard.creed]
            else:
                aClans = ['No Clan']
            for sClan in aClans:
                self.dLibStats['clan'].setdefault(sClan, 0)
                self.dLibStats['clan'][sClan] += 1
            if oCard.discipline:
                aDisciplines = [oP.discipline.fullname for oP in
                                oCard.discipline]
            elif oCard.virtue:
                aDisciplines = [oV.fullname for oV in oCard.virtue]
            else:
                aDisciplines = ['No Discipline']
            for sDisc in aDisciplines:
                self.dLibStats['discipline'].setdefault(sDisc, 0)
                self.dLibStats['discipline'][sDisc] += 1

    # pylint: disable=too-many-branches
    # We need to check all these cases to present a sensible
    # summary - there isn't a benefit to splitting these into different
    # functions
    def _prepare_main(self, bRapid):
        """Setup the main notebook display"""
        oCS = self._get_card_set()

        sTitleText = ("Analysis Results for :\n\t\t<b>%(name)s</b>\n"
                      "\t\tby <i>%(author)s</i>\n" % {
                          'name': self._escape(self.view.sSetName),
                          'author': self._escape(oCS.author),
                      })
        # We wrap the description in a scrollable widget, since it
        # can be very, very long (Matt Morgan's TWDA entries, for
        # example)
        sDesc = self._escape(oCS.comment)
        if not sDesc:
            sDesc = "<i>No description</i>"
        oDesc = wrap(sDesc)
        oScrolledBox = Gtk.VBox(homogeneous=False, spacing=1)
        oDescTitle = Gtk.Label()
        oDescTitle.set_markup("<b>Description:</b>")
        oScrolledBox.pack_start(oDescTitle, False, True, 0)
        oScrolledBox.pack_start(AutoScrolledWindow(oDesc), True, True, 0)

        if bRapid:
            sMainText = '<i>Rapid Thoughts Analysis</i>\n'
        else:
            sMainText = '<i>V:EKN Constructed Analysis</i>\n'
        # Set main notebook text
        for sCardType in CRYPT_TYPES:
            if self.dTypeNumbers[sCardType] > 0:
                sMainText += 'Number of %s = %d\n' % (
                    sCardType, self.dTypeNumbers[sCardType])
        if (self.dTypeNumbers['Vampire'] > 0 and
                self.dTypeNumbers['Imbued'] > 0) or self.iCryptSize == 0:
            sMainText += "Total Crypt size = %d\n" % self.iCryptSize
        if self.iCryptSize > 0:
            sMainText += ("Minimum Group in Crypt = %d\n" %
                          self.dCryptStats['min group'])
            sMainText += ("Maximum Group in Crypt = %d\n" %
                          self.dCryptStats['max group'])
        if bRapid:
            if self.iCryptSize < 6:
                sMainText += ('<span foreground = "red">Less than 6 Crypt'
                              ' Cards</span>\n')
        elif self.iCryptSize < 12:
            sMainText += ('<span foreground = "red">Less than 12 Crypt Cards'
                          '</span>\n')

        if self.dCryptStats['max group'] - self.dCryptStats['min group'] > 1:
            sMainText += ('<span foreground = "red">Group Range Exceeded'
                          '</span>\n')

        if self.dTypeNumbers['Not Tournament Legal Cards'] > 0:
            sMainText += ('<span foreground = "red">Card Set uses cards that '
                          'are not legal for tournament play</span>\n')

        if bRapid and self.dTypeNumbers[RT_BANNED]:
            sMainText += ('<span foreground = "red">Card Set uses cards that '
                          'are not legal for rapid thought play</span>\n')

        if bRapid and self.dTypeNumbers[RT_WATCHLIST]:
            sMainText += ('<span foreground = "yellow">Card Set uses cards '
                          'that are on the rapid thoughts watchlist</span>\n')

        if self.iCryptSize > 0:
            sMainText += ('\nMaximum cost in crypt = %d\n' %
                          self.dCryptStats['max cost'])
            sMainText += ('Minimum cost in crypt = %d\n' %
                          self.dCryptStats['min cost'])
        fAvg, fAvgDraw = _crypt_avg(self.dCryptStats['total cost'],
                                    self.iCryptSize)

        sMainText += ('Average cost = %3.2f (%3.2f average crypt draw cost)\n'
                      % (fAvg, fAvgDraw))
        sMainText += 'Minimum draw cost = %d\n' % self.dCryptStats['min draw']
        sMainText += 'Maximum Draw cost = %d\n' % self.dCryptStats['max draw']

        sMainText += "Total Library Size = %d\n" % self.iLibSize

        if self.iLibSize < 40:
            sMainText += ('<span foreground = "red">Less than 40 Library'
                          ' Cards</span>\n')
        elif self.iLibSize < 60 and not bRapid:
            sMainText += ('<span foreground = "orange">Less than 60 Library'
                          ' Cards - this deck is not legal for standard'
                          ' constructed tournaments</span>')
        elif self.iLibSize > 90:
            sMainText += ('<span foreground = "orange">More than 90 Library'
                          ' Cards - this deck is not legal for standard'
                          ' constructed tournaments</span>\n')

        return wrap(sTitleText), oScrolledBox, wrap(sMainText)
    # pylint: enable=too-many-branches

    def _process_library(self):
        """Create a notebook for the basic library card overview"""
        oLibNotebook = Gtk.Notebook()
        # Stats by card type
        sTypeText = ''
        # Show card types, sorted by number (then alphabetical by type)
        for sType, iCount in sorted(self.dTypeNumbers.items(),
                                    key=lambda x: (x[1], x[0]), reverse=True):
            if sType not in CRYPT_TYPES and sType not in SPECIAL and \
                    iCount > 0:
                sTypeText += _format_card_line(sType, 'cards', iCount,
                                               self.iLibSize)
        if self.dTypeNumbers['Multirole'] > 0:
            sTypeText += '\n' + _format_card_line(
                'Multirole', 'cards', self.dTypeNumbers['Multirole'],
                self.iLibSize)
        oLibNotebook.append_page(wrap(sTypeText),
                                 Gtk.Label(label='Card Types'))
        # Stats by discipline
        sDiscText = _format_card_line('Master', 'cards',
                                      self.dTypeNumbers['Master'],
                                      self.iLibSize)
        sDiscText += _format_card_line(
            'non-master cards with No ' 'discipline requirement', '',
            self.dLibStats['discipline']['No Discipline'],
            self.iLibSize) + '\n'
        # sort by number, then name
        for sDisc, iNum in sorted(self.dLibStats['discipline'].items(),
                                  key=lambda x: (x[1], x[0]), reverse=True):
            if sDisc != 'No Discipline' and iNum > 0:
                sDiscDesc = 'non-master cards with %s' % sDisc
                sDiscText += _format_card_line(sDiscDesc, '', iNum,
                                               self.iLibSize)
        oLibNotebook.append_page(wrap(sDiscText),
                                 Gtk.Label(label='Disciplines'))
        # Stats by clan requirement
        sClanText = _format_card_line('cards with No clan requirement', '',
                                      self.dLibStats['clan']['No Clan'],
                                      self.iLibSize) + '\n'
        for sClan, iNum in sorted(self.dLibStats['clan'].items()):
            if sClan != 'No Clan' and iNum > 0:
                sClanDesc = 'cards requiring %s' % sClan
                sClanText += _format_card_line(sClanDesc, '', iNum,
                                               self.iLibSize)
        oLibNotebook.append_page(wrap(sClanText),
                                 Gtk.Label(label='Clan Requirements'))
        return oLibNotebook

    def _process_vampire(self, aCards):
        """Process the list of vampires"""
        dDeckDetails = {
            'vampires': {},
            'titles': {},
            'clans': {},
            'sects': {},
            'votes': 0,
        }
        iNum = self.dTypeNumbers['Vampire']
        for oAbsCard in aCards:
            dDeckDetails['vampires'].setdefault(oAbsCard.name, 0)
            dDeckDetails['vampires'][oAbsCard.name] += 1
            for oClan in oAbsCard.clan:
                dDeckDetails['clans'].setdefault(oClan, 0)
                dDeckDetails['clans'][oClan] += 1
            for oSect in oAbsCard.sect:
                dDeckDetails['sects'].setdefault(oSect, 0)
                dDeckDetails['sects'][oSect] += 1
            for oTitle in oAbsCard.title:
                dDeckDetails['titles'].setdefault(oTitle, 0)
                dDeckDetails['titles'][oTitle] += 1
                dDeckDetails['votes'] += Titles.vote_value(oTitle.name)
        # Build up Text
        sVampText = "\t\t<b>Vampires :</b>\n\n"
        sVampText += '<span foreground = "blue">Basic Crypt stats</span>\n'
        sVampText += ("Number of Vampires = %d %s\n" %
                      (iNum, _percentage(iNum, self.iCryptSize, "Crypt")))
        sVampText += ("Number of Unique Vampires = %d\n" %
                      len(dDeckDetails['vampires']))
        sVampText += ("Minimum Group is : %d\n" %
                      self.dCryptStats['vampire min group'])
        sVampText += ("Maximum Group is : %d\n" %
                      self.dCryptStats['vampire max group'])
        sVampText += '\n<span foreground = "blue">Crypt cost</span>\n'
        sVampText += ("Cheapest is : %d\n" %
                      self.dCryptStats['vampire min cost'])
        sVampText += ("Most Expensive is : %d\n" %
                      self.dCryptStats['vampire max cost'])
        sVampText += ("Average Capacity is : %2.3f\n\n" %
                      (sum([x.capacity for x in aCards]) / float(iNum)))
        sVampText += '<span foreground = "blue">Clans</span>\n'
        for oClan, iCount in dDeckDetails['clans'].items():
            sVampText += ("%d Vampires of clan %s %s\n" %
                          (iCount, oClan.name,
                           _percentage(iCount, self.iCryptSize, "Crypt")))
        sVampText += '<span foreground = "blue">Sects</span>\n'
        for oSect, iCount in dDeckDetails['sects'].items():
            sVampText += ("%d %s vampires %s\n" %
                          (iCount, oSect.name,
                           _percentage(iCount, self.iCryptSize, "Crypt")))
        sVampText += '\n<span foreground = "blue">Titles</span>\n'
        iTotalTitles = 0
        for oTitle, iCount in dDeckDetails['titles'].items():
            sVampText += ("%d vampires with the title %s (%d votes)\n" %
                          (iCount, oTitle.name,
                           Titles.vote_value(oTitle.name)))
            iTotalTitles += iCount
        sVampText += ("%d vampires with titles (%s)\n" %
                      (iTotalTitles, _percentage(iTotalTitles,
                                                 self.iCryptSize, "Crypt")))
        sVampText += ("%d votes from titles in the crypt. Average votes per"
                      " vampire is %2.3f\n" %
                      (dDeckDetails['votes'],
                       dDeckDetails['votes'] / float(iNum)))
        sVampText += '\n<span foreground = "blue">Disciplines</span>\n'
        for oDisc, aInfo in sorted(
                self.dCryptStats['crypt discipline'].items(),
                key=_disc_sort_key):
            if aInfo[0] == 'discipline':
                sVampText += ("%(infcount)d Vampires with %(disc)s %(iper)s,"
                              " %(supcount)d at Superior %(sper)s\n" % {
                                  'disc': oDisc.fullname,
                                  'infcount': aInfo[1],
                                  'iper': _percentage(aInfo[1],
                                                      self.iCryptSize,
                                                      "Crypt"),
                                  'supcount': aInfo[2],
                                  'sper': _percentage(aInfo[2],
                                                      self.iCryptSize,
                                                      "Crypt"),
                              })
        return sVampText

    def _process_imbued(self, aCards):
        """Fill the Imbued tab"""
        dDeckImbued = {}
        dDeckCreed = {}
        iNum = self.dTypeNumbers['Imbued']
        for oAbsCard in aCards:
            dDeckImbued.setdefault(oAbsCard.name, 0)
            dDeckImbued[oAbsCard.name] += 1
            for oCreed in oAbsCard.creed:
                dDeckCreed.setdefault(oCreed, 0)
                dDeckCreed[oCreed] += 1
        # Build up Text
        sImbuedText = "\t\t<b>Imbued</b>\n\n"
        sImbuedText += '<span foreground = "blue">Basic Crypt stats</span>\n'
        sImbuedText += "Number of Imbued = %d %s\n" % (
            iNum, _percentage(iNum, self.iCryptSize, "Crypt"))
        sImbuedText += "Number of Unique Imbued = %d\n" % len(dDeckImbued)
        sImbuedText += ('Minimum Group is : %d\n' %
                        self.dCryptStats['imbued min group'])
        sImbuedText += ('Maximum Group is : %d\n' %
                        self.dCryptStats['imbued max group'])
        sImbuedText += '\n<span foreground = "blue">Crypt cost</span>\n'
        sImbuedText += ("Cheapest is : %d\n" %
                        self.dCryptStats['imbued min cost'])
        sImbuedText += ("Most Expensive is : %d\n" %
                        self.dCryptStats['imbued max cost'])
        sImbuedText += "Average Life is : %2.3f\n\n" % (
            sum([x.life for x in aCards]) / float(iNum))
        for oCreed, iCount in dDeckCreed.items():
            sImbuedText += "%d Imbued of creed %s %s\n" % (
                iCount, oCreed.name, _percentage(iCount, self.iCryptSize,
                                                 "Crypt"))
        for oVirtue, aInfo in sorted(
                self.dCryptStats['crypt discipline'].items(),
                key=_disc_sort_key):
            if aInfo[0] == 'virtue':
                sImbuedText += "%d Imbued with %s %s\n" % (
                    aInfo[1], oVirtue.fullname, _percentage(aInfo[1],
                                                            self.iCryptSize,
                                                            "Crypt"))
        return sImbuedText

    def _process_master(self, aCards):
        """Display the stats for Master Cards"""
        iNum = self.dTypeNumbers['Master']
        _aBlood, aPool, _aConviction = _get_card_costs(aCards)
        iClanRequirement, dClan, dMulti = _get_card_clan_multi(aCards)
        # Build up Text
        sText = "\t\t<b>Master Cards :</b>\n\n"
        sText += "Number of Masters = %d %s\n" % (
            iNum, _percentage(iNum, self.iLibSize, "Library"))
        # Extract the number of out-of-turn and trifles
        for sType in ('trifle', 'out-of-turn'):
            try:
                oKeyword = IKeyword(sType)
                iCount = 0
                for oCard in aCards:
                    if oKeyword in oCard.keywords:
                        iCount += 1
                if iCount:
                    sText += '   Number of %s masters = %d (%s)\n' % (
                        sType, iCount, _percentage(iCount, iNum, 'Masters'))
            except SQLObjectNotFound:
                sText += ('<span foreground="red">Keyword <b>%s</b> not '
                          'in the database -- please re-import the WW '
                          'cardlist</span>\n' % sType)
        if aPool[1] > 0:
            sText += '\n<span foreground = "blue">Cost</span>\n'
            sText += _format_cost_numbers('Master', 'pool', aPool, iNum)
        if iClanRequirement > 0:
            sText += '\n<span foreground = "blue">Clan/Creed</span>\n'
            sText += _format_clan('Master', iClanRequirement, dClan, iNum)
        if dMulti:
            sText += '\n' + _format_multi('Master', dMulti, iNum)
        return sText

    def _default_text(self, aCards, sType):
        """Standard boilerplate for most card types"""
        iNum = self.dTypeNumbers[sType]
        aBlood, aPool, aConviction = _get_card_costs(aCards)
        iClanRequirement = 0
        dDisciplines, dVirtues, iNoneCount = _get_card_disciplines(aCards)
        iClanRequirement, dClan, dMulti = _get_card_clan_multi(aCards)
        # Build up Text
        sPerCards = _percentage(iNum, self.iLibSize, 'Library')
        sText = ("\t\t<b>%(type)s Cards :</b>\n\n"
                 "Number of %(type)s cards = %(num)d %(per)s\n" % {
                     'type': sType,
                     'num': iNum,
                     'per': sPerCards,
                 })
        if aBlood[1] > 0 or aPool[1] > 0 or aConviction[1] > 0:
            sText += '\n<span foreground = "blue">Costs</span>\n'
        if aBlood[1] > 0:
            sText += _format_cost_numbers(sType, 'blood', aBlood, iNum)
        if aConviction[1] > 0:
            sText += _format_cost_numbers(sType, 'conviction', aConviction,
                                          iNum)
        if aPool[1] > 0:
            sText += _format_cost_numbers(sType, 'pool', aPool, iNum)
        if iClanRequirement > 0:
            sText += '\n<span foreground = "blue">Clan/Creed</span>\n'
            sText += _format_clan(sType, iClanRequirement, dClan, iNum)
        sText += '\n<span foreground = "blue">Discipline/Virtues</span>\n'
        sText += ('Number of cards with no discipline/virtue requirement = '
                  '%d\n' % iNoneCount)
        if dDisciplines:
            sText += _format_disciplines('discipline', dDisciplines)
        if dVirtues:
            sText += _format_disciplines('virtue', dVirtues)
        if dMulti:
            sText += '\n' + _format_multi(sType, dMulti, iNum)
        return sText

    def _process_combat(self, aCards):
        """Fill the combat tab"""
        sText = self._default_text(aCards, 'Combat')
        return sText

    def _process_action_modifier(self, aCards):
        """Fill the Action Modifier tab"""
        sText = self._default_text(aCards, 'Action Modifier')
        return sText

    def _process_reaction(self, aCards):
        """Fill the reaction tab"""
        sText = self._default_text(aCards, 'Reaction')
        return sText

    def _process_event(self, aCards):
        """Fill the events tab"""
        iNumEvents = len(aCards)
        sEventText = "\t\t<b>Event Cards :</b>\n\n"
        sEventText += "Number of Event cards = %d %s\n\n" % (
            iNumEvents, _percentage(iNumEvents, self.iLibSize, "Library"))
        sEventText += '<span foreground = "blue">Event classes</span>\n'
        dEventTypes = {}
        for oCard in aCards:
            sType = oCard.text.split('.', 1)[0]  # first word is type
            dEventTypes.setdefault(sType, 0)
            dEventTypes[sType] += 1
        for sType, iCount in dEventTypes.items():
            sEventText += '%d of type %s : %s (%s) \n' % (
                iCount, sType, _percentage(iCount, iNumEvents, 'Events'),
                _percentage(iCount, self.iLibSize, 'Library'))
        return sEventText

    def _process_action(self, aCards):
        """Fill the actions tab"""
        sText = self._default_text(aCards, 'Action')
        return sText

    def _process_political_action(self, aCards):
        """Fill the Political Actions tab"""
        sText = self._default_text(aCards, 'Political Action')
        return sText

    def _process_allies(self, aCards):
        """Fill the allies tab"""
        sText = self._default_text(aCards, 'Ally')
        return sText

    def _process_retainer(self, aCards):
        """Fill the retainer tab"""
        sText = self._default_text(aCards, 'Retainer')
        return sText

    def _process_equipment(self, aCards):
        """Fill the equipment tab"""
        sText = self._default_text(aCards, 'Equipment')
        return sText

    def _process_conviction(self, aCards):
        """Fill the conviction tab"""
        sText = self._default_text(aCards, 'Conviction')
        return sText

    def _process_power(self, aCards):
        """Fill the power tab"""
        sText = self._default_text(aCards, 'Power')
        return sText

    def _process_multi(self, aCards):
        """Fill the multirole card tab"""
        dMulti = {}
        sPerCards = _percentage(self.dTypeNumbers['Multirole'], self.iLibSize,
                                'Library')
        sText = ("\t\t<b>Multirole Cards :</b>\n\n"
                 "Number of Multirole cards = %(num)d %(per)s\n" % {
                     'num': self.dTypeNumbers['Multirole'],
                     'per': sPerCards,
                 })
        for oAbsCard in aCards:
            aTypes = [x.name for x in oAbsCard.cardtype]
            if len(aTypes) > 1:
                sKey = "/".join(sorted(aTypes))
                dMulti.setdefault(sKey, 0)
                dMulti[sKey] += 1
        for sMultiType, iNum in sorted(dMulti.items(), key=lambda x: x[1],
                                       reverse=True):
            sPer = _percentage(iNum, self.iLibSize, 'Library')
            sText += 'Number of %(multitype)s cards = %(num)d %(per)s\n' % {
                'multitype': sMultiType,
                'num': iNum,
                'per': sPer,
            }

        return sText

    def _process_non_legal(self, aCards, sType='Not Tournament Legal Cards'):
        """Fill the non_legal card tab"""
        iTotal = self.iCryptSize + self.iLibSize
        dNonLegal = {}
        sPerCards = _percentage(self.dTypeNumbers[sType], iTotal, 'Deck')
        sText = ("\t\t<b>%(type)s :</b>\n\n"
                 "Number of cards %(lowertype)s ="
                 " %(num)d %(per)s\n" % {
                     'type': ILLEGAL_LOOKUP[sType],
                     'lowertype': ILLEGAL_LOOKUP[sType].lower(),
                     'num': self.dTypeNumbers[sType],
                     'per': sPerCards,
                 })
        for oAbsCard in aCards:
            dNonLegal.setdefault(oAbsCard.name, 0)
            dNonLegal[oAbsCard.name] += 1
        for sName, iNum in sorted(dNonLegal.items(), key=lambda x: x[1],
                                  reverse=True):
            sText += '%(num)d X %(name)s\n' % {
                'num': iNum,
                'name': sName,
            }

        return sText

    def _check_crypt_backs(self, dCrypt, aCrypt):
        """Check the backs on the crypt cards"""
        sText = "\t<b>Crypt</b>\n\n"
        sAddText = _simple_back_checks(dCrypt, 'Crypt')
        bOK = True
        if sAddText:
            sText += sAddText
            return sText
        sAddText, bOK = _percentage_backs(dCrypt, self.iCryptSize, 20.0,
                                          'Crypt')
        if sAddText:
            sText += sAddText
        sAddText, _aCryptByExp = _group_backs(dCrypt, aCrypt, 3, self._dBacks)
        if sAddText:
            sText += sAddText
            bOK = False
        if bOK:
            sText += "Mixed backs, but seems sufficiently mixed.\n"
            sText += UNSLEEVED % "Crypt"
        else:
            sText += SLEEVED % "Crypt"

        return sText

    def _check_lib_backs(self, dLib, aLib):
        """Check the card backs for the library"""
        sText = "\n\t<b>Library</b>\n\n"
        sAddText = _simple_back_checks(dLib, 'Library')
        bOK = True
        if sAddText:
            sText += sAddText
            return sText
        sAddText, bOK = _percentage_backs(dLib, self.iLibSize, 20.0, 'Library')
        if sAddText:
            sText += sAddText
        sAddText, aLibByExp = _group_backs(dLib, aLib, 5, self._dBacks)
        if sAddText:
            sText += sAddText
            bOK = False
        for aExpCards in aLibByExp:
            # if a single back contains less than 3 types of library card
            aAllTypes = set()
            for oCard in aExpCards:
                aTypes = [y.name for y in oCard.abstractCard.cardtype]
                aAllTypes.add("/".join(aTypes))
            if len(aAllTypes) < 3:
                aNames = {x.abstractCard.name for x in aExpCards}
                sText += ("Group of cards with the same back"
                          " containing less than 3 different card types.\n")
                sText += "\t" + ", ".join(aNames) + "\n"
                bOK = False
        if bOK:
            sText += "Mixed backs, but seems sufficiently mixed.\n"
            sText += UNSLEEVED % "Library"
        else:
            sText += SLEEVED % "Library"

        return sText

    def _process_backs(self, aPhysCards):
        """Run some heuristic tests to see if cards are 'of sufficiently
           mixed card type'"""
        aCrypt, aLib = _split_into_crypt_lib(aPhysCards)
        dCrypt = _get_back_counts(aCrypt, self._dBacks)
        dLib = _get_back_counts(aLib, self._dBacks)
        sText = "\t\t<b>Mixed Card Backs :</b>\n\n"
        # PDF trumps none
        if 'PDF' in dCrypt or 'PDF' in dLib:
            sText += ("Cards from a V:EKN released pdf set in the deck. "
                      "The V:EKN requires that these cards be sleeved in "
                      "opaque sleeves with a existing VtES card\n")
        elif None in dCrypt and None in dLib:
            sText += ("Both library and crypt have cards with unspecified"
                      " expansions.\nIgnoring the mixed backs.\n")
            return sText
        else:
            # We know there are mixed cards, when we get here.
            sText += ("Mixed card backs in the deck. The V:EKN rules require "
                      "that a mixed deck be of 'sufficiently mixed card "
                      "types' if it's to be played without sleeves. This "
                      "tests some obvious cases, but check with the event "
                      "judge if playing without sleeves\n\n")
        sText += self._check_crypt_backs(dCrypt, aCrypt)
        sText += self._check_lib_backs(dLib, aLib)
        return sText

    def happy_families_init(self, oHFVBox, oDlg):
        """Setup data and tab for HF analysis"""
        oMainLabel = Gtk.Label()
        oHFVBox.pack_start(oMainLabel, False, True, 0)
        # Build up Text
        sHappyFamilyText = "\t\t<b>Happy Families Analysis :</b>\n"
        sHappyFamilyText += ("\t<small><i>Happy Families Analysis from the "
                             "Gangrel antitribu newsletter, Jan 2000, by "
                             "Legbiter</i></small>\n")
        if self.dTypeNumbers['Imbued'] > 0:
            sHappyFamilyText += ('\n<span foreground = "red">This is not'
                                 ' optimised for Imbued, and treats them'
                                 ' as small vampires</span>\n')
        if self.dTypeNumbers['Event'] > 0:
            sHappyFamilyText += ('\n<span foreground = "red">Events are'
                                 ' not considered by Happy Families. We'
                                 ' treat them as additional masters.</span>')
        if self.iCryptSize == 0:
            sHappyFamilyText += ('\n<span foreground = "red">Need to have'
                                 ' a crypt to do the analysis</span>\n')
            oMainLabel.set_markup(sHappyFamilyText)
            oHFVBox.show_all()
            return
        if len(self.dCryptStats['crypt discipline']) < 1:
            # Crypt only has Smudge, for example
            sHappyFamilyText += ('\n<span foreground = "red">Need disciplines'
                                 ' in the crypt to do analysis</span>\n')
            oMainLabel.set_markup(sHappyFamilyText)
            oHFVBox.show_all()
            return
        # OK, for analysis, so set eveything up
        # Masters analysis
        iHFMasters = int(round(0.2 * self.iLibSize))
        iLibMasters = self.dTypeNumbers['Master'] + self.dTypeNumbers['Event']
        iNonMasters = (self.iLibSize - self.dTypeNumbers['Master']
                       - self.dTypeNumbers['Event'])
        sHappyFamilyText += "\n\t<b>Master Cards</b>\n"
        sHappyFamilyText += ("%d Masters %s\n" %
                             (self.dTypeNumbers['Master'],
                              _percentage(self.dTypeNumbers['Master'],
                                          self.iLibSize, "Library")))
        if self.dTypeNumbers['Event'] > 0:
            sHappyFamilyText += "%d Events %s\n" % (
                self.dTypeNumbers['Event'],
                _percentage(self.dTypeNumbers['Event'], self.iLibSize,
                            "Library"))
            sHappyFamilyText += "%d Total %s\n" % (
                iLibMasters,
                _percentage(iLibMasters, self.iLibSize, 'Library'))
        sHappyFamilyText += ("Happy Families recommends 20%, which would"
                             " be ") + str(iHFMasters) + '  : '
        sHappyFamilyText += ("<span foreground = \"blue\">Difference = " +
                             str(abs(iHFMasters - iLibMasters)) +
                             "</span>\n")
        # Discipline analysis
        aSortedDiscs = [x[0].fullname for x in sorted(
            self.dCryptStats['crypt discipline'].items(), key=_disc_sort_key)]
        oMainLabel.set_markup(sHappyFamilyText)
        oDiscSelect = DisciplineNumberSelect(aSortedDiscs, oDlg)
        oHFVBox.pack_start(oDiscSelect, False, False, 0)
        oResLabel = Gtk.Label()
        oButton = Gtk.Button(label='Recalculate Happy Family Analysis')
        oButton.connect('clicked', self._redo_happy_family, oDiscSelect,
                        oResLabel)
        oHFVBox.pack_start(oButton, False, False, 0)
        oResLabel.set_markup(self._happy_lib_analysis(aSortedDiscs[:2],
                                                      iNonMasters))
        oHFVBox.pack_start(oResLabel, False, True, 0)
        oHFVBox.show_all()

    def _redo_happy_family(self, _oButton, oDiscSelect, oResLabel):
        """Redo the HF analysis based on button press"""
        aTheseDiscs = oDiscSelect.get_disciplines()
        if not aTheseDiscs:
            return  # Just ignore the zero selection case
        iNonMasters = self.iLibSize - self.dTypeNumbers['Master']
        oResLabel.hide()
        oResLabel.set_markup(self._happy_lib_analysis(aTheseDiscs,
                                                      iNonMasters))
        oResLabel.show()
        oResLabel.get_parent().show_all()

    def _happy_lib_analysis(self, aDiscsToUse, iNonMasters):
        """Heavy lifting of the HF analysis"""

        iNumberToShow = len(aDiscsToUse)

        sHappyFamilyText = ("<b>" + str(iNumberToShow) +
                            " Discipline Case</b>\n")
        sHappyFamilyText += "Disciplines : <i>%s</i>\n" % ",".join(aDiscsToUse)
        fDemon = float(self.iCryptSize)
        dCryptDiscs = {}
        for sDisc in aDiscsToUse:
            oDisc = _lookup_discipline(sDisc,
                                       self.dCryptStats['crypt discipline'])
            dCryptDiscs[sDisc] = self.dCryptStats['crypt discipline'][oDisc][1]
            fDemon += dCryptDiscs[sDisc]
        iHFNoDiscipline = int((iNonMasters * self.iCryptSize / fDemon))
        iDiff = iNonMasters - iHFNoDiscipline
        dDiscNumbers = {}
        for sDisc in aDiscsToUse:
            iHFNumber = int(iNonMasters * dCryptDiscs[sDisc] / fDemon)
            dDiscNumbers[sDisc] = iHFNumber
            iDiff -= iHFNumber
        if iDiff > 0:
            iHFNoDiscipline += iDiff  # Shove rounding errors here
        sHappyFamilyText += ("Number of Minion cards requiring "
                             " No discipline : %s\n"
                             % (self.dLibStats['discipline']['No Discipline']
                                - self.dTypeNumbers['Master']
                                - self.dTypeNumbers['Event']))
        sHappyFamilyText += ("Happy Families recommends %d (%.1f %%): " %
                             (iHFNoDiscipline,
                              (80 * self.iCryptSize / fDemon)))
        sHappyFamilyText += ('<span foreground = "blue">Difference = '
                             '%s</span>\n\n' %
                             abs(iHFNoDiscipline -
                                 (self.dLibStats['discipline']['No Discipline']
                                  - self.dTypeNumbers['Master']
                                  - self.dTypeNumbers['Event'])))
        for sDisc in aDiscsToUse:
            iHFNum = dDiscNumbers[sDisc]
            if sDisc in self.dLibStats['discipline']:
                iLibNum = self.dLibStats['discipline'][sDisc]
            else:
                iLibNum = 0
            sHappyFamilyText += ("Number of Minion cards requiring %(disc)s :"
                                 " %(lib)d (%(crypt)d crypt members)\n" % {
                                     'disc': sDisc,
                                     'lib': iLibNum,
                                     'crypt': dCryptDiscs[sDisc],
                                 })
            sHappyFamilyText += ("Happy Families recommends %d (%.1f %%): " %
                                 (iHFNum, 80 * dCryptDiscs[sDisc] / fDemon))
            sHappyFamilyText += ('<span foreground = "blue">Difference = '
                                 '%d </span>\n' % abs(iHFNum - iLibNum))
        return sHappyFamilyText


plugin = AnalyzeCardList
