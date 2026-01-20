from connect import openConnection, queryData, writeData
import random
import requests

mojangUrl = "https://api.mojang.com/users/profiles/minecraft/"

def generate_userkey(connection, data) -> tuple[str, str]:
    rows = []
    with connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT mojanguuid,username FROM users;")
            rows = cursor.fetchall()

    username = data['username']
    if username in [row[1] for row in rows]:
        raise DuplicateData("Username " + username + " already exists!")

    mojangUuid = requests.get(mojangUrl+username).json()['id']

    if mojangUuid in [row[0] for row in rows]:
        raise DuplicateData("Error: that user already has an account!")
    
    uid = ""
    acceptableValues = list(range(48, 58))
    acceptableValues.extend(range(65, 91))
    acceptableValues.extend(range(97, 123))
    
    for char in mojangUuid:
        uid += char
        uid += chr(random.choice(acceptableValues))
    
    return uid, mojangUuid

def validate(connection, data) -> tuple[bool, str | None]:
    with connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT username,mojanguuid FROM users WHERE useruuid = %s;",  (data['uuid'],))

            row = cursor.fetchone()

    if row is None or row[0] != data['username'].lower():
        return False, "Invalid access key/username pair!"
    
    if row[0] != data['username'].lower():
        mojangUuid = requests.get(mojangUrl+data['username']).json()['id']

        if row[1] == mojangUuid:
            writeData("UPDATE users SET username = %s WHERE useruuid = %s;", data['username'], data['uuid'])
        else:
            return False, "Invalid access key/username pair!"
        
    return True, None
    
def user_exists(connection, uuid):
    uuids = queryData(connection, "SELECT useruuid FROM users;")
    return uuid in [uuids[0] for uid in uuids]

def username_exists(connection, username):
    usernames = queryData(connection, "SELECT username FROM users;")
    return username.lower() in [user[0].lower() for user in usernames]

def get_uuid_from_username(connection, username):
    return queryData(connection, "SELECT useruuid FROM users WHERE username = %s;", username, fetchAll=False)[0]



class MissingData(Exception):
    def __init__(self, errorCode: int, message: str, *args):
        super().__init__(*args)

        self.errorCode = errorCode
        self.errorMsg = message

class DuplicateData(Exception):
    def __init__(self, message: str, *args):
        super().__init__(*args)

        self.errorMsg = message

def data_present(data, fields: list[str]) -> tuple[bool, list[str] | None]:
    missing_fields = []
    for field in fields:
        if field not in data:
            missing_fields += field 
    missing_data = len(missing_fields) != 0
    return not missing_data, missing_fields if missing_data else None 