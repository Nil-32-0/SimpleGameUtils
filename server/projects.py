from connect import queryData, writeData
from items import get_items_for_project, unreserve_items

from enum import StrEnum
from typing import Optional

class Scope(StrEnum):
    PUBLIC = "PUBLIC"
    GROUP = "GROUP"
    PRIVATE = "PRIVATE"


def get_projects(connection, uuid: str) -> list[tuple[int, str, str, str]]:
    """
        Get the projects visible for the user specified by uuid.\n
        Returns a list of tuples containing project id, name, description, and scope.
    """
    simple_project_list = queryData(connection, "SELECT project_id,project_name,project_desc,scope FROM projects " \
    "WHERE SCOPE = 'PUBLIC' OR owner_uuid = %s;", uuid)

    group_project_list = queryData(connection, "SELECT project_id,project_name,project_desc,scope FROM projects " \
    "LEFT JOIN group_relations ON projects.group_id = group_relations.group_id " \
    "WHERE SCOPE = 'GROUP' AND uuid = %s;", uuid)

    projects = [project for project in simple_project_list if project not in group_project_list]
    projects.extend(group_project_list)
    projects.sort(key=lambda x: x[0])
    return projects

def get_owned_projects(connection, uuid: str) -> list[int]:
    """
        Get the projects owned by the user specified by uuid.\n
        Returns a list of project ids
    """
    project_list = queryData(connection, "SELECT project_id FROM projects WHERE owner_uuid = %s;", uuid)
    return [int(project[0]) for project in project_list]

def get_project_group(connection, id: int) -> int:
    """Get the group id associated with the provided project id."""
    return int(queryData(connection, "SELECT group_id FROM projects WHERE project_id = %s;", id, fetchAll=False)[0])

def get_projects_groups(connection, ids: list[int]) -> dict[int, int]:
    """Get the mapping of project id to group ids for the specified project ids."""
    mapping = {}
    queryFilter = "WHERE project_id = " + str(ids[0])
    if len(ids) > 1:
        for id in ids:
            queryFilter += " OR project_id = " + str(id)
    maps = queryData(connection, "SELECT project_id,group_id FROM PROJECTS " + queryFilter + ";")
    for map in maps:
        mapping[int(map[0])] = int(map[1])

    return mapping

def get_project_goal(connection, id: int) -> dict[str, int]:
    """Get a mapping of items to the goal amount of them, for the specified project id."""
    mapping = {}
    items = queryData(connection, "SELECT item_id,goal_quantity FROM project_goals WHERE project_id = %s;", id)
    for item in items:
        mapping[item[0]] = int(item[1])
    return mapping


def create_project(connection, uuid: str, name: str, scope: Scope, desc: Optional[str] = None, group_id: Optional[int] = None):
    """Create a project with the specified information. If the scope is Group, group_id must be provided"""
    if scope == Scope.GROUP and group_id is None: return

    writeData(connection, "INSERT INTO projects(owner_uuid,project_name,project_desc,scope,group_id) "
    "VALUES (%s,%s,%s,%s,%s)", uuid, name, desc, scope, group_id)

def delete_project(connection, project_id: int):
    """Delete the specified project. This should only be allowed to be done by the project owner. This also unreserves all items reserved for that project."""
    items = get_items_for_project(connection, project_id)
    for item in items:
        unreserve_items(connection, item['id'], item['inventory'], project_id, item['count'])
    writeData(connection, "DELETE FROM projects WHERE project_id = %s;", project_id)

def transfer_project(connection, project_id: int, new_owner_uuid: str):
    """Tranfer ownership of the specified project to the specified user."""
    writeData(connection, "UPDATE projects SET owner_uuid = %s WHERE project_id = %s;", new_owner_uuid, project_id)

def change_scope(connection, project_id: int, new_scope: Scope, group_id: Optional[int] = None):
    """Change the scope of the specified project. If changed to Group, group_id must be provided"""
    if new_scope == Scope.GROUP and group_id is None: return

    writeData(connection, "UPDATE projects SET scope = %s,group_id = %s WHERE project_id = %s;", new_scope, group_id, project_id)

def add_item(connection, project_id: int, item_id: str, quantity: int):
    """Add an item to the project to be tracked"""
    writeData(connection, "INSERT INTO project_goals(project_id,item_id,goal_quantity) VALUES(%s,%s,%s);", project_id, item_id, quantity)

def remove_item(connection, project_id: int, item_id: str):
    """Stop tracking an item with a project"""
    writeData(connection, "DELETE FROM project_goals WHERE project_id = %s AND item_id = %s;", project_id, item_id)

if __name__ == "__main__":
    uid = "dNb8bv853r7X1e61715c0w084t9K3h0Qbq5Z2zeH4H5e1sae8XeSaX6n2Gdh63a5"
    uid2 = "dEcEdte3fhfE7Zby2a5k0Mar4baH9p339N3I8qbzdE0c0Q4Icacfe9et3V0F9y3o"
    