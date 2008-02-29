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

from sqlobject import sqlhub, SQLObject, IntCol, UnicodeCol, RelatedJoin, \
        EnumCol, MultipleJoin, connectionForURI, ForeignKey
from logging import Logger
from sutekh.core.SutekhObjects import PhysicalCard, AbstractCard, \
        AbstractCardSet, PhysicalCardSet, Expansion, Clan, Virtue, \
        Discipline, Rarity, RarityPair, CardType, Ruling, ObjectList, \
        DisciplinePair, Creed, Sect, Title
from sutekh.core.CardSetHolder import CachedCardSetHolder
from sutekh.SutekhUtility import refresh_tables
from sutekh.core.DatabaseVersion import DatabaseVersion
from sutekh.core.Abbreviations import Rarities

# This file handles all the grunt work of the database upgrades. We have some
# (arguablely overly) complex trickery to read old databases, and we create a
# copy in sqlite memory database first, before commiting to the actual DB

# Utility Exceptions

class UnknownVersion(Exception):
    def __init__(self, TableName):
        super(UnknownVersion, self).__init__()
        self.sTableName = TableName

    def __str__(self):
        return "Unrecognised version for " + self.sTableName

# We Need to clone the SQLObject classes in SutekhObjects so we can read
# old versions

class PhysicalCardSet_v3(SQLObject):
    class sqlmeta:
        table = PhysicalCardSet.sqlmeta.table
    name = UnicodeCol(alternateID=True, length=50)
    author = UnicodeCol(length=50, default='')
    comment = UnicodeCol(default='')
    annotations = UnicodeCol(default='')
    cards = RelatedJoin('PhysicalCard', intermediateTable='physical_map',
            createRelatedTable=False)

class AbstractCard_v2(SQLObject):
    class sqlmeta:
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
    class sqlmeta:
        table = Rarity.sqlmeta.table

    name = UnicodeCol(alternateID=True, length=20)

class RarityPair_Rv1(SQLObject):
    class sqlmeta:
        table = RarityPair.sqlmeta.table

    expansion = ForeignKey('Expansion')
    rarity = ForeignKey('Rarity_v1')
    cards = RelatedJoin('AbstractCard_v2',
            intermediateTable='abs_rarity_pair_map', createRelatedTable=False)

class AbstractCardSet_ACv2(SQLObject):
    class sqlmeta:
        table = AbstractCardSet.sqlmeta.table

    name = UnicodeCol(alternateID=True, length=50)
    author = UnicodeCol(length=50, default='')
    comment = UnicodeCol(default='')
    annotations = UnicodeCol(default='')
    # Provides a join to AbstractCard_v2, needed to read old DB
    cards = RelatedJoin('AbstractCard_v2',
            intermediateTable='abstract_map', createRelatedTable=False)

def check_can_read_old_database():
    """
    Can we upgrade from this database version?
    Sutekh 0.5.x can upgrade from the versions in Sutekh 0.4.x, but no earlier
    """
    oVer = DatabaseVersion()
    if not oVer.checkVersions([Rarity], [Rarity.tableversion]) and \
            not oVer.checkVersions([Rarity], [1]):
        raise UnknownVersion("Rarity")
    if not oVer.checkVersions([Expansion], [Expansion.tableversion]):
        raise UnknownVersion("Expansion")
    if not oVer.checkVersions([Discipline], [Discipline.tableversion]):
        raise UnknownVersion("Discipline")
    if not oVer.checkVersions([Clan], [Clan.tableversion]):
        raise UnknownVersion("Clan")
    if not oVer.checkVersions([CardType], [CardType.tableversion]):
        raise UnknownVersion("CardType")
    if not oVer.checkVersions([Creed], [Creed.tableversion]):
        raise UnknownVersion("Creed")
    if not oVer.checkVersions([Virtue], [Virtue.tableversion]):
        raise UnknownVersion("Virtue")
    if not oVer.checkVersions([Sect], [Sect.tableversion]):
        raise UnknownVersion("Sect")
    if not oVer.checkVersions([Title], [Title.tableversion]):
        raise UnknownVersion("Title")
    if not oVer.checkVersions([Ruling], [Ruling.tableversion]):
        raise UnknownVersion("Ruling")
    if not oVer.checkVersions([DisciplinePair], [DisciplinePair.tableversion]):
        raise UnknownVersion("DisciplinePair")
    if not oVer.checkVersions([RarityPair], [RarityPair.tableversion]):
        raise UnknownVersion("RarityPair")
    if not oVer.checkVersions([AbstractCard], [AbstractCard.tableversion]) and \
            not oVer.checkVersions([AbstractCard], [2]):
        raise UnknownVersion("AbstractCard")
    if not oVer.checkVersions([PhysicalCard], [PhysicalCard.tableversion]):
        raise UnknownVersion("PhysicalCard")
    if not oVer.checkVersions([PhysicalCardSet], [PhysicalCardSet.tableversion]) and \
            not oVer.checkVersions([PhysicalCardSet], [3]):
        raise UnknownVersion("PhysicalCardSet")
    if not oVer.checkVersions([AbstractCardSet], [AbstractCardSet.tableversion]):
        raise UnknownVersion("AbstractCardSet")
    return True

