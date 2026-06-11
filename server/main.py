import asyncio
from picows import WSAutoPingStrategy, WSUpgradeRequest, ws_create_server
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

from globals import *
from serverClientListener import ServerClientListener
from events import EventType, ClientConnectedEvent, ServerCommandEvent, ServerShutdownEvent, registerHandlers, handleEvent
from utils import Observable


async def user_input():
    session = PromptSession()
    while True:
        try:
            wsControlQueue.get_nowait()
        except asyncio.QueueEmpty:
            with patch_stdout():
                result = await session.prompt_async("> ")
            eventQueue.put_nowait(ServerCommandEvent(result))
        except asyncio.QueueShutDown:
            return

async def server_loop():
    def listener_factory(r: WSUpgradeRequest):
        return ServerClientListener()
        
    
    server: asyncio.Server = await ws_create_server(
        listener_factory, "127.0.0.1", 9001,
        enable_auto_ping=True,
        auto_ping_strategy=WSAutoPingStrategy.PING_WHEN_IDLE,
        auto_ping_reply_timeout=5
    )

    await server.start_serving()
    shutdown = False
    while not shutdown:
        try:
            await wsControlQueue.get()
        except asyncio.QueueShutDown:
            shutdown = True
    
    server.close()
    await server.wait_closed()

async def event_handler():
    while True:
        try:
            wsControlQueue.get_nowait()
        except asyncio.QueueEmpty:
            handleEvent(await eventQueue.get())
        except asyncio.QueueShutDown:
            return

async def main():
    await asyncio.gather(user_input(), server_loop(), event_handler())

def startup():
    LOGGER.info("Creating Hook Registries", False)
    for type in EventType:
        HOOK_REGISTRY[type] = Observable()
    registerHandlers()

def post_startup():
    for type in EventType:
        try:
            RESOLUTION_REGISTRY[type]
        except:
            LOGGER.error(f"{type} has no resolution handler!", True)
            if type != EventType.SERVER_SHUTDOWN:
                eventQueue.put_nowait(ServerShutdownEvent())

if __name__ == "__main__":
    startup()
    post_startup()
    asyncio.run(main())