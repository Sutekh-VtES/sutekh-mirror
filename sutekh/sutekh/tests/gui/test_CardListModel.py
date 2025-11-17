# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Tests the Card List Model"""

import unittest

from sutekh.base.tests.GuiTestUtils import (count_second_level,
                                            count_all_cards,
                                            count_top_level,
                                            get_card_names,
                                            LocalTestListener)
from sutekh.base.core.BaseTables import PhysicalCard, AbstractCard
from sutekh.base.core.BaseAdapters import (IAbstractCard, IPhysicalCard,
                                           IExpansion)
from sutekh.base.core import BaseFilters
from sutekh.base.core.BaseGroupings import NullGrouping, CardTypeGrouping
from sutekh.base.gui.CardListModel import CardListModel
from sutekh.base.gui.MessageBus import MessageBus

from sutekh.gui.plugins.HideGroupSuffix import HideGroupSuffixPlugin

from sutekh.core.Groupings import CryptLibraryGrouping
from sutekh.tests.GuiSutekhTest import ConfigSutekhTest


class DummyMain(object):

    def __init__(self, oConfig):
        self._oConfig = oConfig

    config_file = property(fget=lambda self: self._oConfig)


class DummyView(object):

    def __init__(self, oConfig):
        self._oMain = DummyMain(oConfig)

    mainwindow = property(fget=lambda self: self._oMain)


class DummyButton(object):

    def __init__(self, bValue):
        self._bValue = bValue

    def get_active(self):
        return self._bValue


