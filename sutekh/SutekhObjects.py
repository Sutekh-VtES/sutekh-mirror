# SutekhObjects.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Minor modifications copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

from sqlobject import *
from protocols import advise, Interface
import protocols

# Interfaces

class IAbstractCard(Interface): pass
class IPhysicalCard(Interface): pass
class IAbstractCardSet(Interface): pass
class IPhysicalCardSet(Interface): pass
class IRarityPair(Interface): pass
class IExpansion(Interface): pass
class IRarity(Interface): pass
class IDisciplinePair(Interface): pass
class IDiscipline(Interface): pass
class IClan(Interface): pass
class ICardType(Interface): pass
class IRuling(Interface): pass

# Table Objects

class VersionTable(SQLObject):
    TableName = UnicodeCol(alternateID=True,length=50)
    Version = IntCol(default=None)
    tableversion = 1

class AbstractCard(SQLObject):
    advise(instancesProvide=[IAbstractCard])

    tableversion = 1
    sqlmeta.lazyUpdate = True

    name = UnicodeCol(alternateID=True,length=50)
    text = UnicodeCol()
    group = IntCol(default=None,dbName='grp')
    capacity = IntCol(default=None)
    cost = IntCol(default=None)
    costtype = EnumCol(enumValues=['pool','blood','conviction',None],default=None)
    level = EnumCol(enumValues=['advanced',None],default=None)

    discipline = RelatedJoin('DisciplinePair',intermediateTable='abs_discipline_pair_map',createRelatedTable=False)
    rarity = RelatedJoin('RarityPair',intermediateTable='abs_rarity_pair_map',createRelatedTable=False)
    clan = RelatedJoin('Clan',intermediateTable='abs_clan_map',createRelatedTable=False)
    cardtype = RelatedJoin('CardType',intermediateTable='abs_type_map',createRelatedTable=False)
    rulings = RelatedJoin('Ruling',intermediateTable='abs_ruling_map',createRelatedTable=False)
    sets = RelatedJoin('AbstractCardSet',intermediateTable='abstract_map',createRelatedTable=False)
    physicalCards = MultipleJoin('PhysicalCard')

class PhysicalCard(SQLObject):
    advise(instancesProvide=[IPhysicalCard])

    tableversion = 1
    abstractCard = ForeignKey('AbstractCard')
    abstractCardIndex = DatabaseIndex(abstractCard)
    sets = RelatedJoin('PhysicalCardSet',intermediateTable='physical_map',createRelatedTable=False)

class AbstractCardSet(SQLObject):
    advise(instancesProvide=[IAbstractCardSet])

    tableversion = 2
    name = UnicodeCol(alternateID=True,length=50)
    author = UnicodeCol(length=50,default='')
    comment = UnicodeCol(default='')
    cards = RelatedJoin('AbstractCard',intermediateTable='abstract_map',createRelatedTable=False)

class PhysicalCardSet(SQLObject):
    advise(instancesProvide=[IPhysicalCardSet])

    tableversion = 2
    name = UnicodeCol(alternateID=True,length=50)
    author = UnicodeCol(length=50,default='')
    comment = UnicodeCol(default='')
    cards = RelatedJoin('PhysicalCard',intermediateTable='physical_map',createRelatedTable=False)

class RarityPair(SQLObject):
    advise(instancesProvide=[IRarityPair])

    tableversion = 1
    expansion = ForeignKey('Expansion')
    rarity = ForeignKey('Rarity')
    cards = RelatedJoin('AbstractCard',intermediateTable='abs_rarity_pair_map',createRelatedTable=False)
    expansionRarityIndex = DatabaseIndex(expansion,rarity,unique=True)

class Expansion(SQLObject):
    advise(instancesProvide=[IExpansion])

    tableversion = 1
    name = UnicodeCol(alternateID=True,length=20)
    pairs = MultipleJoin('RarityPair')

class Rarity(SQLObject):
    advise(instancesProvide=[IRarity])

    tableversion = 1
    name = UnicodeCol(alternateID=True,length=20)

class DisciplinePair(SQLObject):
    advise(instancesProvide=[IDisciplinePair])

    tableversion = 1
    discipline = ForeignKey('Discipline')
    level = EnumCol(enumValues=['inferior','superior'])
    disciplineLevelIndex = DatabaseIndex(discipline,level,unique=True)
    cards = RelatedJoin('AbstractCard',intermediateTable='abs_discipline_pair_map',createRelatedTable=False)

class Discipline(SQLObject):
    advise(instancesProvide=[IDiscipline])

    tableversion = 1
    name = UnicodeCol(alternateID=True,length=30)
    pairs = MultipleJoin('DisciplinePair')

