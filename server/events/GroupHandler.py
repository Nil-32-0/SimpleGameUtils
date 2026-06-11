from globals import *

from backend import auth, groups
from events.Events import *
from events.EventHandler import handleEvent
from events.EventType import EventType

def CreationHandler(event: SGUEvent) -> int:
    getLogger().info(f"Creating group with name {event.payload['group_name']}", False)

    groupId = groups.create_group(event.connection, event.listener.uuid, event.payload['group_name'])
    eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {
        'type': "group-success",
        'message': f"Group '{event.payload['group_name']}' with id {groupId} has been created."
    }))
    getLogger().info(f"Group successfully created with ID {groupId}", False)
    return 0

def AuthUser(event: AuthActionEvent) -> int:
    match event.level:
        case "owner":
            if event.id in groups.get_owned_groups(event.connection, event.listener.uuid): return 0
            eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {
                    'type': "error",
                    'message': "You can't perform that action on a group you don't own!"
                }))
    getLogger().warn(f"User with uuid {event.listener.uuid} does not have {event.level} permissions to perform actions on group {event.id}", True)
    return 1

def DeletionHandler(event: SGUEvent) -> int:
    getLogger().info(f"Deleting group with id {event.payload['group_id']}", False)
    if handleEvent(AuthActionEvent(EventType.AUTH_GROUP, event.listener, event.transport, "owner", event.payload['group_id'])) != 0: 
        return 1
    
    groups.delete_group(event.connection, event.payload['group_id'])
    eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {
        'type': "group-success", 
        'message': "The '" + groups.get_group_name(event.connection, event.payload['group_id']) + "' group has been deleted."
    }))
    getLogger().info("Deletion success", False)
    return 0

def TransferHandler(event: SGUEvent) -> int:
    getLogger().info(f"Transferring group with id {event.payload['group_id']} to user {event.payload['new_owner_username']}", False)
    if handleEvent(AuthActionEvent(EventType.AUTH_GROUP, event.listener, event.transport, "owner", event.payload['group_id'])) != 0:
        return 1
    if not auth.username_exists(event.connection, event.payload['new_owner_username']):
        eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "error", 'message': "You can't transfer ownership to a player who doesn't exist!"}))
        getLogger().warn(f"User with uuid {event.listener.uuid} attempted to transfer a group to a nonexistent player", True)
        return 1
    
    new_uuid = auth.get_uuid_from_username(event.connection, event.payload['new_owner_username'])

    if new_uuid == event.listener.uuid:
        eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "error", 'message': "You can't transfer ownership of a group to yourself!"}))
        getLogger().warn(f"User with uuid {event.listener.uuid} attempted to transfer a group to themself", True)
        return 1
    if new_uuid not in groups.get_group_members(event.connection, event.payload['group_id']):
        eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "error", 'message': "You can't transfer ownership of a group to a member that isn't in it!"}))
        getLogger().warn(f"User with uuid {event.listener.uuid} attempted to transfer a group to a player who isn't in it", False) # Could be an actual mistake, don't print to console
        return 1

    groups.transfer_ownership(event.connection, new_uuid, event.payload['group_id'])
    eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {
        'type': "group-success",
        'message': "The '" + groups.get_group_name(event.connection, event.payload['group_id']) + "' group has been transfered to " + event.payload['new_owner_username'] + "."
    }))
    getLogger().info("Transfer success", False)
    return 0

def AddHandler(event: SGUEvent) -> int:
    getLogger().info(f"Adding user {event.payload['new_member_username']} to group with id {event.payload['group_id']}", False)
    if handleEvent(AuthActionEvent(EventType.AUTH_GROUP, event.listener, event.transport, "owner", event.payload['group_id'])) != 0:
        return 1
    if not auth.username_exists(event.connection, event.payload['new_member_username']):
        eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "error", 'message': "You can't add a player who doesn't exist!"}))
        getLogger().warn(f"User with uuid {event.listener.uuid} attempted to add a player who doesn't exist to a group", True)
        return 1
    
    new_uuid = auth.get_uuid_from_username(event.connection, event.payload['new_member_username'])

    if new_uuid == event.listener.uuid:
        eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "error", 'message': "You can't add yourself to a group you're already in!"}))
        getLogger().warn(f"User with uuid {event.listener.uuid} attempted to add themself to a group they own", True)
        return 1
    
    groups.add_user(event.connection, new_uuid, event.payload['group_id'])
    eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {
        'type': "group-success",
        'message': event.payload['new_member_username'] + " has been added to the '" + 
            groups.get_group_name(event.connection, event.payload['group_id']) + "' group."
    }))
    getLogger().info("Addition success", False)
    return 0

