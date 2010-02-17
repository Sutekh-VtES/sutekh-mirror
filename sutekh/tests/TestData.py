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
<tr><td colspan=2><b>Independent:</b> <n>Ambrogino has 1 vote. +1 bleed.<br />
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
<tr><td colspan=2><b>Independent:</b> <n>Lázár may move one blood from <span class="clarification">&lt;an uncontrolled minion&gt;</span> in your prey's uncontrolled region to a vampire in your uncontrolled region as a (D) action.<br />
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

</td></tr>
</table></body></html>
"""

TEST_RULINGS = """
<html>
<head><title>Sutekh Test Rulings</title></head>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<body>

<p><b>AK-47:</b>
<li><span class="errata">The AK-47 provides the bearer one optional maneuver "each combat".</span>
<a href="http://groups-beta.google.com/groups?selm=46FCEF4C.6050100@white-wolf.com" target="_top" onMouseOver="window.status='Article Archived on Google';return true">[LSJ&nbsp;20070928]</a> </li>
</a>
</p>

<p><b>Ablative Skin:</b>
<li><span class="ruling">Cannot be used to prevent damage that cannot be prevented by cards that require Fortitude (e.g., Blood Rage and Blood Fury).</span>
<a href="http://groups-beta.google.com/groups?selm=36C98715.81740A4B@wizards.com" target="_top" onMouseOver="window.status='Article Archived on Google';return true">[LSJ&nbsp;19990216]</a> </li>
</a>
</p>

<p><b>Lazar Dobrescu:</b>
<li><span class="ruling">Cannot use his special ability if his controller has no vampires in her uncontrolled region.</span>
<a href="http://groups-beta.google.com/groups?selm=36C82B01.3705D2F0@wizards.com" target="_top" onMouseOver="window.status='Article Archived on Google';return true">[LSJ&nbsp;19990215]</a> </li>
</a>
</p>

</body></html>
"""
