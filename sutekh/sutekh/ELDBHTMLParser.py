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
from sqlobject import SQLObjectNotFound
from sutekh.SutekhObjects import AbstractCardSet, AbstractCard

# Abstract Card Set Holder

class ACSHolder(object):
    def __init__(self):
        self._sName, self._sAuthor, self._sComment, self._sAnnotations = None, None, None, None
        self._aCards = [] # list of (#, Abstract Card) tuples
        self._aUnknownCards = [] # list of (#, Card Name) tuples for cards which weren't found

    def addCards(self,iCnt,sName):
        """Append cards to either the known or unknown card list.
           """
        try:
            oAbs = AbstractCard.byCanonicalName(sName.encode('utf8').lower())
            self._aCards.append((iCnt,oAbs))
        except SQLObjectNotFound:
            self._aUnknownCards.append((iCnt,sName))

    def createACS(self):
        """Create an Abstract Card Set.
           """
        if self.name is None:
            raise RuntimeError("No name for the card set")
        oACS = AbstractCardSet(name=self.name.encode('utf8'),
                               author=self.author, comment=self.comment,
                               annotations=self.annotations)
        oACS.syncUpdate()

        for iCnt, oAbs in self._aCards:
            for i in range(iCnt):
                oACS.addAbstractCard(oAbs)

    def unknownCards(self):
        """Retrieve the list of unknown card names (and the number of each card included).
        
           Return looks like [ (3, 'Some Unknown Card), (4, 'Another Unknown Card'), ... ].
           """
        return self._aUnknownCards

    name = property(fget = lambda self: self._sName, fset = lambda self, x: setattr(self,'_sName',x))
    author = property(fget = lambda self: self._sAuthor, fset = lambda self, x: setattr(self,'_sAuthor',x))
    comment = property(fget = lambda self: self._sComment, fset = lambda self, x: setattr(self,'_sComment',x))
    annotations = property(fget = lambda self: self._sAnnotations, fset = lambda self, x: setattr(self,'_sAnnotations',x))

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
            self._oHolder.addCards(self._iCnt,sName)
            self._iCnt = None
            self._sData = ""
            return Collecting(self._oHolder)
        elif sTag == '/tr':
            return Collecting(self._oHolder)
        else:
            return self

# Parser

class ELDBHTMLParser(HTMLParser.HTMLParser,object):
    def reset(self):
        super(ELDBHTMLParser,self).reset()
        self._oHolder = ACSHolder()
        self._state = Collecting(self._oHolder)

    def handle_starttag(self,sTag,aAttr):
        self._state = self._state.transition(sTag.lower(),dict(aAttr))

    def handle_endtag(self,sTag):
        self._state = self._state.transition('/'+sTag.lower(),{})

    def handle_data(self,sData):
        self._state.data(sData)

    def handle_charref(self,sName): pass
    def handle_entityref(self,sName): pass

    def holder(self):
        return self._oHolder
