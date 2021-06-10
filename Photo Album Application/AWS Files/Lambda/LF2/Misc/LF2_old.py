import math
import dateutil.parser
import datetime
import time
import os
import logging
import boto3

from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
import json



logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def get_slots(intent_request):
    return intent_request['currentIntent']['slots']

def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response

def search(intent_request):
    print(intent_request)
    tags = []
    slots = get_slots(intent_request)
    for t in slots:
        if slots[t]:
            tags.append(slots[t])
    results = es(tags)
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': str(results)})
    return es(tags)

def fallback(intent_request):
    search_query = intent_request['inputTranscript']
    tags = []
    if '(' in search_query:
        search_query = search_query.replace("'",'').replace("(","").replace(")","")
        tags = search_query.split(",")
    else:
        tags=[search_query]
    results = es(tags)
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': str(results)})




def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    if intent_name == 'SearchIntent':
        return search(intent_request)
    elif intent_name == "KeywordIntent":
        return fallback(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def es(labels):
    host = 'vpc-photos-y6l4xet4rpcr4vm26d77chpiru.us-east-1.es.amazonaws.com'
    #host = 'vpc-photos-zd4pzjklhsh2hmg4rytiiplil4.us-east-1.es.amazonaws.com'# For example, my-test-domain.us-east-1.es.amazonaws.com
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
    mod_labels =[{"match":{"labels": l }} for l in labels]
    query= {
  "query" : {
    "bool" : {
      "should":mod_labels
    }
  }
}
    res = es.search(index='photos' , body=query)
    results = []
    for r in res['hits']['hits']:
        r=r["_source"]
        results.append({'url':'https://'+r['bucket']+'.s3.amazonaws.com/'+r['objectKey'],'labels':r['labels']})
    return results

def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    #logger.debug('event.bot.name={}'.format(event['bot']['name']))
    if 'currentIntent' in event:
        return dispatch(event)
    else:
        client = boto3.client('lex-runtime')
        response = client.post_text(
        botName='PhotoSearch',
        botAlias='$LATEST',
        userId='LF0',
        sessionAttributes={},
        requestAttributes={},
        inputText=event['queryStringParameters']['q']

        )
        return {
        'statusCode': 200,
        'headers': {
            "Access-Control-Allow-Origin": "*"
        },
        'body': json.dumps({
            'results': eval(response['message'])

        })}
