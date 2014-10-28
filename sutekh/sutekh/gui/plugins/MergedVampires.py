# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2014 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Shows the merged version for advanced vampires."""

from sutekh.base.core.BaseObjects import (PhysicalCardSet,
                                          IKeyword, IAbstractCard)
from sutekh.core.SutekhObjects import (ITitle, ISect, IDisciplinePair,
                                       SutekhAbstractCard)
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.base.gui.MessageBus import MessageBus, CARD_TEXT_MSG
from sutekh.base.gui.GuiUtils import make_markup_button
from sutekh.base.Utility import normalise_whitespace

from sqlobject import SQLObjectNotFound


class FakeTitle(object):
    """Fake titles not in the database"""

    def __init__(self, sText):
        # pylint: disable-msg=C0103
        # We duplicate Title naming here
        self.name = sText


class MergedKeyword(object):
    """Fake a 'merged' keyword"""

    def __init__(self):
        # pylint: disable-msg=C0103
        # We duplicate Keyword naming here
        self.keyword = 'merged'


class FakeCard(object):
    """Class which fakes being an AbstractCard for the text view."""
    # pylint: disable-msg=R0902
    # Need all the attributes to match AbstractCard

    # Keywords which obselete each other
    REPLACE_KEYWORD_MAP = {
        IKeyword('3 bleed'): [IKeyword('2 bleed'), IKeyword('1 bleed')],
        IKeyword('2 bleed'): [IKeyword('1 bleed')],
        IKeyword('3 strength'): [IKeyword('2 strength'),
                                 IKeyword('1 strength')],
        IKeyword('2 strength'): [IKeyword('1 strength')],
        IKeyword('1 strength'): [IKeyword('0 strength')],
        IKeyword('1 stealth'): [IKeyword('0 stealth')],
    }

    def __init__(self, oAbsCard):
        if oAbsCard.level:
            self.oAdvanced = oAbsCard
            self.oBase = self._find_base_vampire()
        else:
            self.oBase = oAbsCard
            self.oAdvanced = self._find_adv_vampire()
        # pylint: disable-msg=C0103
        # We duplicate AbstractCard naming here
        self.name = self.oAdvanced.name.replace('(Advanced)', '(Merged)')
        # These are never set
        self.cost = None
        self.life = None
        self.level = None
        self.creed = []
        self.rulings = []
        self.rarity = []
        self.artists = []
        self.virtue = []
        # Take these from the advanced card
        self.capacity = self.oAdvanced.capacity
        self.group = self.oAdvanced.group
        self.cardtype = self.oAdvanced.cardtype
        self.clan = self.oAdvanced.clan
        self.sect = self.oAdvanced.sect
        self.discipline = [x for x in self.oAdvanced.discipline]
        self.keywords = [x for x in self.oBase.keywords]
        for oKeyword in self.oAdvanced.keywords:
            if oKeyword not in self.keywords:
                self.keywords.append(oKeyword)
        if self.oAdvanced.title:
            self.title = [x for x in self.oAdvanced.title]
        elif self.oBase.title and self.oBase.sect == self.sect:
            self.title = [x for x in self.oBase.title]
        else:
            self.title = []
        self.text = self._make_merged_text()
        # Fix special cases and keywords
        self._fix_special_cases()
        self._fix_keywords()

    def _fix_keywords(self):
        """Fix keywords to remove duplicates and merge things as
           approriates."""
        for oReplacement, aObselete in self.REPLACE_KEYWORD_MAP.items():
            if oReplacement in self.keywords:
                for oKeyword in aObselete:
                    while oKeyword in self.keywords:
                        self.keywords.remove(oKeyword)
        self.keywords.remove(IKeyword('advanced'))
        self.keywords.append(MergedKeyword())

    def _fix_special_cases(self):
        """This is a long and tedious set of cases we need to handle."""
        # pylint: disable-msg=R0915, R0912
        # We can't really shorten this, due to the number
        # of individual special cases.
        if self.name == 'Al-Ashrad, Amr of Alamut (Merged)':
            self.title = [ITitle('Inner Circle')]
            self.keywords.append(IKeyword('3 bleed'))
            self.text = 'Camarilla ' + self.text.replace(' +1 bleed.',
                                                         ' +2 bleed.')
        elif self.name == 'Alfred Benezri (Merged)':
            self.title = [ITitle('Archbishop')]
            self.text = 'Sabbat ' + self.text
        elif self.name == 'Ambrogino Giovanni (Merged)':
            self.keywords.append(IKeyword('3 bleed'))
            self.keywords.append(IKeyword('1 stealth'))
            self.text = self.text.replace('. +1 bleed.', '. +2 bleed.')
        elif self.name == 'Batsheva (Merged)':
            self.keywords.append(IKeyword('2 strength'))
        elif self.name == 'Brunhilde (EC 2013) (Merged)':
            self.title = [ITitle('Baron')]
            self.text = self.text.replace('. Anarch Baron of Stockholm', '.')
            self.text = self.text.replace('Anarch:',
                                          'Anarch Baron of Stockholm:')
            self.text = self.text.replace('{NOT FOR LEGAL PLAY} +1 strength.',
                                          '+1 strength. {NOT FOR LEGAL PLAY}')
        elif self.name == 'Count Germaine (Merged)':
            self.text = 'Independent. ' + self.text
            self.keywords.append(IKeyword('anarch'))
        elif self.name == 'Dominique (Merged)':
            self.text = self.text.replace(
                '. Independent Anarch Baron of Paris.', '')
            self.text = self.text.replace(
                'Sabbat:', 'Independent Anarch Baron of Paris:')
            self.keywords.append(IKeyword('anarch'))
            self.title = [ITitle('Baron')]
            self.sect = [ISect('Independent')]
        elif self.name == 'Dr. Julius Sutphen (Merged)':
            self.title = [ITitle('Archbishop')]
            self.text = 'Sabbat ' + self.text
        elif self.name == 'Ferox, The Rock Lord (Merged)':
            # remove duplicate restriction
            self.text = self.text.replace(' Ferox cannot commit diablerie.',
                                          '')
        elif self.name == 'Helena (Merged)':
            # Fix disciplines
            self.discipline.remove(IDisciplinePair(('Daimoinon', 'inferior')))
            self.discipline.append(IDisciplinePair(('Daimoinon', 'superior')))
            self.discipline.append(IDisciplinePair(('Obtenebration',
                                                    'inferior')))
            self.text = self.text.replace(' and gains 1 level of Daimoinon'
                                          ' [dai] and Obtenebration'' [obt]',
                                          '')
        elif self.name == 'Ivan Krenyenko (Merged)':
            self.text = self.text.replace('. +1 strength.', '. +2 strength')
            self.keywords.append(IKeyword('3 strength'))
        elif self.name == 'Jeremy MacNeil (Merged)':
            self.text = self.text.replace(' Anarch Baron of Los Angeles.', '')
            self.text = self.text.replace(
                'Independent:', 'Independent. Anarch Baron of Los Angeles.')
            self.title = [ITitle('Baron')]
            self.keywords.append(IKeyword('anarch'))
        elif self.name == 'Jessica (Merged)':
            self.title = [ITitle('Archbishop')]
            self.text = self.text.replace(' Archbishop of Brussels.', '')
            self.text = self.text.replace('bishop', 'Archbishop of Brussels')
        elif self.name == 'Karsh (Merged)':
            self.title = [FakeTitle('Imperator')]
            self.text = 'Camarilla ' + self.text
        elif self.name == 'Kemintiri (Merged)':
            self.title = [FakeTitle('Independent with 3 votes')]
            self.text = self.text.replace(
                'Kemintiri has 3 votes (titled). ', '')
            self.text = self.text.replace(
                'Independent.', 'Independent. Kemintiri has 3 votes (titled).')
        elif self.name == 'Lambach (Merged)':
            self.text = self.text.replace(' Lambach has 2 votes (titled).', '')
            self.text = self.text.replace(
                'Independent:', 'Independent. Lambach has 2 votes ((titled).')
        elif self.name == 'Lucita (Merged)':
            self.title = [ITitle('Archbishop')]
            self.text = self.text.replace(' Archbishop of Aragon.', '')
            self.text = self.text.replace('Sabbat:',
                                          'Sabbat Archbishop of Aragon:')
        elif self.name == 'Maria Stone (Merged)':
            self.discipline.remove(IDisciplinePair(('Spiritus', 'inferior')))
            self.discipline.append(IDisciplinePair(('Spiritus', 'superior')))
            # Almost all of her text ends up cancelling out, so
            self.text = 'Sabbat: Sterile.'
        elif self.name == 'Melinda Galbraith (Merged)':
            self.keywords.append(IKeyword('3 bleed'))
            self.title = [ITitle('Regent')]
        elif self.name == 'Quentin King III (Merged)':
            self.title = [ITitle('Prince')]
            self.text = self.text.replace('Camarilla',
                                          'Camarilla Prince of Boston')
        elif self.name == 'Reverend Adams (Merged)':
            # remove duplicate restriction
            self.text = self.text.replace(
                ' Older vampires do not tap for successfully blocking'
                ' Reverend Adams.', '', 1)
        elif self.name == 'Sascha Vykos, The Angel of Caine (Merged)':
            self.title = [ITitle('Cardinal')]
            self.text = self.text.replace(' Sabbat cardinal.', '')
            self.text = self.text.replace(
                'Sabbat Archbishop of Washington, D.C', 'Sabbat cardinal')
        elif self.name == 'Tariq, The Silent (Merged)':
            self.text = self.text.replace(
                'Independent: ', 'Independent. Black Hand. Red List: ')
            # capacity restrictions and merge text cancel out
            self.text = self.text.replace(
                " Tariq's capacity is reduced by 4 while he is controlled.",
                '')
            self.text = self.text.replace(
                "Tariq's capacity is not reduced by his card text.", '')
        elif self.name == 'Tegyrius, Vizier (Merged)':
            self.title = [ITitle('Justicar')]
            self.text = self.text.replace(' Assamite Justicar.', '')
            self.text = self.text.replace('Camarilla:',
                                          'Camarilla Assamite Justicar:')
        elif self.name == "Valerius Maior, Hell's Fool (Merged)":
            self.keywords.remove(IKeyword('infernal'))
            self.keywords.remove(IKeyword('red list'))
            self.capacity = 5
            # All this text goes away with the above changes
            self.text = self.text.replace(
                'Valerius becomes non-infernal and non-Red List as he merges.'
                ' While merged, his capacity is reduced by 2. Infernal.', '')
            self.sect = [ISect('Independent')]
        elif self.name == 'Xaviar (Merged)':
            self.text = self.text.replace(' Xaviar has 2 votes (titled).', '')
        elif self.name == 'Yazid Tamari (Merged)':
            self.sect = [ISect('Independent')]
            self.keywords.append(IKeyword('anarch'))
            self.text = self.text.replace('Independent. Anarch.', '')
            self.text = self.text.replace('Sabbat.', 'Independent. Anarch.')
            self.text = self.text.replace('Black Hand:', 'Black Hand Seraph:')
        # Fix any issues caused by the various replacements
        self.text = normalise_whitespace(self.text)

    def _find_base_vampire(self):
        """Find the corresponding base vampire.

           Due to the checks in the plugin, this is assumed to be safe."""
        # pylint: disable-msg=E1103
        # pyprotocols confuses pylint
        sBaseName = self.oAdvanced.name.replace(' (Advanced)', '')
        # Special cases
        if '(EC 2013)' in sBaseName:
            sBaseName = sBaseName.replace(' (EC 2013)', '')
        return IAbstractCard(sBaseName)

    def _find_adv_vampire(self):
        """Find the corresponding advanced vampire

           Due to the checks in the plugin, this is assumed to be safe."""
        # pylint: disable-msg=E1103
        # pyprotocols confuses pylint
        sAdvName = self.oBase.name + ' (Advanced)'
        # Note that base brunhilde links to the non-storyline advanced version
        return IAbstractCard(sAdvName)

    def _make_merged_text(self):
        """Combine the text of the two versions, cleaning up keyword
           phrases and mostly handling the sect / title prefixes.
           Special cases and hard to automatically fix isses will be
           cleaned up in the special case code."""
        # pylint: disable-msg=E1103
        # pyprotocols confuses pylint
        if ':' in self.oBase.text:
            sBaseText = self.oBase.text.split(':', 1)[1]
        else:
            sBaseText = ''
        if '[MERGED]' in self.oAdvanced.text:
            sAdvText, sMergedText = self.oAdvanced.text.split('[MERGED]')
        else:
            sAdvText = self.oAdvanced.text
            sMergedText = ''
        if 'Advanced, ' in sAdvText:
            sAdvText = sAdvText.replace('Advanced, ', '')
        if ':' in sMergedText:
            sIntro, sMergedText = sMergedText.split(':', 1)
            sIntro = sIntro.strip()
            if ':' in sAdvText:
                sAdvText = sAdvText.split(':', 1)[1]
        else:
            if ':' in sAdvText:
                sIntro, sAdvText = sAdvText.split(':', 1)
            else:
                sIntro = sAdvText
                sAdvText = ''
        sFullText = ''.join([sIntro.strip(), ': ', sBaseText.strip(), '\n',
                             sAdvText.strip(), '\n', sMergedText.strip()])

        sFullText = normalise_whitespace(sFullText)
        # We normalise text by moving phrases to the end of the text
        # special cases will handle doubles we remove here and so forth
        for sPhrase in ['+1 bleed', '+2 bleed', '+1 strength', '+2 strength',
                        'Blood cursed', 'Sterile', 'Flight [FLIGHT]',
                        '+1 stealth', '+1 intercept', 'Infernal']:
            sCheckPhrase = '. %s.' % sPhrase
            if sCheckPhrase in sFullText:
                sFullText = sFullText.replace(sCheckPhrase, '.')
                sFullText += ' %s.' % sPhrase
            sCheckPhrase = ': %s.' % sPhrase
            if sCheckPhrase in sFullText:
                sFullText = sFullText.replace(sCheckPhrase, ':')
                sFullText += ' %s.' % sPhrase
        # Fix some common issues
        sFullText = sFullText.replace('.:', ':')
        return sFullText


