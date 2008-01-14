# Define the reload singal we need

from sqlobject.events import Signal, listen, RowUpdateSignal, RowDestroySignal
from sutekh.core.SutekhObjects import PhysicalCard

class ReloadSignal(Signal):
    """Syncronisation signal for card sets. Needs to be sent after
       changes are commited to the database, so card sets can reload
       properly
    """

# Senders

def send_reload_signal(oAbstractCard, cClass=PhysicalCard):
    cClass.sqlmeta.send(ReloadSignal, oAbstractCard)

# Listeners

def listen_reload(fListener, cClass):
    listen(fListener, cClass, ReloadSignal)

def listen_row_destroy(fListener, cClass):
    listen(fListener, cClass, RowDestroySignal)

def listen_row_update(fListener, cClass):
    listen(fListener, cClass, RowUpdateSignal)

