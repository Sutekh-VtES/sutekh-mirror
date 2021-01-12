# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>,
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Plugin for analysing all clans and determining the discipline
   spreads of the vampires in each.
   """

from gi.repository import GObject, Gtk, Pango

from sqlobject import SQLObjectNotFound
from sutekh.base.core.BaseTables import PhysicalCard
from sutekh.base.core.BaseAdapters import ICardType, IKeyword
from sutekh.core.SutekhTables import Clan, SutekhAbstractCard
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.base.gui.SutekhDialog import SutekhDialog
from sutekh.base.gui.AutoScrolledWindow import AutoScrolledWindow


class ClanDisciplineStats(SutekhPlugin):
    """Display discipline spread for all clans.

       A dialog listing discipline spreads per clan is shown,
       along with useful stats about the disciline spread.
       The user can break down the analysis by vampire groups.
       """

    dTableVersions = {}
    aModelsSupported = (PhysicalCard,)

    sMenuName = "Clan Discipline Stats"

    sHelpCategory = "card_list:analysis"

    sHelpText = """This shows an analysis of all the different clans in the
                   White Wolf card list. For each clan, it displays the total
                   number of vampires in the clan, the sum of the
                   vampires&#8217; capacities, and the most common disciplines.
                   It also shows the score for the disciplines, and various
                   stats about how the disciplines are distributed.

                   You can expand the tree view to show the details for each
                   legal grouping combination.

                   The score is intended to give you some indication of how
                   common disciplines are within the clan. Vampires without
                   a discipline score 0 for that discipline, vampires with
                   the inferior discipline score 1 and vampires with the
                   superior discipline score 2.

                   Note that this will only include cards not legal for
                   tournament play (such as banned cards or storyline only
                   cards) if the current profile for the full card list shows
                   those cards."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._oStatsVbox = None

    def get_menu_item(self):
        """Register on the 'Analyze' menu"""
        oClanStats = Gtk.MenuItem(label=self.sMenuName)
        oClanStats.connect("activate", self.activate)
        return ('Analyze', oClanStats)

    def activate(self, _oWidget):
        """Handle response from menu"""
        oDlg = self.make_dialog()
        oDlg.run()
        self._oStatsVbox = None

    def make_dialog(self):
        """Create the dialog to display the statistics"""
        oDlg = SutekhDialog("Clan Vampire Statistics", self.parent,
                            Gtk.DialogFlags.DESTROY_WITH_PARENT)

        oDlg.add_button("_Close", Gtk.ResponseType.CLOSE)
        oDlg.connect("response", lambda oW, oR: oDlg.destroy())

        self._oStatsVbox = Gtk.VBox(homogeneous=False, spacing=0)

        # pylint: disable=no-member
        # vbox methods not seen
        oDlg.vbox.pack_start(self._oStatsVbox, False, True, 0)
        oDlg.set_size_request(600, 400)
        oDlg.show_all()

        self.populate_stats_box()

        return oDlg

    def populate_stats_box(self):
        """Create a tree view of stats in self._oStatsVbox."""
        # clean box
        for oChild in self._oStatsVbox.get_children():
            self._oStatsVbox.remove(oChild)

        oView = StatsView(self.model.hideillegal)

        # top align, using viewport to scroll
        self._oStatsVbox.pack_start(AutoScrolledWindow(oView), True, True, 0)
        self._oStatsVbox.show_all()


class GroupStats:
    """Manage statistics for a set of vampire groups."""

    def __init__(self):
        self.iVamps = 0
        self.iTotalCapacity = 0
        self.dDisciplines = {}
        # format { oId: [oDis, superior cnt, inferior cnt, score] }

    def add_vamp(self, oVamp):
        """Process a single vampire from the group and clan"""
        self.iVamps += 1
        self.iTotalCapacity += oVamp.capacity
        for oPair in oVamp.discipline:
            oDis = oPair.discipline
            aStats = self.dDisciplines.get(oDis.id, [oDis, 0, 0, 0])

            # Score 1 for inf discipline, 2 for sup
            if oPair.level == "inferior":
                aStats[2] += 1
                aStats[3] += 1
            else:
                aStats[1] += 1
                aStats[3] += 2

            self.dDisciplines[oDis.id] = aStats

    def top_n(self, iNum):
        """Return the iNum highest scoring stats"""
        aScores = [(oId, aStats[3]) for oId, aStats in
                   self.dDisciplines.items()]
        aScores.sort(key=lambda x: x[1])
        aScores.reverse()
        aScores = aScores[:iNum]
        return [self.dDisciplines[oId] for oId, _iScore in aScores]


