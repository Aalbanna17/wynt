import boto3
import logging
import time


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Correctly initialize CloudWatch Logs client
cloudwatch_logs = boto3.client('logs')
LOG_GROUP_NAME = 'Wynt-process-AI'

def ensure_log_stream(LOG_STREAM_NAME):
    try:
        # Create log group if it doesn't exist
        response = cloudwatch_logs.describe_log_groups(logGroupNamePrefix=LOG_GROUP_NAME)
        if not any(group['logGroupName'] == LOG_GROUP_NAME for group in response['logGroups']):
            cloudwatch_logs.create_log_group(logGroupName=LOG_GROUP_NAME)

        # Create log stream if it doesn't exist
        response = cloudwatch_logs.describe_log_streams(logGroupName=LOG_GROUP_NAME, logStreamNamePrefix=LOG_STREAM_NAME)
        if not any(stream['logStreamName'] == LOG_STREAM_NAME for stream in response['logStreams']):
            cloudwatch_logs.create_log_stream(logGroupName=LOG_GROUP_NAME, logStreamName=LOG_STREAM_NAME)

    except Exception as e:
        logger.error(f"Failed to ensure log stream: {str(e)}")


def log_to_cloudwatch_logs(LOG_STREAM_NAME,message):
    try:
        ensure_log_stream(LOG_STREAM_NAME)

        response = cloudwatch_logs.describe_log_streams(logGroupName=LOG_GROUP_NAME, logStreamNamePrefix=LOG_STREAM_NAME)
        log_stream = next((stream for stream in response['logStreams'] if stream['logStreamName'] == LOG_STREAM_NAME), None)
        sequence_token = log_stream.get('uploadSequenceToken', None)

        log_event = {
            'logGroupName': LOG_GROUP_NAME,
            'logStreamName': LOG_STREAM_NAME,
            'logEvents': [
                {
                    'timestamp': int(time.time() * 1000),
                    'message': message
                }
            ]
        }

        if sequence_token:
            log_event['sequenceToken'] = sequence_token

        cloudwatch_logs.put_log_events(**log_event)
        logger.info(f"Logged to CloudWatch Logs: {message}")

    except Exception as e:
        logger.error(f"Failed to log to CloudWatch Logs: {str(e)}")

