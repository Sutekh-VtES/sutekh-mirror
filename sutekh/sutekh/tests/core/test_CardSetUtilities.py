# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test cases for the CardSetUtilities functions"""

import unittest

from sutekh.base.core.BaseTables import PhysicalCardSet
from sutekh.base.core.CardSetUtilities import (delete_physical_card_set,
                                               get_loop_names, detect_loop,
                                               find_children, break_loop,
                                               has_children, clean_empty,
                                               get_current_card_sets,
                                               format_cs_list)

from sutekh.tests.TestCore import SutekhTest


class CardSetUtilTests(SutekhTest):
    """class for the Card Set Utility tests"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    def test_basic(self):
        """Test behaviour without loops"""
        oRoot = PhysicalCardSet(name='Root')
        oChild = PhysicalCardSet(name='Child', parent=oRoot)
        aChildren = []
        for iCnt in range(4):
            oSet = PhysicalCardSet(name='Card Set %d' % iCnt, parent=oChild)
            aChildren.append(oSet)
        # Check detect_loop fails
        self.assertFalse(detect_loop(oRoot))
        self.assertFalse(detect_loop(oChild))

        # Check has_children
        self.assertTrue(has_children(oRoot))
        self.assertTrue(has_children(oChild))
        self.assertFalse(has_children(aChildren[0]))
        self.assertFalse(has_children(aChildren[1]))

        # Check find_children behaves properly
        aFoundChildren = find_children(oRoot)
        self.assertEqual(len(aFoundChildren), 1)
        self.assertEqual(aFoundChildren[0].name, oChild.name)
        aFoundChildren = find_children(oChild)
        self.assertEqual(len(aFoundChildren), 4)
        self.assertEqual(sorted([x.name for x in aFoundChildren]),
                         sorted([x.name for x in aChildren]))

        # Check formatiing works
        sList = (" Root\n"
                 "    Child\n"
                 "       Card Set 0\n"
                 "       Card Set 1\n"
                 "       Card Set 2\n"
                 "       Card Set 3")
        sList2 = (" Child\n"
                  "    Card Set 0\n"
                  "    Card Set 1\n"
                  "    Card Set 2\n"
                  "    Card Set 3")
        sList3 = ("  Card Set 0\n"
                  "  Card Set 1\n"
                  "  Card Set 2\n"
                  "  Card Set 3")
        self.assertEqual(format_cs_list(None), sList)
        self.assertEqual(format_cs_list(oRoot), sList2)
        self.assertEqual(format_cs_list(oChild, '  '), sList3)

        # Check children are reparented correctly
        delete_physical_card_set(oChild.name)
        aFoundChildren = find_children(oRoot)
        self.assertEqual(len(aFoundChildren), 4)
        self.assertEqual(sorted([x.name for x in aFoundChildren]),
                         sorted([x.name for x in aChildren]))

        # Check ordinary deletion
        bRes = delete_physical_card_set(aChildren[0].name)
        self.assertEqual(bRes, True)
        aFoundChildren = find_children(oRoot)
        self.assertEqual(len(aFoundChildren), 3)
        self.assertEqual(sorted([x.name for x in aFoundChildren]),
                         sorted([x.name for x in aChildren[1:]]))

        # Check trying to delete non-existant card set
        bRes = delete_physical_card_set(aChildren[0].name)
        self.assertEqual(bRes, False)

    def test_loops(self):
        """Test loop detection and loop handling"""
        # Create a loop
        oRoot = PhysicalCardSet(name='Root')
        oChild = PhysicalCardSet(name='Child', parent=oRoot)
        aChildren = []
        for iCnt in range(4):
            oSet = PhysicalCardSet(name='Card Set %d' % iCnt, parent=oChild)
            aChildren.append(oSet)
        oRoot.parent = aChildren[0]
        oRoot.syncUpdate()

        # Check that detect_loop picks this up
        self.assertTrue(detect_loop(oRoot))
        self.assertTrue(detect_loop(oChild))
        self.assertTrue(detect_loop(aChildren[0]))
        # This will also run round the loop
        self.assertTrue(detect_loop(aChildren[1]))

        # Check we identify the right cards in the loop
        aList1 = get_loop_names(oRoot)
        self.assertEqual(aList1, ['Child', 'Card Set 0', 'Root'])
        aList2 = get_loop_names(oChild)
        self.assertEqual(sorted(aList2), sorted(aList1))
        aList3 = get_loop_names(aChildren[1])
        self.assertEqual(sorted(aList3), sorted(aList1))
        # Check that deleting doesn't fix the loop, due to reparenting
        delete_physical_card_set(aChildren[0].name)
        self.assertTrue(detect_loop(oRoot))
        # Check that explicit loop breaking working
        oRoot.parent = None
        oRoot.syncUpdate()
        self.assertFalse(detect_loop(oRoot))
        self.assertFalse(detect_loop(aChildren[1]))
        aList1 = get_loop_names(oRoot)
        self.assertEqual(len(aList1), 0)
        # Create another loop
        oRoot.parent = aChildren[1]
        oRoot.syncUpdate()
        self.assertTrue(detect_loop(oRoot))
        # Use the break loop function
        self.assertEqual(break_loop(oRoot), oRoot.name)
        self.assertFalse(detect_loop(oRoot))
        self.assertFalse(detect_loop(aChildren[1]))
        # Check that break_loop returns None for non-loop status
        self.assertEqual(break_loop(oRoot), None)
        self.assertEqual(break_loop(aChildren[1]), None)
        # Try breaking loop with a child
        oRoot.parent = aChildren[1]
        oRoot.syncUpdate()
        self.assertTrue(detect_loop(oRoot))
        self.assertEqual(break_loop(aChildren[1]), aChildren[1].name)
        self.assertFalse(detect_loop(oRoot))
        self.assertFalse(detect_loop(aChildren[1]))

    def test_clean_empty(self):
        """Test clean_empty works as desired."""
        oRoot = PhysicalCardSet(name='Root')
        oChild = PhysicalCardSet(name='Child', parent=oRoot)
        aChildren = []
        for iCnt in range(4):
            oSet = PhysicalCardSet(name='Card Set %d' % iCnt, parent=oChild)
            aChildren.append(oSet)

        aSets = get_current_card_sets()
        self.assertEqual(len(aSets), 6)
        # Check that clean_emtpy doesn't remove any sets we say were existing
        clean_empty(aSets, aSets)
        self.assertEqual(len(get_current_card_sets()), 6)
        # Check that clean_empty removes all the children if we say none
        # were existing
        clean_empty([x.name for x in aChildren], [])
        aSets = get_current_card_sets()
        self.assertEqual(len(aSets), 2)
        self.assertTrue(oChild.name in aSets)
        self.assertTrue(oRoot.name in aSets)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
