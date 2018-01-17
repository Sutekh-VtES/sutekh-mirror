# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006, 2007, 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""Handles the heavy lifting of upgrading the database.

   Holds methods to copy database contents around, utility classes
   to talk to old database versions, and so forth.

   We only support upgrading from the previous stable version
   (currently 0.8)
   """

# pylint: disable=C0302
# This is a long module, partly because of the duplicated code from
# SutekhObjects. We want to keep all the database upgrade stuff together.
# so we jsut live with it

# pylint: disable=E0611
# sqlobject confuses pylint here
from sqlobject import (sqlhub, SQLObject, IntCol, UnicodeCol, RelatedJoin,
                       EnumCol, MultipleJoin, ForeignKey)
# pylint: enable=E0611
from sutekh.base.core.BaseObjects import (PhysicalCard, AbstractCard,
                                          PhysicalCardSet, Expansion,
                                          RarityPair, LookupHints,
                                          Rarity, CardType,
                                          MAX_ID_LENGTH)
from sutekh.core.SutekhObjects import (SutekhAbstractCard, Clan, Virtue,
                                       Discipline, Creed, DisciplinePair,
                                       Sect, Title, TABLE_LIST)
from sutekh.io.WhiteWolfTextParser import strip_braces
from sutekh.base.core.BaseDatabaseUpgrade import BaseDBUpgradeManager
from sutekh.base.core.DatabaseVersion import DatabaseVersion

# This file handles all the grunt work of the database upgrades. We have some
# (arguablely overly) complex trickery to read old databases, and we create a
# copy in sqlite memory database first, before commiting to the actual DB

# We Need to clone the SQLObject classes in SutekhObjects so we can read
# old versions


# pylint: disable=C0103, W0232
# C0103 - names set largely by SQLObject conventions, so ours don't apply
# W0232 - SQLObject classes don't have user defined __init__
class AbstractCard_v5(SQLObject):
    """Table used to upgrade AbstractCard from v5"""
    class sqlmeta:
        """meta class used to set the correct table"""
        table = AbstractCard.sqlmeta.table
        cacheValues = False

    canonicalName = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    name = UnicodeCol()
    text = UnicodeCol()
    group = IntCol(default=None, dbName='grp')
    capacity = IntCol(default=None)
    cost = IntCol(default=None)
    life = IntCol(default=None)
    costtype = EnumCol(enumValues=['pool', 'blood', 'conviction', None],
                       default=None)
    level = EnumCol(enumValues=['advanced', None], default=None)

    # Most of these names are singular when they should be plural
    # since they refer to lists. We've decided to live with the
    # inconsistency for old columns but do the right thing for new
    # ones.
    discipline = RelatedJoin('DisciplinePair',
                             intermediateTable='abs_discipline_pair_map',
                             createRelatedTable=False)
    rarity = RelatedJoin('RarityPair',
                         intermediateTable='abs_rarity_pair_map',
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
    artists = RelatedJoin('Artist', intermediateTable='abs_artist_map',
                          createRelatedTable=False)
    keywords = RelatedJoin('Keyword', intermediateTable='abs_keyword_map',
                           createRelatedTable=False)

    physicalCards = MultipleJoin('PhysicalCard')


class AbstractCard_v6(SQLObject):
    """Table used to upgrade AbstractCard from v6"""
    class sqlmeta:
        """meta class used to set the correct table"""
        table = AbstractCard.sqlmeta.table
        cacheValues = False

    canonicalName = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    name = UnicodeCol()
    text = UnicodeCol()
    search_text = UnicodeCol(default="")
    group = IntCol(default=None, dbName='grp')
    capacity = IntCol(default=None)
    cost = IntCol(default=None)
    life = IntCol(default=None)
    costtype = EnumCol(enumValues=['pool', 'blood', 'conviction', None],
                       default=None)
    level = EnumCol(enumValues=['advanced', None], default=None)

    # Most of these names are singular when they should be plural
    # since they refer to lists. We've decided to live with the
    # inconsistency for old columns but do the right thing for new
    # ones.
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
    artists = RelatedJoin('Artist', intermediateTable='abs_artist_map',
                          createRelatedTable=False)
    keywords = RelatedJoin('Keyword', intermediateTable='abs_keyword_map',
                           createRelatedTable=False)

    physicalCards = MultipleJoin('PhysicalCard')


class PhysicalCard_ACv5(SQLObject):
    """Table used to upgrade AbstractCard from v5"""
    class sqlmeta:
        """meta cleass used to set the correct table"""
        table = PhysicalCard.sqlmeta.table
        cacheValues = False

    abstractCard = ForeignKey('AbstractCard_v5')
    # Explicitly allow None as expansion
    expansion = ForeignKey('Expansion_v3', notNull=False)
    sets = RelatedJoin('PhysicalCardSet', intermediateTable='physical_map',
                       createRelatedTable=False)


class PhysicalCard_ACv6(SQLObject):
    """Table used to upgrade AbstractCard from v6"""
    class sqlmeta:
        """meta cleass used to set the correct table"""
        table = PhysicalCard.sqlmeta.table
        cacheValues = False

    abstractCard = ForeignKey('AbstractCard_v6')
    # Explicitly allow None as expansion
    expansion = ForeignKey('Expansion', notNull=False)
    sets = RelatedJoin('PhysicalCardSet', intermediateTable='physical_map',
                       createRelatedTable=False)


class Expansion_v3(SQLObject):
    """Table used to update Expansion from v3"""

    class sqlmeta:
        """meta cleass used to set the correct table"""
        table = Expansion.sqlmeta.table
        cacheValues = False

    name = UnicodeCol(alternateID=True, length=MAX_ID_LENGTH)
    shortname = UnicodeCol(default=None)
    pairs = MultipleJoin('RarityPair_Ev3')


class RarityPair_Ev3(SQLObject):
    """Table used to update Expansion from v3"""

    class sqlmeta:
        """meta cleass used to set the correct table"""
        table = RarityPair.sqlmeta.table
        cacheValues = False

    expansion = ForeignKey('Expansion_v3')
    rarity = ForeignKey('Rarity')


# pylint: enable=C0103, W0232

class DBUpgradeManager(BaseDBUpgradeManager):
    """Class to handle database upgrades,"""

    # pylint: disable=R0201
    # R0201: Several _copy methods are very simple, but methods for
    # consistency.

    # Sutekh 0.9.x and 1.0.x can upgrade from the versions in Sutekh 0.8.x,
    # but no earlier
    SUPPORTED_TABLES = BaseDBUpgradeManager.SUPPORTED_TABLES
    SUPPORTED_TABLES.update({
        'Discipline': (Discipline, (Discipline.tableversion,)),
        'Clan': (Clan, (Clan.tableversion,)),
        'Creed': (Creed, (Creed.tableversion,)),
        'Virtue': (Virtue, (Virtue.tableversion,)),
        'Sect': (Sect, (Sect.tableversion,)),
        'DisciplinePair': (DisciplinePair, (DisciplinePair.tableversion,)),
        'Title': (Title, (Title.tableversion,)),
    })
    # We override the default values for these
    SUPPORTED_TABLES['Expansion'] = (Expansion, (Expansion.tableversion, 3))
    SUPPORTED_TABLES['AbstractCard'] = (AbstractCard,
                                        (AbstractCard.tableversion, 5, 6))
    SUPPORTED_TABLES['PhysicalCardSet'] = (PhysicalCardSet,
                                           (PhysicalCardSet.tableversion, 6))

    COPY_OLD_DB = [
        ('_copy_old_discipline', 'Discipline table', False),
        ('_copy_old_clan', 'Clan table', False),
        ('_copy_old_creed', 'Creed table', False),
        ('_copy_old_virtue', 'Virtue table', False),
        ('_copy_old_discipline_pair', 'DisciplinePair table', False),
        ('_copy_old_sect', 'Sect table', False),
        ('_copy_old_title', 'Title table', False),
    ] + BaseDBUpgradeManager.COPY_OLD_DB

    COPY_DB = [
        ('_copy_discipline', 'Discipline table', False),
        ('_copy_clan', 'Clan table', False),
        ('_copy_creed', 'Creed table', False),
        ('_copy_virtue', 'Virtue table', False),
        ('_copy_discipline_pair', 'DisciplinePair table', False),
        ('_copy_sect', 'Sect table', False),
        ('_copy_title', 'Title table', False),
    ] + BaseDBUpgradeManager.COPY_DB

    cAbstractCardCls = SutekhAbstractCard

    _aTableList = TABLE_LIST

    def old_database_count(self, oConn):
        """Check number of items in old DB fro progress bars, etc."""
        oVer = DatabaseVersion()
        iCount = 14  # Card property tables
        if oVer.check_tables_and_versions([AbstractCard],
                                          [AbstractCard.tableversion], oConn):
            iCount += AbstractCard.select(connection=oConn).count()
        elif oVer.check_tables_and_versions([AbstractCard], [5], oConn):
            iCount += AbstractCard_v5.select(connection=oConn).count()
        if oVer.check_tables_and_versions([PhysicalCard],
                                          [PhysicalCard.tableversion],
                                          oConn):
            iCount += PhysicalCard.select(connection=oConn).count()
        if oVer.check_tables_and_versions([PhysicalCardSet],
                                          [PhysicalCardSet.tableversion],
                                          oConn):
            iCount += PhysicalCardSet.select(connection=oConn).count()
        elif oVer.check_tables_and_versions([PhysicalCardSet], [6], oConn):
            iCount += PhysicalCardSet.select(connection=oConn).count()
        return iCount

    def cur_database_count(self, oConn):
        """Current number of items in the database."""
        return 14 + self._get_card_counts(oConn)

    def _upgrade_expansion(self, oOrigConn, oTrans, oVer):
        """Copy Expansion, updating as needed"""
        aMessages = []
        if oVer.check_tables_and_versions([Expansion], [3], oOrigConn):
            aMessages.append("Missing date information for expansions."
                             " You will need to reimport the card list"
                             " for these to be correct")
            for oObj in Expansion_v3.select(connection=oOrigConn):
                _oCopy = Expansion(id=oObj.id, name=oObj.name,
                                   shortname=oObj.shortname,
                                   releasedate=None,
                                   connection=oTrans)
        else:
            return (False, ["Unknown Expansion Version"])
        return (True, aMessages)

    def _upgrade_lookup_hints(self, oOrigConn, oTrans, oVer):
        """Create lookup hints table in the case of v3 Expansion data"""
        aMessages = []
        if (oVer.check_tables_and_versions([Expansion], [3], oOrigConn) and
                oVer.check_tables_and_versions([LookupHints],
                                                [-1], oOrigConn)):
            aMessages = ["Incomplete information to fill the LookupHints"
                         " table. You will need to reimport the cardlist"
                         " information."]
            # Rarity
            for oObj in Rarity.select(connection=oOrigConn):
                _oEntry = LookupHints(domain="Rarities",
                                      lookup=oObj.name,
                                      value=oObj.name,
                                      connection=oTrans)
                if oObj.name != oObj.shortname:
                    _oEntry = LookupHints(domain="Rarities",
                                          lookup=oObj.shortname,
                                          value=oObj.name,
                                          connection=oTrans)
            # CardType
            for oObj in CardType.select(connection=oOrigConn):
                _oEntry = LookupHints(domain="CardTypes",
                                      lookup=oObj.name,
                                      value=oObj.name,
                                      connection=oTrans)
            # Expansion
            for oObj in Expansion_v3.select(connection=oOrigConn):
                _oEntry = LookupHints(domain="Expansions",
                                      lookup=oObj.name,
                                      value=oObj.name,
                                      connection=oTrans)
                if oObj.name != oObj.shortname:
                    _oEntry = LookupHints(domain="Expansions",
                                          lookup=oObj.shortname,
                                          value=oObj.name,
                                          connection=oTrans)
        else:
            return super(DBUpgradeManager, self)._upgrade_lookup_hints(
                oOrigConn, oTrans, oVer)
        return (True, aMessages)

    def _copy_discipline(self, oOrigConn, oTrans):
        """Copy Discipline, assuming versions match"""
        for oObj in Discipline.select(connection=oOrigConn):
            _oCopy = Discipline(id=oObj.id, name=oObj.name,
                                fullname=oObj.fullname, connection=oTrans)

    def _copy_old_discipline(self, oOrigConn, oTrans, oVer):
        """Copy disciplines, upgrading as needed."""
        if oVer.check_tables_and_versions([Discipline],
                                          [Discipline.tableversion],
                                          oOrigConn):
            self._copy_discipline(oOrigConn, oTrans)
        else:
            return (False, ["Unknown Discipline version"])
        return (True, [])

    def _copy_clan(self, oOrigConn, oTrans):
        """Copy Clan, assuming database versions match"""
        for oObj in Clan.select(connection=oOrigConn):
            _oCopy = Clan(id=oObj.id, name=oObj.name, shortname=oObj.shortname,
                          connection=oTrans)

    def _copy_old_clan(self, oOrigConn, oTrans, oVer):
        """Copy clan, upgrading as needed."""
        if oVer.check_tables_and_versions([Clan], [Clan.tableversion],
                                          oOrigConn):
            self._copy_clan(oOrigConn, oTrans)
        else:
            return (False, ["Unknown Clan Version"])
        return (True, [])

    def _copy_creed(self, oOrigConn, oTrans):
        """Copy Creed, assuming versions match"""
        for oObj in Creed.select(connection=oOrigConn):
            _oCopy = Creed(id=oObj.id, name=oObj.name,
                           shortname=oObj.shortname, connection=oTrans)

    def _copy_old_creed(self, oOrigConn, oTrans, oVer):
        """Copy Creed, updating if needed"""
        if oVer.check_tables_and_versions([Creed], [Creed.tableversion],
                                          oOrigConn):
            self._copy_creed(oOrigConn, oTrans)
        else:
            return (False, ["Unknown Creed Version"])
        return (True, [])

    def _copy_virtue(self, oOrigConn, oTrans):
        """Copy Virtue, assuming versions match"""
        for oObj in Virtue.select(connection=oOrigConn):
            _oCopy = Virtue(id=oObj.id, name=oObj.name, fullname=oObj.fullname,
                            connection=oTrans)

    def _copy_old_virtue(self, oOrigConn, oTrans, oVer):
        """Copy Virtue, updating if needed"""
        if oVer.check_tables_and_versions([Virtue], [Virtue.tableversion],
                                          oOrigConn):
            self._copy_virtue(oOrigConn, oTrans)
        else:
            return (False, ["Unknown Virtue Version"])
        return (True, [])

    def _copy_discipline_pair(self, oOrigConn, oTrans):
        """Copy DisciplinePair, assuming versions match"""
        for oObj in DisciplinePair.select(connection=oOrigConn):
            # pylint: disable=W0212
            # Need to access _connection here
            # Force for SQLObject >= 0.11.4
            oObj._connection = oOrigConn
            # pylint: enable=W0212
            _oCopy = DisciplinePair(id=oObj.id, level=oObj.level,
                                    discipline=oObj.discipline,
                                    connection=oTrans)

    def _copy_old_discipline_pair(self, oOrigConn, oTrans, oVer):
        """Copy DisciplinePair, upgrading if needed"""
        if oVer.check_tables_and_versions([DisciplinePair],
                                          [DisciplinePair.tableversion],
                                          oOrigConn):
            self._copy_discipline_pair(oOrigConn, oTrans)
        else:
            return (False, ["Unknown Discipline Version"])
        return (True, [])

    def _copy_old_rarity_pair(self, oOrigConn, oTrans, oVer):
        """Copy RarityPair, upgrading as needed"""
        # We override the whole method, rather than using upgrade_rarity_pair
        # hook, due to complexity of the checks here
        if oVer.check_tables_and_versions([RarityPair],
                                          [RarityPair.tableversion],
                                          oOrigConn):
            if oVer.check_tables_and_versions([Expansion],
                                              [Expansion.tableversion],
                                              oOrigConn):
                self._copy_rarity_pair(oOrigConn, oTrans)
            elif oVer.check_tables_and_versions([Expansion], [3], oOrigConn):
                for oObj in RarityPair_Ev3.select(connection=oOrigConn):
                    # pylint: disable=W0212
                    # Need to access _connection here
                    oObj._connection = oOrigConn
                    # pylint: enable=W0212
                    _oCopy = RarityPair(id=oObj.id,
                                        expansionID=oObj.expansion.id,
                                        rarityID=oObj.rarity.id,
                                        connection=oTrans)
            else:
                # This may result in a duplicate error message
                return (False, ["Unknown Expansion version"])
        else:
            return (False, ["Unknown RarityPair version"])
        return (True, [])

    def _copy_sect(self, oOrigConn, oTrans):
        """Copy Sect, assuming versions match"""
        for oObj in Sect.select(connection=oOrigConn):
            _oCopy = Sect(id=oObj.id, name=oObj.name, connection=oTrans)

    def _copy_old_sect(self, oOrigConn, oTrans, oVer):
        """Copy Sect, updating if needed"""
        if oVer.check_tables_and_versions([Sect], [Sect.tableversion],
                                          oOrigConn):
            self._copy_sect(oOrigConn, oTrans)
        else:
            return (False, ["Unknown Sect Version"])
        return (True, [])

    def _copy_title(self, oOrigConn, oTrans):
        """Copy Title, assuming versions match"""
        for oObj in Title.select(connection=oOrigConn):
            _oCopy = Title(id=oObj.id, name=oObj.name, connection=oTrans)

    def _copy_old_title(self, oOrigConn, oTrans, oVer):
        """Copy Title, updating if needed"""
        if oVer.check_tables_and_versions([Title], [Title.tableversion],
                                          oOrigConn):
            self._copy_title(oOrigConn, oTrans)
        else:
            return (False, ["Unknown Title Version"])
        return (True, [])

    def drop_old_tables(self, _oConn):
        """Nothing to drop on the upgrade from 0.8"""
        return True

    def _make_abs_card(self, oOldCard, oTrans):
        """Copy SutekhAbstractCard, assuming versions match"""
        # pylint: disable=R0912
        # R0912 - need the branches for this
        oCardCopy = SutekhAbstractCard(
            id=oOldCard.id, canonicalName=oOldCard.canonicalName,
            name=oOldCard.name, text=oOldCard.text,
            search_text=oOldCard.search_text, connection=oTrans)
        # If I don't do things this way, I get encoding issues
        # I don't really feel like trying to understand why
        oCardCopy.group = oOldCard.group
        oCardCopy.capacity = oOldCard.capacity
        oCardCopy.cost = oOldCard.cost
        oCardCopy.costtype = oOldCard.costtype
        oCardCopy.level = oOldCard.level
        oCardCopy.life = oOldCard.life
        for oData in oOldCard.discipline:
            oCardCopy.addDisciplinePair(oData)
        for oData in oOldCard.clan:
            oCardCopy.addClan(oData)
        for oData in oOldCard.sect:
            oCardCopy.addSect(oData)
        for oData in oOldCard.title:
            oCardCopy.addTitle(oData)
        for oData in oOldCard.creed:
            oCardCopy.addCreed(oData)
        for oData in oOldCard.virtue:
            oCardCopy.addVirtue(oData)
        return oCardCopy

    def _upgrade_abstract_card(self, oOrigConn, oTrans, oLogger, oVer):
        """Copy AbstractCard, upgrading as needed"""
        # pylint: disable=R0912, R0915
        # R0912 - need the branches for this
        # R0915 - This is long, but needs to be to handle all the cases
        # Postgres 9's default ordering may not be by id, which causes issues
        # when doing the database upgrade when combined with postgres 9's
        # auto-incrementing behaviour. We explictly sort by id to force
        # the issue, which works, but may break again later.
        aMessages = []
        if oVer.check_tables_and_versions([AbstractCard], [5], oOrigConn):
            oTempConn = sqlhub.processConnection
            sqlhub.processConnection = oTrans
            sqlhub.processConnection = oTempConn
            for oCard in AbstractCard_v5.select(
                    connection=oOrigConn).orderBy('id'):
                # pylint: disable=W0212
                # Need to access _connection here
                # force issue for SQObject >= 0.11.4
                oCard._connection = oOrigConn
                # pylint: enable=W0212
                oCardCopy = SutekhAbstractCard(
                    id=oCard.id, canonicalName=oCard.canonicalName,
                    name=oCard.name, text=oCard.text, connection=oTrans)
                oCardCopy.group = oCard.group
                oCardCopy.capacity = oCard.capacity
                oCardCopy.cost = oCard.cost
                oCardCopy.costtype = oCard.costtype
                oCardCopy.level = oCard.level
                oCardCopy.life = oCard.life
                oCardCopy.search_text = strip_braces(oCard.text)
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
                for oData in oCard.keywords:
                    oCardCopy.addKeyword(oData)
                for oData in oCard.artists:
                    oCardCopy.addArtist(oData)
                oCardCopy.syncUpdate()
                # pylint: disable=W0212
                # Need to access _parent here
                oCardCopy._parent.syncUpdate()
                oLogger.info('copied AC %s', oCardCopy.name)
        elif oVer.check_tables_and_versions([AbstractCard], [6], oOrigConn):
            oTempConn = sqlhub.processConnection
            sqlhub.processConnection = oTrans
            sqlhub.processConnection = oTempConn
            for oCard in AbstractCard_v6.select(
                    connection=oOrigConn).orderBy('id'):
                # pylint: disable=W0212
                # Need to access _connection here
                # force issue for SQObject >= 0.11.4
                oCard._connection = oOrigConn
                # pylint: enable=W0212
                oCardCopy = SutekhAbstractCard(
                    id=oCard.id, canonicalName=oCard.canonicalName,
                    name=oCard.name, text=oCard.text, connection=oTrans)
                oCardCopy.group = oCard.group
                oCardCopy.capacity = oCard.capacity
                oCardCopy.cost = oCard.cost
                oCardCopy.costtype = oCard.costtype
                oCardCopy.level = oCard.level
                oCardCopy.life = oCard.life
                oCardCopy.search_text = oCard.search_text
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
                for oData in oCard.keywords:
                    oCardCopy.addKeyword(oData)
                for oData in oCard.artists:
                    oCardCopy.addArtist(oData)
                oCardCopy.syncUpdate()
                # pylint: disable=W0212
                # Need to access _parent here
                oCardCopy._parent.syncUpdate()
                oLogger.info('copied AC %s', oCardCopy.name)
        else:
            return (False, ["Unknown AbstractCard version"])
        return (True, aMessages)

    def _upgrade_physical_card(self, oOrigConn, oTrans, oLogger, oVer):
        """Copy PhysicalCards, upgrading if needed."""
        aMessages = []
        if not oVer.check_tables_and_versions([PhysicalCard],
                                              [PhysicalCard.tableversion],
                                              oOrigConn):
            return (False, ["Unknown PhysicalCard version"])
        elif oVer.check_tables_and_versions([AbstractCard], [5], oOrigConn):
            for oCard in PhysicalCard_ACv5.select(
                    connection=oOrigConn).orderBy('id'):
                oCardCopy = PhysicalCard(
                    id=oCard.id, abstractCardID=oCard.abstractCardID,
                    expansionID=oCard.expansionID, connection=oTrans)
                oCardCopy.syncUpdate()
                oLogger.info('copied PC %s', oCardCopy.id)
        elif oVer.check_tables_and_versions([AbstractCard], [6], oOrigConn):
            for oCard in PhysicalCard_ACv6.select(
                    connection=oOrigConn).orderBy('id'):
                oCardCopy = PhysicalCard(
                    id=oCard.id, abstractCardID=oCard.abstractCardID,
                    expansionID=oCard.expansionID, connection=oTrans)
                oCardCopy.syncUpdate()
                oLogger.info('copied PC %s', oCardCopy.id)
        else:
            return (False, ["Unknown PhysicalCard version"])
        return (True, aMessages)

    def _upgrade_physical_card_set(self, oOrigConn, oTrans, oLogger, oVer):
        """Copy PCS, upgrading as needed."""
        aMessages = []
        if oVer.check_tables_and_versions([PhysicalCardSet, PhysicalCard],
                                          [6, PhysicalCard.tableversion],
                                          oOrigConn):
            # Version 7 just adds an extra index, so we don't need
            # fancier copy logic
            self._copy_physical_card_set(oOrigConn, oTrans, oLogger)
        else:
            return (False, ["Unknown PhysicalCardSet version"])
        return (True, aMessages)
