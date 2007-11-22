# DatabaseUpgrade.py
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

from sqlobject import sqlhub, SQLObject, IntCol, UnicodeCol, RelatedJoin, \
        EnumCol, MultipleJoin, connectionForURI, ForeignKey
from sutekh.core.SutekhObjects import PhysicalCard, AbstractCard, AbstractCardSet, \
        PhysicalCardSet, Expansion, Clan, Virtue, Discipline, Rarity, \
        RarityPair, CardType, Ruling, ObjectList, DisciplinePair, Creed, \
        Sect, Title, FlushCache
from sutekh.core.CardSetHolder import CachedCardSetHolder
from sutekh.SutekhUtility import refreshTables
from sutekh.core.DatabaseVersion import DatabaseVersion
from sutekh.core.Abbreviations import Rarities

# This file handles all the grunt work of the database upgrades. We have some
# (arguablely overly) complex trickery to read old databases, and we create a
# copy in sqlite memory database first, before commiting to the actual DB

# Utility Exceptions

class UnknownVersion(Exception):
    def __init__(self, TableName):
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
    cards = RelatedJoin('PhysicalCard', intermediateTable='physical_map', createRelatedTable=False)

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
    costtype = EnumCol(enumValues=['pool', 'blood', 'conviction', None], default=None)
    level = EnumCol(enumValues=['advanced', None], default=None)
    discipline = RelatedJoin('DisciplinePair', intermediateTable='abs_discipline_pair_map', createRelatedTable=False)
    rarity = RelatedJoin('RarityPair', intermediateTable='abs_rarity_pair_map', createRelatedTable=False)
    clan = RelatedJoin('Clan', intermediateTable='abs_clan_map', createRelatedTable=False)
    cardtype = RelatedJoin('CardType', intermediateTable='abs_type_map', createRelatedTable=False)
    sect = RelatedJoin('Sect', intermediateTable='abs_sect_map', createRelatedTable=False)
    title = RelatedJoin('Title', intermediateTable='abs_title_map', createRelatedTable=False)
    creed = RelatedJoin('Creed', intermediateTable='abs_creed_map', createRelatedTable=False)
    virtue = RelatedJoin('Virtue', intermediateTable='abs_virtue_map', createRelatedTable=False)
    rulings = RelatedJoin('Ruling', intermediateTable='abs_ruling_map', createRelatedTable=False)
    sets = RelatedJoin('AbstractCardSet', intermediateTable='abstract_map', createRelatedTable=False)
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
    cards = RelatedJoin('AbstractCard_v2',intermediateTable='abs_rarity_pair_map',createRelatedTable=False)

class AbstractCardSet_ACv2(SQLObject):
    class sqlmeta:
        table = AbstractCardSet.sqlmeta.table

    name = UnicodeCol(alternateID=True, length=50)
    author = UnicodeCol(length=50, default='')
    comment = UnicodeCol(default='')
    annotations = UnicodeCol(default='')
    # Provides a join to AbstractCard_v2, needed to read old DB
    cards = RelatedJoin('AbstractCard_v2', intermediateTable='abstract_map', createRelatedTable=False)

def check_can_read_old_DB(orig_conn):
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

def copy_Rarity(orig_conn, trans):
    """
    Copy rarity tables, assumings same version
    """
    for oObj in Rarity.select(connection=orig_conn):
        oCopy = Rarity(id=oObj.id, name=oObj.name,
                shortname=oObj.shortname, connection=trans)

def copy_old_Rarity(orig_conn, trans):
    """
    Copy rarity table, upgrading versions as needed
    """
    oVer = DatabaseVersion()
    if oVer.checkVersions([Rarity], [Rarity.tableversion]):
        copy_Rarity(orig_conn, trans)
    elif oVer.checkVersions([Rarity], [1]):
        for oObj in Rarity_v1.select(connection=orig_conn):
            oCopy = Rarity(id=oObj.id, name=oObj.name,
                    shortname=Rarities.shortname(oObj.name),
                    connection=trans)
    else:
        return (False, ["Unknown Version for Rarity"])
    return (True, [])

def copy_Expansion(orig_conn, trans):
    """
    Copy expansion, assuming versions match
    """
    for oObj in Expansion.select(connection=orig_conn):
        oCopy = Expansion(id=oObj.id, name=oObj.name,
                shortname=oObj.shortname, connection=trans)

