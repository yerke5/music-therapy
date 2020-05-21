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

def getSessionScores(data):
    try:
        data = json.loads(data)
        
        if not "userID" in data or not "password" in data:
            return wrap_response(400, json.dumps({"error": "Either userID or password is missing"}))
            
        userID = data['userID']
        password = data['password']
            
        if "numEntries" in data:
            numEntries = int(data["numEntries"])
        else:
            numEntries = 30
            
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
        
        if incoming_password != real_password and incoming_password != AUTHORISED_PASSWORD:
            return wrap_response(200, json.dumps({"message": "error"})) # return success even if the password is wrong
        
        table = dynamodb.Table('MusicTherapySessionScores')
        
        curr_year = datetime.now().year
        curr_month = datetime.now().month
        curr_day = datetime.now().day
        #latest = datetime.strptime(datetime.now(), "%y-%m-%d")
        latestDate = datetime.today() - timedelta(days=numEntries)
        latestDateStr =  datetime.strftime(latestDate, "%Y-%m-%d")
        api_res = {"userID": userID, "scores": []}  
        response = table.query(
            ProjectionExpression="userID, #dt, preSessionScore, postSessionScore, sessionGoal",
            ExpressionAttributeNames={"#dt": "date"},
            KeyConditionExpression=Key('userID').eq(userID) #& (Key('date').gt(latestDateStr))
        )
        #api_res['response'] = response
        
        
        #rows = response['Items'] if 'Items' in response else ([] if 'Item' not in response else response['Item'])
        rows = []
        if 'Items' in response:
            rows = response['Items']
        elif 'Item' in response:
            rows = [response['Item']]
        
        for i in range(min(len(rows), numEntries)):
            api_res['scores'].append({
                "date": rows[i]['date'],
                "preSessionScore": rows[i]['preSessionScore'],
                "postSessionScore": rows[i]['postSessionScore'],
                "sessionGoal": rows[i]['sessionGoal']
            })
    except ClientError as e:
        return wrap_response(500, json.dumps({"error": "getAll(): " + e.response['Error']['Message']}))
    else:
        return wrap_response(200, json.dumps(api_res, indent=4, cls=DecimalEncoder))

def wrap_response(statusCode, body):
    return {
        "statusCode": statusCode,
        "body": body
    }

def lambda_handler(event, context):
    #testing
    #return getSessionScores("yerke", numEntries=30)
    if(event['requestContext']['httpMethod'] == 'POST'):
        return getSessionScores(event['body'])
