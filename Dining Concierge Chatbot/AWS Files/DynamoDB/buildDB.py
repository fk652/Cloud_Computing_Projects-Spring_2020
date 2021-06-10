import sys
import boto3
from boto3.dynamodb.conditions import Key, Attr
import os
import json
import time
import datetime

from collections.abc import Iterable, Mapping, ByteString, Set
import numbers
import decimal

context = decimal.Context(
    Emin=-128, Emax=126, rounding=None, prec=38,
    traps=[decimal.Clamped, decimal.Overflow, decimal.Underflow]
)

def dump_to_dynamodb(item):
    # don't catch str/bytes with Iterable check below;
    # don't catch bool with numbers.Number
    if isinstance(item, (str, ByteString, bool)):
        return item

    # ignore inexact, rounding errors
    if isinstance(item, numbers.Number):
        return context.create_decimal(item)
    
    # mappings are also Iterable
    elif isinstance(item, Mapping):
        return {
            key: dump_to_dynamodb(value)
            for key, value in item.values()
        }

    # boto3's dynamodb.TypeSerializer checks isinstance(o, Set)
    # so we can't handle this as a list
    elif isinstance(item, Set):
        return set(map(dump_to_dynamodb, item))
    
    # may not be a literal instance of list
    elif isinstance(item, Iterable):
        return list(map(dump_to_dynamodb, item))
    
    # datetime, custom object, None
    return item


# Reading yelp restaurants JSON data
data = []
restaurants = {}
json_file = open('restaurants.json', encoding='utf-8')
data = json.load(json_file)
count = 0
for food in data:
    for business in data[food]:
        b_id = business["id"]
        restaurants[b_id] = {}
        restaurants[b_id]["business_id"] = b_id

        if business["name"] != "":
            restaurants[b_id]["name"] = business["name"]

        if business["location"]["display_address"] !=  "":
            restaurants[b_id]["location"] = business["location"]["display_address"]

        if business["coordinates"] != {}:
            restaurants[b_id]["coordinates"] = {}
            restaurants[b_id]["coordinates"]["latitude"] = dump_to_dynamodb(business["coordinates"]["latitude"])
            restaurants[b_id]["coordinates"]["longitude"] = dump_to_dynamodb(business["coordinates"]["longitude"])

        if business["review_count"] != "":
            restaurants[b_id]["review_count"] = dump_to_dynamodb(business["review_count"])

        if business["rating"] != "":
            restaurants[b_id]["rating"] = dump_to_dynamodb(business["rating"])

        if business["location"]["zip_code"] != "":
            restaurants[b_id]["zip_code"] = dump_to_dynamodb(business["location"]["zip_code"])

        if business["display_phone"] != "":
            restaurants[b_id]["phone"] = business["display_phone"]

        count+=1
# print(count, len(restaurants))

# Connecting to AWS DynamoDB
#########################
aws_access = '*'
aws_secret_access = '*'
##########################
client = boto3.client('dynamodb', 
                   region_name = 'us-east-1',
				   aws_access_key_id = aws_access,
		           aws_secret_access_key = aws_secret_access)

dynamodb = boto3.resource('dynamodb',
				   region_name = 'us-east-1',
				   aws_access_key_id = aws_access,
		           aws_secret_access_key = aws_secret_access)
print("Connected to DynamoDB")

# Creating DynamoDB yelp table
table_name = 'yelp-restaurants'
existing_tables = client.list_tables()['TableNames']

if table_name not in existing_tables:
    table = dynamodb.create_table(
        TableName='yelp-restaurants',
        KeySchema=[
            {
                'AttributeName': 'business_id',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'insertedAtTimestamp',
                'KeyType': 'RANGE'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'business_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'insertedAtTimestamp',
                'AttributeType': 'N'
            },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )

    # Wait until the table exists.
    table.meta.client.get_waiter('table_exists').wait(TableName='yelp-restaurants')

    # Print out some data about the table.
    print("yelp restaurant table created",table.item_count)
else:
    table = dynamodb.Table('yelp-restaurants')
    print("yelp table already exists")

# Inserting all restaurant data into DynamoDB
failed = {}
if table.item_count != len(restaurants):
    print("inserting all restaurant data into DynamoDB")
    with table.batch_writer() as batch:
        for r in restaurants:
            time.sleep(.20)
            response = table.query(
                KeyConditionExpression=Key("business_id").eq(r)
            )
            if response['Items'] == []:
                print("adding", r)
                try:
                    restaurants[r]["insertedAtTimestamp"] = dump_to_dynamodb(datetime.datetime.now().timestamp())
                    batch.put_item(
                        Item = restaurants[r]
                    )
                except:
                    print("could not add", r)
                    failed[r] = restaurants[r]
    print("yelp restaurant table is complete")

    # Retry all failed restaurant objects
    failedCount = 0
    with table.batch_writer() as batch:
        for f in failed:
            time.sleep(.20)
            response = table.query(
                KeyConditionExpression=Key("business_id").eq(f)
            )
            if response['Items'] == []:
                print("trying again", f)
                try:
                    restaurants[f]["insertedAtTimestamp"] = dump_to_dynamodb(datetime.datetime.now().timestamp())
                    batch.put_item(
                        Item = restaurants[f]
                    )
                except:
                    print("could not add again", f)
                else:
                    failedCount += 1
            else:
                failedCount += 1

    if len(failed) == failedCount:
        print("failed list succesfully completed")
    else:
        print("failed list not completed")
else:
    print("ALL data has already been inserted")

print("Build DynamoDB yelp-restaurants FINISH")