def copy_old_Expansion(orig_conn, trans):
    """
    Copy Expansion, updating as needed
    """
    oVer = DatabaseVersion()
    if oVer.checkVersions([Expansion], [Expansion.tableversion]):
        copy_Expansion(orig_conn, trans)
    else:
        return (False, ["Unknown Expansion Version"])
    return (True, [])

def copy_Discipline(orig_conn, trans):
    """
    Copy Discipline, assuming versions match
    """
    for oObj in Discipline.select(connection=orig_conn):
        oCopy = Discipline(id=oObj.id, name=oObj.name,
            fullname=oObj.fullname, connection=trans)

def copy_old_Discipline(orig_conn, trans):
    oVer = DatabaseVersion()
    if oVer.checkVersions([Discipline], [Discipline.tableversion]):
        copy_Discipline(orig_conn, trans)
    else:
        return (False, ["Unknown Discipline version"])
    return (True, [])

def copy_Clan(orig_conn, trans):
    """
    Copy Clan, assuming database versions match
    """
    for oObj in Clan.select(connection=orig_conn):
        oCopy = Clan(id=oObj.id, name=oObj.name, connection=trans)

def copy_old_Clan(orig_conn, trans):
    oVer = DatabaseVersion()
    if oVer.checkVersions([Clan], [Clan.tableversion]):
        copy_Clan(orig_conn, trans)
    else:
        return (False, ["Unknown Clan Version"])
    return (True, [])

def copy_Creed(orig_conn, trans):
    """
    Copy Creed, assuming versions match
    """
    for oObj in Creed.select(connection=orig_conn):
        oCopy = Creed(id=oObj.id, name=oObj.name, shortname=oObj.shortname,
                connection=trans)

def copy_old_Creed(orig_conn, trans):
    """
    Copy Creed, updating if needed
    """
    oVer = DatabaseVersion()
    if oVer.checkVersions([Creed], [Creed.tableversion]):
        copy_Creed(orig_conn, trans)
    else:
        return (False, ["Unknown Creed Version"])
    return (True, [])

def copy_Virtue(orig_conn, trans):
    """
    Copy Virtue, assuming versions match
    """
    for oObj in Virtue.select(connection=orig_conn):
        oCopy = Virtue(id=oObj.id, name=oObj.name, fullname=oObj.fullname,
                connection=trans)

def copy_old_Virtue(orig_conn, trans):
    """
    Copy Virtue, updating if needed
    """
    oVer = DatabaseVersion()
    if oVer.checkVersions([Virtue], [Virtue.tableversion]):
        copy_Virtue(orig_conn, trans)
    else:
        return (False, ["Unknown Virtue Version"])
    return (True, [])

def copy_CardType(orig_conn, trans):
    """
    Copy CardType, assuming versions match
    """
    for oObj in CardType.select(connection=orig_conn):
        oCopy = CardType(id=oObj.id, name=oObj.name, connection=trans)

def copy_old_CardType(orig_conn, trans):
    """
    Copy CardType, upgrading as needed
    """
    oVer = DatabaseVersion()
    if oVer.checkVersions([CardType], [CardType.tableversion]):
        copy_CardType(orig_conn, trans)
    else:
        return (False, ["Unknown CardType Version"])
    return (True, [])

def copy_Ruling(orig_conn, trans):
    """
    Copy Ruling, assuming versions match
    """
    for oObj in Ruling.select(connection=orig_conn):
        oCopy = Ruling(id=oObj.id, text=oObj.text, code=oObj.code, url=oObj.url,
                connection=trans)

def copy_old_Ruling(orig_conn, trans):
    """
    Copy Ruling, upgrading as needed
    """
    oVer = DatabaseVersion()
    if oVer.checkVersions([CardType], [CardType.tableversion]):
        copy_Ruling(orig_conn, trans)
    else:
        return (False, ["Unknown Ruling Version"])
    return (True, [])

def copy_DisciplinePair(orig_conn, trans):
    """
    Copy DisciplinePair, assuming versions match
    """
    for oObj in DisciplinePair.select(connection=orig_conn):
        oCopy = DisciplinePair(id=oObj.id, level=oObj.level,
               discipline=oObj.discipline, connection=trans)

def copy_old_DisciplinePair(orig_conn, trans):
    oVer = DatabaseVersion()
    if oVer.checkVersions([DisciplinePair], [DisciplinePair.tableversion]):
        copy_DisciplinePair(orig_conn, trans)
    else:
        return (False, ["Unknown Discipline Version"])
    return (True, [])

