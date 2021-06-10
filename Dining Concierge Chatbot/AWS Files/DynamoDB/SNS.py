import sys
import boto3
from boto3.dynamodb.conditions import Key, Attr
import urllib.parse
import time

#### TESTING #########################
ids1 = ["-KahGyU9G7JT0JmoC_Yc0Q",
        "07CFPHGST8k37uHYAGxYqQ",
        "0kFP2UiYHoJHx6d9w1ZNhg"
        ]
ids = ["jWuUibgnTGsJibOrr6UUSw",
        "J1daQ8bKu551cpNx9Z522w",
        "CkIuzZ71nhSgoPayPFVTUA"
        ]
ids2 = ["-KahGyU9G7JT0JmoC_Yc0Q"]

phone_number = "+16466101368" #uses e.164 phone number format (i.e +1 123 456 7890)

# # Reading yelp restaurants JSON data
# import json
# data = []
# ids = []
# json_file = open('restaurants.json', encoding='utf-8')
# data = json.load(json_file)
# for food in data:
#     for business in data[food]:
#         ids.append(business["id"])
# ids = ids[0:1001]
######################################

def get_restaurant_info(ids):  
    '''
    takes in an array of business ids, returns a list of restaurant object data
    '''
    # Connecting to AWS DynamoDB
    aws_access = '*'
    aws_secret_access = '*'
    dynamodb = boto3.resource('dynamodb',
                    region_name = 'us-east-1',
                    aws_access_key_id = aws_access,
                    aws_secret_access_key = aws_secret_access)
    table = dynamodb.Table('yelp-restaurants')

    # Query dynamodb for each business_id
    responses = []
    for i in ids:
        time.sleep(.2)
        response = table.query(
            KeyConditionExpression=Key("business_id").eq(i)
        )
        items = response['Items']
        if items != []:
            responses.append(items)
    return responses

def send_text_message(info, phone_number): 
    '''
    sends text messages for each of the restaurant info
    '''
    # Connecting to AWS SNS
    aws_access = '*' # MIGHT NEED TO USE A DIFFERENT AWS ACCOUNT IF SNS LIMIT IS REACHED
    aws_secret_access = '*'
    sns_client = boto3.client('sns', 
                    region_name = 'us-east-1',
                    aws_access_key_id = aws_access,
                    aws_secret_access_key = aws_secret_access)

    #creating a message for each restaurant
    messages = []
    messages.append('Hello! Here are my restaurant suggestions for you:')
    for i in info:
        msg = '\n--------------------\n' + i[0]['name'] + '\n\n'

        r_address = ''
        r_map = ''
        for l in i[0]['location']:
            r_address = r_address + l + '\n'
            r_map = r_map + l + ','
        r_map = urllib.parse.quote_plus(r_map[:-1])
        msg = msg + r_address + '\n'
        msg = msg + "https://www.google.com/maps/search/?api=1&query=" + r_map + '\n\n'

        msg = msg + "Ratings: " + str(i[0]['rating']) + '/5\n' + "Reviews: " + str(i[0]['review_count'])

        if 'phone' in i[0].keys():
            msg = msg + '\n\n' + "Phone: " + i[0]['phone'] 
        
        messages.append(msg)
    
    #sorting messages and appending them, to help save costs on text messaging
    messages.sort(key=len)
    texts = []
    single_text = ''
    for i in range(0, len(messages)):
        if len(messages[i].encode('utf-8')) < (1600 - len(single_text.encode('utf-8'))):
            single_text = single_text + messages[i]
        else:
            texts.append(single_text)
            single_text = messages[i]
    if single_text != '':
        texts.append(single_text)

    #send all the text messages
    texts[0] = texts[0][0:50] + texts[0][71:]
    for t in texts:
        time.sleep(1)
        # print(t)
        response = sns_client.publish(
            PhoneNumber = phone_number,
            Message = t
            )
        print("message sent")

def dynamo_sns(business_ids, phone_num):
    ''' 
    Call this function in LF2, pass in list of business ids from ElasticSeach and the phone_number from SQS
    Queries DynamoDB yelp-restaurants table for additional restaurant indo
    Sends an SNS text message with a greeting followed by a message for each restaurant's info
    '''
    info = get_restaurant_info(business_ids)
    send_text_message(info, phone_num)

dynamo_sns(ids, phone_number)