def old_database_count():
    """
    Check number of items in old DB fro progress bars, etc.
    """
    oVer = DatabaseVersion()
    iCount = 12 # Card property tables
    if oVer.checkVersions([AbstractCard], [AbstractCard.tableversion]):
        iCount += AbstractCard.select().count()
    elif oVer.checkVersions([AbstractCard], [2]):
        iCount += AbstractCard_v2.select().count()
    if oVer.checkVersions([PhysicalCard], [PhysicalCard.tableversion]):
        iCount += PhysicalCard.select().count()
    if oVer.checkVersions([PhysicalCardSet], [PhysicalCardSet.tableversion]):
        iCount += PhysicalCardSet.select().count()
    elif oVer.checkVersions([PhysicalCardSet], [3]):
        iCount += PhysicalCardSet_v3.select().count()
    if oVer.checkVersions([AbstractCardSet], [AbstractCardSet.tableversion]):
        iCount += AbstractCardSet.select().count()
    return iCount

def copy_Rarity(oOrigConn, oTrans):
    """
    Copy rarity tables, assumings same version
    """
    for oObj in Rarity.select(connection=oOrigConn):
        oCopy = Rarity(id=oObj.id, name=oObj.name,
                shortname=oObj.shortname, connection=oTrans)

def copy_old_Rarity(oOrigConn, oTrans):
    """
    Copy rarity table, upgrading versions as needed
    """
    oVer = DatabaseVersion()
    if oVer.checkVersions([Rarity], [Rarity.tableversion]):
        copy_Rarity(oOrigConn, oTrans)
    elif oVer.checkVersions([Rarity], [1]):
        for oObj in Rarity_v1.select(connection=oOrigConn):
            oCopy = Rarity(id=oObj.id, name=oObj.name,
                    shortname=Rarities.shortname(oObj.name),
                    connection=oTrans)
    else:
        return (False, ["Unknown Version for Rarity"])
    return (True, [])

def copy_Expansion(oOrigConn, oTrans):
    """
    Copy expansion, assuming versions match
    """
    for oObj in Expansion.select(connection=oOrigConn):
        oCopy = Expansion(id=oObj.id, name=oObj.name,
                shortname=oObj.shortname, connection=oTrans)

def copy_old_Expansion(oOrigConn, oTrans):
    """
    Copy Expansion, updating as needed
    """
    oVer = DatabaseVersion()
    if oVer.checkVersions([Expansion], [Expansion.tableversion]):
        copy_Expansion(oOrigConn, oTrans)
    else:
        return (False, ["Unknown Expansion Version"])
    return (True, [])

def copy_Discipline(oOrigConn, oTrans):
    """
    Copy Discipline, assuming versions match
    """
    for oObj in Discipline.select(connection=oOrigConn):
        oCopy = Discipline(id=oObj.id, name=oObj.name,
            fullname=oObj.fullname, connection=oTrans)

def copy_old_Discipline(oOrigConn, oTrans):
    oVer = DatabaseVersion()
    if oVer.checkVersions([Discipline], [Discipline.tableversion]):
        copy_Discipline(oOrigConn, oTrans)
    else:
        return (False, ["Unknown Discipline version"])
    return (True, [])

def copy_Clan(oOrigConn, oTrans):
    """
    Copy Clan, assuming database versions match
    """
    for oObj in Clan.select(connection=oOrigConn):
        oCopy = Clan(id=oObj.id, name=oObj.name, connection=oTrans)

def copy_old_Clan(oOrigConn, oTrans):
    oVer = DatabaseVersion()
    if oVer.checkVersions([Clan], [Clan.tableversion]):
        copy_Clan(oOrigConn, oTrans)
    else:
        return (False, ["Unknown Clan Version"])
    return (True, [])