class CardListModelTests(ConfigSutekhTest):
    """Class for the test cases"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    def _init_hide_plugin(self, oModel):
        HideGroupSuffixPlugin.update_config()
        HideGroupSuffixPlugin.register_with_config(self.oConfig)
        self.oConfig.validate()
        oPlugin = HideGroupSuffixPlugin(DummyView(self.oConfig), oModel, PhysicalCard)
        return oPlugin

    def test_basic(self):
        """Set of simple tests of the Card List Model"""
        # pylint: disable=too-many-statements, too-many-locals
        # Want a long, sequential test case to minimise
        # repeated setups, so it has lots of lines + variables
        oModel = CardListModel(self.oConfig)
        # We test with illegal cards shown
        oModel.hideillegal = False
        oListener = LocalTestListener(oModel, True)
        self.assertFalse(oListener.bLoadCalled)
        oModel.load()
        self.assertTrue(oListener.bLoadCalled)
        aExpectedCards = set(AbstractCard.select())
        self.assertEqual(aExpectedCards, set(oListener.aCards))
        self.assertEqual(oModel.get_card_iterator(None).count(),
                         PhysicalCard.select().count())
        # The model as an entry for every AbstractCard and entries
        # below that for every PhysicalCard
        # Set grouping to None for these tests
        oModel.groupby = NullGrouping
        oModel.load()
        self.assertEqual(count_all_cards(oModel),
                         AbstractCard.select().count())
        self.assertEqual(count_second_level(oModel),
                         PhysicalCard.select().count())
        # Check without expansions
        oModel.bExpansions = False
        oModel.load()
        self.assertEqual(count_all_cards(oModel),
                         AbstractCard.select().count())
        self.assertEqual(count_second_level(oModel), 0)
        oModel.bExpansions = True
        oModel.groupby = CryptLibraryGrouping
        oModel.load()
        self.assertEqual(count_all_cards(oModel),
                         AbstractCard.select().count())
        self.assertEqual(count_second_level(oModel),
                         PhysicalCard.select().count())
        self.assertEqual(count_top_level(oModel), 2)
        # Test filtering
        # Test filter which selects nothing works
        oModel.selectfilter = BaseFilters.CardNameFilter('ZZZZZZZ')
        oModel.applyfilter = True
        oModel.load()
        self.assertEqual(count_top_level(oModel), 1)
        self.assertEqual(count_all_cards(oModel), 0)
        oModel.applyfilter = False
        oModel.load()
        self.assertEqual(count_all_cards(oModel),
                         AbstractCard.select().count())
        self.assertEqual(count_second_level(oModel),
                         PhysicalCard.select().count())
        self.assertEqual(count_top_level(oModel), 2)
        # Test card type
        oModel.selectfilter = BaseFilters.CardTypeFilter('Vampire')
        oModel.applyfilter = True
        oModel.load()
        self.assertEqual(count_top_level(oModel), 1)
        self.assertEqual(count_second_level(oModel),
                         oModel.get_card_iterator(
                             oModel.selectfilter).count())
        oModel.groupby = CardTypeGrouping
        oModel.load()
        self.assertEqual(count_top_level(oModel), 1)
        self.assertEqual(count_second_level(oModel),
                         oModel.get_card_iterator(
                             oModel.selectfilter).count())
        # Test path queries
        # The remain tests require a sorted model
        oModel.enable_sorting()
        oPath = '0:0:0'  # First expansion for the first card
        self.assertEqual(oModel.get_exp_name_from_path(oPath),
                         oModel.sUnknownExpansion)
        self.assertEqual(oModel.get_card_name_from_path(oPath),
                         u'Aabbt Kindred (Group 2)')
        tAll = oModel.get_all_from_path(oPath)
        self.assertEqual(tAll[0], u'Aabbt Kindred (Group 2)')
        self.assertEqual(tAll[1], oModel.sUnknownExpansion)
        self.assertEqual(tAll[2], 0)
        self.assertEqual(tAll[3], 2)
        oIter = oModel.get_iter(oPath)
        self.assertEqual(oModel.get_child_entries_from_iter(oIter), [])
        oPath = '0:0'  # First card
        self.assertEqual(oModel.get_exp_name_from_path(oPath), None)
        self.assertEqual(oModel.get_inc_dec_flags_from_path(oPath),
                         (False, False))
        oIter = oModel.get_iter(oPath)
        tAll = oModel.get_all_from_path(oPath)
        self.assertEqual(tAll[0], u'Aabbt Kindred (Group 2)')
        self.assertEqual(tAll[1], None)
        self.assertEqual(tAll[2], 0)
        self.assertEqual(tAll[3], 1)
        oAbbt = IAbstractCard(u'Aabbt Kindred (Group 2)')
        oFirst = IPhysicalCard((oAbbt, None))
        oSecond = IPhysicalCard((oAbbt, IExpansion('Final Nights')))
        self.assertEqual(oModel.get_child_entries_from_iter(oIter),
                         [(oFirst, 0), (oSecond, 0)])
        # Test that the different variants show correctly
        oPath = '0:30:0'  # Harold's position
        self.assertEqual(oModel.get_card_name_from_path(oPath),
                         u"Harold Zettler, Pentex Director (Group 4)")
        self.assertEqual(oModel.get_exp_name_from_path(oPath),
                         oModel.sUnknownExpansion)
        oPath = '0:30:1'
        self.assertEqual(oModel.get_card_name_from_path(oPath),
                         u"Harold Zettler, Pentex Director (Group 4)")
        self.assertEqual(oModel.get_exp_name_from_path(oPath),
                         "Third Edition")
        oPath = '0:30:2'
        self.assertEqual(oModel.get_card_name_from_path(oPath),
                         u"Harold Zettler, Pentex Director (Group 4)")
        self.assertEqual(oModel.get_exp_name_from_path(oPath),
                         "Third Edition (Sketch)")
        oListener.bLoadCalled = False
        # Test MessageBus clear does the right thing
        MessageBus.clear(oModel)
        oModel.load()
        self.assertFalse(oListener.bLoadCalled)

    def test_postfix(self):
        """Test that the postfix display option works as expected"""
        oModel = CardListModel(self.oConfig)
        oModel.load()
        aCards = get_card_names(oModel)
        self.assertEqual('The Path of Blood' in aCards, True)
        self.assertEqual('Path of Blood, The' in aCards, False)
        self.assertEqual('The Siamese (Group 2)' in aCards, True)
        self.assertEqual('Theo Bell (Group 2)' in aCards, True)
        self.assertEqual('Theo Bell (Group 2) (Advanced)' in aCards, True)
        self.assertEqual('Theo Bell (Group 6)' in aCards, True)
        self.oConfig.set_postfix_the_display(True)
        aCards = get_card_names(oModel)
        self.assertEqual('The Path of Blood' in aCards, False)
        self.assertEqual('Path of Blood, The' in aCards, True)
        self.assertEqual('Siamese (Group 2), The' in aCards, True)
        self.assertEqual('Theo Bell (Group 2)' in aCards, True)
        self.assertEqual('Theo Bell (Group 2) (Advanced)' in aCards, True)
        self.assertEqual('Theo Bell (Group 6)' in aCards, True)

        # Check load works as expected
        oModel.load()
        aCards = get_card_names(oModel)
        self.assertEqual('The Path of Blood' in aCards, False)
        self.assertEqual('Path of Blood, The' in aCards, True)
        self.assertEqual('Siamese (Group 2), The' in aCards, True)
        self.assertEqual('Theo Bell (Group 2)' in aCards, True)
        self.assertEqual('Theo Bell (Group 2) (Advanced)' in aCards, True)
        self.assertEqual('Theo Bell (Group 6)' in aCards, True)
        self.oConfig.set_postfix_the_display(False)
        aCards = get_card_names(oModel)
        self.assertEqual('The Path of Blood' in aCards, True)
        self.assertEqual('Theo Bell (Group 2)' in aCards, True)
        self.assertEqual('Theo Bell (Group 2) (Advanced)' in aCards, True)
        self.assertEqual('Theo Bell (Group 6)' in aCards, True)

    def test_hide_group_suffix(self):
        """Test that the 'hide group suffix' option works as expected"""
        oModel = CardListModel(self.oConfig)
        oModel.load()
        oPlugin = self._init_hide_plugin(oModel)
        aCards = get_card_names(oModel)
        self.assertEqual('The Path of Blood' in aCards, True)
        self.assertEqual('The Siamese' in aCards, False)
        self.assertEqual('The Siamese (Group 2)' in aCards, True)
        self.assertEqual('Kemintiri (Group 2) (Advanced)' in aCards, True)
        self.assertEqual('Theo Bell (Group 2)' in aCards, True)
        self.assertEqual('Theo Bell (Group 2) (Advanced)' in aCards, True)
        self.assertEqual('Theo Bell (Group 6)' in aCards, True)
        oPlugin.config_activate(DummyButton(True))
        aCards = get_card_names(oModel)
        self.assertEqual('The Path of Blood' in aCards, True)
        self.assertEqual('The Siamese' in aCards, True)
        self.assertEqual('The Siamese (Group 2)' in aCards, False)
        self.assertEqual('Kemintiri (Advanced)' in aCards, True)
        self.assertEqual('Kemintiri (Group 2) (Advanced)' in aCards, False)
        # Theo should be unchanged, because of duplicate groups
        self.assertEqual('Theo Bell (Group 2)' in aCards, True)
        self.assertEqual('Theo Bell (Group 2) (Advanced)' in aCards, True)
        self.assertEqual('Theo Bell (Group 6)' in aCards, True)

        # Check load works as expected
        oModel.load()
        aCards = get_card_names(oModel)
        self.assertEqual('The Path of Blood' in aCards, True)
        self.assertEqual('The Siamese' in aCards, True)
        self.assertEqual('The Siamese (Group 2)' in aCards, False)
        self.assertEqual('Kemintiri (Advanced)' in aCards, True)
        self.assertEqual('Kemintiri (Group 2) (Advanced)' in aCards, False)
        self.assertEqual('Theo Bell (Group 2)' in aCards, True)
        self.assertEqual('Theo Bell (Group 2) (Advanced)' in aCards, True)
        self.assertEqual('Theo Bell (Group 6)' in aCards, True)

        oPlugin.config_activate(DummyButton(False))
        aCards = get_card_names(oModel)
        self.assertEqual('The Path of Blood' in aCards, True)
        self.assertEqual('The Siamese' in aCards, False)
        self.assertEqual('The Siamese (Group 2)' in aCards, True)
        self.assertEqual('Kemintiri (Advanced)' in aCards, False)
        self.assertEqual('Kemintiri (Group 2) (Advanced)' in aCards, True)
        self.assertEqual('Theo Bell (Group 2)' in aCards, True)
        self.assertEqual('Theo Bell (Group 2) (Advanced)' in aCards, True)
        self.assertEqual('Theo Bell (Group 6)' in aCards, True)

    def test_name_stacking(self):
        """Test that stacking the name transformers works"""
        oModel = CardListModel(self.oConfig)
        oModel.load()
        oPlugin = self._init_hide_plugin(oModel)
        aCards = get_card_names(oModel)
        self.assertEqual('The Path of Blood' in aCards, True)
        self.assertEqual('Path of Blood, The' in aCards, False)
        self.assertEqual('The Siamese (Group 2)' in aCards, True)
        self.assertEqual('The Siamese' in aCards, False)
        oPlugin.config_activate(DummyButton(True))
        aCards = get_card_names(oModel)
        self.assertEqual('The Path of Blood' in aCards, True)
        self.assertEqual('Path of Blood, The' in aCards, False)
        self.assertEqual('The Siamese' in aCards, True)
        self.assertEqual('The Siamese (Group 2)' in aCards, False)
        self.oConfig.set_postfix_the_display(True)
        aCards = get_card_names(oModel)
        self.assertEqual('Path of Blood, The' in aCards, True)
        self.assertEqual('The Path of Blood' in aCards, False)
        self.assertEqual('Siamese, The' in aCards, True)
        self.assertEqual('The Siamese' in aCards, False)
        self.assertEqual('Siamese (Group 2), The' in aCards, False)
        self.assertEqual('The Siamese (Group 2)' in aCards, False)

        # Check load works as expected
        oModel.load()
        aCards = get_card_names(oModel)
        self.assertEqual('Path of Blood, The' in aCards, True)
        self.assertEqual('The Path of Blood' in aCards, False)
        self.assertEqual('Siamese, The' in aCards, True)
        self.assertEqual('The Siamese' in aCards, False)
        # Change to just postfix
        oPlugin.config_activate(DummyButton(False))
        aCards = get_card_names(oModel)
        self.assertEqual('Path of Blood, The' in aCards, True)
        self.assertEqual('The Path of Blood' in aCards, False)
        self.assertEqual('Siamese (Group 2), The' in aCards, True)
        self.assertEqual('The Siamese (Group 2)' in aCards, False)
        # Revert to normal
        self.oConfig.set_postfix_the_display(False)
        aCards = get_card_names(oModel)
        self.assertEqual('The Path of Blood' in aCards, True)
        self.assertEqual('The Siamese (Group 2)' in aCards, True)
        self.assertEqual('The Siamese' in aCards, False)
        aCards = get_card_names(oModel)

    def test_illegal(self):
        """Test that the hide/show illegal cards works as expected"""
        oModel = CardListModel(self.oConfig)
        oModel.load()
        aCards = get_card_names(oModel)
        self.assertEqual('Dramatic Upheaval' in aCards, False)
        self.assertEqual('Motivated by Gehenna' in aCards, False)
        oModel.hideillegal = False
        oModel.load()
        aCards = get_card_names(oModel)
        self.assertEqual('Dramatic Upheaval' in aCards, True)
        self.assertEqual('Motivated by Gehenna' in aCards, True)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
