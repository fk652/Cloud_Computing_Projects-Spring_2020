
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
import json

import sys
from boto3.dynamodb.conditions import Key, Attr
import urllib.parse
import time


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
                    region_name = 'us-west-2',
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
        time.sleep(0.5)
        # print(t)
        response = sns_client.publish(
            PhoneNumber = phone_number,
            Message = t
            )
        print(t)
        if 'MessageId' in response:
            print("message sent")
            return True
        return False



def dynamo_sns(business_ids, phone_num):
    '''
    Call this function in LF2, pass in list of business ids from ElasticSeach and the phone_number from SQS
    Queries DynamoDB yelp-restaurants table for additional restaurant indo
    Sends an SNS text message with a greeting followed by a message for each restaurant's info
    '''
    info = get_restaurant_info(business_ids)
    send_text_message(info, phone_num)




def lambda_handler(event, context):
    sqs = boto3.client(
        'sqs',
        aws_access_key_id='*',
        aws_secret_access_key='*',
        )
    queue_url = 'https://sqs.us-east-1.amazonaws.com/762867899973/dining_concierge'
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MessageAttributeNames=[
        'All'
    ],
        MaxNumberOfMessages=1,
    )
    #print(response)
    if 'Messages' in response:

        message = response['Messages'][0]
        receipt_handle = message['ReceiptHandle']
        data = message['MessageAttributes']

        #print(data)

        cuisine = data['Cuisine']['StringValue']
        phone_number="+1"+data['PhoneNum']['StringValue']
        print(cuisine,phone_number)


        host = 'search-yelp-restaurants-x35wnwt5lwjuiegna3cfu7ewne.us-east-1.es.amazonaws.com' # For example, my-test-domain.us-east-1.es.amazonaws.com
        region = 'us-east-1' # e.g. us-west-1

        service = 'es'
        credentials = boto3.Session().get_credentials()
        print(credentials)
        awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

        es = Elasticsearch(
            hosts = [{'host': host, 'port': 443}],
            http_auth = awsauth,
            use_ssl = True,
            verify_certs = True,
            connection_class = RequestsHttpConnection,
            timeout=3000
        )
        res = es.search(q=cuisine)
        ids = [r['_id'] for r in res['hits']['hits']]
        ids = ids[:5]

        #print(ids)
        message_response=dynamo_sns(ids, phone_number)
        if message_response:
            sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
        )

lambda_handler([],[])
