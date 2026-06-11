from globals import getLogger, eventQueue

from backend import auth, items, projects
from events.EventHandler import handleEvent
from events.Events import SGUEvent, SendMessageEvent, AuthActionEvent
from events.EventType import EventType

def AuthProject(event: AuthActionEvent) -> int:
    match event.level:
        case "owner":
            if event.id in projects.get_owned_projects(event.connection, event.listener.uuid): return 0
            eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {
                    'type': "error",
                    'message': "You can't perform that action on a project you don't own!"
                }))
        case "member":
            if event.id in [x[0] for x in projects.get_projects(event.connection, event.listener.uuid)]: return 0
            eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {
                    'type': "error",
                    'message': "You can't perform that action on a project you don't have access to!"
                }))
    getLogger().warn(f"User with uuid {event.listener.uuid} does not have {event.level} permissions to perform actions on project {event.id}", True)
    return 1


def ViewAllHandler(event: SGUEvent) -> int:
    getLogger().info(f"User with uuid {event.listener.uuid} viewing all projects", False)
    proj = projects.get_projects(event.connection, event.listener.uuid)
    eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "project-info-all", 'projects': proj}))
    return 0

def ViewOneHandler(event: SGUEvent) -> int:
    getLogger().info(f"User with uuid {event.listener.uuid} viewing details of project {event.payload['project_id']}", False)
    if handleEvent(AuthActionEvent(EventType.AUTH_PROJECT, event.listener, event.transport, "member", event.payload['project_id'])) != 0:
        return 1
    
    goal = projects.get_project_goal(event.connection, event.payload['project_id'])
    gathered = projects.get_items_for_project(event.connection, event.payload['project_id'])
    total = {}
    for entry in gathered:
        if entry['id'] in total:
            total[entry['id']] += entry['count']
        else:
            total[entry['id']] = entry['count']
        entry['inventory'] = items.get_remote_id(event.connection, entry['inventory'])
    progress = {}
    for item in goal:
        if item not in total:
            total[item] = 0
        progress[item] = {'goal': goal[item], 'gathered': total[item]}
    
    eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "project-info-single", 'project_id': event.payload['project_id'],
                            'goal': goal, 'gathered': gathered, 'progress': progress}))
    getLogger().info("Info sent", False)
    return 0

def CreateHandler(event: SGUEvent) -> int:
    getLogger().info(f"User with uuid {event.listener.uuid} is creating project {event.payload['name']}", False)
    if (event.payload['scope'] == "GROUP" and int(event.payload['group_id']) == -1):
        eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "error", 'message': "You must specify the group ID if setting scope to group!"}))
        getLogger().warn("Project with scope GROUP does not have group id specified", False)
        return 1
    if int(event.payload['group_id'] == -1):
        projects.create_project(event.connection, event.listener.uuid, event.payload['name'], event.payload['scope'], event.payload['desc'])
    else:
        projects.create_project(event.connection, event.listener.uuid, event.payload['name'], event.payload['scope'], event.payload['desc'], event.payload['group_id'])
    getLogger().info("Creation success", False)
    return 0

def DeleteHandler(event: SGUEvent) -> int:
    getLogger().info(f"Deleting project with id {event.payload['project_id']}", False)
    if handleEvent(AuthActionEvent(EventType.AUTH_PROJECT, event.listener, event.transport, "owner", event.payload['project_id'])) != 0: 
        return 1
    projects.delete_project(event.connection, event.payload['project_id'])
    getLogger().info("Deletion success", False)
    return 0

def TransferHandler(event: SGUEvent) -> int:
    getLogger().info(f"Tranferring project {event.payload['project_id']} to {event.payload['new_owner_username']}", False)
    if handleEvent(AuthActionEvent(EventType.AUTH_PROJECT, event.listener, event.transport, "owner", event.payload['project_id'])) != 0: 
        return 1
    if not auth.username_exists(event.connection, event.payload['new_owner_username']):
        eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "error", 'message': "You can't transfer the project to a player who doesn't exist!"}))
        getLogger().warn(f"User with uuid {event.listener.uuid} attempted to transfer a project to a player who doesn't exist", True)
        return 1
    
    new_uuid = auth.get_uuid_from_username(event.connection, event.payload['new_owner_username'])

    if new_uuid == event.listener.uuid:
        eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "error", 'message': "You can't transfer ownership of a group to yourself!"}))
        getLogger().warn(f"User with uuid {event.listener.uuid} attempted to transfer a group to themself", True)
        return 1

    projects.transfer_project(event.connection, event.payload['project_id'], new_uuid)
    getLogger().info("Transfer success", False)
    return 0

def ScopeHandler(event: SGUEvent) -> int:
    getLogger().info(f"Changing scope of project {event.payload['project_id']} to {event.payload['scope']}", False)
    if handleEvent(AuthActionEvent(EventType.AUTH_PROJECT, event.listener, event.transport, "owner", event.payload['project_id'])) != 0: 
        return 1
    if (event.payload['scope'] == "GROUP" and int(event.payload['group_id']) == -1):
        eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "error", 'message': "You must specify the group ID if setting scope to group!"}))
        getLogger().warn("Project with scope GROUP does not have group id specified", False)
        return 1
    projects.change_scope(event.connection, event.payload['project_id'], event.payload['scope'], 
                        event.payload['group_id'] if int(event.payload['group_id']) != -1 else None)
    getLogger().info("Scope Change success", False)
    return 0