class ClanStats:
    """Manage combined statistics for a clan"""

    def __init__(self, iMaxGrp):
        # Set of all vampires
        self.oAllStats = GroupStats()
        # group pairs
        self.dSubStats = {}
        for iGrp in range(1, iMaxGrp):
            self.dSubStats[(iGrp, iGrp + 1)] = GroupStats()

    def add_vamp(self, oVamp):
        """Process a vampire to the total"""
        self.oAllStats.add_vamp(oVamp)
        for tGrps, oStats in self.dSubStats.items():
            if oVamp.group in tGrps:
                oStats.add_vamp(oVamp)


class StatsView(Gtk.TreeView):
    # pylint: disable=too-many-public-methods
    # Gtk classes, so we have lots of public methods
    """TreeView used to display clan discipline stats"""

    def __init__(self, bHideIllegal):
        self._oModel = StatsModel(bHideIllegal)
        self._aLabels = [
            "Clan", "Groups", "#", "Total Cap.", "Top 5 Disps.",
            "# Sup / # Inf", "Score", "Score / Vamp", "Score / Total Cap.",
        ]

        super().__init__(self._oModel)

        oCell = Gtk.CellRendererText()
        oCell.set_property('style', Pango.Style.ITALIC)

        for iCol, sLabel in enumerate(self._aLabels):
            oColumn = Gtk.TreeViewColumn(sLabel, oCell, text=iCol)
            oColumn.set_sort_column_id(iCol)
            self.append_column(oColumn)

        self.set_grid_lines(Gtk.TreeViewGridLine._BOTH)


class StatsModel(Gtk.TreeStore):
    # pylint: disable=too-many-public-methods
    # Gtk classes, so we have lots of public methods
    """TreeStore to hold the data about the clan statistics"""

    def __init__(self, bHideIllegal):
        super().__init__(GObject.TYPE_STRING, GObject.TYPE_STRING,
                         GObject.TYPE_INT, GObject.TYPE_INT,
                         *[GObject.TYPE_STRING] * 5)
        self.oExcludedKeyword = None
        if bHideIllegal:
            try:
                self.oExcludedKeyword = IKeyword('not for legal play')
            except SQLObjectNotFound:
                self.oExcludedKeyword = None

        self.load()

    def load(self):
        """Populate the contents of the TreeStore"""
        self.clear()

        for oClan, oClanStats in self.gather_stats():
            oClanIter = self.append(None)
            self.set_iter_values(oClanIter, oClan, None, oClanStats.oAllStats)

            # pylint: disable=invalid-name
            # atGrps doesn't match the regexp, but is a valid name
            atGrps = list(oClanStats.dSubStats.keys())
            atGrps.sort()

            for tGrps in atGrps:
                oSubStats = oClanStats.dSubStats[tGrps]
                if oSubStats.iVamps:
                    oIter = self.append(oClanIter)
                    self.set_iter_values(oIter, oClan, tGrps, oSubStats)

    def set_iter_values(self, oIter, oClan, tGrps, oGrpStats):
        """Fill in the the values for the newly added row oIter"""
        if tGrps:
            sGrps = ",".join([str(i) for i in tGrps])
        else:
            sGrps = None
        aTopN = oGrpStats.top_n(5)
        sDisps = " ".join([x[0].name.upper() for x in aTopN])
        sSupInfCnts = " ".join(["%d/%d" % (x[1], x[2]) for x in aTopN])
        sScores = " ".join([str(x[3]) for x in aTopN])
        sScoresPerVamp = " ".join(["%.2f" % (float(x[3]) / oGrpStats.iVamps)
                                   for x in aTopN])
        sScoresPerCap = " ".join(["%.2f" % (float(x[3]) /
                                            oGrpStats.iTotalCapacity)
                                  for x in aTopN])

        self.set(oIter,
                 0, oClan.name,
                 1, sGrps,
                 2, oGrpStats.iVamps,
                 3, oGrpStats.iTotalCapacity,
                 4, sDisps,
                 5, sSupInfCnts,
                 6, sScores,
                 7, sScoresPerVamp,
                 8, sScoresPerCap,
                )

    def gather_stats(self):
        """Collect up information on vampires from all clans."""
        # pylint: disable=no-member
        # avoid SQLObject method not detected problems
        iMaxGrp = SutekhAbstractCard.select().max(SutekhAbstractCard.q.group)

        aClans = list(Clan.select())
        aClans.sort(key=lambda x: x.name)

        for oClan in aClans:
            yield (oClan, self.gather_clan_stats(oClan, iMaxGrp))

    # pylint: disable=no-self-use
    # could be a function, but that doesn't add to clarity
    def gather_clan_stats(self, oClan, iMaxGrp):
        """Collect information on vampires from a particular clan."""
        oVampType = ICardType("Vampire")
        oClanStats = ClanStats(iMaxGrp)

        for oCard in oClan.cards:
            if oVampType in oCard.cardtype:
                if self.oExcludedKeyword is None or \
                        self.oExcludedKeyword not in oCard.keywords:
                    oClanStats.add_vamp(oCard)

        return oClanStats


plugin = ClanDisciplineStats
