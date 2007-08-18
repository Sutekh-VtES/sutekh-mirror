# DatabaseUpgrade.py
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

from sqlobject import sqlhub, SQLObject, IntCol, UnicodeCol, RelatedJoin, \
                      EnumCol, MultipleJoin, SQLObjectNotFound, ForeignKey, \
                      DatabaseIndex, connectionForURI
from sutekh.SutekhObjects import PhysicalCard, AbstractCard, AbstractCardSet,\
                                 PhysicalCardSet, Expansion, Clan, Virtue, \
                                 Discipline, Rarity, RarityPair, CardType, \
                                 Ruling, ObjectList, DisciplinePair, Creed, \
                                 IVirtue, ISect, ITitle, Sect, Title, \
                                 FlushCache
from sutekh.SutekhUtility import refreshTables
from sutekh.DatabaseVersion import DatabaseVersion
from sutekh.WhiteWolfParser import parseText

# This file handles all the grunt work of the database upgrades. We have some
# (arguablely overly) complex trickery to read old databases, and we create a
# copy in sqlite memory database first, before commiting to the actual DB


# Utility Exceptions

class UnknownVersion(Exception):
    def __init__(self,TableName):
        self.sTableName = TableName
    def __str__(self):
        return "Unrecognised version for "+self.sTableName

# We clone the SQLObject classes in SutekhObjects so we can read
# old versions

class AbstractCardSet_v1(SQLObject):
    class sqlmeta:
        table = AbstractCardSet.sqlmeta.table
    name = UnicodeCol(alternateID=True,length=50)
    cards = RelatedJoin('AbstractCard',intermediateTable='abstract_map',createRelatedTable=False)

class PhysicalCardSet_v1(SQLObject):
    class sqlmeta:
        table = PhysicalCardSet.sqlmeta.table
    name = UnicodeCol(alternateID=True,length=50)
    cards = RelatedJoin('PhysicalCard_v1',intermediateTable='physical_map',createRelatedTable=False)

class AbstractCardSet_v2(SQLObject):
    class sqlmeta:
        table = AbstractCardSet.sqlmeta.table
    name = UnicodeCol(alternateID=True,length=50)
    author = UnicodeCol(length=50,default='')
    comment = UnicodeCol(default='')
    cards = RelatedJoin('AbstractCard_v1',intermediateTable='abstract_map',createRelatedTable=False)

class PhysicalCardSet_v2(SQLObject):
    class sqlmeta:
        table = PhysicalCardSet.sqlmeta.table
    name = UnicodeCol(alternateID=True,length=50)
    author = UnicodeCol(length=50,default='')
    comment = UnicodeCol(default='')
    cards = RelatedJoin('PhysicalCard_v1',intermediateTable='physical_map',createRelatedTable=False)

class AbstractCard_v1(SQLObject):
    class sqlmeta:
        table = AbstractCard.sqlmeta.table

    name = UnicodeCol(alternateID=True,length=50)
    text = UnicodeCol()
    group = IntCol(default=None,dbName='grp')
    capacity = IntCol(default=None)
    cost = IntCol(default=None)
    costtype = EnumCol(enumValues=['pool','blood','conviction',None],default=None)
    level = EnumCol(enumValues=['advanced',None],default=None)
    discipline = RelatedJoin('DisciplinePair_v1',intermediateTable='abs_discipline_pair_map',createRelatedTable=False)
    rarity = RelatedJoin('RarityPair_v1',intermediateTable='abs_rarity_pair_map',createRelatedTable=False)
    clan = RelatedJoin('Clan_v1',intermediateTable='abs_clan_map',createRelatedTable=False)
    cardtype = RelatedJoin('CardType',intermediateTable='abs_type_map',createRelatedTable=False)
    rulings = RelatedJoin('Ruling',intermediateTable='abs_ruling_map',createRelatedTable=False)
    sets = RelatedJoin('AbstractCardSet_v1',intermediateTable='abstract_map',createRelatedTable=False)
    physicalCards = MultipleJoin('PhysicalCard')

class Expansion_v1(SQLObject):
    class sqlmeta:
        table = Expansion.sqlmeta.table
    name = UnicodeCol(alternateID=True,length=20)
    pairs = MultipleJoin('RarityPair')

