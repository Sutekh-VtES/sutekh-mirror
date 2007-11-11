# Define the reload singal we need 

from sqlobject.events import Signal, listen, RowUpdateSignal, RowDestroySignal
from sutekh.core.SutekhObjects import PhysicalCard

class ReloadSignal(Signal):
    """Syncronisation signal for card sets. Needs to be sent after
       changes are commited to the database, so card sets can reload
       properly
    """

def send_reload_signal(oAbstractCard):
    PhysicalCard.sqlmeta.send(ReloadSignal, oAbstractCard)

