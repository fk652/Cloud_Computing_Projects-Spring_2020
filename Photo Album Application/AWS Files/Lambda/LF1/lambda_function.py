import json
import urllib.parse
import boto3

from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from datetime import datetime
import os.path

print('Loading function')

credentials = boto3.Session().get_credentials()
# print(credentials)
region = 'us-east-1'

rekognition = boto3.client('rekognition', 
                        region_name = region,
                        aws_access_key_id = '*',
                        aws_secret_access_key = '*')
                        
host = 'vpc-photos-y6l4xet4rpcr4vm26d77chpiru.us-east-1.es.amazonaws.com'
service = 'es'
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

es = Elasticsearch(
    hosts = [{'host': host, 'port': 443}],
    http_auth = awsauth,
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection,
    timeout=3000
)

def lambda_handler(event, context):
    #print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    print("Received event:", key)
        
    # Check that the image type is supported
    imageType = os.path.splitext(key)[1]
    if not imageType:
        print("Could not determine the image type.")
        return
    elif imageType != ".jpg" and imageType != ".png" and imageType != ".jpeg":
        print('Unsupported image type:', imageType)
        return
    print('Image is valid:', key)
    
    # Get the rekognition labels
    response = rekognition.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':key}}, MaxLabels=10)
    labels = [label['Name'] for label in response['Labels']]
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    print('Labels found:', labels)
    
    # Create index in elasticsearch
    index_obj = {   'objectKey': key,
                    'bucket': bucket,
                    'createdTimestamp': timestamp,
                    'labels': labels }
                    
    es.index(index="photos", id=key, body=index_obj)
    print('new image successfully indexed:', key)
