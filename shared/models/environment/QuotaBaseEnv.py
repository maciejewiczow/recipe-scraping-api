from pydantic import Field
from shared.models.environment.settings import BaseEnvironment


class QuotaBaseEnv(BaseEnvironment):
    quotaTableName: str = Field(
        default=..., validation_alias="DYNAMO_USER_QUOTA_TABLE_NAME"
    )