class Discipline_v1(SQLObject):
    class sqlmeta:
        table = Discipline.sqlmeta.table
    name = UnicodeCol(alternateID=True,length=30)
    pairs = MultipleJoin('DisciplinePair_v1')

class RarityPair_v1(SQLObject):
    class sqlmeta:
        table = RarityPair.sqlmeta.table

    expansion = ForeignKey('Expansion_v1')
    rarity = ForeignKey('Rarity')
    cards = RelatedJoin('AbstractCard',intermediateTable='abs_rarity_pair_map',\
            createRelatedTable=False)

class DisciplinePair_v1(SQLObject):
    class sqlmeta:
        table = DisciplinePair.sqlmeta.table

    discipline = ForeignKey('Discipline_v1')
    level = EnumCol(enumValues=['inferior','superior'])
    cards = RelatedJoin('AbstractCard',intermediateTable='abs_discipline_pair_map',\
            createRelatedTable=False)

class Clan_v1(SQLObject):
    class sqlmeta:
        table = Clan.sqlmeta.table
    name = UnicodeCol(alternateID=True,length=40)
    cards = RelatedJoin('AbstractCard',intermediateTable='abs_clan_map',createRelatedTable=False)

class PhysicalCard_v1(SQLObject):
    class sqlmeta:
        table = PhysicalCard.sqlmeta.table

    abstractCard = ForeignKey('AbstractCard_v1')
    abstractCardIndex = DatabaseIndex(abstractCard)
    sets = RelatedJoin('PhysicalCardSet',intermediateTable='physical_map',createRelatedTable=False)

def checkCanReadOldDB(orig_conn):
    """Can we upgrade from this database version?"""
    oVer = DatabaseVersion()
    if not oVer.checkVersions([Rarity],[Rarity.tableversion]) and \
           not oVer.checkVersions([Rarity],[-1]):
        raise UnknownVersion("Rarity")
    if not oVer.checkVersions([Expansion],[Expansion.tableversion]) and \
            not oVer.checkVersions([Expansion],[1]) and \
            not oVer.checkVersions([Expansion],[-1]):
        raise UnknownVersion("Expansion")
    if not oVer.checkVersions([Discipline],[Discipline.tableversion]) and \
           not oVer.checkVersions([Discipline],[1]) and \
           not oVer.checkVersions([Discipline],[-1]):
        raise UnknownVersion("Discipline")
    if not oVer.checkVersions([Clan],[Clan.tableversion]) and \
           not oVer.checkVersions([Clan],[1]) and \
           not oVer.checkVersions([Clan],[-1]):
        raise UnknownVersion("Clan")
    if not oVer.checkVersions([CardType],[CardType.tableversion]) and \
           not oVer.checkVersions([CardType],[-1]):
        raise UnknownVersion("CardType")
    if not oVer.checkVersions([Ruling],[Ruling.tableversion]) and \
           not oVer.checkVersions([Ruling],[-1]):
        raise UnknownVersion("Ruling")
    if not oVer.checkVersions([DisciplinePair],[DisciplinePair.tableversion]) and \
           not oVer.checkVersions([DisciplinePair],[-1]):
        raise UnknownVersion("DisciplinePair")
    if not oVer.checkVersions([RarityPair],[RarityPair.tableversion]) and \
           not oVer.checkVersions([RarityPair],[-1]):
        raise UnknownVersion("RarityPair")
    if not oVer.checkVersions([AbstractCard],[AbstractCard.tableversion]) and \
           not oVer.checkVersions([AbstractCard],[1]) and \
           not oVer.checkVersions([AbstractCard],[-1]):
        raise UnknownVersion("AbstractCard")
    if not oVer.checkVersions([PhysicalCard],[PhysicalCard.tableversion]) and \
           not oVer.checkVersions([PhysicalCard],[1]) and \
           not oVer.checkVersions([PhysicalCard],[-1]):
        raise UnknownVersion("PhysicalCard")
    if not oVer.checkVersions([PhysicalCardSet],[PhysicalCardSet.tableversion]) and \
           not oVer.checkVersions([PhysicalCardSet],[2]) and \
           not oVer.checkVersions([PhysicalCardSet],[1]) and \
           not oVer.checkVersions([PhysicalCardSet],[-1]):
        raise UnknownVersion("PhysicalCardSet")
    if not oVer.checkVersions([AbstractCardSet],[AbstractCardSet.tableversion]) and \
           not oVer.checkVersions([AbstractCardSet],[2]) and \
           not oVer.checkVersions([AbstractCardSet],[1]) and \
           not oVer.checkVersions([AbstractCardSet],[-1]):
        raise UnknownVersion("AbstractCardSet")
    return True

