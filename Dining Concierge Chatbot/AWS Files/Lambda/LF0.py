import json
import boto3

def lambda_handler(event, context):

    client = boto3.client('lex-runtime')
    response = client.post_text(
        botName='DiningConcierge',
        botAlias='$LATEST',
        userId='LF0',
        sessionAttributes={},
        requestAttributes={},
        inputText=json.loads(event["body"])['message']['value']
    )
    return {
        'statusCode': 200,
        'headers': { 
            "Access-Control-Allow-Origin": "*" 
        },
        'body': response['message']
    }
