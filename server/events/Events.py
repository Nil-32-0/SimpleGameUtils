from events.EventType import EventType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from picows import WSTransport, WSFrame

    from serverClientListener import ServerClientListener

class Event():
    def __init__(self, type: EventType) -> None:
        self.type: EventType = type


class ServerCommandEvent(Event):
    def __init__(self, args: str):
        self._args: list[str] = args.split(" ")
        super().__init__(EventType.SERVER_COMMAND)

    @property
    def command(self) -> str:
        return self._args[0]
    
    @property
    def args(self) -> list[str]:
        return self._args[1:]


class ServerShutdownEvent(Event):
    def __init__(self):
        super().__init__(EventType.SERVER_SHUTDOWN)


class ClientEvent(Event):
    def __init__(self, type: EventType, listener: ServerClientListener, transport: WSTransport):
        self.listener = listener
        self.transport = transport
        super().__init__(type)


class ClientConnectedEvent(ClientEvent):
    def __init__(self, listener: ServerClientListener):
        super().__init__(EventType.CLIENT_CONNECTED, listener, None)
    

class ClientDisconnectedEvent(ClientEvent):
    def __init__(self, listener: ServerClientListener):
        super().__init__(EventType.CLIENT_DISCONNECTED, listener, None)



class ClientMessageEvent(ClientEvent):
    def __init__(self, listener: ServerClientListener, transport: WSTransport, payload: dict[str, any]):
        self.payload = payload
        super().__init__(EventType.CLIENT_MESSAGE, listener, transport)


class SendMessageEvent(ClientEvent):
    def __init__(self, listener: ServerClientListener, transport: WSTransport, message: dict[str, any]):
        self.message = message
        super().__init__(EventType.SEND_MESSAGE, listener, transport)


class SGUEvent(ClientEvent):
    def __init__(self, type: EventType, listener: ServerClientListener, transport: WSTransport, payload: dict[str, any]):
        self.payload = payload
        super().__init__(type, listener, transport)
    
    @property
    def connection(self):
        return self.listener.connection


class AuthActionEvent(ClientEvent):
    def __init__(self, type: EventType, listener: ServerClientListener, transport: WSTransport, level: str, id: int):
        self.level = level
        self.id = id
        super().__init__(type, listener, transport)