def CopyOldRarity(orig_conn,trans):
    for oObj in Rarity.select(connection=orig_conn):
        oCopy = Rarity(id=oObj.id,name=oObj.name,connection=trans)
    return (True,[])

def CopyOldExpansion(orig_conn,trans):
    oVer = DatabaseVersion()
    if oVer.checkVersions([Expansion],[Expansion.tableversion]):
        for oObj in Expansion.select(connection=orig_conn):
            oCopy = Expansion(id=oObj.id,name=oObj.name,\
                    shortname=oObj.shortname,connection=trans)
    elif oVer.checkVersions([Expansion],[1]) or \
            oVer.checkVersions([Expansion],[-1]):
        for oObj in Expansion_v1.select(connection=orig_conn):
            # TODO: Fetch Shortname from expansion data in SutekhObjects.
            sShortName=''
            oCopy = Expansion(id=oObj.id,name=oObj.name,shortname=sShortName,connection=trans)
    return (True,[])

def CopyOldDiscipline(orig_conn,trans):
    oVer = DatabaseVersion()
    if oVer.checkVersions([Discipline],[Discipline.tableversion]):
        for oObj in Discipline.select(connection=orig_conn):
            oCopy = Discipline(id=oObj.id,name=oObj.name,fullname=oObj.fullname,
                    connection=trans)
    elif oVer.checkVersions([Discipline],[1]) or \
         oVer.checkVersions([Discipline],[-1]):
        for oObj in Discipline_v1.select(connection=orig_conn):
            if oObj.name[:2]=='v_':
                #point adaptor at new database
                oldconn=sqlhub.processConnection
                sqlhub.processConnection=trans
                oVirtue=IVirtue(oObj.name[2:])
                sqlhub.processConnection=oldconn
                # Let adaptor create entry for us
            else:
                sFullName=''
                # Not using adaptor creation as I want to preserve ID
                # FIXME: Get the actual fullname from the data.
                # Maybe tweak DisciplinePair copy not to rely on ID's?
                oCopy = Discipline(id=oObj.id,name=oObj.name,fullname=sFullName,
                        connection=trans)
    return (True,[])

def CopyOldClan(orig_conn,trans):
    oVer = DatabaseVersion()
    if oVer.checkVersions([Clan],[Clan.tableversion]):
        for oObj in Clan.select(connection=orig_conn):
            oCopy = Clan(id=oObj.id,name=oObj.name,connection=trans)
    elif oVer.checkVersions([Clan],[1]) or \
         oVer.checkVersions([Clan],[-1]):
        for oObj in Clan_v1.select(connection=orig_conn):
            sShortName = oObj.name
            oCopy = Clan(id=oObj.id,name=oObj.name,shortname=sShortName,connection=trans)
    return (True,[])

def CopyOldCardType(orig_conn,trans):
    for oObj in CardType.select(connection=orig_conn):
        oCopy = CardType(id=oObj.id,name=oObj.name,connection=trans)
    return (True,[])

def CopyOldRuling(orig_conn,trans):
    for oObj in Ruling.select(connection=orig_conn):
        oCopy = Ruling(id=oObj.id,text=oObj.text,code=oObj.code,url=oObj.url,connection=trans)
    return (True,[])

def CopyOldDisciplinePair(orig_conn,trans):
    oVer = DatabaseVersion()
    if oVer.checkVersions([Discipline],[1]) or \
          oVer.checkVersions([Discipline],[-1]):
        for oObj in DisciplinePair_v1.select(connection=orig_conn):
            if oObj.discipline.name[:2]!='v_':
                oCopy = DisciplinePair(id=oObj.id,level=oObj.level,\
                     discipline=oObj.discipline,connection=trans)
    elif oVer.checkVersions([DisciplinePair],[DisciplinePair.tableversion]):
        for oObj in DisciplinePair_v1.select(connection=orig_conn):
            oCopy = DisciplinePair(id=oObj.id,level=oObj.level,\
                   discipline=oObj.discipline,connection=trans)
    return (True,[])

