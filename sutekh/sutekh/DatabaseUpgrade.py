# DatabaseUpgrade.py
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

from sqlobject import *
from SutekhObjects import *
from SutekhUtility import *
from DatabaseVersion import DatabaseVersion

# This file handles all the grunt work of the database upgrades. We have some
# (arguablely overly) complex trickery to read old databases, and we create a
# copy in sqlite memory database first, before commiting to the actual DB


# Utility Exceptions

class unknownVersion(Exception):
    def __init__(self,TableName):
        self.sTableName=TableName
    def __str__(self):
        return "Unrecognised version for "+self.sTableName

# We clone the SQLObject classes in SutekhObjects so we can read
# old versions

class AbstractCardSet_v1(SQLObject):
    class sqlmeta:
        table=AbstractCardSet.sqlmeta.table

    advise(instancesProvide=[IAbstractCardSet])
    name = UnicodeCol(alternateID=True,length=50)
    cards = RelatedJoin('AbstractCard',intermediateTable='abstract_map',createRelatedTable=False)

class PhysicalCardSet_v1(SQLObject):
    class sqlmeta:
        table=PhysicalCardSet.sqlmeta.table
    advise(instancesProvide=[IPhysicalCardSet])

    name = UnicodeCol(alternateID=True,length=50)
    cards = RelatedJoin('PhysicalCard',intermediateTable='physical_map',createRelatedTable=False)


def checkCanReadOldDB(orig_conn):
    """Can we upgrade from this database version?"""
    oVer=DatabaseVersion()
    if not oVer.checkVersions([Rarity],[Rarity.tableversion]) and \
           not oVer.checkVersions([Rarity],[-1]):
        raise unknownVersion("Rarity")
    if not oVer.checkVersions([Expansion],[Expansion.tableversion]) and \
            not oVer.checkVersions([Expansion],[-1]):
        raise unknownVersion("Expansion")
    if not oVer.checkVersions([Discipline],[Discipline.tableversion]) and \
           not oVer.checkVersions([Discipline],[-1]):
        raise unknownVersion("Discipline")
    if not oVer.checkVersions([Clan],[Clan.tableversion]) and \
           not oVer.checkVersions([Clan],[-1]):
        raise unknownVersion("Clan")
    if not oVer.checkVersions([CardType],[CardType.tableversion]) and \
           not oVer.checkVersions([CardType],[-1]):
        raise unknownVersion("CardType")
    if not oVer.checkVersions([Ruling],[Ruling.tableversion]) and \
           not oVer.checkVersions([Ruling],[-1]):
        raise unknownVersion("Ruling")
    if not oVer.checkVersions([DisciplinePair],[DisciplinePair.tableversion]) and \
           not oVer.checkVersions([DisciplinePair],[-1]):
        raise unknownVersion("DisciplinePair")
    if not oVer.checkVersions([RarityPair],[RarityPair.tableversion]) and \
           not oVer.checkVersions([RarityPair],[-1]):
        raise unknownVersion("RarityPair")
    if not oVer.checkVersions([AbstractCard],[AbstractCard.tableversion]) and \
           not oVer.checkVersions([AbstractCard],[-1]):
        raise unknownVersion("AbstractCard")
    if not oVer.checkVersions([PhysicalCard],[PhysicalCard.tableversion]) and \
           not oVer.checkVersions([PhysicalCard],[-1]):
        raise unknownVersion("PhysicalCard")
    if not oVer.checkVersions([PhysicalCardSet],[PhysicalCardSet.tableversion]) and \
           not oVer.checkVersions([PhysicalCardSet],[1]) and \
           not oVer.checkVersions([PhysicalCardSet],[-1]):
        raise unknownVersion("PhysicalCardSet")
    if not oVer.checkVersions([AbstractCardSet],[AbstractCardSet.tableversion]) and \
           not oVer.checkVersions([AbstractCardSet],[1]) and \
           not oVer.checkVersions([AbstractCardSet],[-1]):
        raise unknownVersion("AbstractCardSet")
    return True

def CopyOldRarity(orig_conn,trans):
    for oObj in Rarity.select(connection=orig_conn):
        oCopy=Rarity(id=oObj.id,name=oObj.name,connection=trans)

def CopyOldExpansion(orig_conn,trans):
    for oObj in Expansion.select(connection=orig_conn):
        oCopy=Expansion(id=oObj.id,name=oObj.name,connection=trans)

def CopyOldDiscipline(orig_conn,trans):
    for oObj in Discipline.select(connection=orig_conn):
        oCopy=Discipline(id=oObj.id,name=oObj.name,connection=trans)

def CopyOldClan(orig_conn,trans):
    for oObj in Clan.select(connection=orig_conn):
        oCopy=Clan(id=oObj.id,name=oObj.name,connection=trans)

def CopyOldCardType(orig_conn,trans):
    for oObj in CardType.select(connection=orig_conn):
        oCopy=CardType(id=oObj.id,name=oObj.name,connection=trans)