class Clan(SQLObject):
    advise(instancesProvide=[IClan])

    tableversion = 1
    name = UnicodeCol(alternateID=True,length=40)
    cards = RelatedJoin('AbstractCard',intermediateTable='abs_clan_map',createRelatedTable=False)

class CardType(SQLObject):
    advise(instancesProvide=[ICardType])

    tableversion = 1
    name = UnicodeCol(alternateID=True,length=50)
    cards = RelatedJoin('AbstractCard',intermediateTable='abs_type_map',createRelatedTable=False)

class Ruling(SQLObject):
    advise(instancesProvide=[IRuling])

    tableversion = 1
    text = UnicodeCol(alternateID=True,length=512)
    code = UnicodeCol(length=50)
    url = UnicodeCol(length=256,default=None)
    cards = RelatedJoin('AbstractCard',intermediateTable='abs_ruling_map',createRelatedTable=False)

# Mapping Tables

class MapPhysicalCardToPhysicalCardSet(SQLObject):
    class sqlmeta:
        table = 'physical_map'

    tableversion = 1

    physicalCard = ForeignKey('PhysicalCard',notNull=True)
    physicalCardSet = ForeignKey('PhysicalCardSet',notNull=True)

    physicalCardIndex = DatabaseIndex(physicalCard,unique=False)
    physicalCardSetIndex = DatabaseIndex(physicalCardSet,unique=False)
    jointIndex = DatabaseIndex(physicalCard,physicalCardSet,unique=False)

class MapAbstractCardToAbstractCardSet(SQLObject):
    class sqlmeta:
        table = 'abstract_map'

    tableversion = 1
    abstractCard = ForeignKey('AbstractCard',notNull=True)
    abstractCardSet = ForeignKey('AbstractCardSet',notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard,unique=False)
    abstractCardSetIndex = DatabaseIndex(abstractCardSet,unique=False)

class MapAbstractCardToRarityPair(SQLObject):
    class sqlmeta:
        table = 'abs_rarity_pair_map'

    tableversion = 1

    abstractCard = ForeignKey('AbstractCard',notNull=True)
    rarityPair = ForeignKey('RarityPair',notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard,unique=False)
    rarityPairIndex = DatabaseIndex(rarityPair,unique=False)

class MapAbstractCardToRuling(SQLObject):
    class sqlmeta:
        table = 'abs_ruling_map'

    tableversion = 1

    abstractCard = ForeignKey('AbstractCard',notNull=True)
    ruling = ForeignKey('Ruling',notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard,unique=False)
    rulingIndex = DatabaseIndex(ruling,unique=False)

class MapAbstractCardToClan(SQLObject):
    class sqlmeta:
        table = 'abs_clan_map'

    tableversion = 1

    abstractCard = ForeignKey('AbstractCard',notNull=True)
    clan = ForeignKey('Clan',notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard,unique=False)
    clanIndex = DatabaseIndex(clan,unique=False)

class MapAbstractCardToDisciplinePair(SQLObject):
    class sqlmeta:
        table = 'abs_discipline_pair_map'

    tableversion = 1

    abstractCard = ForeignKey('AbstractCard',notNull=True)
    disciplinePair = ForeignKey('DisciplinePair',notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard,unique=False)
    disciplinePairIndex = DatabaseIndex(disciplinePair,unique=False)

class MapAbstractCardToCardType(SQLObject):
    class sqlmeta:
        table = 'abs_type_map'

    tableversion = 1

    abstractCard = ForeignKey('AbstractCard',notNull=True)
    cardType = ForeignKey('CardType',notNull=True)

    abstractCardIndex = DatabaseIndex(abstractCard,unique=False)
    cardTypeIndex = DatabaseIndex(cardType,unique=False)

# List of Tables to be created, dropped, etc.

ObjectList = [ AbstractCard, PhysicalCard, AbstractCardSet, PhysicalCardSet,
               Expansion, Rarity, RarityPair, Discipline, DisciplinePair,
               Clan, CardType, Ruling,
               # Mapping tables from here on out
               MapPhysicalCardToPhysicalCardSet,
               MapAbstractCardToAbstractCardSet,
               MapAbstractCardToRarityPair,
               MapAbstractCardToRuling,
               MapAbstractCardToClan,
               MapAbstractCardToDisciplinePair,
               MapAbstractCardToCardType ]

# Adapters

class StrAdaptMeta(type):
    def __init__(self, sName, aBases, dDict):
        self.makeLookupDict(dDict['keys'])
        self.makeObjectCache()

    def makeLookupDict(self,dKeys):
        self.__dLook = {}

        for sKey, aAlts in dKeys.iteritems():
            self.__dLook[sKey] = sKey
            for sAlt in aAlts:
                self.__dLook[sAlt] = sKey

    def makeObjectCache(self):
        self.__dCache = {}

    def canonical(self,sName):
        return self.__dLook[sName]

    def fetch(self,sName,oCls):
        o = self.__dCache.get(sName,None)
        if not o is None:
            return o

        try:
            o = oCls.byName(sName.encode('utf8'))
        except SQLObjectNotFound:
            o = oCls(name=sName)

        self.__dCache[sName] = o
        return o