def copy_Creed(oOrigConn, oTrans):
    """
    Copy Creed, assuming versions match
    """
    for oObj in Creed.select(connection=oOrigConn):
        oCopy = Creed(id=oObj.id, name=oObj.name, shortname=oObj.shortname,
                connection=oTrans)

def copy_old_Creed(oOrigConn, oTrans):
    """
    Copy Creed, updating if needed
    """
    oVer = DatabaseVersion()
    if oVer.checkVersions([Creed], [Creed.tableversion]):
        copy_Creed(oOrigConn, oTrans)
    else:
        return (False, ["Unknown Creed Version"])
    return (True, [])

def copy_Virtue(oOrigConn, oTrans):
    """
    Copy Virtue, assuming versions match
    """
    for oObj in Virtue.select(connection=oOrigConn):
        oCopy = Virtue(id=oObj.id, name=oObj.name, fullname=oObj.fullname,
                connection=oTrans)

def copy_old_Virtue(oOrigConn, oTrans):
    """
    Copy Virtue, updating if needed
    """
    oVer = DatabaseVersion()
    if oVer.checkVersions([Virtue], [Virtue.tableversion]):
        copy_Virtue(oOrigConn, oTrans)
    else:
        return (False, ["Unknown Virtue Version"])
    return (True, [])

def copy_CardType(oOrigConn, oTrans):
    """
    Copy CardType, assuming versions match
    """
    for oObj in CardType.select(connection=oOrigConn):
        oCopy = CardType(id=oObj.id, name=oObj.name, connection=oTrans)

def copy_old_CardType(oOrigConn, oTrans):
    """
    Copy CardType, upgrading as needed
    """
    oVer = DatabaseVersion()
    if oVer.checkVersions([CardType], [CardType.tableversion]):
        copy_CardType(oOrigConn, oTrans)
    else:
        return (False, ["Unknown CardType Version"])
    return (True, [])

def copy_Ruling(oOrigConn, oTrans):
    """
    Copy Ruling, assuming versions match
    """
    for oObj in Ruling.select(connection=oOrigConn):
        oCopy = Ruling(id=oObj.id, text=oObj.text, code=oObj.code, url=oObj.url,
                connection=oTrans)

def copy_old_Ruling(oOrigConn, oTrans):
    """
    Copy Ruling, upgrading as needed
    """
    oVer = DatabaseVersion()
    if oVer.checkVersions([CardType], [CardType.tableversion]):
        copy_Ruling(oOrigConn, oTrans)
    else:
        return (False, ["Unknown Ruling Version"])
    return (True, [])

def copy_DisciplinePair(oOrigConn, oTrans):
    """
    Copy DisciplinePair, assuming versions match
    """
    for oObj in DisciplinePair.select(connection=oOrigConn):
        oCopy = DisciplinePair(id=oObj.id, level=oObj.level,
               discipline=oObj.discipline, connection=oTrans)

def copy_old_DisciplinePair(oOrigConn, oTrans):
    oVer = DatabaseVersion()
    if oVer.checkVersions([DisciplinePair], [DisciplinePair.tableversion]):
        copy_DisciplinePair(oOrigConn, oTrans)
    else:
        return (False, ["Unknown Discipline Version"])
    return (True, [])

def copy_RarityPair(oOrigConn, oTrans):
    """
    Copy RairtyPair, assuming versions match
    """
    for oObj in RarityPair.select(connection=oOrigConn):
        oCopy = RarityPair(id=oObj.id, expansion=oObj.expansion,
                rarity=oObj.rarity, connection=oTrans)

def copy_old_RarityPair(oOrigConn, oTrans):
    """
    Copy RarityPair, upgrading as needed
    """
    oVer = DatabaseVersion()
    if oVer.checkVersions([RarityPair], [RarityPair.tableversion]) and \
            oVer.checkVersions([Rarity], [Rarity.tableversion]):
        copy_RarityPair(oOrigConn, oTrans)
    elif oVer.checkVersions([RarityPair], [RarityPair.tableversion]) and \
            oVer.checkVersions([Rarity], [1]):
        for oObj in RarityPair_Rv1.select(connection=oOrigConn):
            oCopy = RarityPair(id=oObj.id, expansion=oObj.expansion,
                    rarity=oObj.rarity, connection=oTrans)
    else:
        return (False, ["Unknown RarityPair version"])
    return (True, [])

