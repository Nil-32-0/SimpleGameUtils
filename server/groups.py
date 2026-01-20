from connect import queryData, writeData

def get_group_name(connection, group_id) -> str:
    """Get the name of the group from the id."""
    return queryData(connection, "SELECT group_name FROM groups WHERE group_id = %s;", group_id, fetchAll=False)[0]

def get_groups(connection, uuid) -> list[int]:
    """Get all group ids of groups the user specified is a member of."""
    tuple_list = queryData(connection, "SELECT group_id FROM group_relations WHERE uuid = %s;", uuid)
    return [tup[0] for tup in tuple_list]

def get_owned_groups(connection, uuid) -> list[int]:
    """Get all group ids of groups owned by the user specified."""
    tuple_list = queryData(connection, "SELECT group_id FROM groups WHERE owner_uuid = %s;", uuid)
    return [tup[0] for tup in tuple_list]
        
def get_group_members(connection, group_id) -> list[str]:
    """Get all uuids of the members of the specified group."""
    tuple_list = queryData(connection, "SELECT uuid FROM group_relations WHERE group_id = %s;", group_id)
    return [tup[0] for tup in tuple_list]

def get_group_member_usernames(connection, group_id) -> list[str]:
    """Get all usernames of the members of the specified group."""
    tuple_list = queryData(connection, "SELECT username " \
        "FROM group_relations LEFT JOIN users " \
        "ON group_relations.uuid = users.useruuid " \
        "WHERE group_id = %s;", group_id
    )
    return [tup[0] for tup in tuple_list]

def get_group_list(connection, uuid, include_uuids = True) -> dict[int, dict[str, any]]:
    group_info = {}
    tuple_list = queryData(connection, "SELECT group_id,group_name,owner_uuid,username " \
    "FROM groups " \
    "LEFT JOIN users ON groups.owner_uuid = users.useruuid " \
    "LEFT JOIN group_relations ON groups.group_id = group_relations.group_id " \
    "WHERE group_relations.uuid = %s;", uuid
    )
    for group in tuple_list:
        info = {}
        info["group_name"] = group[1]
        if include_uuids:
            info["owner_uuid"] = group[2]
        info["owner_name"] = group[3]
        group_info[group[0]] = info
    return group_info
    

def get_group_info(connection, group_id, include_uuids = True) -> dict[str, str | list[dict[str, str]]]:
    """Get the group name, owner name and uuid (optional), and a list of its members, with their names and uuids (optional)."""
    group_info = {}
    group = queryData(connection, "SELECT group_name,owner_uuid,username " \
    "FROM groups " \
    "LEFT JOIN users ON groups.owner_uuid = users.useruuid " \
    "WHERE group_id = %s", group_id)[0]

    members = queryData(connection, "SELECT useruuid,username " \
    "FROM group_relations " \
    "LEFT JOIN users ON group_relations.uuid = users.useruuid " \
    "WHERE group_id = %s", group_id)
    
    group_info["group_name"] = group[0]
    group_info["owner_name"] = group[2]
    if include_uuids:
        group_info["owner_uuid"] = group[1]

    memberList = []
    for member in members:
        mem = {}
        mem["username"] = member[1]
        if include_uuids:
            mem["uuid"] = member[0]
        memberList.append(mem)
    group_info["members"] = memberList

    return group_info

def get_groups_info(connection, group_ids: list[int], include_uuids = True) -> dict[int, dict[str, str | list[dict[str, str]]]]:
    """Get the group names, owners names and uuids (optional), and lists of the group members, with their names and uuids (optional)."""
    groups = {}
    queryFilter = "WHERE group_id = " + str(group_ids[0])
    if len(group_ids) > 1:
        for id in group_ids:
            queryFilter += " OR group_id = " + str(id)

    group_names = queryData(connection, "SELECT group_id,group_name,owner_uuid,username " \
    "FROM groups " \
    "LEFT JOIN users ON groups.owner_uuid = users.useruuid " + queryFilter + ";"
    )

    for group in group_names:
        addition = {}
        addition['name'] = group[1]
        if include_uuids: addition['owner_uuid'] = group[2]
        addition['owner_name'] = group[3]
        groups[group[0]] = addition
    
    group_members = queryData(connection, "SELECT group_id,useruuid,username " \
    "FROM group_relations " \
    "LEFT JOIN users ON group_relations.uuid = users.useruuid " + queryFilter + ";"
    )

    for members in group_members:
        mem = {}
        if include_uuids: mem['uuid'] = members[1]
        mem['username'] = members[2]

        mem_list = groups[members[0]]['members'] if 'members' in groups[members[0]] else []
        mem_list.append(mem)
        groups[members[0]]['members'] = mem_list

    return groups

def create_group(connection, uuid, name) -> int:
    """Create a new group with the specified name. The owner of the group is the provided uuid."""
    group_id = writeData(connection, "INSERT INTO groups(owner_uuid, group_name) VALUES(%s,%s) RETURNING group_id;", uuid, name)

    add_user(connection, uuid, group_id[0])
    return group_id

def delete_group(connection, group_id) -> None:
    """Delete the specified group. This should only be allowed to be done by the owner."""
    writeData(connection, "DELETE FROM groups WHERE group_id = %s", group_id)

def add_user(connection, uuid, group_id) -> None:
    """Add a user to the specified group. This assumes the user uuid is valid; use auth.user_exists to confirm before calling this."""
    writeData(connection, "INSERT INTO group_relations(group_id, uuid) VALUES (%s,%s);", group_id, uuid)

def remove_user(connection, uuid, group_id) -> None:
    """Remove a user from the specified group. This should not be used if the user is the owner of the group."""
    writeData(connection, "DELETE FROM group_relations WHERE group_id = %s AND uuid = %s", group_id, uuid)

def transfer_ownership(connection, uuid, group_id) -> None:
    """Transfer ownership of the specified group to the specified user."""
    writeData(connection, "UPDATE groups SET owner_uuid = %s WHERE group_id = %s", uuid, group_id)