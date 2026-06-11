from enum import Enum
from events.EventType import EventType

class SGUMsgType(Enum):
    AUTH_SUCCESS = "auth-success", ['type'], None
    AUTH_LOGIN = "auth-login", ['type', 'username', 'password'], None
    ERROR = "error", ['type', 'message'], None
    GROUP_CREATE = "group-create", ['type', 'group_name'], EventType.GROUP_CREATE
    GROUP_DELETE = "group-delete", ['type', 'group_id'], EventType.GROUP_DELETE
    GROUP_SUCCESS = "group-success", ['type', 'message'], None
    GROUP_TRANSFER = "group-transfer", ['type', 'group_id', 'new_owner_username'], EventType.GROUP_TRANSFER
    GROUP_ADD = "group-add", ['type', 'group_id', 'new_member_username'], EventType.GROUP_ADD
    GROUP_REMOVE = "group-remove", ['type', 'group_id', 'member_username'], EventType.GROUP_REMOVE
    GROUP_LEAVE = "group-leave", ['type', 'group_id'], EventType.GROUP_LEAVE
    GROUP_INFO = "group-info-req", ['type', 'group_id'], EventType.GROUP_INFO
    GROUP_LIST = "group-list", ['type'], EventType.GROUP_LIST
    INVENTORY_ADD = "inventory-add", ['type', 'external_id'], EventType.INVENTORY_ADD
    INVENTORY_REMOVE = "inventory-remove", ['type', 'external_id'], EventType.INVENTORY_REMOVE
    ITEM_GET = "item-get", ['type', 'external_id'], EventType.ITEM_GET
    ITEM_ADD = "item-add", ['type', 'external_id', 'item_id', 'item_qty'], EventType.ITEM_ADD
    ITEM_REMOVE = "item-remove", ['type', 'external_id', 'item_id', 'item_qty'], EventType.ITEM_REMOVE
    ITEM_DELETE = "item-delete", ['type', 'external_id', 'item_id'], EventType.ITEM_DELETE
    ITEM_TRANSFER = "item-transfer", ['type', 'item_id', 'item_qty', 'source_id', 'target_id'], EventType.ITEM_TRANSFER
    PROJECT_VIEW_ALL = "project-view-all", ['type'], EventType.PROJECT_VIEW_ALL
    PROJECT_VIEW_ONE = "project-view-one", ['type', 'project_id'], EventType.PROJECT_VIEW_ONE
    PROJECT_CREATE = "project-create", ['type', 'name', 'scope', 'desc', 'group_id'], EventType.PROJECT_CREATE
    PROJECT_DELETE = "project-delete", ['type', 'project_id'], EventType.PROJECT_DELETE
    PROJECT_TRANSFER = "project-transfer", ['type', 'project_id', 'new_owner_username'], EventType.PROJECT_TRANSFER
    PROJECT_SCOPE = "project-scope", ['type', 'project_id', 'scope', 'group_id'], EventType.PROJECT_SCOPE
    PROJECT_ITEM_TRACK = "project-item-track", ['type', 'project_id', 'item_id', 'item_qty'], EventType.PROJECT_ITEM_TRACK
    PROJECT_ITEM_DELETE = "project-item-delete", ['type', 'project_id', 'item_id'], EventType.PROJECT_ITEM_DELETE
    PROJECT_ITEM_ADD = "project-item-add", ['type', 'project_id', 'item_id', 'item_qty', 'external_id'], EventType.PROJECT_ITEM_ADD
    PROJECT_ITEM_REMOVE = "project-item-remove", ['type', 'project_id', 'item_id', 'item_qty', 'external_id'], EventType.PROJECT_ITEM_REMOVE
    PROJECT_ITEM_RESERVE = "project-item-reserve", ['type', 'target_project_id', 'item_id', 'item_qty', 'external_id', 'source_project_id'], EventType.PROJECT_ITEM_RESERVE
    PROJECT_ITEM_RELEASE = "project-item-release", ['type', 'project_id', 'item_id', 'item_qty', 'external_id'], EventType.PROJECT_ITEM_RELEASE




def find_type(type: str) -> SGUMsgType | None:
    """
    Finds the SGU Message Type for the given type string
    
    :param type: The main type to search for
    :type type: str
    :return: The first found SGUMsgType, or None if none is found
    :rtype: SGUMsgType | None
    """
    for enum in SGUMsgType:
        if enum.value[0] == type:
            return enum
    

def find_event_type(type: str) -> EventType | None:
    """
    Finds the associated Event type for the given SGU Message Type string
    
    :param type: The main type to search for
    :type type: str
    :return: The Event associated with the SGUMsgType, or None
    :rtype: Event | None
    """
    t = find_type(type)
    if t == None:
        return t
    return t.value[2]