def RemoveHandler(event: SGUEvent) -> int:
    getLogger().info(f"Removing user {event.payload['member_username']} from group with id {event.payload['group_id']}", False)
    if handleEvent(AuthActionEvent(EventType.AUTH_GROUP, event.listener, event.transport, "owner", event.payload['group_id'])) != 0:
        return 1
    if not auth.username_exists(event.connection, event.payload['member_username']):
        eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "error", 'message': "You can't remove a player who doesn't exist!"}))
        getLogger().warn(f"User with uuid {event.listener.uuid} attempted to remove a player who doesn't exist from a group", True)
        return 1

    user_uuid = auth.get_uuid_from_username(event.connection, event.payload['member_username'])
    if event.listener.uuid == user_uuid:
        eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "error", 'message': "You can't remove yourself from a group you own!"}))
        getLogger().warn(f"User with uuid {event.listener.uuid} attempted to remove themself from a group they own", True)
        return 1
    if user_uuid not in groups.get_group_members(event.connection, event.payload['group_id']):
        eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "error", 'message': "You can't remove a player who isn't in the group!"}))
        getLogger().warn(f"User with uuid {event.listener.uuid} attempted to remove a player who isn't in the group", False)
        return 1
    
    groups.remove_user(event.connection, user_uuid, event.payload['group_id'])
    eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {
        'type': "group-success",
        'message': event.payload['member_username'] + " has been removed from the '" + 
            groups.get_group_name(event.connection, event.payload['group_id']) + "' group."
    }))
    getLogger().info("Removal success", False)
    return 0

def LeaveHandler(event: SGUEvent) -> int:
    getLogger().info(f"User with uuid {event.listener.uuid} is leaving group with id {event.payload['group_id']}", False)
    if event.payload['group_id'] in groups.get_owned_groups(event.connection, event.listener.uuid):
        eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "error", 'message': "You can't leave a group you own!"}))
        return 1
    if event.listener.uuid not in groups.get_group_members(event.connection, event.payload['group_id']):
        eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "error", 'message': "You can't leave a group you're not in!"}))
        getLogger().warn(f"User with uuid {event.listener.uuid} attempted to leave a group they aren't in", True)
        return 1
    
    groups.remove_user(event.connection, event.listener.uuid, event.payload['group_id'])
    eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {
        'type': "group-success",
        'message': "You have successfully left the '" + 
            groups.get_group_name(event.connection, event.payload['group_id']) + "' group."
    }))
    getLogger().info("Success leaving group", False)
    return 0

def InfoHandler(event: SGUEvent) -> int:
    getLogger().info(f"User with uuid {event.listener.uuid} is getting info on group with id {event.payload['group_id']}", False)
    if event.listener.uuid not in groups.get_group_members(event.connection, event.payload['group_id']):
        eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "error", 'message': "You can't view info of a group you aren't in!"}))
        getLogger().warn(f"User with uuid {event.listener.uuid} attempted to view info of a group they aren't in", True)
        return 1
    info = groups.get_group_info(event.connection, event.payload['group_id'], False)
    eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {
        'type': "group-info",
        'info': info 
    }))
    getLogger().info("Success getting info", False)
    return 0

def ListHandler(event: SGUEvent) -> int:
    getLogger().info(f"User with uuid {event.listener.uuid} is viewing their groups", False)
    info = groups.get_group_list(event.connection, event.listener.uuid, False)
    eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {
        'type': "group-info",
        'info': info
    }))
    getLogger().info("Success getting list", False)
    return 0