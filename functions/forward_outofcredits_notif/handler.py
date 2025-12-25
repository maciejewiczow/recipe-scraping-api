from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.parser import event_parser
from aws_lambda_powertools.utilities.parser.models.sqs import SqsModel
import boto3
import botocore
import botocore.exceptions
from pydantic import BaseModel, ValidationError
from shared.utils.dump_response import dump_response
from shared.utils.environment import validate_environment
from shared.utils.messages import EmailContent, get_messages
from .env import Environment

log = Logger("forward_outofcredits_notif")


class SQSNotificationMessage(BaseModel):
    recipeId: str


@log.inject_lambda_context(log_event=True)
@event_parser(
    model=SqsModel,
)
@validate_environment(model=Environment, log=log)
@dump_response
def handler(
    event: SqsModel,
    context: LambdaContext,
    *,
    env: Environment,
):
    sns = boto3.client("sns")

    message = get_messages(env.emailMessage, EmailContent, log)

    for record in event.Records:
        try:
            payload = SQSNotificationMessage.model_validate_json(record.body)  # pyright: ignore[reportArgumentType]

            sns.publish(
                Subject=message.subject,
                Message=message.body.format(recipeId=payload.recipeId),
                TopicArn=env.emailTopicArn,
            )
        except ValidationError:
            log.exception("Invalid messsage body")
        except botocore.exceptions.ClientError:
            log.exception("Error while publishing the sns message")