def CopyOldRarityPair(orig_conn,trans):
    oVer = DatabaseVersion()
    if oVer.checkVersions([Expansion],[1]) or \
          oVer.checkVersions([Expansion],[-1]):
        for oObj in RarityPair_v1.select(connection=orig_conn):
            oCopy = RarityPair(id=oObj.id,expansion=oObj.expansion,rarity=oObj.rarity,\
                connection=trans)
    elif oVer.checkVersions([RarityPair],[RarityPair.tableversion]):
        for oObj in RarityPair.select(connection=orig_conn):
            oCopy = RarityPair(id=oObj.id,expansion=oObj.expansion,rarity=oObj.rarity,\
                connection=trans)
    return (True,[])

def CopyOldAbstractCard(orig_conn,trans):
    oVer = DatabaseVersion()
    aMessages = []
    bFirstImbuedCreedMessage = True
    if oVer.checkVersions([AbstractCard],[AbstractCard.tableversion]):
        for oCard in AbstractCard.select(connection=orig_conn):
            oCardCopy = AbstractCard(id=oCard.id,canonicalName=oCard.canonicalName,name=oCard.name,text=oCard.text,connection=trans)
            # If I don't do things this way, I get encoding issues
            # I don't really feel like trying to understand why
            oCardCopy.group = oCard.group
            oCardCopy.capacity = oCard.capacity
            oCardCopy.cost = oCard.cost
            oCardCopy.costtype = oCard.costtype
            oCardCopy.level = oCard.level
            oCardCopy.life = oCard.life
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
    elif oVer.checkVersions([AbstractCard],[1]) or \
         oVer.checkVersions([AbstractCard],[-1]):
        for oCard in AbstractCard_v1.select(connection=orig_conn):
            oCardCopy = AbstractCard(id=oCard.id,canonicalName=oCard.name.lower(),name=oCard.name,text=oCard.text,connection=trans)
            oCardCopy.group = oCard.group
            oCardCopy.capacity = oCard.capacity
            oCardCopy.cost = oCard.cost
            oCardCopy.costtype = oCard.costtype
            oCardCopy.level = oCard.level
            for oData in oCard.rarity:
                oCardCopy.addRarityPair(oData)
            for oData in oCard.rulings:
                oCardCopy.addRuling(oData)
            for oData in oCard.clan:
                oCardCopy.addClan(oData)
            for oData in oCard.cardtype:
                oCardCopy.addCardType(oData)
            oCardCopy.syncUpdate()
            (sSect,sTitle) = parseText(oCard)
            for oData in oCard.discipline:
                if oData.discipline.name[:2] == 'v_':
                    # Need to point adaptors at new database
                    oldconn = sqlhub.processConnection
                    sqlhub.processConnection = trans
                    oVirtue = IVirtue(oData.discipline.name[2:])
                    sqlhub.processConnection = oldconn
                    oCardCopy.addVirtue(oVirtue)
                else:
                    oCardCopy.addDisciplinePair(oData)
            if sSect is not None:
                # Need to point adaptors at new database
                oldconn = sqlhub.processConnection
                sqlhub.processConnection = trans
                oSect = ISect(sSect)
                sqlhub.processConnection = oldconn
                oCardCopy.addSect(oSect)
            if sTitle is not None:
                # Need to point adaptors at new database
                oldconn = sqlhub.processConnection
                sqlhub.processConnection = trans
                oTitle = ITitle(sTitle)
                sqlhub.processConnection = oldconn
                oCardCopy.addTitle(oTitle)
            aTypes = [oT.name for oT in oCard.cardtype]
            if 'Imbued' in aTypes:
                if bFirstImbuedCreedMessage:
                    aMessages.append('Missing data for the Imbued. You will need to reimport the White wolf card list for these to be correct')
                    bFirstImbuedCreedMessage=False
                aMessages.append('Unable to infer sensible values for life and creed for '+oCard.name.encode('ascii','xmlcharrefreplace'))
            oCardCopy.syncUpdate()
    return (True,aMessages)

