# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test cases for the various Groupings"""


from sutekh.base.core.BaseGroupings import (CardTypeGrouping, RarityGrouping,
                                            ExpansionGrouping, NullGrouping,
                                            ArtistGrouping, KeywordGrouping,
                                            MultiTypeGrouping, DEF_GET_CARD)
from sutekh.base.core.BaseTables import AbstractCard, PhysicalCard
from sutekh.base.core.BaseAdapters import IAbstractCard

from sutekh.core.Groupings import (ClanGrouping, DisciplineGrouping,
                                   GroupPairGrouping, ExpansionRarityGrouping,
                                   CryptLibraryGrouping, SectGrouping,
                                   TitleGrouping, CostGrouping, GroupGrouping,
                                   DisciplineLevelGrouping)
from sutekh.tests.TestCore import SutekhTest

def _get_cards_for_group(aGrouping, sName):
    for aGrp in aGrouping:
        if aGrp[0] == sName:
            return aGrp[1]
    raise RuntimeError("Missed Grouping")  # pragma: no cover


def _get_top_levels(aGrouping):
    """Get a sorted list of the top level groupings"""
    # We use the custom key to handle None values sensibly
    return sorted([x[0] for x in aGrouping], key=lambda x: x if x else "")


class GroupingsTests(SutekhTest):
    """class for various lookup tests"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    @classmethod
    def setUpClass(cls):
        """Setup some useful constants for the test cases"""
        cls.aCards = list(AbstractCard.select())

        cls.oSwallowed = IAbstractCard("Swallowed by the Night")
        cls.oAshur = IAbstractCard("Ashur Tablets")
        cls.oPath = IAbstractCard("The Path of Blood")
        cls.oAire = IAbstractCard("Aire of Elation")
        cls.oAabbt = IAbstractCard("Aabbt Kindred")
        cls.oEarl = IAbstractCard('Earl "Shaka74" Deams')
        cls.oShaEnnu = IAbstractCard("Sha-Ennu")
        cls.oRaven = IAbstractCard("Raven Spy")
        cls.oNewBlood = IAbstractCard("New Blood")

    def test_null_grouping(self):
        """Test behaviour of NullGrouping on abstract card list"""
        aGrp = list(NullGrouping(self.aCards, DEF_GET_CARD))
        self.assertEqual(len(aGrp), 1)
        self.assertEqual(len(aGrp[0][1]), len(self.aCards))
        self.assertTrue(aGrp[0][1][0] in self.aCards)

    def test_card_type_grouping(self):
        """Test behaviour of CardTypeGrouping on abstract card list"""
        aGrp = list(CardTypeGrouping(self.aCards, DEF_GET_CARD))
        self.assertEqual(['Action', 'Action Modifier', 'Ally', 'Combat',
                          'Equipment', 'Imbued', 'Master',
                          'Political Action', 'Power', 'Reaction',
                          'Reflex', 'Retainer', 'Vampire'],
                         _get_top_levels(aGrp))
        self.assertTrue(self.oSwallowed in _get_cards_for_group(
            aGrp, 'Action Modifier'))
        self.assertTrue(self.oAire in _get_cards_for_group(
            aGrp, 'Action Modifier'))
        self.assertTrue(self.oSwallowed in _get_cards_for_group(
            aGrp, 'Combat'))
        self.assertTrue(self.oAire not in _get_cards_for_group(
            aGrp, 'Combat'))
        self.assertTrue(self.oAshur in _get_cards_for_group(
            aGrp, 'Master'))
        self.assertTrue(self.oPath in _get_cards_for_group(
            aGrp, 'Master'))
        self.assertTrue(self.oAshur not in _get_cards_for_group(
            aGrp, 'Combat'))
        self.assertTrue(self.oEarl in _get_cards_for_group(
            aGrp, 'Imbued'))
        self.assertTrue(self.oAabbt not in _get_cards_for_group(
            aGrp, 'Imbued'))
        self.assertTrue(self.oAabbt in _get_cards_for_group(
            aGrp, 'Vampire'))

    def test_rarity_grouping(self):
        """Test behaviour of RarityGrouping on abstract card list"""
        aGrp = list(RarityGrouping(self.aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)
        self.assertTrue(None not in aGrpNames)
        self.assertTrue('Fixed' in aGrpNames)
        self.assertTrue('Precon' in aGrpNames)
        self.assertTrue('Vampire' in aGrpNames)

        self.assertTrue(self.oAabbt in _get_cards_for_group(aGrp, 'Uncommon'))
        self.assertTrue(self.oShaEnnu in _get_cards_for_group(aGrp, 'Vampire'))
        self.assertTrue(self.oShaEnnu not in _get_cards_for_group(aGrp,
                                                                  'Precon'))
        self.assertTrue(self.oSwallowed in _get_cards_for_group(aGrp,
                                                                'Common'))
        self.assertTrue(self.oRaven not in _get_cards_for_group(aGrp,
                                                                'Common'))
        self.assertTrue(self.oRaven in _get_cards_for_group(aGrp, 'Precon'))
        self.assertTrue(self.oRaven in _get_cards_for_group(aGrp, 'Uncommon'))

        aGrp = list(ExpansionGrouping(self.aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)
        self.assertTrue(None not in aGrpNames)
        self.assertTrue('Anthology' in aGrpNames)
        self.assertTrue('Final Nights' in aGrpNames)
        self.assertTrue('Sabbat Wars' in aGrpNames)

        self.assertTrue(self.oAabbt in _get_cards_for_group(
            aGrp, 'Final Nights'))
        self.assertTrue(self.oShaEnnu in _get_cards_for_group(
            aGrp, 'Third Edition'))
        self.assertTrue(self.oSwallowed in _get_cards_for_group(
            aGrp, 'Third Edition'))
        self.assertTrue(self.oRaven in _get_cards_for_group(
            aGrp, 'Lords of the Night'))
        self.assertTrue(self.oRaven in _get_cards_for_group(
            aGrp, 'Third Edition'))
        self.assertTrue(self.oRaven in _get_cards_for_group(aGrp, 'Jyhad'))

    def test_artist_grouping(self):
        """Test behaviour of ArtistGrouping on abstract card list"""
        aGrp = list(ArtistGrouping(self.aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)
        self.assertTrue('Rebecca Guay' in aGrpNames)
        self.assertTrue('Richard Thomas' in aGrpNames)

        self.assertTrue(self.oShaEnnu in _get_cards_for_group(
            aGrp, 'Richard Thomas'))
        self.assertTrue(self.oSwallowed in _get_cards_for_group(
            aGrp, 'Thea Maia'))
        self.assertTrue(self.oSwallowed in _get_cards_for_group(
            aGrp, 'Tom Biondillo'))

    def test_keyword_grouping(self):
        """Test behaviour of KeywordGrouping on abstract card list"""
        aGrp = list(KeywordGrouping(self.aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)
        self.assertTrue(None in aGrpNames)
        self.assertTrue('3 bleed' in aGrpNames)
        self.assertTrue('trifle' in aGrpNames)
        self.assertTrue('unique' in aGrpNames)

        self.assertTrue(self.oShaEnnu in _get_cards_for_group(aGrp, '3 bleed'))
        self.assertTrue(self.oShaEnnu in _get_cards_for_group(aGrp,
                                                              '1 strength'))
        self.assertTrue(self.oAabbt in _get_cards_for_group(aGrp,
                                                            '1 strength'))
        self.assertTrue(self.oPath in _get_cards_for_group(aGrp, 'unique'))

    def test_multitype_grouping(self):
        """Test behaviour of MultiTypeGrouping on abstract card list"""
        aGrp = list(MultiTypeGrouping(self.aCards, DEF_GET_CARD))
        self.assertEqual(['Action', 'Action Modifier',
                          'Action Modifier / Combat',
                          'Ally', 'Combat', 'Combat / Reaction',
                          'Equipment', 'Imbued', 'Master',
                          'Political Action', 'Power', 'Reaction',
                          'Reaction / Reflex',
                          'Retainer', 'Vampire'],
                         _get_top_levels(aGrp))
        self.assertTrue(self.oAire in _get_cards_for_group(
            aGrp, 'Action Modifier'))
        self.assertTrue(self.oSwallowed not in _get_cards_for_group(
            aGrp, 'Action Modifier'))
        self.assertTrue(self.oSwallowed not in _get_cards_for_group(
            aGrp, 'Combat'))
        self.assertTrue(self.oSwallowed in _get_cards_for_group(
            aGrp, 'Action Modifier / Combat'))
        self.assertTrue(self.oAshur in _get_cards_for_group(aGrp, 'Master'))
        self.assertTrue(self.oEarl in _get_cards_for_group(aGrp, 'Imbued'))
        self.assertTrue(self.oAabbt in _get_cards_for_group(aGrp, 'Vampire'))

    def test_clan_grouping(self):
        """Test behaviour of ClanGrouping on abstract card list"""
        aGrp = list(ClanGrouping(self.aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)
        self.assertTrue(None in aGrpNames)
        self.assertTrue('Abomination' in aGrpNames)
        self.assertTrue('Osebo' in aGrpNames)
        self.assertTrue('Pander' in aGrpNames)
        self.assertTrue(self.oAabbt in _get_cards_for_group(
            aGrp, 'Follower of Set'))
        self.assertTrue(self.oEarl in _get_cards_for_group(aGrp, 'Visionary'))
        self.assertTrue(self.oSwallowed in _get_cards_for_group(aGrp, None))

    def test_discipline_grouping(self):
        """Test behaviour of DisciplineGrouping on abstract card list"""
        aGrp = list(DisciplineGrouping(self.aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)
        self.assertTrue(None in aGrpNames)
        self.assertTrue('Obfuscate' in aGrpNames)
        self.assertTrue('Vision' in aGrpNames)

        self.assertTrue(self.oEarl in _get_cards_for_group(aGrp, 'Vision'))
        self.assertTrue(self.oSwallowed in _get_cards_for_group(aGrp,
                                                                'Obfuscate'))
        self.assertTrue(self.oAabbt not in _get_cards_for_group(aGrp,
                                                                'Obfuscate'))
        self.assertTrue(self.oAshur in _get_cards_for_group(aGrp, None))
        self.assertTrue(self.oAabbt in _get_cards_for_group(aGrp,
                                                            'Serpentis'))
        self.assertTrue(self.oAabbt in _get_cards_for_group(aGrp, 'Presence'))
        self.assertTrue(self.oAire in _get_cards_for_group(aGrp, 'Presence'))

    def test_group_pair_grouping(self):
        """Test behaviour of GroupPairGrouping on abstract card list"""
        aGrp = list(GroupPairGrouping(self.aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)
        self.assertTrue(None in aGrpNames)
        self.assertTrue('Groups 1, 2' in aGrpNames)
        self.assertTrue('Groups 4, 5' in aGrpNames)

        self.assertTrue(self.oEarl in _get_cards_for_group(
            aGrp, 'Groups 4, 5'))
        self.assertTrue(self.oEarl in _get_cards_for_group(
            aGrp, 'Groups 3, 4'))
        self.assertTrue(self.oSwallowed in _get_cards_for_group(
            aGrp, None))
        self.assertTrue(self.oAabbt in _get_cards_for_group(
            aGrp, 'Groups 1, 2'))
        self.assertTrue(self.oAabbt in _get_cards_for_group(
            aGrp, 'Groups 2, 3'))
        self.assertTrue(self.oAabbt not in _get_cards_for_group(
            aGrp, 'Groups 3, 4'))
        self.assertTrue(self.oNewBlood in _get_cards_for_group(
            aGrp, 'Groups 3, 4'))
        self.assertTrue(self.oNewBlood in _get_cards_for_group(
            aGrp, 'Groups 1, 2'))
        self.assertTrue(self.oNewBlood in _get_cards_for_group(
            aGrp, 'Groups 5, 6'))

    def test_expansion_rarity_grouping(self):
        """Test behaviour of ExpansionRarityGrouping on abstract card list"""
        aGrp = list(ExpansionRarityGrouping(self.aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)
        self.assertTrue('VTES : Vampire' in aGrpNames)
        self.assertTrue('Jyhad : Uncommon' in aGrpNames)
        self.assertTrue('Sabbat Wars : Precon' in aGrpNames)
        self.assertTrue('Sabbat Wars : Precon Only' in aGrpNames)
        self.assertTrue(None not in aGrpNames)

        self.assertTrue(self.oAabbt in _get_cards_for_group(
            aGrp, 'Final Nights : Uncommon'))
        self.assertTrue(self.oShaEnnu in _get_cards_for_group(
            aGrp, 'Third Edition : Vampire'))
        self.assertTrue(self.oShaEnnu not in _get_cards_for_group(
            aGrp, 'Third Edition : Precon'))
        self.assertTrue(self.oSwallowed in _get_cards_for_group(
            aGrp, 'Third Edition : Common'))
        self.assertTrue(self.oRaven not in _get_cards_for_group(
            aGrp, 'Third Edition : Common'))
        self.assertTrue(self.oRaven not in _get_cards_for_group(
            aGrp, 'Third Edition : Uncommon'))
        self.assertTrue(self.oRaven in _get_cards_for_group(
            aGrp, 'Third Edition : Precon'))
        self.assertTrue(self.oRaven in _get_cards_for_group(
            aGrp, 'Lords of the Night : Precon'))
        self.assertTrue(self.oRaven in _get_cards_for_group(
            aGrp, 'Third Edition : Precon Only'))
        self.assertTrue(self.oRaven in _get_cards_for_group(
            aGrp, 'Jyhad : Uncommon'))

    def test_crypt_lib_grouping(self):
        """Test behaviour of CryptLibraryGrouping on abstract card list"""
        aGrp = list(CryptLibraryGrouping(self.aCards, DEF_GET_CARD))
        self.assertEqual(['Crypt', 'Library'], _get_top_levels(aGrp))
        self.assertTrue(self.oSwallowed in _get_cards_for_group(aGrp,
                                                                'Library'))
        self.assertTrue(self.oAshur in _get_cards_for_group(aGrp, 'Library'))
        self.assertTrue(self.oPath in _get_cards_for_group(aGrp, 'Library'))
        self.assertTrue(self.oEarl in _get_cards_for_group(aGrp, 'Crypt'))
        self.assertTrue(self.oEarl not in _get_cards_for_group(aGrp,
                                                               'Library'))
        self.assertTrue(self.oAabbt not in _get_cards_for_group(aGrp,
                                                                'Library'))
        self.assertTrue(self.oAabbt in _get_cards_for_group(aGrp, 'Crypt'))

    def test_sect_grouping(self):
        """Test behaviour of SectGrouping on abstract card list"""
        aGrp = list(SectGrouping(self.aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)
        self.assertTrue('Camarilla' in aGrpNames)
        self.assertTrue('Sabbat' in aGrpNames)
        self.assertTrue('Laibon' in aGrpNames)

        self.assertTrue(self.oAabbt in _get_cards_for_group(aGrp,
                                                            'Independent'))
        self.assertTrue(self.oAire in _get_cards_for_group(aGrp, None))
        self.assertTrue(self.oShaEnnu in _get_cards_for_group(aGrp, 'Sabbat'))
        aGrp = list(TitleGrouping(self.aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)

        self.assertTrue(None in aGrpNames)
        self.assertTrue('Bishop' in aGrpNames)
        self.assertTrue('Prince' in aGrpNames)
        self.assertTrue('Regent' in aGrpNames)

        self.assertTrue(self.oAabbt in _get_cards_for_group(aGrp, None))
        self.assertTrue(self.oAire in _get_cards_for_group(aGrp, None))
        self.assertTrue(self.oShaEnnu in _get_cards_for_group(aGrp, 'Regent'))

    def test_cost_grouping(self):
        """Test behaviour of CostGrouping on abstract card list"""
        aGrp = list(CostGrouping(self.aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)
        self.assertTrue(None in aGrpNames)
        self.assertTrue('1 pool' in aGrpNames)
        self.assertTrue('1 blood' in aGrpNames)
        self.assertTrue('3 conviction' in aGrpNames)

        self.assertTrue(self.oEarl in _get_cards_for_group(aGrp, None))
        self.assertTrue(self.oAabbt in _get_cards_for_group(aGrp, None))
        self.assertTrue(self.oAshur in _get_cards_for_group(aGrp, None))
        self.assertTrue(self.oAire in _get_cards_for_group(aGrp, '1 blood'))
        self.assertTrue(self.oPath in _get_cards_for_group(aGrp, '1 pool'))

    def test_group_grouping(self):
        """Test behaviour of GroupGrouping on abstract card list"""
        aGrp = list(GroupGrouping(self.aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)
        self.assertTrue(None in aGrpNames)
        self.assertTrue('Group 1' in aGrpNames)
        self.assertTrue('Group 5' in aGrpNames)
        self.assertTrue('Any Group' in aGrpNames)

        self.assertTrue(self.oEarl in _get_cards_for_group(aGrp, 'Group 4'))
        self.assertTrue(self.oSwallowed in _get_cards_for_group(aGrp, None))
        self.assertTrue(self.oAabbt in _get_cards_for_group(aGrp, 'Group 2'))
        self.assertTrue(self.oNewBlood in _get_cards_for_group(aGrp,
                                                               'Any Group'))

    def test_discipline_level_grouping(self):
        """Test behaviour of DisciplineLevelGrouping on abstract card list"""
        aGrp = list(DisciplineLevelGrouping(self.aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)
        self.assertTrue(None in aGrpNames)
        self.assertTrue('Obfuscate (inferior)' in aGrpNames)
        self.assertTrue('Obfuscate (superior)' in aGrpNames)
        self.assertTrue('Vision' in aGrpNames)

        self.assertTrue(self.oEarl in _get_cards_for_group(aGrp, 'Vision'))
        self.assertTrue(self.oSwallowed in _get_cards_for_group(
            aGrp, 'Obfuscate (superior)'))
        self.assertTrue(self.oAshur in _get_cards_for_group(aGrp, None))
        self.assertTrue(self.oAabbt in _get_cards_for_group(
            aGrp, 'Serpentis (inferior)'))
        self.assertTrue(self.oAabbt not in _get_cards_for_group(
            aGrp, 'Serpentis (superior)'))
        self.assertTrue(self.oAabbt in _get_cards_for_group(
            aGrp, 'Presence (inferior)'))
        self.assertTrue(self.oAabbt not in _get_cards_for_group(
            aGrp, 'Presence (superior)'))
        self.assertTrue(self.oAire in _get_cards_for_group(
            aGrp, 'Presence (superior)'))
        self.assertTrue(self.oAire not in _get_cards_for_group(
            aGrp, 'Presence (inferior)'))

    def test_physical_card_iterator(self):
        """Test behaviour on physical card lists"""

        # We rely on the abstract card checks to cover the behaviour
        # This just sanity checks using physical card lists

        aPhysCards = list(PhysicalCard.select())
        fGetCard = lambda x: x.abstractCard

        aGrp = list(CryptLibraryGrouping(aPhysCards, fGetCard))
        self.assertEqual(len(aGrp), 2)
        self.assertEqual(['Crypt', 'Library'], _get_top_levels(aGrp))

        aGrp = list(NullGrouping(aPhysCards, fGetCard))
        self.assertEqual(len(aGrp), 1)
        self.assertEqual(len(aGrp[0][1]), len(aPhysCards))
        self.assertTrue(aGrp[0][1][0] in aPhysCards)

        aGrp = list(ClanGrouping(aPhysCards, fGetCard))
        aGrpNames = _get_top_levels(aGrp)
        self.assertTrue(None in aGrpNames)
        self.assertTrue('Abomination' in aGrpNames)
        self.assertTrue('Osebo' in aGrpNames)
        self.assertTrue('Pander' in aGrpNames)

        aFollwers = [x.abstractCard for x in
                     _get_cards_for_group(aGrp, 'Follower of Set')]
        self.assertTrue(self.oAabbt in aFollwers)
