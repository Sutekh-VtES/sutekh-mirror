# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Allow the use to change how the cards are grouped in the CardListView"""

from sutekh.core.Groupings import (ClanGrouping, DisciplineGrouping,
                                   CryptLibraryGrouping, SectGrouping,
                                   TitleGrouping, CostGrouping, GroupGrouping,
                                   GroupPairGrouping, DisciplineLevelGrouping)

from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.base.gui.plugins.BaseChangeGroupBy import BaseGroupBy


class GroupCardList(SutekhPlugin, BaseGroupBy):
    """Plugin to allow the user to change how cards are grouped."""

    # This feels a bit hack'ish - is there a better approach
    GROUPINGS = BaseGroupBy.GROUPINGS.copy()  # Should this be a copy?
    GROUPINGS.update({
        'Crypt or Library': CryptLibraryGrouping,
        'Clans and Creeds': ClanGrouping,
        'Disciplines and Virtues': DisciplineGrouping,
        'Disciplines (by level) and Virtues': DisciplineLevelGrouping,
        'Sect': SectGrouping,
        'Title': TitleGrouping,
        'Cost': CostGrouping,
        'Group': GroupGrouping,
        'Group pairs': GroupPairGrouping,
    })


plugin = GroupCardList
