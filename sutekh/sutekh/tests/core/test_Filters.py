# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Sutekh Filters tests"""

import unittest
from sqlobject import SQLObjectNotFound
from sutekh.tests.TestCore import SutekhTest
from sutekh.base.tests.TestUtils import make_card
from sutekh.tests.io import test_WhiteWolfParser
from sutekh.base.core.BaseTables import (AbstractCard, PhysicalCard,
                                         Printing, PhysicalCardSet,
                                         MapPhysicalCardToPhysicalCardSet)
from sutekh.base.core.BaseAdapters import (IAbstractCard, IPhysicalCard,
                                           IExpansion, IPrinting)
from sutekh.core import Filters
from sutekh.base.core import BaseFilters


def make_physical_card_sets():
    """Create the set of physical card sets used for testing"""
    aCardSets = [
        ('Test 1', 'Author A', 'A set', False),
        ('Test 2', 'Author B', 'Another set', False),
        ('Test 3', 'Author A', 'Something different', True)
    ]
    aPCSCards = [
        # Set 1
        [('Abombwe', None), ('Alexandra', 'CE'),
         ('Sha-Ennu', None), ('Sha-Ennu', None), ('Sha-Ennu', None),
         ('Sha-Ennu', 'Third Edition')],
        # Set 2
        [('Sha-Ennu', 'Third Edition'), ('Anson', 'Jyhad'),
         ('.44 magnum', 'Jyhad'), ('ak-47', 'LotN'),
         ('Alexandra', 'CE'), ('Alexandra', 'CE')],
        # Set 3
        [('Yvette, The Hopeless', 'BSC')]
    ]
    aPCSs = []
    for iCnt, tData in enumerate(aCardSets):
        sName, sAuthor, sComment, bInUse = tData
        if bInUse:
            oParent = aPCSs[0]
        else:
            oParent = None
        oPCS = PhysicalCardSet(name=sName, comment=sComment,
                               author=sAuthor, inuse=bInUse,
                               parent=oParent)
        for sName, sExp in aPCSCards[iCnt]:
            # pylint: disable=no-member
            # SQLObect confused pylint
            oPhys = make_card(sName, sExp)
            oPCS.addPhysicalCard(oPhys.id)
        aPCSs.append(oPCS)
    return aPCSs


