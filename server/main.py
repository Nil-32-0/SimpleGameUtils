import flask
import random
import requests
import psycopg2

import auth
from auth import MissingData, DuplicateData
from connect import openConnection, writeData


app = flask.Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook_reciever():
    data = flask.request.json

    print("Recieved webhook data: ", data)
    return flask.jsonify({'message': 'Webhook recieved correctly!'}), 200

@app.route("/userkey/generate", methods=["POST"])
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
        print(error)
        return flask.jsonify({'message': "Error: " + str(error)}), 503
    
    try:
        writeData("INSERT INTO users(useruuid, username, mojanguuid) VALUES(%s,%s,%s);", 
            uid, data['username'], mojanguuid 
        )

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return flask.jsonify({'message': "Error: " + str(error)}), 503
    
    return flask.jsonify({'message': "Your access key has been generated, save this in a safe place", 'key': uid}), 200


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