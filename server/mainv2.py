import asyncio
import auth
from connect import openConnection, writeData
from enum import Enum
import groups
from json import loads, dumps
from picows import ws_create_server, WSFrame, WSTransport, WSListener, WSMsgType, WSUpgradeRequest, WSAutoPingStrategy

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
    
    allFieldsPresent, missingFields = auth.data_present(payload, msgType.value[2])
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
            print("Connection closed!")
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
        send_json(transport, {'type': "auth", 'subtype': "success"})

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