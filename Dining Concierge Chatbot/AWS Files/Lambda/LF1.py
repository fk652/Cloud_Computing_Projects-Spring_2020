

import math
import dateutil.parser
import datetime
import time
import os
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """


def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


""" --- Helper Functions --- """


def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')


def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def isvalid_date(date):
    try:
        datetime.datetime.strptime(date, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def validate_input(dining_date, dining_time, num_people, phone, location, cuisine):
    
    if dining_date is not None:
        if not isvalid_date(dining_date):
            return build_validation_result(False, 'date', 'I did not understand that, what date?')
        elif datetime.datetime.strptime(dining_date, '%Y-%m-%d').date() < datetime.date.today():
            return build_validation_result(False, 'date', 'You can only pick a date from today onwards. What date?')

    if dining_time is not None:
        logger.debug("Time is %s" % dining_time)

        if len(dining_time) != 5:
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'time', 'I did not understand that, what time?')

        hour, minute = dining_time.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        if math.isnan(hour) or math.isnan(minute):
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'time', 'I did not understand that, what time?')

    if num_people is not None:
        if not (0 < parse_int(num_people) <= 30):
            return build_validation_result(False, 'num_people', 'Party size must be between 1 and 30 people. How many?')

    if phone is not None:
        if len(phone) != 10:
            return build_validation_result(False, 'phone', 'Invalid phone number. Phone number should be 10 digits number. Try again?')

    if location is not None:
        if location.lower() != 'new york':
            return build_validation_result(False, 'location', 'Sorry, we only support restaurants in New York at this moment. Where?')

    if cuisine is not None:
        cuisines = ['Mexican','Chinese','Italian','Thai','Japanese','Mediterranean']
        if (cuisine[0].upper() + cuisine[1:].lower()) not in cuisines:
            return build_validation_result(False, 'cuisine', f'Sorry, we only support these cuisines {cuisines} at the moment? Which cuisine?')

    return build_validation_result(True, None, None)


""" --- Functions that control the bot's behavior --- """

def greet(intent_request):
    return close(
        intent_request['sessionAttributes'],
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': 'Hi there, how can I help?'
        }
    )
    
def thank(intent_request):
    return close(
        intent_request['sessionAttributes'],
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': 'You\'re welcome.'
        }
    )
    
def suggest(intent_request):
    print(intent_request)
    location = get_slots(intent_request)['location']
    cuisine = get_slots(intent_request)['cuisine']
    num_people = get_slots(intent_request)['num_people']
    dining_date = get_slots(intent_request)['date']
    dining_time = get_slots(intent_request)['time']
    phone = get_slots(intent_request)['phone']

    if intent_request['invocationSource'] == 'DialogCodeHook':
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt for the first violation detected.
        slots = get_slots(intent_request)

        validation_result = validate_input(dining_date, dining_time, num_people, phone, location, cuisine)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])
       
        return delegate(intent_request['sessionAttributes'], intent_request['currentIntent']['slots'])

    sqs = boto3.client('sqs')
    queue_url = 'https://sqs.us-east-1.amazonaws.com/762867899973/dining_concierge'
    response = sqs.send_message(
        QueueUrl=queue_url,
        DelaySeconds=10,
        MessageAttributes={
            'Location': {
                'DataType': 'String',
                'StringValue': location
            },
            'DiningDate': {
                'DataType': 'String',
                'StringValue': dining_date
            },
            'DiningTime': {
                'DataType': 'String',
                'StringValue': dining_time
            },
            'NumPeople': {
                'DataType': 'String',
                'StringValue': num_people
            },
            'Cuisine': {
                'DataType': 'String',
                'StringValue': cuisine
            },
            'PhoneNum': {
                'DataType': 'String',
                'StringValue': phone
            }
        },
        MessageBody=(
            'Restaurant suggestion'
        )
    )
    logger.debug("Put into Queue succeeded. MessageId: %s" % response['MessageId'])

    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'You\'re all set. Expect my suggestions shortly! Have a good day'})


""" --- Intents --- """


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'GreetingIntent':
        return greet(intent_request)
    elif intent_name == 'ThankYouIntent':
        return thank(intent_request)
    elif intent_name == 'DiningSuggestionsIntent':
        return suggest(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
