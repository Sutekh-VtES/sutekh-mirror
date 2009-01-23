# DatabaseUpgrade.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006, 2007, 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""Handles the heavy lifting of upgrading the database.

   Holds methods to copy database contents around, utility classes
   to talk to old database versions, and so forth.
   """

# pylint: disable-msg=E0611
# sqlobject confuses pylint here
from sqlobject import sqlhub, SQLObject, IntCol, UnicodeCol, RelatedJoin, \
        EnumCol, MultipleJoin, connectionForURI, ForeignKey, BoolCol, \
        SQLObjectNotFound
# pylint: enable-msg=E0611
from logging import Logger
from sutekh.core.SutekhObjects import PhysicalCard, AbstractCard, \
        PhysicalCardSet, Expansion, Clan, Virtue, Discipline, Rarity, \
        RarityPair, CardType, Ruling, aObjectList, DisciplinePair, Creed, \
        Sect, Title, flush_cache
from sutekh.core.CardSetHolder import CachedCardSetHolder
from sutekh.SutekhUtility import refresh_tables
from sutekh.core.DatabaseVersion import DatabaseVersion
from sutekh.core.Abbreviations import Rarities

# This file handles all the grunt work of the database upgrades. We have some
# (arguablely overly) complex trickery to read old databases, and we create a
# copy in sqlite memory database first, before commiting to the actual DB

# Utility Exception
class UnknownVersion(Exception):
    """Exception for versions we cannot handle"""
    def __init__(self, sTableName):
        Exception.__init__(self)
        self.sTableName = sTableName

    def __str__(self):
        return "Unrecognised version for %s" % self.sTableName

# We Need to clone the SQLObject classes in SutekhObjects so we can read
# old versions
# pylint: disable-msg=C0103, W0232
# C0103 - names set largely by SQLObject conventions, so ours don't apply
# W0232 - SQLObject classes don't have user defined __init__
class PhysicalCardSet_v3(SQLObject):
    """PhysicalCardSet V3 - doesn't have the inuse flag."""
    class sqlmeta:
        """meta class used to set the correct table."""
        table = PhysicalCardSet.sqlmeta.table
    name = UnicodeCol(alternateID=True, length=50)
    author = UnicodeCol(length=50, default='')
    comment = UnicodeCol(default='')
    annotations = UnicodeCol(default='')
    cards = RelatedJoin('PhysicalCard', intermediateTable='physical_map',
            createRelatedTable=False)

class AbstractCard_v2(SQLObject):
    """AbstractCard V2 - doesn't have the burnoption"""
    class sqlmeta:
        """meta class used to set the correct table."""
        table = AbstractCard.sqlmeta.table
    canonicalName = UnicodeCol(alternateID=True, length=50)
    name = UnicodeCol(length=50)
    text = UnicodeCol()
    group = IntCol(default=None, dbName='grp')
    capacity = IntCol(default=None)
    cost = IntCol(default=None)
    life = IntCol(default=None)
    costtype = EnumCol(enumValues=['pool', 'blood', 'conviction', None],
            default=None)
    level = EnumCol(enumValues=['advanced', None], default=None)
    discipline = RelatedJoin('DisciplinePair',
            intermediateTable='abs_discipline_pair_map',
            createRelatedTable=False)
    rarity = RelatedJoin('RarityPair', intermediateTable='abs_rarity_pair_map',
            createRelatedTable=False)
    clan = RelatedJoin('Clan', intermediateTable='abs_clan_map',
            createRelatedTable=False)
    cardtype = RelatedJoin('CardType', intermediateTable='abs_type_map',
            createRelatedTable=False)
    sect = RelatedJoin('Sect', intermediateTable='abs_sect_map',
            createRelatedTable=False)
    title = RelatedJoin('Title', intermediateTable='abs_title_map',
            createRelatedTable=False)
    creed = RelatedJoin('Creed', intermediateTable='abs_creed_map',
            createRelatedTable=False)
    virtue = RelatedJoin('Virtue', intermediateTable='abs_virtue_map',
            createRelatedTable=False)
    rulings = RelatedJoin('Ruling', intermediateTable='abs_ruling_map',
            createRelatedTable=False)
    sets = RelatedJoin('AbstractCardSet_v3', intermediateTable='abstract_map',
            createRelatedTable=False)
    physicalCards = MultipleJoin('PhysicalCard')

class Rarity_v1(SQLObject):
    """Rarity v1 - doesn't have shortname"""
    class sqlmeta:
        """meta class used to set the correct table."""
        table = Rarity.sqlmeta.table
    name = UnicodeCol(alternateID=True, length=20)

class RarityPair_Rv1(SQLObject):
    """RarityPior table that joins with Rarity_v1"""
    class sqlmeta:
        """meta class used to set the correct table."""
        table = RarityPair.sqlmeta.table
    expansion = ForeignKey('Expansion')
    rarity = ForeignKey('Rarity_v1')
    cards = RelatedJoin('AbstractCard_v2',
            intermediateTable='abs_rarity_pair_map', createRelatedTable=False)

class AbstractCardSet_ACv2(SQLObject):
    """AbstractCardSet table that joins with AbstractCard_v2"""
    class sqlmeta:
        """meta class used to set the correct table."""
        table = 'abstract_card_set'
    name = UnicodeCol(alternateID=True, length=50)
    author = UnicodeCol(length=50, default='')
    comment = UnicodeCol(default='')
    annotations = UnicodeCol(default='')
    # Provides a join to AbstractCard_v2, needed to read old DB
    cards = RelatedJoin('AbstractCard_v2',
            intermediateTable='abstract_map', createRelatedTable=False)

