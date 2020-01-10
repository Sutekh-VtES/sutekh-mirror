# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2011 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

# pylint: disable=line-too-long
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
# pylint: enable=line-too-long
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

    # pylint: disable=no-self-use
    # method for consistency with the other methods
    def _gen_header(self, oHolder):
        """Generate an suitable forum header."""
        return "[size=18][b]Deck Name : %s[/b][/size]\n" \
               "[b][u]Author :[/u][/b] %s\n" \
               "[b][u]Description :[/u][/b]\n%s\n" % (oHolder.name,
                                                      oHolder.author,
                                                      oHolder.comment)
    # pylint: enable=no-self-use

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
        for oCard, (iCount, _sSet) in sorted(dCombinedVamps.items(),
                                             key=self._crypt_sort_key):
            dLine = self._format_crypt_line(oCard, iCount)
            add_clan_symbol(dLine)
            dLine['adv'] = dLine['adv'].strip()
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
            dLine['url'] = secret_library_url(oCard, True)

            aCryptLines.append(dLine)

        sCrypt += "[table]\n"
        for dLine in aCryptLines:
            sCrypt += ("[tr][td]%(count)dx[/td]"
                       "[td][url=%(url)s]%(name)s[/url][/td][td]%(adv)s[/td]"
                       "[td](%(capacity)d)[/td][td]%(disc)s[/td]"
                       "[td]%(title)s[/td][td]%(clansymbol)s %(clan)s[/td]"
                       "[td](group %(group)d)[/td][/tr]\n" % dLine)

        sCrypt += "[/table]"

        return sCrypt

    def _gen_library(self, dCards):
        """Generaten an VEKN Forum library description.

           dCards is mapping of (card id, card name) -> card count.
           """
        (dLib, iLibSize) = self._extract_library(dCards)
        dCombinedLib = self._group_sets(dLib)
        dTypes = self._group_types(dCombinedLib)

        sLib = "[size=18][u]Library [%d cards][/u][/size]\n" \
            % (iLibSize,)

        for sTypeString in sorted(dTypes):
            dCards = dTypes[sTypeString]
            iTotal = sum(dCards.values())

            if sTypeString == 'Master':
                iTrifles = self._count_trifles(dLib)
                if iTrifles > 1:
                    sLib += "[b][u]%s [%d] (%d trifles)[/u][/b]\n" % (
                        sTypeString, iTotal, iTrifles)
                elif iTrifles == 1:
                    sLib += "[b][u]%s [%d] (%d trifle)[/u][/b]\n" % (
                        sTypeString, iTotal, iTrifles)
                else:
                    sLib += "[b][u]%s [%d][/u][/b]\n" % (sTypeString, iTotal)
            else:
                sLib += "[b][u]%s [%d][/u][/b]\n" % (sTypeString, iTotal)

            for oCard, iCount in sorted(dCards.items(),
                                        key=lambda x: x[0].name):
                sUrl = secret_library_url(oCard, False)
                sLib += " %dx [url=%s]%s[/url]\n" % (iCount, sUrl, oCard.name)

            sLib += "\n"

        return sLib

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
