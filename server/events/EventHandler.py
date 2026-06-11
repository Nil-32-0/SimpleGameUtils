from json import dumps
from picows import WSMsgType

from backend import auth
from globals import *
from events.Events import *
from events.SGUMsgType import find_event_type, find_type


def handleEvent(event: Event) -> int:
    event = HOOK_REGISTRY[event.type].resolve(event)
    if event is int: return event 
    return RESOLUTION_REGISTRY[event.type](event)


def ServerCommandHandler(event: ServerCommandEvent):
    if event.command == "exit":
        eventQueue.put_nowait(ServerShutdownEvent())
    if event.command == "lookup":
        getLogger().info(f"User with uuid {event.args[0]} has username {auth.get_username_from_uuid(CLI_CONNECTION, event.args[0])}", True)
    return 0

def ShutdownEventHandler(event: ServerShutdownEvent):
    getLogger().info("Shutting down server...", True)
    wsControlQueue.put_nowait("exit")
    wsControlQueue.shutdown()
    CLI_CONNECTION.close()
    return 0

def ClientConnectedHandler(event: ClientConnectedEvent):
    getLogger().info("Client connected", True)
    return 0

def ClientDisconnectedHandler(event: ClientDisconnectedEvent):
    getLogger().info("Client disconnected", True)
    return 0

def ClientMessageHandler(event: ClientMessageEvent):
    getLogger().info(event.payload, True) # TODO: Remove
    allFieldsPresent, errorMsg = auth_sgu_message(event.payload)
    if not allFieldsPresent:
        eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "error", 'message': errorMsg}))
        return 1
    if event.listener not in AUTH_LISTENERS.values():
        if event.payload['type'] == "auth-login":
            event.listener.on_initial_connection(event.transport, event.payload)
        else:
            eventQueue.put_nowait(SendMessageEvent(event.listener, event.transport, {'type': "error", 'message': "You must authenticate before performing any other operations!"}))
            return 1
    else:
        newEvent = find_event_type(event.payload['type'])
        if newEvent != None:
            eventQueue.put_nowait(SGUEvent(newEvent, event.listener, event.transport, event.payload))
    return 0
        

def SendMessageHandler(event: SendMessageEvent):
    if event.listener.uuid == None:
        getLogger().info(f"Sending message via connection with id {event.listener}", False)
    else:
        getLogger().info(f"Sending message to user with uuid {event.listener.uuid}", False)
    send_json(event.transport, event.message)
    return 0


def send_json(transport: WSTransport, json: dict[str, any]) -> None:
    transport.send(WSMsgType.TEXT, bytes(dumps(json), 'utf-8'))

def auth_sgu_message(payload: dict[str, any]) -> tuple[bool, str | None]:
    """
    Authenticate an SGU Message payload.
    
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