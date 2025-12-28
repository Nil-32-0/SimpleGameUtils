from connect import queryData, writeData

def get_groups(uuid):
    """Get all group ids of groups the user specified is a member of."""
    tuple_list = queryData("SELECT group_id FROM group_relations WHERE uuid = %s;", uuid)
    return [tup[0] for tup in tuple_list]

def get_owned_groups(uuid):
    """Get all group ids of groups owned by the user specified."""
    tuple_list = queryData("SELECT group_id FROM groups WHERE owner_uuid = %s;", uuid)
    return [tup[0] for tup in tuple_list]
        
def get_group_members(group_id):
    """Get all uuids of the members of the specified group."""
    tuple_list = queryData("SELECT uuid FROM group_relations WHERE group_id = %s;", group_id)
    return [tup[0] for tup in tuple_list]

def get_group_member_usernames(group_id):
    """Get all usernames of the members of the specified group."""
    tuple_list = queryData("SELECT username " \
        "FROM group_relations LEFT JOIN users " \
        "ON group_relations.uuid = users.useruuid " \
        "WHERE group_id = %s;", group_id
    )
    return [tup[0] for tup in tuple_list]

def get_group_info(group_id, include_uuids = True):
    """Get the group name, owner name and uuid (optional), and a list of its members, with their names and uuids (optional)."""
    group_info = {}
    group = queryData("SELECT group_name,owner_uuid,username " \
    "FROM groups " \
    "LEFT JOIN users ON groups.owner_uuid = users.useruuid " \
    "WHERE group_id = %s", group_id)[0]

    members = queryData("SELECT useruuid,username " \
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

def get_groups_info(group_ids: list[int], include_uuids = True):
    """Get the group names, owners names and uuids (optional), and lists of the group members, with their names and uuids (optional)."""
    groups = {}
    queryFilter = "WHERE group_id = " + str(group_ids[0])
    if len(group_ids) > 1:
        for id in group_ids:
            queryFilter += " OR group_id = " + str(id)

    group_names = queryData("SELECT group_id,group_name,owner_uuid,username " \
    "FROM groups " \
    "LEFT JOIN users ON groups.owner_uuid = users.useruuid " + queryFilter + ";"
    )

    for group in group_names:
        addition = {}
        addition['name'] = group[1]
        if include_uuids: addition['owner_uuid'] = group[2]
        addition['owner_name'] = group[3]
        groups[group[0]] = addition
    
    group_members = queryData("SELECT group_id,useruuid,username " \
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

def create_group(uuid, name):
    """Create a new group with the specified name. The owner of the group is the provided uuid."""
    group_id = writeData("INSERT INTO groups(owner_uuid, group_name) VALUES(%s,%s) RETURNING group_id;", uuid, name)

    add_user(uuid, group_id[0])

def delete_group(group_id):
    """Delete the specified group. This should only be allowed to be done by the owner."""
    writeData("DELETE FROM groups WHERE group_id = %s", group_id)

def add_user(uuid, group_id):
    """Add a user to the specified group. This assumes the user uuid is valid; use auth.user_exists to confirm before calling this."""
    writeData("INSERT INTO group_relations(group_id, uuid) VALUES (%s,%s);", group_id, uuid)

def remove_user(uuid, group_id):
    """Remove a user from the specified group. This should not be used if the user is the owner of the group."""
    writeData("DELETE FROM group_relations WHERE group_id = %s AND uuid = %s", group_id, uuid)

def transfer_ownership(uuid, group_id):
    """Transfer ownership of the specified group to the specified user."""
    writeData("UPDATE groups SET owner_uuid = %s WHERE group_id = %s", uuid, group_id)