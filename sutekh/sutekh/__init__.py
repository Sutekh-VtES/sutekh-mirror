__all__ = ['AbstractCard', 'PhysicalCard', 'AbstractCardSet', 'PhysicalCardSet',
           'RarityPair', 'Expansion', 'Rarity', 'DisciplinePair', 'Discipline',
           'Clan', 'CardType', 'Ruling', 'start' ]

from SutekhObjects import *
from SutekhCli import main

def start(aArgs=['sutekh']):
    main(aArgs)
