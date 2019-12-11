# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Based on the card data published by WhiteWolf at:
#  * http://www.white-wolf.com/vtes/index.php?line=cardlist
#  * http://www.white-wolf.com/vtes/index.php?line=rulings
# pylint: disable=too-many-lines
# Don't care about the length here.

"""Data used for test cases"""
# pylint: disable=invalid-name
# don't care about naming conventions here

# Note - Yvette & Aire of Elation are deliberately duplicated, so we ensure
# that duplicates in the cardlist are handled properly

TEST_LOOKUP_LIST = """CardNames,"Ankara Citadel","The Ankara Citadel, Turkey"
CardNames,Anastaszdi Zagreb,Anastasz di Zagreb
CardNames,"Pier 13","Pier 13, Port of Baltimore"
Expansions,Jyhad,Jyhad
Expansions,VTES,VTES
Expansions,Sabbat,Sabbat
Expansions,SW,Sabbat Wars
Expansions,Anarchs,Anarchs
Expansions,CE,Camarilla Edition
Expansions,LoB,Legacy of Blood
Expansions,EK,Ebony Kingdom
Expansions,FN,Final Nights
Expansions,Third,Third Edition
Expansions,KoT,Keepers of Tradition
Expansions,HttB,Heirs to the Blood
Expansions,AH,Ancient Hearts
Expansions,LotN,Lords of the Night
Expansions,NoR,Nights of Reckoning
Expansions,Gehenna,Gehenna
Expansions,BL,Bloodlines
Expansions,BH,Black Hand
Expansions,DS,Dark Sovereigns
Expansions,KMW,Kindred Most Wanted
Expansions,BSC,Blood Shadowed Court
Expansions,Anthology,Anthology
Expansions,AnthologyI,Anthology I Reprint Set
Expansions,Tenth,Tenth Anniversary
Expansions,TR,Twilight Rebellion
Expansions,LK,Lost Kindred
Expansions,Anarchs and Alastors Storyline,Anarchs and Alastors Storyline
Expansions,Eden's Legacy Storyline,Eden's Legacy Storyline
Expansions,Black Chantry Reprint,Black Chantry
Expansions,Black Chantry,Black Chantry
Expansions,ReversePrefix:Promo-,Promo
Rarities,C,Common
Rarities,C1,Common
Rarities,C2,Common
Rarities,C3,Common
Rarities,C½,Common
Rarities,P,Precon
Rarities,V,Vampire
Rarities,V3,Vampire
Rarities,U,Uncommon
Rarities,U2,Uncommon
Rarities,U5,Uncommon
Rarities,R,Rare
Rarities,R1,Rare
Rarities,R2,Rare
Rarities,NA,Not Applicable
Rarities,BSC,BSC
Rarities,X,BSC
Rarities,A,Fixed
Rarities,B,Fixed
Rarities,1,Fixed
Rarities,3,Fixed
Rarities,A1,Fixed
Rarities,A2,Fixed
Rarities,B1,Fixed
Rarities,B2,Fixed
Rarities,Rules,Rules
Rarities,Storyline,Storyline
Rarities,Demo,Demo
Rarities,Prefix:P,Precon
CardTypes,Equipment,Equipment
CardTypes,Action,Action
CardTypes,Vampire,Vampire
CardTypes,Reaction,Reaction
CardTypes,Combat,Combat
CardTypes,Power,Power
CardTypes,Master,Master
CardTypes,Event,Event
CardTypes,Ally,Ally
CardTypes,Action Modifier,Action Modifier
CardTypes,Political Action,Political Action
CardTypes,Imbued,Imbued
CardTypes,Retainer,Retainer
CardTypes,Reflex,Reflex
CardTypes,Conviction,Conviction
Clans,Brujah,Brujah
Clans,Malk,Malkavian
Clans,Nos,Nosferatu
Clans,Tor,Toreador
Clans,Tre,Tremere
Clans,Ven,Ventrue
Clans,Caitiff,Caitiff
Clans,Abom,Abomination
Clans,Gangrel,Gangrel
Clans,Assa,Assamite
Clans,Set,Follower of Set
Clans,FoS,Follower of Set
Clans,Giov,Giovanni
Clans,Ravnos,Ravnos
Clans,Baali,Baali
Clans,DoC,Daughter of Cacophony
Clans,Garg,Gargoyle
Clans,Naga,Nagaraja
Clans,Salu,Salubri
Clans,Sam,Samedi
Clans,TBruj,True Brujah
Clans,Lasom,Lasombra
Clans,Tz,Tzimisce
Clans,!Brujah,Brujah antitribu
Clans,!Gangrel,Gangrel antitribu
Clans,!Malk,Malkavian antitribu
Clans,!Nos,Nosferatu antitribu
Clans,!Tor,Toreador antitribu
Clans,!Tre,Tremere antitribu
Clans,!Ven,Ventrue antitribu
Clans,Pan,Pander
Clans,Ahrimanes,Ahrimane
Clans,Blood Brothers,Blood Brother
Clans,BB,Blood Brother
Clans,HoS,Harbinger of Skulls
Clans,Kias,Kiasyd
Clans,!Salu,Salubri antitribu
Clans,Aku,Akunanse
Clans,Guru,Guruhi
Clans,Ish,Ishtarri
Clans,Ose,Osebo
Creeds,Avenger,Avenger
Creeds,Defender,Defender
Creeds,Innocent,Innocent
Creeds,Judge,Judge
Creeds,Martyr,Martyr
Creeds,Redeemer,Redeemer
Creeds,Visionary,Visionary
Sects,Camarilla,Camarilla
Sects,Sabbat,Sabbat
Sects,Independent,Independent
Sects,Laibon,Laibon
Sects,Anarch,Anarch
Disciplines,Abombwe,abo
Disciplines,ABO,abo
Disciplines,Animalism,ani
Disciplines,ANI,ani
Disciplines,Auspex,aus
Disciplines,AUS,aus
Disciplines,Celerity,cel
Disciplines,CEL,cel
Disciplines,Chimerstry,chi
Disciplines,CHI,chi
Disciplines,Daimoinon,dai
Disciplines,DAI,dai
Disciplines,Dementation,dem
Disciplines,DEM,dem
Disciplines,Dominate,dom
Disciplines,DOM,dom
Disciplines,Flight,fli
Disciplines,FLI,fli
Disciplines,Fortitude,for
Disciplines,FOR,for
Disciplines,Maleficia,mal
Disciplines,MAL,mal
Disciplines,Melpominee,mel
Disciplines,MEL,mel
Disciplines,Mytherceria,myt
Disciplines,MYT,myt
Disciplines,Necromancy,nec
Disciplines,NEC,nec
Disciplines,Obeah,obe
Disciplines,OBE,obe
Disciplines,Obfuscate,obf
Disciplines,OBF,obf
Disciplines,Obtenebration,obt
Disciplines,OBT,obt
Disciplines,Potence,pot
Disciplines,POT,pot
Disciplines,Presence,pre
Disciplines,PRE,pre
Disciplines,Protean,pro
Disciplines,PRO,pro
Disciplines,Quietus,qui
Disciplines,QUI,qui
Disciplines,Sanguinus,san
Disciplines,SAN,san
Disciplines,Serpentis,ser
Disciplines,SER,ser
Disciplines,Spiritus,spi
Disciplines,SPI,spi
Disciplines,Striga,str
Disciplines,STR,str
Disciplines,Temporis,tem
Disciplines,TEM,tem
Disciplines,Thanatosis,thn
Disciplines,THN,thn
Disciplines,Thaumaturgy,tha
Disciplines,THA,tha
Disciplines,Valeren,val
Disciplines,VAL,val
Disciplines,Vicissitude,vic
Disciplines,VIC,vic
Disciplines,Visceratika,vis
Disciplines,VIS,vis
Virtues,Defense,def
Virtues,Innocence,inn
Virtues,Judgment,jud
Virtues,Judgement,jud
Virtues,Martyrdom,mar
Virtues,Redemption,red
Virtues,Vengeance,ven
Virtues,Vision,vis
"""

