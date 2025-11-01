import json
import os
from datetime import datetime

print('Loading function: Infrastructure_NotificationMessageSender')

def lambda_handler(event, context):
    """
    Lambda function to send notification messages.
    Triggered by SNS to process and forward notifications.
    """
    function_name = context.function_name
    request_id = context.request_id

    print(f"Function: {function_name} | Request ID: {request_id}")
    print(f"Invoked at: {datetime.utcnow().isoformat()}")

    # Extract SNS message
    try:
        if 'Records' in event and len(event['Records']) > 0:
            sns_message = event['Records'][0]['Sns']['Message']
            sns_subject = event['Records'][0]['Sns'].get('Subject', 'No Subject')

            print(f"SNS Subject: {sns_subject}")
            print(f"SNS Message: {sns_message}")

            # TODO: Implement your notification logic here
            # Example: Send email, post to Slack, write to database, etc.

            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Notification sent successfully",
                    "function": function_name,
                    "subject": sns_subject,
                    "notification_content": sns_message
                })
            }
        else:
            print("No SNS records found in event")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid event structure"})
            }
    except Exception as e:
        print(f"Error processing notification: {str(e)}")
        raise