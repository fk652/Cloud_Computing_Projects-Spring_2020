import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
import os
import time
from urllib.parse import parse_qs

def authenticate_OTP(passcode_input):
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

    delete_response = table.delete_item(
        Key={
            'OTP': passcode_input
        },
        ReturnValues = 'ALL_OLD'
    )

    if 'Attributes' not in delete_response:
        return '-1'
    elif delete_response['Attributes']['TimeToLive'] < time.time():
        return '-1'

    return delete_response['Attributes']['Face_ID']

def get_Visitor_Info(face_id):
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
    table = dynamodb.Table('visitors')
    
    response = table.query(
        KeyConditionExpression=Key("id").eq(face_id)
    )

    if response['Items'] == []:
        return 1
        
    return response['Items'][0]['name']

def lambda_handler(event, context):
    body = parse_qs(event["body"])
    passcode_input = body['passcode'][0]
    
    fail_response = {
        "statusCode": 200,
        "body": '<html><head><meta http-equiv="Refresh" content="0; url=http://nyudoorbell-visitor.s3-website-us-east-1.amazonaws.com/failure.html" /></head><body></body></html>',
        "headers": {
            'Content-Type': 'text/html',
            
        }
    }
    
    success_response = {
        "statusCode": 200,
        "body": "",
        "headers": {
            'Content-Type': 'text/html',
            
        }
    }
    
    face_id = authenticate_OTP(passcode_input)
    if face_id == '-1':
        return fail_response
    else:
        name = get_Visitor_Info(face_id)
        
        if type(name) is int:
            return fail_response
        
        success_response["body"] = '<html><head><meta http-equiv="Refresh" content="0; url=http://nyudoorbell-visitor.s3-website-us-east-1.amazonaws.com/success.html?name='+name+'" /></head><body></body></html>'
        return success_response
    
