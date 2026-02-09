from connect import queryData, writeData

from typing import Optional, Union

def get_remote_id(connection, internal_id: int) -> str:
    """Get the remote uid of the inventory from the internal id"""
    return queryData(connection, "SELECT remote_uid FROM inventories WHERE inventory_id = %s;", internal_id, fetchAll=False)[0]

def get_internal_id(connection, remote_id: str) -> int:
    """Get the internal id of the inventory from the external id"""
    return int(queryData(connection, "SELECT inventory_id FROM inventories WHERE remote_uid = %s;", remote_id, fetchAll=False)[0])

def get_items(connection, id: int) -> list[tuple[str, int]]:
    """Get the items in the inventory, using internal inventory id"""
    return queryData(connection, "SELECT item_id,item_count FROM stored_items WHERE inventory = %s;", id)

def get_items_for_project(connection, project_id: int) -> list[dict[str, Union[str, int]]]:
    """Get all items reserved for the project, and where they're stored."""
    entries = queryData(connection, "SELECT item_id,item_count,inventory FROM stored_items WHERE project_id = %s;", project_id)
    result = []
    for entry in entries:
        item = {}
        item['id'] = str(entry[0])
        item['count'] = int(entry[1])
        item['inventory'] = int(entry[2])
        result.append(item)
    return result

def add_inventory(connection, external_id: str):
    """Track an inventory, with its id as the argument"""
    writeData(connection, "INSERT INTO inventories(remote_uid) VALUES(%s);", external_id)

def remove_inventory(connection, external_id: str):
    """Remove an inventory by external id"""
    writeData(connection, "DELETE FROM inventories WHERE remote_uid = %s;", external_id)

def add_item(connection, inventory_id: int, item_id: str, item_qty: int, project_id: Optional[int] = None) -> int:
    """Add a quantity of the item specified to the specified inventory, returning the new amount of that item"""
    items = get_items(connection, inventory_id)

    for item in items:
        if item_id == item[0]:
            qty = item[1]
            writeData(connection, "UPDATE stored_items SET item_count = %s WHERE inventory = %s AND item_id = %s AND project_id = %s;", 
                qty+item_qty, inventory_id, item_id, project_id)
            return qty + item_qty
    writeData(connection, "INSERT INTO stored_items(inventory,item_id,item_count,project_id) VALUES(%s,%s,%s,%s);", 
                inventory_id, item_id, item_qty, project_id)
    return item_qty

def remove_item(connection, inventory_id: int, item_id: str, item_qty: int, project_id: Optional[int] = None) -> int:
    """Remove a quantity of the item from the specified inventory. If this would reduce the quantity to < 0, it is set to 0 instead."""
    items = get_items(connection, inventory_id)

    qty = item_qty * -1
    for item in items:
        if item_id == item[0]:
            qty += item[1]
    
    if qty < 0:
        qty = 0

    writeData(connection, "UPDATE stored_items SET item_count = %s WHERE inventory = %s AND item_id = %s AND project_id = %s;", 
                qty, inventory_id, item_id, project_id)
    return qty

def delete_item(connection, inventory_id: int, item_id: str, project_id: Optional[int] = None) -> None:
    """Remove the item from the specified inventory and project."""
    if project_id is None:
        writeData(connection, "DELETE FROM stored_items WHERE inventory = %s AND item_id = %s;", inventory_id, item_id)
    else:
        writeData(connection, "DELETE FROM stored_items WHERE inventory = %s AND item_id = %s AND project_id = %s;", inventory_id, item_id, project_id)

def transfer_item(connection, 
        item_id: str, 
        source_inventory: int, 
        target_inventory: int, 
        transfer_qty: int, 
        source_project: Optional[int] = None, 
        target_project: Optional[int] = None
    ) -> tuple[int, int]:
    """
    Move an amount of the item from the source inventory to the target inventory. 

    Returns the number of that item in the source and target inventories.
    """
    source = remove_item(connection, source_inventory, item_id, transfer_qty, source_project)
    target = add_item(connection, target_inventory, item_id, transfer_qty, target_project)
    return source, target

def reserve_items(connection, item_id: str, inventory_id: int, target_project: int, reservation_qty: int, source_project: Optional[int] = None) -> tuple[int, int]:
    """
    Mark an amount of the item in the inventory as being reserved for the specified project. 
    
    This can be used to reserve items from one project directly to another.
    """
    return transfer_item(connection, item_id, inventory_id, inventory_id, reservation_qty, source_project, target_project)

def unreserve_items(connection, item_id: str, inventory_id: int, project_id: int, qty: int) -> tuple[int, int]:
    """
    Mark an amount of the item in the inventory that was reserved for the specified project as not reserved for any project.
    """
    return transfer_item(connection, item_id, inventory_id, inventory_id, qty, project_id)