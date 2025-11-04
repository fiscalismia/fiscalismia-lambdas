import json
import os
from datetime import datetime

print('Loading function')

# ==================== REUSABLE HELPER FUNCTIONS ====================

def log_event(event: dict) -> None:
    """Log the full event in a formatted way."""
    print("=" * 60)
    print("FULL EVENT:")
    print(json.dumps(event, indent=2, default=str))
    print("=" * 60)

def log_context(context) -> None:
    """Log all relevant Lambda context information."""
    print("=" * 60)
    print("LAMBDA CONTEXT INFORMATION:")
    print(f"  Function Name:        {context.function_name}")
    print(f"  Function Version:     {context.function_version}")
    print(f"  Invoked Function ARN: {context.invoked_function_arn}")
    print(f"  Memory Limit (MB):    {context.memory_limit_in_mb}")
    print(f"  Log Group Name:       {context.log_group_name}")
    print(f"  Log Stream Name:      {context.log_stream_name}")
    print(f"  Remaining Time (ms):  {context.get_remaining_time_in_millis()}")
    print("=" * 60)

def log_environment() -> None:
    """Log relevant environment variables."""
    print("=" * 60)
    print("ENVIRONMENT VARIABLES:")
    print(f"  AWS_REGION:           {os.environ.get('AWS_REGION', 'N/A')}")
    print(f"  AWS_EXECUTION_ENV:    {os.environ.get('AWS_EXECUTION_ENV', 'N/A')}")
    print(f"  AWS_LAMBDA_FUNCTION_NAME: {os.environ.get('AWS_LAMBDA_FUNCTION_NAME', 'N/A')}")
    print(f"  AWS_LAMBDA_FUNCTION_VERSION: {os.environ.get('AWS_LAMBDA_FUNCTION_VERSION', 'N/A')}")
    print("=" * 60)

def extract_sns_message(event: dict) -> str:
    """
    Extract and return the SNS message from the event.
    Returns 'N/A' if the event is not from SNS.
    """
    try:
        if 'Records' in event and len(event['Records']) > 0:
            record = event['Records'][0]
            if 'Sns' in record:
                return record['Sns']['Message']
        return "N/A - Event is not from SNS"
    except (KeyError, IndexError) as e:
        return f"Error extracting SNS message: {str(e)}"

def process_data(data: str) -> dict:
    """
    Example reusable function to process some data.
    Replace this with your actual business logic.
    """
    return {
        "processed_at": datetime.utcnow().isoformat(),
        "original_data": data,
        "processed_data": data.upper(),
        "length": len(data)
    }

# ==================== MAIN LAMBDA HANDLER ====================

def lambda_handler(event, context):
    """
    Main entry point for the Lambda function.
    Logs all relevant information and processes SNS messages.
    """
    print(f"Lambda invoked at: {datetime.utcnow().isoformat()}")

    # Log all Lambda context information
    log_context(context)

    # Log environment variables
    log_environment()

    # Log the full incoming event
    log_event(event)

    # Extract and log SNS message if present
    sns_message = extract_sns_message(event)
    print("=" * 60)
    print("SNS MESSAGE:")
    print(f"  {sns_message}")
    print("=" * 60)

    # Example: Process the data using a helper function
    if sns_message != "N/A - Event is not from SNS":
        result = process_data(sns_message)
        print("=" * 60)
        print("PROCESSING RESULT:")
        print(json.dumps(result, indent=2))
        print("=" * 60)
    else:
        result = {"status": "No SNS message to process"}

    # Return a response
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Lambda executed successfully",
            "sns_message": sns_message,
            "result": result
        }, default=str)
    }