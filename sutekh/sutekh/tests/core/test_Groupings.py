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
    raise RuntimeError("Missed Grouping")


def _get_top_levels(aGrouping):
    return sorted([x[0] for x in aGrouping])


class GroupingsTests(SutekhTest):
    """class for various lookup tests"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    def test_abstract_card_iterator(self):
        """Test behaviour on abstract card lists"""

        aCards = list(AbstractCard.select())

        oSwallowed = IAbstractCard("Swallowed by the Night")
        oAshur = IAbstractCard("Ashur Tablets")
        oPath = IAbstractCard("The Path of Blood")
        oAire = IAbstractCard("Aire of Elation")
        oAabbt = IAbstractCard("Aabbt Kindred")
        oEarl = IAbstractCard('Earl "Shaka74" Deams')
        oShaEnnu = IAbstractCard("Sha-Ennu")
        oRaven = IAbstractCard("Raven Spy")
        oNewBlood = IAbstractCard("New Blood")

        aGrp = list(NullGrouping(aCards, DEF_GET_CARD))
        self.assertEqual(len(aGrp), 1)
        self.assertEqual(len(aGrp[0][1]), len(aCards))
        self.assertTrue(aGrp[0][1][0] in aCards)

        aGrp = list(CardTypeGrouping(aCards, DEF_GET_CARD))
        self.assertEqual(['Action', 'Action Modifier', 'Ally', 'Combat',
                          'Equipment', 'Imbued', 'Master',
                          'Political Action', 'Power', 'Reaction',
                          'Reflex', 'Retainer', 'Vampire'],
                         _get_top_levels(aGrp))
        self.assertTrue(oSwallowed in _get_cards_for_group(aGrp,
                                                           'Action Modifier'))
        self.assertTrue(oAire in _get_cards_for_group(aGrp,
                                                      'Action Modifier'))
        self.assertTrue(oSwallowed in _get_cards_for_group(aGrp, 'Combat'))
        self.assertTrue(oAire not in _get_cards_for_group(aGrp, 'Combat'))
        self.assertTrue(oAshur in _get_cards_for_group(aGrp, 'Master'))
        self.assertTrue(oPath in _get_cards_for_group(aGrp, 'Master'))
        self.assertTrue(oAshur not in _get_cards_for_group(aGrp, 'Combat'))
        self.assertTrue(oEarl in _get_cards_for_group(aGrp, 'Imbued'))
        self.assertTrue(oAabbt not in _get_cards_for_group(aGrp, 'Imbued'))
        self.assertTrue(oAabbt in _get_cards_for_group(aGrp, 'Vampire'))

        aGrp = list(RarityGrouping(aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)
        self.assertTrue(None not in aGrpNames)
        self.assertTrue('Fixed' in aGrpNames)
        self.assertTrue('Precon' in aGrpNames)
        self.assertTrue('Vampire' in aGrpNames)

        self.assertTrue(oAabbt in _get_cards_for_group(aGrp, 'Uncommon'))
        self.assertTrue(oShaEnnu in _get_cards_for_group(aGrp, 'Vampire'))
        self.assertTrue(oShaEnnu not in _get_cards_for_group(aGrp, 'Precon'))
        self.assertTrue(oSwallowed in _get_cards_for_group(aGrp, 'Common'))
        self.assertTrue(oRaven not in _get_cards_for_group(aGrp, 'Common'))
        self.assertTrue(oRaven in _get_cards_for_group(aGrp, 'Precon'))
        self.assertTrue(oRaven in _get_cards_for_group(aGrp, 'Uncommon'))

        aGrp = list(ExpansionGrouping(aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)
        self.assertTrue(None not in aGrpNames)
        self.assertTrue('Anthology' in aGrpNames)
        self.assertTrue('Final Nights' in aGrpNames)
        self.assertTrue('Sabbat Wars' in aGrpNames)

        self.assertTrue(oAabbt in _get_cards_for_group(aGrp, 'Final Nights'))
        self.assertTrue(oShaEnnu in _get_cards_for_group(aGrp,
                                                         'Third Edition'))
        self.assertTrue(oSwallowed in _get_cards_for_group(aGrp,
                                                           'Third Edition'))
        self.assertTrue(oRaven in _get_cards_for_group(aGrp,
                                                       'Lords of the Night'))
        self.assertTrue(oRaven in _get_cards_for_group(aGrp, 'Third Edition'))
        self.assertTrue(oRaven in _get_cards_for_group(aGrp, 'Jyhad'))

        aGrp = list(ArtistGrouping(aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)
        self.assertTrue('Rebecca Guay' in aGrpNames)
        self.assertTrue('Richard Thomas' in aGrpNames)

        self.assertTrue(oShaEnnu in _get_cards_for_group(aGrp,
                                                         'Richard Thomas'))
        self.assertTrue(oSwallowed in _get_cards_for_group(
            aGrp, 'Thea Maia'))
        self.assertTrue(oSwallowed in _get_cards_for_group(
            aGrp, 'Tom Biondillo'))

        aGrp = list(KeywordGrouping(aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)
        self.assertTrue(None in aGrpNames)
        self.assertTrue('3 bleed' in aGrpNames)
        self.assertTrue('trifle' in aGrpNames)
        self.assertTrue('unique' in aGrpNames)

        self.assertTrue(oShaEnnu in _get_cards_for_group(aGrp, '3 bleed'))
        self.assertTrue(oShaEnnu in _get_cards_for_group(aGrp, '1 strength'))
        self.assertTrue(oAabbt in _get_cards_for_group(aGrp, '1 strength'))
        self.assertTrue(oPath in _get_cards_for_group(aGrp, 'unique'))

        aGrp = list(MultiTypeGrouping(aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)
        self.assertEqual(['Action', 'Action Modifier',
                          'Action Modifier / Combat',
                          'Ally', 'Combat', 'Combat / Reaction',
                          'Equipment', 'Imbued', 'Master',
                          'Political Action', 'Power', 'Reaction',
                          'Reaction / Reflex',
                          'Retainer', 'Vampire'],
                         _get_top_levels(aGrp))
        self.assertTrue(oAire in _get_cards_for_group(aGrp, 'Action Modifier'))
        self.assertTrue(oSwallowed not in _get_cards_for_group(
            aGrp, 'Action Modifier'))
        self.assertTrue(oSwallowed not in _get_cards_for_group(aGrp, 'Combat'))
        self.assertTrue(oSwallowed in _get_cards_for_group(
            aGrp, 'Action Modifier / Combat'))
        self.assertTrue(oAshur in _get_cards_for_group(aGrp, 'Master'))
        self.assertTrue(oEarl in _get_cards_for_group(aGrp, 'Imbued'))
        self.assertTrue(oAabbt in _get_cards_for_group(aGrp, 'Vampire'))

        aGrp = list(ClanGrouping(aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)
        self.assertTrue(None in aGrpNames)
        self.assertTrue('Abomination' in aGrpNames)
        self.assertTrue('Osebo' in aGrpNames)
        self.assertTrue('Pander' in aGrpNames)
        self.assertTrue(oAabbt in _get_cards_for_group(aGrp,
                                                       'Follower of Set'))
        self.assertTrue(oEarl in _get_cards_for_group(aGrp, 'Visionary'))
        self.assertTrue(oSwallowed in _get_cards_for_group(aGrp, None))

        aGrp = list(DisciplineGrouping(aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)
        self.assertTrue(None in aGrpNames)
        self.assertTrue('Obfuscate' in aGrpNames)
        self.assertTrue('Vision' in aGrpNames)

        self.assertTrue(oEarl in _get_cards_for_group(aGrp, 'Vision'))
        self.assertTrue(oSwallowed in _get_cards_for_group(aGrp, 'Obfuscate'))
        self.assertTrue(oAabbt not in _get_cards_for_group(aGrp, 'Obfuscate'))
        self.assertTrue(oAshur in _get_cards_for_group(aGrp, None))
        self.assertTrue(oAabbt in _get_cards_for_group(aGrp, 'Serpentis'))
        self.assertTrue(oAabbt in _get_cards_for_group(aGrp, 'Presence'))
        self.assertTrue(oAire in _get_cards_for_group(aGrp, 'Presence'))

        aGrp = list(GroupPairGrouping(aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)
        self.assertTrue(None in aGrpNames)
        self.assertTrue('Groups 1, 2' in aGrpNames)
        self.assertTrue('Groups 4, 5' in aGrpNames)

        self.assertTrue(oEarl in _get_cards_for_group(aGrp, 'Groups 4, 5'))
        self.assertTrue(oEarl in _get_cards_for_group(aGrp, 'Groups 3, 4'))
        self.assertTrue(oSwallowed in _get_cards_for_group(aGrp, None))
        self.assertTrue(oAabbt in _get_cards_for_group(aGrp, 'Groups 1, 2'))
        self.assertTrue(oAabbt in _get_cards_for_group(aGrp, 'Groups 2, 3'))
        self.assertTrue(oAabbt not in _get_cards_for_group(aGrp,
                                                           'Groups 3, 4'))
        self.assertTrue(oNewBlood in _get_cards_for_group(aGrp, 'Groups 3, 4'))
        self.assertTrue(oNewBlood in _get_cards_for_group(aGrp, 'Groups 1, 2'))
        self.assertTrue(oNewBlood in _get_cards_for_group(aGrp, 'Groups 5, 6'))

        aGrp = list(ExpansionRarityGrouping(aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)
        self.assertTrue('VTES : Vampire' in aGrpNames)
        self.assertTrue('Jyhad : Uncommon' in aGrpNames)
        self.assertTrue('Sabbat Wars : Precon' in aGrpNames)
        self.assertTrue('Sabbat Wars : Precon Only' in aGrpNames)
        self.assertTrue(None not in aGrpNames)

        self.assertTrue(oAabbt in _get_cards_for_group(
            aGrp, 'Final Nights : Uncommon'))
        self.assertTrue(oShaEnnu in _get_cards_for_group(
            aGrp, 'Third Edition : Vampire'))
        self.assertTrue(oShaEnnu not in _get_cards_for_group(
            aGrp, 'Third Edition : Precon'))
        self.assertTrue(oSwallowed in _get_cards_for_group(
            aGrp, 'Third Edition : Common'))
        self.assertTrue(oRaven not in _get_cards_for_group(
            aGrp, 'Third Edition : Common'))
        self.assertTrue(oRaven not in _get_cards_for_group(
            aGrp, 'Third Edition : Uncommon'))
        self.assertTrue(oRaven in _get_cards_for_group(
            aGrp, 'Third Edition : Precon'))
        self.assertTrue(oRaven in _get_cards_for_group(
            aGrp, 'Lords of the Night : Precon'))
        self.assertTrue(oRaven in _get_cards_for_group(
            aGrp, 'Third Edition : Precon Only'))
        self.assertTrue(oRaven in _get_cards_for_group(
            aGrp, 'Jyhad : Uncommon'))

        aGrp = list(CryptLibraryGrouping(aCards, DEF_GET_CARD))
        self.assertEqual(['Crypt', 'Library'], _get_top_levels(aGrp))
        self.assertTrue(oSwallowed in _get_cards_for_group(aGrp, 'Library'))
        self.assertTrue(oAshur in _get_cards_for_group(aGrp, 'Library'))
        self.assertTrue(oPath in _get_cards_for_group(aGrp, 'Library'))
        self.assertTrue(oEarl in _get_cards_for_group(aGrp, 'Crypt'))
        self.assertTrue(oEarl not in _get_cards_for_group(aGrp, 'Library'))
        self.assertTrue(oAabbt not in _get_cards_for_group(aGrp, 'Library'))
        self.assertTrue(oAabbt in _get_cards_for_group(aGrp, 'Crypt'))

        aGrp = list(SectGrouping(aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)
        self.assertTrue('Camarilla' in aGrpNames)
        self.assertTrue('Sabbat' in aGrpNames)
        self.assertTrue('Laibon' in aGrpNames)

        self.assertTrue(oAabbt in _get_cards_for_group(aGrp, 'Independent'))
        self.assertTrue(oAire in _get_cards_for_group(aGrp, None))
        self.assertTrue(oShaEnnu in _get_cards_for_group(aGrp, 'Sabbat'))
        aGrp = list(TitleGrouping(aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)

        self.assertTrue(None in aGrpNames)
        self.assertTrue('Bishop' in aGrpNames)
        self.assertTrue('Prince' in aGrpNames)
        self.assertTrue('Regent' in aGrpNames)

        self.assertTrue(oAabbt in _get_cards_for_group(aGrp, None))
        self.assertTrue(oAire in _get_cards_for_group(aGrp, None))
        self.assertTrue(oShaEnnu in _get_cards_for_group(aGrp, 'Regent'))

        aGrp = list(CostGrouping(aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)
        self.assertTrue(None in aGrpNames)
        self.assertTrue('1 pool' in aGrpNames)
        self.assertTrue('1 blood' in aGrpNames)
        self.assertTrue('3 conviction' in aGrpNames)

        self.assertTrue(oEarl in _get_cards_for_group(aGrp, None))
        self.assertTrue(oAabbt in _get_cards_for_group(aGrp, None))
        self.assertTrue(oAshur in _get_cards_for_group(aGrp, None))
        self.assertTrue(oAire in _get_cards_for_group(aGrp, '1 blood'))
        self.assertTrue(oPath in _get_cards_for_group(aGrp, '1 pool'))

        aGrp = list(GroupGrouping(aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)
        self.assertTrue(None in aGrpNames)
        self.assertTrue('Group 1' in aGrpNames)
        self.assertTrue('Group 5' in aGrpNames)
        self.assertTrue('Any Group' in aGrpNames)

        self.assertTrue(oEarl in _get_cards_for_group(aGrp, 'Group 4'))
        self.assertTrue(oSwallowed in _get_cards_for_group(aGrp, None))
        self.assertTrue(oAabbt in _get_cards_for_group(aGrp, 'Group 2'))
        self.assertTrue(oNewBlood in _get_cards_for_group(aGrp, 'Any Group'))

        aGrp = list(DisciplineLevelGrouping(aCards, DEF_GET_CARD))
        aGrpNames = _get_top_levels(aGrp)
        self.assertTrue(None in aGrpNames)
        self.assertTrue('Obfuscate (inferior)' in aGrpNames)
        self.assertTrue('Obfuscate (superior)' in aGrpNames)
        self.assertTrue('Vision' in aGrpNames)

        self.assertTrue(oEarl in _get_cards_for_group(aGrp, 'Vision'))
        self.assertTrue(oSwallowed in _get_cards_for_group(
            aGrp, 'Obfuscate (superior)'))
        self.assertTrue(oAshur in _get_cards_for_group(aGrp, None))
        self.assertTrue(oAabbt in _get_cards_for_group(
            aGrp, 'Serpentis (inferior)'))
        self.assertTrue(oAabbt not in _get_cards_for_group(
            aGrp, 'Serpentis (superior)'))
        self.assertTrue(oAabbt in _get_cards_for_group(
            aGrp, 'Presence (inferior)'))
        self.assertTrue(oAabbt not in _get_cards_for_group(
            aGrp, 'Presence (superior)'))
        self.assertTrue(oAire in _get_cards_for_group(
            aGrp, 'Presence (superior)'))
        self.assertTrue(oAire not in _get_cards_for_group(
            aGrp, 'Presence (inferior)'))

    def test_physical_card_iterator(self):
        """Test behaviour on physical card lists"""

        # We rely on the abstract card checks to cover the behaviour
        # This just sanity checks using physical card lists

        aCards = list(PhysicalCard.select())
        oAabbt = IAbstractCard("Aabbt Kindred")
        fGetCard = lambda x: x.abstractCard

        aGrp = list(CryptLibraryGrouping(aCards, fGetCard))
        self.assertEqual(len(aGrp), 2)
        self.assertEqual(['Crypt', 'Library'], _get_top_levels(aGrp))

        aGrp = list(NullGrouping(aCards, fGetCard))
        self.assertEqual(len(aGrp), 1)
        self.assertEqual(len(aGrp[0][1]), len(aCards))
        self.assertTrue(aGrp[0][1][0] in aCards)

        aGrp = list(ClanGrouping(aCards, fGetCard))
        aGrpNames = _get_top_levels(aGrp)
        self.assertTrue(None in aGrpNames)
        self.assertTrue('Abomination' in aGrpNames)
        self.assertTrue('Osebo' in aGrpNames)
        self.assertTrue('Pander' in aGrpNames)

        aFollwers = [x.abstractCard for x in
                     _get_cards_for_group(aGrp, 'Follower of Set')]
        self.assertTrue(oAabbt in aFollwers)
