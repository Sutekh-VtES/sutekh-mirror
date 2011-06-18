# TestData.py
# -*- coding: cp1252 -*-
# vim:fileencoding=cp1252 ai ts=4 sts=4 et sw=4
# Based on the card data published by WhiteWolf at:
#  * http://www.white-wolf.com/vtes/index.php?line=cardlist
#  * http://www.white-wolf.com/vtes/index.php?line=rulings

"""Data used for test cases"""
# pylint: disable-msg=C0103
# don't care about naming conventions here

# Note - Yvette & Aire of Elation are deliberately duplicated, so we ensure
# that duplicates in the cardlist are handled properly

TEST_CARD_LIST = """
<html>
<head><title>Sutekh Test Cards</title></head>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<body>
<table>
<tr><td>

<p>
<a name="card_1"><span class="cardname">.44 Magnum</span></a>
<span class="exp">[Jyhad:C, VTES:C, Sabbat:C, SW:PB, CE:PTo3, LoB:PO3]</span><br />
<table><tr><td><span class="key">Cardtype:</span> </td><td>Equipment<br /></td></tr>
<tr><td><span class="key">Cost:</span> </td><td>2 pool<br /></td></tr>
<tr><td colspan=2><b>Weapon, gun.</b><br />
<n>2R damage each strike, with an optional maneuver each combat.<br />
<tr><td><span class="key">Artist:</span> </td><td>Né Né Thomas; Greg Simanson<br /></td></tr>
</table>
</p>
<p>
<a name="card_2"><span class="cardname">AK-47</span></a>
<span class="exp">[LotN:R]</span><br />
<table><tr><td><span class="key">Cardtype:</span> </td><td>Equipment<br /></td></tr>
<tr><td><span class="key">Cost:</span> </td><td>5 pool<br /></td></tr>
<tr><td colspan=2><b>Weapon. Gun.</b><br />
<n>2R damage each strike, with an optional maneuver <span class="errata">{each combat}</span>. When bearer strikes with this gun, he or she gets an optional additional strike this round, only usable to strike with this gun.<br />
<tr><td><span class="key">Artist:</span> </td><td>Franz Vohwinkel<br /></td></tr>
</table>
</p>
<p>
<a name="card_3"><span class="cardname">Aabbt Kindred</span></a>
<span class="exp">[FN:U2]</span><br />
<table><tr><td><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td><span class="key">Clan:</span> </td><td>Follower of Set<br /></td></tr>
<tr><td><span class="key">Group:</span> </td><td>2<br /></td></tr>
<tr><td><span class="key">Capacity:</span> </td><td>4<br /></td></tr>
<tr><td><span class="key">Discipline:</span> </td><td>for pre ser<br /></td></tr>
<tr><td colspan=2><b>Independent:</b> <n>Aabbt Kindred cannot perform (D) actions unless Nefertiti is ready. Aabbt Kindred can prevent 1 damage each combat. Aabbt Kindred are not unique and do not contest.<br />
<tr><td><span class="key">Artist:</span> </td><td>Lawrence Snelly<br /></td></tr>
</table>
</p>
<p>
<a name="card_4"><span class="cardname">Aaron Bathurst</span></a>
<span class="exp">[Third:V]</span><br />
<table><tr><td><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td><span class="key">Clan:</span> </td><td>Nosferatu antitribu<br /></td></tr>
<tr><td><span class="key">Group:</span> </td><td>4<br /></td></tr>
<tr><td><span class="key">Capacity:</span> </td><td>4<br /></td></tr>
<tr><td><span class="key">Discipline:</span> </td><td>for obf pot<br /></td></tr>
<tr><td colspan=2><b>Sabbat.</b><br />
<tr><td><span class="key">Artist:</span> </td><td>Rik Martin<br /></td></tr>
</table>
</p>
<p>
<a name="card_5"><span class="cardname">Aaron Duggan, Cameron's Toady</span></a>
<span class="exp">[Sabbat:V, SW:U]</span><br />
<table><tr><td><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td><span class="key">Clan:</span> </td><td>Lasombra<br /></td></tr>
<tr><td><span class="key">Group:</span> </td><td>2<br /></td></tr>
<tr><td><span class="key">Capacity:</span> </td><td>2<br /></td></tr>
<tr><td><span class="key">Discipline:</span> </td><td>obt<br /></td></tr>
<tr><td colspan=2><b>Sabbat</b><br />
<tr><td><span class="key">Artist:</span> </td><td>Eric LaCombe<br /></td></tr>
</table>
</p>
<p>
<a name="card_6"><span class="cardname">Aaron's Feeding Razor</span></a>
<span class="exp">[Jyhad:R, VTES:R, CE:R]</span><br />
<table><tr><td><span class="key">Cardtype:</span> </td><td>Equipment<br /></td></tr>
<tr><td><span class="key">Cost:</span> </td><td>1 pool<br /></td></tr>
<tr><td colspan=2><b>Unique equipment.</b><br />
<n>If the vampire with this equipment successfully hunts, he or she gains 1 additional blood.<br />
<tr><td><span class="key">Artist:</span> </td><td>Thomas Nairb; Christopher Rush<br /></td></tr>
</table>
</p>
<p>
<a name="card_7"><span class="cardname">Abandoning the Flesh</span></a>
<span class="exp">[CE:R, Third:R]</span><br />
<table><tr><td><span class="key">Cardtype:</span> </td><td>Reaction/Combat<br /></td></tr>
<tr><td><span class="key">Discipline:</span> </td><td>Dementation<br /></td></tr>
<tr><td colspan=2><b>Only usable by a vampire being burned. Usable by a vampire in torpor.</b><br />
<n>[dem] Remove this vampire from the game instead (diablerie, if any, is still successful), and put this card into play. You may not play this card if you already have an Abandoning the Flesh in play. You may tap this card when a vampire with Dementation is bleeding to give that vampire +1 bleed for the current action.<br />
<tr><td><span class="key">Artist:</span> </td><td>Steve Ellis<br /></td></tr>
</table>
</p>
<p>
<a name="card_8"><span class="cardname">Abbot</span></a>
<span class="exp">[Third:U]</span><br />
<table><tr><td><span class="key">Cardtype:</span> </td><td>Action<br /></td></tr>
<tr><td colspan=2><b>+1 stealth action. Requires a Sabbat vampire.</b><br />
<n>Put this card on this acting Sabbat vampire and untap him or her. This Sabbat vampire gets +1 intercept against (D) actions directed at his or her controller. A vampire may have only one Abbot.<br />
<tr><td><span class="key">Artist:</span> </td><td>John Bridges<br /></td></tr>
</table>
</p>
<p>
<a name="card_9"><span class="cardname">Abd al-Rashid</span></a>
<span class="exp">[AH:V3, FN:PA]</span><br />
<table><tr><td><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td><span class="key">Clan:</span> </td><td>Assamite<br /></td></tr>
<tr><td><span class="key">Group:</span> </td><td>2<br /></td></tr>
<tr><td><span class="key">Capacity:</span> </td><td>5<br /></td></tr>
<tr><td><span class="key">Discipline:</span> </td><td>obf CEL QUI<br /></td></tr>
<tr><td colspan=2><b>Independent:</b> <n>(Blood Cursed)<br />
<tr><td><span class="key">Artist:</span> </td><td>Tom Wänerstrand<br /></td></tr>
</table>
</p>
<p>
<a name="card_10"><span class="cardname">Abdelsobek</span></a>
<span class="exp">[LotN:U]</span><br />
<table><tr><td><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td><span class="key">Clan:</span> </td><td>Follower of Set<br /></td></tr>
<tr><td><span class="key">Group:</span> </td><td>5<br /></td></tr>
<tr><td><span class="key">Capacity:</span> </td><td>5<br /></td></tr>
<tr><td><span class="key">Discipline:</span> </td><td>for nec obf pre ser<br /></td></tr>
<tr><td colspan=2><b>Independent:</b> <n>Abdelsobek can untap a vampire or mummy you control as a +1 stealth action.<br />
<tr><td><span class="key">Artist:</span> </td><td>Ken Meyer, Jr.<br /></td></tr>
</table>
</p>
<p>
<a name="card_11"><span class="cardname">Abebe</span></a>
<span class="exp">[LoB:U]</span><br />
<table><tr><td><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td><span class="key">Clan:</span> </td><td>Samedi<br /></td></tr>
<tr><td><span class="key">Group:</span> </td><td>4<br /></td></tr>
<tr><td><span class="key">Capacity:</span> </td><td>4<br /></td></tr>
<tr><td><span class="key">Discipline:</span> </td><td>nec obf thn<br /></td></tr>
<tr><td colspan=2><b>Independent.</b><br />
<tr><td><span class="key">Artist:</span> </td><td>James Stowe<br /></td></tr>
</table>
</p>
<p>
<a name="card_12"><span class="cardname">Abjure</span></a>
<span class="exp">[NoR:R]</span><br />
<table><tr><td><span class="key">Cardtype:</span> </td><td>Power<br /></td></tr>
<tr><td><span class="key">Virtue:</span> </td><td>Redemption<br /></td></tr>
<tr><td colspan=2><n>[COMBAT] Tap this imbued before range is determined to end a combat between a monster and a mortal. If the mortal is a minion other than this imbued, you may move a conviction to this imbued from your hand or ash heap.<br />
<tr><td><span class="key">Artist:</span> </td><td>Brian LeBlanc<br /></td></tr>
</table>
</p>
<p>
<a name="card_13"><span class="cardname">Ablative Skin</span></a>
<span class="exp">[Sabbat:R, SW:R, Third:R]</span><br />
<table><tr><td><span class="key">Cardtype:</span> </td><td>Action<br /></td></tr>
<tr><td><span class="key">Discipline:</span> </td><td>Fortitude<br /></td></tr>
<tr><td colspan=2><b>+1 stealth action.</b><br />
<n>[for] Put this card on the acting vampire and put 3 ablative counters on this card. While in combat, this vampire may remove any number of ablative counters from this card to prevent that amount of non-aggravated damage. Burn this card when it has no more ablative counters.<br />
<b>[FOR] As above, but this vampire may also prevent aggravated damage in combat in this way.</b><br />
<tr><td><span class="key">Artist:</span> </td><td>Richard Thomas<br /></td></tr>
</table>
</p>
<p>
<a name="card_14"><span class="cardname">Abombwe [abo]</span></a>
<span class="exp">[LoB:C/PA]</span><br />
<table><tr><td><span class="key">Cardtype:</span> </td><td>Master<br /></td></tr>
<tr><td><span class="key">Capacity:</span> </td><td>+1<br /></td></tr>
<tr><td colspan=2><b>Master: Discipline. Trifle.</b><br />
<n>Put this card on a Laibon or on a vampire with Protean [pro]. This vampire gains one level of Abombwe [abo]. Capacity increases by 1: the vampire is one generation older. Cannot be placed on a vampire with superior Abombwe.<br />
<tr><td><span class="key">Artist:</span> </td><td>Ken Meyer, Jr.<br /></td></tr>
</table>
</p>

<p>
<a name="Aeron"><span class="cardname">Aeron</span></a>
<span class="exp">[Gehenna:U]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Nosferatu antitribu<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>3<br /></td></tr>
<tr><td width=1><span class="key">Capacity:</span> </td><td>9<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>aus pro ANI OBF POT<br /></td></tr>
<tr><td colspan=2><b>Sabbat Archbishop of London:</b> <n>Minions opposing Aeron in combat take an additional point of damage during strike resolution if the range is close. Once each combat, Aeron may burn a blood for a press.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Ken Meyer, Jr.<br /></td></tr>
</table>
</p>

<p>
<a name="Aire_of_Elation"><span class="cardname">Aire of Elation</span></a>
<span class="exp">[DS:C3, FN:PS3, CE:C/PTo3, Anarchs:PAB, KMW:PAn2]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Action Modifier<br /></td></tr>
<tr><td width=1><span class="key">Cost:</span> </td><td>1 blood<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>Presence<br /></td></tr>
<tr><td colspan=2><b>You cannot play another action modifier to further increase the bleed for this action.</b><br />
<n>[pre] +1 bleed; +2 bleed if the acting vampire is Toreador.<br />
<b>[PRE] +2 bleed; +3 bleed if the acting vampire is Toreador.</b><br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Greg Simanson<br /></td></tr>
</table>
</p>

<p>
<a name="Aire_of_Elation"><span class="cardname">Aire of Elation</span></a>
<span class="exp">[DS:C3, FN:PS3, CE:C/PTo3, Anarchs:PAB, KMW:PAn2]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Action Modifier<br /></td></tr>
<tr><td width=1><span class="key">Cost:</span> </td><td>1 blood<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>Presence<br /></td></tr>
<tr><td colspan=2><b>You cannot play another action modifier to further increase the bleed for this action.</b><br />
<n>[pre] +1 bleed; +2 bleed if the acting vampire is Toreador.<br />
<b>[PRE] +2 bleed; +3 bleed if the acting vampire is Toreador.</b><br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Greg Simanson<br /></td></tr>
</table>
</p>

<p>
<a name="Akram"><span class="cardname">Akram</span></a>
<span class="exp">[AH:V3, CE:PB]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Brujah<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>2<br /></td></tr>
<tr><td width=1><span class="key">Capacity:</span> </td><td>8<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>pot pre CEL QUI<br /></td></tr>
<tr><td colspan=2><b>Camarilla primogen:</b> <n>Once each turn after completing combat, if Akram and the opposing minion are still ready, Akram may burn 1 blood to begin another combat with the opposing minion.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Terese Nielsen<br /></td></tr>
</table>
</p>

<p>
<a name="Alan_Sovereign"><span class="cardname">Alan Sovereign</span></a>
<span class="exp">[CE:V, BSC:X]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Ventrue<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>3<br /></td></tr>
<tr><td width=1><span class="key">Capacity:</span> </td><td>6<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>for pre AUS DOM<br /></td></tr>
<tr><td colspan=2><b>Camarilla:</b> When you play an investment card, add an additional counter to it from the blood bank.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Steve Prescott<br /></td></tr>
</table>
</p>

<p>
<a name="Alan_Sovereign_2"><span class="cardname">Alan Sovereign</span></a>
<span class="exp">[Promo-20051001]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Ventrue<br /></td></tr>
<tr><td width=1><span class="key">Level:</span> </td><td>Advanced<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>3<br /></td></tr>
<tr><td width=1><span class="key">Capacity:</span> </td><td>6<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>for pre AUS DOM<br /></td></tr>
<tr><td colspan=2><b>Advanced, Camarilla:</b> While Alan is ready, you may pay some or all of the pool cost of equipping from any investment cards you control.<br />
[MERGED] During your master phase, if Alan is ready, you may move a counter from any investment card to your pool.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Leif Jones<br /></td></tr>
</table>
</p>

<p>
<a name="Alexandra"><span class="cardname">Alexandra</span></a>
<span class="exp">[DS:V, CE:PTo]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Toreador<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>2<br /></td></tr>
<tr><td width=1><span class="key">Capacity:</span> </td><td>11<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>dom ANI AUS CEL PRE<br /></td></tr>
<tr><td colspan=2><b>Camarilla Inner Circle:</b> <n>Once during your turn, you may tap or untap another ready Toreador. +2 bleed.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Lawrence Snelly<br /></td></tr>
</table>
</p>

<p>
<a name="Alfred_Benezri"><span class="cardname">Alfred Benezri</span></a>
<span class="exp">[CE:V]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Pander<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>3<br /></td></tr>
<tr><td width=1><span class="key">Capacity:</span> </td><td>6<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>aus dom PRE THA<br /></td></tr>
<tr><td colspan=2><b>Sabbat bishop:</b> <n>Alfred gets -1 strength in combat with an ally.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Quinton Hoover<br /></td></tr>
</table>
</p>

<p>
<a name="Ambrogino_Giovanni"><span class="cardname">Ambrogino Giovanni</span></a>
<span class="exp">[FN:U2]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Giovanni<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>2<br /></td></tr>
<tr><td width=1><span class="key">Capacity:</span> </td><td>9<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>aus DOM NEC POT THA<br /></td></tr>
<tr><td colspan=2><b>Independent:</b> Ambrogino has 1 vote. +1
bleed.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Christopher Shy<br /></td></tr>
</table>
</p>
<p>
<a name="Amisa"><span class="cardname">Amisa</span></a>
<span class="exp">[AH:V3, FN:PS]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Follower of Set<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>2<br /></td></tr>
<tr><td width=1><span class="key">Capacity:</span> </td><td>8<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>pre pro OBF SER<br /></td></tr>
<tr><td colspan=2><b>Independent:</b> <n>Amisa has 2 votes. Amisa can tap a vampire with a capacity above 7 as a (D) action.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Pete Venters<br /></td></tr>
</table>
</p>
<p>
<a name="Angelica_The_Canonicus"><span class="cardname">Angelica, The Canonicus</span></a>
<span class="exp">[Sabbat:V, SW:PL]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Lasombra<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>2<br /></td></tr>
<tr><td width=1><span class="key">Capacity:</span> </td><td>10<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>cel obf DOM OBT POT<br /></td></tr>
<tr><td colspan=2><b>Sabbat cardinal:</b> <n>Once each <span class="errata">{action that}</span> Angelica attempts to block, you may burn X master cards from your hand to give her +X intercept.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>John Bolton<br /></td></tr>
</table>
</p>

<p>
<a name="Anna_Dictatrix11_Suljic"><span class="cardname">Anna "Dictatrix11" Suljic</span></a>
<span class="exp">[NoR:U]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Imbued<br /></td></tr>
<tr><td width=1><span class="key">Creed:</span> </td><td>Martyr<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>4<br /></td></tr>
<tr><td width=1><span class="key">Life:</span> </td><td>6<br /></td></tr>
<tr><td width=1><span class="key">Virtue:</span> </td><td>mar red vis<br /></td></tr>
<tr><td colspan=2><n>Anna may move 2 blood from the blood bank to any vampire as a +1 stealth action. During your untap phase, you may look at the top three cards of your library.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Thomas Manning<br /></td></tr>
</table>
</p>

<p>
<a name="Anson"><span class="cardname">Anson</span></a>
<span class="exp">[Jyhad:V, VTES:V, Tenth:A]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Toreador<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>1<br /></td></tr>
<tr><td width=1><span class="key">Capacity:</span> </td><td>8<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>aus dom CEL PRE<br /></td></tr>
<tr><td colspan=2><b>Camarilla Prince of Seattle:</b> <n>If Anson is ready during your master phase, you get two master phase actions (instead of one).<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Mark Tedin<br /></td></tr>
</table>
</p>

<p>
<a name="Anastasz_di_Zagreb"><span class="cardname">Anastasz di Zagreb</span></a>
<span class="exp">[CE:V, KMW:PAl]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Tremere<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>3<br /></td></tr>
<tr><td width=1><span class="key">Capacity:</span> </td><td>8<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>ani cel dom AUS THA<br /></td></tr>
<tr><td colspan=2><b>Camarilla Tremere Justicar:</b> <n>If there are any other justicars ready, Anastasz gets 1 fewer vote from his justicar title. Anastasz may steal 1 blood as a ranged strike.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Christopher Shy<br /></td></tr>
</table>
</p>

<p>
<a name="Bronwen"><span class="cardname">Bronwen</span></a>
<span class="exp">[Sabbat:V, SW:PB]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Brujah antitribu<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>2<br /></td></tr>
<tr><td width=1><span class="key">Capacity:</span> </td><td>10<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>dom obt CEL POT PRE<br /></td></tr>
<tr><td colspan=2><b>Sabbat priscus:</b> <n>Once each combat, Bronwen may dodge as a strike.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Ken Meyer, Jr.<br /></td></tr>
</table>
</p>

<p>
<a name="Cedric"><span class="cardname">Cedric</span></a>
<span class="exp">[LoB:U]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Gargoyle<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>4<br /></td></tr>
<tr><td width=1><span class="key">Capacity:</span> </td><td>6<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>obf pot vis FOR<br /></td></tr>
<tr><td colspan=2><b>Camarilla. Tremere slave:</b> <n>If Cedric successfully blocks a (D) action, he may burn 1 blood when the action ends (after combat, if any) to untap. Flight [FLIGHT].<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>David Day<br /></td></tr>
</table>
</p>

<p>
<a name="Cesewayo"><span class="cardname">Cesewayo</span></a>
<span class="exp">[LoB:PO2]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Osebo<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>4<br /></td></tr>
<tr><td width=1><span class="key">Capacity:</span> </td><td>10<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>ani AUS CEL DOM POT THA<br /></td></tr>
<tr><td colspan=2><b>Laibon magaji:</b> <n>Once each action, Cesewayo may burn 1 blood to get +1 intercept.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Abrar Ajmal<br /></td></tr>
</table>
</p>

<p>
<a name="Earl_Shaka74_Deams"><span class="cardname">Earl "Shaka74" Deams</span></a>
<span class="exp">[NoR:U]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Imbued<br /></td></tr>
<tr><td width=1><span class="key">Creed:</span> </td><td>Visionary<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>4<br /></td></tr>
<tr><td width=1><span class="key">Life:</span> </td><td>6<br /></td></tr>
<tr><td width=1><span class="key">Virtue:</span> </td><td>jud mar vis<br /></td></tr>
<tr><td colspan=2><n>Earl gets +1 stealth on actions other than actions to enter combat. During your untap phase, if you control more than two ready imbued, Earl burns 1 conviction [1 CONVICTION].<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>David Day<br /></td></tr>
</table>
</p>

<p>
<a name="Gracis_Nostinus"><span class="cardname">Gracis Nostinus</span></a>
<span class="exp">[CE:V]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Ventrue<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>3<br /></td></tr>
<tr><td width=1><span class="key">Capacity:</span> </td><td>7<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>aus for DOM PRE<br /></td></tr>
<tr><td colspan=2><b>Camarilla Primogen:</b> <n>If a younger vampire attempts to block Gracis and fails, that vampire is tapped at the end of the action.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Max Shade Fellwalker<br /></td></tr>
</table>
</p>

<p>
<a name="Inez_Nurse216_Villagrande"><span class="cardname">Inez "Nurse216" Villagrande</span></a>
<span class="exp">[NoR:U]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Imbued<br /></td></tr>
<tr><td width=1><span class="key">Creed:</span> </td><td>Innocent<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>4<br /></td></tr>
<tr><td width=1><span class="key">Life:</span> </td><td>3<br /></td></tr>
<tr><td width=1><span class="key">Virtue:</span> </td><td>inn<br /></td></tr>
<tr><td colspan=2><n>When Inez enters play, you may search your library (shuffle afterward) or hand for a power that requires innocence and put it on her.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Jim Pavelec<br /></td></tr>
</table>
</p>

<p>
<a name="Kabede_Maru"><span class="cardname">Kabede Maru</span></a>
<span class="exp">[LotN:U]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Assamite<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>5<br /></td></tr>
<tr><td width=1><span class="key">Capacity:</span> </td><td>9<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>abo pot AUS CEL OBF QUI<br /></td></tr>
<tr><td colspan=2><b>Laibon magaji:</b> <n>Kabede gets +1 intercept against political actions. (The blood curse does not affect Kabede.)<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Ken Meyer, Jr.<br /></td></tr>
</table>
</p>

<p>
<a name="Kemintiri_2"><span class="cardname">Kemintiri</span></a>
<span class="exp">[KMW:U]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Follower of Set<br /></td></tr>
<tr><td width=1><span class="key">Level:</span> </td><td>Advanced<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>2<br /></td></tr>
<tr><td width=1><span class="key">Capacity:</span> </td><td>10<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>aus dom OBF PRE SER THA<br /></td></tr>
<tr><td colspan=2><b>Advanced, Independent. Red List:</b> <n>+1 stealth.<br /> <n>[MERGED] Kemintiri has 3 votes (titled). She can play <span class="clarification">&lt;minion&gt;</span> cards that require Camarilla, Ventrue, and/or a justicar title <span class="clarification">&lt;as if she met that/those requirement(s)&gt;</span>.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Lawrence Snelly<br /></td></tr>
</table>
</p>
<p>
<a name="card_15"><span class="cardname">Lázár Dobrescu</span></a>
<span class="exp">[AH:V3, FN:PR]</span><br />
<table><tr><td width=1><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td><span class="key">Clan:</span> </td><td>Ravnos<br /></td></tr>
<tr><td><span class="key">Group:</span> </td><td>2<br /></td></tr>
<tr><td><span class="key">Capacity:</span> </td><td>3<br /></td></tr>
<tr><td><span class="key">Discipline:</span> </td><td>for<br /></td></tr>
<tr><td colspan=2><b>Independent:</b> <n>Lázár may
move one blood from <span class="clarification">&lt;an uncontrolled
minion&gt;</span> in your prey's uncontrolled region to a vampire in your
uncontrolled region as a (D) action.<br />
<tr><td><span class="key">Artist:</span> </td><td>Rebecca Guay<br /></td></tr>
</table>
</p>

<p>
<a name="Path_of_Blood"><span class="cardname">The Path of Blood</span></a>
<span class="exp">[AH:C2, FN:PA, LotN:PA2]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Master<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Assamite<br /></td></tr>
<tr><td width=1><span class="key">Cost:</span> </td><td>1 pool<br /></td></tr>
<tr><td colspan=2><b>Unique master.</b><br />
Put this card in play. Cards that require Quietus [qui] <span class="clarification">&lt;cost Assamites 1 less blood&gt;</span>. Any minion may burn this card as a (D) action; if that minion is a vampire, he or she then takes 1 unpreventable damage when this card is burned.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Drew Tucker; Jeff Holt<br /></td></tr>
</table>
</p>

<p>
<a name="Predators_Communion"><span class="cardname">Predator's Communion</span></a>
<span class="exp">[LoB:C]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Reaction<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>Abombwe<br /></td></tr>
<tr><td colspan=2><n>[abo] [REFLEX] Cancel a frenzy card played on this vampire as it is played.<br />
<n>[abo] +1 intercept. Only usable when a vampire is acting.<br />
<b>[ABO] Only usable by a tapped vampire when a vampire is acting. This reacting vampire untaps.</b><br />
<tr><td width=1><span class="key">Artist:</span> </td><td>David Day<br /></td></tr>
</table>
</p>

<p>
<a name="Sha_Ennu"><span class="cardname">Sha-Ennu</span></a>
<span class="exp">[Third:V]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Tzimisce<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>4<br /></td></tr>
<tr><td width=1><span class="key">Capacity:</span> </td><td>11<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>obf tha ANI AUS CHI VIC<br /></td></tr>
<tr><td colspan=2><b>Sabbat regent:</b> <n>Vampires with capacity less than 4 cannot block Sha-Ennu. +2 bleed.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Richard Thomas<br /></td></tr>
</table>
</p>

<p>
<a name="Yvette_The_Hopeless"><span class="cardname">Yvette, The Hopeless</span></a>
<span class="exp">[CE:V/PTo]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Toreador<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>3<br /></td></tr>
<tr><td width=1><span class="key">Capacity:</span> </td><td>3<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>aus cel<br /></td></tr>
<tr><td colspan=2><b>Camarilla.</b><br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Leif Jones<br /></td></tr>
</table>
</p>

<p>
<a name="Yvette_The_Hopeless"><span class="cardname">Yvette, The Hopeless</span></a>
<span class="exp">[CE:V/PTo]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Toreador<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>3<br /></td></tr>
<tr><td width=1><span class="key">Capacity:</span> </td><td>3<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>aus cel<br /></td></tr>
<tr><td colspan=2><b>Camarilla.</b><br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Leif Jones<br /></td></tr>
</table>
</p>

<p>
<a name="Siamese"><span class="cardname">The Siamese</span></a>
<span class="exp">[BL:U2]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Ahrimane<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>2<br /></td></tr>
<tr><td width=1><span class="key">Capacity:</span> </td><td>7<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>ani pro PRE SPI<br /></td></tr>
<tr><td colspan=2><b>Sabbat:</b> +1 bleed. Sterile.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Lawrence Snelly<br /></td></tr>
</table>
</p>

<p>
<a name="Slaughterhouse"><span class="cardname">The Slaughterhouse</span></a>
<span class="exp">[BL:C1, LoB:C]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Master<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Harbinger of Skulls<br /></td></tr>
<tr><td width=1><span class="key">Cost:</span> </td><td>1 pool<br /></td></tr>
<tr><td><span class="key">Burn Option</span></td></tr>
<tr><td colspan=2><b>Master: location.</b><br />
<n>Tap to burn two cards from the top of your prey's library.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>William O'Connor<br /></td></tr>
</table>
</p>

<p>
<a name="Fidus_The_Shrunken_Beast"><span class="cardname">Fidus, The Shrunken Beast</span></a>
<span class="exp">[BL:U2]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Gargoyle<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>2<br /></td></tr>
<tr><td width=1><span class="key">Capacity:</span> </td><td>4<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>for tha vis<br /></td></tr>
<tr><td colspan=2><b>Camarilla Tremere Slave:</b> Fidus gets +1 stealth on undirected actions. -1 strength. Flight [FLIGHT].<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Christopher Shy<br /></td></tr>
</table>
</p>

<p>
<a name="Enkidu_The_Noah"><span class="cardname">Enkidu, The Noah</span></a>
<span class="exp">[KMW:U/PG]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Gangrel antitribu<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>4<br /></td></tr>
<tr><td width=1><span class="key">Capacity:</span> </td><td>11<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>for ANI CEL OBF POT PRO<br /></td></tr>
<tr><td colspan=2><b>Sabbat. Red List:</b> Enkidu can enter combat with any minion as a (D) action. If Enkidu successfully performs an action to employ a retainer, he untaps at the end of the turn. He cannot have or use equipment. +2 strength.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Mark Nelson<br /></td></tr>
</table>
</p>

<p>
<a name="Ossian"><span class="cardname">Ossian</span></a>
<span class="exp">[KMW:R, KoT:R]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Ally<br /></td></tr>
<tr><td width=1><span class="key">Cost:</span> </td><td>3 pool<br /></td></tr>
<tr><td colspan=2><b>Unique werewolf with 4 life. 2 strength, 0 bleed. Red List.</b><br />
Ossian may enter combat with any vampire as a +1 stealth (D) action. In the first round of combat with a vampire who has played a card that requires Auspex [aus] during this action, that vampire cannot use any maneuvers or strikes. Ossian gains 1 life at the end of each round for each blood the opposing vampire used to heal damage or prevent destruction that round.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Roel Wielinga<br /></td></tr>
</table>
</p>

<p>
<a name="Pariah"><span class="cardname">Pariah</span></a>
<span class="exp">[KMW:U]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Abomination<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>2<br /></td></tr>
<tr><td width=1><span class="key">Capacity:</span> </td><td>6<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>pot pre OBF PRO<br /></td></tr>
<tr><td colspan=2><b>Independent:</b> During your master phase, discard a master card or tap Pariah. Pariah cannot take undirected actions other than hunting. He can enter combat with any minion as a (D) action. +1
strength. Scarce. Sterile.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Richard Thomas<br /></td></tr>
</table>
</p>

<p>
<a name="Paris_Opera_House"><span class="cardname">Paris Opera House</span></a>
<span class="exp">[BL:R1, LoB:R]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Master<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Daughter of Cacophony<br /></td></tr>
<tr><td width=1><span class="key">Cost:</span> </td><td>2 pool<br /></td></tr>
<tr><td><span class="key">Burn Option</span></td></tr>
<tr><td colspan=2><b>Master: unique location.</b><br />
Tap to give a Daughter of Cacophony you control +1 stealth. Tap this card and a Daughter of Cacophony you control to give any minion +1 stealth.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>William O'Connor<br /></td></tr>
</table>
</p>

<p>
<a name="Park_Hunting_Ground"><span class="cardname">Park Hunting Ground</span></a>
<span class="exp">[DS:C2, FN:PR, LotN:PR]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Master<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Ravnos<br /></td></tr>
<tr><td width=1><span class="key">Cost:</span> </td><td>2 pool<br /></td></tr>
<tr><td colspan=2><b>Master: unique location. Hunting ground.</b><br />
During your untap phase, you may move 1 blood from the blood bank to a ready vampire you control. A vampire can gain blood from only one Hunting Ground card each turn.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Pete Venters; Sam Araya<br /></td></tr>
</table>
</p>

<p>
<a name="Pier_13_Port_of_Baltimore"><span class="cardname">Pier 13, Port of Baltimore</span></a>
<span class="exp">[SW:U/PB, Third:U, KoT:U]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Equipment<br /></td></tr>
<tr><td width=1><span class="key">Cost:</span> </td><td>2 blood<br /></td></tr>
<tr><td colspan=2><b>This equipment card represents a unique location and does not count as equipment while in play.</b><br />
During your influence phase, this minion may equip with a non-location, non-unique equipment card from your hand (requirements and cost apply as normal). This is not an action and cannot be blocked.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Steve Prescott<br /></td></tr>
</table>
</p>

<p>
<a name="Political_Hunting_Ground"><span class="cardname">Political Hunting Ground</span></a>
<span class="exp">[Sabbat:U, SW:U/PL]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Master<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Lasombra<br /></td></tr>
<tr><td width=1><span class="key">Cost:</span> </td><td>2 pool<br /></td></tr>
<tr><td colspan=2><b>Master: unique location. <span class="clarification">&lt;Hunting Ground&gt;</span></b><br />
During your untap phase, <span class="errata">{you may move 1 blood from the blood bank to}</span> a ready vampire you control. <span class="ruling">[A vampire can gain blood from only one hunting ground card each turn.]</span><br />
<tr><td width=1><span class="key">Artist:</span> </td><td>John Scotello<br /></td></tr>
</table>
</p>

<p>
<a name="Ankara_Citadel_Turkey"><span class="cardname">The Ankara Citadel, Turkey</span></a>
<span class="exp">[AH:U5, CE:U, KoT:U]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Equipment<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Tremere<br /></td></tr>
<tr><td width=1><span class="key">Cost:</span> </td><td>2 blood<br /></td></tr>
<tr><td colspan=2><b>This equipment card represents a unique location and does not count as equipment while in play.</b><br />
The vampire with this location pays only half of the blood cost for any cards he or she plays (round down).<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Greg Simanson; Brian LeBlanc<br /></td></tr>
</table>
</p>

<p>
<a name="Living_Manse"><span class="cardname">Living Manse</span></a>
<span class="exp">[Sabbat:R, SW:R, Third:R]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Equipment<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Tzimisce<br /></td></tr>
<tr><td width=1><span class="key">Cost:</span> </td><td>1 blood<br /></td></tr>
<tr><td colspan=2><b>This equipment card represents a location and does not count as an equipment card while it is in play.</b><br />
The vampire with this location gets +1 bleed. He or she can burn this card before range is determined to end combat. A vampire may have only one Living Manse.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Mark Tedin<br /></td></tr>
</table>
</p>

<p>
<a name="Rock_Cat"><span class="cardname">Rock Cat</span></a>
<span class="exp">[BL:R1, LoB:R]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Ally<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Gargoyle<br /></td></tr>
<tr><td width=1><span class="key">Cost:</span> </td><td>4 pool<br /></td></tr>
<tr><td colspan=2><b>Gargoyle creature with 4 life. 3 strength, 0 bleed.</b><br />
Rock Cat may enter combat with any ready minion controlled by another Methuselah as a (D) action. When in combat with the Rock Cat, vampires with capacity less than 4 cannot strike in the first round. Rock Cat gets an optional press each combat. Rock Cat may play cards requiring basic Potence [pot] as a vampire of capacity 3.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Jeff Holt<br /></td></tr>
</table>
</p>

<p>
<a name="Scapelli_The_Family_Mechanic"><span class="cardname">Scapelli, The Family "Mechanic"</span></a>
<span class="exp">[DS:U2]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Ally<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Giovanni<br /></td></tr>
<tr><td width=1><span class="key">Cost:</span> </td><td>3 pool<br /></td></tr>
<tr><td colspan=2><b>Unique <span class="ruling">[mortal]</span> with 3 life. <span class="clarification">&lt;0 strength&gt;</span>, 1 bleed.</b><br />
<span class="clarification">&lt;Scapelli may strike for 2R damage.&gt;</span> Once each combat, Scapelli may press to continue combat.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Richard Thomas<br /></td></tr>
</table>
</p>

<p>
<a name="Shade"><span class="cardname">Shade</span></a>
<span class="exp">[Sabbat:U, SW:PL]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Retainer<br /></td></tr>
<tr><td width=1><span class="key">Cost:</span> </td><td>1 blood<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>Obtenebration<br /></td></tr>
<tr><td colspan=2><b><span class="ruling">[Demon]</span> with 2 life.</b><br />
[obt] When the minion with this retainer is in combat, the opposing minion takes 1 damage during strike resolution <span class="clarification">&lt;if the range is close&gt;</span>.<br />
<b>[OBT] As above, but Shade has 3 life.</b><br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Stuart Beel<br /></td></tr>
</table>
</p>

<p>
<a name="Raven_Spy"><span class="cardname">Raven Spy</span></a>
<span class="exp">[Jyhad:U, VTES:U, CE:U/PN, Anarchs:PG2, BH:PN3, KMW:PG, Third:PTz3, LotN:PR3, KoT:U]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Retainer<br /></td></tr>
<tr><td width=1><span class="key">Cost:</span> </td><td>1 blood<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>Animalism<br /></td></tr>
<tr><td colspan=2><b>Animal with 1 life.</b><br />
[ani] This minion gets +1 intercept.<br />
<b>[ANI] As above, but the Raven Spy has 2 life.</b><br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Jeff Holt; Dan Frazier<br /></td></tr>
</table>
</p>

<p>
<a name="Ghoul_Retainer"><span class="cardname">Ghoul Retainer</span></a>
<span class="exp">[Jyhad:R2, VTES:R, CE:R2, KoT:U/R]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Retainer<br /></td></tr>
<tr><td width=1><span class="key">Cost:</span> </td><td>2 pool<br /></td></tr>
<tr><td colspan=2><b>Ghoul with 2 life. 1 strength.</b><br />
During the initial strike resolution each round, the Ghoul Retainer inflicts 1 damage or may use a weapon not used by the employing minion (or another retainer) that round (either before or after). This is not a strike, although it does count as "using" the weapon.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>L. A. Williams; Richard Thomas<br /></td></tr>
</table>
</p>

<p>
<a name="Gypsies"><span class="cardname">Gypsies</span></a>
<span class="exp">[Jyhad:U, VTES:U]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Ally<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Gangrel<br /></td></tr>
<tr><td width=1><span class="key">Cost:</span> </td><td>3 pool<br /></td></tr>
<tr><td colspan=2><b>Unique <span class="ruling">[mortal]</span> with 1 life. 1 <span class="clarification">&lt;strength&gt;</span>, 1 bleed.</b><br />
Gypsies get +1 stealth on each of their actions.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Pete Venters<br /></td></tr>
</table>
</p>

<p>
<a name="High_Top"><span class="cardname">High Top</span></a>
<span class="exp">[BL:R1, LoB:R]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Ally<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Ahrimane<br /></td></tr>
<tr><td width=1><span class="key">Cost:</span> </td><td>4 pool<br /></td></tr>
<tr><td colspan=2><b>Unique werewolf with 3 life. 1 strength, 0 bleed.</b><br />
High Top gets +1 intercept. High Top may enter combat with any minion controlled by another Methuselah as a (D) action. High Top gets an additional strike each round and an optional maneuver once each combat. He may play cards requiring basic Celerity [cel] as a vampire with a capacity of 4. If High Top has less than 3 life during your untap phase, he gains 1 life.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Mark Nelson<br /></td></tr>
</table>
</p>

<p>
<a name="Two_Wrongs"><span class="cardname">Two Wrongs</span></a>
<span class="exp">[Promo-20081119]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Master<br /></td></tr>
<tr><td colspan=2><b>Master: out-of-turn. Trifle.</b><br />
Play when a minion controlled by a Methuselah other than your predator is bleeding you. That minion is now bleeding his or her prey. The next card that would change the target of this bleed is canceled as it is played.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Leif Jones<br /></td></tr>
</table>
</p>

<p>
<a name="Vox_Domini"><span class="cardname">Vox Domini</span></a>
<span class="exp">[BH:R, LoB:PA]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Master<br /></td></tr>
<tr><td width=1><span class="key">Cost:</span> </td><td>1 pool<br /></td></tr>
<tr><td colspan=2><b>Master: out-of-turn.</b><br />
Only usable during the referendum of a political action. Not usable on a referendum that is automatically passing. The referendum fails. Each Methuselah may play only one Vox Domini each game.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Christopher Shy<br /></td></tr>
</table>
</p>

<p>
<a name="Agent_of_Power"><span class="cardname">Agent of Power</span></a>
<span class="exp">[LotN:C]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Master<br /></td></tr>
<tr><td colspan=2><b>Master: Discipline. Trifle. Unique.</b><br />
Put this card on a vampire you control and choose a Discipline. This vampire gains 1 level of that Discipline. Burn this card during your discard phase.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Jeff Holt<br /></td></tr>
</table>
</p>

<p>
<a name="Necromancy_nec"><span class="cardname">Necromancy [nec]</span></a>
<span class="exp">[DS:C2, FN:PG2, LotN:PG]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Master<br /></td></tr>
<tr><td width=1><span class="key">Capacity:</span> </td><td>+1<br /></td></tr>
<tr><td colspan=2><b>Master: Discipline.</b><br />
Put this card on a vampire. This vampire gains 1 level of Necromancy [nec]. Capacity increases by 1: the vampire is one generation older. Cannot be placed on a vampire with superior Necromancy.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Anson Maddocks; Sam Araya<br /></td></tr>
</table>
</p>

<p>
<a name="Rebekka_Chantry_Elder_of_Munich"><span class="cardname">Rebekka, Chantry Elder of Munich</span></a>
<span class="exp">[DS:V, CE:PTr]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Vampire<br /></td></tr>
<tr><td width=1><span class="key">Clan:</span> </td><td>Tremere<br /></td></tr>
<tr><td width=1><span class="key">Group:</span> </td><td>2<br /></td></tr>
<tr><td width=1><span class="key">Capacity:</span> </td><td>8<br /></td></tr>
<tr><td width=1><span class="key">Discipline:</span> </td><td>pot AUS PRE THA<br /></td></tr>
<tr><td colspan=2><b>Camarilla:</b> Rebekka gets +1 stealth on each of her actions. Rebekka gets +1 bleed when bleeding a Methuselah who controls a ready Malkavian.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Anson Maddocks<br /></ td></tr>
</table>
</p>

<p>
<a name="Protracted_Investment"><span class="cardname">Protracted Investment</span></a>
<span class="exp">[Jyhad:C, VTES:C, CE:PTr]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Master<br /></td></tr>
<tr><td width=1><span class="key">Cost:</span> </td><td>2 pool<br /></td></tr>
<tr><td colspan=2><b>Master. Investment.</b><br />
<span class="clarification">&lt;Put this card in play and&gt;</span> move 5 blood from the blood bank to this card. You may use a master phase action to move 1 blood from this card to your pool. Burn this card when all blood has been removed.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Brian Snoddy<br /></td></tr>
</table>
</p>

<p>
<a name="Bravo"><span class="cardname">Bravo</span></a>
<span class="exp">[Gehenna:C]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Master<br /></td></tr>
<tr><td colspan=2><b>Master: archetype.</b><br />
Put this card on a vampire you control. Once per turn, when this vampire successfully performs an action to enter combat with another, he or she gains 1 blood from the blood bank when the combat ends, if he or she is still ready. A vampire can have only one archetype.<br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Nilson<br /></td></tr>
</table>
</p>

<p>
<a name="Dramatic_Upheaval"><span class="cardname">Dramatic Upheaval</span></a>
<span class="exp">[Jyhad:V, VTES:V, CE:U, Anarchs:PAB, BH:PM]</span><br />
<table border=0 cellpadding=0 cellspacing=0><tr><td width=1><span class="key">Cardtype:</span> </td><td>Political Action<br /></td></tr>
<tr><td colspan=2>Choose another Methuselah. Successful referendum means you switch places with that Methuselah. <span class="errata">{Added to the V:EKN banned list in 2005.}</span><br />
<tr><td width=1><span class="key">Artist:</span> </td><td>Heather Hudson; Mike Huddleston<br /></td></tr>
</table>
</p>

<p>
<a name="Motivated_by_Gehenna"><span class="cardname">Motivated by Gehenna</span></a>
<span class="exp">Eden's Legacy Storyline:Storyline</span><table border=0 cellpadding=0 cellspacing=0><tr><td width=1><tr><td width=1><span class="key">Cardtype:</span> </td><td>Master<br /></td></tr>
<tr><td colspan=2><b>Master.</b><br />
Put this card in play, If you control the Edge, any vampire you control may enter combat with a ready minion controlled by another Methuselah as a (D) action that costs 1 blood.<br />
{NOT FOR LEGAL PLAY}<br />
</table>
</p>

</td></tr>
</table></body></html>
"""

