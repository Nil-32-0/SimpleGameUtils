from globals import eventQueue, getLogger

from backend import items, projects
from events.EventHandler import handleEvent
from events.Events import AuthActionEvent, SGUEvent, SendMessageEvent
from events.EventType import EventType

def TrackHandler(event: SGUEvent) -> int:
    getLogger().info(f"User with uuid {event.listener.uuid} tracking {event.payload['item_qty']}x {event.payload['item_id']} in project {event.payload['project_id']}", False)
    if handleEvent(AuthActionEvent(EventType.AUTH_PROJECT, event.listener, event.transport, "member", event.payload['project_id'])) != 0:
        return 1
    projects.add_item(event.connection, event.payload['project_id'], event.payload['item_id'], event.payload['item_qty'])
    getLogger().info("Tracking successful", False)
    return 0

def DeleteHandler(event: SGUEvent) -> int:
    getLogger().info(f"User with uuid {event.listener.uuid} deleting item {event.payload['item_id']} from project {event.payload['project_id']}", False)
    if handleEvent(AuthActionEvent(EventType.AUTH_PROJECT, event.listener, event.transport, "member", event.payload['project_id'])) != 0:
        return 1
    projects.remove_item(event.connection, event.payload['project_id'], event.payload['item_id'])
    getLogger().info("Deletion successful", False)
    return 0

def AddHandler(event: SGUEvent) -> int:
    getLogger().info(f"User with uuid {event.listener.uuid} adding {event.payload['item_qty']}x {event.payload['item_id']} to project {event.payload['project_id']}", False)
    if handleEvent(AuthActionEvent(EventType.AUTH_PROJECT, event.listener, event.transport, "member", event.payload['project_id'])) != 0:
        return 1
    qty = items.add_item(event.connection, items.get_internal_id(event.connection, event.payload['external_id']), event.payload['item_id'],
                    event.payload['item_qty'], event.payload['project_id'])
    eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "project-item-info", 'items': [(event.payload['item_id'], qty)], 'inventory': event.payload['external_id'], 
                            'project_id': event.payload['project_id']}))
    getLogger().info("Addition successful", False)
    return 0

def RemoveHandler(event: SGUEvent) -> int:
    getLogger().info(f"User with uuid {event.listener.uuid} removing {event.payload['item_qty']}x {event.payload['item_id']} from project {event.payload['project_id']}", False)
    if handleEvent(AuthActionEvent(EventType.AUTH_PROJECT, event.listener, event.transport, "member", event.payload['project_id'])) != 0:
        return 1
    qty = items.remove_item(event.connection, items.get_internal_id(event.connection, event.payload['external_id']), event.payload['item_id'],
                    event.payload['item_qty'], event.payload['project_id'])
    eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "project-item-info", 'items': [(event.payload['item_id'], qty)], 'inventory': event.payload['external_id'], 
                            'project_id': event.payload['project_id']}))
    getLogger().info("Removal successful", False)
    return 0

def ReserveHandler(event: SGUEvent) -> int:
    getLogger().info(f"User with uuid {event.listener.uuid} reserving {event.payload['item_qty']}x {event.payload['item_id']} for project {event.payload['project_id']}", False)
    if handleEvent(AuthActionEvent(EventType.AUTH_PROJECT, event.listener, event.transport, "member", event.payload['project_id'])) != 0:
        return 1
    qty1, qty2 = items.reserve_items(event.connection, event.payload['item_id'], items.get_internal_id(event.connection, event.payload['external_id']),
                        event.payload['target_project_id'], event.payload['item_qty'], 
                        event.payload['source_project_id'] if int(event.payload['source_project_id']) == -1 else None)
    
    eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "project-item-info", 'items': [(event.payload['item_id'], qty1)], 'inventory': event.payload['external_id'],
                            'project_id': event.payload['source_project_id']}))
    eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "project-item-info", 'items': [(event.payload['item_id'], qty2)], 'inventory': event.payload['external_id'],
                            'project_id': event.payload['target_project_id']}))
    getLogger().info("Reservation successful", False)
    return 0

def ReleaseHandler(event: SGUEvent) -> int:
    getLogger().info(f"User with uuid {event.listener.uuid} releasing {event.payload['item_qty']}x {event.payload['item_id']} from project {event.payload['project_id']}", False)
    if handleEvent(AuthActionEvent(EventType.AUTH_PROJECT, event.listener, event.transport, "member", event.payload['project_id'])) != 0:
        return 1
    qty1, qty2 = items.unreserve_items(event.connection, event.payload['item_id'], items.get_internal_id(event.connection, event.payload['external_id']),
                                        event.payload['project_id'], event.payload['item_qty'])
    eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "project-item-info", 'items': [(event.payload['item_id'], qty1)], 'inventory': event.payload['external_id'],
                            'project_id': event.payload['project_id']}))
    eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "project-item-info", 'items': [(event.payload['item_id'], qty1)], 'inventory': event.payload['external_id'],
                            'project_id': -1}))
    getLogger().info("Release successful", False)
    return 0