import asyncio
import auth
from connect import openConnection, writeData
from enum import Enum
import groups
import items
from json import loads, dumps
from picows import ws_create_server, WSFrame, WSTransport, WSListener, WSMsgType, WSUpgradeRequest, WSAutoPingStrategy
import projects

auth_connections = {}

def send_json(transport: WSTransport, json: dict[str, any]) -> None:
    transport.send(WSMsgType.TEXT, bytes(dumps(json), 'utf-8'))

class SBUMsgType(Enum):
    AUTH_KEY = "auth-key", ['type', 'uuid']
    AUTH_SUCCESS = "auth-success", ['type']
    AUTH_USERNAME = "auth-username", ['type', 'username']
    AUTH_UUID = "auth-uuid", ['type', 'username', 'uuid']
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
    PROJECT_SCOPE = "project-scope", ['type', 'scope', 'group_id']
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

def auth_sbu_message(payload: dict[str, any]) -> tuple[bool, str | None]:
    """
    Authenticate an SBU Message payload.
    
    :param payload: The payload recieved, to authenticate
    :type payload: dict[str, any]
    :return: A tuple, where the first element is True iff the payload has all necessary fields, and the second element is
    a string describing the error iff the first element is False
    :rtype: tuple[bool, str]
    """
    typeFieldPresent = auth.data_present(payload, ['type'])[0]
    if not typeFieldPresent:
        return False, "The type of the message must be specified!"
    msgType = find_type(payload['type'])
    if msgType is None:
        return False, "Invalid type!"
    
    allFieldsPresent, missingFields = auth.data_present(payload, msgType.value[1])
    return allFieldsPresent, None if allFieldsPresent else "Missing fields: " + ", ".join(missingFields)


