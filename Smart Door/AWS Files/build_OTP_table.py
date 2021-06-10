import sys
import boto3
from boto3.dynamodb.conditions import Key, Attr
import os

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
table_name = 'passcodes'
existing_tables = client.list_tables()['TableNames']

if table_name not in existing_tables:
    table = dynamodb.create_table(
        TableName = table_name,
        AttributeDefinitions=[
            {
                'AttributeName': 'OTP',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'Face_ID',
                'AttributeType': 'S'
            },
        ],
        KeySchema = [
            {
                'AttributeName': 'OTP',
                'KeyType': 'HASH'
            }
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'Face_ID_Index',
                'KeySchema': [
                    {
                        'AttributeName': 'Face_ID',
                        'KeyType': 'HASH'
                    },
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )

    # Wait until the table exists.
    table.meta.client.get_waiter('table_exists').wait(TableName=table_name)

    response = client.update_time_to_live(
        TableName=table_name,
        TimeToLiveSpecification={
            'Enabled': True,
            'AttributeName': 'TimeToLive'
        }
    )

    # Print out some data about the table.
    print("passcodes table created", table.item_count)
else:
    print("passcodes table already exists")
