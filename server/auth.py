from connect import openConnection
import flask
import random
import requests

def generate_userkey(data) -> tuple[str, str]:
    mojangUrl = "https://api.mojang.com/users/profiles/minecraft/"

    rows = []
    with openConnection() as connection:
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
    min = 48
    max = 126
    for char in mojangUuid:
        uid += char
        uid += chr(random.randint(min, max))
    
    return uid, mojangUuid

def validate(data):
    data_present(data, ['uuid', 'username'], 401)

    with openConnection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT username FROM users WHERE useruuid = %s;",  (data['uuid'],))

            row = cursor.fetchone()

    if row is None or row[0] != data['username'].lower():
        raise MissingData(401, "Invalid access key/username pair!")


class MissingData(Exception):
    def __init__(self, errorCode: int, message: str, *args):
        super().__init__(*args)

        self.errorCode = errorCode
        self.errorMsg = message

class DuplicateData(Exception):
    def __init__(self, message: str, *args):
        super().__init__(*args)

        self.errorMsg = message

def data_present(data, fields: list[str], errorCode = 400):
    for field in fields:
        if field not in data:
            raise MissingData(errorCode, "Error: Missing " + field + " field!")