def CopyOldPhysicalCard(orig_conn,trans):
    oVer = DatabaseVersion()
    if oVer.checkVersions([PhysicalCard],[PhysicalCard.tableversion]):
        for oCard in PhysicalCard.select(connection=orig_conn):
            oCardCopy = PhysicalCard(id=oCard.id,abstractCard=oCard.abstractCard,
                                     expansion=oCard.expansion,connection=trans)
    elif oVer.checkVersions([PhysicalCard],[1]) or \
           oVer.checkVersions([PhysicalCard],[-1]):
        for oCard in PhysicalCard_v1.select(connection=orig_conn):
            oCardCopy = PhysicalCard(id=oCard.id,abstractCard=oCard.abstractCard,
                                     expansion=None,connection=trans)
    return (True,[])

def CopyOldPhysicalCardSet(orig_conn,trans):
    oVer = DatabaseVersion()
    if oVer.checkVersions([PhysicalCardSet],[PhysicalCardSet.tableversion]):
        for oSet in PhysicalCardSet.select(connection=orig_conn):
            oCopy = PhysicalCardSet(id=oSet.id,name=oSet.name,
                                    author=oSet.author,comment=oSet.comment,
                                    annotations=oSet.annotations,
                                    connection=trans)
            for oCard in oSet.cards:
                oCopy.addPhysicalCard(oCard.id)
            oCopy.syncUpdate()
    elif oVer.checkVersions([PhysicalCardSet],[2]):
        for oSet in PhysicalCardSet_v2.select(connection=orig_conn):
            oCopy = PhysicalCardSet(id=oSet.id,name=oSet.name,
                                    author=oSet.author,comment=oSet.comment,
                                    annotations=None,
                                    connection=trans)
            for oCard in oSet.cards:
                oCopy.addPhysicalCard(oCard.id)
            oCopy.syncUpdate()
    elif oVer.checkVersions([PhysicalCardSet],[1]) or \
           oVer.checkVersions([PhysicalCardSet],[-1]):
        for oSet in PhysicalCardSet_v1.select(connection=orig_conn):
            oCopy = PhysicalCardSet(id=oSet.id,name=oSet.name,
                                    connection=trans)
            for oCard in oSet.cards:
                oCopy.addPhysicalCard(oCard.id)
            oCopy.syncUpdate()
    return (True,[])

def CopyOldAbstractCardSet(orig_conn,trans):
    oVer = DatabaseVersion()
    if oVer.checkVersions([AbstractCardSet],[AbstractCardSet.tableversion]):
        for oSet in AbstractCardSet.select(connection=orig_conn):
            oCopy = AbstractCardSet(id=oSet.id,name=oSet.name,
                                    author=oSet.author,comment=oSet.comment,
                                    annotations=oSet.annotations,
                                    connection=trans)
            for oCard in oSet.cards:
                oCopy.addAbstractCard(oCard.id)
            oCopy.syncUpdate()
    elif oVer.checkVersions([AbstractCardSet],[2]):
        for oSet in AbstractCardSet_v2.select(connection=orig_conn):
            oCopy = AbstractCardSet(id=oSet.id,name=oSet.name,
                                    author=oSet.author,comment=oSet.comment,
                                    annotations=None,
                                    connection=trans)
            for oCard in oSet.cards:
                oCopy.addAbstractCard(oCard.id)
            oCopy.syncUpdate()
    elif oVer.checkVersions([AbstractCardSet],[1]) or \
           oVer.checkVersions([AbstractCardSet],[-1]):
        for oSet in AbstractCardSet_v1.select(connection=orig_conn):
            oCopy = AbstractCardSet(id=oSet.id,name=oSet.name,
                                    connection=trans)
            for oCard in oSet.cards:
                oCopy.addAbstractCard(oCard.id)
            oCopy.syncUpdate()
    return (True,[])