def CopyOldRuling(orig_conn,trans):
    for oObj in Ruling.select(connection=orig_conn):
        oCopy=Ruling(id=oObj.id,text=oObj.text,code=oObj.code,url=oObj.url,connection=trans)

def CopyOldDisciplinePair(orig_conn,trans):
    for oObj in DisciplinePair.select(connection=orig_conn):
        oCopy=DisciplinePair(id=oObj.id,level=oObj.level,discipline=oObj.discipline,connection=trans)

def CopyOldRarityPair(orig_conn,trans):
    for oObj in RarityPair.select(connection=orig_conn):
        oCopy=RarityPair(id=oObj.id,expansion=oObj.expansion,rarity=oObj.rarity,\
                connection=trans)

def CopyOldAbstractCard(orig_conn,trans):
    for oCard in AbstractCard.select(connection=orig_conn):
        oCardCopy=AbstractCard(id=oCard.id,name=oCard.name,text=oCard.text,connection=trans)
        # If I don't do things this way, I get encoding issues
        # I don't really feel like trying to understand why
        oCardCopy.group=oCard.group
        oCardCopy.capacity=oCard.capacity
        oCardCopy.cost=oCard.cost
        oCardCopy.costtype=oCard.costtype
        oCardCopy.level=oCard.level
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
        oCardCopy.syncUpdate()

def CopyOldPhysicalCard(orig_conn,trans):
    for oCard in PhysicalCard.select(connection=orig_conn):
        oCardCopy=PhysicalCard(id=oCard.id,abstractCard=oCard.abstractCard,connection=trans)

def CopyOldPhysicalCardSet(orig_conn,trans):
    oVer=DatabaseVersion()
    if oVer.checkVersions([PhysicalCardSet],[PhysicalCardSet.tableversion]):
        for oSet in PhysicalCardSet.select(connection=orig_conn):
            oCopy=PhysicalCardSet(id=oSet.id,name=oSet.name,\
                    author=oSet.author,comment=oSet.comment,\
                    connection=trans)
            for oCard in oSet.cards:
                oCopy.addPhysicalCard(oCard.id)
            oCopy.syncUpdate()
    elif oVer.checkVersions([PhysicalCardSet],[1]) or \
           oVer.checkVersions([PhysicalCardSet],[-1]):
        for oSet in PhysicalCardSet_v1.select(connection=orig_conn):
            oCopy=PhysicalCardSet(id=oSet.id,name=oSet.name,\
                    connection=trans)
            for oCard in oSet.cards:
                oCopy.addPhysicalCard(oCard.id)
            oCopy.syncUpdate()

def CopyOldAbstractCardSet(orig_conn,trans):
    oVer=DatabaseVersion()
    if oVer.checkVersions([AbstractCardSet],[AbstractCardSet.tableversion]):
        for oSet in AbstractCardSet.select(connection=orig_conn):
            oCopy=AbstractCardSet(id=oSet.id,name=oSet.name,\
                    author=oSet.author,comment=oSet.comment,\
                    connection=trans)
            for oCard in oSet.cards:
                oCopy.addAbstractCard(oCard.id)
            oCopy.syncUpdate()
    elif oVer.checkVersions([AbstractCardSet],[1]) or \
           oVer.checkVersions([AbstractCardSet],[-1]):
        for oSet in AbstractCardSet_v1.select(connection=orig_conn):
            oCopy=AbstractCardSet(id=oSet.id,name=oSet.name,\
                    connection=trans)
            for oCard in oSet.cards:
                oCopy.addAbstractCard(oCard.id)
            oCopy.syncUpdate()

def readOldDB(orig_conn,dest_conn):
    """Read the old database into memory table, filling in
       blanks when needed"""
    try:
        if not checkCanReadOldDB(orig_conn):
            return False
    except unknownVersion, err:
        raise err
    # OK, version checks pass, so we should be able to deal with this
    trans=dest_conn.transaction()
    # Magic happens in the individual functions, as needed
    CopyOldRarity(orig_conn,trans)
    CopyOldExpansion(orig_conn,trans)
    CopyOldDiscipline(orig_conn,trans)
    CopyOldClan(orig_conn,trans)
    CopyOldCardType(orig_conn,trans)
    CopyOldRuling(orig_conn,trans)
    CopyOldDisciplinePair(orig_conn,trans)
    CopyOldRarityPair(orig_conn,trans)
    CopyOldAbstractCard(orig_conn,trans)
    CopyOldPhysicalCard(orig_conn,trans)
    CopyOldPhysicalCardSet(orig_conn,trans)
    CopyOldAbstractCardSet(orig_conn,trans)
    trans.commit()
    return True

