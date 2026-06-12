# s3://fiscalismia-infrastructure/lambdas/infrastructure/python/Infrastructure_ApiGatewayRouteThrottler.zip
import json
import boto3
import os
from aws_lambda_powertools import Logger
from datetime import datetime
from zoneinfo import ZoneInfo
from sns_utility import SnsWrapper

# Read ENV Variables from Terraform
REST_API_ID = os.environ.get('REST_API_ID')
REST_API_STAGE = os.environ.get('REST_API_STAGE')
REST_API_S3_IMG_DOWNSCALE_ROUTE = os.environ.get('REST_API_S3_IMG_DOWNSCALE_ROUTE')
REST_API_RAW_DATA_ETL_ROUTE = os.environ.get('REST_API_RAW_DATA_ETL_ROUTE')
SNS_TOPIC_ARN_NOTIFICATION_SENDER = os.environ.get('SNS_TOPIC_ARN_NOTIFICATION_SENDER')
POST_IMG_ROUTE_CLOUDWATCH_ALARM_NAME = os.environ.get('POST_IMG_ROUTE_CLOUDWATCH_ALARM_NAME')
RAW_DATA_ETL_ROUTE_CLOUDWATCH_ALARM_NAME  = os.environ.get('RAW_DATA_ETL_ROUTE_CLOUDWATCH_ALARM_NAME')
logger = Logger(service="Infrastructure_ApiGatewayRouteThrottler")
def lambda_handler(event, context):
    """
    Lambda function to handle API Gateway route throttling alerts.
    Triggered by SNS when throttling thresholds are exceeded.
    """
    function_name = context.function_name
    request_id = context.aws_request_id
    current_time = datetime.now(tz=ZoneInfo("Europe/Berlin"))

    logger.debug("Function invoked", extra={"function_name": function_name, "request_id": request_id, "invoked_at": current_time })

    # Extract SNS message triggering the lambda
    try:
        if 'Records' in event and len(event['Records']) > 0:
            sns_message = event['Records'][0]['Sns']['Message']
            sns_subject = event['Records'][0]['Sns']['Subject']
            sns_timestamp = event['Records'][0]['Sns']['Timestamp']
            sns_topic_arn = event['Records'][0]['Sns']['TopicArn']

            logger.info("SNS Message Received.", extra={"topic_arn": sns_topic_arn,  "sns_message": sns_message, "timestamp": sns_timestamp, "subject": sns_subject})

            # Create API Gateway Client via boto3 sdk
            # See https://awscli.amazonaws.com/v2/documentation/api/2.0.34/reference/apigatewayv2/index.html
            client = boto3.client('apigatewayv2')

            throttled_route = None
            throttle_message = None
            is_invalid = False
            if POST_IMG_ROUTE_CLOUDWATCH_ALARM_NAME in sns_subject:
                throttled_route = REST_API_S3_IMG_DOWNSCALE_ROUTE
            if RAW_DATA_ETL_ROUTE_CLOUDWATCH_ALARM_NAME in sns_subject:
                throttled_route = REST_API_RAW_DATA_ETL_ROUTE
            if throttled_route is not None:
                # Throttle S3 Route on receiving valid Alarm via SNS Subject
                response = client.update_stage(
                    ApiId=REST_API_ID,
                    StageName=REST_API_STAGE,
                    RouteSettings={
                    throttled_route: {
                        'ThrottlingBurstLimit': 0,
                        'ThrottlingRateLimit': 0
                        }
                    }
                )
                updated_route_settings = response.get("RouteSettings", None)
                logger.debug("Throttled Route .", extra={"RouteSettings": updated_route_settings})
                throttle_message = {
                    "status": "THROTTLED",
                    "service": "Infrastructure_ApiGatewayRouteThrottler",
                    "invoking_sns": sns_subject,
                    "s3_route_settings": updated_route_settings.get(REST_API_S3_IMG_DOWNSCALE_ROUTE, None),
                    "etl_route_settings": updated_route_settings.get(REST_API_RAW_DATA_ETL_ROUTE, None),
                }
            else:
                is_invalid = True
                error_msg = "Subject of invoking sns routine does not contain correct route_key"
                logger.error(error_msg)
                throttle_message = {
                    "status": "INVALID",
                    "service": "Infrastructure_ApiGatewayRouteThrottler",
                    "invoking_sns": sns_subject,
                    "s3_route_settings": "unchanged",
                    "etl_route_settings": "unchanged",
                }
            # Notify Admin via SNS Topic invoking a Notification Sender Lambda Function
            sns_resource = boto3.resource("sns")
            sns_wrapper = SnsWrapper(sns_resource)
            topic = sns_resource.Topic(SNS_TOPIC_ARN_NOTIFICATION_SENDER)
            attributes = {"test": "string", "bintest": b"binary"}
            sns_response = sns_wrapper.publish_message(topic, json.dumps(throttle_message), attributes, logger)
            logger.debug("Sent SNS message.", extra={"sns_response": sns_response})

            # Use Operator to merge these two dictionaries and return as result
            result_message = json.dumps(throttle_message | {"sns_notification_response": sns_response})
            if not is_invalid:
                return {
                    "statusCode": 200,
                    "body": result_message
                }
            else:
                return {
                    "statusCode": 422,
                    "body": result_message
                }
        else:
            logger.error("No SNS records found in event")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid SNS event structure"})
            }
    except Exception as e:
        logger.error("Unexpected error during RouteThrottler", extra={"error": str(e)})
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }