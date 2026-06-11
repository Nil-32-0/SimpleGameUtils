from globals import *
from events import EventHandler, GroupHandler, InventoryHandler, ItemHandler, ProjectHandler, ProjectItemHandler
from events.EventType import EventType

def registerHandlers():
    RESOLUTION_REGISTRY[EventType.SERVER_COMMAND] = EventHandler.ServerCommandHandler
    RESOLUTION_REGISTRY[EventType.SERVER_SHUTDOWN] = EventHandler.ShutdownEventHandler
    RESOLUTION_REGISTRY[EventType.CLIENT_CONNECTED] = EventHandler.ClientConnectedHandler
    RESOLUTION_REGISTRY[EventType.CLIENT_DISCONNECTED] = EventHandler.ClientDisconnectedHandler
    RESOLUTION_REGISTRY[EventType.CLIENT_MESSAGE] = EventHandler.ClientMessageHandler
    RESOLUTION_REGISTRY[EventType.SEND_MESSAGE] = EventHandler.SendMessageHandler
    RESOLUTION_REGISTRY[EventType.AUTH_GROUP] = GroupHandler.AuthUser
    RESOLUTION_REGISTRY[EventType.GROUP_CREATE] = GroupHandler.CreationHandler
    RESOLUTION_REGISTRY[EventType.GROUP_DELETE] = GroupHandler.DeletionHandler
    RESOLUTION_REGISTRY[EventType.GROUP_TRANSFER] = GroupHandler.TransferHandler
    RESOLUTION_REGISTRY[EventType.GROUP_ADD] = GroupHandler.AddHandler
    RESOLUTION_REGISTRY[EventType.GROUP_REMOVE] = GroupHandler.RemoveHandler
    RESOLUTION_REGISTRY[EventType.GROUP_LEAVE] = GroupHandler.LeaveHandler
    RESOLUTION_REGISTRY[EventType.GROUP_INFO] = GroupHandler.InfoHandler
    RESOLUTION_REGISTRY[EventType.GROUP_LIST] = GroupHandler.ListHandler
    RESOLUTION_REGISTRY[EventType.INVENTORY_ADD] = InventoryHandler.AddHandler
    RESOLUTION_REGISTRY[EventType.INVENTORY_REMOVE] = InventoryHandler.RemoveHandler
    RESOLUTION_REGISTRY[EventType.ITEM_GET] = ItemHandler.GetHandler
    RESOLUTION_REGISTRY[EventType.ITEM_ADD] = ItemHandler.AddHandler
    RESOLUTION_REGISTRY[EventType.ITEM_REMOVE] = ItemHandler.RemoveHandler
    RESOLUTION_REGISTRY[EventType.ITEM_DELETE] = ItemHandler.DeleteHandler
    RESOLUTION_REGISTRY[EventType.ITEM_TRANSFER] = ItemHandler.TransferHandler
    RESOLUTION_REGISTRY[EventType.AUTH_PROJECT] = ProjectHandler.AuthProject
    RESOLUTION_REGISTRY[EventType.PROJECT_VIEW_ALL] = ProjectHandler.ViewAllHandler
    RESOLUTION_REGISTRY[EventType.PROJECT_VIEW_ONE] = ProjectHandler.ViewOneHandler
    RESOLUTION_REGISTRY[EventType.PROJECT_CREATE] = ProjectHandler.CreateHandler
    RESOLUTION_REGISTRY[EventType.PROJECT_DELETE] = ProjectHandler.DeleteHandler
    RESOLUTION_REGISTRY[EventType.PROJECT_TRANSFER] = ProjectHandler.TransferHandler
    RESOLUTION_REGISTRY[EventType.PROJECT_SCOPE] = ProjectHandler.ScopeHandler
    RESOLUTION_REGISTRY[EventType.PROJECT_ITEM_TRACK] = ProjectItemHandler.TrackHandler
    RESOLUTION_REGISTRY[EventType.PROJECT_ITEM_DELETE] = ProjectItemHandler.DeleteHandler
    RESOLUTION_REGISTRY[EventType.PROJECT_ITEM_ADD] = ProjectItemHandler.AddHandler
    RESOLUTION_REGISTRY[EventType.PROJECT_ITEM_REMOVE] = ProjectItemHandler.RemoveHandler
    RESOLUTION_REGISTRY[EventType.PROJECT_ITEM_RESERVE] = ProjectItemHandler.ReserveHandler
    RESOLUTION_REGISTRY[EventType.PROJECT_ITEM_RELEASE] = ProjectItemHandler.ReleaseHandler