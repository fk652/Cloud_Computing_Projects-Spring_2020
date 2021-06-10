from decimal import *
from boto3.dynamodb.conditions import Key, Attr
from random import randrange
import time
import cv2
import base64
import boto3
import json
import math
import os
from datetime import datetime

MIN_RE_ENTRY_INTERVAL_IN_SECONDS = 60
BUCKET_NAME = 'nyudoorbell'
OWNER_ENDPOINT = 'http://smart-door-b1.s3-website-us-east-1.amazonaws.com/'
STREAM_NAME = 'DoorBell'
RK_COLLECTION_ID = 'doorbell'
owner_phone_num = ''
kv_client = boto3.client('kinesisvideo')
get_ep = kv_client.get_data_endpoint(StreamName=STREAM_NAME, APIName='GET_MEDIA_FOR_FRAGMENT_LIST')
kvam_ep = get_ep['DataEndpoint']
kvam_client = boto3.client('kinesis-video-archived-media', endpoint_url=kvam_ep)
s3_client = boto3.client('s3')
rk_client = boto3.client('rekognition')


def count_frame(input_vid_path):
    vid_cap = cv2.VideoCapture(input_vid_path)
    count = 0
    while True:
        has_frames, image = vid_cap.read()
        if not has_frames:
            break
        count += 1
    vid_cap.release()
    return count


def get_frame_from_fragment(fragment_id, frame_offset_in_sec, output_file_path):
    fragment_media = kvam_client.get_media_for_fragment_list(
        StreamName=STREAM_NAME,
        Fragments=[fragment_id])

    tmp_vid_path = '/tmp/' + fragment_id + '.webm'
    f = open(tmp_vid_path, 'wb')
    f.write(fragment_media['Payload'].read())
    f.close()
    print("[DEBUG] video created: ", tmp_vid_path, " info:", os.stat(tmp_vid_path))
    get_frame_from_vid(tmp_vid_path, output_file_path, frame_offset_in_sec)
    os.remove(tmp_vid_path)
    print('[DEBUG] ', "video deleted: " + tmp_vid_path)


def get_frame_from_vid(input_vid_path, output_file_path, sec):
    has_frame = False
    # cv2.CAP_PROP_FRAME_COUNT doesn't return correct value
    total_frame_count = count_frame(input_vid_path)
    vid_cap = cv2.VideoCapture(input_vid_path)
    frame_pos = int(sec * (vid_cap.get(cv2.CAP_PROP_FPS) - 1))
    if frame_pos >= total_frame_count:
        frame_pos = total_frame_count - 1
    if total_frame_count > 0:
        # vid_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos) doesn't work
        for i in range(0, total_frame_count):
            has_frame, image = vid_cap.read()
            if has_frame and i == frame_pos:
                cv2.imwrite(output_file_path, image)  # save frame as JPG file
                print('[DEBUG] ', "image created: ", output_file_path, " info: ", os.stat(output_file_path))
    if not has_frame:
        raise Exception("Cannot capture frame")


def index_faces(bucket, key):
    response = rk_client.index_faces(
        Image={'S3Object': {'Bucket': bucket,
                            'Name': key}},
        ExternalImageId=key,
        CollectionId=RK_COLLECTION_ID,
        MaxFaces=1)
    face_id = response['FaceRecords'][0]['Face']['FaceId']
    print('[DEBUG] face indexed.', ' face id: ', face_id, ' external image id: ', key)

    return face_id


def search_faces(bucket, key):
    response = rk_client.search_faces_by_image(
        Image={'S3Object': {'Bucket': bucket,
                            'Name': key}},
        CollectionId=RK_COLLECTION_ID,
        MaxFaces=1)
    face_id = None
    if response['FaceMatches']:
        face_id = response['FaceMatches'][0]['Face']['FaceId']
        print('[DEBUG] face matched.', ' face id: ', face_id, ' external image id: ', key)
    return face_id


def check_visitor(id, BUCKET_NAME, img_name):
    aws_access = '*'
    aws_secret_access = '*'

    dynamodb = boto3.resource('dynamodb',
                              region_name='us-east-1',
                              aws_access_key_id=aws_access,
                              aws_secret_access_key=aws_secret_access)
    table = dynamodb.Table('visitors')
    response = ""
    response = table.get_item(
        Key={
            'id': id,
        })

    if response:
        if 'Item' in response:
            table.update_item(
                Key={
                    'id': id
                },
                UpdateExpression='SET photos = list_append(photos, :photo_obj)',
                ExpressionAttributeValues={
                    ":photo_obj": [
                        {
                            "objectKey": img_name,
                            "bucket": BUCKET_NAME,
                            "createdTimestamp":
                                str(datetime.now())
                        }
                    ]
                })

            return response['Item']
    return None


def send_SNS_approval(face_id, img_url,img_name):
    aws_access = '*'
    aws_secret_access = '*'
    sns_client = boto3.client('sns',
                              region_name='us-east-1',
                              aws_access_key_id=aws_access,
                              aws_secret_access_key=aws_secret_access)

    message = "New visitor. Click on the link to approve.\n"
    message += "Image Link:\n" + img_url + "\n"
    message += "Approval Link:\n" +  OWNER_ENDPOINT + "?id=" + face_id +"&img_name="+img_name
    response = sns_client.publish(
        PhoneNumber=owner_phone_num,
        Message=message
    )
    print("Message Sent")


def get_last_visited_date(face_id):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('recent_visitors')
    response = table.query(
        KeyConditionExpression=Key("faceId").eq(face_id)
    )
    last_visited_date = float(response['Items'][0]['dateVisited']) if response['Items'] else None
    print('[DEBUG] ', "last visited on: ", last_visited_date)
    return last_visited_date


