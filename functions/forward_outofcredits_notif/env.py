from pydantic import Field
from shared.models.environment.settings import BaseEnvironment


class Environment(BaseEnvironment):
    emailTopicArn: str = Field(validation_alias="EMAIL_TOPIC_ARN")