class AbstractCardSet_v3(SQLObject):
    """Old abstract card set table."""
    class sqlmeta:
        """meta class used to set the correct table."""
        table = 'abstract_card_set'
    name = UnicodeCol(alternateID=True, length=50)
    author = UnicodeCol(length=50, default='')
    comment = UnicodeCol(default='')
    annotations = UnicodeCol(default='')
    cards = RelatedJoin('AbstractCard_v3', intermediateTable='abstract_map',
            createRelatedTable=False)

class AbstractCard_v3(SQLObject):
    """Old abstract card with join to abstract card set."""
    class sqlmeta:
        """meta class used to set the correct table."""
        table = AbstractCard.sqlmeta.table
    canonicalName = UnicodeCol(alternateID=True, length=50)
    name = UnicodeCol(length=50)
    text = UnicodeCol()
    group = IntCol(default=None, dbName='grp')
    capacity = IntCol(default=None)
    cost = IntCol(default=None)
    life = IntCol(default=None)
    costtype = EnumCol(enumValues=['pool', 'blood', 'conviction', None],
            default=None)
    level = EnumCol(enumValues=['advanced', None], default=None)
    burnoption = BoolCol(default=False)
    discipline = RelatedJoin('DisciplinePair',
            intermediateTable='abs_discipline_pair_map',
            createRelatedTable=False)
    rarity = RelatedJoin('RarityPair',
            intermediateTable='abs_rarity_pair_map', createRelatedTable=False)
    clan = RelatedJoin('Clan',
            intermediateTable='abs_clan_map', createRelatedTable=False)
    cardtype = RelatedJoin('CardType', intermediateTable='abs_type_map',
            createRelatedTable=False)
    sect = RelatedJoin('Sect', intermediateTable='abs_sect_map',
            createRelatedTable=False)
    title = RelatedJoin('Title', intermediateTable='abs_title_map',
            createRelatedTable=False)
    creed = RelatedJoin('Creed', intermediateTable='abs_creed_map',
            createRelatedTable=False)
    virtue = RelatedJoin('Virtue', intermediateTable='abs_virtue_map',
            createRelatedTable=False)
    rulings = RelatedJoin('Ruling', intermediateTable='abs_ruling_map',
            createRelatedTable=False)
    sets = RelatedJoin('AbstractCardSet_v3', intermediateTable='abstract_map',
            createRelatedTable=False)
    physicalCards = MultipleJoin('PhysicalCard')

class PhysicalCardSet_v4(SQLObject):
    """Old PCS table without parent links."""
    class sqlmeta:
        """meta class used to set the correct table."""
        table = PhysicalCardSet.sqlmeta.table
    name = UnicodeCol(alternateID=True, length=50)
    author = UnicodeCol(length=50, default='')
    comment = UnicodeCol(default='')
    annotations = UnicodeCol(default='')
    inuse = BoolCol(default=False)
    cards = RelatedJoin('PhysicalCard', intermediateTable='physical_map',
            createRelatedTable=False)

class MapAbstractCardToAbstractCardSet_v3(SQLObject):
    """Old abstract card map to need so we can drop tables properly"""
    class sqlmeta:
        """meta class used to set the correct table."""
        table = 'abstract_map'
    abstractCard = ForeignKey('AbstractCard_v3', notNull=True)
    abstractCardSet = ForeignKey('AbstractCardSet_v3', notNull=True)

# pylint: enable-msg=C0103, W0232

def check_can_read_old_database(oConn):
    # pylint: disable-msg=R0912
    # This has to be a giant if .. elif statement to check all the classes
    # subdivision isn't really beneficial
    """Can we upgrade from this database version?

       Sutekh 0.5.x and 0.6.x can upgrade from the versions in Sutekh 0.4.x,
       but no earlier
       """
    oVer = DatabaseVersion()
    oVer.expire_cache()
    if not oVer.check_tables_and_versions([Rarity], [Rarity.tableversion],
            oConn) and not oVer.check_tables_and_versions([Rarity], [1],
                    oConn):
        raise UnknownVersion("Rarity")
    if not oVer.check_tables_and_versions([Expansion],
            [Expansion.tableversion], oConn):
        raise UnknownVersion("Expansion")
    if not oVer.check_tables_and_versions([Discipline],
            [Discipline.tableversion], oConn):
        raise UnknownVersion("Discipline")
    if not oVer.check_tables_and_versions([Clan], [Clan.tableversion], oConn):
        raise UnknownVersion("Clan")
    if not oVer.check_tables_and_versions([CardType], [CardType.tableversion],
            oConn):
        raise UnknownVersion("CardType")
    if not oVer.check_tables_and_versions([Creed], [Creed.tableversion],
            oConn):
        raise UnknownVersion("Creed")
    if not oVer.check_tables_and_versions([Virtue], [Virtue.tableversion],
            oConn):
        raise UnknownVersion("Virtue")
    if not oVer.check_tables_and_versions([Sect], [Sect.tableversion], oConn):
        raise UnknownVersion("Sect")
    if not oVer.check_tables_and_versions([Title], [Title.tableversion],
            oConn):
        raise UnknownVersion("Title")
    if not oVer.check_tables_and_versions([Ruling], [Ruling.tableversion],
            oConn):
        raise UnknownVersion("Ruling")
    if not oVer.check_tables_and_versions([DisciplinePair],
            [DisciplinePair.tableversion], oConn):
        raise UnknownVersion("DisciplinePair")
    if not oVer.check_tables_and_versions([RarityPair],
            [RarityPair.tableversion], oConn):
        raise UnknownVersion("RarityPair")
    if not oVer.check_tables_and_versions([AbstractCard],
            [AbstractCard.tableversion], oConn) \
            and not oVer.check_table_in_versions(AbstractCard, [2, 3]):
        raise UnknownVersion("AbstractCard")
    if not oVer.check_tables_and_versions([PhysicalCard],
            [PhysicalCard.tableversion], oConn):
        raise UnknownVersion("PhysicalCard")
    if not oVer.check_tables_and_versions([PhysicalCardSet],
            [PhysicalCardSet.tableversion], oConn) and not \
                    oVer.check_table_in_versions(PhysicalCardSet, [3, 4]):
        raise UnknownVersion("PhysicalCardSet")
    # NB: This test should go away for Sutekh 0.8, as we will no longer
    # support upgrading from DB version which have abstract card sets
    if not oVer.check_table_in_versions(AbstractCardSet_v3, [-1, 3]):
        raise UnknownVersion("AbstractCardSet")
    return True

