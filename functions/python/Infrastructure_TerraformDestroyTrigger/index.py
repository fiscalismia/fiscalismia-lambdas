# s3://fiscalismia-infrastructure/lambdas/infrastructure/python/Infrastructure_TerraformDestroyTrigger.zip
import json
import requests
import boto3
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities import parameters
from sns_utility import SnsWrapper

# Read ENV Variables from Terraform
SNS_TOPIC_ARN_NOTIFICATION_SENDER = os.environ.get('SNS_TOPIC_ARN_NOTIFICATION_SENDER')
COST_BUDGET_ALARM_TOTAL_ACTUAL_NAME = os.environ.get('COST_BUDGET_ALARM_TOTAL_ACTUAL_NAME')
COST_BUDGET_ALARM_TOTAL_FORECAST_NAME  = os.environ.get('COST_BUDGET_ALARM_TOTAL_FORECAST_NAME')
logger = Logger(service="Infrastructure_TerraformDestroyTrigger")
def lambda_handler(event, context):
    """
    Lambda function to trigger infrastructure teardown.
    Triggered by SNS when budget limits are exceeded.
    2 Cases:
        - NOTIFICATION Cost forecast exceeds budget notification_type = "FORECASTED"
        - TEARDOWN: Costs exceed 80% of budget -> notification_type = "ACTUAL"
    WARNING: This function initiates destruction of infrastructure resources.
    """
    function_name = context.function_name
    request_id = context.aws_request_id
    current_time = datetime.now(tz=ZoneInfo("Europe/Berlin"))

    logger.debug("Function invoked", extra={"function_name": function_name, "request_id": request_id, "invoked_at": current_time })

    # Extract SNS message
    try:
        if 'Records' in event and len(event['Records']) > 0:
            sns_message = event['Records'][0]['Sns']['Message']
            sns_subject = event['Records'][0]['Sns']['Subject']
            sns_timestamp = event['Records'][0]['Sns']['Timestamp']
            sns_topic_arn = event['Records'][0]['Sns']['TopicArn']

            logger.info("SNS Message Received.", extra={"topic_arn": sns_topic_arn,  "sns_message": sns_message, "timestamp": sns_timestamp, "subject": sns_subject})

            is_match: bool = False
            auto_destroy: bool = False
            user_message = None
            alarm_amount = None
            
            # Pattern to extract the forecasted / actual amount from cost alarm
            pattern = r"((?:FORECASTED|ACTUAL) Amount:\s*\$\d+(?:\.\d+)?)"
            match = re.search(pattern, sns_message)
            if match:
                alarm_amount = match.group(1)
            
            if COST_BUDGET_ALARM_TOTAL_ACTUAL_NAME in sns_subject:
                is_match = True
                auto_destroy = True
                user_message = {
                    "auto_destroy": auto_destroy,
                    "manual_action_required": False,
                    "status": "DESTRUCTION_INVOKED",
                    "target": "AWS INFRASTRUCTURE",
                    "invoking_sns": sns_subject,
                    "alarm_amount": alarm_amount,
                }
            if COST_BUDGET_ALARM_TOTAL_FORECAST_NAME in sns_subject:
                is_match = True
                user_message = {
                    "auto_destroy": auto_destroy,
                    "manual_action_required": True,
                    "status": "FORECAST_EXCEEDED",
                    "invoking_sns": sns_subject,
                    "alarm_amount": alarm_amount,
                }
            # Fallback in case the alarm is not found within sns_subject
            if not is_match:
                error_msg = "Cost Alarm Names not found within sns subject"
                logger.error(error_msg)
                user_message = {
                    "status": "ERROR",
                    "service": "Infrastructure_TerraformDestroyTrigger",
                    "error_msg" : error_msg,
                    "invoking_sns": sns_subject,
                    "sns_message": sns_message,
                }
            # Notify Admin via SNS Topic invoking a Notification Sender Lambda Function
            sns_resource = boto3.resource("sns")
            sns_wrapper = SnsWrapper(sns_resource)
            topic = sns_resource.Topic(SNS_TOPIC_ARN_NOTIFICATION_SENDER)
            attributes = {"test": "string", "bintest": b"binary"}

            if auto_destroy:
                logger.debug("Querying SecureString Parameters from Parameter Store", extra={"params": "TERRAFORM_DESTROY_GITHUB_WEBHOOK"})
                TERRAFORM_DESTROY_GITHUB_WEBHOOK = parameters.get_parameter(
                    "/github/webhooks/TERRAFORM_DESTROY_GITHUB_WEBHOOK",
                    decrypt=True
                )
                if TERRAFORM_DESTROY_GITHUB_WEBHOOK is None:
                    error_msg = "Github SecureString could not be extracted from parameter store."
                    logger.error(error_msg)
                    return {
                        "statusCode": 400,
                        "body": json.dumps({"error": error_msg})
                    }
                
                # Call Github Actions Pipeline to destroy non-persistent ephemeral aws infrastructure
                logger.warn("INFRASTRUCTURE KILLSWITCH INVOKED", extra={"invoking": "TerraformModuleDestroyer Pipeline"})

                url = "https://api.github.com/repos/fiscalismia/fiscalismia-infrastructure/dispatches"
                payload = {
                    "event_type": "aws_infrastructure_destroyer",
                    "client_payload": { "destroy_aws_resources": True }
                }
                headers = {
                    "accept": "application/vnd.github+json",
                    "authorization": f"Bearer {TERRAFORM_DESTROY_GITHUB_WEBHOOK}",
                    "content-type": "application/json"
                }
                response = requests.post(url, json=payload, headers=headers)
                status = response.status_code
                content = None
                if status != 204:
                    try:
                        content = response.json()
                    except ValueError:
                        content = response.text
                    error_msg = f"Github Webhook Invocation status invalid: {status}"
                    logger.error(error_msg, extra={"github_response": content})
                    sns_response = sns_wrapper.publish_message(topic, json.dumps({"error_msg": error_msg} | {"github_response": content} | user_message), attributes, logger)
                    logger.debug("Sent SNS github error message.", extra={"sns_response": sns_response})
                    return {
                        "statusCode": 404,
                        "body": json.dumps({"error": error_msg, "github_response": content})
                    }
                logger.info("Invoked TerraformModuleDestroyer Pipeline via webhook.", extra={"github_response": content, "actions_url" : "https://github.com/fiscalismia/fiscalismia-infrastructure/actions"})
                user_message = user_message | {"gh_status": status, "actions_url" : "https://github.com/fiscalismia/fiscalismia-infrastructure/actions"}

            sns_response = sns_wrapper.publish_message(topic, json.dumps(user_message), attributes, logger)
            logger.debug("Sent SNS message.", extra={"sns_response": sns_response})

            # Use Operator to merge these two dictionaries and return as result
            result_message = json.dumps(user_message | {"sns_notification_response": sns_response})
            if not is_match:
                return {
                    "statusCode": 422,
                    "body": result_message
                }
            else:
                return {
                    "statusCode": 200,
                    "body": result_message
                }
        else:
            logger.error("No SNS records found in event")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid SNS event structure"})
            }
    except Exception as e:
        logger.error("Unexpected error during TerraformDestroyTrigger", extra={"error": str(e)})
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }