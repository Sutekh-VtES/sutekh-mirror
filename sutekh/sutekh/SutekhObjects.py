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

# Table Objects

class AbstractCard(SQLObject):
    advise(instancesProvide=[IAbstractCard])

    name = StringCol(alternateID=True,length=50)
    text = StringCol(length=512)
    group = IntCol(default=None,dbName='grp')
    capacity = IntCol(default=None)
    cost = IntCol(default=None)
    costtype = EnumCol(enumValues=['pool','blood',None],default=None)
    
    discipline = RelatedJoin('DisciplinePair',intermediateTable='abs_discipline_pair_map')
    rarity = RelatedJoin('RarityPair',intermediateTable='abs_rarity_pair_map')
    clan = RelatedJoin('Clan',intermediateTable='abs_clan_map')
    cardtype = RelatedJoin('CardType',intermediateTable='abs_type_map')
    sets = RelatedJoin('AbstractCardSet',intermediateTable='abstract_map')
    
class PhysicalCard(SQLObject):
    advise(instancesProvide=[IPhysicalCard])

    abstractCard = ForeignKey('AbstractCard')
    sets = RelatedJoin('PhysicalCardSet',intermediateTable='physical_map')
    
class AbstractCardSet(SQLObject):
    advise(instancesProvide=[IAbstractCardSet])

    name = StringCol(alternateID=True,length=50)
    cards = RelatedJoin('AbstractCard',intermediateTable='abstract_map')
    
class PhysicalCardSet(SQLObject):
    advise(instancesProvide=[IPhysicalCardSet])

    name = StringCol(alternateID=True,length=50)
    cards = RelatedJoin('PhysicalCard',intermediateTable='physical_map')

class RarityPair(SQLObject):
    advise(instancesProvide=[IRarityPair])

    expansion = ForeignKey('Expansion')
    rarity = ForeignKey('Rarity')
    cards = RelatedJoin('AbstractCard',intermediateTable='abs_rarity_pair_map')
    expansionRarityIndex = DatabaseIndex(expansion,rarity,unique=True)
    
class Expansion(SQLObject):
    advise(instancesProvide=[IExpansion])

    name = StringCol(alternateID=True,length=20)
    
class Rarity(SQLObject):
    advise(instancesProvide=[IRarity])

    name = StringCol(alternateID=True,length=20)

class DisciplinePair(SQLObject):
    advise(instancesProvide=[IDisciplinePair])

    discipline = ForeignKey('Discipline')
    level = EnumCol(enumValues=['inferior','superior'])
    disciplineLevelIndex = DatabaseIndex(discipline,level,unique=True)
    cards = RelatedJoin('AbstractCard',intermediateTable='abs_discipline_pair_map')

class Discipline(SQLObject):
    advise(instancesProvide=[IDiscipline])

    name = StringCol(alternateID=True,length=30)

class Clan(SQLObject):
    advise(instancesProvide=[IClan])
    
    name = StringCol(alternateID=True,length=40)
    cards = RelatedJoin('AbstractCard',intermediateTable='abs_clan_map')

class CardType(SQLObject):
    advise(instancesProvide=[ICardType])
    
    name = StringCol(alternateID=True,length=50)
    cards = RelatedJoin('AbstractCard',intermediateTable='abs_type_map')
    
ObjectList = [ AbstractCard, PhysicalCard, AbstractCardSet, PhysicalCardSet,
               RarityPair, Expansion, Rarity, DisciplinePair, Discipline,
               Clan, CardType ]

# Adapters

class ExpansionAdapter(object):
    advise(instancesProvide=[IExpansion],asAdapterForTypes=[basestring])

    dKey = { 'Jyhad' : [],
             'VTES' : [],
             'Sabbat' : [],
             'Sabbat Wars' : ['SW'],
             'Camarilla Edition' : ['CE'],
             'Final Nights' : ['FN'],
             'Ancient Hearts' : ['AH'],
             'Gehenna' : [],
             'Bloodlines' : ['BL'],
             'Blackhand' : ['BH'],
             'Dark Sovereigns' : ['DS'],
             'Kindred Most Wanted' : ['KMW'],
             'Tenth Anniversary' : ['Tenth'],
             'Anarchs' : [],             
           }
    
    dLook = {}
    for sKey, aAlts in dKey.iteritems():
        dLook[sKey] = sKey
        for sAlt in aAlts:
            dLook[sAlt] = sKey
    
    def __new__(cls,s):
        if s.startswith('Promo-'):
            sCanonical = s
        else:
            sCanonical = cls.dLook[s]
        try:
            oE = Expansion.byName(sCanonical)
        except:
            oE = Expansion(name=sCanonical)
        return oE
    
class RarityAdapter(object):
    advise(instancesProvide=[IRarity],asAdapterForTypes=[basestring])

    dKey = { 'Common' : ['C','C1','C2','C3'],
             'Uncommon' : ['U','U1','U2','U3','U5'],
             'Rare' : ['R','R1','R2','R3'],
             'Vampire' : ['V','V1','V2','V3'],
             'Tenth': ['A','B'],
             'Precon' : ['PB','PA','PTo3','PTr','PG','PB2','PTo4','PAl2'],
             'Not Applicable' : ['NA'],
           }
    
    dLook = {}
    for sKey, aAlts in dKey.iteritems():
        dLook[sKey] = sKey
        for sAlt in aAlts:
            dLook[sAlt] = sKey
    
    def __new__(cls,s):
        if s.startswith('P'):
            sCanonical = 'Precon'
        else:
            sCanonical = cls.dLook[s]
        try:
            oR = Rarity.byName(sCanonical)
        except:
            oR = Rarity(name=sCanonical)
        return oR

class RarityPairAdapter(object):
    advise(instancesProvide=[IRarityPair],asAdapterForTypes=[tuple])
    
    def __new__(cls,t):
        oE = IExpansion(t[0])
        oR = IRarity(t[1])
        try:
            aRes = list(RarityPair.selectBy(expansion=oE,rarity=oR))
            if len(aRes) != 1:
                raise TypeError
            oP = aRes[0]    
        except:
            oP = RarityPair(expansion=oE,rarity=oR)
        return oP

class DisciplineAdapter(object):
    advise(instancesProvide=[IDiscipline],asAdapterForTypes=[basestring])

    dKey = { 'ani' : ['ANI','Animalism'],
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
           }
           
    dLook = {}
    for sKey, aAlts in dKey.iteritems():
        dLook[sKey] = sKey
        for sAlt in aAlts:
            dLook[sAlt] = sKey

    def __new__(cls,s):
        sCanonical = cls.dLook[s]
        try:
            oD = Discipline.byName(sCanonical)
        except:
            oD = Discipline(name=sCanonical)
        return oD

class ClanAdapter(object):
    advise(instancesProvide=[IClan],asAdapterForTypes=[basestring])
    
    dKey = { 'Follower of Set' : [], 'Toreador' : [],
             'Lasombra' : [], 'Gangrel' : [], 'Caitiff' : [],
             'Assamite' : [], 'Ravnos' : [], 'Harbinger of Skulls' : [],
             'Tremere' : [], 'Giovanni' : [], 'Ventrue' : [],
             'Malkavian' : [], 'Salubri' :[], 'Pander' : [],
             'Brujah' : [], 'Nosferatu' : [], 'Abomination' : [],
             'Tzimisce' : [], 'Daughter of Cacophony' : [], 'Baali' : [],
             'Samedi' : [], 'Blood Brother' : [], 'Kiasyd' : [],
             'Ahrimanes' : [], 'Gargoyle' : [], 'Nagaraja' : [],
             'True Brujah' : [],
           }
           
    dLook = {}
    for sKey, aAlts in dKey.iteritems():
        dLook[sKey] = sKey
        dLook[sKey + ' antitribu'] = sKey + ' antitribu'
        for sAlt in aAlts:
            dLook[sAlt] = sKey

    def __new__(cls,s):
        sCanonical = cls.dLook[s]
        try:
            oC = Clan.byName(sCanonical)
        except:
            oC = Clan(name=sCanonical)
        return oC

class CardTypeAdapter(object):
    advise(instancesProvide=[ICardType],asAdapterForTypes=[basestring])
    
    dKey = { 'Action' : [], 'Action Modifier' : [], 'Combat' : [],
             'Reaction' : [], 'Ally' : [], 'Equipment' : [], 'Event' : [],
             'Master' : [], 'Political Action' : [], 'Retainer' : [],
             'Vampire' : []
           }
    
    dLook = {}
    for sKey, aAlts in dKey.iteritems():
        dLook[sKey] = sKey
        for sAlt in aAlts:
            dLook[sAlt] = sKey

    def __new__(cls,s):
        sCanonical = cls.dLook[s]
        try:
            oC = CardType.byName(sCanonical)
        except:
            oC = CardType(name=sCanonical)
        return oC
    
