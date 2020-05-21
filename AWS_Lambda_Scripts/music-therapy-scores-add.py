import json
import boto3
from botocore.exceptions import ClientError
import decimal
import logging
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime, timedelta
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

def addSessionInfo(info) :
    try:
        info = json.loads(info, parse_float=decimal.Decimal)
        
        if not "userID" in info or not "password" in info:
            return wrap_response(400, json.dumps({"error": "Either userID or password is missing"}))
        
        userID = info["userID"]
        password = info["password"]
        
        # connect to the db
        dynamodb = boto3.resource('dynamodb')
        
        users_table = dynamodb.Table("MusicTherapyUsers")
        
        user_data = users_table.get_item(Key = {
            "userID": userID
        })
        
        if not 'Item' in user_data:
            return wrap_response(400, json.dumps({"User not found in the database"}))
        
        incoming_password = hashlib.sha256(password.encode("utf-8")).hexdigest()
        real_password = user_data['Item']['password']
        
        if incoming_password != real_password:
            return wrap_response(200, json.dumps({"message": "error"})) # return success even if the password is wrong
        
        sessionScoresTable = dynamodb.Table('MusicTherapySessionScores')
        
        # add session scores
        sessionScoresTable.put_item(
            Item = {
                "userID": info['userID'],
                "date": datetime.today().strftime('%Y-%m-%d'),
                "sessionGoal": info['sessionGoal'],
                "preSessionScore": info['preSessionScore'],
                "postSessionScore": info['postSessionScore']
            }
        )
        
        if "history" in info:
        
            historyTable = dynamodb.Table('MusicTherapyHistory')
            
            # add history
            history = info['history']
            print("Length of history:", len(history))
            for songID in history:
                print(songID)
                key = {
                        "userID": info['userID'],
                        "songID": songID
                    } 
                print(key)
                response = historyTable.get_item(
                    Key = key
                )
                print(response)
                
                if not 'Item' in response and not 'Items' in response:
                    print("Item is being inserted")
                    historyTable.put_item(
                        Item = {
                            "userID": info['userID'],
                            "songID": songID,
                            "listenCount": 1
                        }    
                    )
                elif 'Item' in response:
                    print('Item is being updated to', int(response['Item']['listenCount']) + 1)
                    historyTable.update_item(
                        Key={
                            'userID': info['userID'],
                            'songID': songID
                        },
                        UpdateExpression="set listenCount = :r",
                        ExpressionAttributeValues={
                            ':r': int(response['Item']['listenCount']) + 1
                        }
                    )
    except ClientError as e:
        return wrap_response(500, "getAll(): " + e.response['Error']['Message'])
    else:
        return wrap_response(200, json.dumps({"message": "success"}, indent=4, cls=DecimalEncoder))


def wrap_response(statusCode, body):
    return {
        "statusCode": statusCode,
        "body": body
    }

def lambda_handler(event, context):
    testing = False
    if not testing:
        if(event['requestContext']['httpMethod'] == 'POST'):
            return addSessionInfo(event['body'])
    else:
        print(addSessionInfo(json.dumps(
        {
            "userID": "yerke",
            "sessionGoal": "relax",
            "date": "2020-04-10",
            "preSessionScore": "10",
            "postSessionScore": "30",
        	"history": ["classical.mp3", "fast.mp3"]
            
        } )   
    ))      
    #testing
    #return getSessionScores("yerke", numEntries=30)