def old_database_count(oConn):
    """Check number of items in old DB fro progress bars, etc."""
    oVer = DatabaseVersion()
    iCount = 12 # Card property tables
    if oVer.check_tables_and_versions([AbstractCard],
            [AbstractCard.tableversion], oConn):
        iCount += AbstractCard.select(connection=oConn).count()
    elif oVer.check_tables_and_versions([AbstractCard], [3], oConn):
        # We log once for each AC copied, and once for each set of PC's
        # created from the abstract cards
        iCount += 2 * AbstractCard_v3.select(connection=oConn).count()
    elif oVer.check_tables_and_versions([AbstractCard], [2], oConn):
        iCount += 2 * AbstractCard_v2.select(connection=oConn).count()
    if oVer.check_tables_and_versions([PhysicalCard],
            [PhysicalCard.tableversion], oConn):
        iCount += PhysicalCard.select(connection=oConn).count()
    if oVer.check_tables_and_versions([PhysicalCardSet],
            [PhysicalCardSet.tableversion], oConn):
        iCount += PhysicalCardSet.select(connection=oConn).count()
    elif oVer.check_tables_and_versions([PhysicalCardSet], [3], oConn):
        iCount += PhysicalCardSet_v3.select(connection=oConn).count()
    elif oVer.check_tables_and_versions([PhysicalCardSet], [4], oConn):
        iCount += PhysicalCardSet_v4.select(connection=oConn).count()
    if oVer.check_tables_and_versions([AbstractCardSet_v3], [3], oConn):
        iCount += AbstractCardSet_v3.select(connection=oConn).count()
    return iCount

# pylint: disable-msg=W0612
# W0612 - we have lots of unused variables from creating copies

def copy_rarity(oOrigConn, oTrans):
    """Copy rarity tables, assumings same version"""
    for oObj in Rarity.select(connection=oOrigConn):
        oCopy = Rarity(id=oObj.id, name=oObj.name,
                shortname=oObj.shortname, connection=oTrans)

def copy_old_rarity(oOrigConn, oTrans, oVer):
    """Copy rarity table, upgrading versions as needed"""
    if oVer.check_tables_and_versions([Rarity], [Rarity.tableversion],
            oOrigConn):
        copy_rarity(oOrigConn, oTrans)
    elif oVer.check_tables_and_versions([Rarity], [1], oOrigConn):
        for oObj in Rarity_v1.select(connection=oOrigConn):
            oCopy = Rarity(id=oObj.id, name=oObj.name,
                    shortname=Rarities.shortname(oObj.name),
                    connection=oTrans)
    else:
        return (False, ["Unknown Version for Rarity"])
    return (True, [])

def copy_expansion(oOrigConn, oTrans):
    """Copy expansion, assuming versions match"""
    for oObj in Expansion.select(connection=oOrigConn):
        oCopy = Expansion(id=oObj.id, name=oObj.name,
                shortname=oObj.shortname, connection=oTrans)

def copy_old_expansion(oOrigConn, oTrans, oVer):
    """Copy Expansion, updating as needed"""
    if oVer.check_tables_and_versions([Expansion], [Expansion.tableversion],
            oOrigConn):
        copy_expansion(oOrigConn, oTrans)
    else:
        return (False, ["Unknown Expansion Version"])
    return (True, [])

def copy_discipline(oOrigConn, oTrans):
    """Copy Discipline, assuming versions match"""
    for oObj in Discipline.select(connection=oOrigConn):
        oCopy = Discipline(id=oObj.id, name=oObj.name,
            fullname=oObj.fullname, connection=oTrans)

def copy_old_discipline(oOrigConn, oTrans, oVer):
    """Copy disciplines, upgrading as needed."""
    if oVer.check_tables_and_versions([Discipline], [Discipline.tableversion],
            oOrigConn):
        copy_discipline(oOrigConn, oTrans)
    else:
        return (False, ["Unknown Discipline version"])
    return (True, [])

def copy_clan(oOrigConn, oTrans):
    """Copy Clan, assuming database versions match"""
    for oObj in Clan.select(connection=oOrigConn):
        oCopy = Clan(id=oObj.id, name=oObj.name, shortname=oObj.shortname,
                connection=oTrans)

def copy_old_clan(oOrigConn, oTrans, oVer):
    """Copy clan, upgrading as needed."""
    if oVer.check_tables_and_versions([Clan], [Clan.tableversion], oOrigConn):
        copy_clan(oOrigConn, oTrans)
    else:
        return (False, ["Unknown Clan Version"])
    return (True, [])

def copy_creed(oOrigConn, oTrans):
    """Copy Creed, assuming versions match"""
    for oObj in Creed.select(connection=oOrigConn):
        oCopy = Creed(id=oObj.id, name=oObj.name, shortname=oObj.shortname,
                connection=oTrans)

def copy_old_creed(oOrigConn, oTrans, oVer):
    """Copy Creed, updating if needed"""
    if oVer.check_tables_and_versions([Creed], [Creed.tableversion],
            oOrigConn):
        copy_creed(oOrigConn, oTrans)
    else:
        return (False, ["Unknown Creed Version"])
    return (True, [])