TEST_CARD_LIST = """
Name: .44 Magnum
[Jyhad:C, VTES:C, Sabbat:C, SW:PB, CE:PTo3, LoB:PO3]
Cardtype: Equipment
Cost: 2 pool
Weapon, gun.
2R damage each strike, with an optional maneuver each combat.
Artist: Né Né Thomas; Greg Simanson

Name: AK-47
[LotN:R]
Cardtype: Equipment
Cost: 5 pool
Weapon. Gun.
2R damage each strike, with an optional maneuver ={each combat}=. When bearer strikes with this gun, he or she gets an optional additional strike this round, only usable to strike with this gun.
Artist: Franz Vohwinkel

Name: Aabbt Kindred
[FN:U2]
Cardtype: Vampire
Clan: Follower of Set
Group: 2
Capacity: 4
Discipline: for pre ser
Independent: Aabbt Kindred cannot perform (D) actions unless Nefertiti is ready. Aabbt Kindred can prevent 1 damage each combat. Aabbt Kindred are not unique and do not contest.
Artist: Lawrence Snelly

Name: Aaron Bathurst
[Third:V]
Cardtype: Vampire
Clan: Nosferatu antitribu
Group: 4
Capacity: 4
Discipline: for obf pot
Sabbat.
Artist: Rik Martin

Name: Aaron Duggan, Cameron's Toady
[Sabbat:V, SW:U]
Cardtype: Vampire
Clan: Lasombra
Group: 2
Capacity: 2
Discipline: obt
Sabbat
Artist: Eric LaCombe

Name: Aaron's Feeding Razor
[Jyhad:R, VTES:R, CE:R, KoT:R]
Cardtype: Equipment
Cost: 1 pool
Unique.
The bearer gets +1 hunt.
Artist: Thomas Nairb; Christopher Rush

Name: Abandoning the Flesh
[CE:R, Third:R]
Cardtype: Reaction/Combat
Discipline: Dementation
Only usable by a vampire being burned. Usable by a vampire in torpor.
[dem] Remove this vampire from the game instead (diablerie, if any, is still successful), and put this card into play. You may not play this card if you already have an Abandoning the Flesh in play. You may lock this card when a vampire with Dementation is bleeding to give that vampire +1 bleed for the current action.
Artist: Steve Ellis

Name: Abbot
[Third:U]
Cardtype: Action
+1 stealth action. Requires a Sabbat vampire.
Put this card on this acting Sabbat vampire and unlock him or her. This Sabbat vampire gets +1 intercept against (D) actions directed at his or her controller. A vampire may have only one Abbot.
Artist: John Bridges

Name: Abd al-Rashid
[AH:V3, FN:PA]
Cardtype: Vampire
Clan: Assamite
Group: 2
Capacity: 5
Discipline: obf CEL QUI
Independent: (Blood Cursed)
Artist: Tom Wänerstrand

Name: Abdelsobek
[LotN:U]
Cardtype: Vampire
Clan: Follower of Set
Group: 5
Capacity: 5
Discipline: for nec obf pre ser
Independent: Abdelsobek can unlock a vampire or mummy you control as a +1 stealth action.
Artist: Ken Meyer, Jr.

Name: Abebe
[LoB:U]
Cardtype: Vampire
Clan: Samedi
Group: 4
Capacity: 4
Discipline: nec obf thn
Independent.
Artist: James Stowe

Name: Abjure
[NoR:R]
Cardtype: Power
Virtue: Redemption
[COMBAT] Lock this imbued before range is determined to end a combat between a monster and a mortal. If the mortal is a minion other than this imbued, you may move a conviction to this imbued from your hand or ash heap.
Artist: Brian LeBlanc

Name: Ablative Skin
[Sabbat:R, SW:R, Third:R]
Cardtype: Action
Discipline: Fortitude
+1 stealth action.
[for] Put this card on the acting vampire and put 3 ablative counters on this card. While in combat, this vampire may remove any number of ablative counters from this card to prevent that amount of non-aggravated damage. Burn this card when it has no more ablative counters.
[FOR] As above, but this vampire may also prevent aggravated damage in combat in this way.
Artist: Richard Thomas

Name: Abombwe [abo]
[LoB:C/PA]
Cardtype: Master
Capacity: +1
Master: Discipline. Trifle.
Put this card on a Laibon or on a vampire with Protean [pro]. This vampire gains one level of Abombwe [abo]. Capacity increases by 1: the vampire is one generation older. Cannot be placed on a vampire with superior Abombwe.
Artist: Ken Meyer, Jr.

Name: Aeron
[Gehenna:U]
Cardtype: Vampire
Clan: Nosferatu antitribu
Group: 3
Capacity: 9
Discipline: aus pro ANI OBF POT
Sabbat Archbishop of London: Minions opposing Aeron in combat take an additional point of damage during strike resolution if the range is close. Once each combat, Aeron may burn a blood for a press.
Artist: Ken Meyer, Jr.

Name: Agent of Power
[LotN:C, HttB:PSam4]
Cardtype: Master
Master: Discipline. Trifle. Unique.
Put this card on a vampire you control and choose a Discipline. This vampire gains 1 level of that Discipline. Burn this card during your discard phase.
Artist: Jeff Holt

Name: Aire of Elation
[DS:C3, FN:PS3, CE:C/PTo3, Anarchs:PAB, KMW:PAn2]
Cardtype: Action Modifier
Cost: 1 blood
Discipline: Presence
You cannot play another action modifier to further increase the bleed for this action.
[pre] +1 bleed; +2 bleed if the acting vampire is Toreador.
[PRE] +2 bleed; +3 bleed if the acting vampire is Toreador.
Artist: Greg Simanson

Name: Aire of Elation
[DS:C3, FN:PS3, CE:C/PTo3, Anarchs:PAB, KMW:PAn2]
Cardtype: Action Modifier
Cost: 1 blood
Discipline: Presence
You cannot play another action modifier to further increase the bleed for this action.
[pre] +1 bleed; +2 bleed if the acting vampire is Toreador.
[PRE] +2 bleed; +3 bleed if the acting vampire is Toreador.
Artist: Greg Simanson

Name: Akram
[AH:V3, CE:PB]
Cardtype: Vampire
Clan: Brujah
Group: 2
Capacity: 8
Discipline: pot pre CEL QUI
Camarilla primogen: Once each turn after completing combat, if Akram and the opposing minion are still ready, Akram may burn 1 blood to begin another combat with the opposing minion.
Artist: Terese Nielsen

Name: Alan Sovereign
[CE:V, BSC:X]
Cardtype: Vampire
Clan: Ventrue
Group: 3
Capacity: 6
Discipline: for pre AUS DOM
Camarilla: When you play an investment card, add an additional counter to it from the blood bank.
Artist: Steve Prescott

Name: Alan Sovereign (Adv)
[Promo-20051001]
Cardtype: Vampire
Clan: Ventrue
Group: 3
Capacity: 6
Discipline: for pre AUS DOM
Advanced, Camarilla: While Alan is ready, you may pay some or all of the pool cost of equipping from any investment cards you control.
[MERGED] During your master phase, if Alan is ready, you may move a counter from any investment card to your pool.
Artist: Leif Jones

Name: Alexandra
[DS:V, CE:PTo]
Cardtype: Vampire
Clan: Toreador
Group: 2
Capacity: 11
Discipline: dom ANI AUS CEL PRE
Camarilla Inner Circle: Once during your turn, you may lock or unlock another ready Toreador. +2 bleed.
Artist: Lawrence Snelly

Name: Alfred Benezri
[CE:V, BSC:X]
Cardtype: Vampire
Clan: Pander
Group: 3
Capacity: 6
Discipline: aus dom PRE THA
Sabbat bishop: Alfred gets -1 strength in combat with an ally.
Artist: Quinton Hoover

Name: Alabástrom
[Anthology:1]
Cardtype: Vampire
Clan: Gargoyle
Group: 6
Capacity: 7
Discipline: aus cel for POT VIS
Independent anarch: If Alabástrom is ready during your turn, you can unlock another ready Gargoyle you control. Flight [FLIGHT].
Artist: Ginés Quiñonero

Name: Ambrogino Giovanni
[FN:U2]
Cardtype: Vampire
Clan: Giovanni
Group: 2
Capacity: 9
Discipline: aus DOM NEC POT THA
Independent: Ambrogino has 1 vote. +1 bleed.
Artist: Christopher Shy

Name: Amisa
[AH:V3, FN:PS]
Cardtype: Vampire
Clan: Follower of Set
Group: 2
Capacity: 8
Discipline: pre pro OBF SER
Independent: Amisa has 2 votes. Amisa can lock a vampire with a capacity above 7 as a (D) action.
Artist: Pete Venters

Name: Anarch Manifesto, An
[TR:C]
Cardtype: Equipment
Equipment.
The anarch with this equipment gets +1 stealth on actions that require an anarch. Titled non-anarch vampires get +1 strength in combat with this minion. A minion may have only one Anarch Manifesto.
Artist: Heather Kreiter

Name: Anastasz di Zagreb
[CE:V, KMW:PAl, BSC:X]
Cardtype: Vampire
Clan: Tremere
Group: 3
Capacity: 8
Discipline: ani cel dom AUS THA
Camarilla Tremere Justicar: If there are any other justicars ready, Anastasz gets 1 fewer vote from his justicar title. Anastasz may steal 1 blood as a ranged strike.
Artist: Christopher Shy

Name: Angelica, The Canonicus
[Sabbat:V, SW:PL]
Cardtype: Vampire
Clan: Lasombra
Group: 2
Capacity: 10
Discipline: cel obf DOM OBT POT
Sabbat cardinal: Once each ={action that}= Angelica attempts to block, you may burn X master cards from your hand to give her +X intercept.
Artist: John Bolton

Name: The Ankara Citadel, Turkey
[AH:U5, CE:U, KoT:U]
Cardtype: Equipment
Clan: Tremere
Cost: 2 blood
This equipment card represents a unique location and does not count as equipment while in play.
The vampire with this location pays only half of the blood cost for any cards he or she plays (round down).
Artist: Greg Simanson; Brian LeBlanc

Name: Anna "Dictatrix11" Suljic
[NoR:U]
Cardtype: Imbued
Creed: Martyr
Group: 4
Life: 6
Virtue: mar red vis
Anna may move 2 blood from the blood bank to any vampire as a +1 stealth action. During your unlock phase, you may look at the top three cards of your library.
Artist: Thomas Manning

Name: Anson
[Jyhad:V, VTES:V, Tenth:A]
Cardtype: Vampire
Clan: Toreador
Group: 1
Capacity: 8
Discipline: aus dom CEL PRE
Camarilla Prince of Seattle: If Anson is ready during your master phase, you get two master phase actions (instead of one).
Artist: Mark Tedin

Name: Ashur Tablets
[KoT:C, Anthology:3]
Cardtype: Master
Master.
Put this card in play. If you control three copies, remove all copies in play (even controlled by other Methuselahs) from the game to gain 3 pool and choose up to thirteen cards from your ash heap. Move one of those cards to your hand and shuffle the others into your library.
Artist: Sandra Chang;Ginés Quiñonero

Name: Aye
[LoB:C, EK:C½]
Cardtype: Master
Master: trifle.
Put this card on a Laibon. This Laibon may lock this card to cancel a Frenzy card p
Artist: Brad Williams

Name: Baron Dieudonne
[KoT:V/A2]
Cardtype: Vampire
Clan: Nosferatu
Group: 4
Capacity: 9
Discipline: ANI OBF POT PRO
Camarilla Prince of Brussels: After Dieudonne performs a successful action during your minion phase, he can burn 1 blood to unlock.
Artist: Tony Shasteen

Name: Bravo
[Gehenna:C]
Cardtype: Master
Master: archetype.
Put this card on a vampire you control. Once per turn, when this vampire successfully performs an action to enter combat with another, he or she gains 1 blood from the blood bank when the combat ends, if he or she is still ready. A vampire can have only one archetype.
Artist: Nilson

Name: Bronwen
[Sabbat:V, SW:PB]
Cardtype: Vampire
Clan: Brujah antitribu
Group: 2
Capacity: 10
Discipline: dom obt CEL POT PRE
Sabbat priscus: Once each combat, Bronwen may dodge as a strike.
Artist: Ken Meyer, Jr.

Name: Cedric
[LoB:U, HttB:PGar2]
Cardtype: Vampire
Clan: Gargoyle
Group: 4
Capacity: 6
Discipline: obf pot vis FOR
Camarilla. Tremere slave: If Cedric successfully blocks a (D) action, he may burn 1 blood when the action ends (after combat, if any) to unlock. Flight [FLIGHT].
Artist: David Day

Name: Cesewayo
[LoB:PO2]
Cardtype: Vampire
Clan: Osebo
Group: 4
Capacity: 10
Discipline: ani AUS CEL DOM POT THA
Laibon magaji: Once each action, Cesewayo may burn 1 blood to get +1 intercept.
Artist: Abrar Ajmal

Name: Dramatic Upheaval
[Jyhad:V, VTES:V, CE:U, Anarchs:PAB, BH:PM]
Cardtype: Political Action
Choose another Methuselah. Successful referendum means you switch places with that Methuselah. ={Added to the V:EKN banned list in 2005.}=
Artist: Heather Hudson; Mike Huddleston

Name: Earl "Shaka74" Deams
[NoR:U]
Cardtype: Imbued
Creed: Visionary
Group: 4
Life: 6
Virtue: jud mar vis
Earl gets +1 stealth on actions other than actions to enter combat. During your unlock phase, if you control more than two ready imbued, Earl burns 1 conviction [1 CONVICTION].
Artist: David Day

Name: Enkidu, The Noah
[KMW:U/PG]
Cardtype: Vampire
Clan: Gangrel antitribu
Group: 4
Capacity: 11
Discipline: for ANI CEL OBF POT PRO
Sabbat. Red List: Enkidu can enter combat with any minion as a (D) action. If Enkidu successfully performs an action to employ a retainer, he unlocks at the end of the turn. He cannot have or use equipment. +2 strength.
Artist: Mark Nelson

Name: Fidus, The Shrunken Beast
[BL:U2]
Cardtype: Vampire
Clan: Gargoyle
Group: 2
Capacity: 4
Discipline: for tha vis
Camarilla Tremere Slave: Fidus gets +1 stealth on undirected actions. -1 strength. Flight [FLIGHT].
Artist: Christopher Shy

Name: Ghoul Retainer
[Jyhad:R2, VTES:R, CE:R2, KoT:U/R]
Cardtype: Retainer
Cost: 2 pool
Ghoul with 2 life. 1 strength.
During the initial strike resolution each round, the Ghoul Retainer inflicts 1 damage or may use a weapon not used by the employing minion (or another retainer) that round (either before or after). This is not a strike, although it does count as "using" the weapon.
Artist: L. A. Williams; Richard Thomas

Name: Gracis Nostinus
[CE:V, BSC:X]
Cardtype: Vampire
Clan: Ventrue
Group: 3
Capacity: 7
Discipline: aus for DOM PRE
Camarilla Primogen: If a younger vampire attempts to block Gracis and fails, lock that vampire at the end of the action.
Artist: Max Shade Fellwalker

Name: Gypsies
[Jyhad:U, VTES:U]
Cardtype: Ally
Clan: Gangrel
Cost: 3 pool
Unique -{mortal}- with 1 life. 1 {strength}, 1 bleed.
Gypsies get +1 stealth on each of their actions.
Artist: Pete Venters

Name: Harold Zettler, Pentex Director
[Third:PM]
Cardtype: Vampire
Clan: Malkavian antitribu
Group: 4
Capacity: 9
Discipline: vic AUS DEM OBF POT
Sabbat: Giovanni get +1 bleed when bleeding you. +1 stealth.
Artist: Rik Martin

Name: Hektor
[Third:PB2]
Cardtype: Vampire
Clan: Brujah antitribu
Group: 4
Capacity: 9
Discipline: for CEL POT PRE QUI
Sabbat priscus: Damage from Hektor's hand strikes is aggravated. Baali get +1 bleed
 when bleeding you.
Artist: Abrar Ajmal

Name: High Top
[BL:R1, LoB:R]
Cardtype: Ally
Clan: Ahrimane
Cost: 4 pool
Unique werewolf with 3 life. 1 strength, 0 bleed.
High Top gets +1 intercept. High Top may enter combat with any minion controlled by another Methuselah as a (D) action. High Top gets an additional strike each round and an optional maneuver once each combat. He may play cards requiring basic Celerity [cel] as a vampire with a capacity of 4. If High Top has less than 3 life during your unlock phase, he gains 1 life.
Artist: Mark Nelson

Name: Immortal Grapple
[Jyhad:R2, VTES:R, Sabbat:U, SW:U/PB, FN:PG, CE:U/PB2, Third:U, LotN:PG2, KoT:U/PB3, HttB:PGar3]
Cardtype: Combat
Discipline: Potence
Only usable at close range before strikes are chosen. Grapple.
[pot] Strikes that are not hand strikes may not be used this round (by either combatant). A vampire may play only one Immortal Grapple each round.
[POT] As above, with an optional press. If another round of combat occurs, that round is at close range; skip the determine range step for that round.
Artist: Clint Langley; L. A. Williams; Avery Butterworth

Name: Inez "Nurse216" Villagrande
[NoR:U]
Cardtype: Imbued
Creed: Innocent
Group: 4
Life: 3
Virtue: inn
When Inez enters play, you may search your library (shuffle afterward) or hand for a power that requires innocence and put it on her.
Artist: Jim Pavelec

Name: Kabede Maru
[LotN:U]
Cardtype: Vampire
Clan: Assamite
Group: 5
Capacity: 9
Discipline: abo pot AUS CEL OBF QUI
Laibon magaji: Kabede gets +1 intercept against political actions. (The blood curse does not affect Kabede.)
Artist: Ken Meyer, Jr.

Name: Kemintiri
[KMW:U]
Cardtype: Vampire
Clan: Follower of Set
Group: 2
Capacity: 10
Level: Advanced
Discipline: aus dom OBF PRE SER THA
Advanced, Independent. Red List: +1 stealth.
[MERGED] Kemintiri has 3 votes (titled). She can play {minion} cards that require Camarilla, Ventrue, and/or a justicar title {as if she met that/those requirement(s)}.
Artist: Lawrence Snelly

Name: Lázár Dobrescu
AKA: Lazar Dobrescu
[AH:V3, FN:PR]
Cardtype: Vampire
Clan: Ravnos
Group: 2
Capacity: 3
Discipline: for
Independent: Lázár may move one blood from {an uncontrolled minion} in your prey's uncontrolled region to a vampire in your uncontrolled region as a (D) action.
Artist: Rebecca Guay

Name: Living Manse
[Sabbat:R, SW:R, Third:R]
Cardtype: Equipment
Clan: Tzimisce
Cost: 1 blood
This equipment card represents a location and does not count as an equipment card while it is in play.
The vampire with this location gets +1 bleed. He or she can burn this card before range is determined to end combat. A vampire may have only one Living Manse.
Artist: Mark Tedin

Name: Necromancy [nec]
[DS:C2, FN:PG2, LotN:PG]
Cardtype: Master
Capacity: +1
Master: Discipline.
Put this card on a vampire. This vampire gains 1 level of Necromancy [nec]. Capacity increases by 1: the vampire is one generation older. Cannot be placed on a vampire with superior Necromancy.
Artist: Anson Maddocks; Sam Araya

Name: New Blood
[Promo-20150213, Anthology:2]
Cardtype: Vampire
Clan: Blood Brother
Group: ANY
Capacity: 2
Discipline: san
Sabbat: When New Blood enters play during your influence phase, choose a circle and draw 1 card from your crypt. New Blood belongs to the chosen circle. Sterile.
Artist: Gábor Németh

Name: Off Kilter
[HttB:C/PSam2/A2]
Cardtype: Action
Clan: Samedi
+1 stealth action.
Gain 1 pool. If you do not have the Edge, you get the Edge. Otherwise, you may burn the Edge to gain 1 additional pool.
Artist: Leif Jones

Name: Ossian
[KMW:R, KoT:R]
Cardtype: Ally
Cost: 3 pool
Unique werewolf with 4 life. 2 strength, 0 bleed. Red List.
Ossian may enter combat with any vampire as a +1 stealth (D) action. In the first round of combat with a vampire who has played a card that requires Auspex [aus] during this action, that vampire cannot use any maneuvers or strikes. Ossian gains 1 life at the end of each round for each blood the opposing vampire used to heal damage or prevent destruction that round.
Artist: Roel Wielinga

Name: Pariah
[KMW:U]
Cardtype: Vampire
Clan: Abomination
Group: 2
Capacity: 6
Discipline: pot pre OBF PRO
Independent: During your master phase, discard a master card or lock Pariah. Pariah cannot take undirected actions other than hunting. He can enter combat with any minion as a (D) action. +1 strength. Scarce. Sterile.
Artist: Richard Thomas

Name: Paris Opera House
[BL:R1, LoB:R]
Cardtype: Master
Clan: Daughter of Cacophony
Cost: 2 pool
Burn Option
Master: unique location.
Lock to give a Daughter of Cacophony you control +1 stealth. Lock this card and a Daughter of Cacophony you control to give any minion +1 stealth.
Artist: William O'Connor

Name: Park Hunting Ground
[DS:C2, FN:PR, LotN:PR]
Cardtype: Master
Clan: Ravnos
Cost: 2 pool
Master: unique location. Hunting ground.
During your unlock phase, you may move 1 blood from the blood bank to a ready vampire you control. A vampire can gain blood from only one Hunting Ground card each turn.
Artist: Pete Venters; Sam Araya

Name: The Path of Blood
[AH:C2, FN:PA, LotN:PA2]
Cardtype: Master
Clan: Assamite
Cost: 1 pool
Unique master.
Put this card in play. Cards that require Quietus [qui] {cost Assamites 1 less blood}. Any minion may burn this card as a (D) action; if that minion is a vampire, he or she then takes 1 unpreventable damage when this card is burned.
Artist: Drew Tucker; Jeff Holt

Name: Pier 13, Port of Baltimore
[SW:U/PB, Third:U, KoT:U]
Cardtype: Equipment
Cost: 2 blood
This equipment card represents a unique location and does not count as equipment while in play.
During your influence phase, this minion may equip with a non-location, non-unique equipment card from your hand (requirements and cost apply as normal). This is not an action and cannot be blocked.
Artist: Steve Prescott

Name: Political Hunting Ground
[Sabbat:U, SW:U/PL, HttB:PKia]
Cardtype: Master
Clan: Lasombra
Cost: 2 pool
Master: unique location. Hunting ground.
During your unlock phase, you may move 1 blood from the bank to a ready vampire you control. A vampire can gain blood from only one hunting ground card each turn.
Artist: John Scotello; Melissa Uran

Name: Predator's Communion
[LoB:C]
Cardtype: Reaction
Discipline: Abombwe
[abo] [REFLEX] Cancel a frenzy card played on this vampire as it is played.
[abo] +1 intercept. Only usable when a vampire is acting.
[ABO] Only usable by a locked vampire when a vampire is acting. This reacting vampire unlocks.
Artist: David Day

Name: Protracted Investment
[Jyhad:C, VTES:C, CE:PTr]
Cardtype: Master
Cost: 2 pool
Master. Investment.
{Put this card in play and} move 5 blood from the blood bank to this card. You may use a master phase action to move 1 blood from this card to your pool. Burn this card when all blood has been removed.
Artist: Brian Snoddy

Name: Raven Spy
[Jyhad:U, VTES:U, CE:U/PN, Anarchs:PG2, BH:PN3, KMW:PG, Third:PTz3, LotN:PR3, KoT:U]
Cardtype: Retainer
Cost: 1 blood
Discipline: Animalism
Animal with 1 life.
[ani] This minion gets +1 intercept.
[ANI] As above, but the Raven Spy has 2 life.
Artist: Jeff Holt; Dan Frazier

Name: Rebekka, Chantry Elder of Munich
[DS:V, CE:PTr]
Cardtype: Vampire
Clan: Tremere
Group: 2
Capacity: 8
Discipline: pot AUS PRE THA
Camarilla: Rebekka gets +1 stealth on each of her actions. Rebekka gets +1 bleed when bleeding a Methuselah who controls a ready Malkavian.
Artist: Anson Maddocks

Name: Rock Cat
[BL:R1, LoB:R, HttB:PGar]
Cardtype: Ally
Clan: Gargoyle
Cost: 4 pool
Gargoyle creature with 4 life. 3 strength, 0 bleed.
Rock Cat may enter combat with a ready minion as a (D) action. Opposing vampires with capacity 3 or less cannot strike in the first round. Rock Cat gets an optional press each combat. Rock Cat may play cards requiring basic Potence [pot] as a 3-capacity vampire.
Artist: Jeff Holt

Name: Scapelli, The Family "Mechanic"
[DS:U2]
Cardtype: Ally
Clan: Giovanni
Cost: 3 pool
Unique -{mortal}- with 3 life. {0 strength}, 1 bleed.
{Scapelli may strike for 2R damage.} Once each combat, Scapelli may press to continue combat.
Artist: Richard Thomas

Name: Shade
[Sabbat:U, SW:PL]
Cardtype: Retainer
Cost: 1 blood
Discipline: Obtenebration
-{Demon}- with 2 life.
[obt] When the minion with this retainer is in combat, the opposing minion takes 1 damage during strike resolution {if the range is close}.
[OBT] As above, but Shade has 3 life.
Artist: Stuart Beel

Name: Sha-Ennu
[Third:V]
Cardtype: Vampire
Clan: Tzimisce
Group: 4
Capacity: 11
Discipline: obf tha ANI AUS CHI VIC
Sabbat regent: Vampires with capacity less than 4 cannot block Sha-Ennu. +2 bleed.
Artist: Richard Thomas

Name: Sheela Na Gig
[LK:2]
Cardtype: Vampire
Clan: Gargoyle
Group: 5
Capacity: 2
Discipline: vis
Sabbat: Sheela Na Gig can lock to give a Tremere antitribu you control +1 bleed. Flight [FLIGHT]. Tremere antitribu slave.
Artist: Noah Hirka

Name: Swallowed by the Night
[Third:C]
Cardtype: Action Modifier/Combat
Discipline: Obfuscate
[obf] [ACTION MODIFIER] +1 stealth.
[OBF] [COMBAT] Maneuver.
Artist: Thea Maia; Tom Biondillo

Name: The Siamese
[BL:U2]
Cardtype: Vampire
Clan: Ahrimane
Group: 2
Capacity: 7
Discipline: ani pro PRE SPI
Sabbat: +1 bleed. Sterile.
Artist: Lawrence Snelly

Name: The Slaughterhouse
[BL:C1, LoB:C]
Cardtype: Master
Clan: Harbinger of Skulls
Cost: 1 pool
Burn Option
Master: location.
Lock to burn two cards from the top of your prey's library.
Artist: William O'Connor

Name: Two Wrongs
[Promo-20081119]
Cardtype: Master
Master: out-of-turn. Trifle.
Play when a minion controlled by a Methuselah other than your predator is bleeding you -{after blocks are declined}-. That minion is now bleeding his or her prey. The next card that would change the target of this bleed is canceled as it is played.
Artist: Leif Jones

Name: Vox Domini
[BH:R, LoB:PA]
Cardtype: Master
Cost: 1 pool
Master: out-of-turn.
Only usable during the referendum of a political action. Not usable on a referendum that is automatically passing. The referendum fails. Each Methuselah may play only one Vox Domini each game.
Artist: Christopher Shy

Name: Yvette, The Hopeless
[CE:V/PTo, BSC:X]
Cardtype: Vampire
Clan: Toreador
Group: 3
Capacity: 3
Discipline: aus cel
Camarilla.
Artist: Leif Jones

Name: Hide the Heart
[HttB:C/B2/PSal2]
Cardtype: Reaction
Discipline: Valeren / Auspex

[aus] Reduce a bleed against you by 1.
[val] The action ends (unsuccessfully). The acting minion may burn 1 blood to cancel this card as it is played. Only one Hide the Heart may be played at [val] each action.
[VAL] Reduce a bleed against you by 2, or lock to reduce a bleed against any Methuselah by 2.
Artist: Kari Christensen

Name: Walk of Flame
[Jyhad:U2, VTES:U, Sabbat:U, CE:C/PTr3, BH:PTr2, Third:C/PTr4, KoT:C]
Cardtype: Combat
Discipline: Thaumaturgy
Not usable on the first round of combat.
[tha] Strike: 1R aggravated damage.
[THA] Strike: 2R aggravated damage.
Artist: Scott Fischer; Richard Thomas

Name: Anarch Railroad
[Anarchs:R2]
Cardtype: Master
Cost: 2 pool
Master: unique location.
Lock to give an anarch +1 stealth for the current action.
Artist: Joel Biske

Name: Anarch Revolt
[Jyhad:U, VTES:U, CE:U, Anarchs:PAB2, KMW:PAn, Third:U]
Cardtype: Master
Master.
Put this card in play. A Methuselah who does not control a ready anarch burns 1 pool during his or her unlock phase. Any vampire can call a referendum to burn this card as a +1 stealth political action.
Artist: Pete Venters; Steve Prescott

Name: Anarch Railroad
[Anarchs and Alastors Storyline]

Name: Anarch Revolt
[Anarchs and Alastors Storyline]

Name: Smite
[NoR:R]
Cardtype: Combat
Cost: 3 Conviction
Virtue: Vengeance
{Strike:} strength+1 aggravated ranged damage. Even if the strike is dodged, burn any electronic equipment (e.g., IR Goggles, Laptop Computer, or Phased Motion Detector) on either combatant.
Artist: Heather Kreiter

Name: Motivated by Gehenna
[Eden's Legacy Storyline:Storyline]
Cardtype: Master
Master.
Put this card in play, If you control the Edge, any vampire you control may enter combat with a ready minion controlled by another Methuselah as a (D) action that costs 1 blood.  {NOT FOR LEGAL PLAY}
Artist: Brian LeBlanc

Name: Étienne Fauberge
AKA: Etienne Fauberge
[Anarchs:U2]
Cardtype: Vampire
Clan: Ravnos
Group: 3
Capacity: 8
Discipline: ANI CEL CHI FOR
Independent: Other Methuselahs' actions targeting Etienne cost 1 additional blood. When in combat with Baali or Followers of Set, Etienne's hand damage is aggravated.
Artist: Jeff Holt
"""

