# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Test the white wolf card reader"""

import datetime
import unittest

from sqlobject import SQLObjectNotFound

from sutekh.base.core.BaseTables import AbstractCard
from sutekh.base.core.BaseAdapters import (IAbstractCard, IPhysicalCard,
                                           IExpansion, IRarity, IRarityPair,
                                           ICardType, IArtist, IKeyword,
                                           IPrinting)
from sutekh.base.core.DBUtility import CARDLIST_UPDATE_DATE, get_metadata_date

from sutekh.core.SutekhAdapters import (IClan, IDisciplinePair, ISect,
                                        ITitle, ICreed, IVirtue)
from sutekh.SutekhUtility import is_crypt_card, is_vampire, is_trifle
from sutekh.tests.TestCore import SutekhTest


class WhiteWolfParserTests(SutekhTest):
    """Test class for the white wolf card reader.

       Check the parsing done in SutekhTest setup and verify the results
       are correct.
       """
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods
    aExpectedCards = [
        u".44 Magnum",
        u"AK-47",
        u"Aabbt Kindred",
        u"Aaron Bathurst",
        u"Aaron Duggan, Cameron's Toady",
        u"Aaron's Feeding Razor",
        u"Abandoning the Flesh",
        u"Abbot",
        u"Abd al-Rashid",
        u"Abdelsobek",
        u"Abebe",
        u"Abjure",
        u"Ablative Skin",
        u"Abombwe",
        u"Aeron",
        u"Agent of Power",
        u"Aire of Elation",
        u"Akram",
        u"Alabástrom",
        u"Alan Sovereign",
        u"Alan Sovereign (Advanced)",
        u"Alexandra",
        u"Alfred Benezri",
        u"Ambrogino Giovanni",
        u"Amisa",
        u"An Anarch Manifesto",
        u"Anarch Railroad",
        u"Anarch Revolt",
        u"Anastasz di Zagreb",
        u"Angelica, The Canonicus",
        u'Anna "Dictatrix11" Suljic',
        u"Anson",
        u"Ashur Tablets",
        u"Aye",
        u"Baron Dieudonne",
        u"Bravo",
        u"Bronwen",
        u"Cedric",
        u"Cesewayo",
        u"Dramatic Upheaval",
        u'Earl "Shaka74" Deams',
        u"Enkidu, The Noah",
        u"Fidus, The Shrunken Beast",
        u"Ghoul Retainer",
        u"Gracis Nostinus",
        u"Gypsies",
        u"Harold Zettler, Pentex Director",
        u"Hektor",
        u"Hide the Heart",
        u"High Top",
        u"Immortal Grapple",
        u'Inez "Nurse216" Villagrande',
        u"Kabede Maru",
        u"Kemintiri (Advanced)",
        u"Living Manse",
        u"L\xe1z\xe1r Dobrescu",
        u"Motivated by Gehenna",
        u"Necromancy",
        u"New Blood",
        u"Off Kilter",
        u"Ossian",
        u"Pariah",
        u"Paris Opera House",
        u"Park Hunting Ground",
        u"Pier 13, Port of Baltimore",
        u"Political Hunting Ground",
        u"Predator's Communion",
        u"Protracted Investment",
        u"Raven Spy",
        u"Rebekka, Chantry Elder of Munich",
        u"Rock Cat",
        u'Scapelli, The Family "Mechanic"',
        u"Sha-Ennu",
        u"Shade",
        u"Sheela Na Gig",
        u"Smite",
        u"Swallowed by the Night",
        u"The Ankara Citadel, Turkey",
        u"The Path of Blood",
        u"The Siamese",
        u"The Slaughterhouse",
        u"Two Wrongs",
        u"Vox Domini",
        u"Walk of Flame",
        u"Yvette, The Hopeless",
        u"Étienne Fauberge",
        ]

    def test_basic(self):
        """Basic WW list parser tests"""
        # pylint: disable=too-many-statements, too-many-locals
        # Want a long, sequential test case to minimise repeated setups

        # Check that we've added the 'last updated' date entry
        oToday = datetime.date.today()
        self.assertEqual(get_metadata_date(CARDLIST_UPDATE_DATE), oToday)

        aCards = sorted(list(AbstractCard.select()), key=lambda oC: oC.name)

        # Check card names
        self.assertEqual(len(aCards), len(self.aExpectedCards))
        self.assertEqual([oC.name for oC in aCards], self.aExpectedCards)

        # Check Magnum
        # pylint: disable=invalid-name
        # o44 is OK here
        o44 = IAbstractCard(".44 Magnum")
        self.assertEqual(o44.canonicalName, u".44 magnum")
        self.assertEqual(o44.name, u".44 Magnum")
        self.failUnless(o44.text.startswith(u"Weapon, gun.\n2R"))
        self.failUnless(o44.text.endswith(u"each combat."))
        self.assertEqual(o44.group, None)
        self.assertEqual(o44.capacity, None)
        self.assertEqual(o44.cost, 2)
        self.assertEqual(o44.life, None)
        self.assertEqual(o44.costtype, 'pool')
        self.assertEqual(o44.level, None)

        # pylint: enable=invalid-name
        oCommon = IRarity('Common')
        oJyhad = IExpansion('Jyhad')
        oVTES = IExpansion('VTES')
        oAnthology = IExpansion('Anthology')

        self.assertTrue(oCommon in [oP.rarity for oP in o44.rarity])
        self.assertTrue(oJyhad in [oP.expansion for oP in o44.rarity])
        self.assertTrue(oVTES in [oP.expansion for oP in o44.rarity])
        self.assertTrue(oAnthology not in [oP.expansion for oP in o44.rarity])

        self.assertTrue(IRarityPair(('VTES', 'Common')) in o44.rarity)

        self.failUnless(IKeyword('gun') in o44.keywords)
        self.failUnless(IKeyword('weapon') in o44.keywords)

        # Find some discipline pairs
        oFortInf = IDisciplinePair((u"Fortitude", u"inferior"))
        oFortSup = IDisciplinePair((u"Fortitude", u"superior"))
        oQuiSup = IDisciplinePair((u"Quietus", u"superior"))
        oCelInf = IDisciplinePair((u"Celerity", u"inferior"))
        oAusInf = IDisciplinePair((u"Auspex", u"inferior"))
        oAusSup = IDisciplinePair((u"Auspex", u"superior"))
        oPreSup = IDisciplinePair((u"Presence", u"superior"))
        oObfSup = IDisciplinePair((u"Obfuscate", u"superior"))
        oAboInf = IDisciplinePair((u"Abombwe", u"inferior"))
        oAboSup = IDisciplinePair((u"Abombwe", u"superior"))
        oValSup = IDisciplinePair((u'Valeren', u"superior"))

        # Check Dobrescu
        oDob = IAbstractCard(u"L\xe1z\xe1r Dobrescu")
        self.assertEqual(oDob.canonicalName, u"l\xe1z\xe1r dobrescu")
        self.assertEqual(oDob.name, u"L\xe1z\xe1r Dobrescu")
        self.failUnless(oDob.text.startswith(
            u"Independent: L\xe1z\xe1r may move"))
        self.failUnless(oDob.text.endswith(u"as a (D) action."))
        self.assertEqual(oDob.group, 2)
        self.assertEqual(oDob.capacity, 3)
        self.assertEqual(oDob.cost, None)
        self.assertEqual(oDob.life, None)
        self.assertEqual(oDob.costtype, None)
        self.assertEqual(oDob.level, None)

        self.failUnless(IClan('Ravnos') in oDob.clan)
        self.assertEqual(len(oDob.discipline), 1)
        self.failUnless(oFortInf in oDob.discipline)
        self.assertEqual(len(oDob.cardtype), 1)
        self.failUnless(ICardType('Vampire') in oDob.cardtype)
        self.failUnless(ISect('Independent') in oDob.sect)
        self.assertEqual(len(oDob.artists), 1)
        self.failUnless(IArtist('Rebecca Guay') in oDob.artists)

        self.assertEqual(len(oDob.rulings), 1)
        oRuling = oDob.rulings[0]
        self.assertTrue(oRuling.text.startswith("Cannot use his special"))
        self.assertTrue(oRuling.text.endswith("uncontrolled region."))
        self.assertEqual(oRuling.code, "[LSJ 19990215]")

        # Check Ashur Tablets
        oAshur = IAbstractCard('Ashur Tablets')
        self.assertTrue(oAnthology in [oP.expansion for oP in oAshur.rarity])
        self.assertTrue(IRarityPair(('Anthology', 'Fixed'))
                        in oAshur.rarity)

        # Check Abstract and Physical expansions match
        for oAbs in AbstractCard.select():
            aExps = [oPair.expansion for oPair in oAbs.rarity]
            for oExp in aExps:
                try:
                    oPrint = IPrinting((oExp, None))
                    _oPair = IPhysicalCard((oAbs, oPrint))
                except SQLObjectNotFound:
                    self.fail("Missing physical card %s from expansion %s"
                              % (oAbs.name, oExp.name))

        # Check Yvette
        oYvette = IAbstractCard(u"Yvette, The Hopeless")
        self.assertEqual(oYvette.canonicalName, u"yvette, the hopeless")
        self.assertEqual(oYvette.name, u"Yvette, The Hopeless")
        self.failUnless(oYvette.text.startswith("Camarilla."))
        self.assertEqual(oYvette.group, 3)
        self.assertEqual(oYvette.capacity, 3)
        self.assertEqual(oYvette.cost, None)
        self.assertEqual(oYvette.life, None)
        self.assertEqual(oYvette.costtype, None)
        self.assertEqual(oYvette.level, None)

        self.failUnless(IClan('Toreador') in oYvette.clan)
        self.assertEqual(len(oYvette.clan), 1)
        self.assertEqual(len(oYvette.discipline), 2)
        self.failUnless(oFortInf not in oYvette.discipline)
        self.failUnless(oCelInf in oYvette.discipline)
        self.failUnless(oAusInf in oYvette.discipline)
        self.assertEqual(len(oYvette.cardtype), 1)
        self.failUnless(ICardType('Vampire') in oYvette.cardtype)
        self.failUnless(ISect('Camarilla') in oYvette.sect)
        self.assertEqual(len(oYvette.artists), 1)
        self.failUnless(IArtist('Leif Jones') in oYvette.artists)

        # Check Sha-Ennu

        oShaEnnu = IAbstractCard(u"Sha-Ennu")
        self.assertEqual(oShaEnnu.canonicalName, u"sha-ennu")
        self.assertEqual(oShaEnnu.name, u"Sha-Ennu")
        self.failUnless(oShaEnnu.text.startswith("Sabbat regent:"))
        self.failUnless(oShaEnnu.text.endswith("+2 bleed."))
        self.assertEqual(oShaEnnu.group, 4)
        self.assertEqual(oShaEnnu.capacity, 11)
        self.assertEqual(oShaEnnu.cost, None)
        self.assertEqual(oShaEnnu.life, None)
        self.assertEqual(oShaEnnu.costtype, None)
        self.assertEqual(oShaEnnu.level, None)

        self.failUnless(IClan('Tzimisce') in oShaEnnu.clan)
        self.assertEqual(len(oShaEnnu.clan), 1)
        self.assertEqual(len(oShaEnnu.discipline), 6)
        self.failUnless(oAusSup in oShaEnnu.discipline)
        self.failUnless(oAusInf not in oShaEnnu.discipline)
        self.assertEqual(len(oShaEnnu.cardtype), 1)
        self.failUnless(ICardType('Vampire') in oShaEnnu.cardtype)
        self.failUnless(ISect('Sabbat') in oShaEnnu.sect)
        self.failUnless(ITitle('Regent') in oShaEnnu.title)
        self.assertTrue(IRarityPair(('Third', 'Vampire')) in oShaEnnu.rarity)
        self.assertFalse(IRarityPair(('VTES', 'Common')) in oShaEnnu.rarity)
        self.assertFalse(IRarityPair(('VTES', 'Vampire')) in oShaEnnu.rarity)
        self.assertEqual(len(oShaEnnu.artists), 1)
        self.failUnless(IArtist('Richard Thomas') in oShaEnnu.artists)

        self.failUnless(IKeyword('0 stealth') in oShaEnnu.keywords)
        self.failUnless(IKeyword('0 intercept') in oShaEnnu.keywords)
        self.failUnless(IKeyword('1 strength') in oShaEnnu.keywords)
        self.failUnless(IKeyword('3 bleed') in oShaEnnu.keywords)

        # Check Kabede

        oKabede = IAbstractCard(u"Kabede Maru")
        self.assertEqual(oKabede.canonicalName, u"kabede maru")
        self.assertEqual(oKabede.name, u"Kabede Maru")
        self.failUnless(oKabede.text.startswith("Laibon magaji:"))
        self.failUnless(oKabede.text.endswith("affect Kabede.)"))
        self.assertEqual(oKabede.group, 5)
        self.assertEqual(oKabede.capacity, 9)
        self.assertEqual(oKabede.cost, None)
        self.assertEqual(oKabede.life, None)
        self.assertEqual(oKabede.costtype, None)
        self.assertEqual(oKabede.level, None)

        self.failUnless(IClan('Assamite') in oKabede.clan)
        self.assertEqual(len(oKabede.clan), 1)
        self.assertEqual(len(oKabede.discipline), 6)
        self.failUnless(oAusSup in oKabede.discipline)
        self.failUnless(oQuiSup in oKabede.discipline)
        self.failUnless(oAboInf in oKabede.discipline)
        self.failUnless(oAboSup not in oKabede.discipline)
        self.assertEqual(len(oKabede.cardtype), 1)
        self.failUnless(ICardType('Vampire') in oKabede.cardtype)
        self.failUnless(ISect('Laibon') in oKabede.sect)
        self.failUnless(ITitle('Magaji') in oKabede.title)
        self.assertTrue(IRarityPair(('LotN', 'Uncommon')) in oKabede.rarity)
        self.assertEqual(len(oKabede.artists), 1)
        self.failUnless(IArtist('Ken Meyer, Jr.') in oKabede.artists)

        self.failUnless(IKeyword('0 stealth') in oKabede.keywords)
        self.failUnless(IKeyword('0 intercept') in oKabede.keywords)
        self.failUnless(IKeyword('1 strength') in oKabede.keywords)
        self.failUnless(IKeyword('1 bleed') in oKabede.keywords)

        # Check Predator's Communion
        oPredComm = IAbstractCard(u"Predator's Communion")
        self.assertEqual(oPredComm.canonicalName, u"predator's communion")
        self.assertEqual(oPredComm.name, u"Predator's Communion")
        self.failUnless(oPredComm.text.startswith("[abo] [REFLEX]"))
        self.failUnless(oPredComm.text.endswith("unlocks."))
        self.assertEqual(oPredComm.group, None)
        self.assertEqual(oPredComm.capacity, None)
        self.assertEqual(oPredComm.cost, None)
        self.assertEqual(oPredComm.life, None)
        self.assertEqual(oPredComm.costtype, None)
        self.assertEqual(oPredComm.level, None)

        self.assertEqual(len(oPredComm.discipline), 1)
        self.failUnless(oAboSup in oPredComm.discipline)
        self.assertEqual(len(oPredComm.cardtype), 2)
        self.failUnless(ICardType('Reaction') in oPredComm.cardtype)
        self.failUnless(ICardType('Reflex') in oPredComm.cardtype)
        self.assertTrue(IRarityPair(('LoB', 'Common')) in oPredComm.rarity)
        self.assertEqual(len(oPredComm.artists), 1)
        self.failUnless(IArtist('David Day') in oPredComm.artists)

        # Check Earl
        oEarl = IAbstractCard(u'Earl "Shaka74" Deams')
        self.assertEqual(oEarl.canonicalName, u'earl "shaka74" deams')
        self.assertEqual(oEarl.name, u'Earl "Shaka74" Deams')
        self.failUnless(oEarl.text.startswith("Earl gets +1 stealth"))
        self.failUnless(oEarl.text.endswith("[1 CONVICTION]."))
        self.assertEqual(oEarl.group, 4)
        self.assertEqual(oEarl.capacity, None)
        self.assertEqual(oEarl.cost, None)
        self.assertEqual(oEarl.life, 6)
        self.assertEqual(oEarl.costtype, None)
        self.assertEqual(oEarl.level, None)

        self.failUnless(ICreed('Visionary') in oEarl.creed)
        self.assertEqual(len(oEarl.creed), 1)
        self.assertEqual(len(oEarl.virtue), 3)
        self.failUnless(IVirtue('Martyrdom') in oEarl.virtue)
        self.failUnless(IVirtue('Judgment') in oEarl.virtue)
        self.failUnless(IVirtue('Vision') in oEarl.virtue)
        self.assertEqual(len(oEarl.cardtype), 1)
        self.failUnless(ICardType('Imbued') in oEarl.cardtype)
        self.assertTrue(IRarityPair(('NoR', 'Uncommon')) in oEarl.rarity)
        self.assertEqual(len(oEarl.artists), 1)
        self.failUnless(IArtist('David Day') in oEarl.artists)

        # Check Aire
        oAire = IAbstractCard("Aire of Elation")
        self.assertEqual(oAire.canonicalName, u"aire of elation")
        self.assertEqual(oAire.name, u"Aire of Elation")
        self.failUnless(oAire.text.startswith("You cannot play another"))
        self.failUnless(oAire.text.endswith("is Toreador."))
        self.assertEqual(oAire.group, None)
        self.assertEqual(oAire.capacity, None)
        self.assertEqual(oAire.cost, 1)
        self.assertEqual(oAire.life, None)
        self.assertEqual(oAire.costtype, 'blood')
        self.assertEqual(oAire.level, None)

        self.assertEqual(len(oAire.discipline), 1)
        self.failUnless(oPreSup in oAire.discipline)
        self.assertEqual(len(oAire.cardtype), 1)
        self.failUnless(ICardType("Action Modifier") in oAire.cardtype)

        self.assertTrue(IRarityPair(('DS', 'Common')) in oAire.rarity)
        self.assertTrue(IRarityPair(('FN', 'Precon')) in oAire.rarity)
        self.assertTrue(IRarityPair(('CE', 'Common')) in oAire.rarity)
        self.assertTrue(IRarityPair(('CE', 'Precon')) in oAire.rarity)
        self.assertTrue(IRarityPair(('Anarchs', 'Precon')) in oAire.rarity)
        self.assertTrue(IRarityPair(('KMW', 'Precon')) in oAire.rarity)

        self.assertEqual(len(oAire.artists), 1)
        self.failUnless(IArtist('Greg Simanson') in oAire.artists)

        # Abjure
        oAbjure = IAbstractCard("Abjure")
        self.assertEqual(oAbjure.canonicalName, u"abjure")
        self.assertEqual(oAbjure.name, u"Abjure")
        self.failUnless(oAbjure.text.startswith("[COMBAT] Lock this"))
        self.failUnless(oAbjure.text.endswith("or ash heap."))
        self.assertEqual(oAbjure.group, None)
        self.assertEqual(oAbjure.capacity, None)
        self.assertEqual(oAbjure.cost, None)
        self.assertEqual(oAbjure.life, None)
        self.assertEqual(oAbjure.costtype, None)
        self.assertEqual(oAbjure.level, None)

        self.assertEqual(len(oAbjure.virtue), 1)
        self.failUnless(IVirtue('Redemption') in oAbjure.virtue)
        self.assertEqual(len(oAbjure.cardtype), 1)
        self.failUnless(ICardType('Power') in oAbjure.cardtype)
        self.assertEqual(len(oAbjure.artists), 1)
        self.failUnless(IArtist('Brian LeBlanc') in oAbjure.artists)

        # Abombwe Master Card
        oAbo = IAbstractCard('Abombwe')

        self.assertEqual(oAbo.canonicalName, 'abombwe')
        self.assertEqual(oAbo.name, 'Abombwe')
        self.failUnless(oAbo.text.startswith("Master: Discipline. Trifle"))
        self.failUnless(oAbo.text.endswith("superior Abombwe."))
        self.assertEqual(oAbo.group, None)
        self.assertEqual(oAbo.capacity, 1)
        self.assertEqual(oAbo.cost, None)
        self.assertEqual(oAbo.life, None)
        self.assertEqual(oAbo.costtype, None)
        self.assertEqual(oAbo.level, None)


        self.assertEqual(len(oAbo.discipline), 0)
        self.assertEqual(len(oAbo.cardtype), 1)
        self.failUnless(ICardType('Master') in oAbo.cardtype)
        self.assertEqual(len(oAbo.rulings), 0)
        self.assertEqual(len(oAbo.artists), 1)
        self.failUnless(IArtist('Ken Meyer, Jr.') in oAbo.artists)

        self.failUnless(IKeyword('trifle') in oAbo.keywords)
        self.failUnless(IKeyword('discipline') in oAbo.keywords)

        # Ablative Skin Card
        oAblat = IAbstractCard('Ablative Skin')

        self.assertEqual(oAblat.canonicalName, 'ablative skin')
        self.assertEqual(oAblat.name, 'Ablative Skin')
        self.failUnless(oAblat.text.startswith("+1 stealth action"))
        self.failUnless(oAblat.text.endswith("damage in combat in this way."))
        self.assertEqual(oAblat.group, None)
        self.assertEqual(oAblat.cost, None)
        self.assertEqual(oAblat.life, None)
        self.assertEqual(oAblat.costtype, None)
        self.assertEqual(oAblat.level, None)

        self.assertEqual(len(oAblat.discipline), 1)
        self.failUnless(oFortSup in oAblat.discipline)
        self.assertEqual(len(oAblat.cardtype), 1)
        self.failUnless(ICardType('Action') in oAblat.cardtype)
        self.assertEqual(len(oAblat.rulings), 1)
        oRuling = oAblat.rulings[0]
        self.assertTrue(oRuling.text.startswith("Cannot be used to prevent"))
        self.assertTrue(oRuling.text.endswith("Blood Fury)."))
        self.assertEqual(oRuling.code, "[LSJ 19990216]")
        self.assertEqual(len(oAblat.artists), 1)
        self.failUnless(IArtist('Richard Thomas') in oAblat.artists)

        # Check Independent titles
        oAmbrig = IAbstractCard(u"Ambrogino Giovanni")
        self.failUnless(ITitle('Independent with 1 vote') in oAmbrig.title)
        oAmisa = IAbstractCard(u"Amisa")
        self.failUnless(ITitle('Independent with 2 votes') in oAmisa.title)

        # Check Kemintiri
        oKemintiri = IAbstractCard(u"Kemintiri (Advanced)")
        self.assertEqual(oKemintiri.canonicalName, u"kemintiri (advanced)")
        self.assertEqual(oKemintiri.name, u"Kemintiri (Advanced)")
        self.failUnless(oKemintiri.text.startswith("Advanced, Independent."))
        self.assertEqual(oKemintiri.group, 2)
        self.assertEqual(oKemintiri.capacity, 10)
        self.assertEqual(oKemintiri.cost, None)
        self.assertEqual(oKemintiri.life, None)
        self.assertEqual(oKemintiri.costtype, None)
        self.assertEqual(oKemintiri.level, 'advanced')
        self.failUnless(IKeyword('advanced') in oKemintiri.keywords)

        self.failUnless(IClan('Follower of Set') in oKemintiri.clan)
        self.assertEqual(len(oKemintiri.clan), 1)
        self.assertEqual(len(oKemintiri.discipline), 6)
        self.failUnless(oAusInf in oKemintiri.discipline)
        self.failUnless(oObfSup in oKemintiri.discipline)
        self.failUnless(oPreSup in oKemintiri.discipline)
        self.assertEqual(len(oKemintiri.cardtype), 1)
        self.failUnless(ICardType('Vampire') in oKemintiri.cardtype)
        self.failUnless(ISect('Independent') in oKemintiri.sect)
        self.assertEqual(len(oKemintiri.artists), 1)
        self.failUnless(IArtist('Lawrence Snelly') in oKemintiri.artists)

        # Make sure we're not picking up the Merged title
        self.assertEqual(len(oKemintiri.title), 0)
        self.assertTrue(IRarityPair(('KMW', 'Uncommon')) in oKemintiri.rarity)

        # Check ANY group handling
        oNewBlood = IAbstractCard('New Blood')
        self.assertEqual(oNewBlood.group, -1)
        self.assertEqual(oNewBlood.capacity, 2)
        self.assertEqual(oNewBlood.life, None)
        self.assertEqual(oNewBlood.cost, None)

        self.failUnless(IClan('Blood Brother') in oNewBlood.clan)
        self.assertEqual(len(oNewBlood.clan), 1)
        self.assertEqual(len(oNewBlood.discipline), 1)
        self.assertTrue('belongs to the chosen circle.' in oNewBlood.text)

        # Check The Path
        oPath1 = IAbstractCard('The Path of Blood')

        self.failUnless(IClan('Assamite') in oPath1.clan)
        self.assertEqual(oPath1.cost, 1)
        self.assertEqual(oPath1.costtype, 'pool')
        self.failUnless(ICardType('Master') in oPath1.cardtype)

        self.failUnless(IKeyword('unique') in oPath1.keywords)

        # Check alternative lookup
        oPath2 = IAbstractCard('Path of Blood, The')
        self.assertEqual(oPath1.id, oPath2.id)

        # Check The Slaughterhouse
        oSlaughter = IAbstractCard('The Slaughterhouse')
        self.assertEqual(oSlaughter.canonicalName, u"the slaughterhouse")
        self.assertEqual(len(oSlaughter.keywords), 2)
        self.failUnless(IKeyword('burn option') in oSlaughter.keywords)
        self.failUnless(IKeyword('location') in oSlaughter.keywords)

        # Check keywords for The Ankara Citadel, Turkey
        oCitadel = IAbstractCard('The Ankara Citadel, Turkey')
        self.assertEqual(oCitadel.cost, 2)
        self.failUnless(IClan('Tremere') in oCitadel.clan)
        self.assertEqual(oCitadel.costtype, 'blood')
        self.failUnless(IKeyword('location') in oCitadel.keywords)
        self.failUnless(IKeyword('unique') in oCitadel.keywords)

        # Check life & keywords for Ossian
        oOssian = IAbstractCard('Ossian')
        self.assertEqual(oOssian.life, 4)
        self.assertEqual(oOssian.cost, 3)
        self.assertEqual(oOssian.costtype, 'pool')
        self.failUnless(IKeyword('werewolf') in oOssian.keywords)
        self.failUnless(IKeyword('red list') in oOssian.keywords)
        self.failUnless(IKeyword('unique') in oOssian.keywords)
        self.failUnless(IKeyword('0 bleed') in oOssian.keywords)
        self.failUnless(IKeyword('2 strength') in oOssian.keywords)

        # Check life & keywords for Raven Spy
        oRaven = IAbstractCard('Raven Spy')
        self.failUnless(IKeyword('animal') in oRaven.keywords)
        self.failUnless(IKeyword('1 strength') not in oRaven.keywords)
        self.assertEqual(oRaven.life, 1)
        self.assertEqual(oRaven.cost, 1)
        self.assertEqual(oRaven.costtype, 'blood')

        # Check slave keywords for Fidus and Sheela Na Gig
        oFidus = IAbstractCard(u"Fidus, The Shrunken Beast")
        self.assertTrue(IKeyword('tremere slave') in oFidus.keywords)

        oSheela = IAbstractCard(u"Sheela Na Gig")
        self.assertTrue(IKeyword('tremere antitribu slave')
                        in oSheela.keywords)

        # Check for Anarch sect status
        oAlab = IAbstractCard(u"Alabástrom")
        self.failUnless(ISect('Anarch') in oAlab.sect)

        # Check special cases
        oRetainer = IAbstractCard('Ghoul Retainer')
        self.failUnless(IKeyword('1 strength') in oRetainer.keywords)
        oHighTop = IAbstractCard('High Top')
        self.failUnless(IKeyword('1 intercept') in oHighTop.keywords)
        oGypsies = IAbstractCard('Gypsies')
        self.failUnless(IKeyword('1 stealth') in oGypsies.keywords)
        # Check brace normalisation
        self.failUnless('{strength' in oGypsies.text)
        self.failUnless('{mortal' in oGypsies.text)
        self.assertTrue('-{' not in oGypsies.text)
        # check brace filtering
        self.assertTrue('{' not in oGypsies.search_text)
        oRebekka = IAbstractCard('Rebekka, Chantry Elder of Munich')
        self.failUnless(IKeyword('1 stealth') in oRebekka.keywords)
        oProtracted = IAbstractCard('Protracted Investment')
        self.failUnless(IKeyword('investment') in oProtracted.keywords)
        oBravo = IAbstractCard('Bravo')
        self.failUnless(IKeyword('archetype') in oBravo.keywords)
        oDramatic = IAbstractCard('Dramatic Upheaval')
        self.failUnless(IKeyword('not for legal play') in oDramatic.keywords)
        oMotivated = IAbstractCard('Motivated by Gehenna')
        self.failUnless(IKeyword('not for legal play') in oMotivated.keywords)
        oAaron = IAbstractCard("Aaron's Feeding Razor")
        self.failUnless(IKeyword('unique') in oAaron.keywords)

        # Test adding extra expansions works

        oAnarchRailroad = IAbstractCard("Anarch Railroad")
        self.assertEqual(oAnarchRailroad.canonicalName, u"anarch railroad")
        self.assertEqual(oAnarchRailroad.cost, 2)
        self.assertEqual(oAnarchRailroad.costtype, 'pool')
        self.failUnless(oAnarchRailroad.text.startswith(u"Master: unique"))
        oAnarchs = IExpansion('Anarchs')
        oAA = IExpansion('Anarchs and Alastors Storyline')

        self.assertTrue(oAnarchs in [oP.expansion for oP in
                                     oAnarchRailroad.rarity])
        self.assertTrue(oAA in [oP.expansion for oP in oAnarchRailroad.rarity])

        oAnarchRevolt = IAbstractCard("Anarch Revolt")
        self.assertEqual(oAnarchRevolt.canonicalName, u"anarch revolt")
        self.assertEqual(oAnarchRevolt.cost, None)
        self.failUnless(oAnarchRevolt.text.startswith(u"Master."))

        self.assertTrue(oAnarchs in [oP.expansion for oP in
                                     oAnarchRevolt.rarity])
        self.assertTrue(oAA in [oP.expansion for oP in oAnarchRevolt.rarity])
        self.assertTrue(oJyhad in [oP.expansion for oP in
                                   oAnarchRevolt.rarity])

        oHtH = IAbstractCard("Hide the Heart")
        self.assertEqual(oHtH.canonicalName, u"hide the heart")
        self.assertEqual(len(oHtH.discipline), 2)
        self.failUnless(oAusSup in oHtH.discipline)
        self.failUnless(oValSup in oHtH.discipline)
        self.assertEqual(len(oHtH.cardtype), 1)
        self.failUnless(ICardType("Reaction") in oHtH.cardtype)
        self.failUnless(oHtH.text.startswith('[aus] Reduce'))

        self.assertTrue(IRarityPair(('HttB', 'Common')) in oHtH.rarity)
        self.assertTrue(IRarityPair(('Black Chantry', 'Fixed')) in oHtH.rarity)
        self.assertTrue(IRarityPair(('HttB', 'Precon')) in oHtH.rarity)

        oSmite = IAbstractCard("Smite")
        self.assertEqual(oSmite.canonicalName, u"smite")
        self.assertEqual(oSmite.cost, 3)
        self.assertEqual(oSmite.costtype, "conviction")
        self.failUnless(oSmite.text.startswith('{Strike:}'))

        # Check for Black Chantry Expansion data
        oBaronD = IAbstractCard('Baron Dieudonne')
        oKoT = IExpansion('Keepers of Tradition')
        oBC = IExpansion('Black Chantry')
        # Check we handle the conversion of our old name for the Black Chantry
        # cards correctly
        oBCold = IExpansion('Black Chantry Reprint')
        self.assertEqual(oBC, oBCold)
        self.assertTrue(oKoT in [oP.expansion for oP in oBaronD.rarity])
        self.assertTrue(oBC in [oP.expansion for oP in oBaronD.rarity])
        # Check that we also pick up the BC expansion for Hide the Heart
        self.assertTrue(oBC in [oP.expansion for oP in oHtH.rarity])
        self.assertFalse(oKoT in [oP.expansion for oP in oHtH.rarity])

        # Check we get the rarity for Aye correct
        oAye = IAbstractCard("Aye")
        self.assertEqual(oAye.canonicalName, u"aye")
        oLoB = IExpansion('Legacy of Blood')
        oEK = IExpansion('EK')
        # Check some expansion properties while we're here
        self.assertEqual(oLoB.name, 'Legacy of Blood')
        self.assertEqual(oLoB.shortname, 'LoB')
        self.assertEqual(oEK.name, 'Ebony Kingdom')
        self.assertEqual(oEK.shortname, 'EK')
        self.assertTrue(oLoB in [oP.expansion for oP in oAye.rarity])
        self.assertTrue(oEK in [oP.expansion for oP in oAye.rarity])
        self.assertTrue(oCommon in [oP.rarity for oP in oAye.rarity])
        # Check that we only got 1 rarity for Aye
        self.assertEqual(set([oCommon]),
                         set([oP.rarity for oP in oAye.rarity]))

        self.assertTrue(IRarityPair(('LoB', 'Common')) in oAye.rarity)
        self.assertTrue(IRarityPair(('EK', 'Common')) in oAye.rarity)


    def test_card_type_checkers(self):
        """Check the various utilities for checking card type
           and properties."""
        oDob = IAbstractCard(u"L\xe1z\xe1r Dobrescu")
        self.assertTrue(is_vampire(oDob))
        self.assertTrue(is_crypt_card(oDob))
        self.assertFalse(is_trifle(oDob))

        oAbo = IAbstractCard('Abombwe')
        self.assertFalse(is_vampire(oAbo))
        self.assertFalse(is_crypt_card(oAbo))
        self.assertTrue(is_trifle(oAbo))

        oAshur = IAbstractCard('Ashur Tablets')
        self.assertFalse(is_vampire(oAshur))
        self.assertFalse(is_crypt_card(oAshur))
        self.assertFalse(is_trifle(oAshur))

        oEarl = IAbstractCard(u'Earl "Shaka74" Deams')
        self.assertFalse(is_vampire(oEarl))
        self.assertTrue(is_crypt_card(oEarl))
        self.assertFalse(is_trifle(oEarl))

        oOssian = IAbstractCard('Ossian')
        self.assertFalse(is_vampire(oOssian))
        self.assertFalse(is_crypt_card(oOssian))
        self.assertFalse(is_trifle(oOssian))

    def test_adapters(self):
        """Extra sanity checks on the adapaters."""
        for oAdapter in (IAbstractCard, IPhysicalCard,
                         IExpansion, IRarity, IRarityPair,
                         ICardType, IArtist, IKeyword):
            self.assertRaises(NotImplementedError, oAdapter, 1)
            self.assertRaises(NotImplementedError, oAdapter, None)

        # Various pass through tests
        self.assertEqual(IAbstractCard("Ossian"),
                         IAbstractCard(IAbstractCard("Ossian")))
        oExp = IExpansion("KMW")
        self.assertEqual(oExp, IExpansion(oExp))

        oPrinting = IPrinting((oExp, None))
        self.assertEqual(oPrinting, IPrinting(oPrinting))

        oPhysCard = IPhysicalCard((IAbstractCard("Ossian"), oPrinting))
        self.assertEqual(oPhysCard, IPhysicalCard(oPhysCard))
        self.assertEqual(oPhysCard.abstractCard, IAbstractCard("Ossian"))
        self.assertEqual(oPhysCard.abstractCard, IAbstractCard(oPhysCard))

        self.assertEqual(IArtist("Lawrence Snelly"),
                         IArtist(IArtist("Lawrence Snelly")))
        self.assertEqual(IKeyword('not for legal play'),
                         IKeyword(IKeyword('not for legal play')))
        self.assertEqual(IRarity("Common"), IRarity(IRarity("Common")))
        self.assertEqual(IRarityPair(("EK", "Common")),
                         IRarityPair(IRarityPair(("EK", "Common"))))
        self.assertEqual(ICardType("Vampire"), ICardType(ICardType("Vampire")))


if __name__ == "__main__":
    unittest.main()