class FilterTests(SutekhTest):
    """Test class for testing Sutekh Filters"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods
    aExpectedCards = test_WhiteWolfParser.WhiteWolfParserTests.aExpectedCards

    def _physical_test(self, tTest):
        # pylint: disable=too-many-locals, too-many-branches
        # This is a fairly linear function and everything is required,
        # so there's not a lot of value to dividing it further
        """Convert the tuple describing the test as a filter and a list of
           card names and optional expansions into the correct
           filter on the physical card list and a list of expected
           PhysicalCard objects."""
        if len(tTest) < 2 or len(tTest) > 4:
            raise RuntimeError("Invalid input to _physical_test: %s" % tTest)
        if len(tTest) == 2:
            oFilter, aExpectedNames = tTest
            aAllowedPrintings = set(Printing.select())
            aAllowedPrintings.add(None)
        else:
            oFilter, aExpectedNames = tTest[:2]
            aAllowedPrintings = set()
            aExp = [IExpansion(sExp) if sExp else None for sExp in tTest[2]]
            if len(tTest) == 3:
                # Add all the printings for each expansion
                for oExp in aExp:
                    if oExp:
                        for oPrint in oExp.printings:
                            aAllowedPrintings.add(oPrint)
                    else:
                        aAllowedPrintings.add(oExp)
            else:
                # Only added the specified printings
                for oExp, sPrint in zip(aExp, tTest[3]):
                    oPrint = IPrinting((oExp, sPrint))
                    aAllowedPrintings.add(oPrint)
        aPhysicalCards = []
        for sName in aExpectedNames:
            oAbs = IAbstractCard(sName)
            aExps = {oRarity.expansion for oRarity in oAbs.rarity}

            if None in aAllowedPrintings:
                aPhysicalCards.append(IPhysicalCard((oAbs, None)))

            for oExp in aExps:
                for oPrint in oExp.printings:
                    if oPrint not in aAllowedPrintings:
                        continue
                    try:
                        oCard = IPhysicalCard((oAbs, oPrint))
                        aPhysicalCards.append(oCard)
                    except SQLObjectNotFound:
                        # If the printing name isn't None, we
                        # assume the abstract card just isn't in that
                        # variant
                        if oPrint.name is None:
                            # this is fatal
                            self.fail(
                                "Missing physical card %s from expansion %s"
                                % (oAbs.name, oExp.name))

        oFullFilter = Filters.FilterAndBox([Filters.PhysicalCardFilter(),
                                            oFilter])

        return oFullFilter, sorted(aPhysicalCards, key=lambda x: x.id)

    def _convert_to_phys_cards(self, aList):
        """Converts a list of Name, Expansion Name tuples into physical
           cards"""
        aPhysCards = []
        for sName, sExp in aList:
            try:
                oCard = make_card(sName, sExp)
                aPhysCards.append(oCard)
            except SQLObjectNotFound:
                self.fail("Invalid physical card (%s from expansion %s)"
                          % (sName, sExp))
        return sorted(aPhysCards, key=lambda x: x.id)

    # pylint: disable=too-many-locals
    # We don't really care about the number of local variables here
    def test_basic(self):
        """Simple tests of the filter"""
        # setup filters
        aTests = [
            # Single / Multi Filters
            (Filters.ClanFilter('Follower of Set'),
             [u"Aabbt Kindred", u"Abdelsobek", u"Amisa",
              u"Kemintiri (Advanced)"]),
            (Filters.MultiClanFilter(['Ravnos', 'Samedi']),
             [u"Abebe", u"L\xe1z\xe1r Dobrescu", u"Off Kilter",
              u"Park Hunting Ground", u"\xc9tienne Fauberge"]),
            (Filters.DisciplineFilter('obf'),
             [u"Aaron Bathurst", u"Abd al-Rashid", u"Abdelsobek", u"Abebe",
              u"Aeron", u"Amisa", u"Angelica, The Canonicus",
              u"Baron Dieudonne", u"Cedric",
              u"Enkidu, The Noah", u"Harold Zettler, Pentex Director",
              u"Kabede Maru", u"Kemintiri (Advanced)",
              u"Pariah", u"Sha-Ennu", u'Swallowed by the Night']),
            (Filters.DisciplineFilter('fli'),
             [u'Alab\xe1strom', u"Cedric", u"Fidus, The Shrunken Beast",
              u"Sheela Na Gig"]),
            (Filters.MultiDisciplineFilter(['nec', 'qui']),
             [u"Abd al-Rashid", u"Abdelsobek", u"Abebe", u"Akram",
              u"Ambrogino Giovanni", u"Hektor", u"Kabede Maru"]),
            (Filters.ExpansionFilter('NoR'),
             [u"Abjure", u'Anna "Dictatrix11" Suljic',
              u'Earl "Shaka74" Deams', u'Inez "Nurse216" Villagrande',
              u'Smite']),
            (Filters.MultiExpansionFilter(['NoR', 'LoB']),
             [u".44 Magnum", u"Abebe", u"Abjure", u"Abombwe",
              u'Anna "Dictatrix11" Suljic', u"Aye", u"Cedric", u"Cesewayo",
              u'Earl "Shaka74" Deams', u"High Top",
              u'Inez "Nurse216" Villagrande', u"Paris Opera House",
              u"Predator's Communion", u"Rock Cat", u'Smite',
              u"The Slaughterhouse", u"Vox Domini"]),
            (Filters.ExpansionRarityFilter(('Sabbat', 'Rare')),
             [u"Ablative Skin", u"Living Manse"]),
            (Filters.ExpansionRarityFilter(('Blood Shadowed Court',
                                            'BSC')),
             [u"Alan Sovereign", u"Alfred Benezri", u"Anastasz di Zagreb",
              u"Gracis Nostinus", u"Yvette, The Hopeless"]),
            (Filters.MultiExpansionRarityFilter([('Third', 'Uncommon'),
                                                 ('Jyhad', 'Rare')]),
             [u"Aaron's Feeding Razor", u"Abbot", u"Anarch Revolt",
              u"Ghoul Retainer", u"Immortal Grapple",
              u"Pier 13, Port of Baltimore"]),
            (Filters.PrintingFilter('Third Edition (No Draft Text)'),
             [u"Swallowed by the Night", u"Walk of Flame"]),
            (Filters.MultiPrintingFilter(['Third Edition (No Draft Text)',
                                          'Third Edition (Sketch)']),
             [u"Harold Zettler, Pentex Director", "Hektor",
              u"Swallowed by the Night", u"Walk of Flame"]),
            (Filters.MultiPrintingFilter(
                ['Keepers of Tradition (No Draft Text)',
                 'Third Edition (Sketch)']),
             [u"Harold Zettler, Pentex Director", "Hektor",
              u"Immortal Grapple"]),
            (Filters.DisciplineLevelFilter(('cel', 'superior')),
             [u"Abd al-Rashid", u"Akram", u"Alexandra", u"Anson", u"Bronwen",
              u"Cesewayo", u"Enkidu, The Noah", u"Hektor", u"Kabede Maru",
              u"\xc9tienne Fauberge"]),
            (Filters.MultiDisciplineLevelFilter([('obt', 'inferior'),
                                                 ('pot', 'inferior'),
                                                 ('obf', 'superior')]),
             [u"Aaron Bathurst", u"Aaron Duggan, Cameron's Toady", u"Aeron",
              u"Akram", u"Amisa", u"Baron Dieudonne",
              u"Bronwen", u"Cedric", u"Enkidu, The Noah",
              u"Harold Zettler, Pentex Director", u"Kabede Maru",
              u"Kemintiri (Advanced)", u"Pariah",
              u"Rebekka, Chantry Elder of Munich", u'Swallowed by the Night']),
            (Filters.MultiDisciplineLevelFilter(['obt with inferior',
                                                 'pot with inferior',
                                                 'obf with superior']),
             [u"Aaron Bathurst", u"Aaron Duggan, Cameron's Toady", u"Aeron",
              u"Akram", u"Amisa", u"Baron Dieudonne",
              u"Bronwen", u"Cedric", u"Enkidu, The Noah",
              u'Harold Zettler, Pentex Director', u"Kabede Maru",
              u"Kemintiri (Advanced)", u"Pariah",
              u"Rebekka, Chantry Elder of Munich", u'Swallowed by the Night']),
            (Filters.CardTypeFilter('Equipment'),
             [u".44 Magnum", u"AK-47", u"Aaron's Feeding Razor",
              u"An Anarch Manifesto", u"Living Manse",
              u"Pier 13, Port of Baltimore", u"The Ankara Citadel, Turkey"]),
            (Filters.CardTypeFilter('Reflex'), [u"Predator's Communion"]),
            (Filters.MultiCardTypeFilter(['Power', 'Action']),
             [u"Abbot", u"Abjure", u"Ablative Skin", u"Off Kilter"]),
            (Filters.SectFilter('Sabbat'),
             [u"Aaron Bathurst", u"Aaron Duggan, Cameron's Toady", u"Aeron",
              u"Alfred Benezri", u"Angelica, The Canonicus", u"Bronwen",
              u"Enkidu, The Noah", u"Harold Zettler, Pentex Director",
              u"Hektor", u"New Blood", u"Sha-Ennu", u"Sheela Na Gig",
              u"The Siamese"]),
            (Filters.MultiSectFilter(['Sabbat', 'Independent']),
             [u"Aabbt Kindred", u"Aaron Bathurst",
              u"Aaron Duggan, Cameron's Toady", u"Abd al-Rashid",
              u"Abdelsobek", u"Abebe", u"Aeron", u"Alfred Benezri",
              u"Ambrogino Giovanni", u"Amisa", u"Angelica, The Canonicus",
              u"Bronwen", u"Enkidu, The Noah",
              u"Harold Zettler, Pentex Director", u"Hektor",
              u"Kemintiri (Advanced)", u"L\xe1z\xe1r Dobrescu", u"New Blood",
              u"Pariah", u"Sha-Ennu", u"Sheela Na Gig", u"The Siamese",
              u"\xc9tienne Fauberge"]),
            (Filters.TitleFilter('Bishop'), [u"Alfred Benezri"]),
            (Filters.TitleFilter('Independent with 1 vote'),
             [u"Ambrogino Giovanni"]),
            (Filters.MultiTitleFilter(['Bishop', 'Prince']),
             [u"Alfred Benezri", u"Anson", u"Baron Dieudonne"]),
            (Filters.MultiTitleFilter(['Magaji', 'Regent']),
             [u"Cesewayo", u"Kabede Maru", u"Sha-Ennu"]),
            (Filters.MultiTitleFilter(['Primogen', 'Priscus', 'Cardinal']),
             [u"Akram", u"Angelica, The Canonicus", u"Bronwen",
              u"Gracis Nostinus", u"Hektor"]),
            (Filters.CreedFilter('Martyr'),
             [u'Anna "Dictatrix11" Suljic']),
            (Filters.MultiCreedFilter(['Martyr', 'Innocent']),
             [u'Anna "Dictatrix11" Suljic', u'Inez "Nurse216" Villagrande']),
            (Filters.VirtueFilter('Redemption'),
             [u"Abjure", u'Anna "Dictatrix11" Suljic']),
            (Filters.MultiVirtueFilter(['Redemption', 'Judgement']),
             [u"Abjure", u'Anna "Dictatrix11" Suljic',
              u'Earl "Shaka74" Deams']),
            (Filters.GroupFilter(4),
             [u"Aaron Bathurst", u"Abebe", u'Anna "Dictatrix11" Suljic',
              u"Baron Dieudonne", u"Cedric", u"Cesewayo",
              u'Earl "Shaka74" Deams', u"Enkidu, The Noah",
              u"Harold Zettler, Pentex Director",
              u"Hektor", u'Inez "Nurse216" Villagrande', u"Sha-Ennu"]),
            (Filters.MultiGroupFilter([4, 5]),
             [u"Aaron Bathurst", u"Abdelsobek", u"Abebe",
              u'Anna "Dictatrix11" Suljic', u"Baron Dieudonne",
              u"Cedric", u"Cesewayo",
              u'Earl "Shaka74" Deams', u"Enkidu, The Noah",
              u"Harold Zettler, Pentex Director", u"Hektor",
              u'Inez "Nurse216" Villagrande', u"Kabede Maru", u"Sha-Ennu",
              u"Sheela Na Gig"]),
            (Filters.CapacityFilter(2),
             [u"Aaron Duggan, Cameron's Toady", u"New Blood",
              u"Sheela Na Gig"]),
            (Filters.MultiCapacityFilter([2, 1]),
             [u"Aaron Duggan, Cameron's Toady", u"Abombwe", u"Necromancy",
              u"New Blood", u"Sheela Na Gig"]),
            (Filters.CostFilter(5), [u"AK-47"]),
            (Filters.MultiCostFilter([2, 5]),
             [u".44 Magnum", u"AK-47", u"Anarch Railroad", u"Ghoul Retainer",
              u"Paris Opera House", u"Park Hunting Ground",
              u"Pier 13, Port of Baltimore", u"Political Hunting Ground",
              u"Protracted Investment", u"The Ankara Citadel, Turkey"]),
            (Filters.CostFilter(0),
             [u'Aabbt Kindred', u'Aaron Bathurst',
              u"Aaron Duggan, Cameron's Toady", u'Abandoning the Flesh',
              u'Abbot', u'Abd al-Rashid', u'Abdelsobek', u'Abebe', u'Abjure',
              u'Ablative Skin', u'Abombwe', u'Aeron', u"Agent of Power",
              u'Akram', u'Alab\xe1strom', u'Alan Sovereign',
              u'Alan Sovereign (Advanced)', u'Alexandra', u'Alfred Benezri',
              u'Ambrogino Giovanni', u'Amisa', u"An Anarch Manifesto",
              u'Anarch Revolt', u'Anastasz di Zagreb',
              u'Angelica, The Canonicus', u'Anna "Dictatrix11" Suljic',
              u'Anson', u'Ashur Tablets', u"Aye",
              u"Baron Dieudonne", u'Bravo', u'Bronwen',
              u'Cedric', u'Cesewayo', u'Dramatic Upheaval',
              u'Earl "Shaka74" Deams', u"Enkidu, The Noah",
              u"Fidus, The Shrunken Beast", u'Gracis Nostinus',
              u"Harold Zettler, Pentex Director", u"Hektor",
              u'Hide the Heart', u"Immortal Grapple",
              u'Inez "Nurse216" Villagrande', u'Kabede Maru',
              u"Kemintiri (Advanced)", u'L\xe1z\xe1r Dobrescu',
              u'Motivated by Gehenna', u"Necromancy", u"New Blood",
              u"Off Kilter", u"Pariah", u"Predator's Communion",
              u"Rebekka, Chantry Elder of Munich", u"Sha-Ennu",
              u"Sheela Na Gig", u'Swallowed by the Night', u"The Siamese",
              u"Two Wrongs", u"Walk of Flame", u"Yvette, The Hopeless",
              u"\xc9tienne Fauberge"]),
            (Filters.MultiCostFilter([0, 5]),
             [u"AK-47", u'Aabbt Kindred', u'Aaron Bathurst',
              u"Aaron Duggan, Cameron's Toady", u'Abandoning the Flesh',
              u'Abbot', u'Abd al-Rashid', u'Abdelsobek', u'Abebe', u'Abjure',
              u'Ablative Skin', u'Abombwe', u'Aeron', u"Agent of Power",
              u'Akram', u'Alab\xe1strom', u'Alan Sovereign',
              u'Alan Sovereign (Advanced)', u'Alexandra', u'Alfred Benezri',
              u'Ambrogino Giovanni', u'Amisa', u"An Anarch Manifesto",
              u'Anarch Revolt', u'Anastasz di Zagreb',
              u'Angelica, The Canonicus', u'Anna "Dictatrix11" Suljic',
              u'Anson', u'Ashur Tablets', u"Aye",
              u"Baron Dieudonne", u'Bravo', u'Bronwen',
              u'Cedric', u'Cesewayo', u'Dramatic Upheaval',
              u'Earl "Shaka74" Deams', u"Enkidu, The Noah",
              u"Fidus, The Shrunken Beast", u'Gracis Nostinus',
              u"Harold Zettler, Pentex Director", u"Hektor",
              u'Hide the Heart', u"Immortal Grapple",
              u'Inez "Nurse216" Villagrande', u'Kabede Maru',
              u'Kemintiri (Advanced)', u'L\xe1z\xe1r Dobrescu',
              u'Motivated by Gehenna', u"Necromancy", u"New Blood",
              u"Off Kilter", u"Pariah", u"Predator's Communion",
              u"Rebekka, Chantry Elder of Munich", u'Sha-Ennu',
              u"Sheela Na Gig", u'Swallowed by the Night', u"The Siamese",
              u"Two Wrongs", u"Walk of Flame", u'Yvette, The Hopeless',
              u"\xc9tienne Fauberge"]),
            (Filters.LifeFilter(6),
             [u'Anna "Dictatrix11" Suljic', u'Earl "Shaka74" Deams']),
            (Filters.MultiLifeFilter([3, 6]),
             [u'Anna "Dictatrix11" Suljic', u'Earl "Shaka74" Deams',
              u"High Top", u'Inez "Nurse216" Villagrande',
              u'Scapelli, The Family "Mechanic"']),
            (Filters.CostTypeFilter('Pool'),
             [u".44 Magnum", u"AK-47", u"Aaron's Feeding Razor",
              u"Anarch Railroad", u"Ghoul Retainer", u"Gypsies", u"High Top",
              u"Ossian", u"Paris Opera House", u"Park Hunting Ground",
              u"Political Hunting Ground", u"Protracted Investment",
              u"Rock Cat", u'Scapelli, The Family "Mechanic"',
              u"The Path of Blood", u"The Slaughterhouse", u"Vox Domini"]),
            (Filters.CostTypeFilter('Blood'),
             [u"Aire of Elation", u"Living Manse",
              u"Pier 13, Port of Baltimore", u"Raven Spy", u"Shade",
              u"The Ankara Citadel, Turkey"]),
            (Filters.MultiCostTypeFilter(['Pool', 'Blood']),
             [u".44 Magnum", u"AK-47", u"Aaron's Feeding Razor",
              u"Aire of Elation", u"Anarch Railroad", u"Ghoul Retainer",
              u"Gypsies", u"High Top", u"Living Manse", u"Ossian",
              u"Paris Opera House", u"Park Hunting Ground",
              u"Pier 13, Port of Baltimore", u"Political Hunting Ground",
              u"Protracted Investment", u"Raven Spy", u"Rock Cat",
              u'Scapelli, The Family "Mechanic"', u"Shade",
              u"The Ankara Citadel, Turkey", u"The Path of Blood",
              u"The Slaughterhouse", u"Vox Domini"]),
            (Filters.LifeFilter(4), [u"Ossian", u"Rock Cat"]),
            (Filters.MultiLifeFilter([4, 5]), [u"Ossian", u"Rock Cat"]),
            (Filters.ArtistFilter('Leif Jones'),
             [u"Alan Sovereign (Advanced)", u"Off Kilter",
              u"Two Wrongs", u"Yvette, The Hopeless"]),
            (Filters.MultiArtistFilter(["William O'Connor",
                                        u"N\xe9 N\xe9 Thomas"]),
             [u".44 Magnum", u"Paris Opera House", u"The Slaughterhouse"]),
            (Filters.KeywordFilter('burn option'),
             [u"Paris Opera House", u"The Slaughterhouse"]),
            (Filters.KeywordFilter('0 strength'),
             [u"Fidus, The Shrunken Beast",
              u'Scapelli, The Family "Mechanic"']),
            (Filters.KeywordFilter('2 strength'), [u"Ossian", u"Pariah"]),
            (Filters.KeywordFilter('3 strength'),
             [u"Enkidu, The Noah", u"Rock Cat"]),
            (Filters.KeywordFilter('3 bleed'), [u"Alexandra", u"Sha-Ennu"]),
            (Filters.KeywordFilter('2 bleed'),
             [u"Ambrogino Giovanni", u"The Siamese"]),
            (Filters.KeywordFilter('gargoyle creature'), [u"Rock Cat"]),
            (Filters.KeywordFilter('animal'), [u"Raven Spy"]),
            (Filters.KeywordFilter('unique'),
             [u"Aaron's Feeding Razor", u"Agent of Power", u"Anarch Railroad",
              u"Gypsies", u"High Top", u"Ossian", u"Paris Opera House",
              u"Park Hunting Ground", u"Pier 13, Port of Baltimore",
              u"Political Hunting Ground", u'Scapelli, The Family "Mechanic"',
              u"The Ankara Citadel, Turkey", u"The Path of Blood"]),
            (Filters.KeywordFilter('hunting ground'),
             [u"Park Hunting Ground", u"Political Hunting Ground"]),
            (Filters.KeywordFilter('location'),
             [u"Anarch Railroad", u"Living Manse", u"Paris Opera House",
              u"Park Hunting Ground", u"Pier 13, Port of Baltimore",
              u"Political Hunting Ground", u"The Ankara Citadel, Turkey",
              u"The Slaughterhouse"]),
            (Filters.KeywordFilter('trifle'),
             [u"Abombwe", u"Agent of Power", u"Aye", u"Two Wrongs"]),
            (Filters.KeywordFilter('out-of-turn'),
             [u"Two Wrongs", u"Vox Domini"]),
            (Filters.MultiKeywordFilter(['burn option']),
             [u"Paris Opera House", u"The Slaughterhouse"]),

            # Other Filters
            (Filters.CardTextFilter('strike'),
             [u".44 Magnum", u"AK-47", u"Aeron", u"Anastasz di Zagreb",
              u"Bronwen", u"Ghoul Retainer", u"Hektor", u"High Top",
              u"Immortal Grapple", u"Ossian", u"Rock Cat",
              u'Scapelli, The Family "Mechanic"', u"Shade",
              u'Smite', u"Walk of Flame"]),
            (Filters.CardTextFilter('{strength'), [u"Gypsies"]),
            (Filters.CardNameFilter(u'L\xe1z\xe1r'),
             [u"L\xe1z\xe1r Dobrescu"]),
            (Filters.NullFilter(), self.aExpectedCards),
            (Filters.SpecificCardFilter(IAbstractCard("Abebe")),
             [u"Abebe"]),

            # Compound Filters
            (Filters.FilterAndBox([Filters.CardTypeFilter('Equipment'),
                                   Filters.CostFilter(5)]),
             [u"AK-47"]),
            (Filters.FilterOrBox([Filters.CardTypeFilter('Equipment'),
                                  Filters.CardTypeFilter('Power')]),
             [u".44 Magnum", u"AK-47", u"Aaron's Feeding Razor",
              u"Abjure", u"An Anarch Manifesto",
              u"Living Manse", u"Pier 13, Port of Baltimore",
              u"The Ankara Citadel, Turkey"]),
            (Filters.FilterNot(Filters.MultiCardTypeFilter(['Equipment',
                                                            'Vampire'])),
             [u"Abandoning the Flesh", u"Abbot", u"Abjure", u"Ablative Skin",
              u"Abombwe", u"Agent of Power", u"Aire of Elation",
              u"Anarch Railroad", "Anarch Revolt",
              u'Anna "Dictatrix11" Suljic', u'Ashur Tablets',
              u"Aye", u"Bravo", u'Dramatic Upheaval',
              u'Earl "Shaka74" Deams', u"Ghoul Retainer", u"Gypsies",
              u"Hide the Heart", u"High Top", u"Immortal Grapple",
              u'Inez "Nurse216" Villagrande',
              u'Motivated by Gehenna', u"Necromancy", u"Off Kilter",
              u"Ossian", u"Paris Opera House", u"Park Hunting Ground",
              u"Political Hunting Ground", u"Predator's Communion",
              u"Protracted Investment", u"Raven Spy", u"Rock Cat",
              u'Scapelli, The Family "Mechanic"', u"Shade", u'Smite',
              u'Swallowed by the Night', u"The Path of Blood",
              u"The Slaughterhouse", u"Two Wrongs",
              u"Vox Domini", u"Walk of Flame"]),
        ]

        aPhysicalTests = [self._physical_test(tTest) for tTest in aTests]

        # Abstract Card Filtering Tests
        for oFilter, aExpectedNames in aTests:
            aCards = oFilter.select(AbstractCard).distinct()
            aNames = sorted([oC.name for oC in aCards])
            self.assertEqual(aNames, aExpectedNames,
                             "Filter Object %s failed. %s != %s." % (
                                 oFilter, aNames, aExpectedNames))

        # Filter values Tests
        self.assertEqual(Filters.MultiClanFilter.get_values(),
                         [u"Abomination", u"Ahrimane", u"Assamite",
                          u"Blood Brother", u"Brujah",
                          u"Brujah antitribu", u"Daughter of Cacophony",
                          u"Follower of Set", u"Gangrel",
                          u"Gangrel antitribu", u"Gargoyle", u"Giovanni",
                          u"Harbinger of Skulls", u"Lasombra",
                          u"Malkavian antitribu", u"Nosferatu",
                          u"Nosferatu antitribu", u"Osebo",
                          u"Pander", u"Ravnos", u"Samedi",
                          u"Toreador", u"Tremere", u"Tzimisce", u"Ventrue"])
        self.assertEqual(Filters.MultiCapacityFilter.get_values(),
                         [str(x) for x in range(1, 12)])
        self.assertEqual(Filters.MultiDisciplineFilter.get_values(),
                         [u"Abombwe", u"Animalism", u"Auspex", u"Celerity",
                          u"Chimerstry", u"Dementation", u"Dominate",
                          u"Flight", u"Fortitude", u"Necromancy",
                          u"Obfuscate", u"Obtenebration", u"Potence",
                          u"Presence", u"Protean", u"Quietus", u"Sanguinus",
                          u"Serpentis", u"Spiritus", u"Thaumaturgy",
                          u"Thanatosis", u"Valeren", u"Vicissitude",
                          u"Visceratika"])
        self.assertEqual(Filters.MultiCardTypeFilter.get_values(),
                         [u"Action", u"Action Modifier", u"Ally", u"Combat",
                          u"Equipment", u"Imbued", u"Master",
                          u"Political Action", u"Power", u"Reaction",
                          u"Reflex", u"Retainer", u"Vampire"])
        self.assertEqual(Filters.MultiTitleFilter.get_values(),
                         [u"Archbishop", u"Bishop", u"Cardinal",
                          u"Independent with 1 vote",
                          u"Independent with 2 votes",
                          u"Inner Circle", u"Justicar", u"Magaji",
                          u"Primogen", u"Prince", u"Priscus", u"Regent"])
        self.assertEqual(Filters.MultiCreedFilter.get_values(),
                         [u"Innocent", u"Martyr", u"Visionary"])
        self.assertEqual(Filters.MultiVirtueFilter.get_values(),
                         [u"Innocence", u"Judgment", u"Martyrdom",
                          u"Redemption", u"Vengeance", u"Vision"])
        self.assertEqual(Filters.MultiPrintingFilter.get_values(),
                         ['Heirs to the Blood (No Draft Text)',
                          'Jyhad (Variant Printing)',
                          'Keepers of Tradition (No Draft Text)',
                          'Sabbat Wars (Second Printing)',
                          'Third Edition (No Draft Text)',
                          'Third Edition (Sketch)'])
        # Test the physical card filtering
        for oFilter, aExpectedCards in aPhysicalTests:
            aCards = sorted(oFilter.select(PhysicalCard).distinct(),
                            key=lambda x: x.id)
            self.assertEqual(aCards, aExpectedCards,
                             "Filter Object %s failed. %s != %s." % (
                                 oFilter, aCards, aExpectedCards))

        # test filtering on expansion
        aExpansionTests = [
            (Filters.PhysicalExpansionFilter('Jyhad'),
             ['.44 Magnum', "Aaron's Feeding Razor", u"Anarch Revolt",
              u"Anson", u'Dramatic Upheaval', u"Ghoul Retainer",
              u"Gypsies", u"Immortal Grapple",
              u"Protracted Investment", u"Raven Spy", u"Walk of Flame"],
             ['Jyhad']
            ),
            # Check we are getting all the printings we expect
            (Filters.PhysicalExpansionFilter('Jyhad'),
             ['.44 Magnum', "Aaron's Feeding Razor", u"Anarch Revolt",
              u"Anson", u'Dramatic Upheaval', u"Ghoul Retainer",
              u"Gypsies", u"Immortal Grapple",
              u"Protracted Investment", u"Raven Spy", u"Walk of Flame"],
             ['Jyhad', 'Jyhad'], [None, 'Variant Printing'],
            ),

            (Filters.PhysicalExpansionFilter('LoB'),
             ['Abombwe', 'Aye', '.44 Magnum', 'Abebe', u"Cedric", u"Cesewayo",
              u"Predator's Communion", u"The Slaughterhouse",
              u"Vox Domini", u"Paris Opera House", u"High Top",
              u"Rock Cat"],
             ['LoB']
            ),
            (Filters.PhysicalExpansionFilter(None),
             self.aExpectedCards,
             [None]
            ),
            (Filters.MultiPhysicalExpansionFilter(['LoB', 'LotN']),
             ['Abombwe', '.44 Magnum', 'Abebe', 'AK-47', 'Abdelsobek',
              'Aye', u"Cedric", u"Cesewayo", u"Kabede Maru",
              u"Predator's Communion", u"The Path of Blood",
              u"The Slaughterhouse", u"Raven Spy",
              u"Park Hunting Ground", u"Necromancy",
              u"Agent of Power", u"Immortal Grapple", u"Paris Opera House",
              u"Vox Domini", u"Rock Cat", u"High Top"],
             ['LoB', 'LotN']
            ),
            (Filters.MultiPhysicalExpansionFilter(['  Unspecified Expansion',
                                                   'VTES']),
             self.aExpectedCards,
             [None, 'VTES']
            ),
            (Filters.PhysicalPrintingFilter('Jyhad'),
             ['.44 Magnum', "Aaron's Feeding Razor", u"Anarch Revolt",
              u"Anson", u'Dramatic Upheaval', u"Ghoul Retainer",
              u"Gypsies", u"Immortal Grapple",
              u"Protracted Investment", u"Raven Spy", u"Walk of Flame"],
             ['Jyhad'], [None],
            ),
            (Filters.PhysicalPrintingFilter('Jyhad (Variant Printing)'),
             [u"Ghoul Retainer", u"Immortal Grapple", u"Walk of Flame"],
             ['Jyhad'], ['Variant Printing'],
            ),
            (Filters.PhysicalPrintingFilter(
                'Keepers of Tradition (No Draft Text)'),
             [u"Immortal Grapple"],
             ["Keepers of Tradition"], ["No Draft Text"],
            ),
            (Filters.MultiPhysicalPrintingFilter([
                'Legacy of Blood',
                'Lords of the Night']),
             ['Abombwe', '.44 Magnum', 'Abebe', 'AK-47', 'Abdelsobek',
              'Aye', u"Cedric", u"Cesewayo", u"Kabede Maru",
              u"Predator's Communion", u"The Path of Blood",
              u"The Slaughterhouse", u"Raven Spy",
              u"Park Hunting Ground", u"Necromancy",
              u"Agent of Power", u"Immortal Grapple", u"Paris Opera House",
              u"Vox Domini", u"Rock Cat", u"High Top"],
             ['LoB', 'LotN'], [None, None]
            ),
            (Filters.MultiPhysicalPrintingFilter([
                'Jyhad (Variant Printing)',
                'Keepers of Tradition (No Draft Text)']),
             [u"Ghoul Retainer", u"Immortal Grapple", u"Walk of Flame"],
             ['Jyhad', 'KoT'], ['Variant Printing', 'No Draft Text'],
            ),
        ]

        for tTest in aExpansionTests:
            oFilter, aExpectedCards = self._physical_test(tTest)
            aCards = sorted(oFilter.select(PhysicalCard).distinct(),
                            key=lambda x: x.id)
            self.assertEqual(aCards, aExpectedCards,
                             "Filter Object %s failed. %s != %s." % (
                                 oFilter,
                                 [(IAbstractCard(x).name, x.printing)
                                  for x in aCards],
                                 [(IAbstractCard(x).name, x.printing)
                                  for x in aExpectedCards]))

        # Test we get the right values from the physical expansion and
        # printing filters
        self.assertEqual(Filters.MultiPhysicalExpansionFilter.get_values(),
                         ["  Unspecified Expansion", "Anarchs",
                          "Anarchs and Alastors Storyline", "Ancient Hearts",
                          'Anthology', 'Anthology I Reprint Set',
                          'Black Chantry', 'Black Hand',
                          'Blood Shadowed Court', 'Bloodlines',
                          'Camarilla Edition', 'Dark Sovereigns',
                          'Ebony Kingdom', "Eden's Legacy Storyline",
                          'Final Nights', 'Gehenna', 'Heirs to the Blood',
                          'Jyhad', 'Keepers of Tradition',
                          'Kindred Most Wanted', 'Legacy of Blood',
                          'Lords of the Night', 'Lost Kindred',
                          'Nights of Reckoning', 'Sabbat',
                          'Sabbat Wars', 'Tenth Anniversary',
                          'Third Edition', 'Twilight Rebellion', 'VTES']
                        )

        self.assertEqual(Filters.MultiPhysicalPrintingFilter.get_values(),
                         ["  Unspecified Expansion",
                          "Anarchs",
                          "Anarchs and Alastors Storyline",
                          "Ancient Hearts",
                          'Anthology',
                          'Anthology I Reprint Set',
                          'Black Chantry',
                          'Black Hand',
                          'Blood Shadowed Court',
                          'Bloodlines',
                          'Camarilla Edition',
                          'Dark Sovereigns',
                          'Ebony Kingdom',
                          "Eden's Legacy Storyline",
                          'Final Nights',
                          'Gehenna',
                          'Heirs to the Blood',
                          'Heirs to the Blood (No Draft Text)',
                          'Jyhad',
                          'Jyhad (Variant Printing)',
                          'Keepers of Tradition',
                          'Keepers of Tradition (No Draft Text)',
                          'Kindred Most Wanted',
                          'Legacy of Blood',
                          'Lords of the Night',
                          'Lost Kindred',
                          'Nights of Reckoning',
                          'Sabbat',
                          'Sabbat Wars',
                          'Sabbat Wars (Second Printing)',
                          'Tenth Anniversary',
                          'Third Edition',
                          'Third Edition (No Draft Text)',
                          'Third Edition (Sketch)',
                          'Twilight Rebellion',
                          'VTES']
                        )

    def test_multi_filters(self):
        """Test that MultiFilters and the equivilent single filters work as
           expected"""
        # Tests are MultiFilter, EquivFilter pairs - we want to assert that
        # the behaviours match
        aTests = [
            (Filters.MultiClanFilter(['Follower of Set']),
             Filters.ClanFilter('Follower of Set')),
            (Filters.MultiClanFilter(['Follower of Set', 'Ravnos']),
             Filters.FilterOrBox(
                 [Filters.ClanFilter('Follower of Set'),
                  Filters.ClanFilter('Ravnos')])),
            (Filters.MultiDisciplineFilter(['nec']),
             Filters.DisciplineFilter('nec')),
            (Filters.MultiDisciplineFilter(['nec', 'obf']),
             Filters.FilterOrBox(
                 [Filters.DisciplineFilter('nec'),
                  Filters.DisciplineFilter('obf')])),
            (Filters.MultiExpansionRarityFilter([('Third', 'Uncommon')]),
             Filters.ExpansionRarityFilter(('Third', 'Uncommon'))),
            (Filters.MultiDisciplineLevelFilter([('obf', 'inferior')]),
             Filters.DisciplineLevelFilter(('obf', 'inferior'))),
            (Filters.MultiCardTypeFilter(['Action']),
             Filters.CardTypeFilter('Action')),
            (Filters.MultiSectFilter(['Sabbat']),
             Filters.SectFilter('Sabbat')),
            (Filters.MultiTitleFilter(['Bishop']),
             Filters.TitleFilter('Bishop')),
            (Filters.MultiVirtueFilter(['Redemption']),
             Filters.VirtueFilter('Redemption')),
            (Filters.MultiCreedFilter(['Innocent']),
             Filters.CreedFilter('Innocent')),
            (Filters.MultiGroupFilter([4]), Filters.GroupFilter(4)),
            (Filters.MultiCapacityFilter([2]), Filters.CapacityFilter(2)),
            (Filters.MultiCapacityFilter([2, 3]),
             Filters.FilterOrBox(
                 [Filters.CapacityFilter(2),
                  Filters.CapacityFilter(3)])),
            (Filters.MultiCapacityFilter([2, 3]),
             Filters.FilterOrBox(
                 [Filters.MultiCapacityFilter([2]),
                  Filters.MultiCapacityFilter([3])])),
            (Filters.MultiCostFilter([0]), Filters.CostFilter(0)),
            (Filters.MultiCostFilter([2]), Filters.CostFilter(2)),
            (Filters.MultiLifeFilter([1]), Filters.LifeFilter(1)),
            (Filters.MultiCostTypeFilter(['pool']),
             Filters.CostTypeFilter('pool')),
            (Filters.MultiArtistFilter(["William O'Connor"]),
             Filters.ArtistFilter("William O'Connor")),
        ]

        for oFilter, oEquivFilter in aTests:
            aCards = sorted(oFilter.select(AbstractCard).distinct(),
                            key=lambda x: x.id)
            aExpectedCards = sorted(
                oEquivFilter.select(AbstractCard).distinct(),
                key=lambda x: x.id)
            self.assertEqual(aCards, aExpectedCards,
                             "Filter Object %s failed. %s != %s." % (
                                 oFilter, aCards, aExpectedCards))

        aExpansionTests = [
            (Filters.MultiPhysicalExpansionFilter(['Jyhad']),
             Filters.PhysicalExpansionFilter('Jyhad')),
            (Filters.MultiPhysicalExpansionFilter(['LoB', 'LotN']),
             Filters.FilterOrBox(
                 [Filters.PhysicalExpansionFilter('LoB'),
                  Filters.PhysicalExpansionFilter('LotN')])),
        ]

        for oFilter, oEquivFilter in aExpansionTests:
            aCards = sorted(oFilter.select(PhysicalCard).distinct(),
                            key=lambda x: x.id)
            aExpectedCards = sorted(
                oEquivFilter.select(PhysicalCard).distinct(),
                key=lambda x: x.id)
            self.assertEqual(aCards, aExpectedCards,
                             "Filter Object %s failed. %s != %s." % (
                                 oFilter, aCards, aExpectedCards))

    def test_card_set_filters(self):
        """Tests for the physical card set filters."""
        # Tests on the physical card set properties
        # Although splitting this off does add an additional init
        # pass, the logical grouping is fairly different
        aPCSs = make_physical_card_sets()
        aPhysicalCardSetTests = [
            (Filters.CardSetNameFilter('Test 1'), [aPCSs[0]]),
            (Filters.CardSetNameFilter('Test'), sorted(aPCSs,
                                                       key=lambda x: x.id)),
            (Filters.CSPhysicalCardSetInUseFilter(),
             [aPCSs[2]]),
            (Filters.CardSetAuthorFilter('Author A'),
             sorted([aPCSs[0], aPCSs[2]], key=lambda x: x.id)),
            (Filters.CardSetDescriptionFilter('set'),
             sorted([aPCSs[0], aPCSs[1]], key=lambda x: x.id)),
            (Filters.CardSetDescriptionFilter('different'),
             [aPCSs[2]]),
        ]

        for oFilter, aExpectedSets in aPhysicalCardSetTests:
            aCardSets = sorted(oFilter.select(PhysicalCardSet).distinct(),
                               key=lambda x: x.id)
            self.assertEqual(aCardSets, aExpectedSets,
                             "Filter Object %s failed. %s != %s." % (
                                 oFilter, aCardSets, aExpectedSets))

        # Test data for the Specific card filters
        oAbsAK = IAbstractCard('ak-47')
        oExp = IExpansion('LotN')
        oPhysAK = IPhysicalCard((oAbsAK, oExp))

        aPCSAbsCardTests = [
            (Filters.PhysicalCardSetFilter('Test 1'),
             Filters.CardTypeFilter('Vampire'),
             [u"Alexandra", u"Sha-Ennu", u"Sha-Ennu", u"Sha-Ennu",
              u"Sha-Ennu"]),
            (Filters.PhysicalCardSetFilter('Test 1'),
             Filters.CardTypeFilter('Master'),
             [u"Abombwe"]),
            (Filters.PhysicalCardSetFilter('Test 2'),
             Filters.CardTypeFilter('Equipment'),
             [u".44 Magnum", u"AK-47"]),
            (Filters.PhysicalCardSetFilter('Test 2'),
             Filters.SpecificCardFilter('AK-47'),
             [u"AK-47"]),
            (Filters.PhysicalCardSetFilter('Test 2'),
             Filters.SpecificCardIdFilter(oAbsAK.id),
             [u"AK-47"]),
            (Filters.PhysicalCardSetFilter('Test 2'),
             Filters.SpecificPhysCardIdFilter(oPhysAK.id),
             [u"AK-47"]),
            (Filters.PhysicalCardSetFilter('Test 3'),
             Filters.SpecificPhysCardIdFilter(oPhysAK.id),
             []),
        ]

        for oPCSFilter, oFilter, aExpectedCards in aPCSAbsCardTests:
            oFullFilter = Filters.FilterAndBox([oPCSFilter, oFilter])
            self.assertTrue('PhysicalCard' in oFullFilter.types)
            aCSCards = [IAbstractCard(x).name for x in
                        oFullFilter.select(
                            MapPhysicalCardToPhysicalCardSet).distinct()]
            aCSCards.sort()
            aExpectedCards.sort()
            self.assertEqual(aCSCards, aExpectedCards,
                             "Filter Object %s failed. %s != %s." % (
                                 oFullFilter, aCSCards, aExpectedCards))

        aPCSPhysCardTests = [
            (Filters.PhysicalCardSetFilter('Test 1'),
             Filters.CardTypeFilter('Vampire'),
             [('Alexandra', 'CE'), ('Sha-Ennu', None),
              ('Sha-Ennu', None), ('Sha-Ennu', None),
              ('Sha-Ennu', 'Third Edition')]),
            (Filters.PhysicalCardSetFilter('Test 2'),
             Filters.SpecificCardFilter('AK-47'),
             [('AK-47', 'LotN')]),
            (Filters.PhysicalCardSetFilter('Test 3'),
             Filters.SpecificPhysCardIdFilter(oPhysAK.id),
             []),
        ]

        for oPCSFilter, oFilter, aExpectedCards in aPCSPhysCardTests:
            oFullFilter = Filters.FilterAndBox([oPCSFilter, oFilter])
            self.assertTrue('PhysicalCard' in oFullFilter.types)
            aCSCards = sorted(
                [IPhysicalCard(x) for x in
                 oFullFilter.select(
                     MapPhysicalCardToPhysicalCardSet).distinct()],
                key=lambda x: x.id)
            aExpectedPhysCards = self._convert_to_phys_cards(aExpectedCards)
            aExpectedPhysCards.sort(key=lambda x: x.id)
            self.assertEqual(aCSCards, aExpectedPhysCards,
                             "Filter Object %s failed. %s != %s." % (
                                 oFullFilter, aCSCards, aExpectedPhysCards))

        aPCSCardsInUse = list(Filters.PhysicalCardSetInUseFilter([
            'Test 1']).select(PhysicalCard).distinct())
        aExpectedCards = list(aPCSs[2].cards)
        self.assertEqual(aPCSCardsInUse, aExpectedCards,
                         'PhysicalCardSet In Use Filter failed %s != %s' % (
                             aPCSCardsInUse, aExpectedCards))

        # Number tests
        aPCSNumberTests = [
            (Filters.PhysicalCardSetFilter('Test 1'),
             Filters.CardSetMultiCardCountFilter(('4', aPCSs[0].name)),
             [u"Sha-Ennu", u"Sha-Ennu", u"Sha-Ennu", u"Sha-Ennu"]),
            (Filters.PhysicalCardSetFilter('Test 1'),
             Filters.CardSetMultiCardCountFilter((['4'], [aPCSs[0].name])),
             [u"Sha-Ennu", u"Sha-Ennu", u"Sha-Ennu", u"Sha-Ennu"]),
            (Filters.PhysicalCardSetFilter('Test 1'),
             Filters.CardSetMultiCardCountFilter(('7', aPCSs[0].name)),
             []),
            (Filters.PhysicalCardSetFilter('Test 1'),
             Filters.CardSetMultiCardCountFilter(('1', aPCSs[0].name)),
             [u"Abombwe", u"Alexandra"]),
            (Filters.PhysicalCardSetFilter('Test 1'),
             Filters.CardSetMultiCardCountFilter((['1', '4'], aPCSs[0].name)),
             [u"Abombwe", u"Alexandra", u"Sha-Ennu", u"Sha-Ennu",
              u"Sha-Ennu", u"Sha-Ennu"]),
            (Filters.PhysicalCardSetFilter('Test 1'),
             Filters.CardSetMultiCardCountFilter((['4'],
                                                  [aPCSs[0].name,
                                                   aPCSs[1].name])),
             [u"Sha-Ennu", u"Sha-Ennu", u"Sha-Ennu", u"Sha-Ennu"]),
            (Filters.PhysicalCardSetFilter('Test 1'),
             Filters.CardSetMultiCardCountFilter((['1', '4'],
                                                  [aPCSs[0].name,
                                                   aPCSs[1].name])),
             [u'Abombwe', u'Alexandra', u"Sha-Ennu", u"Sha-Ennu",
              u"Sha-Ennu", u"Sha-Ennu"]),
            # Cards in 'Test 2' with zero count in 'Test 1'
            (Filters.PhysicalCardSetFilter('Test 2'),
             Filters.CardSetMultiCardCountFilter(('0', aPCSs[0].name)),
             [u"Anson", u".44 Magnum", u"AK-47"]),
            # Nothing with >30
            (Filters.PhysicalCardSetFilter('Test 2'),
             Filters.CardSetMultiCardCountFilter((['>30'], aPCSs[0].name)),
             []),
            # Check for syntax of combinations
            (Filters.PhysicalCardSetFilter('Test 2'),
             Filters.CardSetMultiCardCountFilter((['0', '>30'],
                                                  aPCSs[0].name)),
             [u"Anson", u".44 Magnum", u"AK-47"]),
            (Filters.PhysicalCardSetFilter('Test 2'),
             Filters.CardSetMultiCardCountFilter((['0', '30', '>30'],
                                                  aPCSs[0].name)),
             [u"Anson", u".44 Magnum", u"AK-47"]),
        ]

        for oPCSFilter, oFilter, aExpectedCards in aPCSNumberTests:
            oFullFilter = Filters.FilterAndBox([oPCSFilter, oFilter])
            aCSCards = [IAbstractCard(x).name for x in
                        oFullFilter.select(
                            MapPhysicalCardToPhysicalCardSet).distinct()]
            aCSCards.sort()
            aExpectedCards.sort()
            self.assertEqual(aCSCards, aExpectedCards,
                             "Filter Object %s failed. %s != %s." % (
                                 oFullFilter, aCSCards, aExpectedCards))

    def test_best_guess_filter(self):
        """Test the best guess filter"""
        # This seems the best fit, to include it with the other filter tests
        aTests = [
            ('Sha-Ennu', [u'Sha-Ennu']),
            ('She-Ennu', [u'Sha-Ennu']),
            ('Saa-Ennu', [u'Sha-Ennu']),
            ('47', [u'AK-47']),
            ('4', [u'.44 Magnum', u'AK-47', u'Earl "Shaka74" Deams']),
            ('Alex', [u'Alexandra']),
            ('Raven', [u'Raven Spy']),
            ('Path of Blood, The', [u'The Path of Blood']),
        ]
        for sGuess, aExpectedNames in aTests:
            oFilter = BaseFilters.best_guess_filter(sGuess)
            aNames = sorted([x.name for x in oFilter.select(AbstractCard)])
            self.assertEqual(aNames, aExpectedNames,
                             '%s != expected %s for guess %s' % (
                                 aNames, aExpectedNames, sGuess))


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