def copy_RarityPair(orig_conn, trans):
    """
    Copy RairtyPair, assuming versions match
    """
    for oObj in RarityPair.select(connection=orig_conn):
        oCopy = RarityPair(id=oObj.id, expansion=oObj.expansion,
                rarity=oObj.rarity, connection=trans)

def copy_old_RarityPair(orig_conn, trans):
    """
    Copy RarityPair, upgrading as needed
    """
    oVer = DatabaseVersion()
    if oVer.checkVersions([RarityPair], [RarityPair.tableversion]) and \
            oVer.checkVersions([Rarity], [Rarity.tableversion]):
        copy_RarityPair(orig_conn, trans)
    elif oVer.checkVersions([RarityPair], [RarityPair.tableversion]) and \
            oVer.checkVersions([Rarity], [1]):
        for oObj in RarityPair_Rv1.select(connection=orig_conn):
            oCopy = RarityPair(id=oObj.id, expansion=oObj.expansion,
                    rarity=oObj.rarity, connection=trans)
    else:
        return (False, ["Unknown RarityPair version"])
    return (True, [])

def copy_Sect(orig_conn, trans):
    """
    Copy Sect, assuming versions match
    """
    for oObj in Sect.select(connection=orig_conn):
        oCopy = Sect(id=oObj.id, name=oObj.name, connection=trans)

def copy_old_Sect(orig_conn, trans):
    """
    Copy Sect, updating if needed
    """
    oVer = DatabaseVersion()
    if oVer.checkVersions([Sect], [Sect.tableversion]):
        copy_Sect(orig_conn, trans)
    else:
        return (False, ["Unknown Sect Version"])
    return (True, [])

def copy_Title(orig_conn, trans):
    """
    Copy Title, assuming versions match
    """
    for oObj in Title.select(connection=orig_conn):
        oCopy = Title(id=oObj.id, name=oObj.name, connection=trans)

def copy_old_Title(orig_conn, trans):
    """
    Copy Title, updating if needed
    """
    oVer = DatabaseVersion()
    if oVer.checkVersions([Title], [Title.tableversion]):
        copy_Title(orig_conn, trans)
    else:
        return (False, ["Unknown Title Version"])
    return (True, [])

def copy_AbstractCard(orig_conn, trans):
    """
    Copy AbstractCard, assuming versions match
    """
    for oCard in AbstractCard.select(connection=orig_conn):
        oCardCopy = AbstractCard(id=oCard.id, canonicalName=oCard.canonicalName,
                name=oCard.name, text=oCard.text, connection=trans)
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

def copy_old_AbstractCard(orig_conn, trans):
    """
    Copy AbstractCard, upgrading as needed
    """
    oVer = DatabaseVersion()
    aMessages = []
    if oVer.checkVersions([AbstractCard], [AbstractCard.tableversion]):
        copy_AbstractCard(orig_conn, trans)
    elif oVer.checkVersions([AbstractCard], [2]):
        aMessages.append('Missing data for the Burn Option on cards. You will need to reimport the White wolf card list for these to be correct')
        for oCard in AbstractCard_v2.select(connection=orig_conn):
            oCardCopy = AbstractCard(id=oCard.id, canonicalName=oCard.canonicalName,
                    name=oCard.name, text=oCard.text, connection=trans)
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
    else:
        return (False, ["Unknown AbstractCard version"])
    return (True, aMessages)

def copy_PhysicalCard(orig_conn, trans):
    """
    Copy PhysicalCard, assuming version match
    """
    # We copy abstractCardID rather than abstractCard, to avoid issues
    # with abstract card class changes
    for oCard in PhysicalCard.select(connection=orig_conn):
        oCardCopy = PhysicalCard(id=oCard.id, abstractCardID=oCard.abstractCardID,
                expansionID=oCard.expansionID, connection=trans)

def copy_old_PhysicalCard(orig_conn, trans):
    oVer = DatabaseVersion()
    if oVer.checkVersions([PhysicalCard], [PhysicalCard.tableversion]):
        copy_PhysicalCard(orig_conn, trans)
    else:
        return (False, ["Unknown PhysicalCard version"])
    return (True, [])

def copy_PhysicalCardSet(orig_conn, trans):
    """
    Copy PCS, assuming versions match
    """
    for oSet in PhysicalCardSet.select(connection=orig_conn):
        oCopy = PhysicalCardSet(id=oSet.id, name=oSet.name,
                author=oSet.author, comment=oSet.comment,
                annotations=oSet.annotations, inuse=oSet.inuse,
                connection=trans)
        for oCard in oSet.cards:
            oCopy.addPhysicalCard(oCard.id)
        oCopy.syncUpdate()

