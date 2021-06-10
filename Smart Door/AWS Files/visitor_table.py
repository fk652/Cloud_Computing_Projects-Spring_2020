import sys
import boto3
from boto3.dynamodb.conditions import Key, Attr
import os

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
print("Connected to DynamoDB")

table_name = 'visitors'
existing_tables = client.list_tables()['TableNames']

if table_name not in existing_tables:
    table = dynamodb.create_table(
        TableName = table_name,
        AttributeDefinitions=[
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'phone_number',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'name',
                'AttributeType': 'S'
            },


        ],
        KeySchema = [
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'
            }
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'phone_number_Index',
                'KeySchema': [
                    {
                        'AttributeName': 'phone_number',
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
                        {
                            'IndexName': 'name_Index',
                            'KeySchema': [
                                {
                                    'AttributeName': 'name',
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