def copy_virtue(oOrigConn, oTrans):
    """Copy Virtue, assuming versions match"""
    for oObj in Virtue.select(connection=oOrigConn):
        oCopy = Virtue(id=oObj.id, name=oObj.name, fullname=oObj.fullname,
                connection=oTrans)

def copy_old_virtue(oOrigConn, oTrans, oVer):
    """Copy Virtue, updating if needed"""
    if oVer.check_tables_and_versions([Virtue], [Virtue.tableversion],
            oOrigConn):
        copy_virtue(oOrigConn, oTrans)
    else:
        return (False, ["Unknown Virtue Version"])
    return (True, [])

def copy_card_type(oOrigConn, oTrans):
    """Copy CardType, assuming versions match"""
    for oObj in CardType.select(connection=oOrigConn):
        oCopy = CardType(id=oObj.id, name=oObj.name, connection=oTrans)

def copy_old_card_type(oOrigConn, oTrans, oVer):
    """Copy CardType, upgrading as needed"""
    if oVer.check_tables_and_versions([CardType], [CardType.tableversion],
            oOrigConn):
        copy_card_type(oOrigConn, oTrans)
    else:
        return (False, ["Unknown CardType Version"])
    return (True, [])

def copy_ruling(oOrigConn, oTrans):
    """Copy Ruling, assuming versions match"""
    for oObj in Ruling.select(connection=oOrigConn):
        oCopy = Ruling(id=oObj.id, text=oObj.text, code=oObj.code,
                url=oObj.url, connection=oTrans)

def copy_old_ruling(oOrigConn, oTrans, oVer):
    """Copy Ruling, upgrading as needed"""
    if oVer.check_tables_and_versions([CardType], [CardType.tableversion],
            oOrigConn):
        copy_ruling(oOrigConn, oTrans)
    else:
        return (False, ["Unknown Ruling Version"])
    return (True, [])

def copy_discipline_pair(oOrigConn, oTrans):
    """Copy DisciplinePair, assuming versions match"""
    for oObj in DisciplinePair.select(connection=oOrigConn):
        oCopy = DisciplinePair(id=oObj.id, level=oObj.level,
               discipline=oObj.discipline, connection=oTrans)

def copy_old_discipline_pair(oOrigConn, oTrans, oVer):
    """Copy DisciplinePair, upgrading if needed"""
    if oVer.check_tables_and_versions([DisciplinePair],
            [DisciplinePair.tableversion], oOrigConn):
        copy_discipline_pair(oOrigConn, oTrans)
    else:
        return (False, ["Unknown Discipline Version"])
    return (True, [])

def copy_rarity_pair(oOrigConn, oTrans):
    """Copy RairtyPair, assuming versions match"""
    for oObj in RarityPair.select(connection=oOrigConn):
        oCopy = RarityPair(id=oObj.id, expansion=oObj.expansion,
                rarity=oObj.rarity, connection=oTrans)

def copy_old_rarity_pair(oOrigConn, oTrans, oVer):
    """Copy RarityPair, upgrading as needed"""
    if oVer.check_tables_and_versions([RarityPair], [RarityPair.tableversion],
            oOrigConn) and oVer.check_tables_and_versions([Rarity],
                    [Rarity.tableversion], oOrigConn):
        copy_rarity_pair(oOrigConn, oTrans)
    elif oVer.check_tables_and_versions([RarityPair],
            [RarityPair.tableversion], oOrigConn) and \
            oVer.check_tables_and_versions([Rarity], [1], oOrigConn):
        for oObj in RarityPair_Rv1.select(connection=oOrigConn):
            oCopy = RarityPair(id=oObj.id, expansion=oObj.expansion,
                    rarity=oObj.rarity, connection=oTrans)
    else:
        return (False, ["Unknown RarityPair version"])
    return (True, [])

def copy_sect(oOrigConn, oTrans):
    """Copy Sect, assuming versions match"""
    for oObj in Sect.select(connection=oOrigConn):
        oCopy = Sect(id=oObj.id, name=oObj.name, connection=oTrans)

def copy_old_sect(oOrigConn, oTrans, oVer):
    """Copy Sect, updating if needed"""
    if oVer.check_tables_and_versions([Sect], [Sect.tableversion], oOrigConn):
        copy_sect(oOrigConn, oTrans)
    else:
        return (False, ["Unknown Sect Version"])
    return (True, [])

def copy_title(oOrigConn, oTrans):
    """Copy Title, assuming versions match"""
    for oObj in Title.select(connection=oOrigConn):
        oCopy = Title(id=oObj.id, name=oObj.name, connection=oTrans)

def copy_old_title(oOrigConn, oTrans, oVer):
    """Copy Title, updating if needed"""
    if oVer.check_tables_and_versions([Title], [Title.tableversion],
            oOrigConn):
        copy_title(oOrigConn, oTrans)
    else:
        return (False, ["Unknown Title Version"])
    return (True, [])

