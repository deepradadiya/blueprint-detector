import boto3
import os
from botocore.exceptions import ClientError

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

# Bucket name
bucket_name = os.getenv('S3_BUCKET_NAME')

def test_s3():
    try:
        # List objects in the bucket (or check if bucket exists)
        response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        print(f"Success! Bucket '{bucket_name}' is accessible.")
        if 'Contents' in response:
            print(f"Found objects: {response['Contents']}")
        else:
            print("Bucket is empty or no objects found.")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"Error: {error_code} - {e.response['Error']['Message']}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    test_s3()