def readOldDB(orig_conn,dest_conn):
    """Read the old database into new database, filling in
       blanks when needed"""
    try:
        if not checkCanReadOldDB(orig_conn):
            return False
    except UnknownVersion, err:
        raise err
    # OK, version checks pass, so we should be able to deal with this
    aMessages = []
    bRes = True
    trans = dest_conn.transaction()
    # Magic happens in the individual functions, as needed
    (bOK,aNewMessages) = CopyOldRarity(orig_conn,trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK,aMessages) = CopyOldExpansion(orig_conn,trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK,aNewMessages) = CopyOldDiscipline(orig_conn,trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK,aNewMessages) = CopyOldClan(orig_conn,trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK,aNewMessages) = CopyOldCardType(orig_conn,trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK,aNewMessages) = CopyOldRuling(orig_conn,trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK,aNewMessages) = CopyOldDisciplinePair(orig_conn,trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK,aNewMessages) = CopyOldRarityPair(orig_conn,trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK,aNewMessages) = CopyOldAbstractCard(orig_conn,trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK,aNewMessages) = CopyOldPhysicalCard(orig_conn,trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK,aNewMessages) = CopyOldPhysicalCardSet(orig_conn,trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    (bOK,aNewMessages) = CopyOldAbstractCardSet(orig_conn,trans)
    bRes = bRes and bOK
    aMessages += aNewMessages
    trans.commit()
    return (bRes,aMessages)

def copyDB(orig_conn,dest_conn):
    # This is a straight copy, with no provision for funky stuff
    # Compataibility of database structures is assumed, but not checked
    # (probably should be fixed)
    # Copy tables needed before we can copy AbstractCard
    bRes = True
    aMessages = []
    trans = dest_conn.transaction()
    # Todo: More error checking
    for oObj in Rarity.select(connection=orig_conn):
        oCopy = Rarity(id=oObj.id,name=oObj.name,connection=trans)
    for oObj in Expansion.select(connection=orig_conn):
        oCopy = Expansion(id=oObj.id,name=oObj.name,shortname=oObj.shortname,connection=trans)
    for oObj in Discipline.select(connection=orig_conn):
        oCopy = Discipline(id=oObj.id,name=oObj.name,fullname=oObj.fullname,connection=trans)
    for oObj in Clan.select(connection=orig_conn):
        oCopy = Clan(id=oObj.id,name=oObj.name,shortname=oObj.shortname,connection=trans)
    for oObj in Creed.select(connection=orig_conn):
        oCopy = Creed(id=oObj.id,name=oObj.name,shortname=oObj.shortname,connection=trans)
    for oObj in Virtue.select(connection=orig_conn):
        oCopy = Virtue(id=oObj.id,name=oObj.name,fullname=oObj.fullname,connection=trans)
    for oObj in CardType.select(connection=orig_conn):
        oCopy = CardType(id=oObj.id,name=oObj.name,connection=trans)
    for oObj in Ruling.select(connection=orig_conn):
        oCopy = Ruling(id=oObj.id,text=oObj.text,code=oObj.code,url=oObj.url,connection=trans)
    for oObj in DisciplinePair.select(connection=orig_conn):
        oCopy = DisciplinePair(id=oObj.id,level=oObj.level,discipline=oObj.discipline,connection=trans)
    for oObj in RarityPair.select(connection=orig_conn):
        oCopy = RarityPair(id=oObj.id,expansion=oObj.expansion,rarity=oObj.rarity,\
                connection=trans)
    for oObj in Sect.select(connection=orig_conn):
        oCopy = Sect(id=oObj.id,name=oObj.name,connection=trans)
    for oObj in Title.select(connection=orig_conn):
        oCopy = Title(id=oObj.id,name=oObj.name,connection=trans)
    trans.commit()
    trans = dest_conn.transaction()
    for oCard in AbstractCard.select(connection=orig_conn):
        oCardCopy = AbstractCard(id=oCard.id,canonicalName=oCard.canonicalName,name=oCard.name,text=oCard.text,connection=trans)
        oCardCopy.group = oCard.group
        oCardCopy.capacity = oCard.capacity
        oCardCopy.cost = oCard.cost
        oCardCopy.costtype = oCard.costtype
        oCardCopy.life = oCard.life
        oCardCopy.level = oCard.level
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
    trans.commit()
    trans = dest_conn.transaction()
    for oCard in PhysicalCard.select(connection=orig_conn):
        oCardCopy = PhysicalCard(id=oCard.id,abstractCard=oCard.abstractCard,
                                 expansion=oCard.expansion,connection=trans)
    trans.commit()
    trans = dest_conn.transaction()
    # Copy Physical card sets
    for oSet in PhysicalCardSet.select(connection=orig_conn):
        oCopy = PhysicalCardSet(id=oSet.id,name=oSet.name,
                                author=oSet.author,comment=oSet.comment,
                                annotations=oSet.annotations,
                                connection=trans)
        for oCard in oSet.cards:
            oCopy.addPhysicalCard(oCard.id)
        oCopy.syncUpdate()
    trans.commit()
    trans = dest_conn.transaction()
    for oSet in AbstractCardSet.select(connection=orig_conn):
        oCopy = AbstractCardSet(id=oSet.id,name=oSet.name,
                                author=oSet.author,comment=oSet.comment,
                                annotations=oSet.annotations,
                                connection=trans)
        for oCard in oSet.cards:
            oCopy.addAbstractCard(oCard.id)
        oCopy.syncUpdate()
    trans.commit()
    return (bRes,aMessages)

def copyToNewAbstractCardDB(orig_conn,new_conn):
    # Given an existing database, and a new database created from
    # a new cardlist, copy the PhysicalCards and the CardSets,
    # adjusting for the possibly changed id's in the AbstractCard Table
    bRes = True
    aMessages = []
    target = new_conn.transaction()
    # Copy the physical card list
    for oCard in PhysicalCard.select(connection=orig_conn):
        sName = oCard.abstractCard.canonicalName
        try:
            oNewAbsCard = AbstractCard.byCanonicalName(sName,connection=target)
            oCardCopy = PhysicalCard(id=oCard.id,abstractCard=oNewAbsCard,
                                     expansion=oCard.expansion,connection=target)
        except SQLObjectNotFound:
            aMessages.append("Unable to find match for "+sName)
            bRes=False
    # Copy Physical card sets
    # IDs are unchangd, since we preserve Physical Card set ids
    for oSet in PhysicalCardSet.select(connection=orig_conn):
        oCopy = PhysicalCardSet(id=oSet.id,name=oSet.name,
                                author=oSet.author,comment=oSet.comment,
                                connection=target)
        for oCard in oSet.cards:
            sName = oAbstractCard=oCard.abstractCard.canonicalName
            try:
                oNewAbsCard = AbstractCard.byCanonicalName(sName,connection=target)
                oCopy.addPhysicalCard(oCard.id)
            except SQLObjectNotFound:
                aMessages.append("Unable to add Physical card %d name %s to set %s" % (oCard.id,oAbstractCard.name,oSet.name))
                bRes = False
        oCopy.syncUpdate() # probably unnessecary
    # Copy AbstractCardSets
    # AbstractCArd is not preserved, so adjust for this
    for oSet in AbstractCardSet.select(connection=orig_conn):
        oCopy = AbstractCardSet(id=oSet.id,name=oSet.name,
                                author=oSet.author,comment=oSet.comment,
                                connection=target)
        for oCard in oSet.cards:
            sName = oCard.name
            try:
                oNewAbsCard = AbstractCard.byCanonicalName(sName.lower(),connection=target)
                oCopy.addAbstractCard(oNewAbsCard.id)
            except SQLObjectNotFound:
                aMessages.append("Unable to find match for %s" % sName)
                bRes = False
        oCopy.syncUpdate()
    target.commit()
    return (bRes,aMessages)

def createMemoryCopy(tempConn):
    # We create a temporary memory database, and create the updated
    # database in it. readOldDB is responsbile for upgrading stuff
    # as needed
    FlushCache()
    if refreshTables(ObjectList,tempConn):
        return readOldDB (sqlhub.processConnection,tempConn)
    else:
        return (False,["Unable to create tables"])

def createFinalCopy(tempConn):
    FlushCache()
    # Copy from the memory database to the real thing
    if refreshTables(ObjectList,sqlhub.processConnection):
        return copyDB(tempConn,sqlhub.processConnection)
    else:
        return (False,["Unable to create tables"])

def attemptDatabaseUpgrade():
    tempConn = connectionForURI("sqlite:///:memory:")
    (bOK,aMessages) = createMemoryCopy(tempConn)
    if bOK:
        print "Copied database to memory, performing upgrade."
        if len(aMessages) > 0:
            print "Messages reported",aMessages
        (bOK,aMessages) = createFinalCopy(tempConn)
        if bOK:
            print "Everything seems to have gone OK"
            if len(aMessages) > 0:
                print "Messages reported",aMessages
            return True
        else:
            print "Unable to perform upgrade."
            if len(aMessages) > 0:
                print "Errors reported",aMessages
            print "!!YOUR DATABASE MAY BE CORRUPTED!!"
            return False
    else:
        print "Unable to create memory copy. Database not upgraded."
        if len(aMessages) > 0:
            print "Errors reported",aMessages
        return False
