import boto3
import json
import urllib.parse
from io import BytesIO
import os
import email
from sms_spam_classifier_utilities import one_hot_encode
from sms_spam_classifier_utilities import vectorize_sequences
runtime= boto3.client('runtime.sagemaker')
import datetime
from botocore.exceptions import ClientError


def send_email(message,prediction,prob):
    SENDER = "SpamTest  <hw4@mynox.tech>"
    RECIPIENT = message['From']
    AWS_REGION = "us-east-1"
    SUBJECT = "Email Classification"
    BODY_HTML = """<html>
    <head></head>
    <body>
      <h1>Email Classification</h1>
      <p>“We received your email sent at {}with the
    subject {}. <p><br>
     <p>
     Here is a 240 character sample of the email body:
    {}
    <br>
    <p>
     The email was categorized as {} with a
    {}% confidence.<p>
    </body>
    </html>
                """.format(message['Date'],message['Subject'],message['Body'][:240],prediction,prob)

    CHARSET = "UTF-8"
    client = boto3.client('ses',region_name=AWS_REGION)
    try:
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    }
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])

def get_email(email_content):
    b = email.message_from_string(email_content)

    message={'From':b['From'],'To':b['To'],'Subject':b['Subject'],'Date':b['Date']}
    body = ""

    if b.is_multipart():
        for part in b.walk():
            ctype = part.get_content_type()
            if ctype == 'text/plain':
                body = part.get_payload()  # decode
                break
    else:
        body = b.get_payload()
    message['Body']=body.strip().replace("\r"," ").replace("\n"," ")
    return message


def lambda_handler(event, context):
    vocabulary_length = 9013

    label ='Not Spam'
    prob = 0
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(record['s3']['object']['key'], encoding='utf-8')

        s3 = boto3.resource('s3')
        obj = s3.Object(bucket, key)
        email_content=""
        for line in obj.get()['Body']._raw_stream:
            email_content+=str(line.decode("utf-8"))
        message = get_email(email_content)
        text = message['Body']
        print("Message:",text)
        test_messages = [text]
        one_hot_test_messages = one_hot_encode(test_messages, vocabulary_length)
        encoded_test_messages = vectorize_sequences(one_hot_test_messages, vocabulary_length)

        payload = json.dumps(encoded_test_messages.tolist())
        endpoint_name = os.environ['PredictionEndpoint']
        print(endpoint_name)
        response = runtime.invoke_endpoint(EndpointName=endpoint_name,
                                           Body=payload)
        result = json.loads(response['Body'].read().decode())
        print(result)
        if int(result['predicted_label'][0][0]):
            label ='Spam'
        prob = result['predicted_probability'][0][0]*100
        send_email(message,label,prob)
        return {
                'statusCode': 200,
                'body': json.dumps(message)
            }
