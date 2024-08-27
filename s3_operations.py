import boto3
from botocore.exceptions import ClientError
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

s3 = boto3.client('s3')

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

async def send_and_save_to_s3(cv_data,scorecandidate_json,extracted_text,resumeid,region='us-east-1'):
    bucket_name = 'wynt'
    root_path = f'resumes/{resumeid}/'

    cv_data_json = json.dumps(cv_data)
    score_data_c_json = json.dumps(scorecandidate_json)


    cv_data_file_name = 'cv_data.json'
    score_c_data_file_name = 'scorecandidate.json'

    extracted_text_file_name = 'extracted_text.txt'

    s3_url = f'http://{bucket_name}.s3-{region}.amazonaws.com/{root_path}'

    try:
        s3 = boto3.client('s3', region_name=region)
        s3.put_object(
            Bucket=bucket_name,
            Key=f'{root_path}{cv_data_file_name}',
            Body=cv_data_json,
            ContentType='application/json'
        )

        s3.put_object(
            Bucket=bucket_name,
            Key=f'{root_path}{score_c_data_file_name}',
            Body=score_data_c_json,
            ContentType='application/json'
        )

        s3.put_object(
            Bucket=bucket_name,
            Key=f'{root_path}{extracted_text_file_name}',
            Body=extracted_text,
            ContentType='application/txt'
        )

        logger.info(f'Files successfully uploaded to {s3_url} in {bucket_name}')
    except ClientError as e:
        logger.error(f'Failed to upload files to S3: {e}')
        raise
    except Exception as e:
        logger.error(f'Unexpected error: {e}')
        raise