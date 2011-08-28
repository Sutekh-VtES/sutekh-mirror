# WriteVEKNForum.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2011 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

# pylint: disable-msg=C0301
# documentation, so line length ignored
"""Writer for VEKN Forum posts, based on the ARDB Text format

   Style intended to copy that produced by ARDB, based on the TWD postings
   on the vekn.net forum.

   Example deck:

   [size=18][b]Deck Name : Followers of Set Preconstructed Deck[/b][/size]
   [b][u]Author :[/u][/b] L. Scott Johnson
   [b][u]Description :[/u][/b]
   Followers of Set Preconstructed Starter from Lords of the Night.

   http://www.white-wolf.com/vtes/index.php?line=Checklist_LordsOfTheNight

   [size=18][u]Crypt [12 vampires] Capacity min: 2 max: 10 average: 5.84[/u][/size]
   [table]
   [tr][td]2x[/td][td][url=http://www.secretlibrary.info/...]Nakhthorheb[/url][/td][td][/td][td](10)[/td][td]:OBF: :PRE: :SER:[/td][td]:fose: Follower of Set[/td][td](group 4)[/td][/tr]
   ...
   [/table]

   [size=18][u]Library [77 cards][/u][/size]
   [b][u]Action [20][/u][/b]
     2x [url=...]Blithe Acceptance[/url]
     4x [url=....]Dream World[/url]
   ...
   """
# pylint: enable-msg=C0301
import time
from sutekh.core.ArdbInfo import ArdbInfo
from sutekh.SutekhUtility import secret_library_url
from sutekh.SutekhInfo import SutekhInfo


def add_clan_symbol(dLine):
    """Fix the clan symbol to account for special cases"""
    dSpecialClanMap = {
            'True Brujah': ':trub:',
            'Daughter of Cacophony': ':doca:',
            'Follower of Set': ':fose:',
            'Harbinger of Skulls': ':hosk:',
            'Blood Brother': ':bbro:',
            }
    if dLine['clan'] in dSpecialClanMap:
        sSymbol = dSpecialClanMap[dLine['clan']]
    elif 'antitribu' in dLine['clan']:
        sSymbol = "!%s!" % dLine['clan'][:4].lower()
    else:
        # This is the usual default
        sSymbol = ":%s:" % dLine['clan'][:4].lower()
    dLine['clansymbol'] = sSymbol


