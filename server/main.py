import flask
import random
import requests
from connect import connect
import psycopg2

app = flask.Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook_reciever():
    data = flask.request.json

    print("Recieved webhook data: ", data)
    return flask.jsonify({'message': 'Webhook recieved correctly!'}), 200

@app.route("/userkey/generate", methods=["POST"])
def generate_userkey():
    data = flask.request.json

    mojangUrl = "https://api.mojang.com/users/profiles/minecraft/"

    rows = None
    try:
        with connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT mojanguuid FROM users")
                rows = cursor.fetchall()

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return flask.jsonify({'message': "Error: " + str(error)}), 503

    username = data['username']
    mojangUuid = requests.get(mojangUrl+username).json()['id']

    for row in rows: 
        if row[0] == mojangUuid:
            return flask.jsonify({'message': "Error: That user already has an account!"}), 403
    
    uid = ""
    for char in mojangUuid:
        min = 48
        max = 126
        uid += char
        uid += chr(random.randint(min, max))
    
    try:
        with connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO users(useruuid, username, mojanguuid) VALUES(%s,%s,%s);", (
                    uid, username, mojangUuid
                ))

                connection.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return flask.jsonify({'message': "Error: " + str(error)}), 503
    
    return flask.jsonify({'message': "Your access key has been generated, save this in a safe place", 'key': uid}), 200

inv = {}

def item_modification(itemID, delta):
    if itemID in inv:
        inv[itemID] += delta
    else:
        inv[itemID] = delta

    if inv[itemID] < 0:
        inv[itemID] -= delta
        raise ValueError("You cannot have less than 0 "+ itemID + "! Value has been reset to previous value.")
    
    return inv[itemID]

def get_username_from_uuid(uuid):
    row = None
    with connect() as connection:
        with connection.cursor() as cur:
            cur.execute("SELECT username FROM users WHERE useruuid = %s;",  (uuid,))

            row = cur.fetchone()

    return row[0] if row != None else None

def authenticate(username, uuid):
    try:
        validUser = get_username_from_uuid(uuid)
        return validUser is not None and validUser == username
    except Exception as ex:
        print(ex)
        return False
    

@app.route("/webhook/item_changed", methods=["POST"])
def item_reciever():
    data = flask.request.json

    print(data)

    if 'username' not in data:
        return flask.jsonify({'message': "Invalid username!"}), 401
    if 'uuid' not in data:
        return flask.jsonify({'message': "Invalid uuid!"}), 401
    if not authenticate(data['username'], data['uuid']):
        return flask.jsonify({'message': "Invalid access key/username pair!"}), 401

    item = data['item']
    try:
        newQty = item_modification(item, data['amount'])
    except ValueError as v:
        return flask.jsonify({"message": v.args[0]}), 422

    print(inv)

    return flask.jsonify({'item': item, 'amount': newQty}), 200

if __name__ == "__main__":
    app.run(debug=True)