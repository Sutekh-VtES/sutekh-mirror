# SecretLibrary.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar+sutekh@gmail.com>
# GPL - see COPYING for details

"""Plugin for interacting with the Secret Library website."""

import gtk
import urllib2
import urllib
from sutekh.core.SutekhObjects import PhysicalCardSet, IAbstractCard
from sutekh.core.Filters import MultiCardTypeFilter, FilterNot
from sutekh.gui.PluginManager import CardListPlugin

class SecretLibrary(CardListPlugin):
    """Provides ability to export cards directly to the Secret Library."""
    dTableVersions = { PhysicalCardSet: [5]}
    aModelsSupported = [PhysicalCardSet]

    def get_menu_item(self):
        """Register on the 'Export Card Set' Menu"""
        if not self.check_versions() or not self.check_model_type():
            return None
        oExport = gtk.MenuItem("Export to Secret Library")
        oExport.connect("activate", self.make_dialog)
        return ('Export Card Set', oExport)

    # pylint: disable-msg=W0613
    # oWidget has to be here, although it's unused

    def make_dialog(self, oWidget):
        """Create the dialog"""
        self.handle_response()

    # pylint: enable-msg=W0613

    def handle_response(self):
        """Handle the users response. Submit to Secret Library."""
        # pylint: disable-msg=E1101
        # SQLObject methods confuse pylint
        self._submit_card_set()

    # Inventory import (to Secret Library)

        # sl_inventory_import (tells that an inventory will be imported to SL)
        # sl_user_agent, sl_agent_version, username and password as in other
        #      APIs
        # inventory_crypt and inventory_library contain crypt and library data
        # one entry per line
        # 4;3;Alan Sovereign (Adv) would mean that i have 4 advanced alans
        #      and i want to keep 3 of them (meaning 1 extra)
        # 2;3;François Warden Loehr (would mean that i have 2 Francois and
        #      want 1 more)
        # 3;3;Coven, The (initial the after card name)

    # Inventory export (from Secret Library)

        # ***SL***CRYPT***
        # 2;2;Abebe
        # 2;2;Alan Sovereign (Adv)
        # 4;3;François Warden Loehr
        # ***SL***LIBRARY***
        # 1;1;Absimiliard's Army
        # 5;5;Ahriman's Demesne
        # 1;1;Textbook Damnation, The
        # 8;8;Watch Commander
        # ***SL***ENDEXPORT***

    # Deck Export (from Secret Library)

        # ***SL***CRYPT***
        # 2 Count Germaine (Adv)
        # 2 Count Germaine
        # ***SL***LIBRARY***
        # 10 Cloak the Gathering
        # 2 Coven, The
        # ***SL***ENDDECK***

    def _submit_card_set(self):
        """Submit card set to Secret Library."""
        sUrl = "http://www.tenerdo.org/sl_import_test.php"

        # using http-post method
        #
        # username (string, 6 <= characters <= 24)
        # password (string, 6 <= characters <= 16)
        # author (string, 100 characters)
        # title (string, 100 characters)
        # description (string, 1000 characters)
        # crypt (string, 1000 characters)
        # library (string, 10000 characters)
        # sl_deck_submit (non-null value to activate script)
        # sl_user_agent (string, 20, will tell me what agents work and
        #    what agents don't)
        # sl_agent_version (string, 20, more specifics to previous)
        # the field lengths can be modified if necessary
        # yeah, password is plane text
        #
        # Errors:
        #
        # 1: Invalid POST variables
        #    given if sl_deck_submit, sl_user_agent or sl_agent_version is
        #    missing
        # 2: Invalid username or password
        #    given if username or password fields don't match, in the test
        #    version username can be anything between 6 and 24 characters and
        #    password can be anything between 6 and 16 characters
        # 4: Invalid user agent
        #    given if sl_user_agent or sl_agent_version are empty
        # 8: Empty library
        #    given if library is empty
        # 16: Empty crypt
        #     same for crypt
        # 32: Database error
        #     if mysql queries return an error
        #
        # all errors return "N: Short explenation"

        oCardSet = self.get_card_set()

        dData = {
            'username': 'testuser',
            'password': 'testpass',
            'author': oCardSet.author,
            'title': oCardSet.name,
            'description': oCardSet.comment,
            'sl_deck_submit': '1',
            'sl_user_agent': 'Sutekh',
            'sl_agent_version': '0.0.0.1',
        }

        # populate crypt
        aCrypt = []
        oCryptFilter = MultiCardTypeFilter(['Vampire', 'Imbued'])
        oCryptIter = self.model.get_card_iterator(oCryptFilter)

        for oCard in oCryptIter:
            # pylint: disable-msg=E1101
            # E1101: PyProtocols confuses pylint
            oAbsCard = IAbstractCard(oCard)
            aCrypt.append(oAbsCard.name)

        dData['crypt'] = "\n".join(aCrypt)

        # populate library
        aLibrary = []
        oLibraryFilter = FilterNot(oCryptFilter)
        oLibraryIter = self.model.get_card_iterator(oLibraryFilter)

        for oCard in oLibraryIter:
            # pylint: disable-msg=E1101
            # E1101: PyProtocols confuses pylint
            oAbsCard = IAbstractCard(oCard)
            aLibrary.append(oAbsCard.name)

        dData['library'] = "\n".join(aLibrary)

        sData = urllib.urlencode(dData)
        print "Secret Library Request:", sData

        oReq = urllib2.Request(url=sUrl, data=sData)
        fReq = urllib2.urlopen(oReq)
        print "Secret Library Response:", fReq.read()
        fReq.close()

# pylint: disable-msg=C0103
# accept plugin name
plugin = SecretLibrary
