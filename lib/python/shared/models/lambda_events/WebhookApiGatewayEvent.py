from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventV2Model


class WebhookApiGatewayEvent(APIGatewayProxyEventV2Model):
    body: str = ""
    queryStringParameters: None = None