def update_last_visited_date(face_id, date_visited):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('recent_visitors')
    table.put_item(
        Item={
            'faceId': face_id,
            'dateVisited': Decimal(str(date_visited)),
            'timeToLive': Decimal(str(date_visited + 1800))
        }
    )
    print('[DEBUG] ', "last visited updated:", date_visited)


def lambda_handler(event, context):
    for record in event['Records']:
        # Kinesis data is base64 encoded so decode here
        try:
            print('[DEBUG] ', record)
            payload = base64.b64decode(record['kinesis']['data'])
            result = json.loads(payload)
            print('[DEBUG] ', result)
            face_result = result['FaceSearchResponse']
            if face_result:
                face_id = None
                if face_result[0]['MatchedFaces']:
                    face_id = face_result[0]['MatchedFaces'][0]['Face']['FaceId']
                    print('[DEBUG] ', "face detected in Kinesis data: ", face_id)
                frag_id = result['InputInformation']['KinesisVideo']['FragmentNumber']
                server_timestamp = result['InputInformation']['KinesisVideo']['ServerTimestamp']
                frame_offset_in_sec = result['InputInformation']['KinesisVideo']['FrameOffsetInSeconds']
                frame_timestamp = server_timestamp + frame_offset_in_sec

                # Will not process if the visitor shows up again within MIN_RE_ENTRY_INTERVAL_IN_SECONDS
                last_visited_date = None
                if face_id:
                    last_visited_date = get_last_visited_date(face_id)
                if last_visited_date and \
                        (frame_timestamp - last_visited_date < MIN_RE_ENTRY_INTERVAL_IN_SECONDS):
                    print('[DEBUG] ', "Skipping: face ", face_id, " visited too frequently.")
                else:
                    d, i = math.modf(frame_timestamp)
                    img_name = str(int(i)) + "_" + (str(int(d * 1000)) + '00')[0:3] + '.jpg'
                    tmp_img_path = '/tmp/' + img_name

                    get_frame_from_fragment(frag_id, frame_offset_in_sec, tmp_img_path)
                    s3_client.upload_file(tmp_img_path, BUCKET_NAME, img_name)
                    print('[DEBUG] ', "file: " + img_name + " uploaded to S3")
                    os.remove(tmp_img_path)
                    print('[DEBUG] ', "image deleted: " + tmp_img_path)

                    if not face_id:
                        face_id = search_faces(BUCKET_NAME, img_name)
                        if face_id:
                            last_visited_date = get_last_visited_date(face_id)
                        else:
                            face_id = index_faces(BUCKET_NAME, img_name)
                    if last_visited_date and \
                            (frame_timestamp - last_visited_date < MIN_RE_ENTRY_INTERVAL_IN_SECONDS):
                        print('[DEBUG] ', "Skipping: face ", face_id, " visited too frequently.")
                    else:
                        update_last_visited_date(face_id, frame_timestamp)
                        response = check_visitor(face_id, BUCKET_NAME, img_name)
                        if response:
                            OTP = add_OTP(face_id)
                            send_SNS_OTP(response['phone_number'], OTP)
                        else:
                            presigned_url = s3_client.generate_presigned_url('get_object',
                                                                             Params={'Bucket': BUCKET_NAME,
                                                                                     'Key': img_name},
                                                                             ExpiresIn=3600)
                            send_SNS_approval(face_id, presigned_url)

        except Exception as e:
            print('[ERROR] ', str(e))


###
# generating OTP and sending OTP to a visitor
###
def add_OTP(face_id):
    aws_access = '*'
    aws_secret_access = '*'
    client = boto3.client('dynamodb',
                          region_name='us-east-1',
                          aws_access_key_id=aws_access,
                          aws_secret_access_key=aws_secret_access)

    dynamodb = boto3.resource('dynamodb',
                              region_name='us-east-1',
                              aws_access_key_id=aws_access,
                              aws_secret_access_key=aws_secret_access)
    table = dynamodb.Table('passcodes')

    response = table.query(
        IndexName='Face_ID_Index',
        KeyConditionExpression=Key("Face_ID").eq(face_id)
    )
    if response['Items'] != []:
        if response['Items'][0]['TimeToLive'] > time.time():
            return '-1'
        else:
            delete_response = table.delete_item(
                Key={
                    'OTP': response['Items'][0]['OTP']
                }
            )

    created = False
    while not created:
        random_pass = ""
        for i in range(6):
            digit = randrange(10)
            random_pass += str(digit)

        response = table.query(
            KeyConditionExpression=Key("OTP").eq(random_pass)
        )
        if response['Items'] == []:
            insert_response = client.put_item(
                TableName='passcodes',
                Item={
                    'OTP': {'S': random_pass},
                    'Face_ID': {'S': face_id},
                    'TimeToLive': {'N': str(int(time.time() + 300))}
                }
            )
            created = True

    return random_pass


def send_SNS_OTP(phone_num, OTP):
    if OTP == '-1':
        print("This face_id already has an active OTP")
        return

    aws_access = '*'
    aws_secret_access = '*'
    sns_client = boto3.client('sns',
                              region_name='us-east-1',
                              aws_access_key_id=aws_access,
                              aws_secret_access_key=aws_secret_access)

    message = OTP + " is your visitor one-time passcode"
    response = sns_client.publish(
        PhoneNumber=phone_num,
        Message=message
    )
    print("OTP sent")

# x = add_OTP('034c6560-8a9f-42f3-a16d-8cc8ecd3fbbf')
# print(x)
# send_SNS_OTP("+16466101368", x)
###
