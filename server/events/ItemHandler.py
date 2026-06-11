from globals import getLogger, eventQueue

from backend import items
from events import SGUEvent, SendMessageEvent


def GetHandler(event: SGUEvent) -> int:
    getLogger().info(f"User with uuid {event.listener.uuid} getting item from inventory {event.payload['external_id']}", False)
    item_list = items.get_items(event.connection, items.get_internal_id(event.connection, event.payload['external_id']))
    eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "item-info", 'items': item_list, 'inventory': event.payload['external_id']}))
    return 0

def AddHandler(event: SGUEvent) -> int:
    getLogger().info(f"User with uuid {event.listener.uuid} adding {event.payload['item_qty']}x {event.payload['item_id']} to inventory {event.payload['external_id']}", False)
    qty = items.add_item(event.connection, items.get_internal_id(event.connection, event.payload['external_id']), 
                        event.payload['item_id'], event.payload['item_qty'])
    eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "item-info", 'items': [(event.payload['item_id'], qty)], 'inventory': event.payload['external_id']}))
    return 0

def RemoveHandler(event: SGUEvent) -> int:
    getLogger().info(f"User with uuid {event.listener.uuid} removing {event.payload['item_qty']}x {event.payload['item_id']} from inventory {event.payload['external_id']}", False)
    qty = items.remove_item(event.connection, items.get_internal_id(event.payload['external_id']),
                        event.payload['item_id'], event.payload['item_qty'])
    eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "item-info", 'items': [(event.payload['item_id'], qty)], 'inventory': event.payload['external_id']}))
    return 0

def DeleteHandler(event: SGUEvent) -> int:
    getLogger().info(f"User with uuid {event.listener.uuid} deleting {event.payload['item_id']} from inventory {event.payload['external_id']}", False)
    items.delete_item(event.connection, items.get_internal_id(event.connection, event.payload['external_id']), event.payload['item_id'])
    return 0

def TransferHandler(event: SGUEvent) -> int:
    getLogger().info(f"User with uuid {event.listener.uuid} transferring {event.payload['item_qty']}x {event.payload['item_id']} from inventory {event.payload['source_id']} to {event.payload['target_id']}", False)
    qtys = items.transfer_item(event.connection, event.payload['item_id'], 
                        items.get_internal_id(event.connection, event.payload['source_id']), 
                        items.get_internal_id(event.connection, event.payload['target_id']), event.payload['item_qty'])
    eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "item-info", 'items': [(event.payload['item_id'], qtys[0])], 'inventory': event.payload['source_id']}))
    eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "item-info", 'items': [(event.payload['item_id'], qtys[1])], 'inventory': event.payload['target_id']}))
    return 0