class ExpansionAdapter(object):
    __metaclass__ = StrAdaptMeta
    advise(instancesProvide=[IExpansion],asAdapterForTypes=[basestring])

    keys = { 'Anarchs' : [],
             'Ancient Hearts' : ['AH'],
             'Blackhand' : ['BH'],
             'Bloodlines' : ['BL'],
             'Camarilla Edition' : ['CE'],
             'Dark Sovereigns' : ['DS'],
             'Final Nights' : ['FN'],
             'Gehenna' : [],
             'Jyhad' : [],
             'Kindred Most Wanted' : ['KMW'],
             'Legacy of Blood' : ['LoB'],
             'Nights of Reckoning' : ['NoR'],
             'Sabbat' : [],
             'Sabbat Wars' : ['SW'],
             'Tenth Anniversary' : ['Tenth'],
             'Third Edition' : ['Third'],
             'VTES' : [],
           }

    def __new__(cls,s):
        if s.startswith('Promo-'):
            sName = s
        else:
            sName = cls.canonical(s)
        return cls.fetch(sName,Expansion)

class RarityAdapter(object):
    __metaclass__ = StrAdaptMeta
    advise(instancesProvide=[IRarity],asAdapterForTypes=[basestring])

    keys = { 'Common' : ['C','C1','C2','C3'],
             'Uncommon' : ['U','U1','U2','U3','U5'],
             'Rare' : ['R','R1','R2','R3'],
             'Vampire' : ['V','V1','V2','V3'],
             'Tenth': ['A','B'],
             'Precon' : ['PB','PA','PTo3','PTr','PG','PB2','PTo4','PAl2'],
             'Not Applicable' : ['NA'],
           }

    def __new__(cls,s):
        if s.startswith('P'):
            sName = 'Precon'
        else:
            sName = cls.canonical(s)
        return cls.fetch(sName,Rarity)

class RarityPairAdapter(object):
    advise(instancesProvide=[IRarityPair],asAdapterForTypes=[tuple])

    __dCache = {}

    def __new__(cls,t):
        oE = IExpansion(t[0])
        oR = IRarity(t[1])

        oP = cls.__dCache.get((oE.id,oR.id),None)
        if not oP is None:
            return oP

        try:
            aRes = list(RarityPair.selectBy(expansion=oE,rarity=oR))
            if len(aRes) != 1:
                raise TypeError
            oP = aRes[0]
        except:
            oP = RarityPair(expansion=oE,rarity=oR)

        cls.__dCache[(oE.id,oR.id)] = oP
        return oP

class DisciplineAdapter(object):
    __metaclass__ = StrAdaptMeta
    advise(instancesProvide=[IDiscipline],asAdapterForTypes=[basestring])

    keys = { # Disciplines (last key is full name)
             'abo' : ['ABO','Abombwe'],
             'ani' : ['ANI','Animalism'],
             'aus' : ['AUS','Auspex'],
             'cel' : ['CEL','Celerity'],
             'chi' : ['CHI','Chimerstry'],
             'dai' : ['DAI','Daimoinon'],
             'dem' : ['DEM','Dementation'],
             'dom' : ['DOM','Dominate'],
             'fli' : ['FLI','Flight'],
             'for' : ['FOR','Fortitude'],
             'mel' : ['MEL','Melpominee'],
             'myt' : ['MYT','Mytherceria'],
             'nec' : ['NEC','Necromancy'],
             'obe' : ['OBE','Obeah'],
             'obf' : ['OBF','Obfuscate'],
             'obt' : ['OBT','Obtenebration'],
             'pot' : ['POT','Potence'],
             'pre' : ['PRE','Presence'],
             'pro' : ['PRO','Protean'],
             'qui' : ['QUI','Quietus'],
             'san' : ['SAN','Sanguinus'],
             'ser' : ['SER','Serpentis'],
             'spi' : ['SPI','Spiritus'],
             'tem' : ['TEM','Temporis'],
             'thn' : ['THN','Thanatosis'],
             'tha' : ['THA','Thaumaturgy'],
             'val' : ['VAL','Valeren'],
             'vic' : ['VIC','Vicissitude'],
             'vis' : ['VIS','Visceratika'],
             # Virtues (last key is full name)
             'v_def' : ['Defense'],
             'v_inn' : ['Innocence'],
             'v_jud' : ['Judgment','Judgement'],
             'v_mar' : ['Martyrdom'],
             'v_red' : ['Redemption'],
             'v_ven' : ['Vengeance'],
             'v_vis' : ['Vision'],
           }

    def __new__(cls,s):
        sName = cls.canonical(s)
        return cls.fetch(sName,Discipline)

