# ClanDisciplineStats.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>,
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Plugin for analysing all clans and determining the discipline
   spreads of the vampires in each.
   """

import gtk
import pango
import gobject
from sutekh.core.SutekhObjects import AbstractCard, Clan, ICardType
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import SutekhDialog
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow

class ClanDisciplineStats(CardListPlugin):
    dTableVersions = {}
    aModelsSupported = [AbstractCard]

    def __init__(self,*args,**kws):
        super(ClanDisciplineStats,self).__init__(*args,**kws)

    def get_menu_item(self):
        if not self.check_versions() or not self.check_model_type():
            return None
        iClanStats = gtk.MenuItem("Clan Discipline Stats")
        iClanStats.connect("activate", self.activate)
        return iClanStats

    def get_desired_menu(self):
        return "Plugins"

    def activate(self,oWidget):
        oDlg = self.make_dialog()
        oDlg.run()
        self._oStatsVbox = None

    def make_dialog(self):
        oDlg = SutekhDialog("Clan Vampire Statistics",self.parent,
                gtk.DIALOG_DESTROY_WITH_PARENT)

        oDlg.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        oDlg.connect("response", lambda oW, oR: oDlg.destroy())

        self._oStatsVbox = gtk.VBox(False,0)

        oDlg.vbox.pack_start(self._oStatsVbox)
        oDlg.set_size_request(600, 400)
        oDlg.show_all()

        self.populate_stats_box()

        return oDlg

    def populate_stats_box(self):
        """Create a tree view of stats in self._oStatsVbox.
           """
        # clean box
        for oChild in self._oStatsVbox.get_children():
            self._oStatsVbox.remove(oChild)

        oView = StatsView()

        self._oStatsVbox.pack_start(AutoScrolledWindow(oView,True)) # top align, using viewport to scroll
        self._oStatsVbox.show_all()

class GroupStats(object):
    def __init__(self):
        self.iVamps = 0
        self.iTotalCapacity = 0
        self.dDisciplines = {} # { oId: [oDis, superior cnt, inferior cnt, score] }

    def add_vamp(self,oVamp):
        self.iVamps += 1
        self.iTotalCapacity += oVamp.capacity
        for oPair in oVamp.discipline:
            oDis = oPair.discipline
            aStats = self.dDisciplines.get(oDis.id,[oDis,0,0,0])

            if oPair.level == "inferior":
                aStats[2] += 1
                aStats[3] += 1
            else:
                aStats[1] += 1
                aStats[3] += 2

            self.dDisciplines[oDis.id] = aStats

    def top_n(self,n):
        aScores = [(oId,aStats[3]) for oId, aStats in self.dDisciplines.items()]
        aScores.sort(key=lambda x: x[1])
        aScores.reverse()
        aScores = aScores[:n]
        return [self.dDisciplines[oId] for oId, iScore in aScores]

class ClanStats(object):
    def __init__(self):
        self.oAllStats = GroupStats()
        self.dSubStats = { (1,2): GroupStats(),
                           (2,3): GroupStats(),
                           (3,4): GroupStats(),
                           (4,5): GroupStats(),
                         }

    def add_vamp(self,oVamp):
        self.oAllStats.add_vamp(oVamp)
        for tGrps, oStats in self.dSubStats.items():
            if oVamp.group in tGrps:
                oStats.add_vamp(oVamp)

class StatsView(gtk.TreeView, object):
    def __init__(self):
        self._oModel = StatsModel()
        self._aLabels = [
            "Clan","Groups","#","Total Cap.","Top 5 Disps.","# Sup / # Inf",
            "Score", "Score / Vamp", "Score / Total Cap."
        ]

        super(StatsView, self).__init__(self._oModel)

        oCell = gtk.CellRendererText()
        oCell.set_property('style', pango.STYLE_ITALIC)

        for i, sLabel in enumerate(self._aLabels):
            oColumn = gtk.TreeViewColumn(sLabel, oCell, text=i)
            oColumn.set_sort_column_id(i)
            self.append_column(oColumn)

        if hasattr(self, 'set_grid_lines'):
            self.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)

class StatsModel(gtk.TreeStore):
    def __init__(self):
        super(StatsModel, self).__init__(gobject.TYPE_STRING, gobject.TYPE_STRING,
                                         gobject.TYPE_INT, gobject.TYPE_INT,
                                         *[gobject.TYPE_STRING]*5)
        self.load()

    def load(self):
        self.clear()

        for oClan, oClanStats in self.gather_stats():
            oClanIter = self.append(None)
            self.set_iter_values(oClanIter,oClan,None,oClanStats.oAllStats)

            atGrps = oClanStats.dSubStats.keys()
            atGrps.sort()

            for tGrps in atGrps:
                oSubStats = oClanStats.dSubStats[tGrps]
                if oSubStats.iVamps:
                    oIter = self.append(oClanIter)
                    self.set_iter_values(oIter,oClan,tGrps,oSubStats)

    def set_iter_values(self,oIter,oClan,tGrps,oGrpStats):
        if tGrps:
            sGrps = ",".join([str(i) for i in tGrps])
        else:
            sGrps = None

        aTopN = oGrpStats.top_n(5)
        sDisps = " ".join([x[0].name.upper() for x in aTopN])
        sSupInfCnts = " ".join(["%d/%d" % (x[1],x[2]) for x in aTopN])
        sScores = " ".join([str(x[3]) for x in aTopN])
        sScoresPerVamp = " ".join(["%.2f" % (float(x[3])/oGrpStats.iVamps) for x in aTopN])
        sScoresPerCap = " ".join(["%.2f" % (float(x[3])/oGrpStats.iTotalCapacity) for x in aTopN])

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
        """Collect up information on vampires from all clans.
           """
        aClans = list(Clan.select())
        aClans.sort(key = lambda x: x.name)

        for oClan in aClans:
            yield (oClan,self.gather_clan_stats(oClan))

    def gather_clan_stats(self,oClan):
        """Collect information on vampires from a particular clan.
           """
        oVampType = ICardType("Vampire")
        oClanStats = ClanStats()

        for oCard in oClan.cards:
            if oVampType in oCard.cardtype:
                oClanStats.add_vamp(oCard)

        return oClanStats


plugin = ClanDisciplineStats
