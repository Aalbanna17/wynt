import boto3
from botocore.exceptions import ClientError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

s3 = boto3.client('s3')

def get_s3_object_old(bucket, key):
    try:
        metadata_response = s3.head_object(Bucket=bucket, Key=key)
        metadata = metadata_response.get('Metadata', {})
        logger.info(f"Metadata for {key}: {metadata}")
        
        response = s3.get_object(Bucket=bucket, Key=key)
        file_content = response['Body'].read()
        return file_content , metadata
    except ClientError as e:
        logger.error(f"Error getting S3 object: {str(e)}")
        raise

def get_s3_object(bucket, key):
    if not key.endswith("resume.pdf"):
        logger.info(f"Skipping file {key} as it is not 'resume.pdf'")
        return None, None

    try:
        metadata_response = s3.head_object(Bucket=bucket, Key=key)
        metadata = metadata_response.get('Metadata', {})
        logger.info(f"Metadata for {key}: {metadata}")
        
        response = s3.get_object(Bucket=bucket, Key=key)
        file_content = response['Body'].read()
        return file_content, metadata
    except ClientError as e:
        logger.error(f"Error getting S3 object: {str(e)}")
        raise