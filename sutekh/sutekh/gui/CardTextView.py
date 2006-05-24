# CardTextView.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk

class CardTextView(gtk.TextView,object):
    def __init__(self,oController):
        super(CardTextView,self).__init__()
        self.__oC = oController
        self.__oBuf = gtk.TextBuffer(None)
        
        self.set_buffer(self.__oBuf)
        self.set_editable(False)
        self.set_cursor_visible(False)
        self.set_wrap_mode(2)

        self.set_size_request(-1,250)
        
    def setCardText(self,oCard):
        oStart, oEnd = self.__oBuf.get_bounds()
        self.__oBuf.delete(oStart,oEnd)
                
        oIter = self.__oBuf.get_iter_at_offset(0)
        self.__oBuf.insert(oIter,self.printCard(oCard))
        
    def printCard(self,oCard):
        s = oCard.name
        
        if not oCard.cost is None:
            if oCard.cost == -1:
                s += "\nCost: X " + str(oCard.costtype)
            else:
                s += "\nCost: " + str(oCard.cost) + " " + str(oCard.costtype)
        
        if not oCard.capacity is None:
            s += "\nCapacity: " + str(oCard.capacity)
        
        if not oCard.group is None:
            s += "\nGroup: " + str(oCard.group)
            
        if not oCard.level is None:
            s += "\nLevel: " + str(oCard.level)
        
        s += "\nCard Type:"
        if len(oCard.cardtype) == 0:
            s += "\n\t* Unknown"
        for oT in oCard.cardtype:
            s += "\n\t* " + oT.name
        
        if not len(oCard.clan) == 0:
            s += "\nClan:"
        for oC in oCard.clan:
            s += "\n\t* " + oC.name
        
        if not len(oCard.discipline) == 0:
            s += "\nDisciplines:"
        for oP in oCard.discipline:
            if oP.level == 'superior':
                s += "\n\t* " + oP.discipline.name.upper()
            else:
                s += "\n\t* " + oP.discipline.name
                
        if not len(oCard.rarity) == 0:
            s += "\nExpansions:"
        for oP in oCard.rarity:
            s += "\n\t* " + oP.expansion.name + " (" + oP.rarity.name + ")"
        
        if not len(oCard.rulings) == 0:
            s += "\nRulings:"
        for oR in oCard.rulings:
            s += "\n\t* " + oR.text.replace("\n"," ") + " " + oR.code
            
        s += "\n\n" + oCard.text.replace("\n"," ")
        
        return s
