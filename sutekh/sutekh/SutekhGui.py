import sys, optparse, os, codecs
import gtk, gobject, pango
from sqlobject import *
from SutekhObjects import *

# GUI Classes

class MainWindow(gtk.Window,object):
    def __init__(self,oController):
        super(MainWindow,self).__init__()
        self.__oC = oController
        
        self.connect('destroy', lambda wWin: self.__oC.actionQuit())
        
        self.set_title("Sutekh")
        self.set_default_size(600, 400)
   
    def addParts(self,oMenu,oCardText,oAbstractCards,oPhysicalCards):
        wMbox = gtk.VBox(False, 2)
        wHbox = gtk.HBox(False, 2)
        wVbox = gtk.VBox(False, 2)
        
        wMbox.pack_start(oMenu, False, False)
        wMbox.pack_start(wHbox, expand=True)
        
        wHbox.pack_start(AutoScrolledWindow(oAbstractCards), False, False)
        wHbox.pack_start(wVbox)
                
        wVbox.pack_start(AutoScrolledWindow(oPhysicalCards), expand=True)
        wVbox.pack_start(AutoScrolledWindow(oCardText), False, False)
        
        self.add(wMbox)
        self.show_all()
         
class AutoScrolledWindow(gtk.ScrolledWindow,object):
    def __init__(self,wWidgetToWrap):
        super(AutoScrolledWindow,self).__init__()
        
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_IN)
   
        self.add(wWidgetToWrap)

class MainMenu(gtk.MenuBar,object):
    def __init__(self,oController):
        super(MainMenu,self).__init__()
        self.__oC = oController
        
        self.__createFileMenu()
        
    def __createFileMenu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("File")
        wMenu = gtk.Menu()
        iMenu.set_submenu(wMenu)
        
        # items
        iQuit = gtk.MenuItem("Quit")
        iQuit.connect('activate', lambda iItem: self.__oC.actionQuit())
        
        wMenu.add(iQuit)
        
        self.add(iMenu)

class CardTextView(gtk.TextView,object):
    def __init__(self,oController):
        super(CardTextView,self).__init__()
        self.__oC = oController
        self.__oBuf = gtk.TextBuffer(None)
        
        self.set_buffer(self.__oBuf)
        self.set_editable(False)
        self.set_cursor_visible(False)
        self.set_wrap_mode(2)

        self.set_size_request(-1,200)
        
    def setCardText(self,oCard):
        oStart, oEnd = self.__oBuf.get_bounds()
        self.__oBuf.delete(oStart,oEnd)
                
        oIter = self.__oBuf.get_iter_at_offset(0)
        self.__oBuf.insert(oIter,self.printCard(oCard))
        
    def printCard(self,oCard):
        s = oCard.name
        
        if not oCard.cost is None:
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

class CardListView(gtk.TreeView,object):
    def __init__(self,oController):
        self._oModel = gtk.TreeStore(gobject.TYPE_STRING,gobject.TYPE_INT)
    
        super(CardListView,self).__init__(self._oModel)
        self._oC = oController
        
        self.set_size_request(200, -1)
        
        self._oSelection = self.get_selection()
        self._oSelection.set_mode(gtk.SELECTION_BROWSE)
        
        self.connect('row-activated',self.cardActivated)
        self._oSelection.connect('changed',self.cardSelected)

        self.expand_all()
        
    def cardActivated(self,wTree,oPath,oColumn):
        oModel = wTree.get_model()
        oIter = oModel.get_iter(oPath)
        sCardName = oModel.get_value(oIter,0)
        self._oC.setCardText(sCardName)
    
    def cardSelected(self,oSelection):
        oModel, oIter = oSelection.get_selected()
        if not oIter:
            return False
        sCardName = oModel.get_value(oIter,0)
        self._oC.setCardText(sCardName)