class WriteVEKNForum(ArdbInfo):
    """Create a string suitable for pasting into the VEKN forums"""

    # pylint: disable-msg=R0201
    # method for consistency with the other methods
    def _gen_header(self, oHolder):
        """Generate an suitable forum header."""
        return "[size=18][b]Deck Name : %s[/b][/size]\n" \
               "[b][u]Author :[/u][/b] %s\n" \
               "[b][u]Description :[/u][/b]\n%s\n" % (oHolder.name,
                       oHolder.author, oHolder.comment)
    # pylint: enable-msg=R0201

    def _gen_crypt(self, dCards):
        """Generaten a VEKN Forum crypt description.

           dCards is mapping of (card id, card name) -> card count.
           """
        (dVamps, dCryptStats) = self._extract_crypt(dCards)
        dCombinedVamps = self._group_sets(dVamps)

        sCrypt = "[size=18][u]Crypt [%(size)d vampires] Capacity " \
                "min: %(min)d max: %(max)d average: %(avg).2f[/u][/size]\n" \
                % dCryptStats

        aCryptLines = []
        # ARDB's discipline & title padding are based on the longest entry
        # so we need to keep track and format later
        for oCard,  (iCount, _sSet) in sorted(dCombinedVamps.iteritems(),
                key=lambda x: (-x[1][0], -max(x[0].capacity, x[0].life),
                    x[0].name)):
            # We sort inversely on count, then capacity and then normally by
            # name
            dLine = {'count': iCount}
            if len(oCard.creed) > 0:
                dLine['clan'] = "%s (Imbued)" % \
                        [x.name for x in oCard.creed][0]
                dLine['capacity'] = oCard.life
            else:
                dLine['clan'] = [x.name for x in oCard.clan][0]
                dLine['capacity'] = oCard.capacity
            add_clan_symbol(dLine)
            dLine['name'] = oCard.name
            dLine['url'] = secret_library_url(oCard, True)
            dLine['adv'] = ''
            if oCard.level is not None:
                dLine['name'] = dLine['name'].replace(' (Advanced)', '')
                dLine['adv'] = 'Adv'
            aDisc = self._gen_disciplines(oCard).split()
            if aDisc:
                # Get nice frum symbols for the disciplines
                dLine['disc'] = ":" + ": :".join(aDisc) + ":"
                # Annoying special cases
                dLine['disc'] = dLine['disc'].replace(":jud:", ":jus:")
                dLine['disc'] = dLine['disc'].replace(":vis:", ":vsn:")
                dLine['disc'] = dLine['disc'].replace(":FLI:", ":flight:")
            else:
                dLine['disc'] = ""

            dLine['title'] = '   '
            if len(oCard.title):
                dLine['title'] = [oC.name for oC in oCard.title][0]
                dLine['title'] = dLine['title'].replace('Independent with ',
                        '')[:12]
            dLine['group'] = int(oCard.group)
            aCryptLines.append(dLine)

        sCrypt += "[table]\n"
        for dLine in aCryptLines:
            sCrypt += "[tr][td]%(count)dx[/td]" \
                    "[td][url=%(url)s]%(name)s[/url][/td][td]%(adv)s[/td]" \
                    "[td](%(capacity)d)[/td][td]%(disc)s[/td]" \
                    "[td]%(title)s[/td][td]%(clansymbol)s %(clan)s[/td]" \
                    "[td](group %(group)d)[/td][/tr]\n" % dLine

        sCrypt += "[/table]"

        return sCrypt

    def _gen_library(self, dCards):
        """Generaten an VEKN Forum library description.

           dCards is mapping of (card id, card name) -> card count.
           """
        (dLib, iLibSize) = self._extract_library(dCards)
        dCombinedLib = self._group_sets(dLib)

        sLib = "[size=18][u]Library [%d cards][/u][/size]\n" \
            % (iLibSize,)

        dTypes = {}
        for oCard, (iCount, sTypeString, _sSet) in dCombinedLib.iteritems():
            if sTypeString not in dTypes:
                dTypes[sTypeString] = {}
            dTypes[sTypeString].setdefault(oCard, 0)
            dTypes[sTypeString][oCard] += iCount

        for sTypeString in sorted(dTypes):
            dCards = dTypes[sTypeString]
            iTotal = sum(dCards.values())

            sLib += "[b][u]%s [%d][/u][/b]\n" % (sTypeString, iTotal)

            for oCard, iCount in sorted(dCards.iteritems(),
                    key=lambda x: x[0].name):
                sUrl = secret_library_url(oCard, False)
                sLib += " %dx [url=%s]%s[/url]\n" % (iCount, sUrl, oCard.name)

            sLib += "\n"

        return sLib

    # pylint: disable-msg=R0913
    # we need all these arguments
    def write(self, fOut, oHolder):
        """Takes filename, deck details and a dictionary of cards, of the
           form dCard[(id, name, set)] = count and writes the file."""
        # We don't encode strange characters, and just write the unicode string
        # to file. This looks to match ARDB's behaviour (tested against
        # ARDB version 2.8
        dCards = self._get_cards(oHolder.cards)
        fOut.write(self._gen_header(oHolder))
        fOut.write("\n")
        fOut.write(self._gen_crypt(dCards))
        fOut.write("\n")
        fOut.write(self._gen_library(dCards))
        fOut.write("\n")
        fOut.write("Recorded with : Sutekh %s [ %s ]\n" %
                (SutekhInfo.VERSION_STR,
                    time.strftime('%Y-%m-%d', time.localtime())))

    # pylint: enable-msg=R0913