def copy_Sect(oOrigConn, oTrans):
    """
    Copy Sect, assuming versions match
    """
    for oObj in Sect.select(connection=oOrigConn):
        oCopy = Sect(id=oObj.id, name=oObj.name, connection=oTrans)

def copy_old_Sect(oOrigConn, oTrans):
    """
    Copy Sect, updating if needed
    """
    oVer = DatabaseVersion()
    if oVer.checkVersions([Sect], [Sect.tableversion]):
        copy_Sect(oOrigConn, oTrans)
    else:
        return (False, ["Unknown Sect Version"])
    return (True, [])

def copy_Title(oOrigConn, oTrans):
    """
    Copy Title, assuming versions match
    """
    for oObj in Title.select(connection=oOrigConn):
        oCopy = Title(id=oObj.id, name=oObj.name, connection=oTrans)

def copy_old_Title(oOrigConn, oTrans):
    """
    Copy Title, updating if needed
    """
    oVer = DatabaseVersion()
    if oVer.checkVersions([Title], [Title.tableversion]):
        copy_Title(oOrigConn, oTrans)
    else:
        return (False, ["Unknown Title Version"])
    return (True, [])

def copy_AbstractCard(oOrigConn, oTrans, oLogger):
    """
    Copy AbstractCard, assuming versions match
    """
    for oCard in AbstractCard.select(connection=oOrigConn):
        oCardCopy = AbstractCard(id=oCard.id, canonicalName=oCard.canonicalName,
                name=oCard.name, text=oCard.text, connection=oTrans)
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

def copy_old_AbstractCard(oOrigConn, oTrans, oLogger):
    """
    Copy AbstractCard, upgrading as needed
    """
    oVer = DatabaseVersion()
    aMessages = []
    if oVer.checkVersions([AbstractCard], [AbstractCard.tableversion]):
        copy_AbstractCard(oOrigConn, oTrans, oLogger)
    elif oVer.checkVersions([AbstractCard], [2]):
        aMessages.append('Missing data for the Burn Option on cards. You will need to reimport the White wolf card list for these to be correct')
        for oCard in AbstractCard_v2.select(connection=oOrigConn):
            oCardCopy = AbstractCard(id=oCard.id, canonicalName=oCard.canonicalName,
                    name=oCard.name, text=oCard.text, connection=oTrans)
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

def copy_PhysicalCard(oOrigConn, oTrans, oLogger):
    """
    Copy PhysicalCard, assuming version match
    """
    # We copy abstractCardID rather than abstractCard, to avoid issues
    # with abstract card class changes
    for oCard in PhysicalCard.select(connection=oOrigConn):
        oCardCopy = PhysicalCard(id=oCard.id, abstractCardID=oCard.abstractCardID,
                expansionID=oCard.expansionID, connection=oTrans)
        oLogger.info('copied PC %s', oCardCopy.id)

def copy_old_PhysicalCard(oOrigConn, oTrans, oLogger):
    oVer = DatabaseVersion()
    if oVer.checkVersions([PhysicalCard], [PhysicalCard.tableversion]):
        copy_PhysicalCard(oOrigConn, oTrans, oLogger)
    else:
        return (False, ["Unknown PhysicalCard version"])
    return (True, [])

def copy_PhysicalCardSet(oOrigConn, oTrans, oLogger):
    """
    Copy PCS, assuming versions match
    """
    for oSet in PhysicalCardSet.select(connection=oOrigConn):
        oCopy = PhysicalCardSet(id=oSet.id, name=oSet.name,
                author=oSet.author, comment=oSet.comment,
                annotations=oSet.annotations, inuse=oSet.inuse,
                connection=oTrans)
        for oCard in oSet.cards:
            oCopy.addPhysicalCard(oCard.id)
        oCopy.syncUpdate()
        oLogger.info('Copied PCS %s', oCopy.name)

def copy_old_PhysicalCardSet(oOrigConn, oTrans, oLogger):
    """
    Copy PCS, upgrading as needed
    """
    oVer = DatabaseVersion()
    if oVer.checkVersions([PhysicalCardSet], [PhysicalCardSet.tableversion]) \
            and oVer.checkVersions([PhysicalCard], [PhysicalCard.tableversion]):
        copy_PhysicalCardSet(oOrigConn, oTrans, oLogger)
    elif oVer.checkVersions([PhysicalCardSet], [3]):
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

