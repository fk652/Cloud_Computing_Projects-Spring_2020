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

#Update Test Pipeline

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def es(labels):
    host = 'vpc-photos-y6l4xet4rpcr4vm26d77chpiru.us-east-1.es.amazonaws.com'
    #host = 'vpc-photos-zd4pzjklhsh2hmg4rytiiplil4.us-east-1.es.amazonaws.com'
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
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()

    client = boto3.client('lex-runtime')
    response = client.post_text(
    botName='PhotoSearch',
    botAlias='$LATEST',
    userId='LF0',
    sessionAttributes={},
    requestAttributes={},
    inputText=event['queryStringParameters']['q']
        )
    labels = []
    slots=[]
    results = []
    if 'slots' in response:
        slots=response['slots']
        for t in slots:
            if slots[t]:
                labels.append(slots[t])
        results = es(labels)

    return {
    'statusCode': 200,
    'headers': {
        "Access-Control-Allow-Origin": "*"
    },
    'body': json.dumps({
        'results': results

    })}
