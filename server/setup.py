from connect import writeData

if __name__ == "__main__":
    writeData(
        "CREATE TABLE users(" \
        "useruuid VARCHAR(64) PRIMARY KEY," \
        "username VARCHAR(16) NOT NULL," \
        "mojanguuid VARCHAR(32) NOT NULL" \
        ");" \
        "CREATE TABLE groups(" \
        "group_id SERIAL PRIMARY KEY," \
        "group_name VARCHAR(16) NOT NULL," \
        "owner_uuid VARCHAR(64) NOT NULL REFERENCES users" \
        ");" \
        "CREATE TABLE group_relations(" \
        "group_id INTEGER NOT NULL REFERENCES groups ON DELETE CASCADE," \
        "uuid VARCHAR(64) NOT NULL REFERENCES users ON DELETE CASCADE," \
        "PRIMARY KEY(group_id,uuid)" \
        ");" \
        "CREATE TABLE entry_types(" \
        "entry_type VARCHAR(64) PRIMARY KEY," \
        "parent_type VARCHAR(64) REFERENCES entry_types," \
        "description TEXT" \
        ");" \
        "CREATE TABLE items(" \
        "item_id VARCHAR(64) PRIMARY KEY," \
        "item_name VARCHAR(64) NOT NULL," \
        "item_type VARCHAR(64) NOT NULL REFERENCES entry_types" \
        ");" \
        "CREATE TABLE inventories(" \
        "inventory SERIAL PRIMARY KEY," \
        "remote_uid VARCHAR(64) NOT NULL" \
        ");" \
        "CREATE TYPE scopes AS ENUM ('PUBLIC','PRIVATE','GROUP');" \
        "CREATE TABLE projects(" \
        "project_id SERIAL PRIMARY KEY," \
        "project_name VARCHAR(64) NOT NULL," \
        "project_desc TEST," \
        "owner_uuid VARCHAR(64) NOT NULL REFERENCES users ON DELETE CASCADE," \
        "scope scopes NOT NULL," \
        "group_id integer," \
        "CONSTRAINT group_id_required CHECK (scope <> 'GROUP' OR group_id IS NOT NULL)" \
        ");" \
        "CREATE TABLE project_goals(" \
        "project_id INTEGER NOT NULL REFERENCES projects ON DELETE CASCADE," \
        "item_id VARCHAR(64) NOT NULL REFERENCES items ON DELETE CASCADE," \
        "goal_quantity INTEGER DEFAULT 0," \
        "PRIMARY KEY (project_id,item_id)" \
        ");" \
        "CREATE TABLE stored_items(" \
        "inventory INTEGER NOT NULL REFERENCES inventories ON DELETE CASCADE," \
        "item_id VARCHAR(64) NOT NULL REFERENCES items ON DELETE CASCADE," \
        "item_count INTEGER DEFAULT 0," \
        "project_id INTEGER REFERENCES projects ON DELETE CASCADE," \
        "CONSTRAINT unique_entries UNIQUE (inventory,item_id,project_id) NULLS NOT DISTINCT" \
        ");"
    )