class AbstractCardView(CardListView):
    def __init__(self,oController):
        super(AbstractCardView,self).__init__(oController)
    
        oCell = gtk.CellRendererText()
        oCell.set_property('style', pango.STYLE_ITALIC)
        oColumn = gtk.TreeViewColumn("Collection", oCell, text=0)
        self.append_column(oColumn)
        
        aTargets = [ ('STRING', 0, 0), # second 0 means TARGET_STRING
                     ('text/plain', 0, 0) ] # and here
        self.drag_source_set(gtk.gdk.BUTTON1_MASK | gtk.gdk.BUTTON3_MASK,
                  aTargets, gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
        self.connect('drag_data_get',self.dragCard)
        self.connect('drag_data_delete',self.dragDelete)
        
        self.load()
        
    def dragCard(self, btn, context, selection_data, info, time):
        oModel, oIter = self._oSelection.get_selected()
        if not oIter:
            return
        sCardName = oModel.get_value(oIter,0)
        selection_data.set(selection_data.target, 8, sCardName)
    
    def dragDelete(self, btn, context, data):
        pass
        
    def load(self):
        self._oModel.clear()
        
        for oType in CardType.select():
            # Create Section
            oSectionIter = self._oModel.append(None)
            self._oModel.set(oSectionIter,
                0, oType.name,
                1, 0
            )
            
            # Fill in Cards
            for oCard in oType.cards:
                oChildIter = self._oModel.append(oSectionIter)
                self._oModel.set(oChildIter,
                    0, oCard.name,
                    1, 0
                )
    
class PhysicalCardView(CardListView):
    def __init__(self,oController):
        super(PhysicalCardView,self).__init__(oController)
        
        oCell1 = gtk.CellRendererText()
        oCell1.set_property('style', pango.STYLE_ITALIC)
        oCell2 = gtk.CellRendererText()
        oCell2.set_property('style', pango.STYLE_ITALIC)
        oCell3 = gtk.CellRendererToggle()
        oCell4 = gtk.CellRendererToggle()
        
        oColumn1 = gtk.TreeViewColumn("#",oCell1,text=1)
        self.append_column(oColumn1)
        oColumn1.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        oColumn1.set_fixed_width(20)
        oColumn2 = gtk.TreeViewColumn("Cards", oCell2, text=0)
        oColumn2.set_expand(True)
        self.append_column(oColumn2)
        oColumn3 = gtk.TreeViewColumn("",oCell3)
        oColumn3.set_fixed_width(20)
        oColumn3.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.append_column(oColumn3)
        oColumn4 = gtk.TreeViewColumn("",oCell4)
        oColumn4.set_fixed_width(20)
        oColumn4.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.append_column(oColumn4) 

        self.set_expander_column(oColumn2)
       
        oCell3.connect('toggled',self.incCard)
        oCell4.connect('toggled',self.decCard)

        aTargets = [ ('STRING', 0, 0), # second 0 means TARGET_STRING
                     ('text/plain', 0, 0) ] # and here
        self.drag_dest_set(gtk.DEST_DEFAULT_ALL, aTargets, gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
        self.connect('drag_data_received',self.cardDrop)
        
        self.load()
               
    def incCard(self,oCell,oPath):
        oIter = self._oModel.get_iter(oPath)
        sCardName = self._oModel.get_value(oIter,0)
        self._oC.incCard(sCardName)
    
    def decCard(self,oCell,oPath):
        oIter = self._oModel.get_iter(oPath)
        sCardName = self._oModel.get_value(oIter,0)
        self._oC.decCard(sCardName)
    
    def cardDrop(self, w, context, x, y, data, info, time):
        if data and data.format == 8:
            self._oC.addCard(data.data)
            context.finish(True, False, time)
        else:
            context.finish(False, False, time)
    
    def load(self):
        self._oModel.clear()
        # oIter = self._oModel.append(None)
        # This feels a bit clumsy, but does work - NM
        cardDict = {}
        
        for oCard in PhysicalCard.select():                            
            # Check if Card is already in dictionary
            if oCard.abstractCardID in cardDict:
               cardDict[oCard.abstractCardID]+=1
               # Find correct row
               # There may be an easier way of doing this, rather
               # than iterating over the entire list
               oIter=self._oModel.get_iter_first()
               while oIter:
                  Name=self._oModel.get_value(oIter,0)
                  if Name==oCard.abstractCard.name:
                     # Update row entry
                     self._oModel.set_value(oIter,1,cardDict[oCard.abstractCardID])
                     break
                  oIter=self._oModel.iter_next(oIter)
            else:
               cardDict[oCard.abstractCardID]=1
               # add new row entry
               self._oModel.set(self._oModel.append(None),
                  0, oCard.abstractCard.name,
                  1, cardDict[oCard.abstractCardID],
               )

        # I'm not sure if an alternative approach isn't better:
        # rather than find and update each row in turn, merely update the
        # dict, and do an iteration over the dict, adding each card in
        # turn - something like
        # for cD in cardDict:
        #     oC = PhysicalCard.selectBy(abstractCardID=cD) 
        #     self._oModel.set(self._oModel.append(None),
        #           0, oC[-1].abstractCard.name,
        #           1, cardDict[cD]
        #     )
            
        self.expand_all()

class PhysicalCardController(object):
    def __init__(self,oMasterController):
        self.__oView = PhysicalCardView(self)
        self.__oC = oMasterController
        
    def getView(self):
        return self.__oView
    
    def decCard(self,sName):
        try:
            oC = AbstractCard.byName(sName)
        except SQLObjectNotFound:
            return
        # Go from Name to Abstract Card ID to Physical card ID 
        # which is needed for delete
        # find Physical cards cards with this name
        cardCands=PhysicalCard.selectBy(abstractCardID=oC.id)
        # check we found something?
        if cardCands.count()==0:
            return
        # delete last from list (habit)
        PhysicalCard.delete(cardCands[-1].id)
        # Removed card, so reload list - NM
        self.__oView.load()
    
    def incCard(self,sName):
        try:
            oC = AbstractCard.byName(sName)
        except SQLObjectNotFound:
            return
        oPC = PhysicalCard(abstractCard=oC)
        # Inc'ed card, so reload list - NM
        self.__oView.load()
    
    def addCard(self,sName):
        try:
            oC = AbstractCard.byName(sName)
        except SQLObjectNotFound:
            return
        oPC = PhysicalCard(abstractCard=oC)
        self.__oView.load()
        
    def setCardText(self,sCardName):
        self.__oC.setCardText(sCardName)
    
class MainController(object):
    def __init__(self):
        # Create Sub-Controllers
        self.__oPhysicalCards = PhysicalCardController(self)
    
        # Create Views
        self.__oWin = MainWindow(self)
        self.__oMenu = MainMenu(self)
        self.__oCardText = CardTextView(self)
        self.__oAbstractCards = AbstractCardView(self)
                
        # Link
        self.__oWin.addParts(self.__oMenu,self.__oCardText, \
                             self.__oAbstractCards,self.__oPhysicalCards.getView())
        
    def run(self):
        gtk.main()
        
    def actionQuit(self):
        gtk.main_quit()

    def setCardText(self,sCardName):
        try:
            oCard = AbstractCard.byName(sCardName)
            self.__oCardText.setCardText(oCard)
        except SQLObjectNotFound:    
            pass
    
        
# Script Launching    

def parseOptions(aArgs):
    oP = optparse.OptionParser(usage="usage: %prog [options]",version="%prog 0.1")
    oP.add_option("-d","--db",
                  type="string",dest="db",default=None,
                  help="Database URI. [./sutekh.db]")
    return oP, oP.parse_args(aArgs)

def main(aArgs):
    oOptParser, (oOpts, aArgs) = parseOptions(aArgs)
    
    if len(aArgs) != 1:
        oOptParser.print_help()
        return 1
        
    if oOpts.db is None:
        oOpts.db = "sqlite://" + os.path.join(os.getcwd(),"sutekh.db")

    oConn = connectionForURI(oOpts.db)
    sqlhub.processConnection = oConn
    
    MainController().run()

if __name__ == "__main__":
    sys.exit(main(sys.argv))
