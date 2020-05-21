import json
import boto3
from botocore.exceptions import ClientError
import decimal
import logging
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime
import hashlib

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

def create_presigned_url(bucket_name, object_name, expiration=3600): 
    # Generate a presigned URL for the S3 object
    s3_client = boto3.client('s3', region_name='us-east-2')
    try:
        response = s3_client.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': object_name}, ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response

def wrap_response(statusCode, body):
    return {
        "statusCode": statusCode,
        "body": body
    }
    
def sort_users(users):
    return sorted(users, key=lambda k: k['userID'])

def add_user_info(info) :
    try:
        info = json.loads(info)
        if not "userID" in info or not "anxietyScore" in info or not "password" in info:
            return wrap_response(500, {"error": "UserID, anxiety score or password is/are missing"})
        
        print(type(info))
        
        # connect to the db
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('MusicTherapyUsers')
        
        content = {"date": datetime.today().strftime('%Y-%m-%d')}
        for key in info:
            print(key)
            if key != "userID" and key != "password":
                content[key] = info[key]
        
        hashed_password = hashlib.sha256(info['password'].encode("utf-8")).hexdigest()
        print(hashed_password)
        table.put_item(
            Item = {
                "userID": info['userID'],
                "password": hashed_password,
                "info": json.dumps(content, indent=4, cls=DecimalEncoder)
            }
        )
    except ClientError as e:
        return wrap_response(500, json.dumps({"error": "add_user_info(): " + e.response['Error']['Message']}))
    else:
        return wrap_response(200, json.dumps({"message": "User added successfully"}, indent=4, cls=DecimalEncoder))

def lambda_handler(event, context):
    if(event['requestContext']['httpMethod'] == 'POST'):
        return add_user_info(event['body'])