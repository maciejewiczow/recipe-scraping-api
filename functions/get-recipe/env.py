from pydantic import Field
from shared.models.environment.QuotaBaseEnv import QuotaBaseEnv


class Environment(QuotaBaseEnv):
    recipesTableName: str = Field(validation_alias="RECIPES_TABLE_NAME")