class DisciplinePairAdapter(object):
    advise(instancesProvide=[IDisciplinePair],asAdapterForTypes=[tuple])

    __dCache = {}

    def __new__(cls,t):
        oD = IDiscipline(t[0])
        sLevel = str(t[1])

        oP = cls.__dCache.get((oD.id,sLevel),None)
        if not oP is None:
            return oP

        try:
            aRes = list(DisciplinePair.selectBy(discipline=oD,level=sLevel))
            if len(aRes) != 1:
                raise TypeError
            oP = aRes[0]
        except:
            oP = DisciplinePair(discipline=oD,level=sLevel)

        cls.__dCache[(oD.id,sLevel)] = oP
        return oP

class ClanAdapter(object):
    __metaclass__ = StrAdaptMeta
    advise(instancesProvide=[IClan],asAdapterForTypes=[basestring])

    keys = { # Camarilla
             'Brujah' : [], 'Malkavian' : [], 'Nosferatu' : [],
             'Toreador' : [],'Tremere' : [], 'Ventrue' : [],
             'Caitiff' : [],
             # Independents
             'Abomination' : [], 'Gangrel' : [], 'Assamite' : [],
             'Follower of Set' : [], 'Giovanni' : [], 'Ravnos' : [],
             'Baali' : [], 'Daughter of Cacophony' : [], 'Gargoyle' : [],
             'Nagaraja' : [], 'Salubri' :[], 'Samedi' : [],
             'True Brujah' : [],
             # Sabbat
             'Lasombra' : [], 'Tzimisce' : [], 'Brujah antitribu' : [],
             'Gangrel antitribu' : [], 'Malkavian antitribu' : [], 'Nosferatu antitribu' : [],
             'Toreador antitribu' : [], 'Tremere antitribu' : [], 'Ventrue antitribu' : [],
             'Pander' : [], 'Ahrimanes' : [], 'Blood Brother' : [],
             'Harbinger of Skulls' : [], 'Kiasyd' : [], 'Salubri antitribu' : [],
             # Laibon
             'Akunanse' : [], 'Guruhi' : [], 'Ishtarri' : [],
             'Osebo' : [],
             # Other
             'Ahrimane' : [],
           }

    def __new__(cls,s):
        sName = cls.canonical(s)
        return cls.fetch(sName,Clan)

class CardTypeAdapter(object):
    __metaclass__ = StrAdaptMeta
    advise(instancesProvide=[ICardType],asAdapterForTypes=[basestring])

    keys = { 'Action' : [], 'Action Modifier' : [], 'Ally' : [],
             'Combat' : [], 'Conviction' : [], 'Equipment' : [],
             'Event' : [], 'Imbued' : [], 'Master' : [],
             'Political Action' : [], 'Power' : [], 'Reaction' : [],
             'Reflex' : [], 'Retainer' : [], 'Vampire' : [],
           }

    def __new__(cls,s):
        sName = cls.canonical(s)
        return cls.fetch(sName,CardType)

class AbstractCardAdapter(object):
    advise(instancesProvide=[IAbstractCard],asAdapterForTypes=[basestring])

    def __new__(cls,s):
        try:
            oC = AbstractCard.byName(s.encode('utf8'))
        except SQLObjectNotFound:
            oC = AbstractCard(name=s,text="")
        return oC

class RulingAdapter(object):
    advise(instancesProvide=[IRuling],asAdapterForTypes=[tuple])

    def __new__(cls,t):
        sText = t[0]
        sCode = t[1]
        try:
            oR = Ruling.byText(sText.encode('utf8'))
        except SQLObjectNotFound:
            oR = Ruling(text=sText,code=sCode)
        return oR

class AbstractCardSetAdapter(object):
    advise(instancesProvide=[IAbstractCardSet],asAdapterForTypes=[basestring])

    def __new__(cls,s):
        try:
           oS = AbstractCardSet.byName(s.encode('utf8'))
        except:
           oS = AbstractCardSet(name=s)
        return oS

class PhysicalCardSetAdapter(object):
    advise(instancesProvide=[IPhysicalCardSet],asAdapterForTypes=[basestring])

    def __new__(cls,s):
        try:
           oS = PhysicalCardSet.byName(s.encode('utf8'))
        except:
           oS = PhysicalCardSet(name=s)
        return oS

class PhysicalCardToAbstractCardAdapter(object):
    advise(instancesProvide=[IAbstractCard],asAdapterForTypes=[PhysicalCard])

    def __new__(cls,oPhysCard):
        return oPhysCard.abstractCard