def copy_abstract_card(oOrigConn, oTrans, oLogger):
    """Copy AbstractCard, assuming versions match"""
    # pylint: disable-msg=E1101, R0912
    # E1101 - SQLObject confuses pylint
    # R0912 - need the branches for this
    for oCard in AbstractCard.select(connection=oOrigConn):
        oCardCopy = AbstractCard(id=oCard.id,
                canonicalName=oCard.canonicalName, name=oCard.name,
                text=oCard.text, connection=oTrans)
        # If I don't do things this way, I get encoding issues
        # I don't really feel like trying to understand why
        oCardCopy.group = oCard.group
        oCardCopy.capacity = oCard.capacity
        oCardCopy.cost = oCard.cost
        oCardCopy.costtype = oCard.costtype
        oCardCopy.level = oCard.level
        oCardCopy.life = oCard.life
        oCardCopy.burnoption = oCard.burnoption
        for oData in oCard.rarity:
            oCardCopy.addRarityPair(oData)
        for oData in oCard.discipline:
            oCardCopy.addDisciplinePair(oData)
        for oData in oCard.rulings:
            oCardCopy.addRuling(oData)
        for oData in oCard.clan:
            oCardCopy.addClan(oData)
        for oData in oCard.cardtype:
            oCardCopy.addCardType(oData)
        for oData in oCard.sect:
            oCardCopy.addSect(oData)
        for oData in oCard.title:
            oCardCopy.addTitle(oData)
        for oData in oCard.creed:
            oCardCopy.addCreed(oData)
        for oData in oCard.virtue:
            oCardCopy.addVirtue(oData)
        oCardCopy.syncUpdate()
        oLogger.info('copied AC %s', oCardCopy.name)

def copy_old_abstract_card(oOrigConn, oTrans, oLogger, oVer):
    """Copy AbstractCard, upgrading as needed"""
    # pylint: disable-msg=E1101, R0912
    # E1101 - SQLObject confuses pylint
    # R0912 - need the branches for this
    aMessages = []
    if oVer.check_tables_and_versions([AbstractCard],
            [AbstractCard.tableversion], oOrigConn):
        copy_abstract_card(oOrigConn, oTrans, oLogger)
    else:
        if oVer.check_tables_and_versions([AbstractCard], [3], oOrigConn):
            oACTable = AbstractCard_v3
            bHasBurn = True
        elif oVer.check_tables_and_versions([AbstractCard], [2], oOrigConn):
            aMessages.append('Missing data for the Burn Option on cards.'
                    ' You will need to reimport the White wolf card list'
                    ' for these to be correct')
            oACTable = AbstractCard_v2
            bHasBurn = False
        else:
            return (False, ["Unknown AbstractCard version"])
        for oCard in oACTable.select(connection=oOrigConn):
            oCardCopy = AbstractCard(id=oCard.id,
                    canonicalName=oCard.canonicalName, name=oCard.name,
                    text=oCard.text, connection=oTrans)
            oCardCopy.group = oCard.group
            oCardCopy.capacity = oCard.capacity
            oCardCopy.cost = oCard.cost
            oCardCopy.costtype = oCard.costtype
            oCardCopy.level = oCard.level
            oCardCopy.life = oCard.life
            if bHasBurn:
                oCardCopy.burnoption = oCard.burnoption
            else:
                oCardCopy.burnoption = False
            for oData in oCard.rarity:
                oCardCopy.addRarityPair(oData)
            for oData in oCard.discipline:
                oCardCopy.addDisciplinePair(oData)
            for oData in oCard.rulings:
                oCardCopy.addRuling(oData)
            for oData in oCard.clan:
                oCardCopy.addClan(oData)
            for oData in oCard.cardtype:
                oCardCopy.addCardType(oData)
            for oData in oCard.sect:
                oCardCopy.addSect(oData)
            for oData in oCard.title:
                oCardCopy.addTitle(oData)
            for oData in oCard.creed:
                oCardCopy.addCreed(oData)
            for oData in oCard.virtue:
                oCardCopy.addVirtue(oData)
            oCardCopy.syncUpdate()
            oLogger.info('copied AC %s', oCardCopy.name)
    return (True, aMessages)

def copy_physical_card(oOrigConn, oTrans, oLogger):
    """Copy PhysicalCard, assuming version match"""
    # We copy abstractCardID rather than abstractCard, to avoid issues
    # with abstract card class changes
    for oCard in PhysicalCard.select(connection=oOrigConn):
        oCardCopy = PhysicalCard(id=oCard.id,
                abstractCardID=oCard.abstractCardID,
                expansionID=oCard.expansionID, connection=oTrans)
        oLogger.info('copied PC %s', oCardCopy.id)

def get_new_physical_card(oCard, oTrans, aMessages):
    """Get the equivalent physical card in the new physical card table.

       If oCard is an AbstractCard, use None as the expansion.
       """
    if hasattr(oCard,'abstractCardID'):
        # must be a physical card
        oExp = oCard.expansion
        oId = oCard.abstractCardID
    else:
        oExp = None
        oId = oCard.id
    try:
        oNewCard = PhysicalCard.selectBy(
                    abstractCardID=oId,
                    expansion=oExp, connection=oTrans).getOne()
    except SQLObjectNotFound:
        if oExp is None:
            raise

        # probably an invalid (AbstractCard, Expansion) pair in the old
        # database. Try with no expansion.
        aMessages.append("'%s' isn't listed as appearing in" \
                         " expansion '%s'. Attempting to insert " \
                         " without an expansion." \
                         % (oCard.abstractCard.name, oCard.expansion.name))
        oNewCard = PhysicalCard.selectBy(
                    abstractCardID=oId,
                    expansion=None, connection=oTrans).getOne()
    return oNewCard

