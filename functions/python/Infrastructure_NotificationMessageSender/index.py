import json
import requests
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities import parameters
from zoneinfo import ZoneInfo
from datetime import datetime

logger = Logger(service="Infrastructure_NotificationMessageSender")
TELEGRAM_BOT_ENDPOINT_BASE_URL: str = "api.telegram.org/bot"

def sns_message_parser(sns_message) -> str:
    """
    Parse SNS message and return the message content.
    Formatted specifically for telegram api HTML parsing.
    Default fallback is unmodified sns_message.
    """
    logger.debug("Parsing SNS message", extra={"sns_message": sns_message})
    if isinstance(sns_message, str) and len(sns_message) > 0:
        try:
            parsed_delta = json.loads(sns_message)
            preformatted_str = ""
            for key, value in parsed_delta.items():
                pad_len = 25
                pad_char= " "
                pad_str = ""
                if len(key) < pad_len:
                    pad_str = f"{pad_char * (pad_len - len(key))}"
                preformatted_str += f"<code>{key}:{pad_str}{value}</code>\n"
            if len(preformatted_str) > 0:
                parsed_delta = preformatted_str
            print(preformatted_str)
        except json.JSONDecodeError as e:
            logger.warn("JSON parsing failed.", extra={"sns_message": sns_message})
            parsed_delta = sns_message
    else:
        # Early return of unmodified input
        return sns_message
    parsed_result = parsed_delta
    return f"<b>ʕっ•ᴥ•ʔっ  ♡  ⊂ʕ•ᴥ•⊂ʔ</b>\n<pre>{parsed_result}</pre>"

def lambda_handler(event, context):
    """
    Lambda function to send notification messages.
    Triggered by SNS to process and forward notifications.
    """
    function_name = context.function_name
    request_id = context.aws_request_id
    current_time = datetime.now(tz=ZoneInfo("Europe/Berlin"))

    logger.debug("Function invoked", extra={"function_name": function_name, "request_id": request_id, "invoked_at": current_time })

    try:
        logger.debug("Querying SecureString Parameters from Parameter Store", extra={"params": "TELEGRAM_API_TOKEN, TELEGRAM_CHAT_ID"})
        TELEGRAM_API_TOKEN = parameters.get_parameter(
            "/notifications/telegram/FISCALISMIA_MSG_TELEGRAM_API_TOKEN",
            decrypt=True
        )
        TELEGRAM_CHAT_ID = parameters.get_parameter(
            "/notifications/telegram/ADMIN_TELEGRAM_CHAT_ID",
            decrypt=True
        )
        if TELEGRAM_API_TOKEN is None or TELEGRAM_CHAT_ID is None:
            error_msg = "Telegram SecureStrings could not be extracted from parameter store."
            logger.error(error_msg)
            return {
                "statusCode": 400,
                "body": json.dumps({"error": error_msg})
            }
        if 'Records' in event and len(event['Records']) > 0:
            # Decoding received SNS message and subject
            sns_message = event['Records'][0]['Sns']['Message']
            sns_subject = event['Records'][0]['Sns']['Subject']
            sns_timestamp = event['Records'][0]['Sns']['Timestamp']
            sns_topic_arn = event['Records'][0]['Sns']['TopicArn']
            logger.info("SNS Message Received.", extra={"topic_arn": sns_topic_arn,  "sns_message": sns_message, "timestamp": sns_timestamp, "subject": sns_subject})

            # building telegram endpoint and payload
            url = f"https://{TELEGRAM_BOT_ENDPOINT_BASE_URL}{TELEGRAM_API_TOKEN}/sendMessage"
            logger.debug("Sending Notification to Telegram API", extra={"telegram_endpoint": url})

            headers = {"content-type": "application/json"}
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "parse_mode": "HTML",
                "text": sns_message_parser(sns_message)
            }
            # Sending request payload to telegram api
            response = requests.post(url, json=payload, headers=headers)
            data = json.loads(response.text)
            telegram_status = data.get("ok", None)
            telegram_result = data.get("result", None)
            logger.debug("Sent Telegram request.", extra={"status": telegram_status, "result": telegram_result})

            if telegram_status is True:
                telegram_sender_name = data.get("result", None).get("from", None).get("first_name", None)
                telegram_receiver_username = data.get("result", None).get("chat", None).get("username", None)
                logger.info("Telegram Notification sent successfully", extra={"sender_name": telegram_sender_name,"receiver_username": telegram_receiver_username})
            else:
                logger.error("Telegram Notification not sent successfully",extra={"status": telegram_status, "result": telegram_result})
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "Telegram Notification not sent successfully"})
                }
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Notification sent successfully",
                    "function": function_name,
                    "subject": sns_subject,
                    "notification_content": sns_message,
                    "telegram_sender_name": telegram_sender_name,
                    "telegram_receiver_username": telegram_receiver_username,
                })
            }
        else:
            logger.error("No SNS records found in event")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid SNS event structure"})
            }
    except Exception as e:
        logger.error("Unexpected error during NotificationMessageSender", extra={"error": str(e)})
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }