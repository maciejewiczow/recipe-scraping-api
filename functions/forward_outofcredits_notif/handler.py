from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.parser import event_parser
from pydantic import BaseModel
from shared.utils.dump_response import dump_response
from shared.utils.environment import validate_environment
from .env import Environment

log = Logger("forward_outofcredits_notif")


class SQSNotificationMessage(BaseModel):
    pass


@log.inject_lambda_context(log_event=True)
# @event_parser(
#     model=,
# )
@validate_environment(model=Environment, log=log)
@dump_response
def handler(
    event,
    context: LambdaContext,
    *,
    env: Environment,
):
    log.debug(event)
