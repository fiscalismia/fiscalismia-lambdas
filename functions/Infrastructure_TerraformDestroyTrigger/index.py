import json
import os
from datetime import datetime

print('Loading function: Infrastructure_TerraformDestroyTrigger')

def lambda_handler(event, context):
    """
    Lambda function to trigger infrastructure teardown.
    Triggered by SNS when budget limits are exceeded.
    WARNING: This function initiates destruction of infrastructure resources.
    """
    function_name = context.function_name
    request_id = context.request_id

    print(f"Function: {function_name} | Request ID: {request_id}")
    print(f"Invoked at: {datetime.utcnow().isoformat()}")
    print("=" * 60)
    print("WARNING: INFRASTRUCTURE TEARDOWN TRIGGER")
    print("=" * 60)

    # Extract SNS message
    try:
        if 'Records' in event and len(event['Records']) > 0:
            sns_message = event['Records'][0]['Sns']['Message']
            print(f"Budget Alert Message: {sns_message}")

            # TODO: Implement your teardown logic here
            # Example actions:
            # 1. Verify the budget alert is legitimate
            # 2. Send final notifications to administrators
            # 3. Trigger Terraform destroy via AWS Systems Manager, CodeBuild, or similar
            # 4. Log the teardown event to S3 or CloudWatch

            print("TEARDOWN LOGIC WOULD BE EXECUTED HERE")
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Teardown trigger processed",
                    "function": function_name,
                    "alert_message": sns_message,
                    "action_taken": "Logged for review (actual teardown not yet implemented)"
                })
            }
        else:
            print("No SNS records found in event")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid event structure"})
            }
    except Exception as e:
        print(f"Error processing teardown trigger: {str(e)}")
        raise