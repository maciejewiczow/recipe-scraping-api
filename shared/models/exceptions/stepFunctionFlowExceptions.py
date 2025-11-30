from pydantic import BaseModel


class FailedToParseAIOutput(Exception, BaseModel):
    retryCount: int


class RepeatedlyFailedToParseAIOutput(Exception):
    pass
