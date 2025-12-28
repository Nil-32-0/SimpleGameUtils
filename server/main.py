import flask
import psycopg2

import auth
from auth import MissingData, DuplicateData
from connect import openConnection, writeData
import groups


app = flask.Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook_reciever():
    data = flask.request.json

    print("Recieved webhook data: ", data)
    return flask.jsonify({'message': 'Webhook recieved correctly!'}), 200

@app.route("/webhook/userkey/generate", methods=["POST"])
def generate_userkey():
    data = flask.request.json

    try:
        auth.data_present(data, ['username'])
        uid, mojanguuid = auth.generate_userkey(data)
    except MissingData as error:
        print(error)
        return flask.jsonify({'message': error.errorMsg}), error.errorCode
    except DuplicateData as error:
        print(error)
        return flask.jsonify({'message': error.errorMsg}), 400
    except (Exception, psycopg2.DatabaseError) as error:
        print("Errored while validating data:")
        print(error)
        return flask.jsonify({'message': "Error: " + str(error)}), 503
    
    try:
        writeData("INSERT INTO users(useruuid, username, mojanguuid) VALUES(%s,%s,%s);", 
            uid, data['username'].lower(), mojanguuid 
        )

    except (Exception, psycopg2.DatabaseError) as error:
        print("Errored while writing data:")
        print(error)
        return flask.jsonify({'message': "Error: " + str(error)}), 503
    
    return flask.jsonify({'message': "Your access key has been generated, save this in a safe place", 'key': uid}), 200

@app.route("/webhook/groups/create", methods = ["POST"])
def create_group():
    data = flask.request.json

    try:
        auth.validate(data)
        auth.data_present(data, ["group_name"])
    except MissingData as error:
        return flask.jsonify({'message': error.errorMsg}), error.errorCode
    except Exception as error:
        print(error)
        return flask.jsonify({'message': "Error: " + str(error)}), 500

    groups.create_group(data['uuid'], data['group_name'])
    return flask.jsonify({'message': "Group " + data['group_name'] + " has been created"}), 200

@app.route("/webhook/groups/delete", methods = ["POST"])
def delete_group():
    data = flask.request.json

    try:
        auth.validate(data)
        auth.data_present(data, ["group_id"])
    except MissingData as error:
        return flask.jsonify({'message': error.errorMsg}), error.errorCode
    except Exception as error:
        print(error)
        return flask.jsonify({'message': "Error: " + str(error)}), 500
    
    if int(data['group_id']) not in groups.get_owned_groups(data['uuid']):
        return flask.jsonify({'message': "You can't delete a group you don't own!"}), 403
    
    groups.delete_group(data["group_id"])
    return flask.jsonify({'message': "Group with id " + data['group_id'] + " has been deleted"}), 200

@app.route("/webhook/groups/transfer", methods = ["POST"])
def transfer_group():
    data = flask.request.json

    try:
        auth.validate(data)
        auth.data_present(data, ["group_id", "new_owner_username"])
        if not auth.username_exists(data['new_owner_username']):
            raise MissingData(400, "You can't transfer ownership to a user that doesn't exist!")
    except MissingData as error:
        return flask.jsonify({'message': error.errorMsg}), error.errorCode
    except Exception as error:
        print(error)
        return flask.jsonify({'message': "Error: " + str(error)}), 500
    
    if int(data['group_id']) not in groups.get_owned_groups(data['uuid']):
        return flask.jsonify({'message': "You can't transfer ownership of a group you don't own!"}), 403
    
    new_uuid = auth.get_uuid_from_username(data['new_owner_username'])
    if new_uuid == data['uuid']:
        return flask.jsonify({'message': "You can't transfer ownership of a group to yourself!"}), 400
    if new_uuid not in groups.get_group_members(data['group_id']):
        return flask.jsonify({'message': "You can't transfer ownership of a group to a user who isn't in it!"}), 400

    groups.transfer_ownership(new_uuid, data['group_id'])
    return flask.jsonify({'message': "Group ownership has been transferred!"}), 200

@app.route("/webhook/groups/add", methods = ["POST"])
def add_user():
    data = flask.request.json

    try:
        auth.validate(data)
        auth.data_present(data, ["group_id", "new_member_username"])
        if not auth.username_exists(data['new_member_username']):
            raise MissingData(400, "You can't add a user that doesn't exist to the group!")
    except MissingData as error:
        return flask.jsonify({'message': error.errorMsg}), error.errorCode
    except Exception as error:
        print(error)
        return flask.jsonify({'message': "Error: " + str(error)}), 500
    
    if data['new_member_username'] == data['username']:
        return flask.jsonify({'message': "You can't add yourself to a group!"}), 400
    if int(data['group_id']) not in groups.get_owned_groups(data['uuid']):
        return flask.jsonify({'message': "You can't add a user to a group you don't own!"}), 403
    
    new_uuid = auth.get_uuid_from_username(data['new_member_username'])
    groups.add_user(new_uuid, data['group_id'])
    return flask.jsonify({'message': data['new_member_username'] + " has been added to the group!"}), 200

