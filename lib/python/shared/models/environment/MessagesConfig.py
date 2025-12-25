from pydantic import BaseModel, Field


class MessagesConfig(BaseModel):
    key: str = Field(validation_alias="FILE_KEY")
    fileBucket: str = Field(validation_alias="FILE_BUCKET")
    bucketKey: str = Field(validation_alias="FILE_BUCKET_KEY")
