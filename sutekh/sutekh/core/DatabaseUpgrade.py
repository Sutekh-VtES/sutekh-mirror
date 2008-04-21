# DatabaseUpgrade.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006, 2007, 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""
Handles the heavy lifting of upgrading the database
Holds methods to copy database contents around, utility classes
to talk to old database versions, and so forth
"""

# pylint: disable-msg=E0611
# sqlobject confuses pylint herer
from sqlobject import sqlhub, SQLObject, IntCol, UnicodeCol, RelatedJoin, \
        EnumCol, MultipleJoin, connectionForURI, ForeignKey, SQLObjectNotFound
# pylint: enable-msg=E0611
from logging import Logger
from sutekh.core.SutekhObjects import PhysicalCard, AbstractCard, \
        AbstractCardSet, PhysicalCardSet, Expansion, Clan, Virtue, \
        Discipline, Rarity, RarityPair, CardType, Ruling, aObjectList, \
        DisciplinePair, Creed, Sect, Title
from sutekh.core.CardSetHolder import CachedCardSetHolder
from sutekh.core.PhysicalCardMappingHolder import PhysicalCardMappingHolder
from sutekh.SutekhUtility import refresh_tables
from sutekh.core.DatabaseVersion import DatabaseVersion
from sutekh.core.Abbreviations import Rarities

# This file handles all the grunt work of the database upgrades. We have some
# (arguablely overly) complex trickery to read old databases, and we create a
# copy in sqlite memory database first, before commiting to the actual DB

# Utility Exceptions

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
    rarity = RelatedJoin('RarityPair',
            intermediateTable='abs_rarity_pair_map', createRelatedTable=False)
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
    sets = RelatedJoin('AbstractCardSet', intermediateTable='abstract_map',
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
        table = AbstractCardSet.sqlmeta.table

    name = UnicodeCol(alternateID=True, length=50)
    author = UnicodeCol(length=50, default='')
    comment = UnicodeCol(default='')
    annotations = UnicodeCol(default='')
    # Provides a join to AbstractCard_v2, needed to read old DB
    cards = RelatedJoin('AbstractCard_v2',
            intermediateTable='abstract_map', createRelatedTable=False)

# pylint: enable-msg=C0103, W0232

def check_can_read_old_database():
    # pylint: disable-msg=R0912
    # This has to be a giant if .. elif statement to check all the classes
    # subdivision isn't really beneficial
    """Can we upgrade from this database version?

       Sutekh 0.5.x and 0.6.x can upgrade from the versions in Sutekh 0.4.x,
       but no earlier
       """
    oVer = DatabaseVersion()
    if not oVer.check_table_versions([Rarity], [Rarity.tableversion]) and \
            not oVer.check_table_versions([Rarity], [1]):
        raise UnknownVersion("Rarity")
    if not oVer.check_table_versions([Expansion], [Expansion.tableversion]):
        raise UnknownVersion("Expansion")
    if not oVer.check_table_versions([Discipline], [Discipline.tableversion]):
        raise UnknownVersion("Discipline")
    if not oVer.check_table_versions([Clan], [Clan.tableversion]):
        raise UnknownVersion("Clan")
    if not oVer.check_table_versions([CardType], [CardType.tableversion]):
        raise UnknownVersion("CardType")
    if not oVer.check_table_versions([Creed], [Creed.tableversion]):
        raise UnknownVersion("Creed")
    if not oVer.check_table_versions([Virtue], [Virtue.tableversion]):
        raise UnknownVersion("Virtue")
    if not oVer.check_table_versions([Sect], [Sect.tableversion]):
        raise UnknownVersion("Sect")
    if not oVer.check_table_versions([Title], [Title.tableversion]):
        raise UnknownVersion("Title")
    if not oVer.check_table_versions([Ruling], [Ruling.tableversion]):
        raise UnknownVersion("Ruling")
    if not oVer.check_table_versions([DisciplinePair],
            [DisciplinePair.tableversion]):
        raise UnknownVersion("DisciplinePair")
    if not oVer.check_table_versions([RarityPair], [RarityPair.tableversion]):
        raise UnknownVersion("RarityPair")
    if not oVer.check_table_versions([AbstractCard],
            [AbstractCard.tableversion]) \
            and not oVer.check_table_versions([AbstractCard], [2]):
        raise UnknownVersion("AbstractCard")
    if not oVer.check_table_versions([PhysicalCard],
            [PhysicalCard.tableversion]):
        raise UnknownVersion("PhysicalCard")
    if not oVer.check_table_versions([PhysicalCardSet],
            [PhysicalCardSet.tableversion]) and not oVer.check_table_versions(
                    [PhysicalCardSet], [3]):
        raise UnknownVersion("PhysicalCardSet")
    if not oVer.check_table_versions([AbstractCardSet],
            [AbstractCardSet.tableversion]):
        raise UnknownVersion("AbstractCardSet")
    return True

def old_database_count():
    """Check number of items in old DB fro progress bars, etc."""
    oVer = DatabaseVersion()
    iCount = 12 # Card property tables
    if oVer.check_table_versions([AbstractCard], [AbstractCard.tableversion]):
        iCount += AbstractCard.select().count()
    elif oVer.check_table_versions([AbstractCard], [2]):
        iCount += AbstractCard_v2.select().count()
    if oVer.check_table_versions([PhysicalCard], [PhysicalCard.tableversion]):
        iCount += PhysicalCard.select().count()
    if oVer.check_table_versions([PhysicalCardSet],
            [PhysicalCardSet.tableversion]):
        iCount += PhysicalCardSet.select().count()
    elif oVer.check_table_versions([PhysicalCardSet], [3]):
        iCount += PhysicalCardSet_v3.select().count()
    if oVer.check_table_versions([AbstractCardSet],
            [AbstractCardSet.tableversion]):
        iCount += AbstractCardSet.select().count()
    return iCount

# pylint: disable-msg=W0612
# W0612 - we have lots of unused variables from creating copies

def copy_rarity(oOrigConn, oTrans):
    """Copy rarity tables, assumings same version"""
    for oObj in Rarity.select(connection=oOrigConn):
        oCopy = Rarity(id=oObj.id, name=oObj.name,
                shortname=oObj.shortname, connection=oTrans)

def copy_old_rarity(oOrigConn, oTrans):
    """
    Copy rarity table, upgrading versions as needed
    """
    oVer = DatabaseVersion()
    if oVer.check_table_versions([Rarity], [Rarity.tableversion]):
        copy_rarity(oOrigConn, oTrans)
    elif oVer.check_table_versions([Rarity], [1]):
        for oObj in Rarity_v1.select(connection=oOrigConn):
            oCopy = Rarity(id=oObj.id, name=oObj.name,
                    shortname=Rarities.shortname(oObj.name),
                    connection=oTrans)
    else:
        return (False, ["Unknown Version for Rarity"])
    return (True, [])

def copy_expansion(oOrigConn, oTrans):
    """
    Copy expansion, assuming versions match
    """
    for oObj in Expansion.select(connection=oOrigConn):
        oCopy = Expansion(id=oObj.id, name=oObj.name,
                shortname=oObj.shortname, connection=oTrans)

def copy_old_expansion(oOrigConn, oTrans):
    """
    Copy Expansion, updating as needed
    """
    oVer = DatabaseVersion()
    if oVer.check_table_versions([Expansion], [Expansion.tableversion]):
        copy_expansion(oOrigConn, oTrans)
    else:
        return (False, ["Unknown Expansion Version"])
    return (True, [])

def copy_discipline(oOrigConn, oTrans):
    """
    Copy Discipline, assuming versions match
    """
    for oObj in Discipline.select(connection=oOrigConn):
        oCopy = Discipline(id=oObj.id, name=oObj.name,
            fullname=oObj.fullname, connection=oTrans)

def copy_old_discipline(oOrigConn, oTrans):
    """Copy disciplines, upgrading as needed."""
    oVer = DatabaseVersion()
    if oVer.check_table_versions([Discipline], [Discipline.tableversion]):
        copy_discipline(oOrigConn, oTrans)
    else:
        return (False, ["Unknown Discipline version"])
    return (True, [])

def copy_clan(oOrigConn, oTrans):
    """Copy Clan, assuming database versions match"""
    for oObj in Clan.select(connection=oOrigConn):
        oCopy = Clan(id=oObj.id, name=oObj.name, connection=oTrans)

def copy_old_clan(oOrigConn, oTrans):
    """Copy clan, upgrading as needed."""
    oVer = DatabaseVersion()
    if oVer.check_table_versions([Clan], [Clan.tableversion]):
        copy_clan(oOrigConn, oTrans)
    else:
        return (False, ["Unknown Clan Version"])
    return (True, [])

def copy_creed(oOrigConn, oTrans):
    """Copy Creed, assuming versions match"""
    for oObj in Creed.select(connection=oOrigConn):
        oCopy = Creed(id=oObj.id, name=oObj.name, shortname=oObj.shortname,
                connection=oTrans)

def copy_old_creed(oOrigConn, oTrans):
    """Copy Creed, updating if needed"""
    oVer = DatabaseVersion()
    if oVer.check_table_versions([Creed], [Creed.tableversion]):
        copy_creed(oOrigConn, oTrans)
    else:
        return (False, ["Unknown Creed Version"])
    return (True, [])

def copy_virtue(oOrigConn, oTrans):
    """Copy Virtue, assuming versions match"""
    for oObj in Virtue.select(connection=oOrigConn):
        oCopy = Virtue(id=oObj.id, name=oObj.name, fullname=oObj.fullname,
                connection=oTrans)

def copy_old_virtue(oOrigConn, oTrans):
    """Copy Virtue, updating if needed"""
    oVer = DatabaseVersion()
    if oVer.check_table_versions([Virtue], [Virtue.tableversion]):
        copy_virtue(oOrigConn, oTrans)
    else:
        return (False, ["Unknown Virtue Version"])
    return (True, [])

def copy_card_type(oOrigConn, oTrans):
    """Copy CardType, assuming versions match"""
    for oObj in CardType.select(connection=oOrigConn):
        oCopy = CardType(id=oObj.id, name=oObj.name, connection=oTrans)

def copy_old_card_type(oOrigConn, oTrans):
    """Copy CardType, upgrading as needed"""
    oVer = DatabaseVersion()
    if oVer.check_table_versions([CardType], [CardType.tableversion]):
        copy_card_type(oOrigConn, oTrans)
    else:
        return (False, ["Unknown CardType Version"])
    return (True, [])

def copy_ruling(oOrigConn, oTrans):
    """Copy Ruling, assuming versions match"""
    for oObj in Ruling.select(connection=oOrigConn):
        oCopy = Ruling(id=oObj.id, text=oObj.text, code=oObj.code,
                url=oObj.url, connection=oTrans)

def copy_old_ruling(oOrigConn, oTrans):
    """Copy Ruling, upgrading as needed"""
    oVer = DatabaseVersion()
    if oVer.check_table_versions([CardType], [CardType.tableversion]):
        copy_ruling(oOrigConn, oTrans)
    else:
        return (False, ["Unknown Ruling Version"])
    return (True, [])

def copy_discipline_pair(oOrigConn, oTrans):
    """Copy DisciplinePair, assuming versions match"""
    for oObj in DisciplinePair.select(connection=oOrigConn):
        oCopy = DisciplinePair(id=oObj.id, level=oObj.level,
               discipline=oObj.discipline, connection=oTrans)

def copy_old_discipline_pair(oOrigConn, oTrans):
    """Copy DisciplinePair, upgrading if needed"""
    oVer = DatabaseVersion()
    if oVer.check_table_versions([DisciplinePair],
            [DisciplinePair.tableversion]):
        copy_discipline_pair(oOrigConn, oTrans)
    else:
        return (False, ["Unknown Discipline Version"])
    return (True, [])

def copy_rarity_pair(oOrigConn, oTrans):
    """Copy RairtyPair, assuming versions match"""
    for oObj in RarityPair.select(connection=oOrigConn):
        oCopy = RarityPair(id=oObj.id, expansion=oObj.expansion,
                rarity=oObj.rarity, connection=oTrans)

def copy_old_rarity_pair(oOrigConn, oTrans):
    """Copy RarityPair, upgrading as needed"""
    oVer = DatabaseVersion()
    if oVer.check_table_versions([RarityPair], [RarityPair.tableversion]) and \
            oVer.check_table_versions([Rarity], [Rarity.tableversion]):
        copy_rarity_pair(oOrigConn, oTrans)
    elif oVer.check_table_versions([RarityPair],
            [RarityPair.tableversion]) and \
            oVer.check_table_versions([Rarity], [1]):
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

def copy_old_sect(oOrigConn, oTrans):
    """Copy Sect, updating if needed"""
    oVer = DatabaseVersion()
    if oVer.check_table_versions([Sect], [Sect.tableversion]):
        copy_sect(oOrigConn, oTrans)
    else:
        return (False, ["Unknown Sect Version"])
    return (True, [])

def copy_title(oOrigConn, oTrans):
    """Copy Title, assuming versions match"""
    for oObj in Title.select(connection=oOrigConn):
        oCopy = Title(id=oObj.id, name=oObj.name, connection=oTrans)

def copy_old_title(oOrigConn, oTrans):
    """Copy Title, updating if needed"""
    oVer = DatabaseVersion()
    if oVer.check_table_versions([Title], [Title.tableversion]):
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

def copy_old_abstract_card(oOrigConn, oTrans, oLogger):
    """Copy AbstractCard, upgrading as needed"""
    # pylint: disable-msg=E1101, R0912
    # E1101 - SQLObject confuses pylint
    # R0912 - need the branches for this
    oVer = DatabaseVersion()
    aMessages = []
    if oVer.check_table_versions([AbstractCard], [AbstractCard.tableversion]):
        copy_abstract_card(oOrigConn, oTrans, oLogger)
    elif oVer.check_table_versions([AbstractCard], [2]):
        aMessages.append('Missing data for the Burn Option on cards.'
                ' You will need to reimport the White wolf card list'
                ' for these to be correct')
        for oCard in AbstractCard_v2.select(connection=oOrigConn):
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
    else:
        return (False, ["Unknown AbstractCard version"])
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

def copy_old_physical_card(oOrigConn, oTrans, oLogger):
    """Copy PhysicalCards, upgrading if needed."""
    oVer = DatabaseVersion()
    if oVer.check_table_versions([PhysicalCard], [PhysicalCard.tableversion]):
        copy_physical_card(oOrigConn, oTrans, oLogger)
    else:
        return (False, ["Unknown PhysicalCard version"])
    return (True, [])

def copy_physical_card_set(oOrigConn, oTrans, oLogger):
    """Copy PCS, assuming versions match"""
    # pylint: disable-msg=E1101
    # SQLObject confuses pylint
    for oSet in PhysicalCardSet.select(connection=oOrigConn):
        oCopy = PhysicalCardSet(id=oSet.id, name=oSet.name,
                author=oSet.author, comment=oSet.comment,
                annotations=oSet.annotations, inuse=oSet.inuse,
                connection=oTrans)
        for oCard in oSet.cards:
            oCopy.addPhysicalCard(oCard.id)
        oCopy.syncUpdate()
        oLogger.info('Copied PCS %s', oCopy.name)

def copy_old_physical_card_set(oOrigConn, oTrans, oLogger):
    """Copy PCS, upgrading as needed."""
    # pylint: disable-msg=E1101
    # SQLObject confuses pylint
    oVer = DatabaseVersion()
    if oVer.check_table_versions([PhysicalCardSet],
            [PhysicalCardSet.tableversion]) \
            and oVer.check_table_versions([PhysicalCard],
                    [PhysicalCard.tableversion]):
        copy_physical_card_set(oOrigConn, oTrans, oLogger)
    elif oVer.check_table_versions([PhysicalCardSet], [3]):
        for oSet in PhysicalCardSet_v3.select(connection=oOrigConn):
            oCopy = PhysicalCardSet(id=oSet.id, name=oSet.name,
                    author=oSet.author, comment=oSet.comment,
                    annotations=None, inuse=False,
                    connection=oTrans)
            for oCard in oSet.cards:
                oCopy.addPhysicalCard(oCard.id)
            oCopy.syncUpdate()
            oLogger.info('Copied PCS %s', oCopy.name)
    else:
        return (False, ["Unknown PhysicalCardSet version"])
    return (True, [])

def copy_abstract_card_set(oOrigConn, oTrans, oLogger):
    """Copy AbstractCardSet, assuming versions match"""
    # pylint: disable-msg=E1101
    # SQLObject confuses pylint
    for oSet in AbstractCardSet.select(connection=oOrigConn):
        oCopy = AbstractCardSet(id=oSet.id, name=oSet.name,
                author=oSet.author, comment=oSet.comment,
                annotations=oSet.annotations, connection=oTrans)
        for oCard in oSet.cards:
            oCopy.addAbstractCard(oCard.id)
        oCopy.syncUpdate()
        oLogger.info('Copied ACS %s', oCopy.name)

def copy_old_abstract_card_set(oOrigConn, oTrans, oLogger):
    """Copy old Abstract Card Sets, upgrading as needed."""
    # pylint: disable-msg=E1101
    # SQLObject confuses pylint
    oVer = DatabaseVersion()
    if oVer.check_table_versions([AbstractCardSet],
            [AbstractCardSet.tableversion]) \
            and oVer.check_table_versions([AbstractCard],
                    [AbstractCard.tableversion]):
        copy_abstract_card_set(oOrigConn, oTrans, oLogger)
    elif oVer.check_table_versions([AbstractCard], [2]):
        # Upgrade from previous AbstractCard class
        for oSet in AbstractCardSet_ACv2.select(connection=oOrigConn):
            oCopy = AbstractCardSet(id=oSet.id, name=oSet.name,
                    author=oSet.author, comment=oSet.comment,
                    annotations=oSet.annotations, connection=oTrans)
            for oCard in oSet.cards:
                oCopy.addAbstractCard(oCard.id)
            oCopy.syncUpdate()
            oLogger.info('Copied ACS %s', oCopy.name)
    else:
        return (False, ["Unknown AbstractCardSet version"])
    return (True, [])

def read_old_database(oOrigConn, oDestConnn, oLogHandler=None):
    """Read the old database into new database, filling in
       blanks when needed"""
    try:
        if not check_can_read_old_database():
            return False
    except UnknownVersion, oErr:
        raise oErr
    oLogger = Logger('read Old DB')
    if oLogHandler:
        oLogger.addHandler(oLogHandler)
        if hasattr(oLogHandler, 'set_total'):
            oLogHandler.set_total(old_database_count())
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
    for fCopy, sName, bPassLogger in aToCopy:
        try:
            if bPassLogger:
                (bOK, aNewMessages) = fCopy(oOrigConn, oTrans, oLogger)
            else:
                (bOK, aNewMessages) = fCopy(oOrigConn, oTrans)
        except SQLObjectNotFound, oExp:
            bOK = False
            aNewMessages = ['Unable to copy %s: Error %s' % (sName, oExp)]
        else:
            if not bPassLogger:
                oLogger.info('%s copied' % sName)
        bRes = bRes and bOK
        aMessages += aNewMessages
        oTrans.commit()
        oTrans.cache.clear()
    return (bRes, aMessages)

# pylint: enable-msg=W0612, C0103

def copy_database(oOrigConn, oDestConnn, oLogHandler=None):
    """Copy the database, with no attempts to upgrade.

       This is a straight copy, with no provision for funky stuff
       Compatability of database structures is assumed, but not checked.
       """
    # Not checking versions probably should be fixed
    # Copy tables needed before we can copy AbstractCard
    oLogger = Logger('copy DB')
    if oLogHandler:
        oLogger.addHandler(oLogHandler)
        if hasattr(oLogHandler, 'set_total'):
            iTotal = 12 + AbstractCard.select(connection=oOrigConn).count() + \
                    PhysicalCard.select(connection=oOrigConn).count() + \
                    PhysicalCardSet.select(connection=oOrigConn).count() + \
                    AbstractCardSet.select(connection=oOrigConn).count()
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
            (copy_abstract_card_set, 'AbstractCardSet table', True),
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
    return bRes, aMessages

def make_card_set_holder(oCardSet):
    """Given a CardSet, create a Cached Card Set Holder for it."""
    oCS = CachedCardSetHolder()
    oCS.name = oCardSet.name
    oCS.author = oCardSet.author
    oCS.comment = oCardSet.comment
    oCS.annotations = oCardSet.annotations
    for oCard in oCardSet.cards:
        if type(oCard) is PhysicalCard:
            if oCard.expansion is None:
                oCS.add(1, oCard.abstractCard.canonicalName)
            else:
                oCS.add(1, oCard.abstractCard.canonicalName,
                        oCard.expansion.name)
        else:
            oCS.add(1, oCard.canonicalName)
    return oCS

def copy_to_new_abstract_card_db(oOrigConn, oNewConn, oCardLookup,
        oLogHandler=None):
    """Copy the physical card and the card sets to a new Abstract Card List.

      Given an existing database, and a new database created from
      a new cardlist, copy the PhysicalCards and the CardSets,
      going via CardSetHolders, so we can adapt to changed names, etc.
      """
    # pylint: disable-msg=R0914
    aPhysCardSets = []
    aAbsCardSets = []
    oOldConn = sqlhub.processConnection
    # Copy the physical card list
    oLogger = Logger('copy to new abstract card DB')
    if oLogHandler:
        oLogger.addHandler(oLogHandler)
        if hasattr(oLogHandler, 'set_total'):
            iTotal = 2 + PhysicalCardSet.select(connection=oOrigConn).count() \
                    + AbstractCardSet.select(connection=oOrigConn).count()
            oLogHandler.set_total(iTotal)
    oPhysListCS = CachedCardSetHolder()
    for oCard in PhysicalCard.select(connection=oOrigConn):
        if oCard.expansion is None:
            oPhysListCS.add(1, oCard.abstractCard.canonicalName)
        else:
            oPhysListCS.add(1, oCard.abstractCard.canonicalName,
                oCard.expansion.name)
    # Copy Physical card sets
    for oSet in PhysicalCardSet.select(connection=oOrigConn):
        oCS = make_card_set_holder(oSet)
        oCS.inuse = oSet.inuse
        aPhysCardSets.append(oCS)
    # Copy AbstractCardSets
    for oSet in AbstractCardSet.select(connection=oOrigConn):
        oCS = make_card_set_holder(oSet)
        aAbsCardSets.append(oCS)
    # Save the current mapping
    oMapping = PhysicalCardMappingHolder()
    oMapping.fill_from_db(oOrigConn)
    oLogger.info('Memory copies made')
    oTarget = oNewConn.transaction()
    sqlhub.processConnection = oTarget
    # Create the cardsets from the holders
    dLookupCache = oPhysListCS.create_physical_cl(oCardLookup)
    oLogger.info('Physical Card list copied')
    for oSet in aAbsCardSets:
        oSet.create_acs(oCardLookup, dLookupCache)
        oLogger.info('Abstract Card Set: %s', oSet.name)
        oTarget.commit()
        oTarget.cache.clear()
    for oSet in aPhysCardSets:
        oSet.create_pcs(oCardLookup, dLookupCache)
        oLogger.info('Physical Card Set: %s', oSet.name)
        oTarget.commit()
        oTarget.cache.clear()
    # Restore mapping
    oTarget = oNewConn.transaction()
    oMapping.commit_to_db(oTarget, dLookupCache)
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
        return read_old_database(sqlhub.processConnection, oTempConn,
                oLogHandler)
    else:
        return (False, ["Unable to create tables"])

def create_final_copy(oTempConn, oLogHandler=None):
    """Copy from the memory database to the real thing"""
    if refresh_tables(aObjectList, sqlhub.processConnection):
        return copy_database(oTempConn, sqlhub.processConnection, oLogHandler)
    else:
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
            return False
    else:
        oLogger.error("Unable to create memory copy. Database not upgraded.")
        if len(aMessages) > 0:
            oLogger.error("Errors reported %s", aMessages)
        return False
