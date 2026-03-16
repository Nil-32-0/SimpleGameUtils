from enum import Enum

class SBUMsgType(Enum):
    AUTH_SUCCESS = "auth-success", ['type']
    AUTH_LOGIN = "auth-login", ['type', 'username', 'password']
    ERROR = "error", ['type', 'message']
    GROUP_CREATE = "group-create", ['type', 'group_name']
    GROUP_DELETE = "group-delete", ['type', 'group_id']
    GROUP_SUCCESS = "group-success", ['type', 'message']
    GROUP_TRANSFER = "group-transfer", ['type', 'group_id', 'new_owner_username']
    GROUP_ADD = "group-add", ['type', 'group_id', 'new_member_username']
    GROUP_REMOVE = "group-remove", ['type', 'group_id', 'member_username']
    GROUP_LEAVE = "group-leave", ['type', 'group_id']
    GROUP_INFO_REQ = "group-info-req", ['type', 'group_id']
    GROUP_LIST = "group-list", ['type']
    INVENTORY_ADD = "inventory-add", ['type', 'external_id']
    INVENTORY_REMOVE = "inventory-remove", ['type', 'external_id']
    ITEM_GET = "item-get", ['type', 'external_id']
    ITEM_ADD = "item-add", ['type', 'external_id', 'item_id', 'item_qty']
    ITEM_REMOVE = "item-remove", ['type', 'external_id', 'item_id', 'item_qty']
    ITEM_DELETE = "item-delete", ['type', 'external_id', 'item_id']
    ITEM_TRANSFER = "item-transfer", ['type', 'item_id', 'item_qty', 'source_id', 'target_id']
    PROJECT_VIEW_ALL = "project-view-all", ['type']
    PROJECT_VIEW_ONE = "project-view-one", ['type', 'project_id']
    PROJECT_CREATE = "project-create", ['type', 'name', 'scope', 'desc', 'group_id']
    PROJECT_DELETE = "project-delete", ['type', 'project_id']
    PROJECT_TRANSFER = "project-transfer", ['type', 'project_id', 'new_owner_username']
    PROJECT_SCOPE = "project-scope", ['type', 'project_id', 'scope', 'group_id']
    PROJECT_ITEM_TRACK = "project-item-track", ['type', 'project_id', 'item_id', 'item_qty']
    PROJECT_ITEM_DELETE = "project-item-delete", ['type', 'project_id', 'item_id']
    PROJECT_ITEM_ADD = "project-item-add", ['type', 'project_id', 'item_id', 'item_qty', 'external_id']
    PROJECT_ITEM_REMOVE = "project-item-remove", ['type', 'project_id', 'item_id', 'item_qty', 'external_id']
    PROJECT_ITEM_RESERVE = "project-item-reserve", ['type', 'target_project_id', 'item_id', 'item_qty', 'external_id', 'source_project_id']
    PROJECT_ITEM_RELEASE = "project-item-release", ['type', 'project_id', 'item_id', 'item_qty', 'external_id']




def find_type(type: str) -> SBUMsgType | None:
    """
    Finds the SBU Message Type for the given type string
    
    :param type: The main type to search for
    :type type: str
    :return: The first found SBUMsgType, or None if none is found
    :rtype: SBUMsgType | None
    """
    for enum in SBUMsgType:
        if enum.value[0] == type:
            return enum