@app.route("/webhook/groups/remove", methods = ["POST"])
def remove_user():
    data = flask.request.json

    try:
        auth.validate(data)
        auth.data_present(data, ["group_id", "member_username"])
    except MissingData as error:
        return flask.jsonify({'message': error.errorMsg}), error.errorCode
    except Exception as error:
        print(error)
        return flask.jsonify({'message': "Error: " + str(error)}), 500
    
    if data['member_username'] == data['username']:
        return flask.jsonify({'message': "You can't remove yourself from a group!"}), 400
    if int(data['group_id']) not in groups.get_owned_groups(data['uuid']):
        return flask.jsonify({'message': "You can't remove a user from a group you don't own!"}), 403
    
    user_uuid = auth.get_uuid_from_username(data['member_username'])
    if user_uuid not in groups.get_group_members(data['group_id']):
        return flask.jsonify({'message': "You can't remove a user from a group they're not in!"}), 400
    groups.remove_user(user_uuid, data['group_id'])
    return flask.jsonify({'message': data['member_username'] + " has been removed from the group!"}), 200

@app.route("/webhook/groups/leave", methods = ["POST"])
def leave_group():
    data = flask.request.json

    try:
        auth.validate(data)
        auth.data_present(data, ["group_id"])
    except MissingData as error:
        return flask.jsonify({'message': error.errorMsg}), error.errorCode
    except Exception as error:
        print(error)
        return flask.jsonify({'message': "Error: " + str(error)}), 500
    
    if int(data['group_id']) in groups.get_owned_groups(data['uuid']):
        return flask.jsonify({'message': "You can't leave a group you own!"}), 400
    if data['uuid'] not in groups.get_group_members(data['group_id']):
        return flask.jsonify({'message': "You can't leave a group you're not in!"}), 400
    
    groups.remove_user(data['uuid'], data['group_id'])
    return flask.jsonify({'message': "You have successfully left the group!"}), 200

@app.route("/webhook/groups/members", methods = ["POST"])
def group_members():
    data = flask.request.json

    try:
        auth.validate(data)
        auth.data_present(data, ["group_id"])
    except MissingData as error:
        return flask.jsonify({'message': error.errorMsg}), error.errorCode
    except Exception as error:
        print(error)
        return flask.jsonify({'message': "Error: " + str(error)}), 500
    
    members = groups.get_group_member_usernames(data['group_id'])
    if data['uuid'] not in groups.get_group_members(data['group_id']):
        return flask.jsonify({'message': "You cannot view members of a group you aren't in!"}), 403
    return flask.jsonify({'members': members}), 200

@app.route("/webhook/groups", methods = ["POST"])
def get_groups():
    data = flask.request.json

    try:
        auth.validate(data)
    except MissingData as error:
        return flask.jsonify({'message': error.errorMsg}), error.errorCode
    except Exception as error:
        print(error)
        return flask.jsonify({'message': "Error: " + str(error)}), 500
    
    group_list = groups.get_groups(data['uuid'])
    if len(group_list) == 0:
        return flask.jsonify({'groups': {}}), 200
    return flask.jsonify({'groups': groups.get_groups_info(group_list, False)}), 200

def get_projects(uuid):
    try:
        with openConnection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT project_name,project_desc FROM projects WHERE scope = 'PUBLIC' OR creator_uuid = %s", (uuid,))
                projects = cursor.fetchall()

                if len(projects) == 0:
                    return flask.jsonify({'message': "No projects visible!"}), 200

                return flask.jsonify({
                    'project_names': [project[0] for project in projects],
                    'project_descs': [project[1] for project in projects]
                }), 200

    except Exception as ex:
        print(ex)
        return flask.jsonify({'message': ex}), 401

@app.route("/webhook/get_projects", methods=["POST"])
def get_projects_hook():
    data = flask.request.json

    try:
        auth.validate(data)
    except MissingData as error:
        return flask.jsonify({'message': error.errorMsg}), error.errorCode
    except Exception as error:
        print(error)
        return flask.jsonify({'message': "Error: " + str(error)}), 500
    
    return get_projects(data['uuid'])

@app.route("/webhook/create_project", methods=["POST"])
def create_project():
    data = flask.request.json

    try:
        auth.validate(data)
    except MissingData as error:
        return flask.jsonify({'message': error.errorMsg}), error.errorCode
    except Exception as error:
        print(error)
        return flask.jsonify({'message': "Error: " + str(error)}), 500
    
    if 'project_name' not in data:
        return flask.jsonify({'message': "A project name must be specified!"}), 400
    
    project_desc = data['project_desc'] if 'project_desc' in data else ""
    scope = data['scope'] if 'scope' in data else "PUBLIC"

    try:
        with openConnection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO projects(project_name,project_desc,scope,creator_uuid) VALUES (%s,%s,%s,%s)", (
                    data['project_name'],
                    project_desc,
                    scope,
                    data['uuid']
                ))
                connection.commit()
    except Exception as ex:
        print(ex)
        return flask.jsonify({'message': ex}), 500

    return get_projects(data['uuid'])

if __name__ == "__main__":
    app.run(debug=True)