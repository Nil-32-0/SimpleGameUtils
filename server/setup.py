from auth import openConnection
from connect import writeData
import json
from pathlib import Path
from csv import reader
from getpass import getpass

path = Path(__file__).parent

if __name__ == "__main__":
    CREATE_INI = True if input("Create database options file(y/n)? ").lower()[0] == "y" else False
    CREATE_TABLES = True if input("Create tables(y/n)? ").lower()[0] == "y" else False
    POPULATE_ITEMS = True if input("Populate items(y/n)? ").lower()[0] == "y" else False

    if CREATE_INI:
        host = input("Enter the host IP: ")
        database = input("Enter the database name: ")
        user = input("Enter the username for the SGU query role: ")
        passwd = getpass("Enter the password for the user: ")
        with open(str(path)+"/database.ini", "w") as file:
            file.write("[postgresql]\n")
            file.write("host="+host+"\n")
            file.write("database="+database+"\n")
            file.write("user="+user+"\n")
            file.write("password="+passwd)
    connection = openConnection(str(path)+"/database.ini")
    if CREATE_TABLES:
        writeData(connection, 
        "CREATE TABLE users(" \
        "useruuid VARCHAR(64) PRIMARY KEY," \
        "username VARCHAR(16) NOT NULL," \
        "password VARCHAR(32) NOT NULL" \
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
        "item_id VARCHAR(128) PRIMARY KEY," \
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
        "project_desc TEXT," \
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
        "CONSTRAINT unique_entries UNIQUE NULLS NOT DISTINCT (inventory,item_id,project_id)" \
        ");"
        )
    if POPULATE_ITEMS:
        game = input("Enter the game ID: ")
        style = input("Enter the input style(json/csv): ").lower()
        if style == "json":
            for file in path.rglob("./library/" + game + "/items/*.json"):
                data = json.loads(file.read_text())
                print(data['displayname'][3:])
                print(data['itemid'])
                print(data['internalname'])
                writeData(connection, "INSERT INTO items(item_id,item_name,item_type) VALUES(%s,%s,%s);",
                            data['internalname']+"&"+data['itemid'], data['displayname'][3:], "item")
        elif style == "csv":
            with open(str(path)+"/library/" + game + "/items.csv", newline='') as file:
                csv_reader = reader(file, delimiter=",", quotechar='|')
                writeData(connection, "INSERT INTO entry_types(entry_type) VALUES(%s);", "item")
                for line in csv_reader:
                    id = line[1]
                    name = line[0]
                    writeData(connection, "INSERT INTO items(item_id,item_name,item_type) VALUES(%s,%s,%s);",
                                id, name, "item")