class ServerClientListener(WSListener):
    def __init__(self):
        self.connection = None
        self.uuid = None

    def on_ws_connected(self, transport: WSTransport):
        print("New Client Connected!")

    def on_ws_disconnected(self, transport: WSTransport):
        if self.connection is not None:
            self.connection.close()
            print("SQL connection closed!")
        auth_connections.pop(self, None)
        print("Client disconnected")

    def on_ws_frame(self, transport: WSTransport, frame: WSFrame):
        if frame.msg_type == WSMsgType.PING:
            transport.send_pong(frame.get_payload_as_bytes())

        elif frame.msg_type == WSMsgType.PONG:
            return

        elif frame.msg_type == WSMsgType.CLOSE:
            transport.send_close(frame.get_close_code(), frame.get_close_message())
            transport.disconnect()
        
        else:
            try:
                print(frame.get_payload_as_utf8_text())
                payload = loads(frame.get_payload_as_utf8_text())
            except Exception as e:
                send_json(transport, {'type': "error", 'message': "All messages must be String representations of a json object encoded with utf-8!"})
                print(e)
                return
            
            allFieldsPresent, errorMsg = auth_sbu_message(payload)
            if not allFieldsPresent:
                send_json(transport, {
                    'type': "error",
                    'message': errorMsg
                })
                return
            
            if self not in auth_connections.values():
                if payload['type'] in ["auth-username", "auth-uuid"]:
                    self.on_initial_connection(transport, payload)
                else:
                    send_json(transport, {
                        'type': "error",
                        'message': "You must authenticate before performing any other operations!"
                    })
            else:
                try:
                    match payload['type']:
                        case x if str(x).startswith("group"):
                            self.group_handler(transport, payload)
                        case x if str(x).startswith("inventory"):
                            self.inventory_handler(transport, payload)
                        case x if str(x).startswith("item"):
                            self.item_handler(transport, payload)
                        case x if str(x).startswith("project"):
                            self.project_handler(transport, payload)
                except Exception as e:
                    print(e)
                    send_json(transport, {'type': "error", 'message': e})

    def on_initial_connection(self, transport: WSTransport, payload: dict[str, any]) -> None:
        if self.connection is None:
            self.connection = openConnection()

        if payload['type'] == "auth-uuid": # User exists
            valid, errorMsg = auth.validate(self.connection, payload)
            if not valid:
                send_json(transport, {'type': "error", 'message': errorMsg})
                return
            uid = payload['uuid']

        else: # User must be created
            uid, mojanguuid = auth.generate_userkey(self.connection, payload)
            writeData(self.connection, 
                "INSERT INTO users(useruuid, username, mojanguuid) VALUES(%s,%s,%s);", 
                uid, payload['username'], mojanguuid
            )
            send_json(transport, {'type': "auth-key",'uuid': uid})

        self.uuid = uid
        send_json(transport, {'type': "auth-success"})

        auth_connections[uid] = self

    def group_handler(self, transport: WSTransport, payload: dict[str, any]) -> None:
        requires_ownership = ["group-delete", "group-transfer", "group-add", "group-remove"]
        if payload['type'] in requires_ownership and payload['group_id'] not in groups.get_owned_groups(self.connection, self.uuid):
            send_json(transport, {
                'type': "error",
                'message': "You can't perform that action on a group you don't own!"
            })
            return
        
        match payload['type']:
            case "group-create":
                group_id = groups.create_group(self.connection, self.uuid, payload['group_name'])
                send_json(transport, {
                    'type': "group-success", 
                    'message': "Group '" + payload['group_name'] + "' with id " + str(group_id) + " has been created."
                })

            case "group-delete":
                groups.delete_group(self.connection, payload['group_id'])
                send_json(transport, {
                    'type': "group-success", 
                    'message': "The '" + groups.get_group_name(self.connection, payload['group_id']) + "' group has been deleted."
                })

            case "group-transfer":                
                if not auth.username_exists(self.connection, payload['new_owner_username']):
                    send_json(transport, {'type': "error", 'message': "You can't transfer ownership to a player who doesn't exist!"})
                    return
                
                new_uuid = auth.get_uuid_from_username(self.connection, payload['new_owner_username'])

                if new_uuid == self.uuid:
                    send_json(transport, {'type': "error", 'message': "You can't transfer ownership of a group to yourself!"})
                    return
                if new_uuid not in groups.get_group_members(self.connection, payload['group_id']):
                    send_json(transport, {'type': "error", 'message': "You can't transfer ownership of a group to a member that isn't in it!"})
                    return

                groups.transfer_ownership(self.connection, new_uuid, payload['group_id'])
                send_json(transport, {
                    'type': "group-success",
                    'message': "The '" + groups.get_group_name(self.connection, payload['group_id']) + "' group has been transfered to " + payload['new_owner_username'] + "."
                })

            case "group-add":
                if not auth.username_exists(self.connection, payload['new_member_username']):
                    send_json(transport, {'type': "error", 'message': "You can't add a player who doesn't exist!"})
                    return
                
                new_uuid = auth.get_uuid_from_username(self.connection, payload['new_member_username'])

                if new_uuid == self.uuid:
                    send_json(transport, {'type': "error", 'message': "You can't add yourself to a group!"})
                    return
                
                groups.add_user(self.connection, new_uuid, payload['group_id'])
                send_json(transport, {
                    'type': "group-success",
                    'message': payload['new_member_username'] + " has been added to group with id '" + 
                        groups.get_group_name(self.connection, payload['group_id']) + "' group."
                })
            
            case "group-remove":
                if not auth.username_exists(self.connection, payload['member_username']):
                    send_json(transport, {'type': "error", 'message': "You can't remove a player who doesn't exist!"})
                    return

                user_uuid = auth.get_uuid_from_username(self.connection, payload['member_username'])
                if user_uuid not in groups.get_group_members(self.connection, payload['group_id']):
                    send_json(transport, {'type': "error", 'message': "You can't remove a player who isn't in the group!"})
                    return
                
                groups.remove_user(self.connection, self.uuid, payload['group_id'])
                send_json(transport, {
                    'type': "group-success",
                    'message': payload['member_username'] + " has been removed from the '" + 
                        groups.get_group_name(self.connection, payload['group_id']) + "' group."
                })
            
            case "group-leave":
                if payload['group_id'] in groups.get_owned_groups(self.connection, self.uuid):
                    send_json(transport, {'type': "error", 'message': "You can't leave a group you own!"})
                    return
                if self.uuid not in groups.get_group_members(self.connection, payload['group_id']):
                    send_json(transport, {'type': "error", 'message': "You can't leave a group you're not in!"})
                    return
                
                groups.remove_user(self.connection, self.uuid, payload['group_id'])
                send_json(transport, {
                    'type': "group-success",
                    'message': "You have successfully left the '" + 
                        groups.get_group_name(self.connection, payload['group_id']) + "' group."
                })
            
            case "group-info-req":
                if self.uuid not in groups.get_group_members(self.connection, payload['group_id']):
                    send_json(transport, {'type': "error", 'message': "You can't view info of a group you aren't in!"})
                    return
                info = groups.get_group_info(self.connection, payload['group_id'], False)
                send_json(transport, {
                    'type': "group-info",
                    'info': info 
                })

            case "group-list":
                info = groups.get_group_list(self.connection, self.uuid, False)
                send_json(transport, {
                    'type': "group-info",
                    'info': info
                })
    
    def inventory_handler(self, transport: WSTransport, payload: dict[str, any]) -> None:
        match payload['type']:
            case "inventory-add":
                items.add_inventory(self.connection, payload['external_id'])
            case "inventory-remove":
                items.remove_inventory(self.connection, payload['external_id'])

    def item_handler(self, transport: WSTransport, payload: dict[str, any]) -> None:
        match payload['type']:
            case "item-get":
                item_list = items.get_items(self.connection, items.get_internal_id(self.connection, payload['external_id']))
                send_json(transport, {'type': "item-info", 'items': item_list, 'inventory': payload['external_id']})
            case "item-add":
                qty = items.add_item(self.connection, items.get_internal_id(self.connection, payload['external_id']), 
                                    payload['item_id'], payload['item_qty'])
                send_json(transport, {'type': "item-info", 'items': [(payload['item_id'], qty)], 'inventory': payload['external_id']})
            case "item-remove":
                qty = items.remove_item(self.connection, items.get_internal_id(payload['external_id']),
                                    payload['item_id'], payload['item_qty'])
                send_json(transport, {'type': "item-info", 'items': [(payload['item_id'], qty)], 'inventory': payload['external_id']})
            case "item-delete":
                items.delete_item(self.connection, items.get_internal_id(self.connection, payload['external_id']), payload['item_id'])
            case "item-transfer":
                qtys = items.transfer_item(self.connection, payload['item_id'], 
                                    items.get_internal_id(self.connection, payload['source_id']), 
                                    items.get_internal_id(self.connection, payload['target_id']), payload['item_qty'])
                send_json(transport, {'type': "item-info", 'items': [(payload['item_id'], qtys[0])], 'inventory': payload['source_id']})
                send_json(transport, {'type': "item-info", 'items': [(payload['item_id'], qtys[1])], 'inventory': payload['target_id']})

    def project_handler(self, transport: WSTransport, payload: dict[str, any]) -> None:
        requires_ownership = ['project-delete', 'project-transfer', 'project-scope']
        if payload['type'] in requires_ownership and int(payload['project_id']) not in projects.get_owned_projects(self.connection, self.uuid):
            send_json(transport, {
                'type': "error",
                'message': "You can't perform that action on a project you don't own!"
            })
            return

        match payload['type']:
            case "project-view-all":
                proj = projects.get_projects(self.connection, self.uuid)
                send_json(transport, {'type': "project-info-all", 'projects': proj})
            case "project-view-one":
                if int(payload['project_id']) not in [x[0] for x in projects.get_projects(self.connection, self.uuid)]:
                    send_json(transport, {'type': "error", 'message': "You can't view details of a project you don't have access to!"})
                    return
                goal = projects.get_project_goal(self.connection, payload['project_id'])
                gathered = projects.get_items_for_project(self.connection, payload['project_id'])
                total = {}
                for entry in gathered:
                    if entry['id'] in total:
                        total[entry['id']] += entry['count']
                    else:
                        total[entry['id']] = entry['count']
                    entry['inventory'] = items.get_remote_id(self.connection, entry['inventory'])
                progress = {}
                for item in goal:
                    progress[goal] = {'goal': goal[item], 'gathered': total[item]}
                
                send_json(transport, {'type': "project-info-single", 'project_id': payload['project_id'],
                                        'goal': goal, 'gathered': gathered, 'progress': progress})
            case "project-create":
                if (payload['scope'] == "GROUP" and int(payload['group_id']) == -1):
                    send_json(transport, {'type': "error", 'message': "You must specify the group ID if setting scope to group!"})
                    return
                if int(payload['group_id'] == -1):
                    projects.create_project(self.connection, self.uuid, payload['name'], payload['scope'], payload['desc'])
                else:
                    projects.create_project(self.connection, self.uuid, payload['name'], payload['scope'], payload['desc'], payload['group_id'])
            case "project-delete":
                projects.delete_project(self.connection, payload['project_id'])
            case "project-transfer":
                if not auth.username_exists(self.connection, payload['new_owner_username']):
                    send_json(transport, {'type': "error", 'message': "You can't transfer the project to a player who doesn't exist!"})
                    return
                
                projects.transfer_project(self.connection, payload['project_id'], auth.get_uuid_from_username(self.connection, payload['new_owner_username']))
            case "project-scope":
                if (payload['scope'] == "GROUP" and int(payload['group_id']) == -1):
                    send_json(transport, {'type': "error", 'message': "You must specify the group ID if setting scope to group!"})
                    return
                projects.change_scope(self.connection, payload['project_id'], payload['scope'], 
                                    payload['group_id'] if int(payload['group_id']) != -1 else None)
            case "project-item-track":
                projects.add_item(self.connection, payload['project_id'], payload['item_id'], payload['item_qty'])
            case "project-item-delete":
                projects.remove_item(self.connection, payload['project_id'], payload['item_id'])
            case "project-item-add":
                qty = items.add_item(self.connection, items.get_internal_id(self.connection, payload['external_id']), payload['item_id'],
                                payload['item_qty'], payload['project_id'])
                send_json(transport, {'type': "project-item-info", 'items': [(payload['item_id'], qty)], 'inventory': payload['external_id'], 
                                        'project_id': payload['project_id']})
            case "project-item-remove":
                qty = items.remove_item(self.connection, items.get_internal_id(self.connection, payload['external_id']), payload['item_id'],
                                payload['item_qty'], payload['project_id'])
                send_json(transport, {'type': "project-item-info", 'items': [(payload['item_id'], qty)], 'inventory': payload['external_id'], 
                                        'project_id': payload['project_id']})
            case "project-item-reserve":
                qty1, qty2 = items.reserve_items(self.connection, payload['item_id'], items.get_internal_id(self.connection, payload['external_id']),
                                    payload['target_project_id'], payload['item_qty'], 
                                    payload['source_project_id'] if int(payload['source_project_id']) == -1 else None)
                
                send_json(transport, {'type': "project-item-info", 'items': [(payload['item_id'], qty1)], 'inventory': payload['external_id'],
                                        'project_id': payload['source_project_id']})
                send_json(transport, {'type': "project-item-info", 'items': [(payload['item_id'], qty2)], 'inventory': payload['external_id'],
                                        'project_id': payload['target_project_id']})
            case "project-item-release":
                qty1, qty2 = items.unreserve_items(self.connection, payload['item_id'], items.get_internal_id(self.connection, payload['external_id']),
                                                    payload['project_id'], payload['item_qty'])
                send_json(transport, {'type': "project-item-info", 'items': [(payload['item_id'], qty1)], 'inventory': payload['external_id'],
                                        'project_id': payload['project_id']})
                send_json(transport, {'type': "project-item-info", 'items': [(payload['item_id'], qty1)], 'inventory': payload['external_id'],
                                        'project_id': -1})

async def main():
    def listener_factory(r: WSUpgradeRequest):
        return ServerClientListener()
    
    server: asyncio.Server = await ws_create_server(
        listener_factory, "127.0.0.1", 9001,
        enable_auto_ping=True,
        auto_ping_strategy=WSAutoPingStrategy.PING_WHEN_IDLE,
        auto_ping_reply_timeout=5
    )

    for s in server.sockets:
        print(f"Server started on {s.getsockname()}")
    
    await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())