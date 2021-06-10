from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
import json

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

# document = {
#     "title": "Moneyball",
#     "director": "Bennett Miller",
#     "year": "2011"
# }

restaurants = json.load(open('Data/restaurants1.json'))
cuisines = ['Mexican','Chinese','Italian','Thai','Japanese','Mediterranean']
i=0
for c in cuisines:
    for r in restaurants[c]:
        i+=1
        document = {"cuisine": c}
        es.index(index="restaurants", doc_type="_doc", id=r['id'], body=document)
    print(c)