def copy_old_physical_card(oOrigConn, oTrans, oLogger, oVer):
    """Copy PhysicalCards, upgrading if needed."""
    aMessages = []
    if oVer.check_table_in_versions(PhysicalCardSet, [3, 4], oOrigConn) and \
            oVer.check_tables_and_versions([PhysicalCard],
                    [PhysicalCard.tableversion], oOrigConn):
        # We setup the list of cards and expansions as in the WW parser
        for oCard in AbstractCard.select(connection=oTrans):
            PhysicalCard(abstractCardID=oCard.id,
                    expansionID=None, connection=oTrans)
            for oExp in set([oRarity.expansion for oRarity in oCard.rarity]):
                PhysicalCard(abstractCardID=oCard.id,
                        expansionID=oExp.id, connection=oTrans)
            oTrans.commit()
            oLogger.info('created Physical Cards for AC %s', oCard.id)
        # We create a PhysicalCardSet named 'My Collection' and add the
        # changed cards here
        oPCLSet = PhysicalCardSet(name='My Collection', parent=None,
                connection=oTrans)
        # For all the Physical cards currently in the collection,
        # add them to the card set
        # pylint: disable-msg=E1101, E1103
        # SQLObject confuses pylint
        for oCard in PhysicalCard.select(connection=oOrigConn):
            oNewCard = get_new_physical_card(oCard, oTrans, aMessages)
            oPCLSet.addPhysicalCard(oNewCard.id)
            oLogger.info('copied PC %s', oNewCard.id)
    elif oVer.check_tables_and_versions([PhysicalCardSet, PhysicalCard],
            [PhysicalCardSet.tableversion, PhysicalCard.tableversion],
            oOrigConn):
        copy_physical_card(oOrigConn, oTrans, oLogger)
    else:
        return (False, ["Unknown PhysicalCard version"])
    return (True, aMessages)

def copy_physical_card_set(oOrigConn, oTrans, oLogger):
    """Copy PCS, assuming versions match"""
    # pylint: disable-msg=E1101
    # SQLObject confuses pylint
    aSets = list(PhysicalCardSet.select(connection=oOrigConn))
    bDone = False
    dDone = {}
    while not bDone:
        # We make sure we copy parent's before children
        # We need to be careful, since we don't retain card set IDs,
        # due to issues with sequence numbers
        aToDo = []
        for oSet in aSets:
            if oSet.parent is None or oSet.parent in dDone:
                if oSet.parent:
                    oParent = dDone[oSet.parent]
                else:
                    oParent = None
                oCopy = PhysicalCardSet(name=oSet.name,
                        author=oSet.author, comment=oSet.comment,
                        annotations=oSet.annotations, inuse=oSet.inuse,
                        parent=oParent, connection=oTrans)
                for oCard in oSet.cards:
                    oCopy.addPhysicalCard(oCard.id)
                oCopy.syncUpdate()
                oLogger.info('Copied PCS %s', oCopy.name)
                dDone[oSet] = oCopy
            else:
                aToDo.append(oSet)
        if not aToDo:
            bDone = True
        else:
            aSets = aToDo

def copy_old_physical_card_set(oOrigConn, oTrans, oLogger, oVer):
    """Copy PCS, upgrading as needed."""
    # pylint: disable-msg=E1101, E1103
    # SQLObject confuses pylint
    def _copy_cards(oOldSet, oNewSet):
        """Copy the cards from the old physical card set to the new set,
           replacing references to the correct new Physical Cards."""
        for oCard in oOldSet.cards:
            oNewCard = get_new_physical_card(oCard, oTrans, aMessages)
            oNewSet.addPhysicalCard(oNewCard.id)

    aMessages = []
    if oVer.check_tables_and_versions([PhysicalCardSet],
            [PhysicalCardSet.tableversion], oOrigConn) \
            and oVer.check_tables_and_versions([PhysicalCard],
                    [PhysicalCard.tableversion], oOrigConn):
        copy_physical_card_set(oOrigConn, oTrans, oLogger)
    else:
        if oVer.check_tables_and_versions([PhysicalCardSet], [3], oOrigConn):
            oPCSTable = PhysicalCardSet_v3
            bHasInUse = False
        elif oVer.check_tables_and_versions([PhysicalCardSet], [4], oOrigConn):
            oPCSTable = PhysicalCardSet_v4
            bHasInUse = True
        else:
            return (False, ["Unknown PhysicalCardSet version"])
        oParent = PhysicalCardSet.selectBy(name='My Collection',
                connection=oTrans).getOne()
        for oSet in oPCSTable.select(connection=oOrigConn):
            oCopy = PhysicalCardSet(name=oSet.name,
                    author=oSet.author, comment=oSet.comment,
                    annotations=None, inuse=False, parent=oParent,
                    connection=oTrans)
            _copy_cards(oSet, oCopy)
            if bHasInUse:
                oCopy.inuse = oSet.inuse
            oCopy.syncUpdate()
            oLogger.info('Copied PCS %s', oCopy.name)
    return (True, aMessages)

def copy_old_abstract_card_set(oOrigConn, oTrans, oLogger, oVer):
    """Copy old Abstract Card Sets, upgrading as needed."""
    # pylint: disable-msg=E1101
    # SQLObject confuses pylint
    def _gen_new_name(sSetName, aPhysSetNames):
        """Crate a new PCS name for the existing ACS"""
        sNewName = '(ACS) ' + sSetName
        sNewName = sNewName[:50]
        iSuffix = 0
        while sNewName in aPhysSetNames:
            sNewName = '(ACS) %s %d' % (sSetName[:40], iSuffix)
            sNewName = sNewName[:50]
            iSuffix += 1
        aPhysSetNames.append(sNewName)
        return sNewName

    def _copy_cards(oOldSet, oNewSet):
        """Copy the cards from the old abstract card set oOldSet to the
           PhysicalCardSet oNewSet, doing the right thing."""
        for oCard in oOldSet.cards:
            # We find the physical card with the same abstract card id
            # and No expansion info
            # pylint: disable-msg=E1103
            # SQLObject confuses pylint
            oNewCard = get_new_physical_card(oCard, oTrans, aMessages)
            oNewSet.addPhysicalCard(oNewCard.id)

    aMessages = []
    if oVer.check_tables_and_versions([AbstractCardSet_v3], [3], oOrigConn):
        aPhysSetNames = [x.name for x in
                PhysicalCardSet.select(connection=oTrans)]
        if oVer.check_tables_and_versions([AbstractCard], [3], oOrigConn):
            oACSTable = AbstractCardSet_v3
        elif oVer.check_tables_and_versions([AbstractCard], [2], oOrigConn):
            oACSTable = AbstractCardSet_ACv2
        else:
            return (False, ["Unknown AbstractCard version for the "
                "AbstractCardSet version"])
        for oSet in oACSTable.select(connection=oOrigConn):
            # Create a similiar Physical Card Set
            sNewName = _gen_new_name(oSet.name, aPhysSetNames)
            oNewPCS = PhysicalCardSet(name=sNewName, author=oSet.author,
                    annotations=oSet.annotations, comment=oSet.comment,
                    parent=None, inuse=False, connection=oTrans)
            _copy_cards(oSet, oNewPCS)
            oNewPCS.syncUpdate()
            oLogger.info('Copied Abstract CS %s', oNewPCS.name)
    else:
        return (False, ["Unknown AbstractCardSet version"])
    return (True, aMessages)

