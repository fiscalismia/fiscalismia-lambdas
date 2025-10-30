import json
import os
from datetime import datetime

print('Loading function: Infrastructure_ApiGatewayRouteThrottler')

def lambda_handler(event, context):
    """
    Lambda function to handle API Gateway route throttling alerts.
    Triggered by SNS when throttling thresholds are exceeded.
    """
    function_name = context.function_name
    request_id = context.request_id

    print(f"Function: {function_name} | Request ID: {request_id}")
    print(f"Invoked at: {datetime.utcnow().isoformat()}")

    # Extract SNS message
    try:
        if 'Records' in event and len(event['Records']) > 0:
            sns_message = event['Records'][0]['Sns']['Message']
            print(f"SNS Message Received: {sns_message}")

            # TODO: Implement your throttling logic here
            # Example: Parse the message, identify the route, adjust rate limits

            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Route throttling processed successfully",
                    "function": function_name,
                    "sns_message": sns_message
                })
            }
        else:
            print("No SNS records found in event")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid event structure"})
            }
    except Exception as e:
        print(f"Error processing event: {str(e)}")
        raise