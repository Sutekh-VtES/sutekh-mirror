# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2019 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test some of the cli interface functionality"""

from io import StringIO

from mock import patch

from sutekh.base.core.BaseTables import PhysicalCardSet
from sutekh.tests.core.test_PhysicalCardSet import make_set_1
from sutekh.tests.TestCore import SutekhTest

from sutekh.SutekhCli import print_card_details
from sutekh.base.CliUtils import (run_filter, print_card_filter_list,
                                  print_card_list, do_print_card)


TREE_1 = """ Root
    Child 1
       GC 1
       GC 2
       GC 3
    Child 2
       GC 4
    Child 3
"""

TREE_2 = """ Child 1
    GC 1
    GC 2
    GC 3
"""

CARD_DETAILS_1 = """Alexandra
CardType: Vampire
Clan: Toreador
Capacity: 11
Group: 2
Keywords: 3 bleed   0 intercept   0 stealth   1 strength
Discipline: dom ANI AUS CEL PRE
Camarilla Inner Circle: Once during your turn, you may lock or unlock another ready Toreador. +2 bleed.
"""

CARD_DETAILS_2 = """Swallowed by the Night
CardType: Action Modifier / Combat
Discipline: Obfuscate
[obf] [ACTION MODIFIER] +1 stealth.
[OBF] [COMBAT] Maneuver.
"""

CARD_DETAILS_3 = """Gypsies
CardType: Ally
Clan: Gangrel
Life: 1
Cost: 3 pool
Keywords: 1 bleed   1 stealth   1 strength   mortal   unique
Unique {mortal} with 1 life. 1 {strength}, 1 bleed.
Gypsies get +1 stealth on each of their actions.
"""

CARD_DETAILS_4 = """High Top
CardType: Ally
Clan: Ahrimane
Life: 3
Cost: 4 pool
Keywords: 0 bleed   1 intercept   1 strength   unique   werewolf
Unique werewolf with 3 life. 1 strength, 0 bleed.
High Top gets +1 intercept. High Top may enter combat with any minion controlled by another Methuselah as a (D) action. High Top gets an additional strike each round and an optional maneuver once each combat. He may play cards requiring basic Celerity [cel] as a vampire with a capacity of 4. If High Top has less than 3 life during your unlock phase, he gains 1 life.
"""

FILTER_LIST = """Abandoning the Flesh
Hide the Heart
Predator's Communion
"""


class CliUtilsTests(SutekhTest):
    """Run tests on various cli print options, patching stdout so we can see
       the results"""

    def test_print_card_sets(self):
        """Test printing a card set hierachy"""
        # Create a 3 level hierachy
        oRoot = PhysicalCardSet(name='Root')
        oChild1 = PhysicalCardSet(name='Child 1', parent=oRoot)
        oChild2 = PhysicalCardSet(name='Child 2', parent=oRoot)
        PhysicalCardSet(name='Child 3', parent=oRoot)
        PhysicalCardSet(name='GC 1', parent=oChild1)
        PhysicalCardSet(name='GC 2', parent=oChild1)
        PhysicalCardSet(name='GC 3', parent=oChild1)
        PhysicalCardSet(name='GC 4', parent=oChild2)

        with patch('sys.stdout', new_callable=StringIO) as oMock:
            print_card_list('Root')
            self.assertEqual(oMock.getvalue(), TREE_1)

        with patch('sys.stdout', new_callable=StringIO) as oMock:
            print_card_list('Child 1')
            self.assertEqual(oMock.getvalue(), TREE_2)

    def test_print_card_details(self):
        """Test printing a card"""
        with patch('sys.stdout', new_callable=StringIO) as oMock:
            do_print_card('Alexandra', print_card_details)
            self.assertEqual(oMock.getvalue(), CARD_DETAILS_1)

        with patch('sys.stdout', new_callable=StringIO) as oMock:
            do_print_card('Swallowed by the Night', print_card_details)
            self.assertEqual(oMock.getvalue(), CARD_DETAILS_2)

        with patch('sys.stdout', new_callable=StringIO) as oMock:
            do_print_card('Gypsies', print_card_details)
            self.assertEqual(oMock.getvalue(), CARD_DETAILS_3)

        with patch('sys.stdout', new_callable=StringIO) as oMock:
            do_print_card('High Top', print_card_details)
            self.assertEqual(oMock.getvalue(), CARD_DETAILS_4)

        # Check error case
        with patch('sys.stdout', new_callable=StringIO) as oMock:
            do_print_card('Swallowed', print_card_details)
            self.assertEqual(oMock.getvalue(),
                             'Unable to find card Swallowed\n')

    def test_run_filter_abstract_card(self):
        """Test running some filters on the Abstract Card list"""
        dResults = run_filter("Clan = 'Follower of Set'", None)
        self.assertEqual(len(dResults), 4)
        for oCard in dResults:
            self.assertEqual(dResults[oCard], 0)
        aNames = [x.name for x in dResults]
        self.assertTrue('Aabbt Kindred' in aNames)
        self.assertTrue('Amisa' in aNames)

        dResults = run_filter("CardType = 'Reaction'", None)
        self.assertEqual(len(dResults), 3)
        for oCard in dResults:
            self.assertEqual(dResults[oCard], 0)
        aNames = [x.name for x in dResults]
        self.assertTrue('Abandoning the Flesh' in aNames)
        self.assertTrue('Hide the Heart' in aNames)

        dResults = run_filter("CardName = 'YYY'", None)
        self.assertEqual(len(dResults), 0)

    def test_run_filter_pcs(self):
        """Test running filters on a Phyiscal card Set"""
        make_set_1()
        dResults = run_filter("Clan = 'Ahrimane'", 'Test Set 1')
        self.assertEqual(len(dResults), 1)
        oCard = list(dResults)[0]
        self.assertEqual(dResults[oCard], 2)
        self.assertEqual(oCard.name, 'The Siamese')

        dResults = run_filter("Discipline = 'Potence'", 'Test Set 1')
        self.assertEqual(len(dResults), 2)
        dNameResults = {x.name: dResults[x] for x in dResults}
        self.assertEqual(dNameResults['Hektor'], 1)
        self.assertEqual(dNameResults['Immortal Grapple'], 4)

    def test_print_card_filter_list(self):
        """Test printing the results of a filter list"""
        dResults = run_filter("CardType = 'Reaction'", None)
        with patch('sys.stdout', new_callable=StringIO) as oMock:
            print_card_filter_list(dResults, None, False)
            self.assertEqual(oMock.getvalue(), FILTER_LIST)