class MergedVampirePlugin(SutekhPlugin):
    """Plugin providing access to starter deck info."""
    dTableVersions = {PhysicalCardSet: (5, 6, 7)}
    aModelsSupported = ("MainWindow",)

    # pylint: disable-msg=W0142
    # ** magic OK here
    def __init__(self, *args, **kwargs):
        super(MergedVampirePlugin, self).__init__(*args, **kwargs)
        self._oMerged = make_markup_button(
            '<span size="x-small">Show Merged</span>')
        self._oAdv = make_markup_button(
            '<span size="x-small">Show Advanced</span>')
        self._oBase = make_markup_button(
            '<span size="x-small">Show Base</span>')
        self._bMerged = False
        self._oMerged.connect('clicked', self._merge_vampire)
        self._oAdv.connect('clicked', self._show_adv_vampire)
        self._oBase.connect('clicked', self._show_base_vampire)
        self._oAbsCard = None
        self._oFakeCard = None
        self._aBaseVamps = set()
        self._make_base_map()

    def cleanup(self):
        """Remove the listener"""
        if self.check_versions() and self.check_model_type():
            MessageBus.unsubscribe(CARD_TEXT_MSG, 'post_set_text',
                                   self.post_set_card_text)
        super(MergedVampirePlugin, self).cleanup()

    def get_menu_item(self):
        """Overrides method from base class.

           Adds the menu item on the MainWindow if the starters can be found.
           """
        if not self.check_versions() or not self.check_model_type():
            return None
        MessageBus.subscribe(CARD_TEXT_MSG, 'post_set_text',
                             self.post_set_card_text)

    def post_set_card_text(self, oPhysCard):
        """Update the card text pane with the starter info"""
        self._oAbsCard = oPhysCard.abstractCard
        self._oFakeCard = None
        if self._oAbsCard.level is None:
            if self._oAbsCard not in self._aBaseVamps:
                return
        self._oFakeCard = FakeCard(self._oAbsCard)
        oCardTextView = self.parent.card_text_pane.view
        # Button logic
        # For the normal view, we show the buttons
        # "Merged" and "Other version" (Base / Advanced)
        # Because of how add_button_to_text is implemented, we
        # add the second button first
        if self._oAbsCard.level is None:
            oCardTextView.add_button_to_text(self._oAdv, "  ")
        else:
            oCardTextView.add_button_to_text(self._oBase, "  ")
        oCardTextView.add_button_to_text(self._oMerged, "\n  ")

    def _make_base_map(self):
        """Find all the vampires with advanced versions."""
        aAllAdvanced = list(SutekhAbstractCard.selectBy(level='advanced'))
        for oAbsCard in aAllAdvanced:
            sBaseName = oAbsCard.name.replace(' (Advanced)', '')
            try:
                oBaseCard = IAbstractCard(sBaseName)
                self._aBaseVamps.add(oBaseCard)
            except SQLObjectNotFound:
                # we skip the special cases here
                continue

    def _merge_vampire(self, _oWidget):
        """Display the merged version of the vampire."""
        oCardTextView = self.parent.card_text_pane.view
        oCardTextView.clear_text()

        oCardTextView.print_card_to_buffer(self._oFakeCard)
        # We show the buttons as "Normal" and "Other version"
        # where "Normal" is the card that was selected to intialise
        # the text view
        if self._oAbsCard == self._oFakeCard.oAdvanced:
            oCardTextView.add_button_to_text(self._oBase, "  ")
            oCardTextView.add_button_to_text(self._oAdv, "\n  ")
        else:
            # swap button order
            oCardTextView.add_button_to_text(self._oAdv, "  ")
            oCardTextView.add_button_to_text(self._oBase, "\n  ")

    def _show_adv_vampire(self, _oWidget):
        """Display the advanced version"""
        oCardTextView = self.parent.card_text_pane.view
        oCardTextView.clear_text()
        oCardTextView.print_card_to_buffer(self._oFakeCard.oAdvanced)
        # Duplicates button logic in post_set_card_text
        if self._oAbsCard == self._oFakeCard.oAdvanced:
            oCardTextView.add_button_to_text(self._oBase, "  ")
            oCardTextView.add_button_to_text(self._oMerged, "\n  ")
        else:
            oCardTextView.add_button_to_text(self._oMerged, "  ")
            oCardTextView.add_button_to_text(self._oBase, "\n  ")

    def _show_base_vampire(self, _oWidget):
        """Display the base version"""
        oCardTextView = self.parent.card_text_pane.view
        oCardTextView.clear_text()
        oCardTextView.print_card_to_buffer(self._oFakeCard.oBase)
        if self._oAbsCard == self._oFakeCard.oBase:
            oCardTextView.add_button_to_text(self._oAdv, "  ")
            oCardTextView.add_button_to_text(self._oMerged, "\n  ")
        else:
            oCardTextView.add_button_to_text(self._oMerged, "  ")
            oCardTextView.add_button_to_text(self._oAdv, "\n  ")


plugin = MergedVampirePlugin