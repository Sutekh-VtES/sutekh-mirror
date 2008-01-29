# Dialog with progress meter
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>

import gtk
from logging import Handler

class SutekhLogger(Handler):
    # Use messages sent to the logger to update a progress bar
    def __init__(self, oDialog):
        # Handler is a classic class, so super doesn't work. Blergh
        Handler.__init__(self)
        self.oDialog = oDialog

    def emit(self, record):
        self.oDialog.step_bar()

class ProgressDialog(gtk.Window):
    """
    Show a window with a single progress bar.
    """
    # This is not a proper dialog, since we don't want the blocking 
    # behaviour of Dialog.run()
    def __init__(self, oParent, sDescription, iMax):
        super(ProgressDialog, self).__init__()
        self.set_title('Progress')
        self._oLogHandler = SutekhLogger(self)
        oDescription = gtk.Label(sDescription)
        self.oProgressBar = gtk.ProgressBar()
        self.oProgressBar.set_orientation(gtk.PROGRESS_LEFT_TO_RIGHT)
        self.oProgressBar.set_text('% done')
        self.oProgressBar.set_fraction(0.0)
        self.oProgressBar.set_size_request(350, 50)
        self.set_default_size(400, 100)
        oVBox = gtk.VBox()
        self.fMax = float(iMax)
        self.iStep = 0
        # Centre the progress bar horizontally
        oAlign = gtk.Alignment(xalign=0.5, yalign=0.0)
        oAlign.add(self.oProgressBar)
        oVBox.pack_start(oDescription)
        oVBox.pack_start(oAlign)
        self.add(oVBox)
        self.show_all()
        self.set_modal(True)


    log_handler = property(fget=lambda self: self._oLogHandler, doc="LogHandler object")

    def reset(self):
        self.iStep = 0
        self.update_bar(0)

    def step_bar(self):
        """
        Bump the counter by 1
        """
        self.iStep += 1
        if self.iStep > self.fMax:
            fCurStep = 1.0 # gtk.ProgressBar dislikes values > 1.0
        else:
            fCurStep = self.iStep / self.fMax
        self.update_bar(fCurStep)

    def set_complete(self):
         """
         Set the progress bar as being complete
         """
         self.update_bar(1.0)

    def update_bar(self, fStep):
        """
        update the progress bar to the given fStep value
        """
        self.oProgressBar.set_fraction(fStep)
        # Since Sutekh is single threaded, and some IO bound
        # task has the gtk.main loop process, we fudge the
        # required behaviour to get the update drawn
        while gtk.events_pending():
            gtk.main_iteration()


