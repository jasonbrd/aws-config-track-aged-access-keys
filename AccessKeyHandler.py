import os
import json
import boto3
from datetime import datetime, timedelta

def lambda_handler(event, context):
    # Setup environment
    grace_period = int(os.environ['GRACE_PERIOD_DAYS'])
    sns_topic_arn = os.environ['SNS_TOPIC_ARN']
    db_table = os.environ['DB_TABLE']
    sqs_queue = os.environ['SQS_QUEUE']
    
    # Get values from incoming SQS message
    message = event['Records'][0]
    message_body = json.loads(message['body'])
    resource_id = message_body['resource_id']
    account_id = message_body['account_id']
    resource_name = message_body['resource_name']

    # Connect to DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(db_table)
    
    # Query the DynamoDB table for the record with the primary key of the hash string
    response = table.get_item(Key={'resource_id': resource_id})
    item = response.get('Item')
    
    # If the item does not exist in the DynamoDB table, add item
    if item is None:
        now = datetime.utcnow()
        expiry_time = int((now + timedelta(days=(grace_period+30))).timestamp())
        table.put_item(
            Item={
                'resource_id': resource_id,
                'key_grace_period': grace_period,
                'access_key_ttl': expiry_time,
                'account_id': account_id,
                'resource_name': resource_name
            }
        )
        
        # Connect to SNS and send message
        sns = boto3.client('sns')
        
        sns.publish(
            TopicArn=sns_topic_arn,
            Message=f'Access Key for user {resource_name} in account {account_id} now in grace period.'
        )
    else:
        if item.get('key_grace_period') > 0:
            item['key_grace_period'] -= 1
            
            table.update_item(
                Key={'resource_id': resource_id},
                UpdateExpression='set key_grace_period = :val',
                ExpressionAttributeValues={':val': item['key_grace_period']}
            )
        elif item.get('key_grace_period') == 0:
            # Connect to SNS & send violation notice
            sns = boto3.client('sns')

            sns.publish(
                TopicArn=sns_topic_arn,
                Message=f'Access Key for user {resource_name} in account {account_id} is now in violation of policy.'
            )
    
        # Remove message from SQS as it has been processed
        sqs = boto3.client('sqs')
        sqs.delete_message(
            QueueUrl=sqs_queue,
            ReceiptHandle=message['receiptHandle']
        )

    # Return from function
    return {
        'statusCode': 200,
        'body': ''
    }