def read_old_database(oOrigConn, oDestConnn, oLogHandler=None):
    """Read the old database into new database, filling in
       blanks when needed"""
    try:
        if not check_can_read_old_database(oOrigConn):
            return False
    except UnknownVersion, oExp:
        raise oExp
    oLogger = Logger('read Old DB')
    if oLogHandler:
        oLogger.addHandler(oLogHandler)
        if hasattr(oLogHandler, 'set_total'):
            oLogHandler.set_total(old_database_count(oOrigConn))
    # OK, version checks pass, so we should be able to deal with this
    aMessages = []
    bRes = True
    oTrans = oDestConnn.transaction()
    # Magic happens in the individual functions, as needed
    aToCopy = [
            (copy_old_rarity, 'Rarity table', False),
            (copy_old_expansion, 'Expansion table', False),
            (copy_old_discipline, 'Discipline table', False),
            (copy_old_clan, 'Clan table', False),
            (copy_old_creed, 'Creed table', False),
            (copy_old_virtue, 'Virtue table', False),
            (copy_old_card_type, 'CardType table', False),
            (copy_old_ruling, 'Ruling table', False),
            (copy_old_discipline_pair, 'DisciplinePair table', False),
            (copy_old_rarity_pair, 'RarityPair table', False),
            (copy_old_sect, 'Sect table', False),
            (copy_old_title, 'Title table', False),
            (copy_old_abstract_card, 'AbstractCard table', True),
            (copy_old_physical_card, 'PhysicalCard table', True),
            (copy_old_physical_card_set, 'PhysicalCardSet table', True),
            (copy_old_abstract_card_set, 'AbstractCardSet table', True),
            ]
    oVer = DatabaseVersion()
    for fCopy, sName, bPassLogger in aToCopy:
        try:
            if bPassLogger:
                (bOK, aNewMessages) = fCopy(oOrigConn, oTrans, oLogger, oVer)
            else:
                (bOK, aNewMessages) = fCopy(oOrigConn, oTrans, oVer)
        except SQLObjectNotFound, oExp:
            bOK = False
            aNewMessages = ['Unable to copy %s: Error %s' % (sName, oExp)]
        else:
            if not bPassLogger:
                oLogger.info('%s copied' % sName)
        bRes = bRes and bOK
        aMessages.extend(aNewMessages)
        oTrans.commit()
        oTrans.cache.clear()
    return (bRes, aMessages)

# pylint: enable-msg=W0612, C0103

def drop_old_tables(oConn):
    """Drop tables whihc are no longer used from the database.
       Needed for postgres and other such things."""
    oVer = DatabaseVersion()
    if oVer.check_tables_and_versions([AbstractCardSet_v3], [3], oConn):
        # Need to drop the old ACS tables
        MapAbstractCardToAbstractCardSet_v3.dropTable(ifExists=True,
                connection=oConn)
        AbstractCardSet_v3.dropTable(ifExists=True, connection=oConn)

def copy_database(oOrigConn, oDestConnn, oLogHandler=None):
    """Copy the database, with no attempts to upgrade.

       This is a straight copy, with no provision for funky stuff
       Compatability of database structures is assumed, but not checked.
       """
    # Not checking versions probably should be fixed
    # Copy tables needed before we can copy AbstractCard
    flush_cache()
    oVer = DatabaseVersion()
    oVer.expire_cache()
    oLogger = Logger('copy DB')
    if oLogHandler:
        oLogger.addHandler(oLogHandler)
        if hasattr(oLogHandler, 'set_total'):
            iTotal = 12 + AbstractCard.select(connection=oOrigConn).count() + \
                    PhysicalCard.select(connection=oOrigConn).count() + \
                    PhysicalCardSet.select(connection=oOrigConn).count()
            oLogHandler.set_total(iTotal)
    bRes = True
    aMessages = []
    oTrans = oDestConnn.transaction()
    aToCopy = [
            (copy_rarity, 'Rarity table', False),
            (copy_expansion, 'Expansion table', False),
            (copy_discipline, 'Discipline table', False),
            (copy_clan, 'Clan table', False),
            (copy_creed, 'Creed table', False),
            (copy_virtue, 'Virtue table', False),
            (copy_card_type, 'CardType table', False),
            (copy_ruling, 'Ruling table', False),
            (copy_discipline_pair, 'DisciplinePair table', False),
            (copy_rarity_pair, 'RarityPair table', False),
            (copy_sect, 'Sect table', False),
            (copy_title, 'Title table', False),
            (copy_abstract_card, 'AbstractCard table', True),
            (copy_physical_card, 'PhysicalCard table', True),
            (copy_physical_card_set, 'PhysicalCardSet table', True),
            ]
    for fCopy, sName, bPassLogger in aToCopy:
        try:
            if bRes:
                if bPassLogger:
                    fCopy(oOrigConn, oTrans, oLogger)
                else:
                    fCopy(oOrigConn, oTrans)
        except SQLObjectNotFound, oExp:
            bRes = False
            aMessages.append('Unable to copy %s: Aborting with error: %s'
                    % (sName, oExp))
        else:
            oTrans.commit()
            oTrans.cache.clear()
            if not bPassLogger:
                oLogger.info('%s copied' % sName)
    flush_cache()
    # Clear out cache related joins and such
    return bRes, aMessages

