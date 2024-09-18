import boto3
from botocore.exceptions import ClientError
import logging
import os
import asyncio
import json

from extracttext import extract_text_from_pdf
from s3_operations import get_s3_object
from cvprocess import cvprocess
from cloudwatch_operations import log_to_cloudwatch_logs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

QUEUE_wynt_resumes = os.getenv('QUEUE_wynt_resumes')

if not QUEUE_wynt_resumes:
    logger.error("Environment variable QUEUE_wynt_resumes is not set.")
    exit(1)

sqs = boto3.client('sqs')
LOG_STREAM_NAME = 'sqs_processing_stream'

async def process_message(message):
    try:
        messagea = message['Body']
        logger.debug(f"Raw message body: {messagea}")
        log_to_cloudwatch_logs(LOG_STREAM_NAME, f"Started processing message ID: {message['MessageId']}.")

        body = json.loads(message['Body'])
        receipt_handle = message['ReceiptHandle']
        bucket = body['detail']['bucket']['name']
        key = body['detail']['object']['key']

        sqs.delete_message(
            QueueUrl=QUEUE_wynt_resumes,
            ReceiptHandle=receipt_handle
        )
        logger.info(f"Deleted message from queue: {receipt_handle}")

        logger.info(f"Processing file: s3://{bucket}/{key}")
        log_to_cloudwatch_logs(LOG_STREAM_NAME, f"Processing file: s3://{bucket}/{key}")

        if key.endswith('resume.pdf'):
            try:
                file_content, metadata = get_s3_object(bucket, key)
                if file_content is None:
                    logger.error("Failed to extract valid text from PDF due to S3 retrieval error.")
                    log_to_cloudwatch_logs(LOG_STREAM_NAME, f"Failed to extract valid text from PDF due to S3 retrieval error. {message['MessageId']}.")
                    return

                extracted_text, success = extract_text_from_pdf(file_content)
                logger.info(f"Extracted text from {key}: {extracted_text[:100]}...")

                if not success:
                    logger.error(f"Failed to extract text from PDF: {key}")
                    log_to_cloudwatch_logs(LOG_STREAM_NAME, f"Failed to extract text from PDF: {key}")
                    log_to_cloudwatch_logs(LOG_STREAM_NAME, f"Failed to extract text from PDF: {key} -- {message['MessageId']}.")
                    return
                
                await cvprocess(metadata, extracted_text)

            except Exception as pdf_error:
                error_message = str(pdf_error)
                logger.error(f"Error processing PDF: {error_message}")
                if "Error reading PDF file: code=7: no objects found" in error_message or "500: Failed to process PDF file" in error_message:
                    logger.error("Encountered specific PDF processing error. Deleting message from SQS.")
                    log_to_cloudwatch_logs(LOG_STREAM_NAME, f"Encountered specific PDF processing error. Deleting message from SQS.{error_message} -- {message['MessageId']}.")
                    return
                else:
                    raise

        log_to_cloudwatch_logs(LOG_STREAM_NAME, f"Finished processing message ID: {message['MessageId']} successfully.")

    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON for message ID: {message['MessageId']}: {str(e)}")
        log_to_cloudwatch_logs(LOG_STREAM_NAME, f"JSON error occurred while processing message ID: {message['MessageId']}.")
    except ClientError as e:
        logger.error(f"Error processing message ID: {message['MessageId']}: {str(e)}")
        log_to_cloudwatch_logs(LOG_STREAM_NAME, f"Client error occurred while processing message ID: {message['MessageId']}.")
    except Exception as e:
        logger.error(f"Unexpected error during processing message ID: {message['MessageId']}: {str(e)}")
        log_to_cloudwatch_logs(LOG_STREAM_NAME, f"Unexpected error occurred while processing message ID: {message['MessageId']}.")

async def process_sqs_messages():
    while True:
        try:
            logger.info("Starting to poll SQS for messages.")
            response = sqs.receive_message(
                QueueUrl=QUEUE_wynt_resumes,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=1,
                VisibilityTimeout=1
            )

            messages = response.get('Messages', [])

            if not messages:
                logger.info("No messages in queue. Waiting...")
                await asyncio.sleep(5)
                continue

            for message in messages:
                await process_message(message)

        except Exception as e:
            logger.error(f"Error in SQS processing loop: {str(e)}")
            log_to_cloudwatch_logs(LOG_STREAM_NAME, "Error in the SQS processing loop.")
            await asyncio.sleep(1)

"""if __name__ == "__main__":
    asyncio.run(process_sqs_messages())"""