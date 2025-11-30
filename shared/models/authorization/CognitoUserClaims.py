from pydantic import BaseModel, Field
from shared.utils.str_to_timedelta import SerializableTimedelta


class CognitoUserClaims(BaseModel):
    userId: str = Field(validation_alias="sub")
    quotaValue: int = Field(validation_alias="custom:RequestQuotaValue")
    quotaWindow: SerializableTimedelta = Field(
        validation_alias="custom:RequestQuotaWindow"
    )
