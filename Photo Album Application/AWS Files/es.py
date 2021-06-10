#Test Code For Domain Creation
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
import json
def create_index():
    host = 'vpc-photos-zd4pzjklhsh2hmg4rytiiplil4.us-east-1.es.amazonaws.com' # For example, my-test-domain.us-east-1.es.amazonaws.com
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
    mapping = {
                'settings': {
                    'analysis':
                    {
                        'analyzer': {
                            'porter_english': {
                                'type': 'snowball',
                                'tokenizer': 'standard',
                                'stopwords': '_english_',
                                "filter": ["standard", "lowercase", "stop", "snowball"]
                                }
                            }
                        }
                    },
                'mappings': {
                    'properties': {
                        'objectKey': {
                            'type': 'text'
                        },
                        'labels': {
                            'type': 'text',
                            'analyzer': 'porter_english',
                            "search_analyzer": "porter_english"
                        },
                        "createdTimestamp":{
                        'type':"date"
                        },
                        'bucket': {
                            'type': 'text'
                        }
                    }
                }
            }
    es.indices.delete(index='photos',ignore=400)
    es.indices.create(index="photos",body=mapping,ignore=400)
    document ={
    "objectKey": "my-photo.jpg",
    "bucket": "my-photo-bucket",
    "createdTimestamp": "2018-11-05T12:40:02",
    "labels": ["person","dog","ball","blue"]
    }

    es.index(index="photos", doc_type="_doc", id='test', body=document)
