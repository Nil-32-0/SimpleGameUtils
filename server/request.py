import requests

webhook_url = "http://localhost:5000/webhook"

username = "EpicBoss32"
accessKey = "dSb>bU84337Y1s6_7U5S040F4@973q0jbe572YeT465}1faA83eta_6o2hdY6Ra<"

def showResponse(response):
    print(response.status_code)
    print(response.json())

def sendItemIncrease(itemID, amount):
    url = webhook_url + "/item_changed"
    data = {
        'username': username,
        'uuid': accessKey,
        'item': itemID,
        'amount': amount
    }
    showResponse(requests.post(url, json=data))

def viewProjects():
    url = webhook_url + "/get_projects"
    data = {
        'username': username,
        'uuid': accessKey
    }
    showResponse(requests.post(url, json=data))

def createProject(name, desc, scope):
    url = webhook_url + "/"

def generateKey(userName):
    url = "http://localhost:5000/userkey/generate"
    data = {
        'username': userName
    }
    showResponse(requests.post(url, json=data))

userInput = input(">")
while userInput != "quit":
    command = userInput.split(" ")
    # if command[0] == "add":
    #     sendItemIncrease(command[1], int(command[2]))
    if command[0] == "generate":
        generateKey(command[1])
    if command[0] == "projects":
        if len(command) == 4:
            createProject(command[1], command[2], command[3])
        else:
            viewProjects()
    userInput = input(">")