def copy_old_PhysicalCardSet(orig_conn, trans):
    """
    Copy PCS, upgrading as needed
    """
    oVer = DatabaseVersion()
    if oVer.checkVersions([PhysicalCardSet], [PhysicalCardSet.tableversion]) \
            and oVer.checkVersions([PhysicalCard], [PhysicalCard.tableversion]):
        copy_PhysicalCardSet(orig_conn, trans)
    elif oVer.checkVersions([PhysicalCardSet], [3]):
        for oSet in PhysicalCardSet_v3.select(connection=orig_conn):
            oCopy = PhysicalCardSet(id=oSet.id, name=oSet.name,
                    author=oSet.author, comment=oSet.comment,
                    annotations=None, inuse=False,
                    connection=trans)
            for oCard in oSet.cards:
                oCopy.addPhysicalCard(oCard.id)
            oCopy.syncUpdate()
    else:
        return (False, ["Unknown PhysicalCardSet version"])
    return (True, [])

def copy_AbstractCardSet(orig_conn, trans):
    """
    Copy AbstractCardSet, assuming versions match
    """
    for oSet in AbstractCardSet.select(connection=orig_conn):
        oCopy = AbstractCardSet(id=oSet.id, name=oSet.name,
                author=oSet.author, comment=oSet.comment,
                annotations=oSet.annotations, connection=trans)
        for oCard in oSet.cards:
            oCopy.addAbstractCard(oCard.id)
        oCopy.syncUpdate()

def copy_old_AbstractCardSet(orig_conn, trans):
    oVer = DatabaseVersion()
    if oVer.checkVersions([AbstractCardSet], [AbstractCardSet.tableversion]) \
            and oVer.checkVersions([AbstractCard], [AbstractCard.tableversion]):
        copy_AbstractCardSet(orig_conn, trans)
    elif oVer.checkVersions([AbstractCard], [2]):
        # Upgrade from previous AbstractCard class
        for oSet in AbstractCardSet_ACv2.select(connection=orig_conn):
            oCopy = AbstractCardSet(id=oSet.id, name=oSet.name,
                    author=oSet.author, comment=oSet.comment,
                    annotations=oSet.annotations, connection=trans)
            for oCard in oSet.cards:
                oCopy.addAbstractCard(oCard.id)
            oCopy.syncUpdate()
    else:
        return (False, ["Unknown AbstractCardSet version"])
    return (True, [])