TEST_TEXT_CARD_LIST = """
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
Unique equipment.
When this vampire successfully hunts, he or she gains 1 additional blood.
Artist: Thomas Nairb; Christopher Rush

Name: Abandoning the Flesh
[CE:R, Third:R]
Cardtype: Reaction/Combat
Discipline: Dementation
Only usable by a vampire being burned. Usable by a vampire in torpor.
[dem] Remove this vampire from the game instead (diablerie, if any, is still successful), and put this card into play. You may not play this card if you already have an Abandoning the Flesh in play. You may tap this card when a vampire with Dementation is bleeding to give that vampire +1 bleed for the current action.
Artist: Steve Ellis

Name: Abbot
[Third:U]
Cardtype: Action
+1 stealth action. Requires a Sabbat vampire.
Put this card on this acting Sabbat vampire and untap him or her. This Sabbat vampire gets +1 intercept against (D) actions directed at his or her controller. A vampire may have only one Abbot.
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
Independent: Abdelsobek can untap a vampire or mummy you control as a +1 stealth action.
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
[COMBAT] Tap this imbued before range is determined to end a combat between a monster and a mortal. If the mortal is a minion other than this imbued, you may move a conviction to this imbued from your hand or ash heap.
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

Name: Alan Sovereign
[Promo-20051001]
Cardtype: Vampire
Clan: Ventrue
Level: Advanced
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
Camarilla Inner Circle: Once during your turn, you may tap or untap another ready Toreador. +2 bleed.
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
Independent: Amisa has 2 votes. Amisa can tap a vampire with a capacity above 7 as a (D) action.
Artist: Pete Venters

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
Anna may move 2 blood from the blood bank to any vampire as a +1 stealth action. During your untap phase, you may look at the top three cards of your library.
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
Camarilla. Tremere slave: If Cedric successfully blocks a (D) action, he may burn 1 blood when the action ends (after combat, if any) to untap. Flight [FLIGHT].
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
Earl gets +1 stealth on actions other than actions to enter combat. During your untap phase, if you control more than two ready imbued, Earl burns 1 conviction [1 CONVICTION].
Artist: David Day

Name: Enkidu, The Noah
[KMW:U/PG]
Cardtype: Vampire
Clan: Gangrel antitribu
Group: 4
Capacity: 11
Discipline: for ANI CEL OBF POT PRO
Sabbat. Red List: Enkidu can enter combat with any minion as a (D) action. If Enkidu successfully performs an action to employ a retainer, he untaps at the end of the turn. He cannot have or use equipment. +2 strength.
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
Camarilla Primogen: If a younger vampire attempts to block Gracis and fails, tap that vampire at the end of the action.
Artist: Max Shade Fellwalker

Name: Gypsies
[Jyhad:U, VTES:U]
Cardtype: Ally
Clan: Gangrel
Cost: 3 pool
Unique -{mortal}- with 1 life. 1 {strength}, 1 bleed.
Gypsies get +1 stealth on each of their actions.
Artist: Pete Venters

Name: High Top
[BL:R1, LoB:R]
Cardtype: Ally
Clan: Ahrimane
Cost: 4 pool
Unique werewolf with 3 life. 1 strength, 0 bleed.
High Top gets +1 intercept. High Top may enter combat with any minion controlled by another Methuselah as a (D) action. High Top gets an additional strike each round and an optional maneuver once each combat. He may play cards requiring basic Celerity [cel] as a vampire with a capacity of 4. If High Top has less than 3 life during your untap phase, he gains 1 life.
Artist: Mark Nelson

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
Level: Advanced
Group: 2
Capacity: 10
Discipline: aus dom OBF PRE SER THA
Advanced, Independent. Red List: +1 stealth.
[MERGED] Kemintiri has 3 votes (titled). She can play {minion} cards that require Camarilla, Ventrue, and/or a justicar title {as if she met that/those requirement(s)}.
Artist: Lawrence Snelly

Name: Lázár Dobrescu
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
Independent: During your master phase, discard a master card or tap Pariah. Pariah cannot take undirected actions other than hunting. He can enter combat with any minion as a (D) action. +1 strength. Scarce. Sterile.
Artist: Richard Thomas

Name: Paris Opera House
[BL:R1, LoB:R]
Cardtype: Master
Clan: Daughter of Cacophony
Cost: 2 pool
Burn Option
Master: unique location.
Tap to give a Daughter of Cacophony you control +1 stealth. Tap this card and a Daughter of Cacophony you control to give any minion +1 stealth.
Artist: William O'Connor

Name: Park Hunting Ground
[DS:C2, FN:PR, LotN:PR]
Cardtype: Master
Clan: Ravnos
Cost: 2 pool
Master: unique location. Hunting ground.
During your untap phase, you may move 1 blood from the blood bank to a ready vampire you control. A vampire can gain blood from only one Hunting Ground card each turn.
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
During your untap phase, you may move 1 blood from the bank to a ready vampire you control. A vampire can gain blood from only one hunting ground card each turn.
Artist: John Scotello; Melissa Uran

Name: Predator's Communion
[LoB:C]
Cardtype: Reaction
Discipline: Abombwe
[abo] [REFLEX] Cancel a frenzy card played on this vampire as it is played.
[abo] +1 intercept. Only usable when a vampire is acting.
[ABO] Only usable by a tapped vampire when a vampire is acting. This reacting vampire untaps.
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
Tap to burn two cards from the top of your prey's library.
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
[HttB:C/PSal2]
Cardtype: Reaction
Discipline: Valeren / Auspex

[aus] Reduce a bleed against you by 1.
[val] The action ends (unsuccessfully). The acting minion may burn 1 blood to cancel this card as it is played. Only one Hide the Heart may be played at [val] each action.
[VAL] Reduce a bleed against you by 2, or tap to reduce a bleed against any Methuselah by 2.
Artist: Kari Christensen

Name: Anarch Railroad
[Anarchs:R2]
Cardtype: Master
Cost: 2 pool
Master: unique location.
Tap to give an anarch +1 stealth for the current action.
Artist: Joel Biske

Name: Anarch Revolt
[Jyhad:U, VTES:U, CE:U, Anarchs:PAB2, KMW:PAn, Third:U]
Cardtype: Master
Master.
Put this card in play. A Methuselah who does not control a ready anarch burns 1 pool during his or her untap phase. Any vampire can call a referendum to burn this card as a +1 stealth political action.
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