def copyDB(orig_conn,dest_conn):
    # This is a straight copy, with no provision for funky stuff
    # Compataibility of database structures is assumed, but not checked
    # (probably should be fixed)
    # Copy tables needed before we can copy AbstractCard
    trans=dest_conn.transaction()
    # Todo: More error checking
    for oObj in Rarity.select(connection=orig_conn):
        oCopy=Rarity(id=oObj.id,name=oObj.name,connection=trans)
    for oObj in Expansion.select(connection=orig_conn):
        oCopy=Expansion(id=oObj.id,name=oObj.name,connection=trans)
    for oObj in Discipline.select(connection=orig_conn):
        oCopy=Discipline(id=oObj.id,name=oObj.name,connection=trans)
    for oObj in Clan.select(connection=orig_conn):
        oCopy=Clan(id=oObj.id,name=oObj.name,connection=trans)
    for oObj in CardType.select(connection=orig_conn):
        oCopy=CardType(id=oObj.id,name=oObj.name,connection=trans)
    for oObj in Ruling.select(connection=orig_conn):
        oCopy=Ruling(id=oObj.id,text=oObj.text,code=oObj.code,url=oObj.url,connection=trans)
    for oObj in DisciplinePair.select(connection=orig_conn):
        oCopy=DisciplinePair(id=oObj.id,level=oObj.level,discipline=oObj.discipline,connection=trans)
    for oObj in RarityPair.select(connection=orig_conn):
        oCopy=RarityPair(id=oObj.id,expansion=oObj.expansion,rarity=oObj.rarity,\
                connection=trans)
    trans.commit()
    trans=dest_conn.transaction()
    for oCard in AbstractCard.select(connection=orig_conn):
        oCardCopy=AbstractCard(id=oCard.id,name=oCard.name,text=oCard.text,connection=trans)
        oCardCopy.group=oCard.group
        oCardCopy.capacity=oCard.capacity
        oCardCopy.cost=oCard.cost
        oCardCopy.costtype=oCard.costtype
        oCardCopy.level=oCard.level
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
        oCardCopy.syncUpdate()
    trans.commit()
    trans=dest_conn.transaction()
    for oCard in PhysicalCard.select(connection=orig_conn):
        oCardCopy=PhysicalCard(id=oCard.id,abstractCard=oCard.abstractCard,connection=trans)
    trans.commit()
    trans=dest_conn.transaction()
    # Copy Physical card sets
    for oSet in PhysicalCardSet.select(connection=orig_conn):
        oCopy=PhysicalCardSet(id=oSet.id,name=oSet.name,\
                author=oSet.author,comment=oSet.comment,\
                connection=trans)
        for oCard in oSet.cards:
            oCopy.addPhysicalCard(oCard.id)
        oCopy.syncUpdate()
    trans.commit()
    trans=dest_conn.transaction()
    for oSet in AbstractCardSet.select(connection=orig_conn):
        oCopy=AbstractCardSet(id=oSet.id,name=oSet.name,\
                author=oSet.author,comment=oSet.comment,\
                connection=trans)
        for oCard in oSet.cards:
            oCopy.addAbstractCard(oCard.id)
        oCopy.syncUpdate()
    trans.commit()
    return True

def copyToNewAbstractCardDB(orig_conn,new_conn):
    # Given an existing database, and a new database created from
    # a new cardlist, copy the PhysicalCards and the CardSets,
    # adjusting for the possibly changed id's in the AbstractCard Table
    target=new_conn.transaction()
    # Copy the physical card list
    for oCard in PhysicalCard.select(connection=orig_conn):
        sName=oCard.abstractCard.name
        oNewAbsCard=AbstractCard.byName(sName,connection=target)
        oCardCopy=PhysicalCard(id=oCard.id,abstractCard=oNewAbsCard,connection=target)
    # Copy Physical card sets
    # IDs are unchangd, since we preserve Physical Card set ids
    for oSet in PhysicalCardSet.select(connection=orig_conn):
        oCopy=PhysicalCardSet(id=oSet.id,name=oSet.name,\
                author=oSet.author,comment=oSet.comment,\
                connection=target)
        for oCard in oSet.cards:
            oCopy.addPhysicalCard(oCard.id)
        oCopy.syncUpdate() # probably unnessecary
    # Copy AbstractCardSets
    # AbstractCArd is not preserved, so adjust for this
    for oSet in AbstractCardSet.select(connection=orig_conn):
        oCopy=AbstractCardSet(id=oSet.id,name=oSet.name,\
                author=oSet.author,comment=oSet.comment,\
                connection=target)
        for oCard in oSet.cards:
            sName=oCard.name
            oNewAbsCard=AbstractCard.byName(sName,connection=target)
            oCopy.addAbstractCard(oNewAbsCard.id)
        oCopy.syncUpdate()
    target.commit()
    return True

def createMemoryCopy(tempConn):
    # We create a temporary memory database, and create the updated
    # database in it. readOldDB is responsbile for upgrading stuff
    # as needed
    refreshTables(ObjectList,tempConn)
    return readOldDB (sqlhub.processConnection,tempConn)

def createFinalCopy(tempConn):
    # Copy from the memory database to the real thing
    refreshTables(ObjectList,sqlhub.processConnection)
    copyDB(tempConn,sqlhub.processConnection)

def attemptDatabaseUpgrade():
    tempConn=connectionForURI("sqlite:///:memory:")
    if createMemoryCopy(tempConn):
        print "Copied database to memory, performing upgrade"
        createFinalCopy(tempConn)
        return True
    else:
        print "Unable to create memory copy. Database not upgraded"
        return False

