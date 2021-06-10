import json
from random import randint
from boto3.dynamodb.conditions import Key, Attr
from random import randrange
import time
import json
import base64
import boto3
import json
from datetime import datetime
import math
import os
BUCKET_NAME = 'nyudoorbell'

def add_OTP(face_id):
    aws_access = '*'
    aws_secret_access = '*'
    client = boto3.client('dynamodb',
                        region_name = 'us-east-1',
                        aws_access_key_id = aws_access,
                        aws_secret_access_key = aws_secret_access)

    dynamodb = boto3.resource('dynamodb',
                    region_name = 'us-east-1',
                    aws_access_key_id = aws_access,
                    aws_secret_access_key = aws_secret_access)
    table = dynamodb.Table('passcodes')
    response = table.query(
        IndexName='Face_ID_Index',
        KeyConditionExpression=Key("Face_ID").eq(face_id)
    )
    if response['Items'] != []:
        if response['Items'][0]['TimeToLive'] > time.time():
            return '-1'
        else:
            delete_response = table.delete_item(
                Key={
                    'OTP': response['Items'][0]['OTP']
                }
            )

    created = False
    while not created:
        random_pass = ""
        for i in range(6):
            digit = randrange(10)
            random_pass += str(digit)

        response = table.query(
            KeyConditionExpression=Key("OTP").eq(random_pass)
        )
        if response['Items'] == []:
            insert_response = client.put_item(
                TableName='passcodes',
                Item = {
                    'OTP': {'S': random_pass},
                    'Face_ID': {'S': face_id},
                    'TimeToLive': {'N': str(int(time.time() + 300))}
                }
            )
            created = True

    return random_pass
# def send_text_message(phone_number):
#     aws_access = '##'
#     aws_secret_access = '##'
#     sns_client = boto3.client('sns',
#                     region_name = 'us-west-2',
#                     aws_access_key_id = aws_access,
#                     aws_secret_access_key = aws_secret_access)
#
#     OTP = randint(100000,999999)
#     response = sns_client.publish(
#         PhoneNumber = phone_number,
#         Message = "OTP Expires in 5 Minutes\n. Your OTP is:"+ str(OTP)
#         )
#     print(OTP)
#     if 'MessageId' in response:
#         print("message sent")
#         return OTP
#     return False

def send_SNS_OTP(phone_num, OTP):
    if OTP == '-1':
        print("This face_id already has an active OTP")
        return

    aws_access = '*'
    aws_secret_access = '*'
    sns_client = boto3.client('sns',
                    region_name = 'us-east-1',
                    aws_access_key_id = aws_access,
                    aws_secret_access_key = aws_secret_access)

    message = OTP + " is your visitor one-time passcode"
    response = sns_client.publish(
            PhoneNumber = phone_num,
            Message = message
            )
    print("OTP sent")

def lambda_handler(event, context):
    event=json.loads(event['body'])
    OTP = add_OTP(event['id'])

    aws_access = '*'
    aws_secret_access = '*'

    dynamodb = boto3.resource('dynamodb',
    				   region_name = 'us-east-1',
    				   aws_access_key_id = aws_access,
    		           aws_secret_access_key = aws_secret_access)
    table = dynamodb.Table('visitors')
    table.put_item(
          Item={
                'id': event['id'],
                'phone_number': event['phone_number'],
                'name': event['name'],
                    "photos": [
                            {
                            "objectKey": event['img_name'],
                            "bucket": BUCKET_NAME,
                            "createdTimestamp":
                            str(datetime.now())
                            }
                            ]
    })
    send_SNS_OTP(event['phone_number'],OTP)
    return  {
        "statusCode": 200,
    "headers" :{
        'Content-Type': 'application/json',
    	'Access-Control-Allow-Origin': "*",
    },
    "body": "{\"result\":"+ "\"sucesss!"+str(OTP)+"\"}"
    #"body": str(event)
    }
