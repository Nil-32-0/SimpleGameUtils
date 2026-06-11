from globals import getLogger

from backend import items
from events.Events import SGUEvent

def AddHandler(event: SGUEvent) -> int:
    getLogger().info(f"User with uuid {event.listener.uuid} is adding inventory {event.payload['external_id']}", False)
    items.add_inventory(event.connection, event.payload['external_id'])
    return 0

def RemoveHandler(event: SGUEvent) -> int:
    getLogger().info(f"User with uuid {event.listener.uuid} is removing inventory {event.payload['external_id']}", False)
    items.remove_inventory(event.connection, event.payload['external_id'])
    return 0