def copy_AbstractCardSet(oOrigConn, oTrans, oLogger):
    """
    Copy AbstractCardSet, assuming versions match
    """
    for oSet in AbstractCardSet.select(connection=oOrigConn):
        oCopy = AbstractCardSet(id=oSet.id, name=oSet.name,
                author=oSet.author, comment=oSet.comment,
                annotations=oSet.annotations, connection=oTrans)
        for oCard in oSet.cards:
            oCopy.addAbstractCard(oCard.id)
        oCopy.syncUpdate()
        oLogger.info('Copied ACS %s', oCopy.name)

def copy_old_AbstractCardSet(oOrigConn, oTrans, oLogger):
    oVer = DatabaseVersion()
    if oVer.checkVersions([AbstractCardSet], [AbstractCardSet.tableversion]) \
            and oVer.checkVersions([AbstractCard], [AbstractCard.tableversion]):
        copy_AbstractCardSet(oOrigConn, oTrans, oLogger)
    elif oVer.checkVersions([AbstractCard], [2]):
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
    (bOK, aNewMessages) = copy_old_Rarity(oOrigConn, oTrans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    oLogger.info('Rarity table copied')
    (bOK, aMessages) = copy_old_Expansion(oOrigConn, oTrans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    oLogger.info('Expansion table copied')
    (bOK, aNewMessages) = copy_old_Discipline(oOrigConn, oTrans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    oLogger.info('Discipline table copied')
    (bOK, aNewMessages) = copy_old_Clan(oOrigConn, oTrans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    oLogger.info('Clan table copied')
    (bOK, aNewMessages) = copy_old_Creed(oOrigConn, oTrans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    oLogger.info('Creed table copied')
    (bOK, aNewMessages) = copy_old_Virtue(oOrigConn, oTrans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    oLogger.info('Virtue table copied')
    (bOK, aNewMessages) = copy_old_CardType(oOrigConn, oTrans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    oLogger.info('CardType table copied')
    (bOK, aNewMessages) = copy_old_Ruling(oOrigConn, oTrans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    oLogger.info('Ruling table copied')
    (bOK, aNewMessages) = copy_old_DisciplinePair(oOrigConn, oTrans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    oLogger.info('DisciplinePair table copied')
    (bOK, aNewMessages) = copy_old_RarityPair(oOrigConn, oTrans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    oLogger.info('RarityPair table copied')
    (bOK, aNewMessages) = copy_old_Sect(oOrigConn, oTrans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    oLogger.info('Sect table copied')
    (bOK, aNewMessages) = copy_old_Title(oOrigConn, oTrans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    oLogger.info('Title table copied')
    (bOK, aNewMessages) = copy_old_AbstractCard(oOrigConn, oTrans, oLogger)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK, aNewMessages) = copy_old_PhysicalCard(oOrigConn, oTrans, oLogger)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK, aNewMessages) = copy_old_PhysicalCardSet(oOrigConn, oTrans, oLogger)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK, aNewMessages) = copy_old_AbstractCardSet(oOrigConn, oTrans, oLogger)
    bRes = bRes and bOK
    aMessages += aNewMessages
    oTrans.commit()
    return (bRes, aMessages)

def copy_database(oOrigConn, oDestConnn, oLogHandler=None):
    # This is a straight copy, with no provision for funky stuff
    # Compataibility of database structures is assumed, but not checked
    # (probably should be fixed)
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
    # Todo: More error checking
    copy_Rarity(oOrigConn, oTrans)
    oLogger.info('Rarity table copied')
    copy_Expansion(oOrigConn, oTrans)
    oLogger.info('Expansion table copied')
    copy_Discipline(oOrigConn, oTrans)
    oLogger.info('Discipline table copied')
    copy_Clan(oOrigConn, oTrans)
    oLogger.info('Clan table copied')
    copy_Creed(oOrigConn, oTrans)
    oLogger.info('Creed table copied')
    copy_Virtue(oOrigConn, oTrans)
    oLogger.info('Virtue table copied')
    copy_CardType(oOrigConn, oTrans)
    oLogger.info('CardType table copied')
    copy_Ruling(oOrigConn, oTrans)
    oLogger.info('Ruling table copied')
    copy_DisciplinePair(oOrigConn, oTrans)
    oLogger.info('DisciplinePair table copied')
    copy_RarityPair(oOrigConn, oTrans)
    oLogger.info('RarityPair table copied')
    copy_Sect(oOrigConn, oTrans)
    oLogger.info('Sect table copied')
    copy_Title(oOrigConn, oTrans)
    oLogger.info('Title table copied')
    oTrans.commit()
    oTrans.cache.clear()
    copy_AbstractCard(oOrigConn, oTrans, oLogger)
    oTrans.commit()
    oTrans.cache.clear()
    oTrans = oDestConnn.transaction()
    copy_PhysicalCard(oOrigConn, oTrans, oLogger)
    oTrans.commit()
    oTrans.cache.clear()
    # Copy Physical card sets
    copy_PhysicalCardSet(oOrigConn, oTrans, oLogger)
    oTrans.commit()
    oTrans.cache.clear()
    copy_AbstractCardSet(oOrigConn, oTrans, oLogger)
    oTrans.commit()
    return (bRes, aMessages)

def copy_to_new_AbstractCardDB(oOrigConn, oNewConn, oCardLookup, oLogHandler=None):
    # Given an existing database, and a new database created from
    # a new cardlist, copy the PhysicalCards and the CardSets,
    # going via CardSetHolders, so we can adapt to changed names, etc.
    bRes = True
    aMessages = []
    aPhysCardSets = []
    aAbsCardSets = []
    oOldConn = sqlhub.processConnection
    # Copy the physical card list
    oPhysListCS = CachedCardSetHolder()
    oLogger = Logger('copy to new abstract card DB')
    if oLogHandler:
        oLogger.addHandler(oLogHandler)
        if hasattr(oLogHandler, 'set_total'):
            iTotal = 2 + PhysicalCardSet.select(connection=oOrigConn).count() + \
                    AbstractCardSet.select(connection=oOrigConn).count()
            oLogHandler.set_total(iTotal)
    for oCard in PhysicalCard.select(connection=oOrigConn):
        oPhysListCS.add(1, oCard.abstractCard.canonicalName, oCard.expansion)
    # Copy Physical card sets
    # FIXME: Manual mappings of physical cards to the individual card sets
    # will be lost in this process.
    for oSet in PhysicalCardSet.select(connection=oOrigConn):
        oCS = CachedCardSetHolder()
        oCS.name = oSet.name
        oCS.author = oSet.author
        oCS.comment = oSet.comment
        oCS.annotations = oSet.annotations
        oCS.inuse = oSet.inuse
        for oCard in oSet.cards:
            oCS.add(1, oCard.abstractCard.canonicalName, oCard.expansion)
        aPhysCardSets.append(oCS)
    # Copy AbstractCardSets
    for oSet in AbstractCardSet.select(connection=oOrigConn):
        oCS = CachedCardSetHolder()
        oCS.name = oSet.name
        oCS.author = oSet.author
        oCS.comment = oSet.comment
        oCS.annotations = oSet.annotations
        for oCard in oSet.cards:
            oCS.add(1, oCard.canonicalName)
        aAbsCardSets.append(oCS)
    oLogger.info('Memory copies made')
    oTarget = oNewConn.transaction()
    sqlhub.processConnection = oTarget
    # Create the cardsets from the holders
    dLookupCache = oPhysListCS.createPhysicalCardList(oCardLookup)
    oLogger.info('Physical Card list copied')
    for oSet in aAbsCardSets:
        oSet.createACS(oCardLookup, dLookupCache)
        oLogger.info('Abstract Card Set: %s', oSet.name)
    for oSet in aPhysCardSets:
        oSet.createPCS(oCardLookup, dLookupCache)
        oLogger.info('Physical Card Set: %s', oSet.name)
    oTarget.commit()
    sqlhub.processConnection = oOldConn
    return (bRes, aMessages)

def create_memory_copy(oTempConn, oLogHandler=None):
    # We create a temporary memory database, and create the updated
    # database in it. readOldDB is responsbile for upgrading stuff
    # as needed
    if refresh_tables(ObjectList, oTempConn):
        return read_old_database(sqlhub.processConnection, oTempConn, oLogHandler)
    else:
        return (False, ["Unable to create tables"])

def create_final_copy(oTempConn, oLogHandler=None):
    # Copy from the memory database to the real thing
    if refresh_tables(ObjectList, sqlhub.processConnection):
        return copy_database(oTempConn, sqlhub.processConnection, oLogHandler)
    else:
        return (False, ["Unable to create tables"])

def attempt_database_upgrade(oLogHandler=None):
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
