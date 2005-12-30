import sys, optparse, os, codecs
import gtk, gobject, pango
from sqlobject import *
from SutekhObjects import *

# GUI Classes

# Pixbuf Button CellRenderer - limited to icons only ATM - NM 
# This is heavily cribbed from the example in the pygtk FAQ 
# (By Nikos Kouremenos)
# Allows creation of a cell containing a icon pixbuf,
# and returns a "clicked" signal when activated
# To be generically useful, should be extended to abitary pixmaps,
# but that is currently not a priority
class CellRendererSutekhButton(gtk.GenericCellRenderer):
    def __init__(self):
        self.__gobject_init__()
        self.pixbuf = None
        self.set_property("mode",gtk.CELL_RENDERER_MODE_ACTIVATABLE)

    def load_icon(self,name,widget):
        # Load the icon specified in name
        self.pixbuf=widget.render_icon(name,gtk.ICON_SIZE_SMALL_TOOLBAR)
           

    def on_get_size(self,widget,cell_area):
        if self.pixbuf==None:
            return 0, 0, 0, 0
        pixbuf_width  = self.pixbuf.get_width()
        pixbuf_height = self.pixbuf.get_height()
        calc_width  = self.get_property("xpad") * 2 + pixbuf_width
        calc_height = self.get_property("ypad") * 2 + pixbuf_height
        x_offset = 0
        y_offset = 0
        if cell_area and pixbuf_width > 0 and pixbuf_height > 0:
            x_offset = self.get_property("xalign") * (cell_area.width - \
                calc_width -  self.get_property("xpad"))
            y_offset = self.get_property("yalign") * (cell_area.height - \
                calc_height -  self.get_property("ypad"))
        return x_offset, y_offset, calc_width, calc_height

    def on_activate(self, event, widget, path, background_area, cell_area, flags):
        # TODO - setup drawing of clicked image
        # clicke dcallback should be called
        self.emit('clicked',path)
        return True
     
    def on_render(self,window, widget, background_area, cell_area, expose_area, flags):
       if (self.pixbuf==None):
          return None
       # Render pixbuf
       pix_rect = gtk.gdk.Rectangle()
       pix_rect.x, pix_rect.y, pix_rect.width, pix_rect.height = \
          self.on_get_size(widget, cell_area)

       pix_rect.x += cell_area.x
       pix_rect.y += cell_area.y
       pix_rect.width  -= 2 * self.get_property("xpad")
       pix_rect.height -= 2 * self.get_property("ypad")

       draw_rect = cell_area.intersect(pix_rect)
       draw_rect = expose_area.intersect(draw_rect)

       window.draw_pixbuf(widget.style.black_gc, self.pixbuf, \
          draw_rect.x-pix_rect.x, draw_rect.y-pix_rect.y, draw_rect.x, \
          draw_rect.y+2, draw_rect.width, draw_rect.height, \
          gtk.gdk.RGB_DITHER_NONE, 0, 0)
       return None

# HouseKeeping work for CellRendererStukehButton
# Awkward stylistically, but I'm putting it here as it's
# associated with class creation (is global to the class)
# so doesn't belong in the per-instance constructor - NM
# Register class, needed to make clicked signal go to right class
# (otherwise it gets associated with GenericCellRenderer, which is
# not desireable)
gobject.type_register(CellRendererSutekhButton)
# Setup clicked signal -- can also be done using the __gsignals__
# dict in the class, but I couldn't find good documentation for
# that approach. 
gobject.signal_new("clicked", CellRendererSutekhButton,
    gobject.SIGNAL_RUN_FIRST|gobject.SIGNAL_ACTION,
   gobject.TYPE_NONE,
   (gobject.TYPE_STRING,)) 
# the callback is called as callback(self,path)

# Main Window

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
        self.__createDeckMenu()
        
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

    def __createDeckMenu(self):
        iMenu = gtk.MenuItem("Deck")
        wMenu=gtk.Menu()
        iMenu.set_submenu(wMenu)

        iCreate=gtk.MenuItem("Create New Deck")
        wMenu.add(iCreate)

        iLoad=gtk.MenuItem("Load an Existing Deck")
        wMenu.add(iLoad)

        iDelete=gtk.MenuItem("Delete Current Deck")
        wMenu.add(iDelete)

        iClose=gtk.MenuItem("Close Deck View")
        wMenu.add(iClose)

        iAnalyze = gtk.MenuItem("Analyze Deck")
        wMenu.add(iAnalyze)

        self.add(iMenu)
        

class PopupMenu(gtk.Menu):
   def __init__(self,view,path):
      super(PopupMenu,self).__init__()
      iInc=gtk.MenuItem("Increase Card Count")
      iDec=gtk.MenuItem("Decrease Card Count")
      iInc.connect("activate",view.incCard,path)
      iDec.connect("activate",view.decCard,path)
      # Apprantly need these shows as we're using the popup method,
      # which doesn't seem to call them automatically
      iInc.show()
      iDec.show()
      self.add(iInc)
      self.add(iDec)

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

        # HouseKeeping work for 
    
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
        oCell3 = CellRendererSutekhButton()
        oCell4 = CellRendererSutekhButton()
        oCell3.load_icon(gtk.STOCK_GO_UP,self)
        oCell4.load_icon(gtk.STOCK_GO_DOWN,self)
        #oCell3 = gtk.CellRendererToggle()
        #oCell4 = gtk.CellRendererToggle()
        
        oColumn1 = gtk.TreeViewColumn("#",oCell1,text=1)
        self.append_column(oColumn1)
        oColumn1.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        oColumn1.set_fixed_width(40)
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
     
        oCell3.connect('clicked',self.incCard)
        oCell4.connect('clicked',self.decCard)

        aTargets = [ ('STRING', 0, 0), # second 0 means TARGET_STRING
                     ('text/plain', 0, 0) ] # and here
        self.drag_dest_set(gtk.DEST_DEFAULT_ALL, aTargets, gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
        self.connect('drag_data_received',self.cardDrop)
        self.connect('button_press_event',self.pressButton)

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
                cardDict[oCard.abstractCardID][1] += 1
            else:
                cardDict[oCard.abstractCardID] = [oCard.abstractCard.name,1]
         
        aCards = list(cardDict.iteritems())
        aCards.sort(lambda x,y: cmp(x[1],y[1]))
 
        for iD, aItems in aCards:
            sName, iCnt = aItems
            self._oModel.set(self._oModel.append(None),
                0, sName,
                1, iCnt
            )   

        self.expand_all()

    def pressButton(self, treeview, event):
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            time = event.time
            pthinfo = treeview.get_path_at_pos(x, y)
            if pthinfo != None:
                path, col, cellx, celly = pthinfo
                treeview.grab_focus()
                treeview.set_cursor( path, col, False)
                popupMenu=PopupMenu(self,path)
                print gobject.list_properties(col)
                print path, cellx, celly
                popupMenu.popup( None, None, None, event.button, time)
                return True # Don't propogate to buttons
        return False


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


