import boto3
import json
import logging
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

eventbridge = boto3.client('events')

def send_eventbridge_event(profile_id,candidate_id):
    try:
        event_detail = {
            "profile_id": profile_id,        
            "candidate_id": candidate_id        
            }
        
        response = eventbridge.put_events(
            Entries=[
                {
                    'Source': 'ai.service',
                    'DetailType': 'candidate-profile-created',
                    'Detail': json.dumps(event_detail),
                    'EventBusName': 'wynt' 
                }
            ]
        )
        
        logger.info(f"Event sent to EventBridge: {response}")
    except ClientError as e:
        logger.error(f"Error sending event to EventBridge: {str(e)}")
        raise

