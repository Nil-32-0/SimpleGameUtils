from globals import AUTH_LISTENERS, eventQueue, LOGGER

from json import loads
from picows import ws_create_server, WSFrame, WSTransport, WSListener, WSMsgType, WSUpgradeRequest, WSAutoPingStrategy

from backend import auth
from backend.connect import openConnection, writeData
from events import ClientConnectedEvent, ClientDisconnectedEvent, ClientMessageEvent, SendMessageEvent

class ServerClientListener(WSListener):
    def __init__(self):
        self.connection = None
        self.uuid = None

    def on_ws_connected(self, transport: WSTransport):
        eventQueue.put_nowait(ClientConnectedEvent(self))

    def on_ws_disconnected(self, transport: WSTransport):
        if self.connection is not None:
            self.connection.close()
            LOGGER.info(f"Closed SQL Connection for client with uuid {self.uuid}", False)
        AUTH_LISTENERS.pop(self.uuid, None)
        eventQueue.put_nowait(ClientDisconnectedEvent(self))

    def on_ws_frame(self, transport: WSTransport, frame: WSFrame):
        if frame.msg_type == WSMsgType.PING:
            transport.send_pong(frame.get_payload_as_bytes())

        elif frame.msg_type == WSMsgType.PONG:
            return

        elif frame.msg_type == WSMsgType.CLOSE:
            transport.send_close(frame.get_close_code(), frame.get_close_message())
            transport.disconnect()

        else:
            eventQueue.put_nowait(ClientMessageEvent(self, transport, loads(frame.get_payload_as_utf8_text())))

    
    def on_initial_connection(self, transport: WSTransport, payload: dict[str, any]) -> None:
        if self.connection is None:
            self.connection = openConnection()

        if auth.username_exists(self.connection, payload['username']): # User exists
            valid, errorMsg = auth.validate(self.connection, payload)
            if not valid:
                eventQueue.put_nowait(SendMessageEvent(self, transport, {'type': "error", 'message': errorMsg}))
                return
            uid = auth.get_uuid_from_username(self.connection, payload['username'])

        else: # User must be created
            uid, hashword = auth.generate_userkey(self.connection, payload)
            writeData(self.connection, 
                "INSERT INTO users(useruuid, username, password) VALUES(%s,%s,%s);", 
                uid, payload['username'], hashword
            )
            eventQueue.put_nowait(SendMessageEvent(self, transport, {'type': "account-creation-success"}))

        self.uuid = uid
        eventQueue.put_nowait(SendMessageEvent(self, transport, {'type': "auth-success"}))

        AUTH_LISTENERS[uid] = self