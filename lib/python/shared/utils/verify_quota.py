from decimal import Decimal
import functools
from typing import Any
from aws_lambda_powertools import Logger
import boto3
import botocore
import botocore.exceptions
from pydantic import ValidationError
from shared.models.authorization.CognitoUserClaims import CognitoUserClaims
from shared.models.database.QuotaItem import QuotaItem
from shared.models.environment.QuotaBaseEnv import QuotaBaseEnv
from shared.models.responses.HttpResponse import (
    ForbiddenResponse,
    InternalServerErrorResponse,
    TooManyRequestsHeaders,
    TooManyRequestsResponse,
)
from aws_lambda_powertools.utilities.parser.models import (
    RequestContextV2Authorizer,
    RequestContextV2AuthorizerJwt,
    APIGatewayProxyEventV2Model,
)
from boto3.dynamodb.conditions import Key
from aws_lambda_powertools.utilities.parser import parse
from .openapi import OpenApiMetadata, openapi_meta_key_name


class InvalidClaimsError(Exception):
    pass


def get_cognito_claims(event: APIGatewayProxyEventV2Model) -> CognitoUserClaims:
    match event.requestContext.authorizer:
        case RequestContextV2Authorizer(
            jwt=RequestContextV2AuthorizerJwt(claims=claims)
        ):
            try:
                return CognitoUserClaims(**claims)
            except ValidationError as e:
                raise InvalidClaimsError() from e
        case _:
            raise ValueError("Missing authentication info")


def verify_user_quota(log: Logger):
    def decorator(func):
        openapi_def: OpenApiMetadata | None = getattr(func, openapi_meta_key_name, None)

        if openapi_def is not None:
            if TooManyRequestsResponse not in openapi_def.responses:
                openapi_def.responses.append(TooManyRequestsResponse)

            if ForbiddenResponse not in openapi_def.responses:
                openapi_def.responses.append(ForbiddenResponse)

        @functools.wraps(func)
        def wrapper(raw_event: dict[str, Any], *args, **kwargs):
            try:
                event = parse(model=APIGatewayProxyEventV2Model, event=raw_event)
            except ValidationError:
                log.exception("Event validation error")
                return InternalServerErrorResponse(body="Invalid lambda event")

            try:
                env = QuotaBaseEnv()

                claims = get_cognito_claims(event)

                quotaTable = boto3.resource("dynamodb").Table(env.quotaTableName)

                result = quotaTable.query(
                    KeyConditionExpression=Key(QuotaItem.get_primary_key_name()).eq(
                        claims.userId
                    ),
                    Select="COUNT",
                    ReturnConsumedCapacity="NONE",
                )

                if (
                    result.get("LastEvaluatedKey") is not None
                    or result["Count"] >= claims.quotaValue
                ):
                    return TooManyRequestsResponse(
                        headers=TooManyRequestsHeaders(
                            retryAfter=claims.quotaWindow.seconds
                        )
                    )

                quotaItemDict = QuotaItem(
                    UserId=claims.userId,
                    RequestTimestamp=Decimal(
                        str(event.requestContext.timeEpoch.timestamp())
                    ),
                    ExpiresAt=event.requestContext.timeEpoch + claims.quotaWindow,
                ).model_dump()

                log.debug(quotaItemDict)

                quotaTable.put_item(
                    Item=quotaItemDict,
                    ReturnValues="NONE",
                )

                kwargs["jwtClaims"] = claims
            except ValidationError:
                log.exception("Invalid quota table env config")
                return InternalServerErrorResponse(
                    body="Internal server error: invalid env config"
                )
            except botocore.exceptions.ClientError:
                log.exception("Dynamodb client error occured")
                return InternalServerErrorResponse()
            except (InvalidClaimsError, ValueError):
                log.exception("Cognito claims validation failed")
                return ForbiddenResponse()

            return func(event, *args, **kwargs)

        return wrapper

    return decorator
