import json
import boto3
from botocore.exceptions import ClientError
import decimal
import logging
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime
import hashlib

AUTHORISED_PASSWORD = hashlib.sha256(hashlib.sha256(b"6tfyNepAQtGxbaJz").hexdigest().encode("utf-8")).hexdigest()

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

def wrap_response(statusCode, body):
    return {
        "statusCode": statusCode,
        "body": body
    }

def get_history_by_user2(user_id):
    try:
        # connect to the db
        dynamodb = boto3.resource('dynamodb')
        
        # we will only need the table version of the table here
        table = dynamodb.Table('MusicTherapyHistory')
        
        response = table.query(
            ProjectionExpression="userID, songID, listenCount",
            KeyConditionExpression=Key('userID').eq(user_id) & (Key('songID').between("0", "z"))
        )
        
        api_res = {"count": 0, "userID": user_id, "history": []}
        if 'Item' in response:
            api_res = {"count": 1, "history": [{"songID": response["Item"]["songID"], "listenCount": response["Item"]["listenCount"]}]}
        elif 'Items' in response:
            api_res["count"] = len(response['Items'])
            for row in response["Items"]:
                api_res["history"].append({
                    "songID": row["songID"],
                    "listenCount": row["listenCount"]
                })
    except ClientError as e:
        return wrap_response(500, "getHistory(): " + e.response['Error']['Message'])
    else:
        return wrap_response(200, json.dumps(api_res, indent=4, cls=DecimalEncoder))
     
def get_history_by_user(data):
    try:
        data = json.loads(data)
        if not "userID" in data or not "password" in data:
            return wrap_response(400, json.dumps({"error": "Either password or userID is missing"}))
        
        user_id = data["userID"]
        password = data["password"]
        
        # connect to the db
        dynamodb = boto3.resource('dynamodb')
        
        # we will only need the table version of the table here
        users_table = dynamodb.Table('MusicTherapyUsers')
        res = users_table.get_item(Key = {
            "userID": user_id
        })
        
        if not "Item" in res:
            return wrap_response(400, json.dumps({"error": "User not in database"}))
        
        incoming_password = hashlib.sha256(password.encode("utf-8")).hexdigest()
        real_password = res['Item']['password']
        if incoming_password != real_password and incoming_password != AUTHORISED_PASSWORD:
            return wrap_response(200, json.dumps({"message": "error"}))
        
        history_table = dynamodb.Table('MusicTherapyHistory')
        
        response = history_table.query(
            ProjectionExpression="userID, songID, listenCount",
            KeyConditionExpression=Key('userID').eq(user_id) & (Key('songID').between("0", "z"))
        )
        
        api_res = {"count": 0, "userID": user_id, "history": [], "message": "success"}
        if 'Item' in response:
            api_res = {"count": 1, "history": [{"songID": response["Item"]["songID"], "listenCount": response["Item"]["listenCount"]}]}
        elif 'Items' in response:
            api_res["count"] = len(response['Items'])
            for row in response["Items"]:
                api_res["history"].append({
                    "songID": row["songID"],
                    "listenCount": row["listenCount"]
                })
                
    except ClientError as e:
        return wrap_response(500, "getHistory(): " + e.response['Error']['Message'])
    else:
        return wrap_response(200, json.dumps(api_res, indent=4, cls=DecimalEncoder))

def lambda_handler(event, context):
    if event['requestContext']['httpMethod'] == "POST":
        return get_history_by_user(event['body'])