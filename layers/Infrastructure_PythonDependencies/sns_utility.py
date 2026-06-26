from botocore.exceptions import ClientError

# See https://github.com/awsdocs/aws-doc-sdk-examples/blob/main/python/example_code/sns/sns_basics.py
class SnsWrapper:
    """Encapsulates Amazon SNS topic and subscription functions."""

    def __init__(self, sns_resource):
        """
        :param sns_resource: A Boto3 Amazon SNS resource.
        """
        self.sns_resource = sns_resource

    @staticmethod
    def publish_message(topic, message, attributes, logger):
        """
        Publishes a message, with attributes, to a topic. Subscriptions can be filtered
        based on message attributes so that a subscription receives messages only
        when specified attributes are present.

        :param topic: The topic to publish to.
        :param message: The message to publish.
        :param attributes: The key-value attributes to attach to the message. Values
            must be either `str` or `bytes`.
        :return: The ID of the message.
        """
        try:
            att_dict = {}
            for key, value in attributes.items():
                if isinstance(value, str):
                    att_dict[key] = {"DataType": "String", "StringValue": value}
                elif isinstance(value, bytes):
                    att_dict[key] = {"DataType": "Binary", "BinaryValue": value}
            response = topic.publish(Message=message, MessageAttributes=att_dict)
            logger.debug("SNS Topic full response", extra={"full_response": response})
            message_id = response.get("MessageId", None)
            sns_status = response.get("ResponseMetadata", None).get("HTTPStatusCode", None)
            sns_content_type = response.get("ResponseMetadata", None).get("HTTPHeaders", None).get("content-type", None)
            sns_content_length = response.get("ResponseMetadata", None).get("HTTPHeaders", None).get("content-length", None)
            logger.info(
                "Published message with attributes %s to topic %s.",
                attributes,
                topic.arn,
            )
        except ClientError:
            logger.exception("Couldn't publish message to topic %s.", topic.arn)
            raise
        else:
            return {
                "message_id" : message_id,
                "status": sns_status,
                "content_type": sns_content_type,
                "content_length": sns_content_length
            }