def make_card_set_holder(oCardSet, oOrigConn):
    """Given a CardSet, create a Cached Card Set Holder for it."""
    oCurConn = sqlhub.processConnection
    sqlhub.processConnection = oOrigConn
    oCS = CachedCardSetHolder()
    oCS.name = oCardSet.name
    oCS.author = oCardSet.author
    oCS.comment = oCardSet.comment
    oCS.annotations = oCardSet.annotations
    oCS.inuse = oCardSet.inuse
    if oCardSet.parent:
        oCS.parent = oCardSet.parent.name
    for oCard in oCardSet.cards:
        if oCard.expansion is None:
            oCS.add(1, oCard.abstractCard.canonicalName, None)
        else:
            oCS.add(1, oCard.abstractCard.canonicalName, oCard.expansion.name)
    sqlhub.processConnection = oCurConn
    return oCS

def copy_to_new_abstract_card_db(oOrigConn, oNewConn, oCardLookup,
        oLogHandler=None):
    """Copy the card sets to a new Physical Card and Abstract Card List.

      Given an existing database, and a new database created from
      a new cardlist, copy the CardSets, going via CardSetHolders, so we
      can adapt to changed names, etc.
      """
    # pylint: disable-msg=R0914
    # we need a lot of variables here
    aPhysCardSets = []
    oOldConn = sqlhub.processConnection
    sqlhub.processConnection = oOrigConn
    # Copy Physical card sets
    oLogger = Logger('copy to new abstract card DB')
    if oLogHandler:
        oLogger.addHandler(oLogHandler)
        if hasattr(oLogHandler, 'set_total'):
            iTotal = 1 + PhysicalCardSet.select(connection=oOrigConn).count()
            oLogHandler.set_total(iTotal)
    aSets = list(PhysicalCardSet.select(connection=oOrigConn))
    bDone = False
    aDone = []
    # Ensre we only process a set after it's parent
    while not bDone:
        aToDo = []
        for oSet in aSets:
            if oSet.parent is None or oSet.parent in aDone:
                oCS = make_card_set_holder(oSet, oOrigConn)
                aPhysCardSets.append(oCS)
                aDone.append(oSet)
            else:
                aToDo.append(oSet)
        if not aToDo:
            bDone = True
        else:
            aSets = aToDo
    # Save the current mapping
    oLogger.info('Memory copies made')
    oTarget = oNewConn.transaction()
    sqlhub.processConnection = oTarget
    # Create the cardsets from the holders
    dLookupCache = {}
    for oSet in aPhysCardSets:
        oSet.create_pcs(oCardLookup, dLookupCache)
        oLogger.info('Physical Card Set: %s', oSet.name)
        oTarget.commit()
        oTarget.cache.clear()
    # Restore mapping
    oTarget = oNewConn.transaction()
    oTarget.commit()
    sqlhub.processConnection = oOldConn
    return (True, [])

def create_memory_copy(oTempConn, oLogHandler=None):
    """Create a temporary copy of the database in memory.

      We create a temporary memory database, and create the updated
      database in it. readOldDB is responsbile for upgrading stuff
      as needed
      """
    if refresh_tables(aObjectList, oTempConn):
        bRes, aMessages = read_old_database(sqlhub.processConnection,
                oTempConn, oLogHandler)
        oVer = DatabaseVersion()
        oVer.expire_cache()
        return bRes, aMessages
    return (False, ["Unable to create tables"])

def create_final_copy(oTempConn, oLogHandler=None):
    """Copy from the memory database to the real thing"""
    drop_old_tables(sqlhub.processConnection)
    if refresh_tables(aObjectList, sqlhub.processConnection):
        return copy_database(oTempConn, sqlhub.processConnection, oLogHandler)
    return (False, ["Unable to create tables"])

def attempt_database_upgrade(oLogHandler=None):
    """Attempt to upgrade the database, going via a temporary memory copy."""
    oTempConn = connectionForURI("sqlite:///:memory:")
    oLogger = Logger('attempt upgrade')
    if oLogHandler:
        oLogger.addHandler(oLogHandler)
    (bOK, aMessages) = create_memory_copy(oTempConn, oLogHandler)
    if bOK:
        oLogger.info("Copied database to memory, performing upgrade.")
        if len(aMessages) > 0:
            oLogger.info ("Messages reported: %s", aMessages)
        (bOK, aMessages) = create_final_copy(oTempConn, oLogHandler)
        if bOK:
            oLogger.info ("Everything seems to have gone OK")
            if len(aMessages) > 0:
                oLogger.info ("Messages reported %s", aMessages)
            return True
        else:
            oLogger.critical("Unable to perform upgrade.")
            if len(aMessages) > 0:
                oLogger.error("Errors reported: %s", aMessages)
            oLogger.critical("!!YOUR DATABASE MAY BE CORRUPTED!!")
    else:
        oLogger.error("Unable to create memory copy. Database not upgraded.")
        if len(aMessages) > 0:
            oLogger.error("Errors reported %s", aMessages)
    return False
