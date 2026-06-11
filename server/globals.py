from asyncio import Queue
from typing import TYPE_CHECKING

from backend.connect import openConnection
from utils import Logger

if TYPE_CHECKING:
    from typing import Callable

    from events import EventType, Event
    from serverClientListener import ServerClientListener
    from utils import Observable

HOOK_REGISTRY: dict[EventType, Observable] = {}
RESOLUTION_REGISTRY: dict[EventType, Callable[[Event], int]] = {}
LOGGER: Logger = Logger()
def getLogger():
    return LOGGER

eventQueue: Queue[Event] = Queue()
wsControlQueue: Queue[str] = Queue()
AUTH_LISTENERS: dict[str, ServerClientListener] = {}
CLI_CONNECTION = openConnection()