TEST_EXP_INFO = """
{
  "TR": {
    "None": {
      "date": "2008-05-28",
      "back": "VtES"
    }
  },
  "HttB": {
    "None": {
      "date": "2010-02-03",
      "back": "VtES"
    },
    "No Draft Text": {
      "date": "2010-02-03",
      "cards": [
        "Off Kilter"
      ],
      "back": "VtES"
    }
  },
  "Jyhad": {
    "None": {
      "date": "1994-08-16",
      "back": "Jyhad"
    },
    "Variant Printing": {
      "date": "1994-08-16",
      "cards": [
        "Ghoul Retainer",
        "Immortal Grapple",
        "Walk of Flame"
      ],
      "back": "Jyhad"
    }
  },
  "KoT": {
    "None": {
      "date": "2008-11-19",
      "back": "VtES"
    },
    "No Draft Text": {
      "date": "2008-11-19",
      "cards": [
        "Immortal Grapple"
      ],
      "back": "VtES"
    }
  },
  "SW": {
    "Second Printing": {
      "date": "2001-01-12",
      "cards": [
        "Immortal Grapple"
      ],
      "back": "VtES"
    },
    "None": {
      "date": "2000-10-31",
      "back": "VtES"
    }
  },
  "Anthology": {
    "None": {
      "date": "2017-05-11",
      "back": "VEKN"
    }
  },
  "Third": {
    "None": {
      "date": "2006-09-04",
      "back": "Third Edition"
    },
    "No Draft Text": {
      "date": "2006-09-04",
      "cards": [
        "Swallowed by the Night",
        "Walk of Flame"
      ],
      "back": "Third Edition"
    },
    "Sketch": {
      "date": "2006-09-04",
      "cards": [
        "Harold Zettler, Pentex Director",
        "Hektor"
      ],
      "back": "Third Edition"
    }
  },
  "Anarchs and Alastors Storyline": {
    "None": {
      "date": "2008-08-10",
      "back": "VtES"
    }
  }
}
"""

