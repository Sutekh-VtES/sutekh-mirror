# test_WhiteWolfParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Test the white wolf card reader"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.core.SutekhObjects import AbstractCard, IAbstractCard, \
        IPhysicalCard, IClan, IDisciplinePair, ICardType, ISect, ITitle, \
        ICreed, IVirtue, IExpansion, IRarity, IRarityPair
from sqlobject import SQLObjectNotFound
import unittest

class WhiteWolfParserTests(SutekhTest):
    """Test class for the white wolf card reader.

       Check the parsing done in SutekhTest setup and verify the results
       are correct.
       """
    aExpectedCards = [
        u".44 Magnum", u"AK-47", u"Aabbt Kindred",
        u"Aaron Bathurst", u"Aaron Duggan, Cameron's Toady",
        u"Aaron's Feeding Razor", u"Abandoning the Flesh",
        u"Abbot", u"Abd al-Rashid", u"Abdelsobek",
        u"Abebe", u"Abjure", u"Ablative Skin",
        u"Abombwe", u"Aeron", u"Aire of Elation", u"Akram",
        u"Alan Sovereign", u"Alan Sovereign (Advanced)", u"Alexandra",
        u"Alfred Benezri", u"Ambrogino Giovanni", u'Amisa',
        u"Anastasz di Zagreb", u"Angelica, The Canonicus",
        u'Anna "Dictatrix11" Suljic', u"Anson", u"Bronwen", u"Cedric",
        u"Cesewayo", u'Earl "Shaka74" Deams', u"Gracis Nostinus",
        u'Inez "Nurse216" Villagrande', u"Kabede Maru",
        u"Kemintiri (Advanced)", u"L\xe1z\xe1r Dobrescu",
        u"Predator's Communion", u"Sha-Ennu", u"The Path of Blood",
        u"Yvette, The Hopeless",
        ]

    def test_basic(self):
        """Basic WW list parser tests"""
        # pylint: disable-msg=E1101, R0915, R0914
        # E1101: SQLObject + PyProtocols magic confuses pylint
        # R0915, R0914: Want a long, sequential test case to minimise
        aCards = sorted(list(AbstractCard.select()), cmp=lambda oC1, oC2:
                cmp(oC1.name, oC2.name))

        # Check card names
        self.assertEqual([oC.name for oC in aCards], self.aExpectedCards)

        # Check Magnum
        # pylint: disable-msg=C0103
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

        # pylint: enable-msg=C0103
        oCommon = IRarity('Common')
        oJyhad = IExpansion('Jyhad')
        oVTES = IExpansion('VTES')

        self.assertTrue(oCommon in [oP.rarity for oP in o44.rarity])
        self.assertTrue(oJyhad in [oP.expansion for oP in o44.rarity])
        self.assertTrue(oVTES in [oP.expansion for oP in o44.rarity])

        self.assertTrue(IRarityPair(('VTES', 'Common')) in o44.rarity)


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

        self.assertEqual(len(oDob.rulings), 1)
        oRuling = oDob.rulings[0]
        self.assertTrue(oRuling.text.startswith("Cannot use his special"))
        self.assertTrue(oRuling.text.endswith("uncontrolled region."))
        self.assertEqual(oRuling.code, "[LSJ19990215]")

        # Check Abstract and Physical expansions match
        for oAbs in AbstractCard.select():
            aExps = [oPair.expansion for oPair in oAbs.rarity]
            for oExp in aExps:
                try:
                    oPair = IPhysicalCard((oAbs, oExp))
                except SQLObjectNotFound:
                    self.fail(
                        "Missing physical card %s from expansion %s"
                        % (oAbs.name, oExp.name)
                    )

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

        # Check Predator's Communion
        oPredComm = IAbstractCard(u"Predator's Communion")
        self.assertEqual(oPredComm.canonicalName, u"predator's communion")
        self.assertEqual(oPredComm.name, u"Predator's Communion")
        self.failUnless(oPredComm.text.startswith("[abo] [REFLEX]"))
        self.failUnless(oPredComm.text.endswith("untaps."))
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

        # Abjure
        oAbjure = IAbstractCard("Abjure")
        self.assertEqual(oAbjure.canonicalName, u"abjure")
        self.assertEqual(oAbjure.name, u"Abjure")
        self.failUnless(oAbjure.text.startswith("[COMBAT] Tap this"))
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
        self.assertEqual(oRuling.code, "[LSJ19990216]")

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

        self.failUnless(IClan('Follower of Set') in oKemintiri.clan)
        self.assertEqual(len(oKemintiri.clan), 1)
        self.assertEqual(len(oKemintiri.discipline), 6)
        self.failUnless(oAusInf in oKemintiri.discipline)
        self.failUnless(oObfSup in oKemintiri.discipline)
        self.failUnless(oPreSup in oKemintiri.discipline)
        self.assertEqual(len(oKemintiri.cardtype), 1)
        self.failUnless(ICardType('Vampire') in oKemintiri.cardtype)
        self.failUnless(ISect('Independent') in oKemintiri.sect)
        # Make sure we're not picking up the Merged title
        self.assertEqual(len(oKemintiri.title), 0)
        self.assertTrue(IRarityPair(('KMW', 'Uncommon')) in oKemintiri.rarity)


if __name__ == "__main__":
    unittest.main()
