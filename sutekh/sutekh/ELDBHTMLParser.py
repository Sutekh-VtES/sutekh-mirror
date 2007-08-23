# ELDBHTMLParser.py
# ELDB HTML Deck Parser
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Parser for ELDB HTML format.

   Example HTML:
   
   <TR><TD WIDTH=130>Deck Name:</TD><TD WIDTH=520>Osebo Preconstructed Starter Deck</TD></TR>
   <TR><TD WIDTH=130>Created By:</TD><TD WIDTH=520>L. Scott Johnson</TD></TR>
   <TR><TD WIDTH=130 VALIGN="top">Description:</TD><TD WIDTH=520>The Osebo Preconstructed Starter Deck from Legacies of Blood.</TD></TR>
   <TR><TD COLSPAN=2 WIDTH=650>&nbsp;</TD><TR>
   <TR><TD COLSPAN=2 WIDTH=650 BGCOLOR="#eeeeee">Crypt: (12 cards, Min: 12, Max: 36, Avg: 6.00)</TD></TR>
   <TR><TD COLSPAN=2 WIDTH=650>2&nbsp;&nbsp;<a href="http://www.white-wolf.com/vtes/index.php?line=Checklist_LegaciesOfBlood" class="textLink">Uzoma</a> ... </TD></TR>
   ...
   <TR><TD COLSPAN=2 WIDTH=650>2&nbsp;&nbsp;<a href="http://monger.vekn.org/showcard.html?ID=109" class="textLink">Blood Doll</a></TD></TR>
   """

import HTMLParser
import re

# State Base Classes

class StateError(Exception):
    pass

class State(object):
    def __init__(self,oHolder):
        super(State,self).__init__()
        self._sData = ""
        self._oHolder = oHolder

    def transition(self,sTag,dAttr):
        raise NotImplementedError

    def data(self,sData):
        self._sData += sData

# State Classes

class Collecting(State):
    def transition(self,sTag,dAttr):
        if sTag == 'td' and dAttr.get('colspan') == '2':
            return CardItem(self._oHolder)
        elif sTag == 'td':
            return DeckInfoItem(self._oHolder)
        else:
            return self

class DeckInfoItem(State):
    def transition(self,sTag,dAttr):
        if sTag == '/tr':
            aParts = self._sData.split(':',1)

            if len(aParts) != 2:
                return Collecting(self._oHolder)

            sItem, sText = aParts

            if sItem == "Deck Name":
                self._oHolder.name = sText
            elif sItem == "Created By":
                self._oHolder.author = sText
            elif sItem == "Description":
                self._oHolder.comment = sText

            return Collecting(self._oHolder)
        else:
            return self

class CardItem(State):
    _oCountRegex = re.compile(r'^[^0-9]*(?P<cnt>[0-9]+)[^0-9]*')

    def __init__(self,oHolder):
        super(CardItem,self).__init__(oHolder)
        self._iCnt = None

    def transition(self,sTag,dAttr):
        if sTag == 'a':
            oM = self._oCountRegex.match(self._sData)
            if oM:
                self._iCnt = int(oM.group('cnt'))
            else:
                self._iCnt = 1
            self._sData = ""
            return self
        elif sTag == '/a':
            assert(self._iCnt is not None)
            sName = self._sData.strip()
            sName = sName.replace("`","'")
            self._oHolder.add(self._iCnt,sName)
            self._iCnt = None
            self._sData = ""
            return Collecting(self._oHolder)
        elif sTag == '/tr':
            return Collecting(self._oHolder)
        else:
            return self

# Parser

class ELDBHTMLParser(HTMLParser.HTMLParser,object):
    def __init__(self,oHolder):
        """Create an ELDBHTMLParser.
        
           oHolder is a sutekh.CardSetHolder.CardSetHolder object (or similar).
           """
        self._oHolder = oHolder
        super(ELDBHTMLParser,self).__init__()

    def reset(self):
        super(ELDBHTMLParser,self).reset()
        self._state = Collecting(self._oHolder)

    def handle_starttag(self,sTag,aAttr):
        self._state = self._state.transition(sTag.lower(),dict(aAttr))

    def handle_endtag(self,sTag):
        self._state = self._state.transition('/'+sTag.lower(),{})

    def handle_data(self,sData):
        self._state.data(sData)

    def handle_charref(self,sName): pass
    def handle_entityref(self,sName): pass