TEST_RULINGS = """
<html>
<head><title>Sutekh Test Rulings</title></head>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<body id="page_bg">
    <div id="pillmenu"><ul class="menu"><li class="item5"><a href="http://www.vekn.net/"><span>Home</span></a></li><li class="item2"><a href="/index.php/forum/index"><span>Forum</span></a></li><li class="item117"><a href="/index.php/event-calendar"><span>Event Calendar</span></a></li></ul><form action="http://www.vekn.net/index.php/component/comprofiler/login" method="post" id="mod_loginform" class="cbLoginForm" style="margin:0px;">

<tr>
<td valign="top">

<p><b>AK-47:</b></p>
<ul>
<li>The AK-47 provides the bearer one optional maneuver "each combat". <a target="_top" href="http://groups-beta.google.com/groups?selm=46FCEF4C.6050100%40white-wolf.com">[LSJ 20070928]</a></li>
</ul>

<p><b>Ablative Skin:</b></p>
<ul>
<li>Cannot be used to prevent damage that cannot be prevented by cards that require Fortitude (e.g., Blood Rage and Blood Fury). <a target="_top" href="http://groups-beta.google.com/groups?selm=36C98715.81740A4B%40wizards.com">[LSJ 19990216]</a></li>
</ul>

<p><b>Lazar Dobrescu:</b></p>
<ul>
<li>Cannot use his special ability if his controller has no vampires in her uncontrolled region. <a target="_top" href="http://groups-beta.google.com/groups?selm=36C82B01.3705D2F0%40wizards.com">[LSJ 19990215]</a></li>
</ul>

</body></html>
"""
