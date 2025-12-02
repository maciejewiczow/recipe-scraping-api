from pydantic import Field
from shared.models.environment.NotificationsConfig import NotificationsConfig
from shared.models.environment.QuotaBaseEnv import QuotaBaseEnv
from shared.utils.str_to_timedelta import SerializableTimedelta


class Environment(QuotaBaseEnv):
    processIngredientStepFnArn: str = Field(
        validation_alias="PROCESS_INGREDIENTS_STEP_FN_ARN"
    )
    recipesTableName: str = Field(validation_alias="RECIPES_TABLE_NAME")
    recipeTTL: SerializableTimedelta = Field(validation_alias="RECIPE_TTL")
    platformApplicationARN: NotificationsConfig = Field(
        validation_alias="SNS_PLARFORM_APPLICATION_ARN"
    )