def readOldDB(orig_conn, dest_conn):
    """Read the old database into new database, filling in
       blanks when needed"""
    try:
        if not check_can_read_old_DB(orig_conn):
            return False
    except UnknownVersion, err:
        raise err
    # OK, version checks pass, so we should be able to deal with this
    aMessages = []
    bRes = True
    trans = dest_conn.transaction()
    # Magic happens in the individual functions, as needed
    (bOK, aNewMessages) = copy_old_Rarity(orig_conn, trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK, aMessages) = copy_old_Expansion(orig_conn, trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK, aNewMessages) = copy_old_Discipline(orig_conn, trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK, aNewMessages) = copy_old_Clan(orig_conn, trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK, aNewMessages) = copy_old_Creed(orig_conn, trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK, aNewMessages) = copy_old_Virtue(orig_conn, trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK, aNewMessages) = copy_old_CardType(orig_conn, trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK, aNewMessages) = copy_old_Ruling(orig_conn, trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK, aNewMessages) = copy_old_DisciplinePair(orig_conn, trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK, aNewMessages) = copy_old_RarityPair(orig_conn, trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK, aNewMessages) = copy_old_Sect(orig_conn, trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK, aNewMessages) = copy_old_Title(orig_conn, trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK, aNewMessages) = copy_old_AbstractCard(orig_conn, trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK, aNewMessages) = copy_old_PhysicalCard(orig_conn, trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK, aNewMessages) = copy_old_PhysicalCardSet(orig_conn, trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK, aNewMessages) = copy_old_AbstractCardSet(orig_conn, trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    trans.commit()
    return (bRes, aMessages)

def copyDB(orig_conn, dest_conn):
    # This is a straight copy, with no provision for funky stuff
    # Compataibility of database structures is assumed, but not checked
    # (probably should be fixed)
    # Copy tables needed before we can copy AbstractCard
    bRes = True
    aMessages = []
    trans = dest_conn.transaction()
    # Todo: More error checking
    copy_Rarity(orig_conn, trans)
    copy_Expansion(orig_conn, trans)
    copy_Discipline(orig_conn, trans)
    copy_Clan(orig_conn, trans)
    copy_Creed(orig_conn, trans)
    copy_Virtue(orig_conn, trans)
    copy_CardType(orig_conn, trans)
    copy_Ruling(orig_conn, trans)
    copy_DisciplinePair(orig_conn, trans)
    copy_RarityPair(orig_conn, trans)
    copy_Sect(orig_conn, trans)
    copy_Title(orig_conn, trans)
    trans.commit()
    trans = dest_conn.transaction()
    copy_AbstractCard(orig_conn, trans)
    trans.commit()
    trans = dest_conn.transaction()
    copy_PhysicalCard(orig_conn, trans)
    trans.commit()
    trans = dest_conn.transaction()
    # Copy Physical card sets
    copy_PhysicalCardSet(orig_conn, trans)
    trans.commit()
    trans = dest_conn.transaction()
    copy_AbstractCardSet(orig_conn, trans)
    trans.commit()
    return (bRes, aMessages)

def copyToNewAbstractCardDB(orig_conn, new_conn, oCardLookup):
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
    for oCard in PhysicalCard.select(connection=orig_conn):
        oPhysListCS.add(1, oCard.abstractCard.canonicalName, oCard.expansion)
    # Copy Physical card sets
    # FIXME: Manual mappings of physical cards to the individual card sets
    # will be lost in this process. 
    for oSet in PhysicalCardSet.select(connection=orig_conn):
        oCS = CachedCardSetHolder()
        oCS.name = oSet.name
        oCS.author = oSet.author
        oCS.comment = oSet.comment
        oCS.annotations = oSet.annotations
        for oCard in oSet.cards:
            oCS.add(1, oCard.abstractCard.canonicalName, oCard.expansion)
        aPhysCardSets.append(oCS)
    # Copy AbstractCardSets
    for oSet in AbstractCardSet.select(connection=orig_conn):
        oCS = CachedCardSetHolder()
        oCS.name = oSet.name
        oCS.author = oSet.author
        oCS.comment = oSet.comment
        oCS.annotations = oSet.annotations
        for oCard in oSet.cards:
            oCS.add(1, oCard.canonicalName)
        aAbsCardSets.append(oCS)
    oTarget = new_conn.transaction()
    sqlhub.processConnection = oTarget
    # Create the cardsets from the holders
    dLookupCache = oPhysListCS.createPhysicalCardList(oCardLookup)
    for oSet in aAbsCardSets:
        oSet.createACS(oCardLookup, dLookupCache)
    for oSet in aPhysCardSets:
        oSet.createPCS(oCardLookup, dLookupCache)
    oTarget.commit()
    sqlhub.processConnection = oOldConn
    return (bRes, aMessages)

def createMemoryCopy(tempConn):
    # We create a temporary memory database, and create the updated
    # database in it. readOldDB is responsbile for upgrading stuff
    # as needed
    FlushCache()
    if refreshTables(ObjectList, tempConn):
        return readOldDB (sqlhub.processConnection, tempConn)
    else:
        return (False, ["Unable to create tables"])

def createFinalCopy(tempConn):
    FlushCache()
    # Copy from the memory database to the real thing
    if refreshTables(ObjectList, sqlhub.processConnection):
        return copyDB(tempConn, sqlhub.processConnection)
    else:
        return (False, ["Unable to create tables"])

def attemptDatabaseUpgrade():
    tempConn = connectionForURI("sqlite:///:memory:")
    (bOK, aMessages) = createMemoryCopy(tempConn)
    if bOK:
        print "Copied database to memory, performing upgrade."
        if len(aMessages) > 0:
            print "Messages reported", aMessages
        (bOK, aMessages) = createFinalCopy(tempConn)
        if bOK:
            print "Everything seems to have gone OK"
            if len(aMessages) > 0:
                print "Messages reported", aMessages
            return True
        else:
            print "Unable to perform upgrade."
            if len(aMessages) > 0:
                print "Errors reported", aMessages
            print "!!YOUR DATABASE MAY BE CORRUPTED!!"
            return False
    else:
        print "Unable to create memory copy. Database not upgraded."
        if len(aMessages) > 0:
            print "Errors reported", aMessages
        return False
